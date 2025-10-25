# Multi-Platform Social Media Scraper

A well-structured, extensible web scraper for social media platforms using Playwright with persistent browser profiles.

## Features

- 🌐 **Multi-platform support** - Currently supports Threads, easy to extend for Facebook, X, etc.
- 👤 **User-based profiles** - Separate browser profiles per user ID
- ⏱️ **Configurable limits** - Set post count or time limits
- 💾 **Persistent sessions** - Browser profiles survive restarts
- 📊 **Engagement metrics** - Extracts likes, comments, reposts
- 🎯 **Clean API** - Well-structured, programmatic interface

## Setup

1. **Install dependencies:**
   ```bash
   uv sync
   ```

2. **Install Playwright browsers:**
   ```bash
   uv run playwright install
   ```

## Quick Start

Run the interactive script:

```bash
./run.sh
```

This will:
1. Check for existing browser profiles
2. Create a new session if needed (manual login)
3. Run the test scraper with examples

## Usage

### Option 1: Command-Line Tools

**Create a browser session (login):**

```bash
uv run python save_session.py
```

**Run test examples:**

```bash
uv run python test_scraper.py
```

### Option 2: Python API

```python
from scraper import ThreadsScraper, SessionManager

# 1. Create a browser session (one-time setup)
session_mgr = SessionManager()
session_mgr.create_session(
    user_id="user1",
    url="https://www.threads.com/@yannlecun"
)

# 2. Scrape posts with post limit
scraper = ThreadsScraper(
    url="https://www.threads.com/@yannlecun",
    user_id="user1",
    post_limit=100  # Stop after 100 posts
)
data = scraper.scrape()

# 3. Scrape posts with time limit
scraper = ThreadsScraper(
    url="https://www.threads.com/@elonmusk",
    user_id="user1",
    time_limit=300  # Stop after 5 minutes (300 seconds)
)
data = scraper.scrape()

# 4. Save data to JSON
import json
with open(f"threads_data_{data['scraped_at']}.json", 'w') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
```

## API Reference

### ThreadsScraper

```python
scraper = ThreadsScraper(
    url: str,              # Profile URL to scrape
    user_id: str,          # User ID for browser profile
    post_limit: int = None,  # Max posts to scrape (None = unlimited)
    time_limit: int = None,  # Max time in seconds (None = unlimited)
    scroll_delay: float = 0.75,  # Delay between scrolls
    headless: bool = False  # Run browser in headless mode
)

data = scraper.scrape()  # Returns dict with scraped data
```

### SessionManager

```python
from scraper import SessionManager

session_mgr = SessionManager(base_dir="./browser_profiles")

# Create new session (manual login)
session_mgr.create_session(user_id="user1", url="https://www.threads.com")

# Check if profile exists
exists = session_mgr.profile_exists("user1")

# List all profiles
profiles = session_mgr.list_profiles()

# Delete a profile
session_mgr.delete_session("user1")
```

## Data Structure

Scraped data is returned as a dictionary:

```json
{
  "scraped_at": "20251025_143022",
  "url": "https://www.threads.com/@yannlecun",
  "platform": "threads",
  "user_id": "user1",
  "total_items": 100,
  "post_limit": 100,
  "time_limit": null,
  "elapsed_time": 45.3,
  "selector_used": "div[data-pressable-container=\"true\"]",
  "items": [
    {
      "text": "Post text content...",
      "link": "https://www.threads.com/@yannlecun/post/...",
      "likes": 442,
      "comments": 65,
      "reposts": 24
    }
  ]
}
```

## Architecture

```
scraper/
├── __init__.py           # Package exports
├── base.py              # BasePlatformScraper abstract class
├── session_manager.py   # Browser profile management
└── platforms/
    ├── __init__.py
    ├── threads.py       # ThreadsScraper implementation
    ├── facebook.py      # (Future) Facebook scraper
    └── x.py             # (Future) X/Twitter scraper
```

### Adding New Platforms

1. Create a new file in `scraper/platforms/` (e.g., `facebook.py`)
2. Inherit from `BasePlatformScraper`
3. Implement required methods:
   - `get_platform_name()` - Return platform name
   - `get_post_selectors()` - Return CSS selectors for posts
   - `extract_post_data()` - Extract post data from page
   - `scrape()` - Main scraping logic

Example:

```python
from scraper.base import BasePlatformScraper

class FacebookScraper(BasePlatformScraper):
    def get_platform_name(self) -> str:
        return "facebook"

    def get_post_selectors(self) -> list[str]:
        return ['div[role="article"]', 'div.userContentWrapper']

    def extract_post_data(self, page, selector: str) -> list[dict]:
        # Extract Facebook-specific data
        pass

    def scrape(self) -> dict:
        # Main scraping logic
        pass
```

## Session Persistence

Browser profiles are stored in `browser_profiles/{user_id}/`:
- Full browser data (cookies, storage, cache, etc.)
- Sessions survive restarts and reboots
- No need to re-login unless session expires
- Multiple user profiles supported

## Configuration

Limits can be set per scraper instance:

```python
scraper = ThreadsScraper(
    url="https://www.threads.com/@yannlecun",
    user_id="user1",
    post_limit=100,      # Stop after 100 posts
    time_limit=300,      # OR stop after 5 minutes
    scroll_delay=0.75    # Wait 0.75s between scrolls
)
```

## Files

- `scraper/` - Main scraper package
- `test_scraper.py` - Example usage and tests
- `save_session.py` - Simple CLI for creating sessions
- `run.sh` - Interactive runner script
- `browser_profiles/` - Persistent browser profiles (gitignored)
- `threads_data_*.json` - Scraped data files (gitignored)

## How It Works

1. **Session Creation**: Launches a browser, lets you log in manually, saves the complete browser profile
2. **Scraping**: Loads saved profile, navigates to URL, scrolls to load posts, extracts data
3. **Smart Scrolling**: Continues scrolling until post limit, time limit, or no new content
4. **Data Extraction**: Uses CSS selectors to find posts, JavaScript to extract engagement metrics

## Notes

- **Headful by default** - You can see what's happening in the browser
- **Rate limiting** - Configurable scroll delays prevent detection
- **Platform-specific** - Each platform has custom selectors and extraction logic
- **Extensible** - Easy to add new platforms by inheriting base class
