"""Tests for Database Utilities."""

from __future__ import annotations

from datetime import datetime

from bson import ObjectId

from app.infrastructure.database.utils import serialize_document


def test_serialize_document_objectid():
    """Test serialize_document with ObjectId serialization."""
    obj_id = ObjectId()
    result = serialize_document(obj_id)

    assert isinstance(result, str)
    assert result == str(obj_id)


def test_serialize_document_datetime():
    """Test serialize_document with datetime (should pass through)."""
    dt = datetime.now()
    result = serialize_document(dt)

    assert result == dt  # Datetime passes through


def test_serialize_document_nested_structures():
    """Test serialize_document with nested structures."""
    doc = {
        "id": ObjectId(),
        "nested": {
            "id": ObjectId(),
            "list": [ObjectId(), ObjectId()],
        },
        "list": [{"id": ObjectId()}],
    }

    result = serialize_document(doc)

    assert isinstance(result["id"], str)
    assert isinstance(result["nested"]["id"], str)
    assert all(isinstance(item, str) for item in result["nested"]["list"])
    assert isinstance(result["list"][0]["id"], str)


def test_serialize_document_edge_cases():
    """Test serialize_document with edge cases."""
    # None
    assert serialize_document(None) is None

    # Empty dict
    assert serialize_document({}) == {}

    # Empty list
    assert serialize_document([]) == []

    # Primitive types
    assert serialize_document(42) == 42
    assert serialize_document("string") == "string"
    assert serialize_document(True) is True
