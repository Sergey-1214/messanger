
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel


class PresenceStatus(StrEnum):
    ONLINE = "online"
    OFFLINE = "offline"


class AddConnectionRequest(BaseModel):
    user_id: UUID
    connection_id: UUID


class DisconnectRequest(BaseModel):
    user_id: UUID 
    connection_id: UUID