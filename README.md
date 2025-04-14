# Manifest Job

Manifest Job is an automated job scraping and matching system that helps candidates find relevant job opportunities. It scrapes job listings from multiple sources, analyzes them against your resume, and sends notifications for relevant matches.

May this tool help us manifest our dream job in this rough times.

## Features

- **Multi-source Job Scraping**: Configurable scrapers for LinkedIn, Indeed, and other job sites
- **Resume Matching**: LLM-powered analysis to match job postings with your resume and preferences
- **Notification System**: Get alerts for relevant job opportunities via Telegram or Mattermost
- **Containerized Deployment**: Easy deployment using Docker and docker-compose
- **Configurable**: Highly customizable settings via YAML configuration and environment variables

## How It Works

Manifest Job follows a pipeline approach to discover, analyze, and notify you about relevant job opportunities:

1. **Job Scraping**: The system periodically scrapes configured job sites (LinkedIn, Indeed, etc.) based on your specified search terms, locations, and other criteria.

2. **Database Management**: 
   - Newly scraped jobs are compared against the existing database (stored in CSV format)
   - Only new job listings are added to the database
   - Older job listings (configurable, default 7 days) are automatically cleaned up

3. **Job Processing**:
   - New job listings are sent to a processing queue
   - Each job is analyzed against your resume using AI inference
   - The system evaluates the match quality based on skills, experience, and requirements

4. **Notification**:
   - Jobs that pass the analysis phase trigger notifications
   - Detailed information about the job and match quality is sent via your configured notification channels

The system runs on a configurable schedule and can be set to avoid scraping during certain hours to prevent rate limiting or IP blocking.

## Setup & Installation

### Prerequisites

- Python 3.11 or higher
- Docker and docker-compose (for containerized deployment)
- An Ollama model instance for the AI matching capabilities

### Local Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/manifest-job.git
   cd manifest-job
   ```

2. Create and activate a virtual environment:
   ```bash
   ./activate_venv.sh
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create your resume file:
   ```bash
   # Create a resume.md file in the project root
   touch resume.md
   # Edit this file with your resume information
   ```

5. (Optional) Create a preference file to guide the job matching process:
   ```bash
   # Create a preference.md file
   touch preference.md
   # Edit with your job preferences and criteria
   ```

6. Configure your settings by modifying `config.yaml` according to your needs

### Docker Deployment

1. Configure your settings in `config.yaml`

2. Create an `.env` file for environment-specific settings (optional):
   ```bash
   # Example .env file
   PUSH_NOTIFICATION_TELEGRAM_TOKEN=your_telegram_bot_token
   PUSH_NOTIFICATION_TELEGRAM_CHAT_ID=your_chat_id
   MATCH_ANALYSIS_OLLAMA_ENDPOINT=http://your-ollama-host:11434
   ```

3. Deploy with docker-compose:
   ```bash
   docker-compose up -d
   ```

## Configuration

The system is configured through `config.yaml`. Key configuration sections:

- **job_scraper**: Configure job scraping sources and parameters
  - **database**: Database settings
  - **scrapers**: List of scraper configurations
  - **scraper_config**: General scraper settings

- **match_analysis**: Configure the AI-based job matching system
  - **ollama**: Model settings
  - **resume_path**: Path to your resume file
  - **preference_prompt_path**: Path to your preferences file

- **push_notification**: Configure notification services
  - **telegram**: Telegram bot settings
  - **mattermost**: Mattermost webhook settings

## Usage

### Running the Application

For local development:
```bash
python main.py
```

With a custom config file:
```bash
python main.py --config my_config.yaml
```

Using Docker:
```bash
docker-compose up -d
```

### Adding New Job Sources

Add new scrapers in the `config.yaml` file under the `job_scraper.scrapers` section, following the existing format.

### Customizing Matching Logic

The matching logic is implemented using templates in the `templates/` directory. You can customize:
- `prompt_default.j2`: The prompt used for job matching
- `job_default.j2`: The template for job formatting

## System Architecture

- **job_scraper**: Scrapes job listings from multiple sources
- **match_analysis**: Analyzes job postings against your resume
- **push_notification**: Sends notifications for matching jobs
- **configuration**: Manages application configuration

## Upcoming Features

- **OpenAI Integration**: Support for OpenAI and other LLM providers beyond Ollama
- **Notification Filtering**: Customizable filtering system to control which jobs trigger notifications based on match quality, salary range, and other criteria
- More to come!

## Contributors

- **DrC0ns0le** ([@DrC0ns0le](https://github.com/DrC0ns0le)) - Project creator and lead developer
- **Rowen** ([@RowenTey](https://github.com/RowenTey)) - Lead developer

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Acknowledgments

We extend our gratitude to the open source community for their invaluable contributions and ongoing support. This project owes its existence to libraries like [JobSpy](https://github.com/speedyapply/JobSpy) for making job scraping a breeze. We also acknowledge the local LLM community, particularly [Ollama](https://github.com/ollama/ollama), and all individuals and organizations that provide open-weight LLM models.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
