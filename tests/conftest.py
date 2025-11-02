import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch
from httpx._transports.asgi import ASGITransport
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool

from tests.mock_scheduler import scheduler, start_scheduler, schedule_booking_updater, update_bookings_status

import os
os.environ["TESTING"] = "1"

with patch('app.config.Config.DATABASE_URL', 'sqlite+aiosqlite:///:memory:'):
    with patch('app.database.engine') as mock_engine:
        from tests.mock_scheduler import scheduler, start_scheduler, schedule_booking_updater, update_bookings_status
        
        with patch('app.scheduler.scheduler.scheduler', scheduler):
            with patch('app.scheduler.scheduler.start_scheduler', start_scheduler):
                with patch('app.scheduler.scheduler.schedule_booking_updater', schedule_booking_updater):
                    with patch('app.scheduler.scheduler.update_bookings_status', update_bookings_status):
                        from app.main import app
                        from app.database import get_db, Base

# Асинхронная фикстура для тестовой базы данных
@pytest_asyncio.fixture(scope="function")
async def test_db():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    AsyncTestingSessionLocal = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async def override_get_db():
        async with AsyncTestingSessionLocal() as session:
            try:
                yield session
            finally:
                await session.close()
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncTestingSessionLocal() as session:
        yield session
    
    app.dependency_overrides.clear()
    await engine.dispose()

# Асинхронная фикстура для тестового клиента
@pytest_asyncio.fixture(scope="function")
async def client(test_db):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client

# Тестовые данные для позиции меню
@pytest.fixture
def sample_menu_item_data():
    from app.models.menu_items import MenuCategory
    return {
        "name": "Тестовое блюдо",
        "description": "Тестовое описание", 
        "price": 300.00,
        "category": MenuCategory.MAIN.value,
        "is_available": True
    }

# Тестовые данные для ингредиента
@pytest.fixture
def sample_ingredient_data():
    """Тестовые данные для создания ингредиента"""
    return {
        "ingredient": {
            "name": "Новый ингредиент",
            "unit": "кг",
            "quantity": 5.0,
            "threshold": 1.0
        },
        "required_quantity": 0.5
    }

# Тестовые данные для заказа
@pytest.fixture
def sample_order_data():
    return {
        "user_id": 1,
        "table_number": 5,
        "items": [
            {"item_id": 1, "quantity": 2, "price": 150.50},
            {"item_id": 2, "quantity": 1, "price": 200.00}
        ],
        "comment": "Тестовый комментарий"
    }

# Тестовые данные для брони
@pytest.fixture
def sample_booking_data():
    from datetime import datetime, timedelta
    return {
        "table_number": 1,
        "booking_time": (datetime.now() + timedelta(hours=1)).isoformat(),
        "customer_name": "Тестовый Клиент",
        "phone_number": "+79991234567",
        "user_id": 1,
        "status": "Confirmed",
        "duration_minutes": 120
    }

# Тестовые данные для пользователя
@pytest.fixture
def sample_user_data():
    from app.models.user import UserRole
    return {
        "username": "testuser",
        "email": "test@example.com", 
        "phone_number": "+79991234567",
        "password": "shortpass",
        "role": UserRole.CLIENT.value
    }

# Тестовые данные для отзыва
@pytest.fixture
def sample_review_data():
    return {
        "order_id": 1,
        "rating": 5,
        "comment": "Отличный сервис"
    }

# Асинхронная фабрика для создания аутентифицированных пользователей
@pytest_asyncio.fixture
async def create_authenticated_client(client, test_db):
    from app.models.user import UserRole
    async def _create_client(role=UserRole.CLIENT, **user_kwargs):
        from app.models.user import User
        from app.services.auth_service import get_current_user
        
        user_data = {
            "user_id": 1 if role == UserRole.CLIENT else 2,
            "username": "testuser" if role == UserRole.CLIENT else "admin",
            "email": "test@example.com" if role == UserRole.CLIENT else "admin@example.com",
            "password_hash": "hashed_password",
            "role": role,
            "phone_number": "+79991234567" if role == UserRole.CLIENT else "+79998887766"
        }
        user_data.update(user_kwargs)
        
        user = User(**user_data)
        test_db.add(user)
        await test_db.commit()
        await test_db.refresh(user)
        
        async def mock_get_current_user():
            return user
        
        app.dependency_overrides[get_current_user] = mock_get_current_user
        client.user = user
        return client
    
    yield _create_client
    app.dependency_overrides.clear()

# Фикстура для создания аутентифицированного клиента
@pytest_asyncio.fixture
async def authenticated_client(create_authenticated_client):
    from app.models.user import UserRole
    return await create_authenticated_client(role=UserRole.CLIENT)

# Фикстура для создания аутентифицированного админа
@pytest_asyncio.fixture
async def admin_client(create_authenticated_client):
    from app.models.user import UserRole
    return await create_authenticated_client(role=UserRole.ADMIN)

