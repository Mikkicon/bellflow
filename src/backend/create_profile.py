#!/usr/bin/env python3
"""Create a browser profile for scraping."""

from app.scraper.session_manager import SessionManager

if __name__ == "__main__":
    # Initialize session manager
    manager = SessionManager()

    # Create session for user1
    # This will open a browser window where you can log into Threads
    manager.create_session(
        user_id="user1",
        url="https://www.threads.net/login",
        headless=False
    )

    print("\n✅ Profile created successfully!")
    print("You can now use the scraping API with user_id='user1'")
