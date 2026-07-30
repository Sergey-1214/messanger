
from datetime import datetime, timedelta
from unittest.mock import patch

from fastapi import status
import pytest
from sqlalchemy.exc import IntegrityError

from src.exceptions.auth import UnauthorizedException, UserAlreadyExistsException
from src.models.auth import RefreshTokens, User
from src.schemas.auth import LoginRequest, RefreshTokenRequest, RegisterRequest, TokenPair

@pytest.mark.asyncio
class TestAuthService:
    async def test_register_success(self, service, session, repo, user_id):
        request = RegisterRequest(
            username="test user",
            email="testemail@mail.com",
            password="secret123",
        )
        fixed_time = datetime(2025, 1, 1, 12, 0, 0)
        expected_user = User(id=user_id, 
                            username="test user", 
                            email="testemail@mail.com", 
                            created_at=fixed_time
                        )

        repo.register.return_value = expected_user
        
        with patch("src.service.auth.hash_password") as hash_mock:
            hash_mock.return_value = "hashed_secret123"

            result = await service.register(request)

        hash_mock.assert_called_once_with(password="secret123")       

        repo.register.assert_awaited_once_with(
            username="test user",
            email="testemail@mail.com",
            hashed_password="hashed_secret123"
        )

        session.commit.assert_awaited_once()
        session.rollback.assert_not_awaited()

        assert result == expected_user


    async def test_register_conflict(self, service, session, repo):
        repo.register.side_effect = IntegrityError(
            statement="INSERT INTO users ...", 
            params={},                        
            orig=Exception("Duplicate entry") 
        )

        request = RegisterRequest(
            username="test user",
            email="testemail@mail.com",
            password="secret123",
        )

        with patch("src.service.auth.hash_password") as hash_mock:
            hash_mock.return_value = "hash_secret123"
            with pytest.raises(UserAlreadyExistsException) as exc:
                result = await service.register(request)

        expect_detail = f"User with email: testemail@mail.com and username: test user already exsist"
        assert exc.value.detail == expect_detail
        assert exc.value.status_code == status.HTTP_409_CONFLICT

        session.rollback.assert_awaited_once()
        session.commit.assert_not_awaited()

    async def test_login_success(self, service, session, repo, user_id):
        expect_user = User(id=user_id, username="bob", 
                           email="bob@email.com", password_hash="hash123")
        repo.get_user_by_email.return_value = expect_user

        request = LoginRequest(username="bob", 
                           email="bob@email.com", password="123")

        with patch.object(service, "create_token_pair") as mock_create_tokens:
            token_pair = TokenPair(
                access_token="access",
                refresh_token="refresh",
                refresh_token_expires_at=datetime.now()
            )
            mock_create_tokens.return_value = token_pair

            with patch("src.service.auth.verify_password", return_value=True) as verify_mock:
                result = await service.login(request)

        repo.get_user_by_email.assert_awaited_once_with("bob@email.com")
        verify_mock.assert_called_once_with("123", "hash123")

        session.commit.assert_awaited_once()
        session.rollback.assert_not_awaited()

        assert token_pair == result

    async def test_login_user_not_exists(self, service, session, repo):
        request = LoginRequest(
            username="test",
            email="test@email.com",
            password="123"
        )

        repo.get_user_by_email.return_value = None
        with patch("src.service.auth.verify_password") as verify_mock:
            with patch.object(service, "create_token_pair") as create_token_pair_mock:
                with pytest.raises(UnauthorizedException) as exp:
                    result = await service.login(request)

        assert exp.value.detail == "User unauthorized"
        assert exp.value.status_code == status.HTTP_401_UNAUTHORIZED

        repo.get_user_by_email.assert_awaited_once_with("test@email.com")

        verify_mock.assert_not_called()
        create_token_pair_mock.assert_not_awaited()

        
        session.commit.assert_not_awaited()
        session.rollback.assert_not_awaited()

    async def test_login_bad_credential(self, service, session, repo, user_id):
        request = LoginRequest(
            username="test",
            email="test@email.com",
            password="123"
        )

        expect_user = User(
            id=user_id, 
            username="test", 
            email="test@email.com", 
            password_hash="hash123"
        )
        repo.get_user_by_email.return_value = expect_user

        with patch("src.service.auth.verify_password") as verify_mock:
            verify_mock.return_value = False

            with pytest.raises(UnauthorizedException) as exp:
                result = await service.login(request)

        verify_mock.assert_called_once_with("123", "hash123")

        session.commit.assert_not_awaited()
        session.rollback.assert_not_awaited()
        
    async def test_refresh_token_success(self, service, session, repo, user_id):
        request = RefreshTokenRequest(
            refresh_token="refresh"
        )

        expect_token = RefreshTokens(
            refresh_token_hash="hash_refresh", 
            revoked_at=None, 
            expires_at=datetime.now() + timedelta(days=29),
            user_id=user_id
        )

        repo.get_refresh_token.return_value = expect_token
        
        with patch("src.service.auth.hash_refresh_token") as hash_token_mock:
            with patch.object(service, "create_token_pair") as hash_create_token_pair:
                hash_token_mock.return_value = "hash_refresh"
                pair = TokenPair(
                    access_token="access", 
                    refresh_token="refresh", 
                    refresh_token_expires_at=datetime.now() + timedelta(days=30)
                )
                hash_create_token_pair.return_value = pair
                result = await service.refresh_token(request)

        repo.revoked_refresh_token.assert_awaited_once_with(expect_token.refresh_token_hash)
        hash_create_token_pair.assert_awaited_once_with(user_id)
        hash_token_mock.assert_called_once_with("refresh")

        session.commit.assert_awaited_once()
        session.rollback.assert_not_awaited()

        assert result == pair

    async def test_refresh_token_not_exists(self, service, session, repo, user_id):
        request = RefreshTokenRequest(
            refresh_token="refresh"
        )

        repo.get_refresh_token.return_value = None 
        with patch("src.service.auth.hash_refresh_token") as hash_token_mock:
            with patch.object(service, "create_token_pair") as hash_create_token_pair:
                with pytest.raises(UnauthorizedException) as exp:
                    result = await service.refresh_token(request)

        repo.revoked_refresh_token.assert_not_awaited()
        hash_create_token_pair.assert_not_awaited()
        hash_token_mock.assert_called_once_with("refresh")

        session.commit.assert_not_awaited()
        session.rollback.assert_not_awaited()