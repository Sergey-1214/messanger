
from dataclasses import dataclass
from typing import Self
from uuid import UUID


@dataclass
class User:
    user_id: UUID
    username: str

    @classmethod
    def from_json(cls, data: dict) -> Self:
        return cls(
            user_id=UUID(str(data.get("id", data.get("user_id")))),
            username=data["username"],
        )
