import pandas as pd
import logging
from jobspy import scrape_jobs
from datetime import datetime
from job_scraper.database import JobDatabase
from match_analysis.queue import JobQueue

# Configure logging
logging.basicConfig(
    filename="job_scraper.log",
    filemode="a",
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


class JobScraper:
    """
    Handles job scraping operations
    """

    def __init__(self, config, queue: JobQueue = None, name=None):
        self.config = config

        # Validate scraping config
        if "scraping" not in config:
            raise ValueError("Missing 'scraping' section in configuration")

        self.scrape_config = config["scraping"]

        # Get name from config or use provided name
        self.name = name
        self.logger = logging.getLogger(f"job_scraper.{self.name}")

        # Validate required fields
        required_fields = [
            "site_name",
            "search_term",
            "location",
            "results_wanted",
            "hours_wanted",
        ]
        for field in required_fields:
            if field not in self.scrape_config:
                raise ValueError(
                    f"Missing required field '{field}' in scraping configuration for {self.name}"
                )

        # Initialize database
        if "database" not in config:
            raise ValueError(
                f"Missing 'database' section in configuration for {self.name}"
            )

        db_config = config["database"]

        if "csv_path" not in db_config or "cleanup_days" not in db_config:
            raise ValueError(
                f"Missing required fields in database configuration for {self.name}"
            )

        self.database = JobDatabase(db_config["csv_path"], db_config["cleanup_days"])

        # Store queue service reference for sending jobs
        self.queue = queue

    def scrape_jobs(self):
        """Scrape jobs based on configuration"""
        site_name = self.scrape_config["site_name"]
        search_term = self.scrape_config["search_term"]
        location = self.scrape_config["location"]
        results_wanted = self.scrape_config["results_wanted"]
        hours_wanted = self.scrape_config["hours_wanted"]
        proxies = self.scrape_config.get("proxies", None)
        linkedin_fetch_description = self.scrape_config.get(
            "linkedin_fetch_description", True
        )
        country_indeed = self.scrape_config.get("country_indeed", None)
        verbose = self.scrape_config.get("verbose", False)

        self.logger.info(
            f"Scraping {results_wanted} '{search_term}' jobs from {site_name} in {location}"
        )

        # Use JobSpy to scrape jobs
        jobs = scrape_jobs(
            site_name=site_name,
            search_term=search_term,
            location=location,
            results_wanted=results_wanted,
            hours_old=hours_wanted,
            linkedin_fetch_description=linkedin_fetch_description,
            proxies=proxies,
            country_indeed=country_indeed if site_name == "indeed" else "worldwide",
            verbose=verbose,
        )

        # Add timestamp for when we scraped this data
        jobs_df = jobs
        current_time = datetime.now()
        jobs_df["scrape_date"] = current_time.strftime("%Y-%m-%d %H:%M:%S")

        # Add source information to identify which scraper found the job
        jobs_df["search_term"] = search_term
        jobs_df["search_location"] = location
        jobs_df["source"] = f"{self.name}:{site_name}"

        return jobs_df

    def filter_jobs(self, jobs_df):
        """Filter jobs based on configuration"""
        filters = set(
            self.scrape_config.get("global_scraper_config", {}).get(
                "title_blacklisted_keywords", []
            )
        )

        if len(filters) > 0:
            jobs_df = jobs_df[
                ~jobs_df["title"].str.contains(
                    "|".join(filters), case=False, regex=True
                )
            ]

        return jobs_df

    def update_database(self, new_jobs_df):
        """Update database with newly scraped jobs"""
        new_jobs = pd.DataFrame()

        if new_jobs_df.empty:
            self.logger.info("No jobs found in current scrape")
            return new_jobs

        if not self.database.exists():
            # If CSV doesn't exist or is empty, create it with all scraped jobs
            new_jobs = new_jobs_df
            self.database.save(new_jobs_df)
            self.logger.info(f"Created new CSV with {len(new_jobs_df)} job postings")
            return new_jobs

        # Load existing jobs
        existing_jobs = self.database.load()

        # Clean up old job listings
        existing_jobs, old_jobs_count = self.database.clean_old_jobs(existing_jobs)

        # Identify new job postings by comparing job URLs
        new_jobs = new_jobs_df[~new_jobs_df["job_url"].isin(existing_jobs["job_url"])]

        if len(new_jobs) == 0:
            self.logger.info("No new job postings found")

            # Even if no new jobs, we may still need to update the CSV if old jobs were removed
            if old_jobs_count > 0:
                self.database.save(existing_jobs)
                self.logger.info(
                    f"Updated CSV after removing old job postings. Total jobs: {len(existing_jobs)}"
                )
            return new_jobs

        self.logger.info(f"Found {len(new_jobs)} new job postings!")
        self.logger.info("New job postings:")
        for _, job in new_jobs.iterrows():
            self.logger.info(f"{job['title']} at {job['company']} in {job['location']}")

        # Append new jobs to existing CSV
        combined_jobs = pd.concat([existing_jobs, new_jobs])
        self.database.save(combined_jobs)
        self.logger.info(
            f"Updated CSV with new job postings. Total jobs: {len(combined_jobs)}"
        )

        return new_jobs

    def send_to_queue(self, new_jobs):
        """Send new jobs to the queue"""
        if self.queue is None:
            raise ValueError("Queue is not initialized")

        if new_jobs.empty:
            return

        self.logger.info(f"Sending {len(new_jobs)} jobs to the queue...")
        for _, job in new_jobs.iterrows():
            # Convert pandas series to dict
            job_dict = job.to_dict()
            # Add job to queue
            self.queue.put_sync(job_dict)
        self.logger.info("All jobs sent to queue")

    def run(self):
        """Run the complete scraping and updating process"""
        try:
            self.logger.info(f"Starting job scraper {self.name}")

            jobs_df = self.scrape_jobs()
            filtered_jobs_df = self.filter_jobs(jobs_df)
            new_jobs = self.update_database(filtered_jobs_df)

            self.send_to_queue(new_jobs)
            self.logger.info(f"Completed job scraper {self.name}")
            return new_jobs
        except Exception as e:
            self.logger.error(f"Error in job scraper {self.name}: {e}", exc_info=True)
            raise e
