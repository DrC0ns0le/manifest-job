import json
import aiohttp
import requests
from model.job_listing import JobListing
from push_notification.manager import NotificationProvider


class TelegramManager(NotificationProvider):
    """
    Class to manage Telegram notifications
    """

    def __init__(self, config):
        """
        Initialize the TelegramManager with a bot token and chat ID
        """
        token = config.get("token", None)
        chat_id = config.get("chat_id", None)
        if not token or not chat_id:
            raise ValueError("Telegram bot token and chat ID must be provided")

        if not isinstance(token, str):
            raise ValueError("Telegram bot token must be string")

        if not isinstance(chat_id, int):
            raise ValueError("Telegram chat ID must be a number")

        self.token = token
        self.chat_id = chat_id

    def send_job_notification(self, job: JobListing):
        """
        Send a notification about a job listing to the specified Telegram chat
        """
        text = f""" 
New Job Posting ‼️    

Job Title: {job.job_title}
Company: {job.company}
URL: {job.job_posting_url}

Description: 
{job.brief_description}

Justification: 
{job.match_justification}
        """

        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        headers = {"Content-Type": "application/json"}
        data = {"chat_id": self.chat_id, "text": text}
        response = requests.post(url, headers=headers, data=json.dumps(data))
        print(f"Sent notification to Telegram:\n{text}\n")
        return response

    async def async_send_job_notification(self, job: JobListing):
        """
        Asynchronously send a notification about a job listing to the specified Telegram chat

        Args:
            job: A JobListing object containing the job details

        Returns:
            The response from the Mattermost API
        """
        text = f""" 
New Job Posting ‼️    

Job Title: {job.job_title}
Company: {job.company}
URL: {job.job_posting_url}

Description: 
{job.brief_description}

Justification: 
{job.match_justification}
        """

        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        headers = {"Content-Type": "application/json"}
        data = {"chat_id": self.chat_id, "text": text}

        # Send the request asynchronously
        headers = {"Content-Type": "application/json"}

        async with aiohttp.ClientSession() as session:
            async with session.post(
                url, headers=headers, json=json.dumps(data)
            ) as response:
                return response
