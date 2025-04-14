"""
Queue implementation for job processing
"""

import asyncio
import logging
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("job_queue")


class JobQueue:
    """
    Asynchronous queue for job processing
    """

    def __init__(self, max_size: int = 100):
        """
        Initialize job queue

        Args:
            max_size: Maximum queue size
        """
        self.queue = asyncio.Queue(maxsize=max_size)
        self.running = False

    def put_sync(self, job: Dict[str, Any]) -> None:
        """
        Synchronously add a job to the queue

        Args:
            job: Job data dictionary
        """

        # Create a new event loop if needed
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        try:
            # Run the put operation using our async put method which handles logging
            if loop.is_running():
                future = asyncio.run_coroutine_threadsafe(self.put(job), loop)
                # Wait for the result to ensure it completes
                future.result(timeout=5)
            else:
                loop.run_until_complete(self.put(job))

        except Exception as e:
            logger.error(f"Error adding job to queue: {e}", exc_info=True)

    async def put(self, job: Dict[str, Any]) -> None:
        """
        Asynchronously add a job to the queue

        Args:
            job: Job data dictionary
        """
        await self.queue.put(job)
        logger.debug(f"Added job to queue: {job.get('title')} at {job.get('company')}")

    def empty(self) -> bool:
        """
        Check if the queue is empty

        Returns:
            True if the queue is empty, False otherwise
        """
        return self.queue.empty()
