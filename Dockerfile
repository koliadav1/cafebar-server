FROM python:3.11-slim

WORKDIR /app

# Копируем и устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем только нужный код
COPY app/ ./app/
COPY *.py ./

# Создаем обычного пользователя для безопасности
RUN useradd -m -u 1000 appuser
USER appuser

# Указываем где искать Python модули
ENV PYTHONPATH=/app

# Запускаем сервер
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]