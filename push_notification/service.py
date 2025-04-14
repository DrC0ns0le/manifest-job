from model.job_listing import JobListing
from push_notification.mattermost import MattermostManager
from push_notification.telegram import TelegramManager


class NotificationService:
    def __init__(self, config):
        """
        Initialize the notification service with a configuration dictionary

        Args:
            config: A configuration dictionary with a "push_notification" section

        Raises:
            ValueError: If the configuration is invalid
        """
        if "push_notification" not in config:
            raise ValueError("Missing 'push_notification' section in configuration")

        self.config = config["push_notification"]

        self.notification_providers = {}

        if self.config is None:
            raise ValueError("No notification providers configured")
        for provider in self.config:
            if provider == "mattermost":
                self.notification_providers[provider] = MattermostManager(
                    self.config[provider]
                )
            elif provider == "telegram":
                self.notification_providers[provider] = TelegramManager(
                    self.config[provider]
                )
            else:
                raise ValueError(f"Unknown notification provider: {provider}")

        if len(self.notification_providers) == 0:
            raise ValueError("No notification providers configured")

    async def async_send_job_notification(self, job: JobListing):
        """
        Asynchronously send a notification about a job listing to all configured providers.

        Args:
            job: A JobListing object containing the job details
        """

        for provider, _ in self.notification_providers.items():
            await self.notification_providers[provider].async_send_job_notification(job)
