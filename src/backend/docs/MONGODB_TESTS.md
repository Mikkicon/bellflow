# MongoDB Integration Tests

This directory contains two sets of tests for MongoDB integration with the scraper functionality:

## Test Files

### 1. `test_scraper_with_db_mock.py` (Recommended)
**Tests the scraper's MongoDB save logic using mocks - no database required**

✅ **Advantages:**
- Runs fast (no network latency)
- No database setup required
- Works in CI/CD pipelines
- Tests the save logic thoroughly

**Run with:**
```bash
pytest tests/test_scraper_with_db_mock.py -v
```

**What it tests:**
- ✅ Successful scraping saves data to MongoDB with correct structure
- ✅ Scraping errors are saved with status="failed"
- ✅ System handles database unavailability gracefully
- ✅ `save_scraper_result_to_db()` generates correct document structure
- ✅ Save function handles None responses (error case)
- ✅ Multiple saves create unique documents with different UUIDs

### 2. `test_scraper_mongodb.py`
**Tests actual MongoDB writes - requires live database connection**

⚠️ **Requirements:**
- MongoDB instance running (local or Atlas)
- Valid `MONGODB_URL` in `.env` file
- Network access to database

**Run with:**
```bash
pytest tests/test_scraper_mongodb.py -v
```

**What it tests:**
- ✅ End-to-end MongoDB write verification
- ✅ Document persistence and retrieval
- ✅ Error logging to database
- ✅ Multiple scrapes create separate documents
- ✅ MongoDB document schema validation

**Note:** These tests will be automatically skipped if MongoDB connection fails.

## MongoDB Document Structure

Both test files verify that scraped data is saved with this structure:

```python
{
    "id": "uuid-string",              # Unique identifier
    "timestamp": datetime,             # When data was collected
    "source_link": "url",             # URL that was scraped
    "status": "completed|failed",     # Processing status
    "raw_data": "json_string",        # Full ScraperResponse as JSON
    "error": "error_message",         # Error message if failed (optional)
    "created_at": datetime,           # Record creation time
    "updated_at": datetime            # Record update time
}
```

## Running All Tests

```bash
# Run all MongoDB tests (mocked + integration)
pytest tests/test_scraper*.py -v

# Run only mocked tests (fast, no DB required)
pytest tests/test_scraper_with_db_mock.py -v

# Run only integration tests (requires DB)
pytest tests/test_scraper_mongodb.py -v
```

## Troubleshooting

### MongoDB Connection Issues

If you see SSL/TLS errors:
1. Check your `MONGODB_URL` in `.env`
2. Ensure MongoDB Atlas allows your IP address
3. Verify credentials are correct
4. Try using a local MongoDB instance for testing

### Running Without MongoDB

If MongoDB is unavailable, use the mocked tests:
```bash
pytest tests/test_scraper_with_db_mock.py -v
```

These provide the same test coverage without requiring a database.

## What Changed

### Fixed Issues
1. **Uncommented `JobResponse` and `JobStatusResponse`** in `app/models/schemas.py`
   - These were commented out but imported in `scraper.py`
   - Now properly defined for Twitter/LinkedIn async scraping support

### New Test Coverage
- Tests verify the `save_scraper_result_to_db()` function
- Tests check document structure matches schema
- Tests ensure errors are logged to database
- Tests verify graceful degradation when DB is unavailable

## Comparison to `test_scrape_endpoint_valid_request`

The original test (`test_scraper.py:test_scrape_endpoint_valid_request`):
- Tests API endpoint response structure
- Doesn't verify MongoDB writes
- Accepts 200/404/500 status codes

The new tests:
- ✅ Mock the scraper to return consistent test data
- ✅ Verify MongoDB save is called with correct data
- ✅ Check document structure in database
- ✅ Test error handling and logging
- ✅ Verify multiple writes create unique documents
