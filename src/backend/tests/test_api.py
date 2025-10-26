#!/usr/bin/env python3
"""Simple test script for the scraping API."""

import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_threads_scraping():
    """Test Threads scraping (Playwright engine)."""
    print("🧪 Testing Threads scraping...")

    payload = {
        "url": "https://www.threads.com/@zuck",
        "user_id": "test_user",
        "post_limit": 3,
        "headless": True,
        "scroll_delay": 0.3
    }

    response = requests.post(f"{BASE_URL}/v1/scrape", json=payload)

    print(f"Status Code: {response.status_code}")
    print(f"Response:")
    print(json.dumps(response.json(), indent=2))

    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ SUCCESS!")
        print(f"   Platform: {data.get('platform')}")
        print(f"   Total items: {data.get('total_items')}")
        print(f"   Elapsed time: {data.get('elapsed_time')}s")
        print(f"   Selector used: {data.get('selector_used')}")

        if data.get('items'):
            print(f"\n   Sample post:")
            post = data['items'][0]
            print(f"   - Text: {post.get('text', '')[:100]}...")
            print(f"   - Link: {post.get('link')}")
            print(f"   - Likes: {post.get('likes')}")
            print(f"   - Comments: {post.get('comments')}")
    else:
        print(f"\n❌ FAILED: {response.json().get('detail')}")

if __name__ == "__main__":
    test_threads_scraping()
