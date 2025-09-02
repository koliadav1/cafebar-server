from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from zoneinfo import ZoneInfo
from datetime import datetime, timedelta

from app.database import SessionLocal
from app.models.table_booking import TableBooking, BookingStatus

scheduler = AsyncIOScheduler()

def start_scheduler():
    scheduler.start()

def schedule_booking_updater():
    print("[SCHEDULER] schedule_booking_updater вызван")
    scheduler.add_job(
        update_bookings_status,
        trigger=IntervalTrigger(minutes=1),
        id="update_booking_status",
        name="Auto update booking statuses",
        replace_existing=True,
    )

def update_bookings_status():
    print("[SCHEDULER] update_bookings_status вызван")
    db = SessionLocal()
    try:
        now = datetime.now(ZoneInfo("Asia/Novosibirsk"))

        bookings = db.query(TableBooking).filter(
            TableBooking.status == BookingStatus.CONFIRMED
        ).all()

        for booking in bookings:
            booking_time = booking.booking_time

            if booking_time.tzinfo is None:
                booking_time = booking_time.replace(tzinfo=ZoneInfo("Asia/Novosibirsk"))

            end_time = booking_time + timedelta(minutes=booking.duration_minutes)

            if now >= end_time:
                booking.status = BookingStatus.COMPLETED
                db.add(booking)
        db.commit()
    except Exception as e:
        print(f"[BookingUpdater Error] {e}")
        db.rollback()
    finally:
        db.close()