"""LinkedIn scraper implementation using Bright Data API."""

from datetime import datetime
from typing import Optional
import re, json
from typing import List, Dict

from app.scraper.engine_scraper import EngineScraper
from app.scraper.engines.brightdata_engine import BrightDataEngine
from app.scraper.engines.base_engine import ScrapeJob


class LinkedInScraper(EngineScraper):
    """
    Scraper for LinkedIn using Bright Data API.

    This scraper uses the Bright Data API to scrape LinkedIn posts asynchronously.
    """

    def __init__(
        self,
        url: str,
        user_id: str,
        post_limit: Optional[int] = None,
        time_limit: Optional[int] = None,
        api_key: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize LinkedIn scraper.

        Args:
            url: LinkedIn profile URL (e.g., https://www.linkedin.com/in/username)
            user_id: User identifier
            post_limit: Maximum posts to scrape
            time_limit: Not used for API-based scraping
            api_key: Bright Data API key (optional, defaults to env var)
            **kwargs: Additional parameters
        """
        # Initialize Bright Data engine
        engine = BrightDataEngine(api_key=api_key)

        # Call parent constructor
        super().__init__(
            engine=engine,
            url=url,
            user_id=user_id,
            platform="linkedin",
            post_limit=post_limit,
            time_limit=time_limit,
            **kwargs
        )

    def scrape(self) -> ScrapeJob:
        """
        Start scraping LinkedIn posts.

        This is an asynchronous operation. The method returns immediately
        with a job that can be polled for status and results.

        Returns:
            ScrapeJob with job_id and initial status
        """
        return super().scrape()




class LinkedInTxtScraper(EngineScraper):

    def __init__(
        self,
        url: str,
        user_id: str,
        post_limit: Optional[int] = None,
        time_limit: Optional[int] = None,
        api_key: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize LinkedIn scraper.

        Args:
            url: LinkedIn profile URL (e.g., https://www.linkedin.com/in/username)
            user_id: User identifier
            post_limit: Maximum posts to scrape
            time_limit: Not used for API-based scraping
            api_key: Bright Data API key (optional, defaults to env var)
            **kwargs: Additional parameters
        """
        # Initialize Bright Data engine
        engine = BrightDataEngine(api_key=api_key)

        # Call parent constructor
        super().__init__(
            engine=engine,
            url=url,
            user_id=user_id,
            platform="linkedin",
            post_limit=post_limit,
            time_limit=time_limit,
            **kwargs
        )

    async def scrape(self) -> List[Dict]:
        """
        Heuristic parser that turns a pasted LinkedIn feed (like the sample you provided)
        into a list of objects with shape:
        {
            text: string,
            link: string,
            username: string,
            likes: number,
            retweets: number,
            replies: number,
            views: number,
            raw_data: string
        }

        Notes:
        - This uses robust regex/heuristics because pasted LinkedIn HTML/text is noisy and inconsistent.
        - It extracts posts by splitting on 'Feed post number <n>' markers, finds username from a line
        containing 'followers' (fallback to first non-empty line), grabs links, and attempts to read
        likes and reposts (treated as retweets).
        - replies and views are set to 0 when not present in the input.
        """
        text = ""
        with open("ionstream-linkedin-posts-raw.txt", "r") as f:
            text = f.read()

        items = []
        # Split by 'Feed post number' markers
        chunks = re.split(r'Feed post number \d+', text)
        for chunk in chunks[1:]:
            raw = chunk.strip()
            if not raw:
                continue

            # username: try to find a line with 'followers' and take text before it
            m = re.search(r'(?m)^(.*?)\s*\d{1,3}(?:,\d{3})*\s*followers', raw)
            if m:
                username = m.group(1).strip()
            else:
                lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]
                username = lines[0] if lines else ""

            # timestamp line detection — find a timestamp like '2w •  2 weeks ago' or '1mo •'
            ts_match = re.search(r'(?m)^\s*(\d+\s*(?:w|d|mo|y))\s*•.*$', raw)
            if ts_match:
                start_pos = ts_match.end()
                content_candidate = raw[start_pos:]
            else:
                # fallback: assume content starts after first blank-line block
                parts = raw.split("\n\n", 1)
                content_candidate = parts[1] if len(parts) > 1 else raw

            # trim at common trailing markers
            end_markers = [r'\nActivate to view', r'\nlike', r'\nLike\n', r'\nPhoto of',
                        r'\nFeed post number', r'\nView ad library', r'\nhashtag#']
            end_idx = len(content_candidate)
            for marker in end_markers:
                m = re.search(marker, content_candidate, re.IGNORECASE)
                if m:
                    end_idx = min(end_idx, m.start())

            content = content_candidate[:end_idx].strip()

            # extract first link, if any
            links = re.findall(r'https?://\S+', content)
            link = links[0] if links else ""

            # extract reposts (reposts -> retweets)
            rep = re.search(r'(\d{1,6})\s*repost', raw, re.IGNORECASE)
            reposts = int(rep.group(1)) if rep else 0

            # extract likes: multiple heuristics
            likes = None
            # heuristic 1: a standalone number line often corresponds to likes
            like_match = re.search(r'(?m)^[^\S\r\n]*([\d,]{1,7})\s*$\s*(?:\d+\s*repost|repost|reposts)?', raw)
            if like_match:
                try:
                    likes = int(like_match.group(1).replace(",", ""))
                except:
                    likes = None
            # heuristic 2: number right after 'like' words
            if likes is None:
                m_alt = re.search(r'(?s)(?:like.*?)\n\s*([\d,]{1,7})', raw, re.IGNORECASE)
                if m_alt:
                    likes = int(m_alt.group(1).replace(",", ""))
            # heuristic 3: fallback to largest standalone number (excluding reposts)
            if likes is None:
                nums = [int(x.replace(",", "")) for x in re.findall(r'(\d{1,7})', raw)]
                candidates = [n for n in nums if n != reposts]
                likes = max(candidates) if candidates else 0


            # Check if this is a repost by looking for "reposted this" text
            reposted = bool(re.search(r'reposted this', raw, re.IGNORECASE))
            # default replies/views = 0 (not present in many text dumps)
            replies = 0
            views = 0

            items.append({
                "text": re.sub(r'\s+\n', '\n', content).strip(),
                "link": link,
                "username": username,
                "likes": likes,
                "retweets": reposts,
                "replies": replies,
                "views": views,
                "reposted": reposted,
                "raw_data": raw
            })
        
        elapsed_time = 0
        selector = None
        
        # Build result
        result = {
            'scraped_at': datetime.now().strftime("%Y%m%d_%H%M%S"),
            'url': self.url,
            'platform': self.get_platform_name(),
            'user_id': self.user_id,
            'total_items': len(items),
            'post_limit': self.post_limit,
            'time_limit': self.time_limit,
            'elapsed_time': round(elapsed_time, 2),
            'selector_used': selector,
            'items': items
        }

        return result

    # Example usage:
    # parsed = parse_linkedin_feed(your_pasted_text_string)
    # print(json.dumps(parsed, indent=2, ensure_ascii=False))

# ionstream_txt = ""
# with open("ionstream-linkedin-posts-raw.txt", "r") as f:
#     ionstream_txt = f.read()

# parser = LinkedInTxtScraper()
# parsed = asyncio.run(parser.scrape(ionstream_txt))
# with open("parsed_linkedin_posts.json", "w", encoding="utf-8") as f:
#     json.dump(parsed, f, indent=2, ensure_ascii=False)