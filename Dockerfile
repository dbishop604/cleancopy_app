# Use a pinned Python 3.11 slim image for stability
FROM python:3.11.9-slim

# Prevent interactive prompts during package install
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

# Set working directory
WORKDIR /app

# Copy requirements first (for Docker layer caching)
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy all app code
COPY . /app/

# Expose the port Render expects
ENV PORT=10000
EXPOSE 10000

# Default: run the Flask app with Gunicorn
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:10000", "--workers=2", "--threads=2", "--timeout=120"]
