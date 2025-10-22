from unittest.mock import patch

class TestAuthRouter:
    # Тест успешного логина
    def test_login_success(self, client, sample_user, mock_verify_password):
        login_data = {
            "email": "test@example.com",
            "password": "password123"
        }
        
        response = client.post("/auth/login", json=login_data)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 0

    # Тест неуспешного логина
    def test_login_failure(self, client):
        from fastapi import HTTPException
        
        with patch('app.services.auth_service.login_user', 
                  side_effect=HTTPException(status_code=401, detail="Неверный email или пароль")):
            
            login_data = {
                "email": "test@example.com", 
                "password": "wrongpassword"
            }
            
            response = client.post("/auth/login", json=login_data)
            
            assert response.status_code == 401
            assert "Неверный email или пароль" in response.json()["detail"]