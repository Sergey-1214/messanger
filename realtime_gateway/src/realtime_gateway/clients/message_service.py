from datetime import datetime
from uuid import UUID

import httpx
from pydantic import BaseModel, ConfigDict, ValidationError


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


class MessageServiceError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class MessageServiceClient:
    def __init__(self, base_url: str, timeout: float = 5.0) -> None:
        self._client = httpx.AsyncClient(
            base_url=base_url.rstrip("/"),
            timeout=timeout,
        )

    async def create_message(
        self,
        *,
        user_id: UUID,
        chat_id: int,
        content: str,
        request_id: UUID,
    ) -> MessageResponse:
        try:
            response = await self._client.post(
                f"/messages/{chat_id}",
                json={"content": content},
                headers={
                    "User-Id": str(user_id),
                    "X-Request-Id": str(request_id),
                },
            )
        except httpx.RequestError as error:
            raise MessageServiceError(
                code="message_service_unavailable",
                message="Message service is unavailable",
            ) from error

        if response.is_error:
            try:
                response_body = response.json()
            except ValueError:
                response_body = {}

            detail = response_body.get("detail")
            message = detail if isinstance(detail, str) else "Message service error"
            raise MessageServiceError(
                code=f"message_service_{response.status_code}",
                message=message,
            )

        try:
            return MessageResponse.model_validate(response.json())
        except (ValueError, ValidationError) as error:
            raise MessageServiceError(
                code="invalid_message_service_response",
                message="Message service returned an invalid response",
            ) from error

    async def close(self) -> None:
        await self._client.aclose()
