# Scraper API Usage

## Setup

1. **Install dependencies:**
   ```bash
   cd src/backend
   pip install -r requirements.txt
   playwright install chromium
   ```

2. **Run the server:**
   ```bash
   python -m uvicorn app.main:app --reload
   ```

   The API will be available at `http://localhost:8000`

## API Endpoint

### POST /v1/scrape

Scrape posts from a social media profile (currently supports Threads).

**URL:** `http://localhost:8000/v1/scrape`

**Method:** POST

**Request Body:**

```json
{
  "url": "https://www.threads.com/@yannlecun",
  "user_id": "user1",
  "post_limit": 100,
  "time_limit": 300,
  "scroll_delay": 0.75,
  "headless": false
}
```

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `url` | string | Yes | Profile URL to scrape (e.g., https://www.threads.com/@username) |
| `user_id` | string | Yes | User ID for browser profile isolation |
| `post_limit` | integer | No | Maximum number of posts to scrape |
| `time_limit` | integer | No | Maximum scraping time in seconds |
| `scroll_delay` | float | No | Delay between scrolls in seconds (0.1-5.0, default: 0.75) |
| `headless` | boolean | No | Run browser in headless mode (default: false) |

**Response (Success - 200 OK):**

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
  ],
  "error": null
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `scraped_at` | string | Timestamp when scraping was performed |
| `url` | string | The URL that was scraped |
| `platform` | string | Platform name (e.g., "threads") |
| `user_id` | string | User ID used for the scraping session |
| `total_items` | integer | Number of posts scraped |
| `post_limit` | integer | Post limit that was set (if any) |
| `time_limit` | integer | Time limit that was set (if any) |
| `elapsed_time` | float | Time taken to complete scraping (seconds) |
| `selector_used` | string | CSS selector used to find posts |
| `items` | array | Array of scraped posts |
| `error` | string | Error message (null if successful) |

**Post Data Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `text` | string | Post text content |
| `link` | string | Link to the post (may be null) |
| `likes` | integer | Number of likes (may be null) |
| `comments` | integer | Number of comments (may be null) |
| `reposts` | integer | Number of reposts (may be null) |

**Error Responses:**

**400 Bad Request** - Unsupported platform:
```json
{
  "detail": "Unsupported platform. Currently only Threads.com is supported. URL: https://www.example.com/user"
}
```

**404 Not Found** - Browser profile not found:
```json
{
  "detail": "No browser profile found for user 'user1'. Please run create_session() first."
}
```

**422 Validation Error** - Invalid request:
```json
{
  "detail": [
    {
      "loc": ["body", "url"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

**500 Internal Server Error** - Scraping failed:
```json
{
  "detail": "An unexpected error occurred: ..."
}
```

## Usage Examples

### cURL

```bash
# Basic scrape with post limit
curl -X POST "http://localhost:8000/v1/scrape" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.threads.com/@yannlecun",
    "user_id": "user1",
    "post_limit": 50
  }'

# Scrape with time limit
curl -X POST "http://localhost:8000/v1/scrape" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.threads.com/@yannlecun",
    "user_id": "user1",
    "time_limit": 120
  }'

# Headless mode (no browser window)
curl -X POST "http://localhost:8000/v1/scrape" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.threads.com/@yannlecun",
    "user_id": "user1",
    "post_limit": 10,
    "headless": true
  }'
```

### Python

```python
import requests

# Scrape request
response = requests.post(
    "http://localhost:8000/v1/scrape",
    json={
        "url": "https://www.threads.com/@yannlecun",
        "user_id": "user1",
        "post_limit": 100,
        "time_limit": 300,
        "headless": False
    }
)

# Check response
if response.status_code == 200:
    data = response.json()
    print(f"Scraped {data['total_items']} posts in {data['elapsed_time']}s")

    # Access posts
    for post in data['items'][:5]:  # First 5 posts
        print(f"Text: {post['text'][:100]}...")
        print(f"Likes: {post['likes']}, Comments: {post['comments']}")
else:
    print(f"Error: {response.status_code}")
    print(response.json())
```

### JavaScript/Fetch

```javascript
// Scrape request
fetch('http://localhost:8000/v1/scrape', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    url: 'https://www.threads.com/@yannlecun',
    user_id: 'user1',
    post_limit: 100,
    headless: false
  })
})
.then(response => response.json())
.then(data => {
  console.log(`Scraped ${data.total_items} posts`);
  console.log('First post:', data.items[0]);
})
.catch(error => console.error('Error:', error));
```

## Testing

Run the tests:

```bash
cd src/backend
pytest tests/test_scraper.py -v
```

## Interactive API Documentation

Once the server is running, you can access:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

These provide interactive API documentation where you can test the endpoints directly in your browser.

## Creating Browser Profiles

Before scraping, you need to create a browser profile for the user_id:

```python
from app.scraper import SessionManager

session_mgr = SessionManager()
session_mgr.create_session(
    user_id="user1",
    url="https://www.threads.com/@yannlecun"
)
```

This opens a browser where you can log in manually. The session is saved and can be reused for future scraping requests.

## Notes

- **First-time setup**: Create a browser profile using `SessionManager.create_session()` before making scrape requests
- **Browser profiles**: Stored in `browser_profiles/{user_id}/` and persist across restarts
- **Rate limiting**: Use appropriate `scroll_delay` values to avoid detection
- **Platform support**: Currently only Threads.com is supported. More platforms coming soon.
- **Headless mode**: Set `headless: true` for background scraping (useful in production)
