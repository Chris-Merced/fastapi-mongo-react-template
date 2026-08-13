"""
A Team has one leader and, optionally, an org leader it reports to.

`leader_id` / `org_leader_id` reference Individuals rather than embedding
them - a normal relational-style choice, but worth calling out in Mongo
specifically because embedding is also on the table there. We reference
here because leaders are looked up/updated independently of teams (an
Individual's title or location can change without touching every team
they lead), so embedding would mean keeping duplicated copies in sync.

Business questions this shape answers directly:
  - "teams with leader not co-located with members" -> compare this
    team's `location` against its leader Individual's `location` (or
    against each member's location - see the routers for the exact
    aggregation)
  - "teams reporting to an organization leader" -> org_leader_id is set
"""
from pydantic import BaseModel, Field

from app.models.common import Metadata, MongoBaseModel, PyObjectId, TimestampMixin


class TeamBase(BaseModel):
    name: str
    location: str
    leader_id: PyObjectId
    org_leader_id: PyObjectId | None = Field(
        default=None,
        description="Set if this team reports up to an organization leader.",
    )
    metadata: Metadata = Field(default_factory=dict)


class TeamCreate(TeamBase):
    pass


class TeamUpdate(BaseModel):
    name: str | None = None
    location: str | None = None
    leader_id: PyObjectId | None = None
    org_leader_id: PyObjectId | None = None
    metadata: Metadata | None = None


class TeamOut(MongoBaseModel, TeamBase, TimestampMixin):
    pass
