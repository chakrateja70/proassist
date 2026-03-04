from datetime import datetime, timedelta, timezone
from typing import Any

from cryptography.fernet import Fernet
from jose import JWTError, jwt

from app.core.config import get_settings


ALGORITHM = "HS256"


def create_access_token(subject: str, extra: dict[str, Any] | None = None) -> str:
    settings = get_settings()
    expire_at = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    payload: dict[str, Any] = {"sub": subject, "exp": expire_at}
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    return jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])


def encrypt_secret(value: str) -> str:
    fernet = Fernet(get_settings().token_encryption_key.encode("utf-8"))
    return fernet.encrypt(value.encode("utf-8")).decode("utf-8")


def decrypt_secret(value: str) -> str:
    fernet = Fernet(get_settings().token_encryption_key.encode("utf-8"))
    return fernet.decrypt(value.encode("utf-8")).decode("utf-8")


def is_token_expired(expires_at: datetime | None) -> bool:
    if expires_at is None:
        return True
    return expires_at <= datetime.now(timezone.utc)


class AuthError(Exception):
    pass


def parse_jwt_or_raise(token: str) -> dict[str, Any]:
    try:
        return decode_access_token(token)
    except JWTError as exc:
        raise AuthError("Invalid session token") from exc
