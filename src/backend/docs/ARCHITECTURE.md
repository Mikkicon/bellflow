# Scraper Architecture: Engines vs Platforms

## Overview

The scraper library uses a **separation of concerns** pattern that distinguishes between:
- **Engines** (HOW to scrape) - The underlying technology/mechanism
- **Platforms** (WHAT to scrape) - The specific social media platform

## Directory Structure

```
app/scraper/
├── engines/                    # HOW to scrape (technology layer)
│   ├── base_engine.py         # Abstract interface for all engines
│   ├── playwright_engine.py   # Browser automation engine
│   └── brightdata_engine.py   # API-based scraping engine
│
└── platforms/                  # WHAT to scrape (platform layer)
    ├── threads.py             # Threads.com scraper
    ├── twitter.py             # Twitter/X scraper
    └── linkedin.py            # LinkedIn scraper
```

---

## Engines (`app/scraper/engines/`)

**Definition**: Engines define the **underlying mechanism** used to perform scraping.

### What They Do
- Handle the actual **execution** of scraping operations
- Manage **job lifecycle** (create, poll status, get results)
- Abstract away the **technical implementation** details
- Provide a **consistent interface** regardless of technology

### Types of Engines

#### 1. **PlaywrightEngine** (Browser Automation)
- **Technology**: Playwright (headless browser)
- **Mode**: Synchronous (returns results immediately)
- **Use case**: Platforms that require browser rendering, JavaScript execution, or login sessions
- **Example**: Threads.com (requires login, dynamic content)

**How it works:**
```python
engine = PlaywrightEngine()
job = engine.initialize_scrape(url, user_id, platform="threads")
# Job is completed immediately (synchronous)
results = job.result  # Available right away
```

#### 2. **BrightDataEngine** (API-based)
- **Technology**: Bright Data API (third-party service)
- **Mode**: Asynchronous (submit job, poll for results)
- **Use case**: Platforms with complex anti-scraping, or where API access is available
- **Example**: Twitter/X, LinkedIn

**How it works:**
```python
engine = BrightDataEngine(api_key="...")
job = engine.initialize_scrape(url, user_id, platform="twitter")
# Job is pending/running (asynchronous)
while job.status != "completed":
    job = engine.get_status(job.job_id)
    sleep(5)
results = engine.get_results(job.job_id)
```

### BaseScraperEngine Interface

All engines implement this interface:

```python
class BaseScraperEngine(ABC):
    def is_async(self) -> bool:
        """Returns True if async, False if sync"""

    def initialize_scrape(...) -> ScrapeJob:
        """Start a scraping job"""

    def get_status(job_id) -> ScrapeJob:
        """Get current job status"""

    def get_results(job_id) -> Dict:
        """Get completed results"""

    def cancel_job(job_id) -> bool:
        """Cancel running job"""
```

---

## Platforms (`app/scraper/platforms/`)

**Definition**: Platforms define the **specific social media site** being scraped and its unique characteristics.

### What They Do
- Know **platform-specific details**: URL patterns, CSS selectors, data structure
- Define **what data to extract**: posts, likes, comments, etc.
- Handle **platform quirks**: authentication requirements, pagination style
- Choose the **appropriate engine** for the platform

### Platform Examples

#### 1. **ThreadsScraper** (Threads.com)
- **Engine**: PlaywrightEngine
- **Why**: Requires login, dynamic content, JavaScript rendering
- **Selectors**: `div[data-pressable-container="true"]`, `article`, etc.
- **Data**: text, link, likes, comments, reposts

**Implementation:**
```python
class ThreadsScraper(BasePlatformScraper):
    def get_platform_name(self) -> str:
        return "threads"

    def get_post_selectors(self) -> List[str]:
        return ['article', 'div[data-pressable-container="true"]', ...]

    def extract_post_data(self, page, selector) -> List[Dict]:
        # Threads-specific extraction logic
        return items

    def scrape(self) -> Dict:
        # Uses Playwright engine internally
        ...
```

#### 2. **TwitterScraper** (Twitter/X)
- **Engine**: BrightDataEngine
- **Why**: Complex anti-scraping, rate limits, API available via Bright Data
- **Dataset ID**: `gd_lwxkxvnf1cynvib9co`
- **Data**: tweets, likes, retweets, replies, views

**Implementation:**
```python
class TwitterScraper(EngineScraper):
    def __init__(self, url, user_id, ...):
        engine = BrightDataEngine(api_key=api_key)
        super().__init__(
            engine=engine,
            platform="twitter",
            url=url,
            ...
        )
```

#### 3. **LinkedInScraper** (LinkedIn)
- **Engine**: BrightDataEngine
- **Why**: Strong anti-scraping, professional network protection
- **Dataset ID**: `gd_l7q7dkf244hwzk73o`
- **Data**: posts, likes, comments, shares

---

## Key Differences

