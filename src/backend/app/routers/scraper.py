from fastapi import APIRouter, HTTPException
from concurrent.futures import ThreadPoolExecutor
import asyncio
import json
from datetime import datetime
from bson import ObjectId
from typing import Set
from app.models.schemas import (
    ScraperRequest,
    ScraperResponse,
    ScraperTaskResponse
)
from app.database.models import RawDataDocument
from app.scraper import ThreadsScraper
from app.database.connector import get_collection
import logging

# Thread pool for running sync Playwright code
executor = ThreadPoolExecutor(max_workers=4)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router instance
router = APIRouter()

# Global set to track background tasks and prevent garbage collection
background_tasks: Set[asyncio.Task] = set()


def create_scraping_task(source_link: str) -> str:
    """
    Create a new scraping task in the database with status 'retriever:processing'.

    Args:
        source_link: The URL to be scraped

    Returns:
        str: The MongoDB ObjectId as a string, or None if DB not connected
    """
    try:
        collection = get_collection("raw_data")
        if collection is None:
            logger.warning("Database not connected, cannot create task")
            return None

        # Create RawDataDocument with initial status
        document = RawDataDocument(
            timestamp=datetime.utcnow(),
            source_link=source_link,
            status="retriever:processing",
            raw_data="",
            error=None
        )

        # Convert to dict for MongoDB insertion
        doc_dict = document.dict(by_alias=True)

        # Insert into database
        result = collection.insert_one(doc_dict)
        task_id = str(result.inserted_id)
        logger.info(f"Created scraping task with ID: {task_id}")
        return task_id

    except Exception as e:
        logger.error(f"Failed to create scraping task: {e}")
        return None


def update_scraping_task(task_id: str, status: str, scraper_response: ScraperResponse = None, error: str = None):
    """
    Update a scraping task with results or error.

    This function has robust error handling and will retry on failure.

    Args:
        task_id: The MongoDB ObjectId as a string
        status: New status (retriever:completed or retriever:failed)
        scraper_response: The scraper response object (if successful)
        error: Error message (if failed)
    """
    max_retries = 3
    retry_count = 0

    while retry_count < max_retries:
        try:
            collection = get_collection("raw_data")
            if collection is None:
                logger.error(f"Database not connected, cannot update task {task_id}")
                return

            # Prepare update data
            update_data = {
                "status": status,
                "updated_at": datetime.utcnow()
            }

            # Add scraper response if provided
            if scraper_response:
                try:
                    update_data["raw_data"] = json.dumps(scraper_response.dict(), default=str)
                except Exception as json_error:
                    logger.error(f"Failed to serialize scraper response for task {task_id}: {json_error}")
                    # If serialization fails, store a simple error message
                    update_data["raw_data"] = json.dumps({"error": "Failed to serialize response"})

            # Add error if provided
            if error:
                # Truncate very long error messages
                update_data["error"] = str(error)[:5000]

            # Update document
            result = collection.update_one(
                {"_id": ObjectId(task_id)},
                {"$set": update_data}
            )

            if result.matched_count == 0:
                logger.warning(f"Task {task_id} not found in database")
            else:
                logger.info(f"✓ Updated task {task_id} with status: {status}")

            return  # Success, exit

        except Exception as e:
            retry_count += 1
            logger.error(f"Failed to update task {task_id} (attempt {retry_count}/{max_retries}): {e}")

            if retry_count >= max_retries:
                logger.critical(f"CRITICAL: Failed to update task {task_id} after {max_retries} attempts. Data may be lost!")
            else:
                import time
                time.sleep(0.5)  # Brief delay before retry


def task_done_callback(task: asyncio.Task):
    """
    Callback executed when a background task completes.

    Removes the task from the tracking set and logs any exceptions.
    """
    background_tasks.discard(task)

    try:
        # Check if task raised an exception
        exception = task.exception()
        if exception:
            logger.error(f"Background task failed with exception: {exception}", exc_info=exception)
    except asyncio.CancelledError:
        logger.warning("Background task was cancelled")
    except Exception as e:
        logger.error(f"Error in task_done_callback: {e}")

    logger.debug(f"Task completed. Active background tasks: {len(background_tasks)}")


