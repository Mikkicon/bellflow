"""
Multi-platform social media scraper.

Supports scraping posts from various social media platforms with
session persistence and configurable limits.
"""

from app.scraper.platforms.threads import ThreadsScraper
from app.scraper.platforms.twitter import TwitterScraper
from app.scraper.platforms.x import XScraper
from app.scraper.platforms.linkedin import LinkedInScraper
from app.scraper.session_manager import SessionManager
from app.scraper.job_manager import JobManager, job_manager
from app.scraper.engines.base_engine import ScrapeJob, JobStatus

__all__ = [
    'ThreadsScraper',
    'TwitterScraper',
    'XScraper',
    'LinkedInScraper',
    'SessionManager',
    'JobManager',
    'job_manager',
    'ScrapeJob',
    'JobStatus'
]
