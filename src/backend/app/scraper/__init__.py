"""
Multi-platform social media scraper.

Supports scraping posts from various social media platforms with
session persistence and configurable limits.
"""

from app.scraper.platforms.threads import ThreadsScraper
from app.scraper.session_manager import SessionManager

__all__ = ['ThreadsScraper', 'SessionManager']
