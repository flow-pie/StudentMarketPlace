# Use the latest Python 3.13 slim image
FROM python:3.13-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_ENV=production

# Install system dependencies in one go, then clean up
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip for faster wheel installs
RUN pip install --no-cache-dir --upgrade pip

# Set PYTHONPATH to include the API-Core directory
ENV PYTHONPATH=/app/API-Core:$PYTHONPATH

# Create and set work directory
WORKDIR /app

# Copy and install Python dependencies (cached layer)
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy only the API-Core code
COPY API-Core ./API-Core

# Expose Flask port
EXPOSE 5000

# Default command (can be overridden via Docker Compose)
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "API-Core.run:app"]