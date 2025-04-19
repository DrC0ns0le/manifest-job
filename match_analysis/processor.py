"""
Job processor for analyzing and matching jobs with profiles
"""

import logging
import asyncio
import json
import threading
from typing import Dict, Any, Optional

from match_analysis.queue import JobQueue
from match_analysis.template import Templater
from match_analysis.llm import LLM

from configuration import ConfigManager

from push_notification.service import NotificationService
from model.job_listing import JobListing

# Configure logging
logging.basicConfig(
    filename="job_scraper.log",
    filemode="a",
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("job_processor")


class JobMatchProcessor:
    """
    Processes jobs by sending them to an API for matching analysis
    """

    def __init__(
        self,
        config: Dict[str, Any],
        job_queue: Optional[JobQueue] = None,
    ):
        """
        Initialize the job processor

        Args:
            config: Configuration dictionary
            job_queue: Optional job queue (will create one if not provided)
        """
        # Set up notification manager
        self.notification_service = NotificationService(config)

        # Extract API configuration
        if "match_analysis" not in config:
            raise ValueError("Missing 'match_analysis' section in configuration")

        self.config = config["match_analysis"]

        # Set up job queue
        self.job_queue = job_queue or JobQueue()

        self.templater = Templater(self.config)

        # Get process count from config
        self.worker_count = self.config.get("worker_count", 1)
        self.api_timeout = self.config.get("timeout_seconds", 60)
        self.max_retries = self.config.get("max_retries", 3)
        self.retry_delay = self.config.get("retry_delay", 5)

        self.rejection_threshold = self.config.get("rejection_threshold", 2)

        if self.worker_count < 1:
            raise ValueError("Processor count must be at least 1")

    async def process_job(self, job: Dict[str, Any]) -> None:
        """
        Process a job by sending it to the API

        Args:
            job: Job data dictionary
        """

        for attempt in range(self.max_retries):
            try:
                prompt = self.templater.generate_prompt(job)
                model = LLM(self.config).get_model()

                # Ollama is a bit finnicky, so we need to retry a few times
                logger.info(
                    "Processing job: %s at %s (attempt %d)",
                    job.get("title"),
                    job.get("company"),
                    attempt + 1,
                )
                ans = await model.ainvoke(prompt)

                # Parse the ans string as JSON
                ans = json.loads(ans)

                justification = self.generate_justification(ans)

                # Create a JobListing object
                job_listing = JobListing(
                    scrape_site=job["site"],
                    scrape_name=job["source"].split(":")[0],
                    job_title=job["title"],
                    company=job["company"],
                    company_logo_url=job["company_logo"],
                    job_posting_url=job["job_url"],
                    job_requirements=ans["analysis"]["role_requirements"],
                    brief_description=ans["analysis"]["role_summary"],
                    match_justification=justification,
                    rejected=self._rating_to_score(ans["overall_match"]["rating"])
                    <= self.rejection_threshold,
                )

                # Send notification
                await self.notification_service.async_send_job_notification(job_listing)

                logger.info(
                    "Processed job: %(title)s at %(company)s",
                    {"title": job["title"], "company": job["company"]},
                )
                break
            except Exception as e:
                if attempt < self.max_retries - 1:
                    logger.error(
                        "Attempt %d error in processing job %s: %s. Retrying in %d seconds...",
                        attempt + 1,
                        job.get("title"),
                        e,
                        self.retry_delay,
                        exc_info=True,
                    )
                    await asyncio.sleep(self.retry_delay)
                else:
                    raise e

    async def _worker(self):
        """Worker task that processes jobs from the queue"""
        while True:
            try:
                # Get a job from the queue
                job = await asyncio.wait_for(self.job_queue.queue.get(), timeout=1.0)

                # Process the job
                try:
                    await self.process_job(job)
                except (
                    ValueError,
                    json.JSONDecodeError,
                    KeyError,
                    asyncio.TimeoutError,
                ) as e:
                    # Recoverable error, put job back on queue
                    logger.error("Error processing job: %s", e)
                    logger.info("Adding job back to queue: %s", e)
                    # TODO: Can't use async put due to different event loop
                    self.job_queue.put_sync(job)
                finally:
                    # Mark the job as done
                    self.job_queue.queue.task_done()
            except asyncio.TimeoutError:
                # No job available, continue loop
                pass
            except asyncio.CancelledError:
                # Worker is being cancelled
                break
            except Exception as e:
                logger.error(f"Unrecoverable error in worker: {e}", exc_info=True)

    def _run_event_loop(self):
        """Run the event loop in the current thread"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        try:
            # Create worker tasks
            workers = [
                self.loop.create_task(self._worker()) for _ in range(self.worker_count)
            ]

            logger.info(f"Job processor started with {len(workers)} workers")
            # Run until the thread is stopped
            self.loop.run_forever()

            # Cancel all tasks when loop stops
            for worker in workers:
                worker.cancel()

            # Wait for tasks to finish
            self.loop.run_until_complete(
                asyncio.gather(*workers, return_exceptions=True)
            )
        finally:
            self.loop.close()
            self.loop = None

    def start(self) -> None:
        """Start the job processor"""
        # Start a thread for the event loop
        self.thread = threading.Thread(target=self._run_event_loop, daemon=True)
        self.thread.start()

    def stop(self) -> None:
        """Stop the job processor"""
        if hasattr(self, "loop") and self.loop:
            # Schedule stopping the event loop
            asyncio.run_coroutine_threadsafe(
                asyncio.sleep(0), self.loop
            ).add_done_callback(lambda _: self.loop.stop())

            # Wait for the thread to finish
            if hasattr(self, "thread") and self.thread.is_alive():
                self.thread.join(timeout=5)

        logger.info("Job processor stopped")

    def join(self) -> None:
        """
        Check if job queue is done
        """
        # Check if the event loop is running
        if not hasattr(self, "loop") and not self.loop:
            return

        # Check if the job queue is running
        if not hasattr(self, "job_queue") and not self.job_queue:
            return

        # Wait for the job queue to finish
        future = asyncio.run_coroutine_threadsafe(
            self.job_queue.queue.join(), self.loop
        )
        future.result()  # Blocks until the queue is done

    def get_queue(self) -> JobQueue:
        """
        Get the job queue instance

        Returns:
            JobQueue: The job queue
        """
        return self.job_queue

    def generate_justification(self, ans):
        """
        Generate a justification for a job match

        Args:
            ans: Answer from the model

        Returns:
            str: Justification
        """
        return f"Match: {ans['overall_match']['rating']} - {ans['overall_match']['score']}\n{ans['overall_match']['summary']}"

    def _rating_to_score(self, rating: str) -> int:
        """
        Convert a rating to a score

        Args:
            rating: The rating to convert

        Returns:
            int: The score corresponding to the rating
        """
        return {
            "UNLIKELY": 1,
            "MARGINAL": 2,
            "COMPETITIVE": 3,
            "STRONG": 4,
            "EXECELLENT": 5,
            "POOR": 0,
            "MEDIOCRE": 2,
            "DECENT": 3,
            "GOOD": 4,
        }.get(rating.upper(), 0)


if __name__ == "__main__":
    config = {
        "match_analysis": {
            "ollama": {
                "model": "gemma3:12b-it-q4_K_M",
                "endpoint": "http://10.1.1.245:11434",
            },
            "resume_path": "resume.md",
        }
    }
    job = {
        "id": "li-4203668247",
        "site": "linkedin",
        "job_url": "https://www.linkedin.com/jobs/view/4203668247",
        "job_url_direct": "https://jobscentral.com.sg/jobs/other-jobs/903817&urlHash=uGiI",
        "title": "Backend Software Engineer, TikTok Data Ecosystem (Data Lake)",
        "company": "Jobscentral",
        "location": "",
        "date_posted": "None",
        "job_type": "fulltime",
        "salary_source": "None",
        "interval": "None",
        "min_amount": "None",
        "max_amount": "None",
        "currency": "None",
        "is_remote": False,
        "job_level": "not applicable",
        "job_function": "Engineering and Information Technology",
        "listing_type": "None",
        "emails": "nan",
        "description": "TikTok will be prioritizing applicants who have a current right to work in Singapore and do not require Tiktok's sponsorship of a visa.\n   \n\n  \n\n**About TikTok**\n TikTok is the leading destination for short\\-form mobile video. Our mission is to inspire creativity and bring joy. TikTok has global offices including Los Angeles, New York, London, Paris, Berlin, Dubai, Singapore, Jakarta, Seoul and Tokyo.\n   \n\n  \n\n Why Join Us\n   \n\n  \n\n Creation is the core of Tiktok's purpose. Our platform is built to help imaginations thrive. This is doubly true of the teams that make TikTok possible.\n   \n\n  \n\n Together, we inspire creativity and bring joy \\- a mission we all believe in and aim towards achieving every day.\n   \n\n  \n\n To us, every challenge, no matter how difficult, is an opportunity; to learn, to innovate, and to grow as one team. Status quo? Never. Courage? Always.\n   \n\n  \n\n At TikTok, we create together and grow together. That's how we drive impact \\- for ourselves, our company, and the communities we serve.\n   \n\n  \n\n Join us.\n   \n\n  \n\n**About The Team**\n The TikTok Data Ecosystem Team has the vital role of crafting and implementing a storage solution for offline data in Tiktok's recommendation system, which caters to more than a billion users. Their primary objectives are to guarantee system reliability, uninterrupted service, and seamless performance. They aim to create a storage and computing infrastructure that can adapt to various data sources within the recommendation system, accommodating diverse storage needs. Their ultimate goal is to deliver efficient, affordable data storage with easy\\-to\\-use data management tools for the recommendation, search, and advertising functions.\n   \n\n  \n\n**What You Will Be Doing**\n* Design and implement an offline/real\\-time data architecture for large\\-scale recommendation systems.\n* Design and implement a flexible, scalable, stable, and high\\-performance storage system and computation model.\n* Troubleshoot production systems, and design and implement necessary mechanisms and tools to ensure the overall stability of production systems.\n* Build industry\\-leading distributed systems such as offline and online storage, batch, and stream processing frameworks, providing reliable infrastructure for massive data and large\\-scale business systems.\n\n\n**Qualifications**\n What you should have:\n   \n\n  \n\n* Bachelor's Degree or above, majoring in Computer Science, or related fields, with 1\\+ years of experience building scalable systems;\n* Proficiency in common big data processing systems like Spark/Flink at the source code level is required, with a preference for experience in customizing or extending these systems;\n* A deep understanding of the source code of at least one data lake technology, such as Hudi, Iceberg, or DeltaLake, is highly valuable and should be prominently showcased in your resume, especially if you have practical implementation or customisation experience;\n* Knowledge of HDFS principles is expected, and familiarity with columnar storage formats like Parquet/ORC is an additional advantage;\n* Prior experience in data warehousing modeling;\n* Proficiency in programming languages such as Java, C\\+\\+, and Scala is essential, along with strong coding skills and the ability to troubleshoot effectively;\n* Experience with other big data systems/frameworks like Hive, HBase, or Kudu is a plus;\n* A willingness to tackle challenging problems without clear solutions, a strong enthusiasm for learning new technologies, and prior experience in managing large\\-scale data (in the petabyte range) are all advantageous qualities.\n\n\n TikTok is committed to creating an inclusive space where employees are valued for their skills, experiences, and unique perspectives. Our platform connects people from across the globe and so does our workplace. At TikTok, our mission is to inspire creativity and bring joy. To achieve that goal, we are committed to celebrating our diverse voices and to creating an environment that reflects the many communities we reach. We are passionate about this and hope you are too.",
        "company_industry": "Human Resources Services",
        "company_url": "https://sg.linkedin.com/company/jobscentral",
        "company_logo": "https://media.licdn.com/dms/image/v2/C4E0BAQHRIvfbIYAM8Q/company-logo_100_100/company-logo_100_100/0/1642573214889/jobscentral_logo?e=2147483647&v=beta&t=MAck3I2XPIRnur6Di6BpaOq4vDs-gA2zn9evyXQB2vI",
        "company_url_direct": "None",
        "company_addresses": "None",
        "company_num_employees": "None",
        "company_revenue": "None",
        "company_description": "None",
        "skills": "None",
        "experience_range": "None",
        "company_rating": "None",
        "company_reviews_count": "None",
        "vacancy_count": "None",
        "work_from_home_type": "None",
        "scrape_date": "2025-04-09 18:01:15",
        "search_term": "backend engineer",
        "search_location": "Singapore",
        "source": "linkedin_backend_sg:linkedin",
    }

    processer = JobMatchProcessor(ConfigManager().config)
    asyncio.run(processer.process_job(job))
