FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY model_monitor.py .
COPY config.json .

# Expose port
EXPOSE 5003

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5003/health || exit 1

# Run the application
CMD ["python", "model_monitor.py"]

# Add labels for GitHub Container Registry
LABEL org.opencontainers.image.source="https://github.com/TheGreatGooo/HomeLabSmith"
LABEL org.opencontainers.image.description="Model Monitor Service"
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.vendor="HomeLabSmith"
LABEL org.opencontainers.image.title="model-monitor-service"
LABEL org.opencontainers.image.version="1.0.0"