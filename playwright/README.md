# Playwright Web Scraper

Web scraping tool for Threads (@yannlecun) using Playwright with session persistence.

## Setup

1. **Install dependencies:**
   ```bash
   uv sync
   ```

2. **Install Playwright browsers:**
   ```bash
   uv run playwright install
   ```

## Usage

### Quick Start (Interactive Script)

The easiest way to get started:

```bash
./run.sh
```

This interactive script lets you:
1. Save session (login manually)
2. Run scraper (requires saved session)
3. Run both (save session first, then scrape)

### Manual Usage

### Step 1: Save Session (One-time setup)

Run this script to log in manually and save your session:

```bash
uv run python save_session.py
```

This will:
- Open Chromium browser (headful mode)
- Navigate to https://www.threads.com/@yannlecun
- Allow you to log in manually
- Save your session to `storage_state.json` when you close the browser

### Step 2: Scrape with Saved Session

Once you have your session saved, run:

```bash
uv run python scrape_scroll.py
```

This will:
- Load your saved session (stay logged in)
- Auto-scroll through the feed
- Extract post data based on CSS selectors

## Customization

### Update CSS Selectors

In `scrape_scroll.py`, replace `.item-selector` with the actual selector for Threads posts:

```python
items = page.eval_on_selector_all(
    ".your-actual-selector",  # Update this
    "nodes => nodes.map(n => ({ text: n.innerText, link: n.querySelector('a')?.href }))"
)
```

### Adjust Scroll Settings

Modify scrolling behavior in `scrape_scroll.py`:

```python
auto_scroll(page, max_scrolls=300, delay=0.75)  # Adjust these values
```

### Debug Mode

Add screenshot capture for debugging:

```python
page.screenshot(path="last_page.png")
```

## How It Works

- **Headful mode**: See the browser in action
- **Storage state**: Saves cookies/localStorage for session persistence
- **Auto-scroll**: Scrolls until no new content loads
- **JavaScript extraction**: Uses `eval_on_selector_all()` to extract data

## Files

- `run.sh` - Interactive test script (easiest way to get started)
- `save_session.py` - Manual login and session saving
- `scrape_scroll.py` - Main scraping script with auto-scroll
- `storage_state.json` - Saved browser session (gitignored)
- `pyproject.toml` - Project dependencies
