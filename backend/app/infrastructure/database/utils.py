"""Shared database utilities."""

from __future__ import annotations

from typing import Any

from bson import ObjectId


def serialize_document(doc: Any) -> Any:
    """Recursively serialize MongoDB documents, converting ObjectIds to strings.

    Args:
        doc: Document to serialize (can be dict, list, ObjectId, or primitive)

    Returns:
        Serialized document with ObjectIds converted to strings
    """
    if doc is None:
        return None
    if isinstance(doc, ObjectId):
        return str(doc)
    if isinstance(doc, list):
        return [serialize_document(item) for item in doc]
    if isinstance(doc, dict):
        return {key: serialize_document(value) for key, value in doc.items()}
    return doc
