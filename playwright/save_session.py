#!/usr/bin/env python3
"""
Simple script to create a browser session for manual login.

This is a convenience wrapper around SessionManager.create_session()
for users who prefer a simple command-line tool.
"""

import sys
from scraper import SessionManager


def main():
    """Create a browser session for manual login."""
    print("🎭 Browser Session Creator")
    print("=" * 60)

    # Get user input
    user_id = input("Enter user ID (e.g., 'user1'): ").strip()
    if not user_id:
        print("❌ User ID cannot be empty")
        sys.exit(1)

    url = input("Enter URL to login to (default: https://www.threads.com): ").strip()
    if not url:
        url = "https://www.threads.com"

    print("\n" + "=" * 60)

    # Create session
    session_mgr = SessionManager()
    session_mgr.create_session(
        user_id=user_id,
        url=url,
        headless=False,
        slow_mo=100
    )

    print("\n" + "=" * 60)
    print("✅ Session created successfully!")
    print(f"   You can now use user_id='{user_id}' in your scraper")
    print("=" * 60)


if __name__ == "__main__":
    main()
