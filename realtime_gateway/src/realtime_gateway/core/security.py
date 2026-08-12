from uuid import UUID

from jose import JWTError, jwt


def decode_access_token(token: str, secret_key: str) -> UUID | None:
    try:
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
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
