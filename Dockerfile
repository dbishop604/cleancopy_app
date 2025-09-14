# Base Python image
FROM python:3.11-slim

# Install system dependencies for OCR & PDF conversion
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    poppler-utils \
    ghostscript \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Default to running the web app
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:10000", "--workers=2", "--threads=2", "--timeout=120"]
