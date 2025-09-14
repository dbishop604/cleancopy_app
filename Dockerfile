FROM python:3.11-slim

# Install system dependencies for OCR and PDFs
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    poppler-utils \
    libtesseract-dev \
    libleptonica-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app
COPY . .

# Run with Gunicorn, binding to the PORT Render provides
CMD ["sh", "-c", "gunicorn --workers=2 --threads=4 --timeout 120 -b 0.0.0.0:$PORT app:app"]
