FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libmagic1 \
    clamav \
    clamav-daemon \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY backend/ ./backend/
COPY frontend/ ./frontend/

# Expose port
EXPOSE 5000

# Start ClamAV and Flask app
CMD service clamav-daemon start && python backend/app.py
