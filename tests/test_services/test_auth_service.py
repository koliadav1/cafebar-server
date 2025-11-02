import pytest
from unittest.mock import patch
from fastapi import HTTPException

from app.services.auth_service import login_user, create_access_token, get_current_user, verify_password
from app.schemas.auth import LoginRequest


class TestAuthService:
    # Тест успешной проверки пароля
    def test_verify_password_success(self):
        with patch('app.services.auth_service.pwd_context.verify', return_value=True):
            result = verify_password("password123", "hashed_password")
            assert result is True

    # Тест успешного логина
    @pytest.mark.asyncio
    async def test_login_user_success(self, test_db, sample_user, mock_verify_password):
        login_data = LoginRequest(email="test@example.com", password="password123")
        result = await login_user(login_data, test_db)
        assert result.email == "test@example.com"
        assert result.username == "testuser"

    # Тест логина с неправильным паролем
    @pytest.mark.asyncio
    async def test_login_user_wrong_password(self, test_db):
        login_data = LoginRequest(email="test@example.com", password="wrongpassword")
        with patch('app.services.auth_service.verify_password', return_value=False):
            with pytest.raises(HTTPException) as exc_info:
                await login_user(login_data, test_db)
            assert exc_info.value.status_code == 401

    # Тест логина несуществующего пользователя
    @pytest.mark.asyncio
    async def test_login_user_not_found(self, test_db):
        login_data = LoginRequest(email="nonexistent@example.com", password="password")
        with pytest.raises(HTTPException) as exc_info:
            await login_user(login_data, test_db)
        
        assert exc_info.value.status_code == 401
        assert "Неверный email или пароль" in str(exc_info.value.detail)

    # Тест создания JWT токена
    def test_create_access_token(self, mock_token_config):
        data = {"user_id": 1, "role": "Client"}
        token = create_access_token(data)
        assert isinstance(token, str)
        assert len(token) > 0

    # Тест получения текущего пользователя по токену
    @pytest.mark.asyncio
    async def test_get_current_user_success(self, test_db, sample_user):
        token = create_access_token({"user_id": sample_user.user_id})
        result = await get_current_user(token=token, db=test_db)
        assert result.user_id == sample_user.user_id
        assert result.username == "testuser"

    # Тест получения пользователя с невалидным токеном
    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self, test_db):
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token="invalid_token", db=test_db)
        
        assert exc_info.value.status_code == 401

    # Тест получения несуществующего пользователя по токену
    @pytest.mark.asyncio
    async def test_get_current_user_not_found(self, test_db):
        token = create_access_token({"user_id": 999})
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token=token, db=test_db)
        assert exc_info.value.status_code == 401