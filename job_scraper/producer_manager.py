"""
Producer manager for coordinating multiple job scrapers
"""

import logging
import concurrent.futures
from typing import Dict, Any

from job_scraper.scraper import JobScraper
from match_analysis.queue import JobQueue

# Configure logging
logging.basicConfig(
    filename="job_scraper.log",
    filemode="a",
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("producer_manager")


class ProducerManager:
    """
    Manages multiple job scrapers (producers) that feed into a single queue
    """

    def __init__(self, config: Dict[str, Any], queue: JobQueue):
        """
        Initialize the producer manager

        Args:
            config: Configuration dictionary
            queue: The queue to use for sending jobs
        """
        self.config = config
        self.queue = queue
        self.scrapers = []

        # Validate scraper config
        if "scrapers" not in config:
            raise ValueError("No scrapers found in configuration")

        # Get database config
        if "database" not in config:
            raise ValueError("Missing 'database' section in configuration")

        db_config = config["database"]

        # Initialize scrapers for each configuration in the list
        for scraper_config in config["scrapers"]:
            # Create a copy of scraper config with database info
            complete_config = {
                "scraping": scraper_config,
                "database": db_config,
            }

            if "scraper_config" in config:
                complete_config["global_scraper_config"] = config["scraper_config"]

            # Get name from config or use a default
            name = scraper_config.get("name", f"scraper_{len(self.scrapers)+1}")

            # Create and add the scraper
            scraper = JobScraper(complete_config, self.queue, name=name)
            self.scrapers.append(scraper)

        logger.info(f"Initialized {len(self.scrapers)} job scrapers")

    def run_sequential(self) -> None:
        """Run all scrapers sequentially"""
        logger.info("Running scrapers sequentially")
        for idx, scraper in enumerate(self.scrapers):
            logger.info(
                f"Starting scraper {idx+1} of {len(self.scrapers)}: {scraper.name}"
            )
            scraper.run()

    def run_parallel(self) -> None:
        """
        Run all scrapers in parallel

        Uses ThreadPoolExecutor from concurrent.futures to run scrapers in parallel
        Threading is used to run each scraper in a separate thread, asyncio is not possible due to jobspy
        """
        max_workers = self.config.get("scraper_config", {}).get(
            "max_workers", len(self.scrapers)
        )
        logger.info(f"Running scrapers in parallel with {max_workers} workers")

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all scraper jobs
            futures = [executor.submit(scraper.run) for scraper in self.scrapers]

            # Wait for all to complete
            for _, future in enumerate(concurrent.futures.as_completed(futures)):
                try:
                    future.result()
                except Exception as e:
                    logger.error(f"Scraper failed with error: {e}")
