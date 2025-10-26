"""X.com (Twitter) poster implementation."""

from typing import Dict
from datetime import datetime
import time
import asyncio

from app.scraper.base_poster import BasePlatformPoster
from app.scraper.session_manager import SessionManager


class XPoster(BasePlatformPoster):
    """Poster for X.com (formerly Twitter)."""

    def get_platform_name(self) -> str:
        """Return the platform name."""
        return "x"

    def get_composer_selectors(self) -> Dict[str, str]:
        """
        Return selectors for X.com posting UI elements.

        Returns:
            Dictionary with selectors for compose_button, text_area, submit_button
        """
        return {
            # X.com has a compose button in the sidebar and a text area on the home page
            "compose_button": 'a[aria-label="Post"], a[data-testid="SideNav_NewTweet_Button"]',
            "text_area": 'div[data-testid="tweetTextarea_0"], div[role="textbox"][contenteditable="true"]',
            "submit_button": 'button[data-testid="tweetButton"], button[data-testid="tweetButtonInline"]',
        }

    async def post(self) -> Dict:
        """
        Post content to X.com.

        Returns:
            Dictionary containing:
                - posted_at: Timestamp
                - platform: Platform name
                - user_id: User identifier
                - success: Boolean indicating success/failure
                - content: Content that was posted
                - post_url: URL of created post (if detectable)
                - error: Error message (if failed)
                - elapsed_time: Time taken to post
        """
        self.start_time = time.time()

        # Initialize session manager
        session_mgr = SessionManager()

        # Debug: Check profile path
        profile_path = session_mgr.get_profile_dir(self.user_id)
        profile_exists = session_mgr.profile_exists(self.user_id)
        print(f"🔍 [POSTER] Profile path: {profile_path}")
        print(f"🔍 [POSTER] Profile exists: {profile_exists}")
        print(f"🔍 [POSTER] user_id: {self.user_id}")

        # Load browser session
        playwright, context, session_id = await session_mgr.load_session(
            self.user_id, headless=self.headless
        )
        page = context.pages[0] if context.pages else await context.new_page()

        try:
            # Navigate to X.com home or specified URL
            target_url = self.url or "https://x.com/home"
            print(f"🌐 Navigating to: {target_url}")
            await page.goto(target_url, wait_until="domcontentloaded")
            print("⏳ Waiting for page to load...")
            await asyncio.sleep(5)  # Match scraper: 5 seconds for cookies/auth to load

            # Scroll to trigger page initialization (match scraper behavior)
            await page.evaluate("window.scrollTo(0, 500)")
            await asyncio.sleep(2)  # Additional wait after scroll

            # Get selectors
            selectors = self.get_composer_selectors()

            # Try to find the text area first (it's usually visible on the home page)
            print("🔍 Looking for compose area...")
            text_area_found = await self.find_element(
                page, selectors["text_area"], timeout=5000
            )

            if not text_area_found:
                # If text area not found, try clicking the compose button
                print("🔍 Text area not found, trying compose button...")
                compose_button_found = await self.find_element(
                    page, selectors["compose_button"], timeout=5000
                )

                if not compose_button_found:
                    elapsed_time = time.time() - self.start_time
                    return {
                        "posted_at": datetime.now().strftime("%Y%m%d_%H%M%S"),
                        "platform": self.get_platform_name(),
                        "user_id": self.user_id,
                        "success": False,
                        "content": self.content,
                        "post_url": None,
                        "error": "Could not find compose button or text area. You may need to log in first.",
                        "elapsed_time": round(elapsed_time, 2),
                    }

                # Click compose button
                print("✅ Found compose button, clicking...")
                clicked = await self.click_and_wait(
                    page, selectors["compose_button"], wait_time=2.0
                )

                if not clicked:
                    elapsed_time = time.time() - self.start_time
                    return {
                        "posted_at": datetime.now().strftime("%Y%m%d_%H%M%S"),
                        "platform": self.get_platform_name(),
                        "user_id": self.user_id,
                        "success": False,
                        "content": self.content,
                        "post_url": None,
                        "error": "Failed to click compose button",
                        "elapsed_time": round(elapsed_time, 2),
                    }

            # Now type the content
            print(f"📝 Typing content: {self.content[:50]}...")
            typed = await self.type_text(page, selectors["text_area"], self.content)

            if not typed:
                elapsed_time = time.time() - self.start_time
                return {
                    "posted_at": datetime.now().strftime("%Y%m%d_%H%M%S"),
                    "platform": self.get_platform_name(),
                    "user_id": self.user_id,
                    "success": False,
                    "content": self.content,
                    "post_url": None,
                    "error": "Failed to type content into text area",
                    "elapsed_time": round(elapsed_time, 2),
                }

            print("✅ Content typed successfully")

            # Wait a moment for the submit button to become active
            await asyncio.sleep(1)

            # Find and click the submit button
            print("🔍 Looking for submit button...")
            submit_found = await self.find_element(
                page, selectors["submit_button"], timeout=5000
            )

            if not submit_found:
                elapsed_time = time.time() - self.start_time
                return {
                    "posted_at": datetime.now().strftime("%Y%m%d_%H%M%S"),
                    "platform": self.get_platform_name(),
                    "user_id": self.user_id,
                    "success": False,
                    "content": self.content,
                    "post_url": None,
                    "error": "Submit button not found",
                    "elapsed_time": round(elapsed_time, 2),
                }

            print("✅ Found submit button, clicking...")
            submitted = await self.click_and_wait(
                page, selectors["submit_button"], wait_time=3.0
            )

            if not submitted:
                elapsed_time = time.time() - self.start_time
                return {
                    "posted_at": datetime.now().strftime("%Y%m%d_%H%M%S"),
                    "platform": self.get_platform_name(),
                    "user_id": self.user_id,
                    "success": False,
                    "content": self.content,
                    "post_url": None,
                    "error": "Failed to click submit button",
                    "elapsed_time": round(elapsed_time, 2),
                }

            # Wait for post to be submitted
            print("⏳ Waiting for post to be submitted...")
            await asyncio.sleep(3)

            # Try to detect the post URL (this is best-effort)
            post_url = None
            try:
                # After posting, X.com sometimes navigates to the post or shows it in the timeline
                current_url = page.url
                if "/status/" in current_url:
                    post_url = current_url
                    print(f"✅ Post URL detected: {post_url}")
                else:
                    print("ℹ️  Could not detect post URL (this is normal)")
            except Exception as e:
                print(f"ℹ️  Could not detect post URL: {e}")

            # Calculate elapsed time
            elapsed_time = time.time() - self.start_time

            print(f"✅ Post submitted successfully in {elapsed_time:.2f}s")

            # Keep browser open for 15 seconds so user can verify the post
            print("⏳ Keeping browser open for 15 seconds to verify post...")
            await asyncio.sleep(15)

            # Build result
            result = {
                "posted_at": datetime.now().strftime("%Y%m%d_%H%M%S"),
                "platform": self.get_platform_name(),
                "user_id": self.user_id,
                "success": True,
                "content": self.content,
                "post_url": post_url,
                "error": None,
                "elapsed_time": round(elapsed_time, 2),
            }

            return result

        except Exception as e:
            elapsed_time = time.time() - self.start_time
            print(f"❌ Error during posting: {e}")
            return {
                "posted_at": datetime.now().strftime("%Y%m%d_%H%M%S"),
                "platform": self.get_platform_name(),
                "user_id": self.user_id,
                "success": False,
                "content": self.content,
                "post_url": None,
                "error": f"Exception during posting: {str(e)}",
                "elapsed_time": round(elapsed_time, 2),
            }

        finally:
            # Close context and playwright instance to ensure session data is persisted
            await context.close()
            await playwright.stop()
            session_mgr.unregister_session(session_id)
