"""Monthly achievements, scoped to a team via team_id."""
import re

from pydantic import BaseModel, Field, field_validator

from app.models.common import MongoBaseModel, PyObjectId, TimestampMixin

MONTH_PATTERN = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


class AchievementBase(BaseModel):
    team_id: PyObjectId
    month: str = Field(description="YYYY-MM, e.g. 2026-08")
    title: str
    description: str

    @field_validator("month")
    @classmethod
    def validate_month(cls, value: str) -> str:
        if not MONTH_PATTERN.match(value):
            raise ValueError("month must be in YYYY-MM format")
        return value


class AchievementCreate(AchievementBase):
    pass


class AchievementUpdate(BaseModel):
    month: str | None = None
    title: str | None = None
    description: str | None = None

    @field_validator("month")
    @classmethod
    def validate_month(cls, value: str | None) -> str | None:
        if value is not None and not MONTH_PATTERN.match(value):
            raise ValueError("month must be in YYYY-MM format")
        return value


class AchievementOut(MongoBaseModel, AchievementBase, TimestampMixin):
    pass
