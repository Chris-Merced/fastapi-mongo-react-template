"""
Shared Mongo/Pydantic plumbing.

Mongo's `_id` is a `bson.ObjectId`, not a JSON-native type - it can't be
returned directly in an API response or accepted directly from one. The
fix used throughout this app: represent ids as plain `str` everywhere in
the Pydantic layer, and convert to/from `ObjectId` only at the point where
we actually talk to Mongo (see app/db/helpers.py, added alongside the
routers). This keeps the "Mongo-specific" type contained to one place
instead of leaking into every model.

PyObjectId below is a `str` for all Pydantic purposes, but if something
that isn't already a plain string comes in (e.g. Mongo hands back a real
ObjectId), BeforeValidator(str) coerces it first. `Annotated[X, ...]` is
Python's way of attaching metadata to a type - conceptually similar to
using a branded/tagged type in TS, except the "brand" here (BeforeValidator)
actually runs code during validation.
"""
from datetime import datetime
from typing import Annotated, Any

from pydantic import AliasChoices, BaseModel, BeforeValidator, ConfigDict, Field

PyObjectId = Annotated[str, BeforeValidator(str)]


class MongoBaseModel(BaseModel):
    """
    Base for any model that represents a document read back out of Mongo.

    `validation_alias` (input-only, unlike plain `alias`, which would also
    apply on the way out) means: accept this field from Mongo's `_id` key
    OR a plain "id" key, but always *serialize* it back out as "id" - API
    consumers (the React frontend, Swagger docs) should never have to know
    Mongo's `_id` naming exists.
    """
    id: PyObjectId = Field(validation_alias=AliasChoices("_id", "id"))

    model_config = ConfigDict(populate_by_name=True)


class TimestampMixin(BaseModel):
    created_at: datetime
    updated_at: datetime


Metadata = dict[str, Any]
