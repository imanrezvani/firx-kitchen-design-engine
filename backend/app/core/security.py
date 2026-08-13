import datetime as dt
import uuid

import jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return pwd_context.verify(plain, hashed)
    except Exception:
        return False


def _create_token(subject: str, token_type: str, minutes: int) -> str:
    now = dt.datetime.now(dt.timezone.utc)
    payload = {
        "sub": subject,
        "type": token_type,
        "iat": now,
        "exp": now + dt.timedelta(minutes=minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_access_token(user_id: uuid.UUID) -> str:
    return _create_token(str(user_id), "access", settings.access_token_minutes)


def create_refresh_token(user_id: uuid.UUID) -> str:
    return _create_token(str(user_id), "refresh", settings.refresh_token_minutes)


def decode_token(token: str) -> dict:
    """Raises jwt.InvalidTokenError on bad/expired tokens."""
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
