from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.deps import get_current_user
from app.core.security import create_access_token, hash_password, verify_password
from app.db.helpers import with_timestamps
from app.db.mongodb import get_database
from app.models.user import TokenResponse, UserCreate, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])

COLLECTION = "users"


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate, db: AsyncIOMotorDatabase = Depends(get_database)):
    existing = await db[COLLECTION].find_one({"email": user.email})
    if existing is not None:
        raise HTTPException(status_code=400, detail="Email already registered")

    doc = with_timestamps(
        {
            "email": user.email,
            "hashed_password": hash_password(user.password),
            "role": user.role,
        },
        is_new=True,
    )
    result = await db[COLLECTION].insert_one(doc)
    return await db[COLLECTION].find_one({"_id": result.inserted_id})


@router.post("/login", response_model=TokenResponse)
async def login(
    # OAuth2PasswordRequestForm reads standard form fields (username,
    # password) from the request body - not JSON. This is what makes
    # Swagger's "Authorize" button work out of the box, and it's the
    # conventional OAuth2 password-grant shape. We map "username" to our
    # email field below; there's no separate username concept in this app.
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    user = await db[COLLECTION].find_one({"email": form_data.username})
    if user is None or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(subject=user["email"], role=user["role"])
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserOut)
async def read_current_user(current_user: UserOut = Depends(get_current_user)):
    return current_user
