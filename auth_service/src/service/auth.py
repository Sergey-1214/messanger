import logging
from typing import AsyncGenerator
import uuid

from fastapi import Depends
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.client.user import (
    UserClient,
    UserClientConnectionError,
    UserClientResponseError,
    get_user_client,
)
from src.schemas.auth import LoginRequest, LogoutRequest, RefreshTokenRequest, RegisterRequest, TokenPair, User, UserDTO
from src.core.security import create_access_token, create_refresh_token, hash_password, hash_refresh_token, verify_password
from src.db.database import get_db_session
from src.exceptions.auth import (
    BadRequestException,
    UnauthorizedException,
    UserAlreadyExistsException,
    UserNotFoundException,
    UserServiceException,
    UserServiceUnavailableException,
)
from src.repository.auth import AuthRepository, get_auth_repository

logger = logging.getLogger(__name__)

class AuthService:
    def __init__(self, 
        repo: AuthRepository = Depends(get_auth_repository), 
        session: AsyncSession = Depends(get_db_session),
        client: UserClient = Depends(get_user_client)
    ):
        self.repo = repo
        self.session = session
        self.client = client


    async def register(self, request: RegisterRequest) -> User:
        user_id = uuid.uuid4()
        hashed_password = hash_password(password=request.password.get_secret_value())
        try:
            user = await self.repo.register(
                user_id=user_id,
                username=request.username, 
                email=request.email,
                hashed_password=hashed_password
            )

        except IntegrityError as exc:
            await self.session.rollback()
            raise UserAlreadyExistsException(
                email=request.email, 
                username=request.username
            ) from exc
        try:
            await self.client.create_user(
                user_id=user_id,
                username=request.username,
                email=request.email,
            )
        except UserClientResponseError as exc:
            await self.session.rollback()
            if exc.status_code == 409:
                raise UserAlreadyExistsException(
                    email=request.email,
                    username=request.username
                ) from exc
            raise UserServiceException() from exc
        except UserClientConnectionError as exc:
            await self.session.rollback()
            raise UserServiceUnavailableException() from exc

        await self.session.commit()
        return user
    
    
    async def login(self, request: LoginRequest) -> TokenPair:
        if not request.email:
            user = await self.repo.get_user_by_username(request.username)
        else:
            user = await self.repo.get_user_by_email(request.email)

        if user is None or not verify_password(request.password.get_secret_value(), user.password_hash):
            raise UnauthorizedException()
        
        token_pair = await self.create_token_pair(user.id)
        
        await self.session.commit()

        return token_pair
    
    
    async def refresh_token(self, request: RefreshTokenRequest):
        refresh_token_hash = hash_refresh_token(request.refresh_token)
        token = await self.repo.get_refresh_token(refresh_token_hash)
        if not token:
            raise UnauthorizedException()

        await self.repo.revoked_refresh_token(token.refresh_token_hash)

        token_pair = await self.create_token_pair(token.user_id)


        await self.session.commit()

        return token_pair
    

    async def logout(self, request: LogoutRequest):
        refresh_token_hash = hash_refresh_token(request.refresh_token)
        if not await self.repo.get_refresh_token(refresh_token_hash):
            raise UnauthorizedException()
        
        await self.repo.revoked_refresh_token(refresh_token_hash)
    
        await self.session.commit()
        

    async def create_token_pair(self, user_id: uuid.UUID) -> TokenPair:
        access_token = create_access_token(user_id)
        refresh_token, expires_at = create_refresh_token()
        refresh_token_hash = hash_refresh_token(refresh_token)
        await self.repo.save_refresh_token(
            user_id=user_id, 
            refresh_token_hash=refresh_token_hash,
            expires_at=expires_at,
        )

        return TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
            refresh_token_expires_at=expires_at,
        )

    async def users_batch(self, users_ids: set[uuid.UUID]) -> list[UserDTO]:    
        if len(users_ids) > 100:
            raise BadRequestException("Too many users in batch")

        users = await self.repo.users_batch(users_ids=users_ids)

        users_dto = []  
        for user in users:
            users_dto.append(UserDTO(
                id=user.id,
                username=user.username,
                email=user.email,
                created_at=user.created_at
            ))

        return users_dto

    async def get_user_by_id(self, user_id: uuid.UUID) -> UserDTO:
        user = await self.repo.get_user_by_id(user_id)
        if user is None:
            raise UserNotFoundException()

        return UserDTO(
            id=user.id,
            username=user.username,
            email=user.email,
            created_at=user.created_at,
        )

async def get_auth_service(
        repo: AuthRepository = Depends(get_auth_repository),
        session: AsyncSession = Depends(get_db_session),
        client: UserClient = Depends(get_user_client),
) -> AsyncGenerator[AuthService, None]:
    yield AuthService(
        repo=repo,
        session=session,
        client=client,
    )
