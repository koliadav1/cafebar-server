import pytest
from fastapi import HTTPException
from sqlalchemy import select

from app.services.order_service import (
    get_order_by_id,
    create_order,
    update_order_status,
    delete_order,
    assign_staff_to_order
)
from app.schemas.order import OrderCreate, OrderItemCreate
from app.models.orders import Order, OrderStatus
from app.models.order_assignments import OrderAssignment, StaffRole


class TestOrderService:
    # Тест создания заказа
    @pytest.mark.asyncio
    async def test_create_order_success(self, test_db, sample_menu_item):
        from app.models.order_items import OrderItem
        order_data = OrderCreate(
            user_id=1,
            table_number=5,
            items=[
                OrderItemCreate(item_id=sample_menu_item.item_id, quantity=2, price=sample_menu_item.price),
            ],
            comment="Без лука"
        )
        
        result = await create_order(order_data, test_db)
        assert result.user_id == 1
        assert result.table_number == 5
        expected_total = sample_menu_item.price * 2
        assert float(result.total_price) == float(expected_total)
        items_result = await test_db.execute(
            select(OrderItem).where(OrderItem.order_id == result.order_id)
        )
        items_result = await test_db.execute(
            select(OrderItem).where(OrderItem.order_id == result.order_id)
        )
        items = items_result.scalars().all()
        assert len(items) == 1

    # Тест создания заказа с несуществующей позицией меню
    @pytest.mark.asyncio
    async def test_create_order_with_nonexistent_item(self, test_db):
        order_data = OrderCreate(
            user_id=1,
            table_number=5,
            items=[OrderItemCreate(item_id=999, quantity=1, price=100.0)],
            comment="Тест"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await create_order(order_data, test_db)
        
        assert exc_info.value.status_code == 404
        assert "Позиция меню 999 не найдена" in str(exc_info.value.detail)

    # Тест получения заказа по ID
    @pytest.mark.asyncio
    async def test_get_order_by_id_success(self, test_db, sample_order):
        result = await get_order_by_id(sample_order.order_id, test_db)
        assert result.order_id == sample_order.order_id
        assert result.user_id == 1

    # Тест получения несуществующего заказа
    @pytest.mark.asyncio
    async def test_get_order_by_id_not_found(self, test_db):
        with pytest.raises(HTTPException) as exc_info:
            await get_order_by_id(999, test_db)
        assert exc_info.value.status_code == 404
        assert "Заказ не найден" in str(exc_info.value.detail)

    # Тест обновления статуса заказа
    @pytest.mark.asyncio
    async def test_update_order_status_success(self, test_db, sample_order):
        result = await update_order_status(sample_order.order_id, OrderStatus.IN_PROGRESS, test_db)
        assert result.status == OrderStatus.IN_PROGRESS

    # Тест удаления заказа
    @pytest.mark.asyncio
    async def test_delete_order_success(self, test_db, sample_order):
        result = await delete_order(sample_order.order_id, test_db)
        assert result == {"detail": "Заказ удалён"}
        
        db_result = await test_db.execute(select(Order).filter(Order.order_id == sample_order.order_id))
        db_order = db_result.scalar_one_or_none()
        assert db_order is None

    # Тест назначения персонала на заказ
    @pytest.mark.asyncio
    async def test_assign_staff_to_order_success(self, test_db, sample_order, sample_active_shift):
        result = await assign_staff_to_order(sample_order.order_id, 2, StaffRole.WAITER, test_db)
        assert result.order_id == sample_order.order_id
        
        db_result = await test_db.execute(select(OrderAssignment).filter(
            OrderAssignment.order_id == sample_order.order_id
        ))
        assignment = db_result.scalar_one_or_none()
        assert assignment is not None

    # Тест повторного назначения персонала на заказ
    @pytest.mark.asyncio
    async def test_assign_staff_to_order_duplicate(self, test_db, sample_active_shift):
        order = Order(user_id=1, table_number=5, total_price=100.0)
        test_db.add(order)
        await test_db.commit()
        
        await assign_staff_to_order(order.order_id, 2, StaffRole.WAITER, test_db)
        
        with pytest.raises(HTTPException) as exc_info:
            await assign_staff_to_order(order.order_id, 2, StaffRole.WAITER, test_db)
        
        assert exc_info.value.status_code == 400
        assert "уже назначен" in str(exc_info.value.detail)