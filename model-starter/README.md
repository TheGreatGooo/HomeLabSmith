# Model Starter Service

This service starts and manages model inference endpoints, automatically starting models when they are requested via nginx upstream.

## Features
- Accepts all HTTP verbs
- Routes requests to /<model name>/...
- Checks if models are running
- Starts models automatically if needed
- Waits for model readiness before returning 504 status code to trigger nginx retry

## Architecture
This service integrates with nginx as an upstream to ensure models are started when requested. When a model is successfully started and becomes ready, it returns a 504 status code to indicate to nginx that it should retry the actual request to the real model service.

## Configuration
The service can be configured using environment variables:
- `INFERENCE_SERVER_HOST`: Host of the inference server (default: localhost)
- `INFERENCE_SERVER_PORT`: Port of the inference server (default: 5002)

## How It Works
1. When a request comes in to `/model_name/...`, the starter checks if models are running
2. If no models are running, it starts the requested model
3. It waits for the model to become ready
4. Then it returns a 504 status code to trigger nginx retry to the actual model service

## Deployment

### Docker
```bash
docker build -t model-starter .
docker run -p 8080:8080 model-starter
```

### Systemd
```bash
# Copy service file
sudo cp systemd/model-orchestrator.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable model-orchestrator
sudo systemctl start model-orchestrator
```

## API Endpoints
- `GET /<model_name>/` - Handle GET requests
- `POST /<model_name>/` - Handle POST requests
- `PUT /<model_name>/` - Handle PUT requests
- `DELETE /<model_name>/` - Handle DELETE requests
- `PATCH /<model_name>/` - Handle PATCH requests
- `HEAD /<model_name>/` - Handle HEAD requests
- `OPTIONS /<model_name>/` - Handle OPTIONS requests

## Status Codes
- `204 No Content` - When model is already running and request is handled
- `504 Gateway Timeout` - When model was started and is ready, but returns 504 to trigger nginx retry