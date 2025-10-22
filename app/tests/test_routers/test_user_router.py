from unittest.mock import Mock, patch

class TestUserRouter:
    # Тест получения списка пользователей с правами админа
    def test_get_users_as_admin(self, admin_client):
        with patch('app.services.user_service.get_all_users', return_value=[]):
            response = admin_client.get("/users/")
            assert response.status_code == 200
            assert isinstance(response.json(), list)

    # Тест получения списка пользователей без прав админа
    def test_get_users_as_non_admin(self, authenticated_client):
        response = authenticated_client.get("/users/")
        assert response.status_code == 403
        assert "Доступ запрещен" in response.json()["detail"]

    # Тест получения данных текущего пользователя
    def test_get_my_user_data(self, authenticated_client):
        with patch('app.services.user_service.get_user_by_id', return_value=authenticated_client.user):
            response = authenticated_client.get("/users/me")
            assert response.status_code == 200
            data = response.json()
            assert data["user_id"] == authenticated_client.user.user_id
            assert data["username"] == "testuser"

    # Тест создания пользователя
    def test_create_user_success(self, client, sample_user_data, sample_user):
        with patch('app.services.user_service.pwd_context.hash', return_value="hashed_password"), \
            patch('app.services.user_service.create_user', return_value=sample_user):
            
            response = client.post("/users/", json=sample_user_data)
            assert response.status_code == 201
            data = response.json()
            assert data["username"] == sample_user_data["username"]
            assert "password" not in data

    # Тест удаления собственного аккаунта
    def test_delete_own_account(self, authenticated_client):
        with patch('app.services.user_service.delete_user', return_value={"detail": "Пользователь успешно удалён"}):
            response = authenticated_client.delete("/users/me")
            assert response.status_code == 204

    # Тест удаления пользователя админом
    def test_delete_user_as_admin(self, admin_client, test_db):
        with patch('app.services.user_service.delete_user', return_value={"detail": "Пользователь успешно удалён"}):
            response = admin_client.delete("/users/1")
            assert response.status_code == 204

    # Тест удаления пользователя без прав админа
    def test_delete_user_as_non_admin(self, authenticated_client):
        response = authenticated_client.delete("/users/1")
        assert response.status_code == 403
        assert "Доступ запрещен" in response.json()["detail"]

    # Тест получения пользователей по роли с правами админа
    def test_get_users_by_role_as_admin(self, admin_client):
        with patch('app.services.user_service.get_users_by_role', return_value=[]):
            response = admin_client.get("/users/role/Client")
            assert response.status_code == 200
            assert isinstance(response.json(), list)

    # Тест изменения пароля
    def test_change_password(self, authenticated_client, sample_user):
        password_data = {
            "old_password": "oldpass",
            "new_password": "newpass"
        }
        
        with patch('app.services.user_service.update_user_password', return_value=sample_user):
            response = authenticated_client.put("/users/me/password", json=password_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["user_id"] == sample_user.user_id

    # Тест обновления данных пользователя
    def test_update_user_data(self, authenticated_client, sample_user):
        sample_user.email = "newemail@example.com"
        sample_user.phone_number = "+79997654321"
        sample_user.username = "newusername"

        update_data = {
            "email": "newemail@example.com",
            "phone_number": "+79997654321", 
            "username": "newusername"
        }
        
        with patch('app.services.user_service.update_user_data', return_value=sample_user):
            response = authenticated_client.put("/users/me", json=update_data)
            assert response.status_code == 200
            data = response.json()
            assert data["email"] == "newemail@example.com"