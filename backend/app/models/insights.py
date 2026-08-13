"""Response shapes for the aggregation-driven /insights endpoints."""
from pydantic import BaseModel

from app.models.common import MongoBaseModel


class LeaderSummary(MongoBaseModel):
    first_name: str
    last_name: str
    email: str
    location: str
    is_direct_staff: bool


class MemberSummary(MongoBaseModel):
    first_name: str
    last_name: str
    email: str


class TeamInsight(MongoBaseModel):
    name: str
    location: str
    leader: LeaderSummary | None
    members: list[MemberSummary]
    member_count: int
    non_direct_staff_count: int
    non_direct_staff_ratio: float
    leader_co_located: bool
    leader_is_non_direct_staff: bool
    reports_to_org_leader: bool


class InsightsSummary(BaseModel):
    total_teams: int
    teams_with_leader_not_colocated: int
    teams_with_non_direct_leader: int
    teams_with_high_non_direct_ratio: int
    teams_reporting_to_org_leader: int


class AchievementSummary(BaseModel):
    id: str
    month: str
    title: str
    description: str


class TeamAchievements(BaseModel):
    team_id: str
    team_name: str
    achievements: list[AchievementSummary]
