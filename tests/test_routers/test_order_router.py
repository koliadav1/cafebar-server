import pytest
from unittest.mock import patch

class TestOrderRouter:
    # Тест получения заказов для клиента
    @pytest.mark.asyncio
    async def test_get_orders_as_client(self, authenticated_client):
        authenticated_client.user.role = "Client"
        with patch('app.services.order_service.get_orders_by_user', return_value=[]):
            response = await authenticated_client.get("/orders/")
            assert response.status_code == 200
            assert isinstance(response.json(), list)

    # Тест получения заказов для персонала
    @pytest.mark.asyncio
    async def test_get_orders_as_staff(self, authenticated_client):
        authenticated_client.user.role = "Waiter"
        with patch('app.services.order_service.get_all_orders', return_value=[]):
            response = await authenticated_client.get("/orders/")
            assert response.status_code == 200
            assert isinstance(response.json(), list)

    # Тест получения заказа по ID для персонала
    @pytest.mark.asyncio
    async def test_get_order_by_id_as_staff(self, admin_client, sample_order):
        sample_order.items = []
        with patch('app.services.order_service.get_order_by_id', return_value=sample_order):
            response = await admin_client.get(f"/orders/{sample_order.order_id}")
            assert response.status_code == 200
            data = response.json()
            assert data["order_id"] == sample_order.order_id
            assert data["table_number"] == sample_order.table_number

    # Тест запрета получения заказа по ID для клиента
    @pytest.mark.asyncio
    async def test_get_order_by_id_as_client_denied(self, authenticated_client):
        authenticated_client.user.role = "Client"
        response = await authenticated_client.get("/orders/1")
        assert response.status_code == 403
        assert "Доступ запрещен" in response.json()["detail"]

    # Тест создания заказа клиентом
    @pytest.mark.asyncio
    async def test_create_order_as_client(self, authenticated_client, sample_order_data, sample_order):
        with patch('app.services.order_service.create_order', return_value=sample_order):
            response = await authenticated_client.post("/orders/", json=sample_order_data)
            assert response.status_code == 200

    # Тест создания заказа официантом
    @pytest.mark.asyncio
    async def test_create_order_as_waiter(self, authenticated_client, sample_order_data, sample_order):
        authenticated_client.user.role = "Waiter"
        with patch('app.services.order_service.create_order', return_value=sample_order):
            response = await authenticated_client.post("/orders/", json=sample_order_data)
            assert response.status_code == 200

    # Тест запрета создания заказа для неавторизованных ролей
    @pytest.mark.asyncio
    async def test_create_order_denied(self, authenticated_client, sample_order_data):
        authenticated_client.user.role = "Cook"
        response = await authenticated_client.post("/orders/", json=sample_order_data)
        assert response.status_code == 403

    # Тест обновления статуса заказа клиентом
    @pytest.mark.asyncio
    async def test_update_order_status_as_client(self, authenticated_client, sample_order):
        with patch('app.services.order_service.get_order_by_id', return_value=sample_order), \
            patch('app.services.order_service.update_order_status', return_value=sample_order):
            response = await authenticated_client.patch("/orders/1/status?status=Cancelled")
            assert response.status_code == 200

    # Тест самоназначения на заказ
    @pytest.mark.asyncio
    async def test_assign_self_to_order(self, authenticated_client, sample_order):
        authenticated_client.user.role = "Waiter"
        with patch('app.services.order_service.get_order_by_id', return_value=sample_order), \
            patch('app.services.order_service.assign_staff_to_order', return_value=sample_order):
            
            response = await authenticated_client.patch("/orders/1/assign")
            assert response.status_code == 200