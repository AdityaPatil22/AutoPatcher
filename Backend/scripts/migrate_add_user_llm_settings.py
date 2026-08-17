"""One-shot migration: add per-user LLM settings columns to the users table.

Run once against your database:
    python3 scripts/migrate_add_user_llm_settings.py

Safe to re-run — it checks whether each column already exists before adding it.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import inspect, text

from app.db import engine

NEW_COLUMNS = {
    "llm_provider": "VARCHAR(50)",
    "llm_model": "VARCHAR(255)",
    "max_context_files": "INTEGER",
}


def migrate():
    with engine.connect() as conn:
        inspector = inspect(conn)
        columns = {col["name"] for col in inspector.get_columns("users")}

        for name, col_type in NEW_COLUMNS.items():
            if name in columns:
                print(f"Column {name} already exists, skipping")
                continue
            conn.execute(text(f"ALTER TABLE users ADD COLUMN {name} {col_type}"))
            print(f"Added column: {name}")

        conn.commit()
    print("Migration complete.")


if __name__ == "__main__":
    try:
        migrate()
    except Exception as e:
        print(f"Migration failed: {e}", file=sys.stderr)
        sys.exit(1)
