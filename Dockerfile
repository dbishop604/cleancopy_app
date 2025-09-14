FROM python:3.11-slim

# Install system dependencies for Tesseract and PDF handling
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    poppler-utils \
    libtesseract-dev \
    libleptonica-dev \
    libsm6 \
    libxext6 \
    libxrender1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Expose Render's default port
EXPOSE 10000

# Run with Gunicorn in production
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:10000", "app:app", "--timeout", "120"]
