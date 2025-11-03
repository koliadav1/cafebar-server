FROM python:3.11-slim

WORKDIR /app

# Устанавливаем системные зависимости для Postgres и Redis
RUN apt-get update && apt-get install -y \
    curl \
    postgresql-client \
    redis-tools \
    && rm -rf /var/lib/apt/lists/*

# Копируем и устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код приложения
COPY app/ ./app/
COPY alembic.ini .
COPY *.py ./
COPY scripts/ ./scripts/

# Делаем скрипт исполняемым
RUN chmod +x ./scripts/start.sh

# Создаем обычного пользователя для безопасности
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Указываем где искать Python модули
ENV PYTHONPATH=/app

# Запускаем через скрипт
CMD ["./scripts/start.sh"]