# Асинхронная фикстура для тестовой позиции меню
@pytest_asyncio.fixture
async def sample_menu_item(test_db):
    from app.models.menu_items import MenuItem, MenuCategory, MenuItemImage
    
    item = MenuItem(
        name="Тестовое блюдо",
        description="Тестовое описание",
        price=300.00,
        category=MenuCategory.MAIN,
        is_available=True
    )
    test_db.add(item)
    await test_db.commit()
    await test_db.refresh(item)

    image1 = MenuItemImage(item_id=item.item_id, image_url="http://test.com/test.jpg")
    image2 = MenuItemImage(item_id=item.item_id, image_url="http://test.com/image.jpg")
    test_db.add_all([image1, image2])
    await test_db.commit()

    result = await test_db.execute(
        select(MenuItem)
        .options(selectinload(MenuItem.images))
        .where(MenuItem.item_id == item.item_id)
    )
    item_with_relations = result.scalar_one()

    item_with_relations.image_urls = [img.image_url for img in item_with_relations.images]
    
    return item_with_relations

# Асинхронная фикстура для тестового заказа
@pytest_asyncio.fixture
async def sample_order(test_db):
    from app.models.orders import Order, OrderStatus
    from datetime import datetime
    
    order = Order(
        user_id=1,
        table_number=5,
        total_price=100.0,
        status=OrderStatus.PENDING,
        order_date=datetime.now(),
        comment=None
    )
    test_db.add(order)
    await test_db.commit()
    await test_db.refresh(order)

    result = await test_db.execute(
        select(Order)
        .options(
            selectinload(Order.items),
            selectinload(Order.assignments)
        )
        .where(Order.order_id == order.order_id)
    )
    order_with_relations = result.scalar_one()
    
    return order_with_relations

# Асинхронная фикстура для тестовой активной смены
@pytest_asyncio.fixture
async def sample_active_shift(test_db):
    from app.models.staff_shifts import StaffShift
    from datetime import datetime, date, timedelta
    
    now = datetime.now()
    shift_start = (now - timedelta(hours=1)).time()
    shift_end = (now + timedelta(hours=1)).time()
    
    shift = StaffShift(
        user_id=2,
        shift_date=date.today(),
        shift_start=shift_start,
        shift_end=shift_end
    )
    test_db.add(shift)
    await test_db.commit()
    await test_db.refresh(shift)
    return shift

# Асинхронная фикстура для тестового бронирования
@pytest_asyncio.fixture
async def sample_booking(test_db):
    from app.models.table_booking import TableBooking, BookingStatus
    from datetime import datetime, timedelta
    
    booking = TableBooking(
        booking_id=1,
        table_number=1,
        booking_time=datetime.now() + timedelta(hours=1),
        customer_name="Тестовый Клиент",
        phone_number="+79991234567",
        user_id=1,
        status=BookingStatus.CONFIRMED,
        duration_minutes=120
    )
    test_db.add(booking)
    await test_db.commit()
    await test_db.refresh(booking)
    return booking

# Асинхронная фикстура для тестового отзыва
@pytest_asyncio.fixture
async def sample_review(test_db, sample_order):
    from app.models.reviews import Review
    from datetime import datetime
    
    review = Review(
        user_id=1,
        order_id=sample_order.order_id,
        rating=5,
        comment="Тестовый отзыв",
        review_date=datetime.now()
    )
    test_db.add(review)
    await test_db.commit()
    await test_db.refresh(review)
    return review

# Асинхронная фикстура для тестового ингредиента
@pytest_asyncio.fixture
async def sample_ingredient(test_db):
    from app.models.ingredients import Ingredient
    from decimal import Decimal
    
    ingredient = Ingredient(
        name="Тестовый ингредиент",
        unit="г",
        quantity=Decimal("1000.0"),
        threshold=Decimal("100.0")
    )
    test_db.add(ingredient)
    await test_db.commit()
    await test_db.refresh(ingredient)
    return ingredient

# Асинхронная фикстура для тестового пользователя в БД
@pytest_asyncio.fixture
async def sample_user(test_db):
    from app.models.user import User, UserRole
    
    user = User(
        username="testuser",
        email="test@example.com",
        password_hash="hashed_password",
        role=UserRole.CLIENT,
        phone_number="+79991234567"
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    return user

# Фикстура для мока WebSocket менеджера
@pytest.fixture
def mock_websocket_manager():
    with patch('app.realtime.websocket_manager.manager') as mock:
        mock.broadcast = AsyncMock()
        yield mock

# Фикстура для автоматического мока WebSocket broadcast во всех роутерах
@pytest.fixture
def mock_websocket_broadcast(mock_websocket_manager):
    with patch('app.routers.booking.manager.broadcast', mock_websocket_manager.broadcast), \
         patch('app.routers.menu.manager.broadcast', mock_websocket_manager.broadcast):
        yield

# Фикстура для мока хеширования пароля
@pytest.fixture
def mock_password_hash():
    with patch('app.services.user_service.pwd_context.hash', return_value="hashed_password") as mock:
        yield mock

# Фикстура для мока проверки пароля
@pytest.fixture
def mock_verify_password():
    with patch('app.services.auth_service.verify_password', return_value=True) as mock:
        yield mock

# Фикстура для мока конфига токенов
@pytest.fixture
def mock_token_config():
    with patch('app.config.Config.HASH_SECRET_KEY', 'test_secret'), \
         patch('app.config.Config.ALGORITHM', 'HS256'), \
         patch('app.config.Config.ACCESS_TOKEN_EXPIRE_MINUTES', 30):
        yield