# save_session.py
from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, slow_mo=100)  # headful, slow for convenience
    context = browser.new_context()
    page = context.new_page()

    page.goto("https://www.threads.com/@yannlecun", wait_until="domcontentloaded")
    time.sleep(2)  # Wait for page to render
    print("🔓 Log in manually in the browser window...")

    # Keep browser open until you press Enter
    input("Press Enter after you've logged in to save the session...")

    # Save session (cookies + localStorage)
    context.storage_state(path="storage_state.json")
    print("✅ Session saved to storage_state.json")

    browser.close()
