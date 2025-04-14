from abc import ABC, abstractmethod

from model import JobListing


class NotificationProvider(ABC):
    """
    Abstract base class for managing configuration settings
    """

    @abstractmethod
    def send_job_notification(self, job: JobListing):
        """
        Abstract method to send notifications about job listings
        """
        raise NotImplementedError("Subclasses should implement this method")

    @abstractmethod
    def async_send_job_notification(self, job: JobListing):
        """
        Abstract method to asynchronously send notifications about job listings
        """
        raise NotImplementedError("Subclasses should implement this method")
