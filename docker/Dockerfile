# Use a slim version of Python 3.11
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Create a non-root user and switch to it for better security
RUN useradd -m botuser && \
    mkdir -p /app/logs && \
    chown -R botuser:botuser /app
USER botuser

# Expose the API port
EXPOSE 8000

# Default command (can be overridden in docker-compose)
CMD ["python", "main.py"]
