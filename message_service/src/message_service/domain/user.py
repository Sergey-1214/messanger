
from dataclasses import dataclass
from typing import Self

from message_service.models.models import ChatType


@dataclass
class User:
    username: int
    email: str 

    @classmethod
    def from_json(data: dict[str, str]) -> Self:
        return User(
            username = data.get("username"), 
            email = data.get("email")
        )
