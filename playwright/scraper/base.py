"""Base scraper class for all platforms."""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from datetime import datetime
import time


class BasePlatformScraper(ABC):
    """Abstract base class for platform-specific scrapers."""

    def __init__(
        self,
        url: str,
        user_id: str,
        post_limit: Optional[int] = None,
        time_limit: Optional[int] = None,
        scroll_delay: float = 0.75,
        headless: bool = False
    ):
        """
        Initialize the scraper.

        Args:
            url: Profile URL to scrape
            user_id: User identifier for browser profile isolation
            post_limit: Maximum number of posts to scrape (None = unlimited)
            time_limit: Maximum scraping time in seconds (None = unlimited)
            scroll_delay: Delay between scrolls in seconds
            headless: Run browser in headless mode
        """
        self.url = url
        self.user_id = user_id
        self.post_limit = post_limit
        self.time_limit = time_limit
        self.scroll_delay = scroll_delay
        self.headless = headless
        self.start_time = None

    @abstractmethod
    def get_platform_name(self) -> str:
        """Return the platform name (e.g., 'threads', 'facebook')."""
        pass

    @abstractmethod
    def get_post_selectors(self) -> List[str]:
        """Return list of CSS selectors to try for finding posts."""
        pass

    @abstractmethod
    def extract_post_data(self, page, selector: str) -> List[Dict]:
        """
        Extract post data from the page.

        Args:
            page: Playwright page object
            selector: CSS selector that successfully found posts

        Returns:
            List of dictionaries containing post data
        """
        pass

    def should_continue_scraping(self, current_post_count: int) -> bool:
        """
        Check if scraping should continue based on limits.

        Args:
            current_post_count: Number of posts loaded so far

        Returns:
            True if scraping should continue, False otherwise
        """
        # Check post limit
        if self.post_limit and current_post_count >= self.post_limit:
            return False

        # Check time limit
        if self.time_limit and self.start_time:
            elapsed = time.time() - self.start_time
            if elapsed >= self.time_limit:
                return False

        return True

    def find_post_selector(self, page) -> Optional[str]:
        """
        Try different selectors to find posts on the page.

        Args:
            page: Playwright page object

        Returns:
            The selector that successfully found posts, or None
        """
        import json

        for selector in self.get_post_selectors():
            try:
                count = page.evaluate(f'document.querySelectorAll({json.dumps(selector)}).length')
                if count > 0:
                    return selector
            except Exception:
                continue

        return None

    def scroll_and_load(self, page, selector: str, max_scrolls: int = 500) -> int:
        """
        Scroll the page to load more posts.

        Args:
            page: Playwright page object
            selector: CSS selector for posts
            max_scrolls: Maximum number of scroll attempts

        Returns:
            Final count of posts loaded
        """
        import json

        last_count = 0
        scrolls = 0

        for i in range(max_scrolls):
            # Scroll to bottom
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(self.scroll_delay)

            # Count current posts
            current_count = page.evaluate(f'document.querySelectorAll({json.dumps(selector)}).length')
            scrolls += 1

            # Show progress every 5 scrolls
            if scrolls % 5 == 0:
                print(f"  Scroll {scrolls}: {current_count} posts loaded...")

            # Check if we should stop
            if not self.should_continue_scraping(current_count):
                if self.post_limit and current_count >= self.post_limit:
                    print(f"🎯 Post limit reached: {current_count} posts (limit: {self.post_limit})")
                elif self.time_limit:
                    elapsed = time.time() - self.start_time
                    print(f"⏱️  Time limit reached: {elapsed:.1f}s (limit: {self.time_limit}s)")
                break

            # Check if no new content loaded
            if current_count == last_count:
                print(f"🛑 No more content after {scrolls} scrolls. Final count: {current_count} posts")
                break

            last_count = current_count

        return current_count

    @abstractmethod
    def scrape(self) -> Dict:
        """
        Main scraping method. Must be implemented by subclasses.

        Returns:
            Dictionary containing scraped data
        """
        pass
