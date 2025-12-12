FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install curl for healthcheck
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copy application
COPY . .

# Create data and logs directories
RUN mkdir -p /app/data/logs

# Expose port
EXPOSE 8009

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8009", "--log-config", "uvicorn_log_config.ini"]

# Healthcheck using dedicated /health endpoint that tests database connectivity
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD curl -f http://127.0.0.1:8009/health || exit 1
