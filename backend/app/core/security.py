"""
Password hashing (passlib) and JWT issue/verify (python-jose).

Neither of these is async - they're pure CPU-bound crypto, not I/O, so
there's nothing to `await` here and no event-loop-blocking concern (that
concern is specifically about blocking *I/O* calls like a sync DB driver;
a few milliseconds of bcrypt hashing is normal and fine even inside an
async def).
"""
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(*, subject: str, role: str) -> str:
    settings = get_settings()
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    # "sub" (subject) and "exp" (expiry) are standard JWT claim names -
    # jose checks "exp" automatically on decode and raises if it's passed.
    payload = {"sub": subject, "role": role, "exp": expires_at}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict:
    """Raises jose.JWTError (bad signature, expired, malformed) - callers
    decide how to turn that into an HTTP response."""
    settings = get_settings()
    return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])


__all__ = [
    "hash_password",
    "verify_password",
    "create_access_token",
    "decode_access_token",
    "JWTError",
]
