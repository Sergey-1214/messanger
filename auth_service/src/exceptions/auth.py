
from fastapi import status


class AppException(Exception):
    def __init__(self, status_code: int, detail: str, code: str):
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail
        self.code = code


class UserAlreadyExistsException(AppException):
    def __init__(self, username: str, email: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User with email: {email} and username: {username} already exists",
            code="user_already_exists",
        )


class UnauthorizedException(AppException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User unauthorized",
            code="unauthorized",
        )


class UserNotFoundException(AppException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
            code="user_not_found",
        )


class BadRequestException(AppException):
    def __init__(self, detail: str = "Bad Request"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            code="bad_request",
        )


class UserServiceException(AppException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="User service returned an unexpected response",
            code="user_service_error",
        )


class UserServiceUnavailableException(AppException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="User service is unavailable",
            code="user_service_unavailable",
        )
