
from fastapi import status

class UserException(Exception):
    def __init__(self, status_code: str, detail: str):
        self.status_code = status_code
        self.detail = detail


class UserAlreadyExistException(UserException):
    def __init__(self, detail: str):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)


class UserNotFoundException(UserException):
    def __init__(self, detail):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)