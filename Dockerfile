# Use official Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for pdf2image & Tesseract OCR
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    poppler-utils \
    libtesseract-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Expose the Render port
EXPOSE 10000

# Run with Gunicorn (production-ready)
CMD ["gunicorn", "-b", "0.0.0.0:10000", "app:app"]
