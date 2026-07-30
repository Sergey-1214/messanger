from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from src.repository.auth import AuthRepository
from src.service.auth import AuthService 



@pytest.fixture
def session():
    return AsyncMock()
    
@pytest.fixture 
def repo():
    return AsyncMock(spec=AuthRepository)

@pytest.fixture 
def service(session, repo):
    return AuthService(session=session, repo=repo)

@pytest.fixture 
def user_id():
    return uuid4()

