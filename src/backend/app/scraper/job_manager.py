"""Job manager for tracking scraping jobs across different engines."""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
import threading

from app.scraper.engines.base_engine import BaseScraperEngine, ScrapeJob, JobStatus


class JobManager:
    """
    Centralized manager for scraping jobs.

    Tracks jobs across different engines and provides a unified interface
    for job management. Uses in-memory storage (can be upgraded to Redis/DB).
    """

    # Singleton instance
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """Ensure singleton instance."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize the job manager."""
        if self._initialized:
            return

        self.jobs: Dict[str, ScrapeJob] = {}
        self.engines: Dict[str, BaseScraperEngine] = {}  # job_id -> engine
        self.user_jobs: Dict[str, List[str]] = {}  # user_id -> [job_ids]
        self._initialized = True

    def create_job(
        self,
        engine: BaseScraperEngine,
        url: str,
        user_id: str,
        platform: str,
        post_limit: Optional[int] = None,
        time_limit: Optional[int] = None,
        **kwargs
    ) -> ScrapeJob:
        """
        Create a new scraping job.

        Args:
            engine: Scraper engine to use
            url: Profile URL to scrape
            user_id: User identifier
            platform: Platform name
            post_limit: Maximum posts
            time_limit: Maximum time
            **kwargs: Additional parameters

        Returns:
            ScrapeJob instance
        """
        # Initialize scrape with engine
        job = engine.initialize_scrape(
            url=url,
            user_id=user_id,
            platform=platform,
            post_limit=post_limit,
            time_limit=time_limit,
            **kwargs
        )

        # Store job and engine mapping
        self.jobs[job.job_id] = job
        self.engines[job.job_id] = engine

        # Track user's jobs
        if user_id not in self.user_jobs:
            self.user_jobs[user_id] = []
        self.user_jobs[user_id].append(job.job_id)

        return job

    def get_job(self, job_id: str) -> ScrapeJob:
        """
        Get a job by ID.

        For async jobs, this will poll the engine for updated status.

        Args:
            job_id: Job identifier

        Returns:
            ScrapeJob instance

        Raises:
            ValueError: If job not found
        """
        if job_id not in self.jobs:
            raise ValueError(f"Job {job_id} not found")

        engine = self.engines.get(job_id)
        if not engine:
            raise ValueError(f"No engine found for job {job_id}")

        # For async engines, poll for updated status
        if engine.is_async():
            job = engine.get_status(job_id)
            self.jobs[job_id] = job  # Update cached job
        else:
            job = self.jobs[job_id]

        return job

    def get_job_results(self, job_id: str) -> Dict:
        """
        Get results of a completed job.

        Args:
            job_id: Job identifier

        Returns:
            Dictionary with scraped data

        Raises:
            ValueError: If job not found or not completed
        """
        engine = self.engines.get(job_id)
        if not engine:
            raise ValueError(f"No engine found for job {job_id}")

        return engine.get_results(job_id)

    def list_user_jobs(
        self,
        user_id: str,
        status: Optional[JobStatus] = None,
        limit: int = 100
    ) -> List[ScrapeJob]:
        """
        List jobs for a specific user.

        Args:
            user_id: User identifier
            status: Filter by status (optional)
            limit: Maximum number of jobs to return

        Returns:
            List of ScrapeJob instances
        """
        job_ids = self.user_jobs.get(user_id, [])

        jobs = []
        for job_id in reversed(job_ids[-limit:]):  # Most recent first
            try:
                job = self.get_job(job_id)
                if status is None or job.status == status:
                    jobs.append(job)
            except ValueError:
                continue

        return jobs

    def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a running job.

        Args:
            job_id: Job identifier

        Returns:
            True if cancelled successfully
        """
        engine = self.engines.get(job_id)
        if not engine:
            return False

        return engine.cancel_job(job_id)

    def cleanup_old_jobs(self, max_age_hours: int = 24):
        """
        Clean up old completed/failed jobs.

        Args:
            max_age_hours: Maximum age of jobs to keep (in hours)
        """
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        jobs_to_remove = []

        for job_id, job in self.jobs.items():
            # Only remove completed or failed jobs
            if job.status in [JobStatus.COMPLETED, JobStatus.FAILED]:
                if job.updated_at < cutoff_time:
                    jobs_to_remove.append(job_id)

        # Remove old jobs
        for job_id in jobs_to_remove:
            self._remove_job(job_id)

        if jobs_to_remove:
            print(f"🧹 Cleaned up {len(jobs_to_remove)} old jobs")

    def _remove_job(self, job_id: str):
        """Remove a job from all tracking structures."""
        # Remove from jobs dict
        job = self.jobs.pop(job_id, None)

        # Remove from engines dict
        self.engines.pop(job_id, None)

        # Remove from user_jobs
        if job:
            user_job_list = self.user_jobs.get(job.user_id, [])
            if job_id in user_job_list:
                user_job_list.remove(job_id)

    def get_stats(self) -> Dict:
        """
        Get statistics about jobs.

        Returns:
            Dictionary with job statistics
        """
        total_jobs = len(self.jobs)
        status_counts = {
            "pending": 0,
            "running": 0,
            "completed": 0,
            "failed": 0
        }

        for job in self.jobs.values():
            status_counts[job.status.value] += 1

        return {
            "total_jobs": total_jobs,
            "status_counts": status_counts,
            "total_users": len(self.user_jobs)
        }


# Global job manager instance
job_manager = JobManager()
