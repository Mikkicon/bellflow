"""Threads.com scraper implementation."""

from typing import List, Dict
from datetime import datetime
import time
import json as json_module

from app.scraper.base import BasePlatformScraper
from app.scraper.session_manager import SessionManager


class ThreadsScraper(BasePlatformScraper):
    """Scraper for Threads.com (Instagram Threads)."""

    def get_platform_name(self) -> str:
        """Return the platform name."""
        return "threads"

    def get_post_selectors(self) -> List[str]:
        """Return CSS selectors for Threads posts."""
        return [
            'article',
            '[role="article"]',
            'div[data-pressable-container="true"]',
            'div[class*="post"]',
            'div[class*="Post"]',
            'div[class*="thread"]',
            'div[class*="Thread"]',
            'div[role="button"]',
        ]

    def extract_post_data(self, page, selector: str) -> List[Dict]:
        """
        Extract post data from Threads page.

        Args:
            page: Playwright page object
            selector: CSS selector for posts

        Returns:
            List of post dictionaries with text, link, likes, comments, reposts
        """
        # First pass: extract raw data
        raw_items = page.eval_on_selector_all(
            selector,
            """nodes => nodes.map(n => {
                const text = n.innerText;
                const link = n.querySelector('a')?.href;

                // Extract all standalone numbers from text (engagement metrics)
                const textLines = text.split('\\n').filter(line => line.trim());
                const numbers = textLines.filter(line => /^\\d+$/.test(line.trim())).map(n => parseInt(n));

                return {
                    text: text,
                    link: link,
                    raw_numbers: numbers
                };
            })"""
        )

        # Second pass: parse engagement metrics from raw numbers
        items = []
        for raw_item in raw_items:
            item = {
                'text': raw_item['text'],
                'link': raw_item['link'],
                'likes': None,
                'comments': None,
                'reposts': None
            }

            # The last 3-4 numbers in text are usually: likes, comments, reposts, (shares/other)
            numbers = raw_item.get('raw_numbers', [])
            if len(numbers) >= 3:
                # Last numbers are usually engagement metrics
                item['likes'] = numbers[-4] if len(numbers) >= 4 else numbers[-3]
                item['comments'] = numbers[-3] if len(numbers) >= 4 else numbers[-2]
                item['reposts'] = numbers[-2] if len(numbers) >= 4 else numbers[-1]

            items.append(item)

        return items

    def scrape(self) -> Dict:
        """
        Scrape posts from a Threads profile.

        Returns:
            Dictionary containing:
                - scraped_at: Timestamp
                - url: Profile URL
                - platform: Platform name
                - user_id: User identifier
                - total_items: Number of posts scraped
                - post_limit: Post limit (if set)
                - time_limit: Time limit (if set)
                - items: List of post data
        """
        self.start_time = time.time()

        # Initialize session manager
        session_mgr = SessionManager()

        # Load browser session
        context = session_mgr.load_session(self.user_id, headless=self.headless)
        page = context.pages[0] if context.pages else context.new_page()

        try:
            # Navigate to profile
            print(f"🌐 Navigating to: {self.url}")
            page.goto(self.url, wait_until="domcontentloaded")
            print("⏳ Waiting for page to load...")
            time.sleep(8)

            # Scroll a bit to trigger lazy loading
            page.evaluate("window.scrollTo(0, 500)")
            time.sleep(2)

            # Find post selector
            print("🔍 Detecting post selector...")
            selector = self.find_post_selector(page)

            if not selector:
                print("❌ Could not find posts selector!")
                context.close()
                return {
                    'error': 'No posts found',
                    'scraped_at': datetime.now().strftime("%Y%m%d_%H%M%S"),
                    'url': self.url,
                    'platform': self.get_platform_name(),
                    'user_id': self.user_id
                }

            initial_count = page.evaluate(f'document.querySelectorAll({json_module.dumps(selector)}).length')
            print(f"✅ Found {initial_count} posts using selector: {selector}")

            # Scroll to load more posts
            limits_desc = []
            if self.post_limit:
                limits_desc.append(f"target: {self.post_limit} posts")
            if self.time_limit:
                limits_desc.append(f"time limit: {self.time_limit}s")

            limit_str = ", ".join(limits_desc) if limits_desc else "no limit"
            print(f"\n🚀 Scrolling to load posts ({limit_str})...")

            final_count = self.scroll_and_load(page, selector, max_scrolls=500)

            # Extract post data
            print(f"\n🔍 Extracting {final_count} posts...")
            items = self.extract_post_data(page, selector)

            # Apply post limit if needed
            if self.post_limit and len(items) > self.post_limit:
                items = items[:self.post_limit]

            print(f"✅ Scraped {len(items)} items")

            # Calculate elapsed time
            elapsed_time = time.time() - self.start_time

            # Build result
            result = {
                'scraped_at': datetime.now().strftime("%Y%m%d_%H%M%S"),
                'url': self.url,
                'platform': self.get_platform_name(),
                'user_id': self.user_id,
                'total_items': len(items),
                'post_limit': self.post_limit,
                'time_limit': self.time_limit,
                'elapsed_time': round(elapsed_time, 2),
                'selector_used': selector,
                'items': items
            }

            return result

        finally:
            context.close()
