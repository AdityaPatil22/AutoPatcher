"""One-shot migration: rename gemini_requests_* columns to llm_requests_*.

Run once against your database:
    python migrate_rename_llm_columns.py

Safe to re-run — it checks whether the old columns still exist before renaming.
"""

import sys

from sqlalchemy import inspect, text

from app.db import engine


def migrate():
    with engine.connect() as conn:
        inspector = inspect(conn)
        columns = {col["name"] for col in inspector.get_columns("users")}

        if "gemini_requests_today" in columns:
            conn.execute(text(
                'ALTER TABLE users RENAME COLUMN gemini_requests_today TO llm_requests_today'
            ))
            print("Renamed: gemini_requests_today -> llm_requests_today")
        else:
            print("Column gemini_requests_today not found (already migrated?)")

        if "gemini_requests_date" in columns:
            conn.execute(text(
                'ALTER TABLE users RENAME COLUMN gemini_requests_date TO llm_requests_date'
            ))
            print("Renamed: gemini_requests_date -> llm_requests_date")
        else:
            print("Column gemini_requests_date not found (already migrated?)")

        conn.commit()
    print("Migration complete.")


if __name__ == "__main__":
    try:
        migrate()
    except Exception as e:
        print(f"Migration failed: {e}", file=sys.stderr)
        sys.exit(1)
