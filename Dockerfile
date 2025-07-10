# -------- Base image --------
FROM python:3.10-slim

# -------- Environment --------
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# -------- Working dir --------
WORKDIR /app

# -------- System deps --------
RUN apt-get update && apt-get install -y \
        build-essential \
        libglib2.0-0 libsm6 libxrender1 libxext6 \
        poppler-utils \
        tesseract-ocr libtesseract-dev \
        default-libmysqlclient-dev pkg-config \
        libssl-dev libffi-dev \
        default-jre-headless \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# -------- Python deps --------
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# ---- Download the small spaCy model only ----
RUN python -m spacy download en_core_web_sm

# -------- Project code --------
COPY . .

# -------- Collect static (if you use it) --------
RUN python manage.py collectstatic --noinput

# -------- Launch --------
CMD gunicorn resume_analyzer.wsgi:application --bind 0.0.0.0:$PORT
