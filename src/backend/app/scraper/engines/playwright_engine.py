"""Playwright-based scraper engine for browser automation."""

from typing import Dict, Optional
from datetime import datetime
import uuid
import time

from app.scraper.engines.base_engine import BaseScraperEngine, ScrapeJob, JobStatus
from app.scraper.session_manager import SessionManager


class PlaywrightEngine(BaseScraperEngine):
    """
    Synchronous scraper engine using Playwright for browser automation.

    This engine immediately returns completed results since Playwright
    scraping is performed synchronously.
    """

    def __init__(self):
        """Initialize the Playwright engine."""
        self.jobs: Dict[str, ScrapeJob] = {}
        self.session_manager = SessionManager()

    def is_async(self) -> bool:
        """Playwright scraping is synchronous."""
        return False

    def initialize_scrape(
        self,
        url: str,
        user_id: str,
        platform: str,
        post_limit: Optional[int] = None,
        time_limit: Optional[int] = None,
        **kwargs
    ) -> ScrapeJob:
        """
        Initialize and execute a Playwright scraping job synchronously.

        Args:
            url: Profile URL to scrape
            user_id: User identifier for browser profile
            platform: Platform name (e.g., 'threads')
            post_limit: Maximum number of posts to scrape
            time_limit: Maximum scraping time in seconds
            **kwargs: Additional parameters (scroll_delay, headless, etc.)

        Returns:
            ScrapeJob with completed status and results
        """
        job_id = str(uuid.uuid4())
        now = datetime.now()

        # Create initial job
        job = ScrapeJob(
            job_id=job_id,
            status=JobStatus.RUNNING,
            platform=platform,
            url=url,
            user_id=user_id,
            created_at=now,
            updated_at=now
        )
        self.jobs[job_id] = job

        try:
            # Execute scraping
            result = self._execute_scrape(
                url=url,
                user_id=user_id,
                platform=platform,
                post_limit=post_limit,
                time_limit=time_limit,
                **kwargs
            )

            # Update job with results
            job.status = JobStatus.COMPLETED
            job.result = result
            job.updated_at = datetime.now()

        except Exception as e:
            # Update job with error
            job.status = JobStatus.FAILED
            job.error = str(e)
            job.updated_at = datetime.now()

        return job

    def _execute_scrape(
        self,
        url: str,
        user_id: str,
        platform: str,
        post_limit: Optional[int] = None,
        time_limit: Optional[int] = None,
        scroll_delay: float = 0.75,
        headless: bool = False,
        selectors: Optional[list] = None,
        extract_fn: Optional[callable] = None,
        **kwargs
    ) -> Dict:
        """
        Execute Playwright scraping logic.

        Args:
            url: Profile URL to scrape
            user_id: User identifier
            platform: Platform name
            post_limit: Maximum posts
            time_limit: Maximum time in seconds
            scroll_delay: Delay between scrolls
            headless: Run in headless mode
            selectors: List of CSS selectors to try
            extract_fn: Function to extract post data from page
            **kwargs: Additional parameters

        Returns:
            Dictionary with scraped data
        """
        start_time = time.time()

        # Load browser session
        context = self.session_manager.load_session(user_id, headless=headless)
        page = context.pages[0] if context.pages else context.new_page()

        try:
            # Navigate to profile
            print(f"🌐 Navigating to: {url}")
            page.goto(url, wait_until="domcontentloaded")
            print("⏳ Waiting for page to load...")
            time.sleep(8)

            # Scroll to trigger lazy loading
            page.evaluate("window.scrollTo(0, 500)")
            time.sleep(2)

            # Find post selector
            print("🔍 Detecting post selector...")
            selector = self._find_selector(page, selectors or [])

            if not selector:
                print("❌ Could not find posts selector!")
                return {
                    'error': 'No posts found',
                    'scraped_at': datetime.now().strftime("%Y%m%d_%H%M%S"),
                    'url': url,
                    'platform': platform,
                    'user_id': user_id
                }

            import json
            initial_count = page.evaluate(f'document.querySelectorAll({json.dumps(selector)}).length')
            print(f"✅ Found {initial_count} posts using selector: {selector}")

            # Scroll to load more posts
            limits_desc = []
            if post_limit:
                limits_desc.append(f"target: {post_limit} posts")
            if time_limit:
                limits_desc.append(f"time limit: {time_limit}s")

            limit_str = ", ".join(limits_desc) if limits_desc else "no limit"
            print(f"\n🚀 Scrolling to load posts ({limit_str})...")

            final_count = self._scroll_and_load(
                page=page,
                selector=selector,
                post_limit=post_limit,
                time_limit=time_limit,
                scroll_delay=scroll_delay,
                start_time=start_time
            )

            # Extract post data
            print(f"\n🔍 Extracting {final_count} posts...")
            items = extract_fn(page, selector) if extract_fn else []

            # Apply post limit
            if post_limit and len(items) > post_limit:
                items = items[:post_limit]

            print(f"✅ Scraped {len(items)} items")

            # Calculate elapsed time
            elapsed_time = time.time() - start_time

            # Build result
            result = {
                'scraped_at': datetime.now().strftime("%Y%m%d_%H%M%S"),
                'url': url,
                'platform': platform,
                'user_id': user_id,
                'total_items': len(items),
                'post_limit': post_limit,
                'time_limit': time_limit,
                'elapsed_time': round(elapsed_time, 2),
                'selector_used': selector,
                'items': items
            }

            return result

        finally:
            context.close()

    def _find_selector(self, page, selectors: list) -> Optional[str]:
        """Find working CSS selector from list."""
        import json

        for selector in selectors:
            try:
                count = page.evaluate(f'document.querySelectorAll({json.dumps(selector)}).length')
                if count > 0:
                    return selector
            except Exception:
                continue
        return None

    def _scroll_and_load(
        self,
        page,
        selector: str,
        post_limit: Optional[int],
        time_limit: Optional[int],
        scroll_delay: float,
        start_time: float,
        max_scrolls: int = 500
    ) -> int:
        """Scroll page to load more posts."""
        import json

        last_count = 0
        scrolls = 0

        for i in range(max_scrolls):
            # Scroll to bottom
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(scroll_delay)

            # Count current posts
            current_count = page.evaluate(f'document.querySelectorAll({json.dumps(selector)}).length')
            scrolls += 1

            # Show progress
            if scrolls % 5 == 0:
                print(f"  Scroll {scrolls}: {current_count} posts loaded...")

            # Check limits
            should_stop = False
            if post_limit and current_count >= post_limit:
                print(f"🎯 Post limit reached: {current_count} posts (limit: {post_limit})")
                should_stop = True
            elif time_limit:
                elapsed = time.time() - start_time
                if elapsed >= time_limit:
                    print(f"⏱️  Time limit reached: {elapsed:.1f}s (limit: {time_limit}s)")
                    should_stop = True

            if should_stop:
                break

            # Check if no new content
            if current_count == last_count:
                print(f"🛑 No more content after {scrolls} scrolls. Final count: {current_count} posts")
                break

            last_count = current_count

        return current_count

    def get_status(self, job_id: str) -> ScrapeJob:
        """Get job status."""
        if job_id not in self.jobs:
            raise ValueError(f"Job {job_id} not found")
        return self.jobs[job_id]

    def get_results(self, job_id: str) -> Dict:
        """Get job results."""
        job = self.get_status(job_id)

        if job.status != JobStatus.COMPLETED:
            raise ValueError(f"Job {job_id} is not completed (status: {job.status})")

        if not job.result:
            raise ValueError(f"Job {job_id} has no results")

        return job.result

    def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a job (not supported for synchronous engine).

        Since Playwright scraping is synchronous and fast, cancellation
        is not supported.
        """
        return False
