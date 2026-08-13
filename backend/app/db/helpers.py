"""
The one place in the app that knows Mongo ids are ObjectIds.

Every router talks to this module instead of importing `bson.ObjectId`
directly, so if that ever needs to change, it changes in one file.
"""
from datetime import datetime, timezone
from typing import Any

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import HTTPException, status


def to_object_id(id_str: str) -> ObjectId:
    """
    Convert a path/body id string to a real ObjectId, or raise a clean 400.

    Without this, passing something like "not-an-id" to Mongo raises
    bson.errors.InvalidId deep inside a query - which FastAPI would
    otherwise turn into an opaque 500. Converting explicitly at the edge
    turns bad input into the 400 it actually is.
    """
    try:
        return ObjectId(id_str)
    except (InvalidId, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"'{id_str}' is not a valid id",
        )


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def with_timestamps(doc: dict[str, Any], *, is_new: bool) -> dict[str, Any]:
    """Stamp created_at (only on insert) and updated_at (always)."""
    now = utcnow()
    doc["updated_at"] = now
    if is_new:
        doc["created_at"] = now
    return doc
