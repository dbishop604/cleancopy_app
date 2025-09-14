# Start with an official Python runtime
FROM python:3.11-slim

# Install dependencies for pdf2image and tesseract
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    poppler-utils \
    libsm6 \
    libxext6 \
    libxrender1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy dependency list
COPY requirements.txt .

# Install Python dependencies (include gunicorn here)
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Copy the app code
COPY . .

# Expose the port (Render expects $PORT)
ENV PORT=10000
EXPOSE 10000

# Run the app with Gunicorn, binding to $PORT
CMD ["gunicorn", "-b", "0.0.0.0:10000", "app:app"]