| Aspect | Engines | Platforms |
|--------|---------|-----------|
| **Purpose** | HOW to scrape | WHAT to scrape |
| **Responsibility** | Execution mechanism | Platform knowledge |
| **Examples** | Playwright, Bright Data API | Threads, Twitter, LinkedIn |
| **Technology** | Browser, HTTP, APIs | Social media sites |
| **Abstraction Level** | Low-level (technical) | High-level (business) |
| **Reusability** | One engine → many platforms | One platform → one engine |
| **Changes When** | Scraping technology changes | Platform structure changes |

---

## Analogy

Think of it like transportation:

### Engines = Vehicles (HOW to travel)
- **Car** (PlaywrightEngine): Drive yourself, full control, slow but flexible
- **Airplane** (BrightDataEngine): Fast, professional service, less control

### Platforms = Destinations (WHERE to go)
- **New York** (Threads): Need a car (Playwright) because of complex local navigation
- **Tokyo** (Twitter): Need a plane (Bright Data) because too complex to drive
- **London** (LinkedIn): Need a plane (Bright Data) because of distance/complexity

You choose the **vehicle** (engine) based on the **destination** (platform) requirements!

---

## How They Work Together

```
User Request: "Scrape Twitter"
         ↓
    API Router (scraper.py)
         ↓
    Detects platform from URL
         ↓
    Creates TwitterScraper ──→ Uses BrightDataEngine
         ↓                          ↓
    Returns job_id          Submits to Bright Data API
         ↓                          ↓
    User polls status       Polls Bright Data for status
         ↓                          ↓
    Gets results            Transforms Bright Data response
```

### Example Flow (Twitter)

1. **API receives request**: `POST /v1/scrape` with `url="https://twitter.com/elonmusk"`

2. **Router detects platform**:
   ```python
   if "twitter.com" in url_lower:
       scraper = TwitterScraper(...)  # Platform
   ```

3. **Platform chooses engine**:
   ```python
   class TwitterScraper:
       def __init__(...):
           engine = BrightDataEngine()  # Engine
   ```

4. **Engine executes**:
   ```python
   job = engine.initialize_scrape(...)
   # Submits to Bright Data API
   ```

5. **Returns job info**:
   ```json
   {
     "job_id": "abc-123",
     "status": "running",
     "platform": "twitter"
   }
   ```

---

## Adding New Platforms

### If using existing engine (e.g., Bright Data):

1. Add dataset ID to `BrightDataEngine.DATASET_IDS`
2. Create new platform scraper in `platforms/instagram.py`
3. Update router to detect Instagram URLs
4. Done! Uses existing engine

### If needing new engine (e.g., Selenium):

1. Create `engines/selenium_engine.py` implementing `BaseScraperEngine`
2. Create platform scraper using the new engine
3. Update router
4. Done! Other platforms can reuse this engine

---

## Benefits of This Architecture

### ✅ Separation of Concerns
- Engine changes don't affect platform logic
- Platform changes don't affect engine logic

### ✅ Reusability
- One engine can support multiple platforms
- Example: BrightDataEngine supports both Twitter AND LinkedIn

### ✅ Flexibility
- Easy to add new platforms using existing engines
- Easy to add new engines for existing platforms

### ✅ Testability
- Test engines independently of platforms
- Mock engines when testing platforms

### ✅ Maintainability
- Clear boundaries between technical and business logic
- Changes are localized to specific layers

---

## Real-World Mapping

| Platform | Engine | Reason |
|----------|--------|--------|
| Threads | Playwright | Requires login, session persistence, dynamic JS |
| Twitter | Bright Data | Complex anti-bot, rate limits, API available |
| LinkedIn | Bright Data | Professional network, strong protection |
| Instagram* | Bright Data | Similar to Twitter requirements |
| Facebook* | Bright Data | Complex anti-scraping measures |

*Future platforms

---

## Code Organization Summary

```
Engines (HOW):
  - BaseScraperEngine          → Interface
  - PlaywrightEngine           → Browser automation
  - BrightDataEngine           → API scraping

Platforms (WHAT):
  - ThreadsScraper             → Threads.com knowledge
  - TwitterScraper             → Twitter/X knowledge
  - LinkedInScraper            → LinkedIn knowledge

Supporting:
  - JobManager                 → Tracks jobs across all engines
  - SessionManager             → Browser profiles (Playwright only)
  - EngineScraper              → Helper wrapper for engine-based scrapers
```

---

## Summary

**Engines** are the **tools/vehicles** you use to scrape.
**Platforms** are the **destinations/sites** you scrape.

- Want to scrape **Threads**? Use **Playwright engine** (browser)
- Want to scrape **Twitter**? Use **Bright Data engine** (API)
- Want to add **Instagram**? Pick an engine, create platform scraper

The architecture keeps these concerns separate, making the codebase flexible, maintainable, and scalable! 🚀
