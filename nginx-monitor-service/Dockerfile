FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY nginx_monitor.py .
COPY config.json .

# Create log directory
RUN mkdir -p /var/log

# Create non-root user
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app /var/log
USER appuser

# Expose port (if needed for health checks)
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 -c "import requests; response = requests.get('http://localhost:8080/health', timeout=5); exit(1 if response.status_code != 200 else 0)" || exit 1

# Run the application
CMD ["python3", "nginx_monitor.py"]