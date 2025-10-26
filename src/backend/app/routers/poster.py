from fastapi import APIRouter, HTTPException
import asyncio
import json
from datetime import datetime
from bson import ObjectId
from typing import Set
from app.models.schemas import (
    PostRequest,
    PostResponse,
    PostTaskResponse
)
from app.database.models import RawDataDocument
from app.scraper.platforms.x_poster import XPoster
from app.database.connector import get_collection
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router instance
router = APIRouter()

# Global set to track background tasks and prevent garbage collection
background_tasks: Set[asyncio.Task] = set()


def create_posting_task(platform: str, content: str) -> str:
    """
    Create a new posting task in the database with status 'poster:processing'.

    Args:
        platform: The platform to post to (e.g., 'x', 'threads')
        content: The content being posted

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
            source_link=f"{platform}:post",  # Indicate this is a posting task
            status="poster:processing",
            raw_data=json.dumps({"content": content}),
            error=None
        )

        # Convert to dict for MongoDB insertion
        doc_dict = document.dict(by_alias=True)

        # Insert into database
        result = collection.insert_one(doc_dict)
        task_id = str(result.inserted_id)
        logger.info(f"Created posting task with ID: {task_id}")
        return task_id

    except Exception as e:
        logger.error(f"Failed to create posting task: {e}")
        return None


def update_posting_task(task_id: str, status: str, post_response: PostResponse = None, error: str = None):
    """
    Update a posting task with results or error.

    This function has robust error handling and will retry on failure.

    Args:
        task_id: The MongoDB ObjectId as a string
        status: New status (poster:completed or poster:failed)
        post_response: The post response object (if successful)
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

            # Add post response if provided
            if post_response:
                try:
                    update_data["raw_data"] = json.dumps(post_response.dict(), default=str)
                    # Store post URL in analysis field if available
                    if post_response.post_url:
                        update_data["analysis"] = {"post_url": post_response.post_url}
                except Exception as json_error:
                    logger.error(f"Failed to serialize post response for task {task_id}: {json_error}")
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


async def run_posting_task_wrapper(task_id: str, request: PostRequest):
    """
    Wrapper that manages the background task lifecycle.

    This ensures the task runs to completion independent of the HTTP request.
    """
    try:
        await run_posting_task(task_id, request)
        logger.info(f"[Task {task_id}] ✓ Completed successfully")
    except Exception as e:
        logger.critical(f"[Task {task_id}] Unhandled exception in task wrapper: {e}", exc_info=True)


async def run_posting_task(task_id: str, request: PostRequest):
    """
    Background task that runs the actual posting and updates the task status.

    This function has comprehensive error handling to ensure all errors are
    captured and persisted to the database.

    Args:
        task_id: The MongoDB ObjectId of the task
        request: The post request parameters
    """
    poster = None
    data = None

    try:
        logger.info(f"[Task {task_id}] Starting background posting for platform: {request.platform}")

        # Select appropriate poster based on platform
        platform_lower = request.platform.lower()

        if platform_lower == "x" or platform_lower == "twitter":
            poster_class = XPoster
            platform_name = "XPoster"
        else:
            error_msg = f"Unsupported platform. Currently supports 'x' (X.com/Twitter). Platform: {request.platform}"
            logger.error(f"[Task {task_id}] {error_msg}")
            update_posting_task(
                task_id=task_id,
                status="poster:failed",
                error=error_msg
            )
            return

        # Step 1: Initialize poster
        try:
            logger.info(f"[Task {task_id}] Initializing {platform_name}")
            poster = poster_class(
                user_id=request.user_id,
                content=request.content,
                url=request.url,
                headless=request.headless
            )
            logger.info(f"[Task {task_id}] Poster initialized successfully")

        except Exception as init_error:
            error_msg = f"Failed to initialize poster: {str(init_error)}"
            logger.error(f"[Task {task_id}] {error_msg}", exc_info=True)
            update_posting_task(
                task_id=task_id,
                status="poster:failed",
                error=error_msg
            )
            return

        # Step 2: Execute posting
        try:
            logger.info(f"[Task {task_id}] Starting posting execution")
            data = await poster.post()
            logger.info(f"[Task {task_id}] Posting execution completed")

        except Exception as post_error:
            error_msg = f"Posting execution failed: {str(post_error)}"
            logger.error(f"[Task {task_id}] {error_msg}", exc_info=True)
            update_posting_task(
                task_id=task_id,
                status="poster:failed",
                error=error_msg
            )
            return

        # Step 3: Check poster-reported errors
        if not data:
            error_msg = "Poster returned no data"
            logger.error(f"[Task {task_id}] {error_msg}")
            update_posting_task(
                task_id=task_id,
                status="poster:failed",
                error=error_msg
            )
            return

        if "error" in data and data["error"]:
            error_msg = f"Poster reported error: {data['error']}"
            logger.error(f"[Task {task_id}] {error_msg}")
            update_posting_task(
                task_id=task_id,
                status="poster:failed",
                error=data["error"]
            )
            return

        # Step 4: Process and save results
        try:
            logger.info(f"[Task {task_id}] Processing results. Success: {data.get('success', False)}, Time: {data.get('elapsed_time', 0)}s")

            # Create response object
            response = PostResponse(**data)

            # Update task with success
            update_posting_task(
                task_id=task_id,
                status="poster:completed",
                post_response=response
            )

            logger.info(f"[Task {task_id}] ✓ Posting completed successfully")

        except Exception as process_error:
            error_msg = f"Failed to process posting results: {str(process_error)}"
            logger.error(f"[Task {task_id}] {error_msg}", exc_info=True)

            # Try to save partial data if available
            try:
                error_data = {
                    "error": error_msg,
                    "partial_data": str(data)[:1000] if data else "No data"
                }
                update_posting_task(
                    task_id=task_id,
                    status="poster:failed",
                    error=error_msg
                )
            except Exception as save_error:
                logger.critical(f"[Task {task_id}] Failed to save error to DB: {save_error}")

    except Exception as unexpected_error:
        # Catch-all for any unexpected errors
        error_msg = f"Unexpected error in posting task: {str(unexpected_error)}"
        logger.critical(f"[Task {task_id}] {error_msg}", exc_info=True)

        try:
            update_posting_task(
                task_id=task_id,
                status="poster:failed",
                error=error_msg
            )
        except Exception as final_error:
            logger.critical(f"[Task {task_id}] CRITICAL: Failed to save final error to DB: {final_error}")


