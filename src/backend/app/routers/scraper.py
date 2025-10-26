from fastapi import APIRouter, HTTPException
from concurrent.futures import ThreadPoolExecutor
import asyncio
import json
import uuid
from datetime import datetime
from app.models.schemas import (
    ScraperRequest,
    ScraperResponse
)
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
