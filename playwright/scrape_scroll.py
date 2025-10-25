# scrape_scroll.py
from playwright.sync_api import sync_playwright
import time
import json
from datetime import datetime

# Configuration
TARGET_POSTS = 100  # Stop after loading this many posts
SCROLL_DELAY = 0.75  # Seconds between scrolls
MAX_SCROLLS = 500  # Maximum scroll attempts

def auto_scroll_with_count(page, selector, target_posts=100, max_scrolls=500, delay=0.75):
    """Scrolls until target posts reached or no new content appears"""
    last_count = 0
    scrolls = 0

    for i in range(max_scrolls):
        # Scroll to bottom
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(delay)

        # Count current posts
        current_count = page.evaluate(f'document.querySelectorAll({json.dumps(selector)}).length')
        scrolls += 1

        # Show progress
        if scrolls % 5 == 0:  # Update every 5 scrolls
            print(f"  Scroll {scrolls}: {current_count} posts loaded...")

        # Check if we reached target
        if current_count >= target_posts:
            print(f"🎯 Target reached: {current_count} posts (target: {target_posts})")
            break

        # Check if no new content loaded
        if current_count == last_count:
            print(f"🛑 No more content after {scrolls} scrolls. Final count: {current_count} posts")
            break

        last_count = current_count

    return current_count

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context(storage_state="storage_state.json")  # reuse your login
    page = context.new_page()

    page.goto("https://www.threads.com/@yannlecun", wait_until="domcontentloaded")
    print("⏳ Waiting for page to load...")
    time.sleep(8)  # Wait longer for React to render content

    # Scroll a bit to trigger lazy loading
    page.evaluate("window.scrollTo(0, 500)")
    time.sleep(2)

    print("🔍 Detecting post selector...")

    # Try to find Threads posts - common selectors for React apps
    selectors_to_try = [
        'article',
        '[role="article"]',
        'div[class*="post"]',
        'div[class*="Post"]',
        'div[class*="thread"]',
        'div[class*="Thread"]',
        'div[data-pressable-container="true"]',  # Common in React Native Web
        'div[role="button"]',  # Threads might use this
    ]

    found_selector = None

    for selector in selectors_to_try:
        try:
            count = page.evaluate(f'document.querySelectorAll({json.dumps(selector)}).length')
            if count > 0:
                found_selector = selector
                print(f"✅ Found {count} posts using selector: {found_selector}")
                break
        except Exception as e:
            pass  # Silently try next selector

    if not found_selector:
        print("❌ Could not find posts selector!")
        browser.close()
        exit(1)

    print(f"\n🚀 Scrolling to load posts (target: {TARGET_POSTS} posts)...")
    final_count = auto_scroll_with_count(page, found_selector, target_posts=TARGET_POSTS, max_scrolls=MAX_SCROLLS, delay=SCROLL_DELAY)

    print(f"\n🔍 Extracting {final_count} posts...")

    # First pass: extract raw data
    raw_items = page.eval_on_selector_all(
        found_selector,
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
        # Take the last 3 numbers as engagement metrics
        numbers = raw_item.get('raw_numbers', [])
        if len(numbers) >= 3:
            # Last numbers are usually at the end
            item['likes'] = numbers[-4] if len(numbers) >= 4 else numbers[-3]
            item['comments'] = numbers[-3] if len(numbers) >= 4 else numbers[-2]
            item['reposts'] = numbers[-2] if len(numbers) >= 4 else numbers[-1]

        items.append(item)

    print(f"✅ Scraped {len(items)} items")

    # Save to JSON file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"threads_data_{timestamp}.json"

    output = {
        "scraped_at": timestamp,
        "url": "https://www.threads.com/@yannlecun",
        "total_items": len(items),
        "target_posts": TARGET_POSTS,
        "selector_used": found_selector,
        "items": items
    }

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"💾 Data saved to {filename}")
    print(f"\nFirst 3 items preview:")
    for item in items[:3]:
        text_preview = item['text'][:100] + "..." if len(item['text']) > 100 else item['text']
        print(f"\n  Text: {text_preview}")
        print(f"  Link: {item['link']}")
        print(f"  👍 Likes: {item.get('likes', 'N/A')}")
        print(f"  💬 Comments: {item.get('comments', 'N/A')}")
        print(f"  🔄 Reposts: {item.get('reposts', 'N/A')}")

    browser.close()
