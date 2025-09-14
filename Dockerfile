# Use official lightweight Python image
FROM python:3.11-slim

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

# Set working directory
WORKDIR /app

# Copy dependencies first for better caching
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . /app/

# Expose port for Render
ENV PORT=10000

# Start command for Render
CMD ["gunicorn", "-w", "2", "-k", "gthread", "-b", "0.0.0.0:10000", "app:app"]
