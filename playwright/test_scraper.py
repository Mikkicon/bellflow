#!/usr/bin/env python3
"""
Test script for the multi-platform scraper.

This script demonstrates how to use the scraper API to:
1. Create browser sessions (login)
2. Scrape posts with different limits
3. Save data to JSON files
"""

import json
from scraper import ThreadsScraper, SessionManager


def example_1_create_session():
    """Example 1: Create a new browser session for manual login."""
    print("=" * 60)
    print("Example 1: Create Browser Session")
    print("=" * 60)

    session_mgr = SessionManager()

    # Create session for user1
    session_mgr.create_session(
        user_id="user1",
        url="https://www.threads.com/@yannlecun"
    )

    print("\n✅ Session created! You can now use this profile for scraping.")


def example_2_scrape_with_post_limit():
    """Example 2: Scrape with a post limit."""
    print("\n" + "=" * 60)
    print("Example 2: Scrape with Post Limit (100 posts)")
    print("=" * 60)

    # Create scraper instance
    scraper = ThreadsScraper(
        url="https://www.threads.com/@yannlecun",
        user_id="user1",
        post_limit=100  # Stop after 100 posts
    )

    # Scrape data
    data = scraper.scrape()

    # Save to JSON
    filename = f"threads_data_{data['scraped_at']}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"\n💾 Data saved to {filename}")
    print(f"   Posts scraped: {data['total_items']}")
    print(f"   Time elapsed: {data['elapsed_time']}s")

    # Show preview
    print("\nFirst 3 posts:")
    for i, item in enumerate(data['items'][:3], 1):
        print(f"\n  Post {i}:")
        text_preview = item['text'][:80] + "..." if len(item['text']) > 80 else item['text']
        print(f"    Text: {text_preview}")
        print(f"    👍 Likes: {item['likes']}")
        print(f"    💬 Comments: {item['comments']}")
        print(f"    🔄 Reposts: {item['reposts']}")


def example_3_scrape_with_time_limit():
    """Example 3: Scrape with a time limit."""
    print("\n" + "=" * 60)
    print("Example 3: Scrape with Time Limit (60 seconds)")
    print("=" * 60)

    # Create scraper instance
    scraper = ThreadsScraper(
        url="https://www.threads.com/@elonmusk",
        user_id="user1",
        time_limit=60  # Stop after 60 seconds
    )

    # Scrape data
    data = scraper.scrape()

    # Save to JSON
    filename = f"threads_data_{data['scraped_at']}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"\n💾 Data saved to {filename}")
    print(f"   Posts scraped: {data['total_items']}")
    print(f"   Time elapsed: {data['elapsed_time']}s")


def example_4_scrape_different_profile():
    """Example 4: Scrape a different profile with a separate user session."""
    print("\n" + "=" * 60)
    print("Example 4: Scrape Different Profile (separate user)")
    print("=" * 60)

    session_mgr = SessionManager()

    # Check if user2 profile exists
    if not session_mgr.profile_exists("user2"):
        print("Creating new session for user2...")
        session_mgr.create_session(
            user_id="user2",
            url="https://www.threads.com/@zuck"
        )

    # Scrape with user2's session
    scraper = ThreadsScraper(
        url="https://www.threads.com/@zuck",
        user_id="user2",
        post_limit=50
    )

    data = scraper.scrape()

    print(f"\n✅ Scraped {data['total_items']} posts from {data['url']}")
    print(f"   Using user_id: {data['user_id']}")


def example_5_list_profiles():
    """Example 5: List all browser profiles."""
    print("\n" + "=" * 60)
    print("Example 5: List Browser Profiles")
    print("=" * 60)

    session_mgr = SessionManager()
    profiles = session_mgr.list_profiles()

    if profiles:
        print(f"\n📁 Found {len(profiles)} profile(s):")
        for profile in profiles:
            print(f"   - {profile}")
    else:
        print("\n⚠️  No profiles found. Run example 1 to create one.")


def main():
    """Main entry point for test script."""
    print("\n🎭 Multi-Platform Scraper - Test Examples")
    print("=" * 60)

    # Ask user which example to run
    print("\nAvailable examples:")
    print("  1. Create browser session (login)")
    print("  2. Scrape with post limit (100 posts)")
    print("  3. Scrape with time limit (60 seconds)")
    print("  4. Scrape different profile (separate user)")
    print("  5. List browser profiles")
    print("  0. Run all examples")

    choice = input("\nEnter choice (0-5): ").strip()

    examples = {
        '1': example_1_create_session,
        '2': example_2_scrape_with_post_limit,
        '3': example_3_scrape_with_time_limit,
        '4': example_4_scrape_different_profile,
        '5': example_5_list_profiles,
    }

    if choice == '0':
        # Run all examples
        for func in examples.values():
            func()
    elif choice in examples:
        examples[choice]()
    else:
        print("❌ Invalid choice")

    print("\n" + "=" * 60)
    print("✅ Done!")
    print("=" * 60)


if __name__ == "__main__":
    main()
