# Use a lightweight Python image
FROM python:3.11-slim

# Install system dependencies for Tesseract OCR and Poppler
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    libtesseract-dev \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Set workdir
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Copy app code
COPY . .

# Expose Render’s default port
EXPOSE 10000

# Healthcheck endpoint for Render (matches render.yaml)
HEALTHCHECK CMD curl --fail http://localhost:10000/healthz || exit 1

# Start with Gunicorn (more stable than Flask dev server)
CMD ["gunicorn", "app:app", "-b", "0.0.0.0:10000", "-t", "120"]
