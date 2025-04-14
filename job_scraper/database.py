import pandas as pd
import os

from datetime import datetime, timedelta


class JobDatabase:
    """
    Manages job data storage and retrieval
    """

    def __init__(self, csv_path, cleanup_days):
        if not csv_path:
            raise ValueError("Missing CSV path for job database")

        if not isinstance(cleanup_days, int) or cleanup_days < 0:
            raise ValueError("cleanup_days must be a positive integer")

        self.csv_path = csv_path
        self.cleanup_days = cleanup_days

    def exists(self):
        """Check if database exists and has data"""
        return os.path.exists(self.csv_path) and os.path.getsize(self.csv_path) > 0

    def load(self):
        """Load jobs from database"""
        if not self.exists():
            return pd.DataFrame()

        jobs_df = pd.read_csv(self.csv_path)
        jobs_df["scrape_date"] = pd.to_datetime(jobs_df["scrape_date"])
        return jobs_df

    def save(self, jobs_df):
        """Save jobs to database"""
        jobs_df.to_csv(self.csv_path, index=False)

    def clean_old_jobs(self, jobs_df):
        """Remove jobs older than cleanup_days"""
        if jobs_df.empty:
            return jobs_df, 0

        cutoff_date = datetime.now() - timedelta(days=self.cleanup_days)
        old_jobs_count = len(jobs_df[jobs_df["scrape_date"] < cutoff_date])
        if old_jobs_count > 0:
            jobs_df = jobs_df[jobs_df["scrape_date"] >= cutoff_date]
            print(
                f"Removed {old_jobs_count} job postings older than {self.cleanup_days} days."
            )

        return jobs_df, old_jobs_count
