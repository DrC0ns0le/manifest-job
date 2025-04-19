import json
import requests
import aiohttp
from model.job_listing import JobListing
from push_notification.manager import NotificationProvider


class MattermostManager(NotificationProvider):
    """
    Class to manage Mattermost notifications
    """

    def __init__(self, config):
        """
        Initialize the MattermostManager with a webhook URL and optional username

        Args:
            config: A dictionary containing the configuration

        Raises:
            ValueError: If the webhook URL is not provided or is not a string
        """
        webhook_url = config.get("webhook_url")
        username = config.get("username", "Job Notification Bot")

        if not webhook_url:
            raise ValueError("Mattermost webhook URL must be provided")
        if not isinstance(webhook_url, str):
            raise ValueError("Mattermost webhook URL must be a string")

        self.webhook_url = webhook_url
        self.username = username
        self.channel = config.get("channel", None)
        self.rejection_channel = config.get("rejection_channel", None)

    def _generate_message(self, job: JobListing):
        """
        Generate a formatted message for the job listing

        Args:
            job: A JobListing object containing the job details

        Returns:
            A formatted string with the job information
        """
        return f"""
# **{job.job_title}**

{job.job_posting_url}

**Requirements:**
{job.job_requirements}

**Description:**  
{job.brief_description}

**Justification:**  
{job.match_justification}

**Scrape Name:** {job.scrape_name}
        """

    def _create_payload(self, job: JobListing):
        """
        Create the payload for the Mattermost webhook

        Args:
            job: A JobListing object containing the job details

        Returns:
            A dictionary containing the payload
        """
        text = self._generate_message(job)

        # Prepare the payload
        payload = {
            "text": text,
            "username": job.company,
            "icon_url": job.company_logo_url,
        }

        if self.channel:
            payload["channel"] = self.channel

        if self.rejection_channel and job.rejected:
            payload["channel"] = self.rejection_channel

        return payload, text

    def send_job_notification(self, job: JobListing):
        """
        Send a notification about a job listing to the specified Mattermost channel
        """
        payload, text = self._create_payload(job)

        # Send the request
        headers = {"Content-Type": "application/json"}
        response = requests.post(
            self.webhook_url, headers=headers, data=json.dumps(payload)
        )

        # print(f"Sent notification to Mattermost:\n{text}\n")
        return response

    async def async_send_job_notification(self, job: JobListing):
        """
        Asynchronously send a notification about a job listing to the specified Mattermost channel

        Args:
            job: A JobListing object containing the job details

        Returns:
            The response from the Mattermost API
        """
        payload, text = self._create_payload(job)

        # Send the request asynchronously
        headers = {"Content-Type": "application/json"}

        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.webhook_url, headers=headers, json=payload
            ) as response:
                # Wait for the response
                result = await response.text()
                status = response.status

                # print(
                #     f"Asynchronously sent notification to Mattermost (status {status}):\n{text}\n"
                # )

                # Return a response-like object with the results
                return {
                    "status_code": status,
                    "text": result,
                    "ok": 200 <= status < 300,
                }


if __name__ == "__main__":
    # Example usage
    mattermost_manager = MattermostManager(
        {"webhook_url": "https://example.com/webhook"}
    )

    job = JobListing(
        scrape_site="indeed",
        scrape_name="software_eng",
        job_title="Software Engineer",
        brief_description="Company seeks a Software Engineer to design, develop, and maintain innovative software across web, mobile, and backend platforms. The role involves working on diverse projects, collaborating with cross-functional teams, leveraging data analytics and automation, managing cloud infrastructure, and ensuring quality through testing.",
        match_justification="DECENT - 48\nThe candidate demonstrates good alignment with the backend development aspects of the role and has a strong educational background. However, the lack of experience with key technologies like Swift/Kotlin and limited overall professional experience significantly hinders their fit.  The candidate's overall score is pulled down by the required tech skills gap, along with the lack of equivalent experience to match the expectations for this Software Engineer position. The lack of direct mobile development experience also contributes to this assessment.",
        job_posting_url="https://example.com/jobs/123",
        job_requirements="Bachelor's degree in Computer Science/Engineering, Proficiency in Python, Swift, Kotlin, Java, React, Angular, Vue.js, AWS, Azure, GCP, CI/CD pipelines, Experience with data processing, and software testing methodologies.",
        company="Company",
        company_logo_url="https://www.example.com/favicon.ico",
    )

    mattermost_manager.send_job_notification(job)
