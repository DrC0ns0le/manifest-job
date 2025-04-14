"""
Environment variable mapping for configuration
"""

# Mapping from environment variables to configuration paths
ENV_MAPPING = {
    "PUSH_NOTIFICATION_TELEGRAM_TOKEN": "push_notification.telegram.token",
    "PUSH_NOTIFICATION_TELEGRAM_CHAT_ID": "push_notification.telegram.chat_id",
    "PUSH_NOTIFICATION_MATTERMOST_WEBHOOK_URL": "push_notification.mattermost.webhook_url",
    "JOB_SCRAPER_RUN_INTERVAL": "job_scraper.scraper_config.run_interval",
    "JOB_SCRAPER_PARALLEL": "job_scraper.scraper_config.parallel",
    "MATCH_ANALYSIS_OLLAMA_MODEL": "match_analysis.ollama.model",
    "MATCH_ANALYSIS_OLLAMA_ENDPOINT": "match_analysis.ollama.endpoint",
    "JOB_SCRAPER_DATABASE_CSV_PATH": "job_scraper.database.csv_path",
    "JOB_SCRAPER_CLEANUP_DAYS": "job_scraper.database.cleanup_days",
}
