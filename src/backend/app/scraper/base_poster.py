"""Base poster class for all platforms."""

from abc import ABC, abstractmethod
from typing import Dict, Optional
from datetime import datetime
import time
import asyncio


class BasePlatformPoster(ABC):
    """Abstract base class for platform-specific posters."""

    def __init__(
        self,
        user_id: str,
        content: str,
        url: Optional[str] = None,
        headless: bool = False
    ):
        """
        Initialize the poster.

        Args:
            user_id: User identifier for browser profile isolation
            content: Text content to post
            url: Optional URL to navigate to (if None, uses platform home)
            headless: Run browser in headless mode
        """
        self.user_id = user_id
        self.content = content
        self.url = url
        self.headless = headless
        self.start_time = None

    @abstractmethod
    def get_platform_name(self) -> str:
        """Return the platform name (e.g., 'x', 'threads')."""
        pass

    @abstractmethod
    def get_composer_selectors(self) -> Dict[str, str]:
        """
        Return selectors for posting UI elements.

        Should return a dictionary with keys:
            - compose_button: Selector for button to open compose dialog
            - text_area: Selector for text input area
            - submit_button: Selector for submit/post button

        Returns:
            Dictionary mapping element names to CSS selectors
        """
        pass

    async def find_element(self, page, selector: str, timeout: int = 5000) -> bool:
        """
        Check if an element exists on the page.

        Args:
            page: Playwright page object
            selector: CSS selector to find
            timeout: Timeout in milliseconds

        Returns:
            True if element found, False otherwise
        """
        try:
            await page.wait_for_selector(selector, timeout=timeout)
            return True
        except Exception:
            return False

    async def click_and_wait(self, page, selector: str, wait_time: float = 1.0) -> bool:
        """
        Click an element and wait.

        Args:
            page: Playwright page object
            selector: CSS selector to click
            wait_time: Time to wait after click in seconds

        Returns:
            True if successful, False otherwise
        """
        try:
            await page.click(selector)
            await asyncio.sleep(wait_time)
            return True
        except Exception as e:
            print(f"❌ Failed to click {selector}: {e}")
            return False

    async def type_text(self, page, selector: str, text: str, delay: int = 50) -> bool:
        """
        Type text into an input field.

        Args:
            page: Playwright page object
            selector: CSS selector for input field
            text: Text to type
            delay: Delay between keystrokes in milliseconds

        Returns:
            True if successful, False otherwise
        """
        try:
            await page.fill(selector, text)
            await asyncio.sleep(0.5)
            return True
        except Exception as e:
            print(f"❌ Failed to type into {selector}: {e}")
            return False

    @abstractmethod
    async def post(self) -> Dict:
        """
        Main posting method. Must be implemented by subclasses.

        Returns:
            Dictionary containing:
                - posted_at: Timestamp
                - platform: Platform name
                - user_id: User identifier
                - success: Boolean indicating success/failure
                - content: Content that was posted
                - post_url: URL of created post (if detectable)
                - error: Error message (if failed)
                - elapsed_time: Time taken to post
        """
        pass
