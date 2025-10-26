"""Session and browser profile management."""

import os
from pathlib import Path
from playwright.sync_api import sync_playwright, BrowserContext
import time


class SessionManager:
    """Manages browser profiles and sessions for different users."""

    def __init__(self, base_dir: str = "./browser_profiles"):
        """
        Initialize session manager.

        Args:
            base_dir: Base directory for storing browser profiles
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)

    def get_profile_dir(self, user_id: str) -> Path:
        """
        Get the profile directory path for a user.

        Args:
            user_id: User identifier

        Returns:
            Path to the user's browser profile directory
        """
        profile_dir = self.base_dir / user_id
        return profile_dir

    def profile_exists(self, user_id: str) -> bool:
        """
        Check if a profile exists for a user.

        Args:
            user_id: User identifier

        Returns:
            True if profile exists, False otherwise
        """
        return self.get_profile_dir(user_id).exists()

    def create_session(
        self,
        user_id: str,
        url: str,
        headless: bool = False,
        slow_mo: int = 100
    ) -> None:
        """
        Create a new browser session for manual login.

        Args:
            user_id: User identifier
            url: URL to navigate to for login
            headless: Run in headless mode
            slow_mo: Slow down operations by specified ms
        """
        profile_dir = self.get_profile_dir(user_id)

        print(f"📁 Creating browser profile for user: {user_id}")
        print(f"   Profile location: {profile_dir.absolute()}")

        with sync_playwright() as p:
            context = p.chromium.launch_persistent_context(
                user_data_dir=str(profile_dir),
                headless=headless,
                slow_mo=slow_mo,
                args=['--disable-blink-features=AutomationControlled']
            )

            page = context.pages[0] if context.pages else context.new_page()

            page.goto(url, wait_until="domcontentloaded")
            time.sleep(2)

            print("🔓 Log in manually in the browser window...")
            print("   All cookies, storage, and profile data will be saved automatically.")

            input("\nPress Enter after you've logged in to save the session...")

            print(f"✅ Session saved for user: {user_id}")
            context.close()

    def load_session(
        self,
        user_id: str,
        headless: bool = False
    ) -> 'BrowserContext':
        """
        Load an existing browser session.

        Args:
            user_id: User identifier
            headless: Run in headless mode

        Returns:
            Playwright BrowserContext

        Raises:
            ValueError: If profile doesn't exist
        """
        if not self.profile_exists(user_id):
            raise ValueError(
                f"No browser profile found for user '{user_id}'. "
                f"Please run create_session() first."
            )

        profile_dir = self.get_profile_dir(user_id)
        print(f"📁 Loading browser profile for user: {user_id}")

        playwright = sync_playwright().start()
        context = playwright.chromium.launch_persistent_context(
            user_data_dir=str(profile_dir),
            headless=headless,
            args=['--disable-blink-features=AutomationControlled']
        )

        return context

    def delete_session(self, user_id: str) -> None:
        """
        Delete a user's browser profile.

        Args:
            user_id: User identifier
        """
        import shutil

        profile_dir = self.get_profile_dir(user_id)
        if profile_dir.exists():
            shutil.rmtree(profile_dir)
            print(f"🗑️  Deleted profile for user: {user_id}")
        else:
            print(f"⚠️  No profile found for user: {user_id}")

    def list_profiles(self) -> list[str]:
        """
        List all user profiles.

        Returns:
            List of user IDs with profiles
        """
        if not self.base_dir.exists():
            return []

        return [d.name for d in self.base_dir.iterdir() if d.is_dir()]
