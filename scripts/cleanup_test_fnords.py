#!/usr/bin/env python3
"""
Clean up test fnords from the production database.

Removes all fnords with "Test" in their summary.
Run this to clean up test pollution from your actual database.
"""

import sqlite3
from pathlib import Path

from fnord.config import get_config


def cleanup_test_fnords():
    """Remove all fnords with 'Test' in summary."""
    config = get_config()
    db_path = config.get_db_path()

    print(f"Opening database: {db_path}")

    if not db_path.exists():
        print("Database not found!")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Count test fnords before deletion
    cursor.execute(
        "SELECT COUNT(*) FROM fnords WHERE summary LIKE '%Test%' OR source LIKE '%Test%'"
    )
    count = cursor.fetchone()[0]
    print(f"Found {count} test fnords to remove")

    if count == 0:
        print("No test fnords found. Database is clean!")
        conn.close()
        return

    # Delete test fnords
    cursor.execute(
        "DELETE FROM fnords WHERE summary LIKE '%Test%' OR source LIKE '%Test%'"
    )
    deleted = cursor.rowcount

    conn.commit()
    conn.close()

    print(f"Deleted {deleted} test fnords!")
    print("Database cleaned up. The fnords are pleased.")


if __name__ == "__main__":
    print("🍎 Cleaning up test fnords... 🍎")
    print()
    response = input("This will DELETE all fnords with 'Test' in summary. Continue? [y/N]: ")

    if response.lower() in ("y", "yes"):
        cleanup_test_fnords()
    else:
        print("Aborted.")
