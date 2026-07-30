
from fastapi import status

class AppException(Exception):
    def __init__(self, status_code: str, detail: str):
        self.status_code=status_code
        self.detail = detail
        

class UserAlreadyExistsException(AppException):
    def __init__(self, username: str, email: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User with email: {email} and username: {username} already exsist"
        )

class UnauthorizedException(AppException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"User unauthorized"
        )

class UserNotFoundException(AppException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

class BadRequestException(AppException):
    def __init__(self, detail: str = "Bad Request"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )