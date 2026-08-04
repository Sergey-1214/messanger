from datetime import datetime
from typing import Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class CreateMessageRequest(BaseModel):
    content: str = Field(max_length=10000)

    @model_validator(mode="after")
    def validate_content(self) -> Self:
        self.content = self.content.strip()
        if not self.content:
            raise ValueError("Message content cannot be empty")
        return self


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    chat_id: int
    author_id: UUID
    content: str
    seq: int
    is_deleted: bool
    created_at: datetime
    updated_at: datetime
