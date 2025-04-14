import os
import pandas as pd


class JobAnalyzer:
    """
    Analyzes job postings data to provide insights
    """

    def __init__(self, config):
        # Initialize database
        if "database" not in config:
            raise ValueError("Missing 'database' section in configuration")

        db_config = config["database"]
        if "csv_path" not in db_config:
            raise ValueError("Missing required fields in database configuration")

        self.csv_path = db_config["csv_path"]

    def analyze(self):
        """Analyze job database and print insights"""
        if not os.path.exists(self.csv_path) or os.path.getsize(self.csv_path) == 0:
            print("No job database found or the database is empty.")
            return

        jobs_df = pd.read_csv(self.csv_path)
        jobs_df["scrape_date"] = pd.to_datetime(jobs_df["scrape_date"])

        # Get some basic stats
        print("\nJob Database Analysis:")
        print(f"Total jobs in database: {len(jobs_df)}")

        # Most common companies
        company_counts = jobs_df["company"].value_counts().head(5)
        print("\nTop companies with job postings:")
        for company, count in company_counts.items():
            print(f"- {company}: {count} postings")

        # Most recent jobs
        recent_jobs = jobs_df.sort_values("scrape_date", ascending=False).head(5)
        print("\nMost recently added job postings:")
        for i, job in recent_jobs.iterrows():
            print(
                f"- {job['title']} at {job['company']} ({job['scrape_date'].strftime('%Y-%m-%d')})"
            )
