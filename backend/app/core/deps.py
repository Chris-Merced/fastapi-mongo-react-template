"""
FastAPI "dependencies" - functions declared as a route parameter's default
(`Depends(...)`) that FastAPI calls for you before the route body runs,
injecting the result. `get_current_user` here is conceptually an Express
auth middleware, just expressed as "a value the route asks for" instead of
"a function that runs before the handler and calls next()".

`require_role(...)` goes a step further: it's a function that *returns* a
dependency, so each route can parameterize which roles are allowed:

    Depends(require_role(Role.admin, Role.manager))
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.security import JWTError, decode_access_token
from app.db.mongodb import get_database
from app.models.user import Role, UserOut

# tokenUrl tells Swagger's "Authorize" button where to POST for a token -
# it doesn't call that URL itself here, it's purely metadata for /docs.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncIOMotorDatabase = Depends(get_database),
) -> UserOut:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(token)
    except JWTError:
        raise unauthorized

    email = payload.get("sub")
    if email is None:
        raise unauthorized

    user = await db["users"].find_one({"email": email})
    if user is None:
        raise unauthorized

    return UserOut.model_validate(user)


def require_role(*allowed_roles: Role):
    async def role_checker(current_user: UserOut = Depends(get_current_user)) -> UserOut:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to perform this action",
            )
        return current_user

    return role_checker
