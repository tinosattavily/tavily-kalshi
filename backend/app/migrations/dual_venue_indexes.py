"""Standalone MongoDB migration script (CLI ops tool, not part of the FastAPI request path).

Run manually via `python -m app.migrations.dual_venue_indexes [--dry-run]` to
backfill legacy Polymarket-only rows and rebuild venue-aware unique indexes.

Reached only by tests and direct CLI invocation; intentionally NOT imported by
app/main.py or any runtime route. Static reachability analysis from main.py
will (correctly) flag this module as unreachable — that's by design.
"""

from __future__ import annotations

import argparse
import asyncio
from collections import Counter
from typing import Any

from pymongo.errors import OperationFailure

from app.domains.markets.canonicalization import canonicalize_url
from app.infrastructure.database.client import get_async_db


def derive_event_slug(slug: str | None) -> str:
    if not slug:
        return ""
    parts = slug.split("-")
    return "-".join(parts[:-1]) if len(parts) > 1 else slug


def parse_args(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args(argv)


def build_required_indexes():
    return [
        ("markets", (("venue", 1), ("venue_market_id", 1)), True),
        ("events", (("venue", 1), ("venue_event_id", 1)), True),
    ]


def build_legacy_partial_indexes():
    polymarket_slug_filter = {
        "venue": "polymarket",
        "slug": {"$exists": True, "$type": "string"},
    }
    return [
        ("events", "slug", True, polymarket_slug_filter),
        ("markets", "slug", True, polymarket_slug_filter),
        (
            "markets",
            "polymarket_url",
            True,
            {"polymarket_url": {"$exists": True, "$type": "string"}},
        ),
    ]


def build_legacy_unique_indexes_to_drop():
    return [
        ("events", "slug_1"),
        ("markets", "slug_1"),
        ("markets", "polymarket_url_1"),
    ]


async def find_duplicate_target_keys(db):
    duplicates = []
    for collection_name, id_field in (
        ("markets", "venue_market_id"),
        ("events", "venue_event_id"),
    ):
        rows = await db[collection_name].find({}).to_list(length=None)
        keys = [
            (row.get("venue"), row.get(id_field))
            for row in rows
            if (row.get("venue"), row.get(id_field)) != (None, None)
        ]
        duplicates.extend(
            (collection_name, key)
            for key, count in Counter(keys).items()
            if count > 1
        )
    return duplicates


async def backfill_legacy_polymarket_rows(db, *, dry_run: bool):
    market_rows = await db["markets"].find({"venue": {"$exists": False}}).to_list(length=None)
    event_rows = await db["events"].find({"venue": {"$exists": False}}).to_list(length=None)
    if dry_run:
        return {
            "markets": {"matched": len(market_rows), "updated": 0},
            "events": {"matched": len(event_rows), "updated": 0},
        }

    market_updates = 0
    for row in market_rows:
        raw_url = row.get("polymarket_url") or ""
        slug = row.get("slug")
        event_slug = derive_event_slug(slug)
        update = {
            "venue": "polymarket",
            "raw_url": raw_url,
            "canonical_url": canonicalize_url(raw_url) if raw_url else "",
            "venue_market_id": slug,
            "venue_event_id": event_slug,
        }
        await db["markets"].update_one({"_id": row["_id"]}, {"$set": update})
        market_updates += 1

    event_updates = 0
    for row in event_rows:
        slug = row.get("slug")
        update = {
            "venue": "polymarket",
            "venue_event_id": slug,
        }
        await db["events"].update_one({"_id": row["_id"]}, {"$set": update})
        event_updates += 1

    return {
        "markets": {"matched": len(market_rows), "updated": market_updates},
        "events": {"matched": len(event_rows), "updated": event_updates},
    }


async def run_migration(dry_run: bool, db=None):
    db = db or await get_async_db()
    duplicates = await find_duplicate_target_keys(db)
    if duplicates:
        raise RuntimeError(f"Duplicate target venue keys: {duplicates}")

    backfill_result = await backfill_legacy_polymarket_rows(db, dry_run=dry_run)
    if dry_run:
        return {"dry_run": True, "backfill": backfill_result}

    duplicates = await find_duplicate_target_keys(db)
    if duplicates:
        raise RuntimeError(f"Duplicate target venue keys after backfill: {duplicates}")

    for collection_name, index_name in build_legacy_unique_indexes_to_drop():
        try:
            await db[collection_name].drop_index(index_name)
        except OperationFailure as exc:
            if "index not found" not in str(exc).lower():
                raise

    for collection_name, keys, unique in build_required_indexes():
        await db[collection_name].create_index(list(keys), unique=unique)

    for collection_name, key, unique, partial_filter in build_legacy_partial_indexes():
        await db[collection_name].create_index(
            key,
            unique=unique,
            partialFilterExpression=partial_filter,
        )

    return {"dry_run": False, "backfill": backfill_result}


def main(argv=None) -> dict[str, Any]:
    import json

    args = parse_args(argv)
    result = asyncio.run(run_migration(dry_run=args.dry_run))
    print(json.dumps(result, indent=2, default=str))
    return result


if __name__ == "__main__":
    main()
