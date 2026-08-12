from typing import Any, Self
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class ClientEvent(BaseModel):
    type: str
    request_id: UUID
    payload: dict[str, Any]


class CreateMessagePayload(BaseModel):
    chat_id: int = Field(gt=0)
    content: str = Field(max_length=10_000)

    @model_validator(mode="after")
    def validate_content(self) -> Self:
        self.content = self.content.strip()
        if not self.content:
            raise ValueError("Message content cannot be empty")
        return self


class ServerEvent(BaseModel):
    type: str
    request_id: UUID
    payload: dict[str, Any]
