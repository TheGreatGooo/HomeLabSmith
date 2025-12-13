FROM python:3.9-slim

WORKDIR /app

COPY wol-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY wol-service/ .

EXPOSE 5000

CMD ["python", "wol_service.py"]

# Add labels for GitHub Container Registry
LABEL org.opencontainers.image.source="https://github.com/TheGreatGooo/HomeLabSmith"
LABEL org.opencontainers.image.description="Wake-on-LAN Service"
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.vendor="HomeLabSmith"
LABEL org.opencontainers.image.title="wol-service"
LABEL org.opencontainers.image.version="1.0.0"