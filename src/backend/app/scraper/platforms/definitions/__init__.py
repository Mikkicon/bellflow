"""Platform definitions for different social media platforms."""

from app.scraper.platforms.definitions.threads_platform import ThreadsPlatform
from app.scraper.platforms.definitions.twitter_platform import TwitterPlatform

__all__ = [
    'ThreadsPlatform',
    'TwitterPlatform',
]
