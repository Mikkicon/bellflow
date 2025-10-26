"""X.com (Twitter) scraper implementation."""

from typing import List, Dict
from datetime import datetime
import time
import json as json_module
import asyncio

from app.scraper.base import BasePlatformScraper
from app.scraper.session_manager import SessionManager


class XScraper(BasePlatformScraper):
    """Scraper for X.com (formerly Twitter)."""

    def get_platform_name(self) -> str:
        """Return the platform name."""
        return "x"

    def get_post_selectors(self) -> List[str]:
        """Return CSS selectors for X/Twitter posts."""
        return [
            'article[data-testid="tweet"]',
            'article[role="article"]',
            'div[data-testid="cellInnerDiv"]',
            'article',
            'div[data-testid="tweet"]',
        ]

    async def extract_post_data(self, page, selector: str) -> List[Dict]:
        """
        Extract post data from X/Twitter page.

        Args:
            page: Playwright page object
            selector: CSS selector for posts

        Returns:
            List of post dictionaries with text, link, likes, retweets, replies, raw_data
        """
        # Extract post data using JavaScript
        raw_items = await page.eval_on_selector_all(
            selector,
            """nodes => nodes.map(n => {
                const text = n.innerText;
                const html = n.innerHTML;

                // Try to find the tweet link
                const timeElement = n.querySelector('time');
                const link = timeElement?.parentElement?.href || null;

                // Extract engagement metrics
                // X uses aria-label or data-testid for engagement metrics
                const replyButton = n.querySelector('[data-testid="reply"]');
                const retweetButton = n.querySelector('[data-testid="retweet"]');
                const likeButton = n.querySelector('[data-testid="like"]');
                const viewsElement = n.querySelector('[href$="/analytics"]');

                // Extract counts from aria-labels (e.g., "5 Replies", "10 Reposts", "50 Likes")
                const extractCount = (element) => {
                    if (!element) return null;
                    const ariaLabel = element.getAttribute('aria-label');
                    if (!ariaLabel) return null;
                    const match = ariaLabel.match(/(\d+)/);
                    return match ? parseInt(match[1]) : 0;
                };

                const replies = extractCount(replyButton);
                const retweets = extractCount(retweetButton);
                const likes = extractCount(likeButton);

                // Extract view count if available
                let views = null;
                if (viewsElement) {
                    const viewsText = viewsElement.innerText;
                    const viewsMatch = viewsText.match(/(\d+)/);
                    views = viewsMatch ? parseInt(viewsMatch[1]) : null;
                }

                // Extract username
                const usernameElement = n.querySelector('[data-testid="User-Name"] a[href^="/"]');
                const username = usernameElement?.href?.split('/').pop() || null;

                return {
                    text: text,
                    link: link,
                    username: username,
                    replies: replies,
                    retweets: retweets,
                    likes: likes,
                    views: views,
                    html: html
                };
            })"""
        )

        # Process and clean the items
        items = []
        for raw_item in raw_items:
            item = {
                'text': raw_item.get('text', ''),
                'link': raw_item.get('link'),
                'username': raw_item.get('username'),
                'likes': raw_item.get('likes'),
                'retweets': raw_item.get('retweets'),
                'replies': raw_item.get('replies'),
                'views': raw_item.get('views'),
                'raw_data': raw_item.get('html', '')
            }

            # Only add items that have actual content
            if item['text'] or item['link']:
                items.append(item)

        return items

    async def scrape(self) -> Dict:
        """
        Scrape posts from an X/Twitter profile.

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

        # Load browser session (returns tuple of playwright instance, context, and session_id)
        playwright, context, session_id = await session_mgr.load_session(self.user_id, headless=self.headless)
        page = context.pages[0] if context.pages else await context.new_page()

        try:
            # Navigate to profile
            print(f"🌐 Navigating to: {self.url}")
            await page.goto(self.url, wait_until="domcontentloaded")
            print("⏳ Waiting for page to load...")
            await asyncio.sleep(5)

            # Scroll a bit to trigger lazy loading
            await page.evaluate("window.scrollTo(0, 500)")
            await asyncio.sleep(2)

            # Find post selector
            print("🔍 Detecting post selector...")
            selector = await self.find_post_selector(page)

            if not selector:
                print("❌ Could not find posts selector!")
                await context.close()
                await playwright.stop()
                session_mgr.unregister_session(session_id)
                return {
                    'error': 'No posts found. You may need to log in first.',
                    'scraped_at': datetime.now().strftime("%Y%m%d_%H%M%S"),
                    'url': self.url,
                    'platform': self.get_platform_name(),
                    'user_id': self.user_id
                }

            initial_count = await page.evaluate(f'document.querySelectorAll({json_module.dumps(selector)}).length')
            print(f"✅ Found {initial_count} posts using selector: {selector}")

            # Scroll to load more posts
            limits_desc = []
            if self.post_limit:
                limits_desc.append(f"target: {self.post_limit} posts")
            if self.time_limit:
                limits_desc.append(f"time limit: {self.time_limit}s")

            limit_str = ", ".join(limits_desc) if limits_desc else "no limit"
            print(f"\n🚀 Scrolling to load posts ({limit_str})...")

            final_count = await self.scroll_and_load(page, selector, max_scrolls=500)

            # Extract post data
            print(f"\n🔍 Extracting {final_count} posts...")
            items = await self.extract_post_data(page, selector)

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
            # Close context and playwright instance to ensure session data is persisted
            await context.close()
            await playwright.stop()
            session_mgr.unregister_session(session_id)
