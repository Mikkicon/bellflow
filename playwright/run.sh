#!/bin/bash

echo "🎭 Playwright Threads Scraper"
echo "=============================="
echo ""
echo "🔓 Step 1: Saving session..."
echo "A browser will open. Log in to Threads, then press Enter in the terminal."
echo ""

uv run python save_session.py

if [ -f "storage_state.json" ]; then
    echo ""
    echo "✅ Session saved successfully!"
    echo ""
    echo "⏳ Waiting 3 seconds before starting scraper..."
    sleep 3
    echo ""
    echo "🚀 Step 2: Running scraper..."
    echo ""
    uv run python scrape_scroll.py
else
    echo ""
    echo "❌ Session save failed. Scraper not started."
    exit 1
fi
