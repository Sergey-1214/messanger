from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from user_service.core.security import decode_access_token

security = HTTPBearer(auto_error=False)


async def get_verified_user_id(
    user_id: UUID,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> UUID:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    token_user_id = decode_access_token(credentials.credentials)
    if token_user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    if token_user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to modify this user",
        )

    return user_id


VerifiedUserIdDep = Annotated[UUID, Depends(get_verified_user_id)]
