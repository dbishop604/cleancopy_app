# Use official lightweight Python image
FROM python:3.11-slim

# Set environment vars for Flask/Render
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=10000

# Install system dependencies (for tesseract & pdf2image)
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    libtesseract-dev \
    poppler-utils \
    libsm6 \
    libxext6 \
    libxrender1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy requirements first (for better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Expose port for Render
EXPOSE 10000

# Start the app with Gunicorn for production
CMD ["gunicorn", "-b", "0.0.0.0:10000", "app:app"]
