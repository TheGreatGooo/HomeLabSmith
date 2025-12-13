FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5002

CMD ["python", "inference_service.py"]

# Add labels for GitHub Container Registry
LABEL org.opencontainers.image.source="https://github.com/TheGreatGooo/HomeLabSmith"
LABEL org.opencontainers.image.description="Inference Service"
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.vendor="HomeLabSmith"
LABEL org.opencontainers.image.title="inference-service"
LABEL org.opencontainers.image.version="1.0.0"