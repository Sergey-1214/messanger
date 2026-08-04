from fastapi import status

from message_service.exception.chat import AppException


class MessageNotFoundException(AppException):
    def __init__(self, detail: str = "Message not found"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
        )
