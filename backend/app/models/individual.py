"""
An Individual is any person tracked in the system - team members, team
leaders, and org leaders are all Individuals; a "team leader" or "org
leader" is just an Individual referenced by a Team, not a separate type.

`is_direct_staff` backs two of the business questions directly:
  - "team leader as a non-direct staff" -> look at the leader Individual's
    is_direct_staff flag
  - "non-direct staff to employees ratio above 20%" -> count Individuals
    per team where is_direct_staff is False
"""
from pydantic import BaseModel, EmailStr, Field

from app.models.common import Metadata, MongoBaseModel, PyObjectId, TimestampMixin


class IndividualBase(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    title: str
    location: str
    is_direct_staff: bool = Field(
        default=True,
        description="False = non-direct staff (e.g. contractor/vendor), "
        "as distinct from an org's direct employees.",
    )
    team_id: PyObjectId | None = Field(
        default=None, description="Team this individual is a member of, if any."
    )
    metadata: Metadata = Field(default_factory=dict)


class IndividualCreate(IndividualBase):
    pass


class IndividualUpdate(BaseModel):
    """All fields optional - only what's present in the request gets changed."""
    first_name: str | None = None
    last_name: str | None = None
    email: EmailStr | None = None
    title: str | None = None
    location: str | None = None
    is_direct_staff: bool | None = None
    team_id: PyObjectId | None = None
    metadata: Metadata | None = None


class IndividualOut(MongoBaseModel, IndividualBase, TimestampMixin):
    pass
