from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ReturnDocument

from app.core.deps import get_current_user, require_role
from app.db.helpers import to_object_id, with_timestamps
from app.db.mongodb import get_database
from app.models.individual import IndividualCreate, IndividualOut, IndividualUpdate
from app.models.user import Role

# Router-level dependency: EVERY route below requires a valid JWT, i.e.
# you must be logged in to even read this data. Mutating routes layer an
# additional role check on top via their own `dependencies=`.
router = APIRouter(
    prefix="/individuals", tags=["individuals"], dependencies=[Depends(get_current_user)]
)

write_access = Depends(require_role(Role.admin, Role.manager))

COLLECTION = "individuals"


@router.post(
    "",
    response_model=IndividualOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[write_access],
)
async def create_individual(
    individual: IndividualCreate, db: AsyncIOMotorDatabase = Depends(get_database)
):
    doc = with_timestamps(individual.model_dump(), is_new=True)
    result = await db[COLLECTION].insert_one(doc)
    return await db[COLLECTION].find_one({"_id": result.inserted_id})


@router.get("", response_model=list[IndividualOut])
async def list_individuals(
    team_id: str | None = None, db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Optionally filter by team_id, e.g. GET /individuals?team_id=... to
    answer "who are the members of each team?"."""
    query = {} if team_id is None else {"team_id": team_id}
    return await db[COLLECTION].find(query).to_list(length=None)


@router.get("/{individual_id}", response_model=IndividualOut)
async def get_individual(
    individual_id: str, db: AsyncIOMotorDatabase = Depends(get_database)
):
    individual = await db[COLLECTION].find_one({"_id": to_object_id(individual_id)})
    if individual is None:
        raise HTTPException(status_code=404, detail="Individual not found")
    return individual


@router.patch(
    "/{individual_id}", response_model=IndividualOut, dependencies=[write_access]
)
async def update_individual(
    individual_id: str,
    update: IndividualUpdate,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    changes = with_timestamps(update.model_dump(exclude_unset=True), is_new=False)
    result = await db[COLLECTION].find_one_and_update(
        {"_id": to_object_id(individual_id)},
        {"$set": changes},
        return_document=ReturnDocument.AFTER,
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Individual not found")
    return result


@router.delete(
    "/{individual_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[write_access]
)
async def delete_individual(
    individual_id: str, db: AsyncIOMotorDatabase = Depends(get_database)
):
    result = await db[COLLECTION].delete_one({"_id": to_object_id(individual_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Individual not found")
