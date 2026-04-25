import pytest

from app.migrations.dual_venue_indexes import (
    build_legacy_partial_indexes,
    build_legacy_unique_indexes_to_drop,
    build_required_indexes,
)


class FakeCursor:
    def __init__(self, rows):
        self.rows = rows

    async def to_list(self, length=None):
        return self.rows


class FakeCollection:
    def __init__(self, db, name, rows=None):
        self.db = db
        self.name = name
        self.rows = rows or []

    def find(self, query):
        return FakeCursor(self.rows)

    async def update_one(self, *args, **kwargs):
        self.db.update_calls.append((self.name, args, kwargs))

    async def create_index(self, *args, **kwargs):
        self.db.create_index_calls.append((self.name, args, kwargs))

    async def drop_index(self, *args, **kwargs):
        self.db.drop_index_calls.append((self.name, args, kwargs))


class FakeDb:
    def __init__(self):
        self.create_index_calls = []
        self.drop_index_calls = []
        self.update_calls = []
        self.collections = {
            "markets": FakeCollection(self, "markets"),
            "events": FakeCollection(self, "events"),
        }

    def __getitem__(self, name):
        return self.collections[name]


@pytest.fixture
def fake_db():
    return FakeDb()


def test_required_indexes_include_compound_venue_indexes():
    indexes = build_required_indexes()
    assert ("markets", (("venue", 1), ("venue_market_id", 1)), True) in indexes
    assert ("events", (("venue", 1), ("venue_event_id", 1)), True) in indexes


def test_migration_drops_legacy_unique_indexes():
    indexes = build_legacy_unique_indexes_to_drop()
    assert ("markets", "polymarket_url_1") in indexes
    assert ("markets", "slug_1") in indexes
    assert ("events", "slug_1") in indexes


def test_legacy_indexes_are_recreated_as_partial_indexes():
    indexes = build_legacy_partial_indexes()
    assert (
        "markets",
        "polymarket_url",
        True,
        {"polymarket_url": {"$exists": True, "$type": "string"}},
    ) in indexes
    assert any(
        collection == "markets"
        and key == "slug"
        and partial_filter.get("venue") == "polymarket"
        for collection, key, _unique, partial_filter in indexes
    )


def test_migration_supports_dry_run_flag():
    from app.migrations.dual_venue_indexes import parse_args

    args = parse_args(["--dry-run"])
    assert args.dry_run is True


@pytest.mark.asyncio
async def test_dry_run_does_not_mutate_indexes_or_documents(fake_db):
    from app.migrations.dual_venue_indexes import run_migration

    await run_migration(dry_run=True, db=fake_db)
    assert fake_db.create_index_calls == []
    assert fake_db.drop_index_calls == []
    assert fake_db.update_calls == []


@pytest.mark.asyncio
async def test_migration_drops_legacy_indexes_before_creating_new_indexes(fake_db):
    from app.migrations.dual_venue_indexes import run_migration

    await run_migration(dry_run=False, db=fake_db)

    assert ("markets", ("polymarket_url_1",), {}) in fake_db.drop_index_calls
    assert any(
        name == "markets"
        and args == ("polymarket_url",)
        and kwargs["partialFilterExpression"] == {
            "polymarket_url": {"$exists": True, "$type": "string"}
        }
        for name, args, kwargs in fake_db.create_index_calls
    )
