# ✅ REAL Dockerfile
FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential poppler-utils tesseract-ocr tesseract-ocr-eng \
    libglib2.0-0 libsm6 libxext6 libxrender-dev \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/

ENV PORT=10000
CMD ["gunicorn", "-w", "2", "-k", "gthread", "-b", "0.0.0.0:10000", "app:app"]
