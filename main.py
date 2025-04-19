"""
Main application module for job scraper system
"""

import logging
import signal
import sys
import time as time_module
from configuration import ConfigManager

from job_scraper.producer_manager import ProducerManager

from match_analysis.processor import JobMatchProcessor

from datetime import datetime, time, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("job_scraper.log"), logging.StreamHandler()],
)
logger = logging.getLogger("app")


class JobSystem:
    """
    Main application class that orchestrates the job scraping system
    """

    def __init__(self, config_manager):
        """
        Initialize the job system

        Args:
            config_manager: Configuration manager instance
        """
        if "job_scraper" not in config_manager.config:
            raise ValueError("Missing 'job_scraper' section in configuration")

        self.config = config_manager.config

        # Initialize the job processor (consumer)
        self.job_processor = JobMatchProcessor(self.config)

        # Initialize the producer manager
        self.producer_manager = ProducerManager(
            self.config["job_scraper"], self.job_processor.get_queue()
        )

        logger.info("Job system initialized")

        self.shutdown_requested = False

        # Register signal handlers
        signal.signal(signal.SIGTERM, self.handle_shutdown)
        signal.signal(signal.SIGINT, self.handle_shutdown)

    def run_producers(self):
        """
        Run the job producers (scrappers) once
        """
        logger.info("Starting producers")

        # Get parallel config, default to False
        parallel = (
            self.config["job_scraper"].get("scraper_config", {}).get("parallel", False)
        )

        # Run all producers (scrapers)
        if parallel:
            self.producer_manager.run_parallel()
        else:
            self.producer_manager.run_sequential()

        logger.info("All producers completed")

    def run_consumer(self):
        """Start the job consumer"""
        logger.info("Starting consumer")
        self.job_processor.start()

    def stop_consumer(self):
        """Stop the job consumer"""
        logger.info("Stopping consumer")
        self.job_processor.stop()

    def run(self):
        """
        Run the complete job system
        """
        logger.info("Starting job system")

        # Start the consumer
        self.run_consumer()

        run_interval = (
            self.config.get("job_scraper", {})
            .get("scraper_config", {})
            .get("run_interval", None)
        )

        # Main loop
        # The scrapers will execute at regular intervals
        # The consumer will process the job postings
        # Upon receiving a keyboard interrupt, the scrapers will be stopped, while waiting for the consumer to finish
        # On the second interrupt, the scrapers will be stopped immediately
        try:
            while True:
                try:
                    # Check if it's time to run the producers (only if not in blocked period)
                    if not is_current_time_in_range(
                        self.config.get("job_scraper", {})
                        .get("scraper_config", {})
                        .get("blocked_period", "0000-0000")
                    ):
                        # Run the producers
                        self.run_producers()
                    else:
                        logger.info(
                            "Skipping producer run as it's in blocked period: %s",
                            self.config.get("job_scraper", {})
                            .get("scraper_config", {})
                            .get("blocked_period", "0000-0800"),
                        )

                    # Check if shutdown is requested
                    if self.shutdown_requested:
                        logger.info("Shutdown requested, breaking main loop")
                        break

                    # Wait for the run interval
                    if run_interval:
                        next_run_time = datetime.now() + timedelta(seconds=run_interval)
                        logger.info(
                            "Waiting for %d seconds before next run, which is %s",
                            run_interval,
                            next_run_time.strftime("%Y-%m-%d %H:%M:%S"),
                        )
                        time_module.sleep(run_interval)

                    # Analyze the job postings
                    # self.analyze_jobs()
                except KeyboardInterrupt:
                    # This is now handled by the signal handler
                    pass
        finally:
            # Wait for the consumer to finish processing current jobs
            self.wait_for_consumer()
            # Stop the consumer
            self.stop_consumer()
            logger.info("Job system shutdown complete")

    def handle_shutdown(self, signum, frame):
        """Signal handler for graceful shutdown"""
        sig_name = "SIGTERM" if signum == signal.SIGTERM else "SIGINT"
        if not self.shutdown_requested:
            logger.info(f"{sig_name} received. Initiating graceful shutdown...")
            self.shutdown_requested = True
        else:
            logger.info(f"Second {sig_name} received. Exiting immediately.")
            sys.exit(1)

    def wait_for_consumer(self):
        """
        Wait for the consumer to finish processing all jobs in the queue
        """
        logger.info("Waiting for consumer to finish processing...")
        self.job_processor.join()
        logger.info("Consumer finished processing all jobs")


def main(config_path="config.yaml"):
    """
    Main entry point for the application

    Args:
        config_path: Path to configuration file
    """
    try:
        # Load configuration
        config_manager = ConfigManager(config_path=config_path)

        # Create and run job system
        system = JobSystem(config_manager)
        system.run()

    except Exception as e:
        logger.error(f"Error running job system: {e}", exc_info=True)


def is_current_time_in_range(time_range: str):
    """
    Check if the current time is within the specified time range.

    Args:
        time_range_str: A string in format "XXXX-YYYY" where X and Y are military time (24-hour format)

    Returns:
        bool: True if current time is within the range, False otherwise
    """
    if time_range == "0000-0000":
        return False
    # Parse the time range
    start_str, end_str = time_range.split("-")

    # Create time objects directly
    start_time = time(int(start_str[:2]), int(start_str[2:]))
    end_time = time(int(end_str[:2]), int(end_str[2:]))

    # Get current time (just the time component)
    current_time = datetime.now().time()

    # Check if current time is within range
    if start_time <= end_time:
        # Normal case: start time is before end time (e.g., 0800-1700)
        return start_time <= current_time <= end_time
    else:
        # Overnight case: start time is after end time (e.g., 2200-0600)
        return current_time >= start_time or current_time <= end_time


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Job scraper and analysis system")
    parser.add_argument(
        "--config", default="config.yaml", help="Path to configuration file"
    )
    args = parser.parse_args()

    # Application entry point
    main(config_path=args.config)
