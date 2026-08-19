


from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field



class CreateUserRequest(BaseModel):
    username: str = Field(min_length=2, max_length=100)
    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    second_name: str | None = Field(default=None, min_length=1, max_length=100)
    email: EmailStr
    description: str | None = Field(default=None, min_length=1, max_length=500)


class UpdateUserRequest(BaseModel):
    username: str = Field(min_length=2, max_length=100)
    first_name: str | None = Field(..., min_length=1, max_length=100)
    second_name: str | None = Field(..., min_length=1, max_length=100)
    email: EmailStr
    description: str | None = Field(..., min_length=1, max_length=500)


class User(BaseModel):
    id: UUID
    username: str 
    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    second_name: str | None = Field(default=None, min_length=1, max_length=100)
    email: EmailStr
    description: str | None = Field(default=None, min_length=1, max_length=500)

    created_at: datetime

    model_config = ConfigDict(from_attributes=True)