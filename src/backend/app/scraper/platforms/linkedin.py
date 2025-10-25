"""LinkedIn scraper implementation using Bright Data API."""

from typing import Optional
from app.scraper.engine_scraper import EngineScraper
from app.scraper.engines.brightdata_engine import BrightDataEngine
from app.scraper.engines.base_engine import ScrapeJob


class LinkedInScraper(EngineScraper):
    """
    Scraper for LinkedIn using Bright Data API.

    This scraper uses the Bright Data API to scrape LinkedIn posts asynchronously.
    """

    def __init__(
        self,
        url: str,
        user_id: str,
        post_limit: Optional[int] = None,
        time_limit: Optional[int] = None,
        api_key: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize LinkedIn scraper.

        Args:
            url: LinkedIn profile URL (e.g., https://www.linkedin.com/in/username)
            user_id: User identifier
            post_limit: Maximum posts to scrape
            time_limit: Not used for API-based scraping
            api_key: Bright Data API key (optional, defaults to env var)
            **kwargs: Additional parameters
        """
        # Initialize Bright Data engine
        engine = BrightDataEngine(api_key=api_key)

        # Call parent constructor
        super().__init__(
            engine=engine,
            url=url,
            user_id=user_id,
            platform="linkedin",
            post_limit=post_limit,
            time_limit=time_limit,
            **kwargs
        )

    def scrape(self) -> ScrapeJob:
        """
        Start scraping LinkedIn posts.

        This is an asynchronous operation. The method returns immediately
        with a job that can be polled for status and results.

        Returns:
            ScrapeJob with job_id and initial status
        """
        return super().scrape()
