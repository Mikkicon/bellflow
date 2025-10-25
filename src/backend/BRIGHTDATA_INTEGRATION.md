# Bright Data API Integration

This document describes the integration of Bright Data API as an alternative scraping engine for the BellFlow scraping library.

## Overview

The scraping library now supports two engines:

1. **Playwright Engine**: Browser-based scraping (synchronous)
   - Platform: Threads
   - Returns results immediately

2. **Bright Data Engine**: API-based scraping (asynchronous)
   - Platforms: Twitter/X, LinkedIn
   - Returns job ID for polling

## Architecture

### Engine Factory Pattern

```
┌─────────────────────────────────────────────────────────┐
│                    API Router                            │
│  /v1/scrape, /v1/scrape/status, /v1/scrape/result       │
└───────────────────┬─────────────────────────────────────┘
                    │
                    ├─── Threads → ThreadsScraper (BasePlatformScraper)
                    │                    ↓
                    │              PlaywrightEngine
                    │
                    ├─── Twitter → TwitterScraper (EngineScraper)
                    │                    ↓
                    │              BrightDataEngine
                    │
                    └─── LinkedIn → LinkedInScraper (EngineScraper)
                                         ↓
                                   BrightDataEngine
```

### Key Components

#### 1. Engine Abstraction (`app/scraper/engines/`)

- **`BaseScraperEngine`**: Abstract base class for all engines
  - `is_async()`: Returns whether engine is async
  - `initialize_scrape()`: Start scraping job
  - `get_status()`: Get job status
  - `get_results()`: Get job results
  - `cancel_job()`: Cancel running job

- **`PlaywrightEngine`**: Wraps Playwright browser automation
  - Synchronous (returns results immediately)
  - Uses browser profiles for session persistence

- **`BrightDataEngine`**: Wraps Bright Data API
  - Asynchronous (returns job ID, requires polling)
  - Auto-converts post_limit to date ranges
  - Supports Twitter and LinkedIn datasets

#### 2. Job Manager (`app/scraper/job_manager.py`)

- Centralized job tracking across all engines
- In-memory storage (can be upgraded to Redis/DB)
- Methods:
  - `create_job()`: Create new scraping job
  - `get_job()`: Get job status (polls engine if async)
  - `get_job_results()`: Get completed job results
  - `list_user_jobs()`: List jobs for a user
  - `cleanup_old_jobs()`: Remove old completed jobs

#### 3. Platform Scrapers

- **`ThreadsScraper`**: Extends `BasePlatformScraper` (backward compatible)
- **`TwitterScraper`**: Uses `EngineScraper` wrapper with `BrightDataEngine`
- **`LinkedInScraper`**: Uses `EngineScraper` wrapper with `BrightDataEngine`

#### 4. API Endpoints

- **POST `/v1/scrape`**: Submit scraping request
  - Returns `ScraperResponse` for Threads (sync)
  - Returns `JobResponse` for Twitter/LinkedIn (async)

- **GET `/v1/scrape/status/{job_id}`**: Check job status
  - Returns `JobStatusResponse` with current status

- **GET `/v1/scrape/result/{job_id}`**: Get completed job results
  - Returns `ScraperResponse` when job is completed
  - Returns 400 if job not completed yet

## Setup

### 1. Install Dependencies

```bash
cd src/backend
pip install -r requirements.txt
```

### 2. Configure Environment Variables

The application uses python-dotenv to automatically load environment variables from a `.env` file.

#### Step 2.1: Create your .env file

```bash
cd src/backend
cp .env.example .env
```

#### Step 2.2: Get your Bright Data API Key

1. Sign up at: https://brightdata.com/
2. Navigate to **Dashboard** → **API Access**
3. Create or copy your API token
4. The key format looks like: `abcd1234-5678-90ef-ghij-klmnopqrstuv`

#### Step 2.3: Edit .env file

Open `.env` in your editor and replace the placeholder:

```env
# Before (placeholder)
BRIGHTDATA_API_KEY=your_brightdata_api_key_here

# After (your actual key)
BRIGHTDATA_API_KEY=abcd1234-5678-90ef-ghij-klmnopqrstuv
```

**Important Notes:**
- The `.env` file is in `.gitignore` and will NOT be committed to version control
- The environment variables are loaded automatically when the app starts (via `load_dotenv()` in `app/main.py`)
- If you only use Threads scraping (Playwright), you can skip this step
- For Twitter/LinkedIn scraping, this API key is **required**

#### Step 2.4: Verify environment loading

Test that your API key is loaded correctly:

```bash
cd src/backend
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('API Key loaded:', 'Yes' if os.getenv('BRIGHTDATA_API_KEY') else 'No')"
```

Expected output:
```
API Key loaded: Yes
```

### 3. Run the Server

```bash
cd src/backend
python -m uvicorn app.main:app --reload
```

The `.env` file will be automatically loaded on startup. You should see no errors related to missing API keys (unless you try to use Twitter/LinkedIn without the key).

## Usage Examples

### Scraping Threads (Synchronous)

**Request:**
```bash
curl -X POST "http://localhost:8000/v1/scrape" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.threads.com/@username",
    "user_id": "user1",
    "post_limit": 50,
    "headless": true
  }'
```

**Response (immediate):**
```json
{
  "scraped_at": "20251025_143022",
  "url": "https://www.threads.com/@username",
  "platform": "threads",
  "user_id": "user1",
  "total_items": 50,
  "post_limit": 50,
  "elapsed_time": 45.3,
  "items": [...]
}
```

### Scraping Twitter/X (Asynchronous)

**Step 1: Submit scraping job**
```bash
curl -X POST "http://localhost:8000/v1/scrape" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://twitter.com/elonmusk",
    "user_id": "user1",
    "post_limit": 100
  }'
```