@router.post("/post", response_model=PostTaskResponse)
async def post_content(request: PostRequest) -> PostTaskResponse:
    """
    Start a posting task (fire-and-forget).

    This endpoint immediately returns a task ID.

    Supports:
    - X.com / Twitter.com (async background posting with Playwright)

    Args:
        request: PostRequest containing platform, user_id, content, and posting parameters

    Returns:
        PostTaskResponse with task_id

    Raises:
        HTTPException: If task creation fails
    """
    task_id = None

    try:
        logger.info(f"Received post request - Platform: {request.platform}, user_id: {request.user_id}")

        # Validate request parameters
        if not request.platform or not request.platform.strip():
            raise HTTPException(
                status_code=400,
                detail="Platform cannot be empty"
            )

        if not request.user_id or not request.user_id.strip():
            raise HTTPException(
                status_code=400,
                detail="user_id cannot be empty"
            )

        if not request.content or not request.content.strip():
            raise HTTPException(
                status_code=400,
                detail="Content cannot be empty"
            )

        # Create initial task in database with status "poster:processing"
        try:
            task_id = create_posting_task(platform=request.platform, content=request.content)
        except Exception as create_error:
            logger.error(f"Failed to create task in database: {create_error}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create posting task: {str(create_error)}"
            )

        if not task_id:
            raise HTTPException(
                status_code=500,
                detail="Failed to create posting task. Database may not be connected."
            )

        # Start background posting task (fire-and-forget)
        # Add to background_tasks set to prevent garbage collection
        # The task will run independently of the HTTP request lifecycle
        try:
            task = asyncio.create_task(run_posting_task_wrapper(task_id, request))
            background_tasks.add(task)

            # Add callback to clean up when task completes
            task.add_done_callback(task_done_callback)

            logger.info(f"✓ Task {task_id} created and added to background_tasks. Active: {len(background_tasks)}")
        except Exception as task_error:
            logger.error(f"Failed to start background task {task_id}: {task_error}", exc_info=True)

            # Update task status to failed
            try:
                update_posting_task(
                    task_id=task_id,
                    status="poster:failed",
                    error=f"Failed to start background posting: {str(task_error)}"
                )
            except Exception as update_error:
                logger.error(f"Failed to update task {task_id} status: {update_error}")

            raise HTTPException(
                status_code=500,
                detail=f"Failed to start background posting task: {str(task_error)}"
            )

        return PostTaskResponse(
            task_id=task_id,
            message="Posting task started.",
            platform=request.platform
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in post endpoint: {str(e)}", exc_info=True)

        # Try to update task status if we have a task_id
        if task_id:
            try:
                update_posting_task(
                    task_id=task_id,
                    status="poster:failed",
                    error=f"Endpoint error: {str(e)}"
                )
            except Exception as update_error:
                logger.error(f"Failed to update task {task_id} with error: {update_error}")

        raise HTTPException(
            status_code=500,
            detail=f"Failed to start posting task: {str(e)}"
        )


@router.get("/tasks/status")
async def get_background_tasks_status():
    """
    Get the status of active background posting tasks.

    Returns:
        Dictionary with count of active background tasks
    """
    return {
        "active_tasks": len(background_tasks),
        "message": f"{len(background_tasks)} posting task(s) currently running in background"
    }
