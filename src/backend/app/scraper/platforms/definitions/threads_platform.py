"""Threads.com platform definition."""

from typing import List, Dict
from app.scraper.platform_definition import PlatformDefinition


class ThreadsPlatform(PlatformDefinition):
    """Platform definition for Threads.com (Instagram Threads)."""

    def get_platform_name(self) -> str:
        """Return the platform name."""
        return "threads"

    def get_selectors(self) -> List[str]:
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

    def extract_data(self, page, selector: str) -> List[Dict]:
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
