import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.schemas.auth import GetUsersBatchRequest, GetUsersBatchResponse, LoginRequest, RefreshTokenRequest, RegisterRequest, TokenPair, UserDTO
from src.service.auth import AuthService, get_auth_service
from src.core.security import get_access_token_payload

logger = logging.getLogger(__name__)

auth_router = APIRouter(prefix="/auth", tags=["auth"])

security = HTTPBearer()

async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> uuid.UUID:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization token"
        )
    token = credentials.credentials
    user_str_id = get_access_token_payload(token)
    if user_str_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    try:
        user_id = uuid.UUID(user_str_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    return user_id


@auth_router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    service: AuthService = Depends(get_auth_service)
) -> UserDTO:
    return await service.register(request)


@auth_router.post("/login", status_code=status.HTTP_200_OK)
async def login(
    request: LoginRequest,
    service: AuthService = Depends(get_auth_service)
) -> TokenPair:
    return await service.login(request)


@auth_router.post("/refresh", status_code=status.HTTP_200_OK)
async def refresh_token(
    request: RefreshTokenRequest,
    service: AuthService = Depends(get_auth_service),
) -> TokenPair:
    return await service.refresh_token(request)


@auth_router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request: RefreshTokenRequest,
    service: AuthService = Depends(get_auth_service),
    current_user: uuid.UUID = Depends(get_current_user_id)
):
    return await service.logout(request)


@auth_router.post("/users/batch")
async def users_batch(
    request: GetUsersBatchRequest,
    service: AuthService = Depends(get_auth_service),
) -> GetUsersBatchResponse:
    users = await service.users_batch(request.user_ids)
    return GetUsersBatchResponse(users=users)
