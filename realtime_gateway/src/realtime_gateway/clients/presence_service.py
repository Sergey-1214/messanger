from datetime import datetime
from typing import Literal
from uuid import UUID

import httpx
from pydantic import BaseModel, ValidationError


class PresenceStatusItem(BaseModel):
    user_id: UUID
    status: Literal["online", "offline"]
    last_seen: datetime | None = None


class PresenceStatusesResponse(BaseModel):
    statuses: list[PresenceStatusItem]


class PresenceServiceError(Exception):
    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class PresenceServiceClient:
    def __init__(self, base_url: str, timeout: float = 5.0) -> None:
        self._client = httpx.AsyncClient(
            base_url=base_url.rstrip("/"),
            timeout=timeout,
        )

    async def add_connection(self, user_id: UUID, connection_id: str) -> None:
        await self._request(
            "POST",
            "/presence/connections",
            payload={
                "user_id": str(user_id),
                "connection_id": connection_id,
            },
        )

    async def heartbeat(self, user_id: UUID, connection_id: str) -> None:
        await self._request(
            "POST",
            "/presence/heartbeat",
            payload={
                "user_id": str(user_id),
                "connection_id": connection_id,
            },
        )

    async def disconnect(self, user_id: UUID, connection_id: str) -> None:
        await self._request(
            "DELETE",
            "/presence/disconnect",
            payload={
                "user_id": str(user_id),
                "connection_id": connection_id,
            },
        )

    async def get_statuses(
        self,
        user_ids: set[UUID],
    ) -> PresenceStatusesResponse:
        if not user_ids:
            return PresenceStatusesResponse(statuses=[])

        response = await self._request(
            "POST",
            "/presence/statuses",
            payload={
                "user_ids": sorted(str(user_id) for user_id in user_ids),
            },
        )

        try:
            statuses = PresenceStatusesResponse.model_validate_json(
                response.content
            )
        except ValidationError as error:
            raise PresenceServiceError(
                "Presence service returned an invalid response"
            ) from error

        response_user_ids = [item.user_id for item in statuses.statuses]
        if (
            len(response_user_ids) != len(set(response_user_ids))
            or set(response_user_ids) != user_ids
        ):
            raise PresenceServiceError(
                "Presence service returned an incomplete statuses response"
            )

        return statuses

    async def _request(
        self,
        method: str,
        path: str,
        *,
        payload: dict,
    ) -> httpx.Response:
        try:
            response = await self._client.request(
                method,
                path,
                json=payload,
            )
        except httpx.RequestError as error:
            raise PresenceServiceError("Presence service is unavailable") from error

        if response.is_error:
            raise PresenceServiceError(
                f"Presence service returned HTTP {response.status_code}",
                status_code=response.status_code,
            )

        return response

    async def close(self) -> None:
        await self._client.aclose()
