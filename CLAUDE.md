# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

BellFlow is a social media scraping API built with FastAPI and Playwright. It provides endpoints to scrape posts from social media platforms (currently supports Threads.com) with session persistence and configurable limits.

## Development Setup

### Backend Setup
```bash
cd src/backend
python3 -m venv venv
source venv/bin/activate  # On Windows WSL: wsl && source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

### Running the Server
```bash
# From src/backend directory
python -m uvicorn app.main:app --reload

# Or use the convenience script
bash run.sh
```

The API runs on `http://localhost:8000` with interactive docs at `/docs` and `/redoc`.

## Testing

```bash
# Run scraper tests
cd src/backend
pytest tests/test_scraper.py -v

# Run all tests
pytest tests/ -v
```

## Architecture

### Backend Structure (`src/backend/`)
- **`app/main.py`**: FastAPI application entry point with CORS middleware
- **`app/routers/`**: API route handlers
  - `sample.py`: Sample CRUD endpoints for items
  - `scraper.py`: Scraping endpoints (`POST /v1/scrape`)
- **`app/models/schemas.py`**: Pydantic models for request/response validation
- **`app/scraper/`**: Core scraping functionality
  - `base.py`: `BasePlatformScraper` abstract class defining the scraper interface
  - `session_manager.py`: `SessionManager` for browser profile persistence
  - `platforms/`: Platform-specific scrapers (e.g., `threads.py`)

### Scraper Architecture

The scraper follows an object-oriented plugin pattern:

1. **`BasePlatformScraper`** (abstract base class): Defines common scraping logic
   - `get_platform_name()`: Returns platform identifier
   - `get_post_selectors()`: Returns CSS selectors to try for finding posts
   - `extract_post_data()`: Extracts post data from the page
   - `scrape()`: Main scraping orchestration method
   - Common utilities: `scroll_and_load()`, `find_post_selector()`, `should_continue_scraping()`

2. **Platform-specific scrapers** (e.g., `ThreadsScraper`): Implement platform-specific logic
   - Each scraper extends `BasePlatformScraper`
   - Provides platform-specific CSS selectors and data extraction logic

3. **`SessionManager`**: Manages browser profiles per user_id
   - Stores browser profiles in `browser_profiles/{user_id}/`
   - Enables session persistence (login states, cookies)
   - `create_session()`: Opens browser for manual login/setup
   - `get_profile_path()`: Returns path to stored browser profile

### Key Design Patterns

- **Strategy Pattern**: Each platform scraper implements the same interface but with platform-specific behavior
- **Session Isolation**: Browser profiles are isolated per `user_id` to prevent cross-user contamination
- **Limit-based Control**: Supports both post count limits and time-based limits
- **Progressive Scrolling**: Dynamically loads content by scrolling and monitoring post count changes

## API Usage

### Scraping Endpoint

**POST** `/v1/scrape` - Scrape posts from a social media profile

Request body:
```json
{
  "url": "https://www.threads.com/@username",
  "user_id": "user1",
  "post_limit": 100,
  "time_limit": 300,
  "scroll_delay": 0.75,
  "headless": false
}
```

- `url`: Profile URL to scrape (currently only Threads.com supported)
- `user_id`: Identifier for browser profile isolation (required for session persistence)
- `post_limit`: Max posts to scrape (optional, null = unlimited)
- `time_limit`: Max time in seconds (optional, null = unlimited)
- `scroll_delay`: Delay between scrolls in seconds (0.1-5.0, default: 0.75)
- `headless`: Run browser in headless mode (default: false)

**Important**: Before first scrape, create a browser profile using `SessionManager.create_session()` for manual login. This opens a browser where you can authenticate. The session persists for future scrapes.

## Browser Profiles

Browser profiles are stored in `browser_profiles/{user_id}/` and contain:
- Cookies and session data
- Login state
- Browser preferences

This enables authenticated scraping without re-logging in for each request.

## Adding New Platforms

To add a new platform scraper:

1. Create `app/scraper/platforms/{platform}.py`
2. Extend `BasePlatformScraper`
3. Implement required abstract methods:
   - `get_platform_name()`
   - `get_post_selectors()`
   - `extract_post_data()`
   - `scrape()`
4. Update `app/scraper/__init__.py` to export the new scraper
5. Add platform detection logic in `app/routers/scraper.py`

## External Scripts

The `browser/` directory contains standalone Playwright scripts for testing:
- `scrape_threads.py`: Standalone Threads scraper
- `scrape_threads_openai.py`: Threads scraper with OpenAI integration
- `scrape_x_openai.py`: X/Twitter scraper (experimental)

These are development/testing tools and are separate from the FastAPI backend.

## Dependencies

- **FastAPI**: Web framework
- **Playwright**: Browser automation for scraping
- **Pydantic**: Data validation and schemas
- **pytest**: Testing framework
- **uvicorn**: ASGI server

## Important Notes

- Platform detection is URL-based (checks if "threads.com" in URL)
- Browser profiles persist across server restarts
- Headless mode (`headless: true`) is recommended for production
- Use appropriate `scroll_delay` values to avoid rate limiting/detection
- The scraper intelligently tries multiple CSS selectors until one succeeds
- Both `post_limit` and `time_limit` can be combined; whichever is reached first stops scraping
