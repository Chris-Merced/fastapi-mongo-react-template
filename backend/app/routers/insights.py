"""
Aggregation-pipeline endpoints answering ACME's actual business questions.

A motor aggregation call has a different shape than the find()/find_one()
calls elsewhere in this app: `db[coll].aggregate(pipeline)` takes a *list
of pipeline stages* (each a dict, Mongo's own query language - not
Python/Pydantic) and returns an async cursor, same as find(). The stages
run left-to-right, each one's output feeding the next - conceptually a
lot like chaining .filter()/.map()/.reduce() in JS, just expressed as
declarative dicts sent to the database instead of code that runs locally.
Doing it this way (vs. fetching everything and reducing in Python) means
Mongo does the join/filter/math server-side, once, instead of us pulling
every document over the wire.
"""
from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.deps import get_current_user
from app.db.mongodb import get_database
from app.models.insights import InsightsSummary, TeamAchievements, TeamInsight

router = APIRouter(
    prefix="/insights", tags=["insights"], dependencies=[Depends(get_current_user)]
)


def _teams_overview_pipeline() -> list[dict]:
    return [
        # team.leader_id is stored as a string; individuals._id is a real
        # ObjectId. $toObjectId bridges the two so the $lookup below can
        # actually match - this is the gotcha called out above.
        {"$addFields": {"leader_oid": {"$toObjectId": "$leader_id"}}},
        {
            "$lookup": {
                "from": "individuals",
                "localField": "leader_oid",
                "foreignField": "_id",
                "as": "leader_arr",
            }
        },
        # $lookup always returns an array (0 or more matches); $unwind
        # flattens the (at most 1-element, since ids are unique) array
        # into a plain embedded object. preserveNullAndEmptyArrays keeps
        # the team in results even if its leader was somehow deleted.
        {"$unwind": {"path": "$leader_arr", "preserveNullAndEmptyArrays": True}},
        {
            # individuals reference their team by team_id (a string), so
            # this join goes the other direction: match individuals whose
            # team_id equals this team's _id, stringified. `let` + a
            # sub-pipeline (rather than localField/foreignField) is needed
            # here because the comparison itself requires a conversion.
            "$lookup": {
                "from": "individuals",
                "let": {"team_id_str": {"$toString": "$_id"}},
                "pipeline": [
                    {"$match": {"$expr": {"$eq": ["$team_id", "$$team_id_str"]}}},
                    {
                        "$project": {
                            "_id": 1,
                            "first_name": 1,
                            "last_name": 1,
                            "email": 1,
                            "is_direct_staff": 1,
                        }
                    },
                ],
                "as": "members",
            }
        },
        {
            "$addFields": {
                "leader": "$leader_arr",
                "member_count": {"$size": "$members"},
                "non_direct_staff_count": {
                    "$size": {
                        "$filter": {
                            "input": "$members",
                            "as": "m",
                            "cond": {"$eq": ["$$m.is_direct_staff", False]},
                        }
                    }
                },
            }
        },
        {
            "$addFields": {
                "non_direct_staff_ratio": {
                    "$cond": [
                        {"$eq": ["$member_count", 0]},
                        0,
                        {"$divide": ["$non_direct_staff_count", "$member_count"]},
                    ]
                },
                "leader_co_located": {"$eq": ["$location", "$leader.location"]},
                "leader_is_non_direct_staff": {"$eq": ["$leader.is_direct_staff", False]},
                "reports_to_org_leader": {"$ne": ["$org_leader_id", None]},
            }
        },
        {"$project": {"leader_oid": 0, "leader_arr": 0}},
    ]


@router.get("/teams-overview", response_model=list[TeamInsight])
async def teams_overview(db: AsyncIOMotorDatabase = Depends(get_database)):
    """Per-team roster + computed flags - answers "who are the members of
    each team", "where are teams located", co-location, leader staff type,
    non-direct-staff ratio, and org-leader reporting, all in one document
    per team."""
    return await db["teams"].aggregate(_teams_overview_pipeline()).to_list(length=None)


@router.get("/summary", response_model=InsightsSummary)
async def summary(db: AsyncIOMotorDatabase = Depends(get_database)):
    """The literal "how many teams..." counts, computed from the same
    per-team data as /teams-overview."""
    docs = await db["teams"].aggregate(_teams_overview_pipeline()).to_list(length=None)
    return InsightsSummary(
        total_teams=len(docs),
        teams_with_leader_not_colocated=sum(
            1 for d in docs if not d.get("leader_co_located")
        ),
        teams_with_non_direct_leader=sum(
            1 for d in docs if d.get("leader_is_non_direct_staff")
        ),
        teams_with_high_non_direct_ratio=sum(
            1 for d in docs if d.get("non_direct_staff_ratio", 0) > 0.2
        ),
        teams_reporting_to_org_leader=sum(
            1 for d in docs if d.get("reports_to_org_leader")
        ),
    )


@router.get("/achievements-by-month", response_model=list[TeamAchievements])
async def achievements_by_month(
    month: str | None = None, db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Achievements grouped by team, optionally filtered to one YYYY-MM
    month - answers "key achievements of each team on a monthly basis"."""
    stages: list[dict] = []
    if month is not None:
        stages.append({"$match": {"month": month}})
    stages += [
        {"$addFields": {"team_oid": {"$toObjectId": "$team_id"}}},
        {
            "$lookup": {
                "from": "teams",
                "localField": "team_oid",
                "foreignField": "_id",
                "as": "team",
            }
        },
        {"$unwind": "$team"},
        {
            "$group": {
                "_id": "$team_id",
                "team_name": {"$first": "$team.name"},
                "achievements": {
                    "$push": {
                        "id": {"$toString": "$_id"},
                        "month": "$month",
                        "title": "$title",
                        "description": "$description",
                    }
                },
            }
        },
        {"$project": {"_id": 0, "team_id": "$_id", "team_name": 1, "achievements": 1}},
    ]
    return await db["achievements"].aggregate(stages).to_list(length=None)
