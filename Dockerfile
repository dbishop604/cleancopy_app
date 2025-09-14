FROM python:3.11.9-slim

ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies for OCR + PDF handling
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    libtesseract-dev \
    poppler-utils \
    ghostscript \
    gcc \
    g++ \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy all app code
COPY . /app/

# Expose port (Render sets $PORT automatically)
EXPOSE 10000

# Use shell form to expand $PORT at runtime
CMD exec gunicorn app:app --bind 0.0.0.0:$PORT --workers=2 --threads=2 --timeout=120
