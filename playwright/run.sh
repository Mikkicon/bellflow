#!/bin/bash

echo "🎭 Playwright Multi-Platform Scraper"
echo "=============================="
echo ""
echo "This script will:"
echo "1. Create a browser session (if needed)"
echo "2. Run the test scraper with examples"
echo ""

# Check if any profiles exist
if [ -d "browser_profiles" ] && [ "$(ls -A browser_profiles 2>/dev/null)" ]; then
    echo "✅ Found existing browser profiles:"
    ls -1 browser_profiles/
    echo ""
    read -p "Create a new session? (y/N): " create_new

    if [[ $create_new =~ ^[Yy]$ ]]; then
        echo ""
        uv run python save_session.py
    fi
else
    echo "⚠️  No browser profiles found."
    echo "   Creating a new session first..."
    echo ""
    uv run python save_session.py
fi

echo ""
echo "=============================="
echo "🚀 Running test scraper..."
echo "=============================="
echo ""

uv run python test_scraper.py
