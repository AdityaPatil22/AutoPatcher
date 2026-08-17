"""One-shot migration: add has_repo_scope column to the users table.

Run once against your database:
    python3 scripts/migrate_add_has_repo_scope.py

Safe to re-run — it checks whether the column already exists before adding it.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import inspect, text

from app.db import engine


def migrate():
    with engine.connect() as conn:
        inspector = inspect(conn)
        columns = {col["name"] for col in inspector.get_columns("users")}

        if "has_repo_scope" in columns:
            print("Column has_repo_scope already exists, skipping")
        else:
            conn.execute(text(
                "ALTER TABLE users ADD COLUMN has_repo_scope BOOLEAN NOT NULL DEFAULT false"
            ))
            print("Added column: has_repo_scope")

        conn.commit()
    print("Migration complete.")


if __name__ == "__main__":
    try:
        migrate()
    except Exception as e:
        print(f"Migration failed: {e}", file=sys.stderr)
        sys.exit(1)
