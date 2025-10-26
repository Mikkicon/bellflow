#!/usr/bin/env python3
"""Remove all browser profiles."""

from app.scraper.session_manager import SessionManager

if __name__ == "__main__":
    # Initialize session manager
    manager = SessionManager()

    # List all existing profiles
    profiles = manager.list_profiles()

    if not profiles:
        print("No browser profiles found to remove.")
        exit(0)

    # Show profiles to be deleted
    print(f"\nFound {len(profiles)} browser profile(s):")
    for profile in profiles:
        print(f"  - {profile}")

    # Confirm deletion
    response = input("\nAre you sure you want to delete ALL profiles? (yes/no): ")

    if response.lower() not in ['yes', 'y']:
        print("❌ Cancelled. No profiles were deleted.")
        exit(0)

    # Delete all profiles
    print("\n🗑️  Deleting profiles...")
    for profile in profiles:
        manager.delete_session(profile)

    print(f"\n✅ Successfully removed all {len(profiles)} browser profile(s)!")
