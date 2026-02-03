FROM python:3.11-slim

WORKDIR /app

# Установка системных зависимостей для ffmpeg и обработки изображений
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libimage-exiftool-perl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./app /app/app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
