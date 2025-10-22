from app.services.booking_service import (
    create_booking,
    get_booking_by_id,
    get_all_bookings,
    get_bookings_by_user,
    get_bookings_by_status,
    update_booking,
    delete_booking
)
from app.schemas.booking import TableBookingUpdate
from app.models.table_booking import TableBooking, BookingStatus


class TestBookingService:
    # Тест создания бронирования
    def test_create_booking_success(self, test_db, sample_booking_data):
        from app.schemas.booking import TableBookingCreate
        booking_data = TableBookingCreate(**sample_booking_data)
        
        result = create_booking(test_db, booking_data)
        assert result.table_number == 1
        assert result.customer_name == "Тестовый Клиент"

        db_booking = test_db.query(TableBooking).filter(TableBooking.booking_id == result.booking_id).first()
        assert db_booking is not None

    # Тест получения брони по ID
    def test_get_booking_by_id_success(self, test_db, sample_booking):
        result = get_booking_by_id(test_db, sample_booking.booking_id)
        assert result.booking_id == sample_booking.booking_id
        assert result.customer_name == "Тестовый Клиент"

    # Тест получения несуществующей брони
    def test_get_booking_by_id_not_found(self, test_db):
        result = get_booking_by_id(test_db, 999)
        assert result is None

    # Тест получения всех бронирований
    def test_get_all_bookings(self, test_db, sample_booking):
        result = get_all_bookings(test_db)
        assert len(result) >= 1
        assert any(booking.booking_id == sample_booking.booking_id for booking in result)

    # Тест получения бронирований пользователя
    def test_get_bookings_by_user(self, test_db, sample_booking):
        result = get_bookings_by_user(test_db, sample_booking.user_id)
        assert len(result) == 1
        assert result[0].user_id == sample_booking.user_id

    # Тест получения бронирований по статусу
    def test_get_bookings_by_status(self, test_db, sample_booking):
        result = get_bookings_by_status(test_db, BookingStatus.CONFIRMED)
        assert len(result) >= 1
        assert result[0].status == BookingStatus.CONFIRMED
        assert result[0].booking_id == sample_booking.booking_id

    # Тест обновления бронирования
    def test_update_booking_success(self, test_db, sample_booking):
        update_data = TableBookingUpdate(
            customer_name="Обновленное Имя",
            phone_number="+79998887766"
        )

        result = update_booking(test_db, sample_booking.booking_id, update_data)
        assert result.customer_name == "Обновленное Имя"
        assert result.phone_number == "+79998887766"

    # Тест обновления несуществующей брони
    def test_update_booking_not_found(self, test_db):
        update_data = TableBookingUpdate(customer_name="Новое Имя")
        result = update_booking(test_db, 999, update_data)
        assert result is None

    # Тест удаления бронирования
    def test_delete_booking_success(self, test_db, sample_booking):
        result = delete_booking(test_db, sample_booking.booking_id)
        assert result is True
        db_booking = test_db.query(TableBooking).filter(TableBooking.booking_id == sample_booking.booking_id).first()
        assert db_booking is None

    # Тест удаления несуществующей брони
    def test_delete_booking_not_found(self, test_db):
        result = delete_booking(test_db, 999)
        assert result is False