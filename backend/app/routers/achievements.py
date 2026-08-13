from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ReturnDocument

from app.core.deps import get_current_user, require_role
from app.db.helpers import to_object_id, with_timestamps
from app.db.mongodb import get_database
from app.models.achievement import AchievementCreate, AchievementOut, AchievementUpdate
from app.models.user import Role

router = APIRouter(
    prefix="/achievements", tags=["achievements"], dependencies=[Depends(get_current_user)]
)

write_access = Depends(require_role(Role.admin, Role.manager))

COLLECTION = "achievements"


async def _ensure_team_exists(db: AsyncIOMotorDatabase, team_id: str) -> None:
    found = await db["teams"].find_one({"_id": to_object_id(team_id)}, {"_id": 1})
    if found is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"team_id '{team_id}' does not reference an existing team",
        )


@router.post(
    "",
    response_model=AchievementOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[write_access],
)
async def create_achievement(
    achievement: AchievementCreate, db: AsyncIOMotorDatabase = Depends(get_database)
):
    await _ensure_team_exists(db, achievement.team_id)
    doc = with_timestamps(achievement.model_dump(), is_new=True)
    result = await db[COLLECTION].insert_one(doc)
    return await db[COLLECTION].find_one({"_id": result.inserted_id})


@router.get("", response_model=list[AchievementOut])
async def list_achievements(
    team_id: str | None = None,
    month: str | None = None,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """Supports GET /achievements?team_id=...&month=YYYY-MM to answer
    "what are the key achievements of each team on a monthly basis?"."""
    query: dict = {}
    if team_id is not None:
        query["team_id"] = team_id
    if month is not None:
        query["month"] = month
    return await db[COLLECTION].find(query).to_list(length=None)


@router.get("/{achievement_id}", response_model=AchievementOut)
async def get_achievement(
    achievement_id: str, db: AsyncIOMotorDatabase = Depends(get_database)
):
    achievement = await db[COLLECTION].find_one({"_id": to_object_id(achievement_id)})
    if achievement is None:
        raise HTTPException(status_code=404, detail="Achievement not found")
    return achievement


@router.patch(
    "/{achievement_id}", response_model=AchievementOut, dependencies=[write_access]
)
async def update_achievement(
    achievement_id: str,
    update: AchievementUpdate,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    changes = with_timestamps(update.model_dump(exclude_unset=True), is_new=False)
    result = await db[COLLECTION].find_one_and_update(
        {"_id": to_object_id(achievement_id)},
        {"$set": changes},
        return_document=ReturnDocument.AFTER,
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Achievement not found")
    return result


@router.delete(
    "/{achievement_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[write_access],
)
async def delete_achievement(
    achievement_id: str, db: AsyncIOMotorDatabase = Depends(get_database)
):
    result = await db[COLLECTION].delete_one({"_id": to_object_id(achievement_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Achievement not found")
