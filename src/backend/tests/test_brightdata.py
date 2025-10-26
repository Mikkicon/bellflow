#!/usr/bin/env python3
"""Test script for Bright Data API integration."""

import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000"

def test_twitter_scraping():
    """Test Twitter scraping via Bright Data API."""
    print("🐦 Testing Twitter/X scraping with Bright Data...")
    print("=" * 60)

    # Submit scraping job
    payload = {
        "url": "https://twitter.com/elonmusk",
        "user_id": "test_user_brightdata",
        "post_limit": 10,  # Will be converted to ~90 day date range
        "headless": True
    }

    print(f"\n📤 Submitting scrape request...")
    print(f"   URL: {payload['url']}")
    print(f"   Post limit: {payload['post_limit']}")

    response = requests.post(f"{BASE_URL}/v1/scrape", json=payload)

    if response.status_code != 200:
        print(f"\n❌ Request failed: {response.status_code}")
        print(json.dumps(response.json(), indent=2))
        return

    data = response.json()
    print(f"\n✅ Job submitted successfully!")
    print(f"   Job ID: {data.get('job_id')}")
    print(f"   Status: {data.get('status')}")
    print(f"   Platform: {data.get('platform')}")
    print(f"   Message: {data.get('message')}")

    job_id = data.get('job_id')
    if not job_id:
        print("\n❌ No job_id returned!")
        return

    # Poll for status
    print(f"\n⏳ Polling job status...")
    max_polls = 60  # 5 minutes max
    poll_interval = 5  # seconds

    for i in range(max_polls):
        time.sleep(poll_interval)

        status_response = requests.get(f"{BASE_URL}/v1/scrape/status/{job_id}")

        if status_response.status_code != 200:
            print(f"\n❌ Status check failed: {status_response.status_code}")
            print(json.dumps(status_response.json(), indent=2))
            break

        status_data = status_response.json()
        current_status = status_data.get('status')

        print(f"   Poll {i+1}: Status = {current_status}")

        if status_data.get('progress'):
            print(f"          Progress: {status_data['progress']}")

        if current_status == 'completed':
            print(f"\n✅ Job completed!")
            print(f"   Time elapsed: ~{(i+1) * poll_interval} seconds")

            # Get results
            print(f"\n📥 Fetching results...")
            result_response = requests.get(f"{BASE_URL}/v1/scrape/result/{job_id}")

            if result_response.status_code != 200:
                print(f"\n❌ Failed to get results: {result_response.status_code}")
                print(json.dumps(result_response.json(), indent=2))
                return

            result_data = result_response.json()

            print(f"\n🎉 SUCCESS! Results retrieved:")
            print(f"   Platform: {result_data.get('platform')}")
            print(f"   Total items: {result_data.get('total_items')}")
            print(f"   Scraped at: {result_data.get('scraped_at')}")
            print(f"   Elapsed time: {result_data.get('elapsed_time')}s")

            if result_data.get('items'):
                print(f"\n📝 Sample posts (first 3):")
                for idx, item in enumerate(result_data['items'][:3], 1):
                    print(f"\n   Post #{idx}:")
                    print(f"   - Text: {item.get('text', '')[:100]}...")
                    print(f"   - Link: {item.get('link')}")
                    print(f"   - Likes: {item.get('likes')}")
                    print(f"   - Comments: {item.get('comments')}")
                    print(f"   - Retweets: {item.get('reposts')}")
                    print(f"   - Date: {item.get('date_posted')}")
                    print(f"   - Views: {item.get('views')}")

            return

        elif current_status == 'failed':
            print(f"\n❌ Job failed!")
            print(f"   Error: {status_data.get('error')}")
            return

        elif current_status in ['pending', 'running']:
            # Continue polling
            pass
        else:
            print(f"\n⚠️  Unknown status: {current_status}")

    print(f"\n⏱️  Timeout: Job did not complete within {max_polls * poll_interval} seconds")
    print(f"   Last status: {current_status}")
    print(f"   You can check manually:")
    print(f"   curl http://127.0.0.1:8000/v1/scrape/status/{job_id}")

if __name__ == "__main__":
    test_twitter_scraping()