async def run_scraping_task_wrapper(task_id: str, request: ScraperRequest):
    """
    Wrapper that manages the background task lifecycle.

    This ensures the task runs to completion independent of the HTTP request.
    """
    try:
        await run_scraping_task(task_id, request)
        logger.info(f"[Task {task_id}] ✓ Completed successfully")
    except Exception as e:
        logger.critical(f"[Task {task_id}] Unhandled exception in task wrapper: {e}", exc_info=True)


async def run_scraping_task(task_id: str, request: ScraperRequest):
    """
    Background task that runs the actual scraping and updates the task status.

    This function has comprehensive error handling to ensure all errors are
    captured and persisted to the database.

    Args:
        task_id: The MongoDB ObjectId of the task
        request: The scraper request parameters
    """
    scraper = None
    data = None

    try:
        logger.info(f"[Task {task_id}] Starting background scraping for URL: {request.url}")

        # Determine platform from URL
        url_lower = request.url.lower()

        if not "threads.com" in url_lower:
            error_msg = f"Unsupported platform. Currently only Threads.com is supported. URL: {request.url}"
            logger.error(f"[Task {task_id}] {error_msg}")
            update_scraping_task(
                task_id=task_id,
                status="retriever:failed",
                error=error_msg
            )
            return

        # Step 1: Initialize scraper
        try:
            logger.info(f"[Task {task_id}] Initializing ThreadsScraper")
            scraper = ThreadsScraper(
                url=request.url,
                user_id=request.user_id,
                post_limit=request.post_limit,
                time_limit=request.time_limit,
                scroll_delay=request.scroll_delay,
                headless=request.headless
            )
            logger.info(f"[Task {task_id}] Scraper initialized successfully")

        except Exception as init_error:
            error_msg = f"Failed to initialize scraper: {str(init_error)}"
            logger.error(f"[Task {task_id}] {error_msg}", exc_info=True)
            update_scraping_task(
                task_id=task_id,
                status="retriever:failed",
                error=error_msg
            )
            return

        # Step 2: Execute scraping
        try:
            logger.info(f"[Task {task_id}] Starting scraping execution")
            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(executor, scraper.scrape)
            logger.info(f"[Task {task_id}] Scraping execution completed")

        except Exception as scrape_error:
            error_msg = f"Scraping execution failed: {str(scrape_error)}"
            logger.error(f"[Task {task_id}] {error_msg}", exc_info=True)
            update_scraping_task(
                task_id=task_id,
                status="retriever:failed",
                error=error_msg
            )
            return

        # Step 3: Check scraper-reported errors
        if not data:
            error_msg = "Scraper returned no data"
            logger.error(f"[Task {task_id}] {error_msg}")
            update_scraping_task(
                task_id=task_id,
                status="retriever:failed",
                error=error_msg
            )
            return

        if "error" in data and data["error"]:
            error_msg = f"Scraper reported error: {data['error']}"
            logger.error(f"[Task {task_id}] {error_msg}")
            update_scraping_task(
                task_id=task_id,
                status="retriever:failed",
                error=data["error"]
            )
            return

        # Step 4: Process and save results
        try:
            logger.info(f"[Task {task_id}] Processing results. Posts: {data.get('total_items', 0)}, Time: {data.get('elapsed_time', 0)}s")

            # Create response object
            response = ScraperResponse(**data)

            # Update task with success
            update_scraping_task(
                task_id=task_id,
                status="retriever:completed",
                scraper_response=response
            )

            logger.info(f"[Task {task_id}] ✓ Scraping completed successfully")

        except Exception as process_error:
            error_msg = f"Failed to process scraping results: {str(process_error)}"
            logger.error(f"[Task {task_id}] {error_msg}", exc_info=True)

            # Try to save partial data if available
            try:
                error_data = {
                    "error": error_msg,
                    "partial_data": str(data)[:1000] if data else "No data"
                }
                update_scraping_task(
                    task_id=task_id,
                    status="retriever:failed",
                    error=error_msg
                )
            except Exception as save_error:
                logger.critical(f"[Task {task_id}] Failed to save error to DB: {save_error}")

    except Exception as unexpected_error:
        # Catch-all for any unexpected errors
        error_msg = f"Unexpected error in scraping task: {str(unexpected_error)}"
        logger.critical(f"[Task {task_id}] {error_msg}", exc_info=True)

        try:
            update_scraping_task(
                task_id=task_id,
                status="retriever:failed",
                error=error_msg
            )
        except Exception as final_error:
            logger.critical(f"[Task {task_id}] CRITICAL: Failed to save final error to DB: {final_error}")


