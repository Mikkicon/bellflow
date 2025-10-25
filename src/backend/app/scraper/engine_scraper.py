"""Engine-based scraper wrapper for API-based platforms."""

from typing import Dict, Optional
from app.scraper.engines.base_engine import BaseScraperEngine, ScrapeJob


class EngineScraper:
    """
    Simple wrapper for engine-based scrapers.

    This class provides a unified interface for scrapers that use
    engines (Playwright or API-based) for data collection.
    """

    def __init__(
        self,
        engine: BaseScraperEngine,
        url: str,
        user_id: str,
        platform: str,
        post_limit: Optional[int] = None,
        time_limit: Optional[int] = None,
        **kwargs
    ):
        """
        Initialize the engine scraper.

        Args:
            engine: Scraper engine to use
            url: Profile URL to scrape
            user_id: User identifier
            platform: Platform name
            post_limit: Maximum posts
            time_limit: Maximum time
            **kwargs: Additional parameters
        """
        self.engine = engine
        self.url = url
        self.user_id = user_id
        self.platform = platform
        self.post_limit = post_limit
        self.time_limit = time_limit
        self.kwargs = kwargs

    def scrape(self) -> ScrapeJob:
        """
        Execute the scraping job.

        Returns:
            ScrapeJob instance with status and results (if synchronous)
        """
        job = self.engine.initialize_scrape(
            url=self.url,
            user_id=self.user_id,
            platform=self.platform,
            post_limit=self.post_limit,
            time_limit=self.time_limit,
            **self.kwargs
        )
        return job

    def get_platform_name(self) -> str:
        """Return the platform name."""
        return self.platform

    def is_async(self) -> bool:
        """Check if this scraper is asynchronous."""
        return self.engine.is_async()
