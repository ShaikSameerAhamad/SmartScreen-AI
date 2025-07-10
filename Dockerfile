# ---- Base image ----
FROM python:3.10-slim

# ---- Environment variables ----
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# ---- Set working directory ----
WORKDIR /app

# ---- Install system dependencies ----
RUN apt-get update && apt-get install -y \
    build-essential \
    libglib2.0-0 \
    libsm6 \
    libxrender1 \
    libxext6 \
    poppler-utils \
    tesseract-ocr \
    libtesseract-dev \
    default-libmysqlclient-dev \
    pkg-config \
    libssl-dev \
    libffi-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# ---- Install Python dependencies ----
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# ---- Copy project files ----
COPY . .

# ---- Collect static files ----
RUN python manage.py collectstatic --noinput

# ---- Run application ----
CMD gunicorn resume_analyzer.wsgi:application --bind 0.0.0.0:$PORT
