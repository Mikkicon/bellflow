"""Session and browser profile management."""

import os
from pathlib import Path
from playwright.async_api import async_playwright, BrowserContext
import time
import threading
import asyncio


class SessionManager:
    """Manages browser profiles and sessions for different users."""

    # Class-level registry to track active sessions across all instances
    _active_sessions = {}
    _lock = threading.Lock()

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

    async def load_session(
        self,
        user_id: str,
        headless: bool = False
    ) -> tuple:
        """
        Load or create a browser session.

        If a profile exists for the user_id, it will be loaded (with saved cookies, login state, etc.).
        If no profile exists, a new one will be created automatically.

        Args:
            user_id: User identifier
            headless: Run in headless mode

        Returns:
            Tuple of (playwright instance, BrowserContext, session_id)
            Both playwright and context must be closed properly to ensure session persistence.
            Use unregister_session(session_id) after closing to clean up tracking.
        """
        profile_dir = self.get_profile_dir(user_id)

        if self.profile_exists(user_id):
            print(f"📁 Loading existing browser profile for user: {user_id}")
        else:
            print(f"📁 Creating new browser profile for user: {user_id}")

        playwright = await async_playwright().start()
        context = await playwright.chromium.launch_persistent_context(
            user_data_dir=str(profile_dir),
            headless=headless,
            args=['--disable-blink-features=AutomationControlled']
        )

        # Register session for cleanup tracking
        import threading
        session_id = f"{user_id}_{threading.get_ident()}_{time.time()}"

        with self._lock:
            self._active_sessions[session_id] = {
                'playwright': playwright,
                'context': context,
                'user_id': user_id,
                'created_at': time.time()
            }

        print(f"🔍 Registered session: {session_id} (total active: {len(self._active_sessions)})")

        return playwright, context, session_id

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

    def unregister_session(self, session_id: str) -> None:
        """
        Unregister a session from the active sessions registry.

        Args:
            session_id: Session identifier returned by load_session()
        """
        with self._lock:
            if session_id in self._active_sessions:
                del self._active_sessions[session_id]
                print(f"✅ Unregistered session: {session_id} (remaining: {len(self._active_sessions)})")

    @classmethod
    async def cleanup_all_sessions(cls) -> None:
        """
        Clean up all active browser sessions.

        This should be called during application shutdown to ensure
        all browser profiles are properly saved before exit.
        """
        with cls._lock:
            if not cls._active_sessions:
                print("No active sessions to clean up")
                return

            print(f"\n🛑 Cleaning up {len(cls._active_sessions)} active browser session(s)...")

            for session_id, session_data in list(cls._active_sessions.items()):
                try:
                    user_id = session_data.get('user_id', 'unknown')
                    context = session_data.get('context')
                    playwright = session_data.get('playwright')

                    print(f"  💾 Saving profile for user: {user_id}")

                    if context:
                        await context.close()
                    if playwright:
                        await playwright.stop()

                    print(f"  ✅ Profile saved for user: {user_id}")

                except Exception as e:
                    print(f"  ⚠️  Error cleaning up session {session_id}: {e}")

            # Clear the registry
            cls._active_sessions.clear()
            print("✅ All browser sessions cleaned up successfully\n")
