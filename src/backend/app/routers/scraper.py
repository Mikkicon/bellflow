from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from concurrent.futures import ThreadPoolExecutor
import asyncio
import json
import uuid
from datetime import datetime
from bson import ObjectId
from app.models.schemas import (
    ScraperRequest,
    ScraperResponse,
    # JobResponse,  # COMMENTED OUT - Async job tracking disabled
    # JobStatusResponse  # COMMENTED OUT - Async job tracking disabled
)
from app.scraper import (
    ThreadsScraper,
    TwitterScraper,
    LinkedInScraper,
    job_manager,
    JobStatus
)
from app.scraper.engines.base_engine import ScrapeJob
from app.database.connector import get_collection
import logging

# Thread pool for running sync Playwright code
executor = ThreadPoolExecutor(max_workers=4)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router instance
router = APIRouter()


def save_scraper_result_to_db(source_link: str, scraper_response: ScraperResponse, status: str = "completed", error: str = None) -> str:
    """
    Save scraper results to the raw_data collection in MongoDB.

    Args:
        source_link: The URL that was scraped
        scraper_response: The scraper response object (or None if error)
        status: Status of the scraping job (processing, completed, failed)
        error: Error message if status is failed

    Returns:
        str: The MongoDB ObjectId as a string
    """
    try:
        collection = get_collection("raw_data")
        if not collection:
            logger.warning("Database not connected, skipping save to DB")
            return None

        # Serialize scraper response to JSON
        if scraper_response:
            raw_data_json = json.dumps(scraper_response.dict(), default=str)
        else:
            raw_data_json = ""

        # Create document
        document = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow(),
            "source_link": source_link,
            "status": status,
            "raw_data": raw_data_json,
            "error": error,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }

        # Insert into database
        result = collection.insert_one(document)
        logger.info(f"Saved scraper result to DB with ObjectId: {result.inserted_id}")
        return str(result.inserted_id)

    except Exception as e:
        logger.error(f"Failed to save to database: {e}")
        return None


@router.post("/scrape")
async def scrape_profile(request: ScraperRequest) -> ScraperResponse:
    """
    Scrape posts from a social media profile.

    Supports:
    - Threads.com (synchronous, returns results immediately)

    NOTE: Twitter/X and LinkedIn async scraping are currently disabled.

    Args:
        request: ScraperRequest containing URL, user_id, and scraping parameters

    Returns:
        ScraperResponse for Threads scraping

    Raises:
        HTTPException: If scraping fails or profile not found
    """
    try:
        logger.info(f"Starting scrape for URL: {request.url}, user_id: {request.user_id}")

        # Determine platform from URL
        url_lower = request.url.lower()

        # Route to appropriate scraper based on platform
        if "threads.com" in url_lower:
            # Threads: Synchronous scraping with Playwright
            logger.info("Using ThreadsScraper (Playwright)")
            scraper = ThreadsScraper(
                url=request.url,
                user_id=request.user_id,
                post_limit=request.post_limit,
                time_limit=request.time_limit,
                scroll_delay=request.scroll_delay,
                headless=request.headless
            )

            # Perform scraping in thread pool (Playwright sync API requires separate thread)
            logger.info(f"Scraping with limits - posts: {request.post_limit}, time: {request.time_limit}s")

            try:
                loop = asyncio.get_event_loop()
                data = await loop.run_in_executor(executor, scraper.scrape)

                # Check for errors
                if "error" in data and data["error"]:
                    logger.error(f"Scraping error: {data['error']}")

                    # Save error to database
                    save_scraper_result_to_db(
                        source_link=request.url,
                        scraper_response=None,
                        status="failed",
                        error=data["error"]
                    )

                    raise HTTPException(
                        status_code=500,
                        detail=f"Scraping failed: {data['error']}"
                    )

                logger.info(f"Scraping completed. Posts: {data['total_items']}, Time: {data['elapsed_time']}s")

                # Create response object
                response = ScraperResponse(**data)

                # Save to database
                save_scraper_result_to_db(
                    source_link=request.url,
                    scraper_response=response,
                    status="completed"
                )

                return response

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Unexpected error during scraping: {e}")

                # Save error to database
                save_scraper_result_to_db(
                    source_link=request.url,
                    scraper_response=None,
                    status="failed",
                    error=str(e)
                )

                raise HTTPException(
                    status_code=500,
                    detail=f"Scraping failed: {str(e)}"
                )

        # COMMENTED OUT - Twitter/LinkedIn async scraping disabled
        # elif "twitter.com" in url_lower or "x.com" in url_lower:
        #     # Twitter: Asynchronous scraping with Bright Data API
        #     logger.info("Using TwitterScraper (Bright Data API)")
        #
        #     from app.scraper.engines.brightdata_engine import BrightDataEngine
        #
        #     # Create engine
        #     engine = BrightDataEngine()
        #
        #     # Use job_manager to create and track the job
        #     job = job_manager.create_job(
        #         engine=engine,
        #         url=request.url,
        #         user_id=request.user_id,
        #         platform="twitter",
        #         post_limit=request.post_limit,
        #         time_limit=request.time_limit
        #     )
        #
        #     # Return job info
        #     logger.info(f"Twitter scraping job created: {job.job_id} (status: {job.status})")
        #     return JobResponse(
        #         job_id=job.job_id,
        #         status=job.status.value,
        #         platform=job.platform,
        #         url=job.url,
        #         user_id=job.user_id,
        #         created_at=job.created_at.isoformat(),
        #         message=job.progress.get("message", "Job created") if job.progress else "Job created"
        #     )
        #
        # elif "linkedin.com" in url_lower:
        #     # LinkedIn: Asynchronous scraping with Bright Data API
        #     logger.info("Using LinkedInScraper (Bright Data API)")
        #
        #     from app.scraper.engines.brightdata_engine import BrightDataEngine
        #
        #     # Create engine
        #     engine = BrightDataEngine()
        #
        #     # Use job_manager to create and track the job
        #     job = job_manager.create_job(
        #         engine=engine,
        #         url=request.url,
        #         user_id=request.user_id,
        #         platform="linkedin",
        #         post_limit=request.post_limit,
        #         time_limit=request.time_limit
        #     )
        #
        #     # Return job info
        #     logger.info(f"LinkedIn scraping job created: {job.job_id} (status: {job.status})")
        #     return JobResponse(
        #         job_id=job.job_id,
        #         status=job.status.value,
        #         platform=job.platform,
        #         url=job.url,
        #         user_id=job.user_id,
        #         created_at=job.created_at.isoformat(),
        #         message=job.progress.get("message", "Job created") if job.progress else "Job created"
        #     )

        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported platform. Currently only Threads.com is supported. URL: {request.url}"
            )

    except HTTPException:
        # Re-raise HTTPException to preserve status code
        raise
    except ValueError as e:
        logger.error(f"ValueError during scraping: {str(e)}")
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error during scraping: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred: {str(e)}"
        )


