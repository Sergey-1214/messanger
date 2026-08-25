
from dataclasses import dataclass
from enum import Enum, IntEnum


@dataclass(frozen=True, slots=True)
class AddConnectionResult:
    status_changed: bool
    active_connections: int
    version: int


class HeartbeatResult(IntEnum):
    CONNECTION_NOT_FOUND = 0
    OK = 1