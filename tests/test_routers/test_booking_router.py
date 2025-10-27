import pytest
from datetime import datetime, timedelta
from unittest.mock import patch


class TestBookingRouter:
    # Тест создания бронирования клиентом
    @pytest.mark.asyncio
    async def test_create_booking_as_client(self, authenticated_client, sample_booking_data, sample_booking):
        with patch('app.services.booking_service.create_booking', return_value=sample_booking):
            response = await authenticated_client.post("/bookings/", json=sample_booking_data)
            assert response.status_code == 200
            data = response.json()
            assert "booking_id" in data
            assert data["customer_name"] == sample_booking.customer_name
            assert data["table_number"] == sample_booking.table_number

    # Тест создания бронирования с неавторизованной ролью
    @pytest.mark.asyncio
    async def test_create_booking_unauthorized_role(self, authenticated_client):
        authenticated_client.user.role = "Cook"
        
        booking_data = {
            "table_number": 1,
            "booking_time": (datetime.now() + timedelta(hours=1)).isoformat(),
            "customer_name": "Тестовый Клиент",
            "phone_number": "+79991234567"
        }

        response = await authenticated_client.post("/bookings/", json=booking_data)

        assert response.status_code == 403
        assert "Доступ запрещен" in response.json()["detail"]

    # Тест получения бронирований пользователя
    @pytest.mark.asyncio
    async def test_get_bookings_by_user(self, client, sample_booking):
        response = await client.get(f"/bookings/?user_id={sample_booking.user_id}")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["user_id"] == sample_booking.user_id

    # Тест получения бронирований по статусу
    @pytest.mark.asyncio
    async def test_get_bookings_by_status(self, client, sample_booking):
        response = await client.get(f"/bookings/?status={sample_booking.status.value}")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["status"] == sample_booking.status.value

    # Тест получения брони по ID
    @pytest.mark.asyncio
    async def test_get_booking_by_id(self, client, sample_booking):
        response = await client.get(f"/bookings/{sample_booking.booking_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["booking_id"] == sample_booking.booking_id
        assert data["customer_name"] == sample_booking.customer_name

    # Тест получения несуществующей брони
    @pytest.mark.asyncio
    async def test_get_booking_by_id_not_found(self, client):
        response = await client.get("/bookings/999")

        assert response.status_code == 404
        assert "Бронь не найдена" in response.json()["detail"]

    # Тест обновления бронирования клиентом
    @pytest.mark.asyncio
    async def test_update_booking_as_client(self, authenticated_client, sample_booking):
        with patch('app.services.booking_service.update_booking') as mock_update:
            sample_booking.customer_name = "Обновленное Имя"
            mock_update.return_value = sample_booking
            
            update_data = {"customer_name": "Обновленное Имя"}
            response = await authenticated_client.put(f"/bookings/{sample_booking.booking_id}", json=update_data)
            assert response.status_code == 200
            data = response.json()
            assert data["customer_name"] == "Обновленное Имя"

    # Тест удаления бронирования админом
    @pytest.mark.asyncio
    async def test_delete_booking_as_admin(self, admin_client, sample_booking):
        with patch('app.services.booking_service.delete_booking', return_value=True):
            response = await admin_client.delete(f"/bookings/{sample_booking.booking_id}")
            assert response.status_code == 200
            assert response.json()["detail"] == "Бронь удалена"