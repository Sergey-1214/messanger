from fastapi import status


class AppException(Exception):
    def __init__(self, status_code: str, detail: str):
        self.status_code= status_code
        self.detail= detail


class UnauthorizedException(AppException):
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail=detail,
        )


class BadRequestException(AppException):
    def __init__(self, detail):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=detail,
        )

class ForbiddenException(AppException):
    def __init__(self, detail):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail=detail
        )

class ChatNotFoundException(AppException):
    def __init__(self, detail: str = "Chat not found"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail
        )


class ChatAlreadyExistException(AppException):
    def __init__(self, detail: str):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_409_CONFLICT,
        )