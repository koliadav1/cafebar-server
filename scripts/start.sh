#!/bin/bash

# Ждем
echo "Waiting for PostgreSQL..."
until pg_isready -h postgres -p 5432 -U $DB_USER; do
    echo "PostgreSQL is unavailable - sleeping"
    sleep 2
done
echo "PostgreSQL is ready!"

echo "Waiting for Redis..."
until redis-cli -h redis -p 6379 ping | grep -q "PONG"; do
    echo "Redis is unavailable - sleeping"
    sleep 2
done
echo "Redis is ready!"

# Применяем миграции
echo "Running database migrations..."
alembic upgrade head

# Запускаем приложение
echo "Starting application..."
uvicorn app.main:app --host 0.0.0.0 --port 8000