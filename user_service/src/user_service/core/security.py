from uuid import UUID

from jose import JWTError, jwt

from user_service.core.settings import settings


def decode_access_token(token: str) -> UUID | None:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    except JWTError:
        return None

    if payload.get("type") != "access_token":
        return None

    subject = payload.get("sub")
    if not isinstance(subject, str):
        return None

    try:
        return UUID(subject)
    except ValueError:
        return None
