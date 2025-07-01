# Используем Python 3.11 как базовый образ
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    wget \
    gnupg \
    curl \
    unzip \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем Node.js для компиляции TypeScript
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs

# Копируем и устанавливаем зависимости Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем фронтенд и компилируем TypeScript
COPY frontend/ /app/frontend/
WORKDIR /app/frontend
RUN npm install
RUN npm run build

# Возвращаемся в основную директорию
WORKDIR /app

# Копируем backend код
COPY backend/ /app/

# Устанавливаем Playwright браузеры
RUN python -m playwright install chromium
RUN python -m playwright install-deps

# Создаем директории для медиа и статических файлов
RUN mkdir -p /app/media /app/staticfiles

# Открываем порт (только внутри контейнера)
EXPOSE 8000

# Команда для запуска приложения
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"] 