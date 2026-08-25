

from datetime import datetime
from typing import Self
import uuid

from pydantic import BaseModel, EmailStr, SecretStr, model_validator


class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: SecretStr

class LoginRequest(BaseModel):
    username: str | None = None
    email: EmailStr | None = None
    password: SecretStr
    @model_validator(mode="after")
    def validate_content(self) -> Self:
        if not self.username and not self.email:
            raise ValueError("Username or email is required")
        return self

class UserDTO(BaseModel):
    id: uuid.UUID
    
    username: str
    email: str

    created_at: datetime

class User(UserDTO):
    hash_password: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    refresh_token_expires_at: datetime
    

class RefreshTokenRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


class GetUsersBatchRequest(BaseModel):
    user_ids: set[uuid.UUID]

class GetUsersBatchResponse(BaseModel):
    users: list[UserDTO]