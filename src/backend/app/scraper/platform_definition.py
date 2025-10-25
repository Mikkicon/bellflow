"""Platform definition interface for scrapers.

This module defines the abstract interface that all platform-specific
implementations must follow. Platform definitions provide the "what to scrape"
logic, while engines provide the "how to scrape" workflow.
"""

from abc import ABC, abstractmethod
from typing import List, Dict


class PlatformDefinition(ABC):
    """
    Abstract base class for platform-specific scraper definitions.

    Platform definitions provide:
    - Platform name/identifier
    - CSS selectors for finding posts
    - Data extraction logic from page elements

    They do NOT handle:
    - Browser session management
    - Scrolling/pagination
    - Timing/limits
    - Network requests

    These responsibilities belong to the scraper engines.
    """

    @abstractmethod
    def get_platform_name(self) -> str:
        """
        Return the platform identifier.

        Returns:
            Platform name (e.g., 'threads', 'twitter', 'linkedin')
        """
        pass

    @abstractmethod
    def get_selectors(self) -> List[str]:
        """
        Return CSS selectors for finding posts on the platform.

        The selectors are tried in order until one successfully finds posts.

        Returns:
            List of CSS selector strings to try
        """
        pass

    @abstractmethod
    def extract_data(self, page, selector: str) -> List[Dict]:
        """
        Extract post data from the page using the given selector.

        This method receives a Playwright page object and the CSS selector
        that successfully found posts. It should use JavaScript evaluation
        to extract structured data from the posts.

        Args:
            page: Playwright page object
            selector: CSS selector that found the posts

        Returns:
            List of dictionaries containing post data
            Each dictionary should include relevant fields like:
            - text: Post content
            - link: URL to the post
            - likes: Number of likes (if available)
            - comments: Number of comments (if available)
            - date_posted: Post timestamp (if available)
            - etc.
        """
        pass
