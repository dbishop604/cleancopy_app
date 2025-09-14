# Use official Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy all app files
COPY . /app/

# Set environment variable for port
ENV PORT=10000

# Expose the port
EXPOSE 10000

# Start the web server
CMD ["gunicorn", "--bind", "0.0.0.0:10000", "app:app"]

