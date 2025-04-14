import jinja2
from typing import Dict, Any


class Templater:
    def __init__(self, config):
        if "resume_path" not in config:
            raise ValueError("Missing 'resume' section in configuration")

        self.resume = config["resume_path"]
        self.user_prompt_path = config.get("preference_prompt_path", None)

    def generate_prompt(self, job: Dict[str, Any], template: str = "default") -> str:
        """
        Generate prompt from template

        Args:
            template: Template name

        Returns:
            str: Generated prompt
        """
        # Load user prompt
        user_prompt = None
        if self.user_prompt_path:
            try:
                with open(self.user_prompt_path, "r", encoding="utf-8") as file:
                    user_prompt = file.read()
            except FileNotFoundError as exc:
                raise ValueError(
                    f"User prompt {self.user_prompt_path} not found"
                ) from exc

        if user_prompt and template == "default":
            template = "v2"
        # Load template
        try:
            with open(f"templates/prompt_{template}.j2", "r", encoding="utf-8") as file:
                template = file.read()
        except FileNotFoundError as exc:
            raise ValueError(f"Template prompt_{template} not found") from exc

        # Load resume
        try:
            with open(self.resume, "r", encoding="utf-8") as file:
                resume = file.read()
        except FileNotFoundError as exc:
            raise ValueError(f"Resume {self.resume} not found") from exc

        job_text = self._generate_job_text(job)

        # Use Template.from_string to preserve escaping
        jinja_template = jinja2.Template(
            template, autoescape=False, keep_trailing_newline=True
        )

        # Render template
        rendered = jinja_template.render(
            resume_text=resume,
            job_posting_text=job_text,
            candidate_preferences=user_prompt.strip() if user_prompt else None,
        )

        return rendered

    def _generate_job_text(self, job: Dict[str, Any], template: str = "default") -> str:
        """
        Generate job text from job dictionary

        Args:
            job: Job dictionary

        Returns:
            str: Generated job text
        """

        # Load template
        try:
            with open(f"templates/job_{template}.j2", "r", encoding="utf-8") as file:
                template = file.read()
        except FileNotFoundError as exc:
            raise ValueError(f"Template job_{template} not found") from exc

        # Render template
        rendered = jinja2.Template(template).render(job)

        return rendered


if __name__ == "__main__":
    config = {
        "resume_path": "resume.md",
        "user_prompt": "I am looking for a job in the IT industry",
        "job": {
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
        },
    }
    templater = Templater(config)
    prompt = templater.generate_prompt(config["job"])
    print(prompt)
