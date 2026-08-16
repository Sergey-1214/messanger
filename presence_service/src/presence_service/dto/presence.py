
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AddConnectionResult:
    status_changed: bool
    active_connections: int
