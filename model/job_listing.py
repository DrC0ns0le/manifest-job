from pydantic import BaseModel


class JobListing(BaseModel):
    scrape_site: str
    scrape_name: str
    job_title: str
    company: str
    company_logo_url: str
    job_requirements: str
    brief_description: str
    match_justification: str
    job_posting_url: str