**Response (immediate, returns job ID):**
```json
{
  "job_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "running",
  "platform": "twitter",
  "url": "https://twitter.com/elonmusk",
  "user_id": "user1",
  "created_at": "2025-10-25T14:30:22.123Z",
  "message": "Scraping job submitted to Bright Data"
}
```

**Step 2: Check job status**
```bash
curl "http://localhost:8000/v1/scrape/status/a1b2c3d4-e5f6-7890-abcd-ef1234567890"
```

**Response:**
```json
{
  "job_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "completed",
  "platform": "twitter",
  "url": "https://twitter.com/elonmusk",
  "user_id": "user1",
  "created_at": "2025-10-25T14:30:22.123Z",
  "updated_at": "2025-10-25T14:32:45.678Z",
  "progress": {"message": "Scraping completed"},
  "error": null
}
```

**Step 3: Get results**
```bash
curl "http://localhost:8000/v1/scrape/result/a1b2c3d4-e5f6-7890-abcd-ef1234567890"
```

**Response:**
```json
{
  "scraped_at": "20251025_143245",
  "url": "https://twitter.com/elonmusk",
  "platform": "twitter",
  "user_id": "user1",
  "total_items": 100,
  "elapsed_time": 143.2,
  "items": [
    {
      "text": "Tweet content...",
      "link": "https://twitter.com/elonmusk/status/...",
      "likes": 50000,
      "comments": 5000,
      "reposts": 10000,
      "date_posted": "2025-10-25T12:00:00.000Z",
      "views": 1000000
    }
  ]
}
```

### Scraping LinkedIn (Asynchronous)

Same as Twitter, but use LinkedIn profile URL:

```bash
curl -X POST "http://localhost:8000/v1/scrape" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.linkedin.com/in/username",
    "user_id": "user1",
    "post_limit": 50
  }'
```

Then poll `/v1/scrape/status/{job_id}` and retrieve results with `/v1/scrape/result/{job_id}`.

## Post Limit to Date Range Conversion

Bright Data API uses date ranges instead of post limits. The engine automatically converts:

- `post_limit >= 500` or `None`: Last 365 days
- `post_limit >= 100`: Last 90 days
- `post_limit >= 50`: Last 30 days
- `post_limit < 50`: Last 7 days

## Job Status Flow

```
PENDING → RUNNING → COMPLETED
                  ↘ FAILED
```

- **PENDING**: Job created, not yet submitted to Bright Data
- **RUNNING**: Job submitted, Bright Data is scraping
- **COMPLETED**: Scraping finished, results available
- **FAILED**: Error occurred during scraping

## Error Handling

### Bright Data API Errors

If Bright Data returns an error or warning, the job will be marked as FAILED with the error message:

```json
{
  "status": "failed",
  "error": "Bright Data error: dead_page - No posts found"
}
```

### Missing API Key

If `BRIGHTDATA_API_KEY` is not set:

```
EnvironmentError: BRIGHTDATA_API_KEY environment variable is not set
```

### Job Not Found

```
HTTP 404: Job {job_id} not found
```

### Job Not Completed

```
HTTP 400: Job is not completed yet. Current status: running
```

## Supported Platforms

| Platform | Engine | Scraping Mode | Status |
|----------|--------|---------------|--------|
| Threads | Playwright | Synchronous | ✅ Production |
| Twitter/X | Bright Data | Asynchronous | ✅ Production |
| LinkedIn | Bright Data | Asynchronous | ✅ Production |

## Adding New Platforms

To add a new platform using Bright Data:

1. Add dataset ID to `BrightDataEngine.DATASET_IDS`
2. Create new scraper in `app/scraper/platforms/{platform}.py`
3. Update `app/scraper/__init__.py` to export new scraper
4. Add platform detection in `app/routers/scraper.py`
5. Update data transformation in `BrightDataEngine._transform_brightdata_response()`

## Testing

```bash
cd src/backend
pytest tests/ -v
```

## Monitoring

The job manager provides statistics:

```python
from app.scraper import job_manager

stats = job_manager.get_stats()
# Returns:
# {
#   "total_jobs": 150,
#   "status_counts": {
#     "pending": 2,
#     "running": 10,
#     "completed": 130,
#     "failed": 8
#   },
#   "total_users": 25
# }
```

## Cleanup

Old completed/failed jobs are kept in memory. To clean up:

```python
from app.scraper import job_manager

# Remove jobs older than 24 hours
job_manager.cleanup_old_jobs(max_age_hours=24)
```

Consider running this periodically in production (e.g., via cron job or background task).

## Future Improvements

- [ ] Persistent job storage (Redis/PostgreSQL)
- [ ] Webhook notifications for job completion
- [ ] Rate limiting per user
- [ ] Job prioritization
- [ ] Batch scraping requests
- [ ] Job retry mechanism
- [ ] Real-time progress updates via WebSocket
- [ ] Cost tracking per job (Bright Data charges per request)

## Troubleshooting

### Issue: "BRIGHTDATA_API_KEY environment variable is not set"

**Solution**: Create `.env` file with your API key:
```bash
echo "BRIGHTDATA_API_KEY=your_key_here" > src/backend/.env
```

### Issue: Job stuck in "running" status

**Possible causes**:
1. Bright Data still processing (can take 1-5 minutes)
2. Profile has no posts or private profile
3. Invalid URL

**Solution**: Wait a few minutes, then check status again. If still stuck after 10 minutes, the job likely failed on Bright Data's side.

### Issue: "No posts found" error

**Possible causes**:
1. Private profile
2. Profile doesn't exist
3. No posts in the specified date range

**Solution**: Verify profile URL is correct and public. Try increasing `post_limit` to expand date range.

## License

This integration maintains the same license as the parent project.
