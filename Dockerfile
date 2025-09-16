# Use Python 3.11 slim image for smaller footprint
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create logs directory
RUN mkdir -p logs

# Set environment variables for Cloud Run
ENV PORT=8080
ENV PYTHONPATH=/app

# Expose port for Cloud Run
EXPOSE 8080

# Run the application
CMD uvicorn app:app --host 0.0.0.0 --port $PORT --workers 1