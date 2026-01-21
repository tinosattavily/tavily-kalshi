"""Shared database utilities."""

from __future__ import annotations

from typing import Any

from bson import ObjectId


def ensure_object_id(value: Any) -> ObjectId:
    """Ensure a value is a valid ObjectId instance.

    Args:
        value: ObjectId or string value.

    Returns:
        ObjectId instance.

    Raises:
        ValueError: If value cannot be converted to ObjectId.
    """
    if isinstance(value, ObjectId):
        return value
    if isinstance(value, str):
        try:
            return ObjectId(value)
        except Exception as exc:
            raise ValueError("Invalid ObjectId string.") from exc
    raise ValueError("Value must be an ObjectId or ObjectId string.")


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
