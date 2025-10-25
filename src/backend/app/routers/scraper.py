from fastapi import APIRouter, HTTPException, BackgroundTasks
from app.models.schemas import ScraperRequest, ScraperResponse
from app.scraper import ThreadsScraper
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router instance
router = APIRouter()


@router.post("/scrape", response_model=ScraperResponse)
async def scrape_profile(request: ScraperRequest):
    """
    Scrape posts from a social media profile (currently supports Threads).

    Args:
        request: ScraperRequest containing URL, user_id, and scraping parameters

    Returns:
        ScraperResponse with scraped posts and metadata

    Raises:
        HTTPException: If scraping fails or profile not found
    """
    try:
        logger.info(f"Starting scrape for URL: {request.url}, user_id: {request.user_id}")

        # Determine platform from URL
        url_lower = request.url.lower()

        if "threads.com" in url_lower:
            # Use ThreadsScraper
            scraper = ThreadsScraper(
                url=request.url,
                user_id=request.user_id,
                post_limit=request.post_limit,
                time_limit=request.time_limit,
                scroll_delay=request.scroll_delay,
                headless=request.headless
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported platform. Currently only Threads.com is supported. URL: {request.url}"
            )

        # Perform scraping
        logger.info(f"Scraping with limits - posts: {request.post_limit}, time: {request.time_limit}s")
        data = scraper.scrape()

        # Check for errors in scrape result
        if "error" in data and data["error"]:
            logger.error(f"Scraping error: {data['error']}")
            raise HTTPException(
                status_code=500,
                detail=f"Scraping failed: {data['error']}"
            )

        logger.info(f"Scraping completed successfully. Posts: {data['total_items']}, Time: {data['elapsed_time']}s")

        return ScraperResponse(**data)

    except HTTPException:
        # Re-raise HTTPException to preserve status code
        raise
    except ValueError as e:
        # Profile doesn't exist error
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
