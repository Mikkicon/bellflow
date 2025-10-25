"""Base scraper engine abstraction."""

from abc import ABC, abstractmethod
from typing import Dict, Optional, List
from enum import Enum
from datetime import datetime
from dataclasses import dataclass


class JobStatus(str, Enum):
    """Status of a scraping job."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ScrapeJob:
    """Represents a scraping job."""
    job_id: str
    status: JobStatus
    platform: str
    url: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    result: Optional[Dict] = None
    error: Optional[str] = None
    progress: Optional[Dict] = None  # For tracking progress (e.g., posts scraped)


class BaseScraperEngine(ABC):
    """
    Abstract base class for scraper engines.

    Engines can be synchronous (Playwright) or asynchronous (API-based).
    All engines must implement these methods to provide a consistent interface.
    """

    @abstractmethod
    def is_async(self) -> bool:
        """
        Return whether this engine uses asynchronous scraping.

        Returns:
            True if async (requires polling), False if sync (returns results immediately)
        """
        pass

    @abstractmethod
    def initialize_scrape(
        self,
        url: str,
        user_id: str,
        platform: str,
        post_limit: Optional[int] = None,
        time_limit: Optional[int] = None,
        **kwargs
    ) -> ScrapeJob:
        """
        Initialize a scraping job.

        Args:
            url: Profile URL to scrape
            user_id: User identifier
            platform: Platform name (e.g., 'threads', 'twitter', 'linkedin')
            post_limit: Maximum number of posts to scrape
            time_limit: Maximum scraping time in seconds
            **kwargs: Additional platform-specific parameters

        Returns:
            ScrapeJob with initial status
        """
        pass

    @abstractmethod
    def get_status(self, job_id: str) -> ScrapeJob:
        """
        Get the status of a scraping job.

        Args:
            job_id: Job identifier

        Returns:
            ScrapeJob with current status

        Raises:
            ValueError: If job_id not found
        """
        pass

    @abstractmethod
    def get_results(self, job_id: str) -> Dict:
        """
        Get the results of a completed scraping job.

        Args:
            job_id: Job identifier

        Returns:
            Dictionary containing scraped data

        Raises:
            ValueError: If job not found or not completed
        """
        pass

    @abstractmethod
    def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a running scraping job.

        Args:
            job_id: Job identifier

        Returns:
            True if cancelled successfully, False otherwise
        """
        pass
