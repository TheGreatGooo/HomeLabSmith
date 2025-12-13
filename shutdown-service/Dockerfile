FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY shutdown_service.py .

EXPOSE 5001

CMD ["python", "shutdown_service.py"]

# Add labels for GitHub Container Registry
LABEL org.opencontainers.image.source="https://github.com/TheGreatGooo/HomeLabSmith"
LABEL org.opencontainers.image.description="Shutdown Service"
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.vendor="HomeLabSmith"
LABEL org.opencontainers.image.title="shutdown-service"
LABEL org.opencontainers.image.version="1.0.0"