#!/usr/bin/env python3
"""
Quick start example for the multi-platform scraper.

This example shows the simplest way to:
1. Create a session (if needed)
2. Scrape posts from Threads
3. Save data to JSON
"""

import json
from scraper import ThreadsScraper, SessionManager


def main():
    # Configuration
    USER_ID = "user1"
    PROFILE_URL = "https://www.threads.com/@yannlecun"
    POST_LIMIT = 100
    TIME_LIMIT = None  # Set to number of seconds if you want a time limit

    # Step 1: Create session (only needed once)
    session_mgr = SessionManager()
    if not session_mgr.profile_exists(USER_ID):
        print(f"⚠️  No profile found for '{USER_ID}'. Creating session...")
        session_mgr.create_session(
            user_id=USER_ID,
            url=PROFILE_URL
        )
    else:
        print(f"✅ Found existing profile for '{USER_ID}'")

    # Step 2: Create scraper and scrape data
    print(f"\n🚀 Starting scraper...")
    scraper = ThreadsScraper(
        url=PROFILE_URL,
        user_id=USER_ID,
        post_limit=POST_LIMIT,
        time_limit=TIME_LIMIT
    )

    data = scraper.scrape()

    # Step 3: Save to JSON
    filename = f"threads_data_{data['scraped_at']}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    # Step 4: Display summary
    print(f"\n" + "=" * 60)
    print("✅ Scraping Complete!")
    print("=" * 60)
    print(f"URL: {data['url']}")
    print(f"Posts scraped: {data['total_items']}")
    print(f"Time elapsed: {data['elapsed_time']}s")
    print(f"Data saved to: {filename}")

    # Show first post
    if data['items']:
        print(f"\nFirst post preview:")
        first = data['items'][0]
        text_preview = first['text'][:100] + "..." if len(first['text']) > 100 else first['text']
        print(f"  Text: {text_preview}")
        print(f"  👍 Likes: {first['likes']}")
        print(f"  💬 Comments: {first['comments']}")
        print(f"  🔄 Reposts: {first['reposts']}")

    print("=" * 60)


if __name__ == "__main__":
    main()
