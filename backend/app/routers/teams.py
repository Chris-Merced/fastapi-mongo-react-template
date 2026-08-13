from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ReturnDocument

from app.db.helpers import to_object_id, with_timestamps
from app.db.mongodb import get_database
from app.models.team import TeamCreate, TeamOut, TeamUpdate

router = APIRouter(prefix="/teams", tags=["teams"])

COLLECTION = "teams"


async def _ensure_individual_exists(
    db: AsyncIOMotorDatabase, individual_id: str, field_name: str
) -> None:
    """FK-style integrity check - Mongo won't enforce this for us, so the
    application layer has to. Used for leader_id/org_leader_id, which must
    point at a real Individual document."""
    found = await db["individuals"].find_one(
        {"_id": to_object_id(individual_id)}, {"_id": 1}
    )
    if found is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field_name} '{individual_id}' does not reference an existing individual",
        )


@router.post("", response_model=TeamOut, status_code=status.HTTP_201_CREATED)
async def create_team(team: TeamCreate, db: AsyncIOMotorDatabase = Depends(get_database)):
    await _ensure_individual_exists(db, team.leader_id, "leader_id")
    if team.org_leader_id is not None:
        await _ensure_individual_exists(db, team.org_leader_id, "org_leader_id")

    doc = with_timestamps(team.model_dump(), is_new=True)
    result = await db[COLLECTION].insert_one(doc)
    return await db[COLLECTION].find_one({"_id": result.inserted_id})


@router.get("", response_model=list[TeamOut])
async def list_teams(db: AsyncIOMotorDatabase = Depends(get_database)):
    return await db[COLLECTION].find().to_list(length=None)


@router.get("/{team_id}", response_model=TeamOut)
async def get_team(team_id: str, db: AsyncIOMotorDatabase = Depends(get_database)):
    team = await db[COLLECTION].find_one({"_id": to_object_id(team_id)})
    if team is None:
        raise HTTPException(status_code=404, detail="Team not found")
    return team


@router.patch("/{team_id}", response_model=TeamOut)
async def update_team(
    team_id: str, update: TeamUpdate, db: AsyncIOMotorDatabase = Depends(get_database)
):
    if update.leader_id is not None:
        await _ensure_individual_exists(db, update.leader_id, "leader_id")
    if update.org_leader_id is not None:
        await _ensure_individual_exists(db, update.org_leader_id, "org_leader_id")

    changes = with_timestamps(update.model_dump(exclude_unset=True), is_new=False)
    result = await db[COLLECTION].find_one_and_update(
        {"_id": to_object_id(team_id)},
        {"$set": changes},
        return_document=ReturnDocument.AFTER,
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Team not found")
    return result


@router.delete("/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_team(team_id: str, db: AsyncIOMotorDatabase = Depends(get_database)):
    result = await db[COLLECTION].delete_one({"_id": to_object_id(team_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Team not found")
