"""X.com/Twitter platform definition."""

from typing import List, Dict
from app.scraper.platform_definition import PlatformDefinition


class TwitterPlatform(PlatformDefinition):
    """Platform definition for X.com/Twitter."""

    def get_platform_name(self) -> str:
        """Return the platform name."""
        return "twitter"

    def get_selectors(self) -> List[str]:
        """Return CSS selectors for X.com/Twitter tweets."""
        return [
            'article[data-testid="tweet"]',
            'article[role="article"]',
            'div[data-testid="tweet"]',
            'article',
            'div[data-testid="cellInnerDiv"]',
        ]

    def extract_data(self, page, selector: str) -> List[Dict]:
        """
        Extract tweet data from X.com page.

        Args:
            page: Playwright page object
            selector: CSS selector for tweets

        Returns:
            List of tweet dictionaries with text, link, likes, retweets, replies, views
        """
        # Extract raw data using JavaScript
        raw_items = page.eval_on_selector_all(
            selector,
            """nodes => nodes.map(n => {
                const text = n.innerText;

                // Extract link to tweet
                const link = n.querySelector('a[href*="/status/"]')?.href;

                // Extract engagement metrics
                const replyBtn = n.querySelector('[data-testid="reply"]');
                const retweetBtn = n.querySelector('[data-testid="retweet"]');
                const likeBtn = n.querySelector('[data-testid="like"]');
                const viewsSpan = n.querySelector('a[href*="/analytics"] span');

                // Get text content from aria-label or direct text
                const replies = replyBtn?.getAttribute('aria-label')?.match(/\\d+/)?.[0] || '0';
                const retweets = retweetBtn?.getAttribute('aria-label')?.match(/\\d+/)?.[0] || '0';
                const likes = likeBtn?.getAttribute('aria-label')?.match(/\\d+/)?.[0] || '0';
                const views = viewsSpan?.innerText || '0';

                // Extract timestamp
                const timeElement = n.querySelector('time');
                const datePosted = timeElement?.getAttribute('datetime') || '';

                return {
                    text: text,
                    link: link,
                    replies: parseInt(replies),
                    retweets: parseInt(retweets),
                    likes: parseInt(likes),
                    views: views,
                    date_posted: datePosted
                };
            })"""
        )

        # Filter out invalid items (no link means not a real tweet)
        items = [item for item in raw_items if item.get('link')]

        return items