@router.post("/scrape", response_model=ScraperTaskResponse)
async def scrape_profile(request: ScraperRequest) -> ScraperTaskResponse:
    """
    Start a scraping task (fire-and-forget).

    This endpoint immediately returns a task ID that can be used to poll for results.
    Use GET /raw-data/{task_id}/poll to check the scraping status and retrieve results.

    Supports:
    - Threads.com (async background scraping)

    Args:
        request: ScraperRequest containing URL, user_id, and scraping parameters

    Returns:
        ScraperTaskResponse with task_id for polling

    Raises:
        HTTPException: If task creation fails
    """
    task_id = None

    try:
        logger.info(f"Received scrape request - URL: {request.url}, user_id: {request.user_id}")

        # Validate request parameters
        if not request.url or not request.url.strip():
            raise HTTPException(
                status_code=400,
                detail="URL cannot be empty"
            )

        if not request.user_id or not request.user_id.strip():
            raise HTTPException(
                status_code=400,
                detail="user_id cannot be empty"
            )

        # Create initial task in database with status "retriever:processing"
        try:
            task_id = create_scraping_task(source_link=request.url)
        except Exception as create_error:
            logger.error(f"Failed to create task in database: {create_error}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create scraping task: {str(create_error)}"
            )

        if not task_id:
            raise HTTPException(
                status_code=500,
                detail="Failed to create scraping task. Database may not be connected."
            )

        # Start background scraping task (fire-and-forget)
        # Add to background_tasks set to prevent garbage collection
        # The task will run independently of the HTTP request lifecycle
        try:
            task = asyncio.create_task(run_scraping_task_wrapper(task_id, request))
            background_tasks.add(task)

            # Add callback to clean up when task completes
            task.add_done_callback(task_done_callback)

            logger.info(f"✓ Task {task_id} created and added to background_tasks. Active: {len(background_tasks)}")
        except Exception as task_error:
            logger.error(f"Failed to start background task {task_id}: {task_error}", exc_info=True)

            # Update task status to failed
            try:
                update_scraping_task(
                    task_id=task_id,
                    status="retriever:failed",
                    error=f"Failed to start background scraping: {str(task_error)}"
                )
            except Exception as update_error:
                logger.error(f"Failed to update task {task_id} status: {update_error}")

            raise HTTPException(
                status_code=500,
                detail=f"Failed to start background scraping task: {str(task_error)}"
            )

        return ScraperTaskResponse(
            task_id=task_id,
            message="Scraping task started. Use /raw-data/{task_id}/poll to check status.",
            source_link=request.url
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in scrape endpoint: {str(e)}", exc_info=True)

        # Try to update task status if we have a task_id
        if task_id:
            try:
                update_scraping_task(
                    task_id=task_id,
                    status="retriever:failed",
                    error=f"Endpoint error: {str(e)}"
                )
            except Exception as update_error:
                logger.error(f"Failed to update task {task_id} with error: {update_error}")

        raise HTTPException(
            status_code=500,
            detail=f"Failed to start scraping task: {str(e)}"
        )


@router.get("/tasks/status")
async def get_background_tasks_status():
    """
    Get the status of active background scraping tasks.

    Returns:
        Dictionary with count of active background tasks
    """
    return {
        "active_tasks": len(background_tasks),
        "executor_info": {
            "max_workers": executor._max_workers,
            "queue_size": executor._work_queue.qsize() if hasattr(executor, '_work_queue') else "N/A"
        },
        "message": f"{len(background_tasks)} scraping task(s) currently running in background"
    }
