from unittest.mock import MagicMock

scheduler = MagicMock()
scheduler.running = False
scheduler.start = MagicMock()
scheduler.shutdown = MagicMock()
scheduler.add_job = MagicMock()

# Мок функции start_scheduler
def start_scheduler():
    scheduler.start()

# Мок функции schedule_booking_updater
def schedule_booking_updater():
    scheduler.add_job()