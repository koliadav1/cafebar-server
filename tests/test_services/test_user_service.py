import pytest
from unittest.mock import patch
from fastapi import HTTPException
from sqlalchemy import select

from app.services.user_service import (
    get_user_by_id, 
    create_user,
    delete_user,
    update_user_password,
    update_user_data
)
from app.schemas.user import UserCreate, UserPasswordUpdate, UserUpdate
from app.models.user import User, UserRole


class TestUserService:
    # Тест создания пользователя
    @pytest.mark.asyncio
    async def test_create_user_success(self, test_db, sample_user_data, mock_password_hash):
        user_data = UserCreate(**sample_user_data)
        
        result = await create_user(user_data, test_db)
        
        assert result.username == "testuser"
        assert result.email == "test@example.com"
        assert result.phone_number == "+79991234567"
        assert result.role == UserRole.CLIENT
        assert result.password_hash == "hashed_password"
        
        db_result = await test_db.execute(select(User).filter(User.user_id == result.user_id))
        db_user = db_result.scalar_one_or_none()
        assert db_user is not None
        assert db_user.username == "testuser"

    # Тест создания пользователя с существующим email
    @pytest.mark.asyncio
    async def test_create_user_duplicate_email(self, test_db, sample_user_data, mock_password_hash):
        user_data = UserCreate(**sample_user_data)
        await create_user(user_data, test_db)

        with pytest.raises(HTTPException) as exc_info:
            await create_user(user_data, test_db)
        
        assert exc_info.value.status_code == 400
        assert "уже существует" in str(exc_info.value.detail)

    # Тест получения пользователя по ID
    @pytest.mark.asyncio
    async def test_get_user_by_id_success(self, test_db, sample_user):
        result = await get_user_by_id(sample_user.user_id, test_db)
        assert result.user_id == sample_user.user_id
        assert result.username == "testuser"

    # Тест получения несуществующего пользователя
    @pytest.mark.asyncio
    async def test_get_user_by_id_not_found(self, test_db):
        with pytest.raises(HTTPException) as exc_info:
            await get_user_by_id(999, test_db)
        assert exc_info.value.status_code == 404
        assert "Пользователь не найден" in str(exc_info.value.detail)

    # Тест удаления пользователя
    @pytest.mark.asyncio
    async def test_delete_user_success(self, test_db, sample_user):
        result = await delete_user(sample_user.user_id, test_db)
        assert result == {"detail": "Пользователь успешно удалён"}
        
        db_result = await test_db.execute(select(User).filter(User.user_id == sample_user.user_id))
        db_user = db_result.scalar_one_or_none()
        assert db_user is None

    # Тест обновления пароля пользователя
    @pytest.mark.asyncio
    async def test_update_user_password_success(self, test_db, sample_user):
        password_data = UserPasswordUpdate(
            old_password="securepassword123", 
            new_password="newsecurepassword456"
        )

        with patch('app.services.user_service.verify_password', return_value=True), \
            patch('app.services.user_service.pwd_context.hash') as mock_hash:
            mock_hash.return_value = "new_hashed_password"
            
            result = await update_user_password(sample_user.user_id, password_data, test_db)
            assert result.user_id == sample_user.user_id
            assert result.password_hash == "new_hashed_password"

    # Тест обновления данных пользователя
    @pytest.mark.asyncio
    async def test_update_user_data_success(self, test_db, sample_user):
        update_data = UserUpdate(
            email="newemail@example.com",
            phone_number="+79997654321",
            username="newusername"
        )
        
        result = await update_user_data(sample_user.user_id, update_data, test_db)
        assert result.email == "newemail@example.com"
        assert result.phone_number == "+79997654321"
        assert result.username == "newusername"