# COMMENTED OUT - Status check endpoint for async jobs (Twitter/LinkedIn)
# @router.get("/scrape/status/{job_id}", response_model=JobStatusResponse)
# async def get_job_status(job_id: str):
#     """
#     Get the status of a scraping job.
#
#     Args:
#         job_id: Job identifier returned from async scraping request
#
#     Returns:
#         JobStatusResponse with current job status
#
#     Raises:
#         HTTPException: If job not found
#     """
#     try:
#         logger.info(f"Checking status for job: {job_id}")
#
#         # Get job status from job manager
#         job = job_manager.get_job(job_id)
#
#         return JobStatusResponse(
#             job_id=job.job_id,
#             status=job.status.value,
#             platform=job.platform,
#             url=job.url,
#             user_id=job.user_id,
#             created_at=job.created_at.isoformat(),
#             updated_at=job.updated_at.isoformat(),
#             progress=job.progress,
#             error=job.error
#         )
#
#     except ValueError as e:
#         logger.error(f"Job not found: {job_id}")
#         raise HTTPException(
#             status_code=404,
#             detail=str(e)
#         )
#     except Exception as e:
#         logger.error(f"Error checking job status: {str(e)}", exc_info=True)
#         raise HTTPException(
#             status_code=500,
#             detail=f"Error checking job status: {str(e)}"
#         )


@router.get("/scrape/result/{job_id}", response_model=ScraperResponse)
async def get_job_result(job_id: str):
    """
    Get the results of a completed scraping job.

    Args:
        job_id: Job identifier

    Returns:
        ScraperResponse with scraped data

    Raises:
        HTTPException: If job not found or not completed
    """
    try:
        logger.info(f"Getting results for job: {job_id}")

        # Get job results from job manager
        result = job_manager.get_job_results(job_id)

        logger.info(f"Results retrieved for job {job_id}: {result['total_items']} items")

        return ScraperResponse(**result)

    except ValueError as e:
        logger.error(f"Cannot get results: {str(e)}")

        # Check if job exists to provide better error message
        try:
            job = job_manager.get_job(job_id)
            if job.status != JobStatus.COMPLETED:
                raise HTTPException(
                    status_code=400,
                    detail=f"Job is not completed yet. Current status: {job.status.value}"
                )
        except ValueError:
            pass

        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting job results: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error getting job results: {str(e)}"
        )
