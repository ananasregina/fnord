#!/usr/bin/env python3
"""
Migrate fnords from SQLite to PostgreSQL with semantic embeddings.

Reads all existing fnords, generates embeddings via LM Studio,
and writes to PostgreSQL database.
"""

import asyncio
import sqlite3
import sys
from pathlib import Path
import argparse
import json
from datetime import datetime

from fnord.config import get_config
from fnord.embeddings import EmbeddingService
from fnord.models import FnordSighting
import asyncpg
from pgvector.asyncpg import register_vector


async def migrate(sqlite_path: str, dry_run: bool = False):
    """
    Perform migration from SQLite to PostgreSQL.

    Args:
        sqlite_path: Path to SQLite database
        dry_run: If True, don't modify PostgreSQL (just test)
    """
    print("🍎 Migrating fnords to PostgreSQL... 🍎\n")

    # Get config
    config = get_config()

    # Step 1: Read SQLite database
    sqlite_db_path = Path(sqlite_path)
    if not sqlite_db_path.exists():
        print(f"❌ SQLite database not found: {sqlite_db_path}")
        sys.exit(1)

    print(f"📖 Reading SQLite database: {sqlite_db_path}")
    conn = sqlite3.connect(sqlite_db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM fnords")
    total_count = cursor.fetchone()[0]
    print(f"📊 Found {total_count} fnords to migrate\n")

    if total_count == 0:
        print("No fnords found. Nothing to migrate!")
        conn.close()
        return

    # Step 2: Read all fnords
    cursor.execute("SELECT * FROM fnords ORDER BY id")
    rows = cursor.fetchall()
    conn.close()

    fnords = []
    for row in rows:
        # Parse JSON fields
        notes = None
        if row["notes"]:
            try:
                notes = json.loads(row["notes"])
            except json.JSONDecodeError:
                pass

        logical_fallacies = None
        if row["logical_fallacies"]:
            try:
                parsed = json.loads(row["logical_fallacies"])
                if isinstance(parsed, list) and all(isinstance(x, str) for x in parsed):
                    logical_fallacies = parsed
            except json.JSONDecodeError:
                pass

        fnord = FnordSighting(
            id=row["id"],
            when=row["when"],
            where_place_name=row["where_place_name"],
            source=row["source"],
            summary=row["summary"],
            notes=notes,
            logical_fallacies=logical_fallacies,
        )
        fnords.append(fnord)

    # Step 3: Connect to PostgreSQL
    if dry_run:
        print("🔍 Dry run mode - will not modify PostgreSQL database\n")
    else:
        print("🔌 Connecting to PostgreSQL...")
        pool = await asyncpg.create_pool(config.get_postgres_uri())

        async with pool.acquire() as conn:
            # Verify extension
            await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
            await register_vector(conn)
            print("✓ pgvector extension enabled")

            # Create table if not exists
            dim = config.get_embedding_config()["dimension"]
            await conn.execute(f"""
                CREATE TABLE IF NOT EXISTS fnords (
                    id SERIAL PRIMARY KEY,
                    "when" TIMESTAMP NOT NULL,
                    where_place_name TEXT,
                    source TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    notes JSONB,
                    logical_fallacies JSONB,
                    embedding vector({dim}),
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                )
            """)
            print("✓ Table created")

            # Create index
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_fnords_embedding
                ON fnords USING ivfflat (embedding vector_cosine_ops)
            """)
            print("✓ Vector index created")

    # Step 4: Generate embeddings and insert
    print(f"\n🔄 Generating embeddings for {len(fnords)} fnords...")
    emb_service = EmbeddingService()

    migrated = 0
    skipped = 0

    for i, fnord in enumerate(fnords, 1):
        # Prepare search text
        search_text = f"{fnord.summary} {fnord.source}"
        if fnord.where_place_name:
            search_text += f" {fnord.where_place_name}"

        # Generate embedding
        embedding = await emb_service.generate_embedding(search_text)

        if embedding is None:
            print(f"⚠️  Skipping fnord {fnord.id}: Failed to generate embedding")
            skipped += 1
            continue

        if dry_run:
            print(f"   [DRY RUN] Would migrate fnord {fnord.id}: {fnord.summary[:50]}...")
            migrated += 1
        else:
            # Insert with explicit ID to preserve original
            # Convert datetime string to datetime object (offset-naive)
            when_str = fnord.when.replace("Z", "+00:00")
            when_dt = datetime.fromisoformat(when_str).replace(tzinfo=None)
            async with pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO fnords (id, "when", where_place_name, source, summary, notes, logical_fallacies, embedding)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    ON CONFLICT (id) DO UPDATE
                    SET "when" = EXCLUDED."when",
                        where_place_name = EXCLUDED.where_place_name,
                        source = EXCLUDED.source,
                        summary = EXCLUDED.summary,
                        notes = EXCLUDED.notes,
                        logical_fallacies = EXCLUDED.logical_fallacies,
                        embedding = EXCLUDED.embedding
                """, fnord.id, when_dt, fnord.where_place_name, fnord.source,
                    fnord.summary, json.dumps(fnord.notes) if fnord.notes else None,
                    json.dumps(fnord.logical_fallacies) if fnord.logical_fallacies else None, embedding)

            migrated += 1

        # Progress every 10 fnords
        if i % 10 == 0:
            print(f"   Progress: {i}/{len(fnords)}")

    if not dry_run:
        await pool.close()

    print(f"\n✅ Migration complete!")
    print(f"   Migrated: {migrated} fnords")
    print(f"   Skipped: {skipped} fnords")

    if not dry_run:
        print("\n🍎 All hail Discordia! The fnords have a new home! 🍎")


def main():
    """Main entry point for migration script."""
    parser = argparse.ArgumentParser(
        description="Migrate fnords from SQLite to PostgreSQL with semantic embeddings"
    )
    parser.add_argument(
        "sqlite_path",
        type=str,
        default="./fnord.db",
        help="Path to SQLite database (default: ./fnord.db)",
    )
    parser.add_argument(
        "--no-dry-run",
        action="store_true",
        dest="no_dry_run",
        help="Execute migration (default: dry-run mode)",
    )

    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("Fnord Migration Script: SQLite → PostgreSQL + pgvector")
    print("=" * 60 + "\n")

    asyncio.run(migrate(args.sqlite_path, dry_run=not args.no_dry_run))


if __name__ == "__main__":
    main()
