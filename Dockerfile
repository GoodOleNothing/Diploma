# Используем официальный Python образ
FROM python:3.11-slim

# Рабочая директория
WORKDIR /app

# Переменные окружения
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Установка зависимостей
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Копирование проекта
COPY . .

# Команда по умолчанию
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]