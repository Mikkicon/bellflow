"""Bright Data API-based scraper engine."""

from typing import Dict, Optional
from datetime import datetime, timedelta
import uuid
import os
import requests

from app.scraper.engines.base_engine import BaseScraperEngine, ScrapeJob, JobStatus


class BrightDataEngine(BaseScraperEngine):
    """
    Asynchronous scraper engine using Bright Data API.

    This engine submits scraping jobs to Bright Data and polls for results.
    Jobs are asynchronous and require status checking.
    """

    # Bright Data dataset IDs for different platforms
    DATASET_IDS = {
        "twitter": "gd_lwxkxvnf1cynvib9co",  # From brightdata-api.py example
        "linkedin": "gd_l7q7dkf244hwzk73o",  # LinkedIn posts dataset
        # Add more platforms as needed
    }

    API_URL = "https://api.brightdata.com/datasets/v3"

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Bright Data engine.

        Args:
            api_key: Bright Data API key (defaults to BRIGHTDATA_API_KEY env var)
        """
        self.api_key = api_key or os.environ.get("BRIGHTDATA_API_KEY")
        if not self.api_key:
            raise EnvironmentError(
                "BRIGHTDATA_API_KEY environment variable is not set. "
                "Please set it to use Bright Data scraping."
            )

        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        self.jobs: Dict[str, ScrapeJob] = {}
        self.snapshot_map: Dict[str, str] = {}  # job_id -> snapshot_id

    def is_async(self) -> bool:
        """Bright Data scraping is asynchronous."""
        return True

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
        Initialize a Bright Data scraping job.

        Args:
            url: Profile URL to scrape
            user_id: User identifier
            platform: Platform name (e.g., 'twitter', 'linkedin')
            post_limit: Maximum number of posts (converted to date range)
            time_limit: Not used for Bright Data (API handles timing)
            **kwargs: Additional parameters

        Returns:
            ScrapeJob with pending status
        """
        job_id = str(uuid.uuid4())
        now = datetime.now()

        # Create job
        job = ScrapeJob(
            job_id=job_id,
            status=JobStatus.PENDING,
            platform=platform,
            url=url,
            user_id=user_id,
            created_at=now,
            updated_at=now
        )
        self.jobs[job_id] = job

        try:
            # Get dataset ID for platform
            dataset_id = self.DATASET_IDS.get(platform.lower())
            if not dataset_id:
                raise ValueError(
                    f"Platform '{platform}' not supported by Bright Data engine. "
                    f"Supported platforms: {list(self.DATASET_IDS.keys())}"
                )

            # Convert post_limit to date range
            # More posts = longer date range
            start_date, end_date = self._convert_limit_to_dates(post_limit)

            # Prepare API request
            params = {
                "dataset_id": dataset_id,
                "include_errors": "true",
                "type": "discover_new",
                "discover_by": "profile_url",
            }

            data = [
                {
                    "url": url,
                    "start_date": start_date,
                    "end_date": end_date,
                }
            ]

            # Submit scraping job to Bright Data
            print(f"📡 Submitting scrape job to Bright Data for {platform}...")
            print(f"   URL: {url}")
            print(f"   Date range: {start_date} to {end_date}")

            response = requests.post(
                f"{self.API_URL}/trigger",
                headers=self.headers,
                params=params,
                json=data,
                timeout=30
            )

            if response.status_code != 200:
                raise Exception(f"Bright Data API error: {response.status_code} - {response.text}")

            response_data = response.json()
            snapshot_id = response_data.get("snapshot_id")

            if not snapshot_id:
                raise Exception(f"No snapshot_id in Bright Data response: {response_data}")

            # Store snapshot ID mapping
            self.snapshot_map[job_id] = snapshot_id

            # Update job status
            job.status = JobStatus.RUNNING
            job.updated_at = datetime.now()
            job.progress = {
                "snapshot_id": snapshot_id,
                "message": "Scraping job submitted to Bright Data"
            }

            print(f"✅ Job submitted successfully. Snapshot ID: {snapshot_id}")

        except Exception as e:
            job.status = JobStatus.FAILED
            job.error = str(e)
            job.updated_at = datetime.now()
            print(f"❌ Failed to submit job: {e}")

        return job

    def _convert_limit_to_dates(self, post_limit: Optional[int]) -> tuple[str, str]:
        """
        Convert post_limit to date range.

        Logic:
        - No limit or large limit (500+): Last 365 days
        - Medium limit (100-499): Last 90 days
        - Small limit (50-99): Last 30 days
        - Very small limit (<50): Last 7 days

        Args:
            post_limit: Desired number of posts

        Returns:
            Tuple of (start_date, end_date) in ISO format
        """
        end_date = datetime.now()

        if not post_limit or post_limit >= 500:
            start_date = end_date - timedelta(days=365)
        elif post_limit >= 100:
            start_date = end_date - timedelta(days=90)
        elif post_limit >= 50:
            start_date = end_date - timedelta(days=30)
        else:
            start_date = end_date - timedelta(days=7)

        return (
            start_date.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            end_date.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        )

    def get_status(self, job_id: str) -> ScrapeJob:
        """
        Get the current status of a scraping job.

        This method polls the Bright Data API to check the snapshot status.

        Args:
            job_id: Job identifier

        Returns:
            ScrapeJob with updated status
        """
        if job_id not in self.jobs:
            raise ValueError(f"Job {job_id} not found")

        job = self.jobs[job_id]

        # If job is already completed or failed, return cached status
        if job.status in [JobStatus.COMPLETED, JobStatus.FAILED]:
            return job

        # Get snapshot ID
        snapshot_id = self.snapshot_map.get(job_id)
        if not snapshot_id:
            job.status = JobStatus.FAILED
            job.error = "No snapshot_id found for job"
            job.updated_at = datetime.now()
            return job

        try:
            # Poll Bright Data API for snapshot status
            response = requests.get(
                f"{self.API_URL}/snapshot/{snapshot_id}",
                headers=self.headers,
                params={"format": "json"},
                timeout=30
            )

            # Handle different status codes
            if response.status_code == 202:
                # 202 = Accepted, still processing
                try:
                    data = response.json()
                    job.progress = {
                        "message": data.get("message", "Snapshot is being processed...")
                    }
                except:
                    job.progress = {"message": "Scraping in progress..."}
                job.updated_at = datetime.now()
                return job

            if response.status_code == 404:
                # 404 = Not found yet
                job.progress = {"message": "Snapshot not ready yet"}
                job.updated_at = datetime.now()
                return job

            if response.status_code != 200:
                # Other errors
                raise Exception(f"API error: {response.status_code} - {response.text}")

            data = response.json()

            # Check response type
            # If dict with 'status': 'running', still in progress
            if isinstance(data, dict) and data.get("status") == "running":
                job.progress = {
                    "message": data.get("message", "Scraping in progress...")
                }
                job.updated_at = datetime.now()
                return job

            # If list, scraping is complete (or has errors)
            if isinstance(data, list):
                # Check for errors
                if data and "error" in data[0]:
                    job.status = JobStatus.FAILED
                    job.error = f"Bright Data error: {data[0].get('error', 'Unknown error')}"
                    job.updated_at = datetime.now()
                    return job

                # Check for warnings
                if data and "warning" in data[0]:
                    # Warnings are still considered success, but with fewer results
                    print(f"⚠️  Warning from Bright Data: {data[0].get('warning')}")

                # Success - store results
                job.status = JobStatus.COMPLETED
                job.result = self._transform_brightdata_response(data, job)
                job.updated_at = datetime.now()
                print(f"✅ Job {job_id} completed. Found {len(data)} posts")

        except Exception as e:
            job.status = JobStatus.FAILED
            job.error = f"Error checking status: {str(e)}"
            job.updated_at = datetime.now()

        return job

    def _transform_brightdata_response(self, data: list, job: ScrapeJob) -> Dict:
        """
        Transform Bright Data API response to match our schema.

        Args:
            data: List of posts from Bright Data
            job: ScrapeJob instance

        Returns:
            Dictionary matching ScraperResponse schema
        """
        # Transform posts to match our schema
        items = []
        for post in data:
            # Handle different platform schemas
            if job.platform == "twitter":
                items.append({
                    "text": post.get("description") or "",
                    "link": post.get("url"),
                    "likes": post.get("likes"),
                    "comments": post.get("replies"),
                    "reposts": post.get("reposts"),
                    "date_posted": post.get("date_posted"),
                    "views": post.get("views"),
                })
            elif job.platform == "linkedin":
                items.append({
                    "text": post.get("text") or post.get("description") or "",
                    "link": post.get("url") or post.get("post_url"),
                    "likes": post.get("num_likes") or post.get("likes"),
                    "comments": post.get("num_comments") or post.get("comments"),
                    "reposts": post.get("num_shares") or post.get("reposts"),
                    "date_posted": post.get("date") or post.get("date_posted"),
                })
            else:
                # Generic transformation
                items.append({
                    "text": post.get("text") or post.get("description") or "",
                    "link": post.get("url") or post.get("link"),
                    "likes": post.get("likes"),
                    "comments": post.get("comments"),
                    "reposts": post.get("reposts") or post.get("shares"),
                })

        # Build response matching ScraperResponse schema
        return {
            "scraped_at": datetime.now().strftime("%Y%m%d_%H%M%S"),
            "url": job.url,
            "platform": job.platform,
            "user_id": job.user_id,
            "total_items": len(items),
            "post_limit": None,  # Bright Data doesn't use post_limit directly
            "time_limit": None,
            "elapsed_time": (datetime.now() - job.created_at).total_seconds(),
            "selector_used": "BrightData API",
            "items": items
        }

    def get_results(self, job_id: str) -> Dict:
        """
        Get results of a completed job.

        Args:
            job_id: Job identifier

        Returns:
            Dictionary with scraped data
        """
        job = self.get_status(job_id)

        if job.status != JobStatus.COMPLETED:
            raise ValueError(
                f"Job {job_id} is not completed. Current status: {job.status}. "
                f"Progress: {job.progress}"
            )

        if not job.result:
            raise ValueError(f"Job {job_id} has no results")

        return job.result

    def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a running job.

        Note: Bright Data doesn't support cancellation via API,
        so we just mark the job as cancelled locally.

        Args:
            job_id: Job identifier

        Returns:
            True if job was cancelled
        """
        if job_id not in self.jobs:
            return False

        job = self.jobs[job_id]

        if job.status in [JobStatus.COMPLETED, JobStatus.FAILED]:
            return False

        job.status = JobStatus.FAILED
        job.error = "Job cancelled by user"
        job.updated_at = datetime.now()

        return True
