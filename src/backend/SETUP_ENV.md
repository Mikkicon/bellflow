# Quick Setup Guide - Environment Variables

This guide shows how to configure environment variables for BellFlow API.

## Why Environment Variables?

Environment variables keep sensitive data (like API keys) separate from your code:
- ✅ **Security**: API keys are not committed to version control
- ✅ **Flexibility**: Different keys for development/production
- ✅ **Convenience**: Automatic loading via `python-dotenv`

## Setup Steps

### 1. Copy the example file

```bash
cd src/backend
cp .env.example .env
```

### 2. Edit the .env file

Open `.env` in your text editor:

```env
# Before (placeholder)
BRIGHTDATA_API_KEY=your_brightdata_api_key_here

# After (your actual key)
BRIGHTDATA_API_KEY=bd_abc123def456ghi789
```

### 3. Get your Bright Data API Key (if needed)

**Only required for Twitter/X and LinkedIn scraping**

1. Go to: https://brightdata.com/
2. Sign up or log in
3. Navigate to: **Dashboard** → **API Access**
4. Copy your API token
5. Paste it in `.env` file

**Skip this if you only use Threads scraping!** Threads uses Playwright (browser automation) and doesn't need an API key.

### 4. Verify it works

Test that your environment variables are loaded:

```bash
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('API Key:', '✅ Loaded' if os.getenv('BRIGHTDATA_API_KEY') else '❌ Missing')"
```

Expected output:
```
API Key: ✅ Loaded
```

### 5. Start the server

```bash
python -m uvicorn app.main:app --reload
```

The `.env` file is automatically loaded when the app starts (via `load_dotenv()` in `app/main.py`).

## How It Works

### Behind the Scenes

```python
# app/main.py (top of file)
from dotenv import load_dotenv
import os

load_dotenv()  # ← Loads .env file into os.environ
```

```python
# app/scraper/engines/brightdata_engine.py
self.api_key = os.environ.get("BRIGHTDATA_API_KEY")  # ← Reads from environment
```

### File Structure

```
src/backend/
├── .env.example          # Template (committed to git)
├── .env                  # Your actual keys (in .gitignore)
├── app/
│   └── main.py          # Loads .env on startup
└── ...
```

## Quick Reference

| Platform | Engine | Needs API Key? |
|----------|--------|----------------|
| Threads | Playwright | ❌ No |
| Twitter/X | Bright Data | ✅ Yes |
| LinkedIn | Bright Data | ✅ Yes |

## Common Issues

### Issue: "BRIGHTDATA_API_KEY environment variable is not set"

**Cause**: You're trying to scrape Twitter/LinkedIn without the API key.

**Solution**:
1. Create `.env` file: `cp .env.example .env`
2. Add your API key to `.env`
3. Restart the server

### Issue: API key not loading

**Solution**:
1. Make sure `.env` file is in `src/backend/` directory
2. Check there's no typo: `BRIGHTDATA_API_KEY` (not `BRIGHT_DATA_API_KEY`)
3. No quotes needed: `BRIGHTDATA_API_KEY=abc123` (not `"abc123"`)
4. Restart the server after editing `.env`

### Issue: .env file is committed to git

**Solution**:
1. Remove from git: `git rm --cached .env`
2. Verify `.gitignore` contains `.env`
3. Never commit `.env` - only commit `.env.example`

## Security Best Practices

✅ **DO:**
- Keep `.env` file in `.gitignore`
- Use different API keys for development and production
- Rotate API keys regularly
- Share `.env.example` (without real keys)

❌ **DON'T:**
- Commit `.env` to version control
- Share your actual API keys in chat/email
- Use production keys in development
- Hardcode API keys in source code

## Additional Variables

You can add more environment variables to `.env`:

```env
# Bright Data
BRIGHTDATA_API_KEY=your_key_here

# Application settings
DEBUG=True
LOG_LEVEL=INFO
PORT=8000

# CORS (for production)
ALLOWED_ORIGINS=https://yourapp.com,https://www.yourapp.com
```

Then access them in your code:

```python
import os

debug_mode = os.getenv("DEBUG", "False") == "True"
log_level = os.getenv("LOG_LEVEL", "INFO")
port = int(os.getenv("PORT", "8000"))
```

## Next Steps

- For complete setup instructions, see: [`BRIGHTDATA_INTEGRATION.md`](./BRIGHTDATA_INTEGRATION.md)
- For architecture details, see: [`ARCHITECTURE.md`](./ARCHITECTURE.md)
- For project overview, see: [`CLAUDE.md`](../../CLAUDE.md)

## Need Help?

- Bright Data docs: https://docs.brightdata.com/
- API documentation: Check `/docs` endpoint when server is running
- Issues: File a bug report in the project repository
