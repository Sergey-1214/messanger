
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field


class PresenceStatus(StrEnum):
    ONLINE = "online"
    OFFLINE = "offline"


class AddConnectionRequest(BaseModel):
    user_id: UUID
    connection_id: str


class DisconnectRequest(BaseModel):
    user_id: UUID
    connection_id: str

class HeartbeatRequest(BaseModel):
    user_id: UUID
    connection_id: str


class PresenceStatusesRequest(BaseModel):
    user_ids: set[UUID] = Field(min_length=1, max_length=500)


class PresenceStatusItem(BaseModel):
    user_id: UUID
    status: PresenceStatus
    last_seen: datetime | None = None


class PresenceStatusesResponse(BaseModel):
    statuses: list[PresenceStatusItem]
