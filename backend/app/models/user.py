"""
Auth identity (User) is deliberately separate from the business entity
(Individual). A User is "someone who can log into this tool"; an
Individual is "a person tracked by the org chart data." They'll often be
the same human, but conflating the two models would mean every business
CRUD change (an Individual changing teams, say) risks touching login
credentials, and vice versa - unrelated concerns, kept unrelated.
"""
from enum import Enum

from pydantic import BaseModel, EmailStr, Field

from app.models.common import MongoBaseModel, TimestampMixin


class Role(str, Enum):
    """
    Subclassing both `str` and `Enum` (a common Python idiom) means Role.admin
    behaves as the string "admin" wherever a string is expected (query
    params, JSON, Mongo documents) while still being a real enum for type
    checking - closer to a TS string-literal union than a typical enum.
    """
    admin = "admin"
    manager = "manager"
    viewer = "viewer"


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    role: Role = Role.viewer


class UserOut(MongoBaseModel, TimestampMixin):
    email: EmailStr
    role: Role
    # Note: hashed_password is intentionally NOT a field here - this is the
    # model returned to clients, and password hashes should never leave
    # the server, even hashed ones.


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
