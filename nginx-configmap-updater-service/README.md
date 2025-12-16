# NGINX ConfigMap Updater Service

This service continuously monitors an inference service for available models and dynamically updates an NGINX ConfigMap with location entries that route to corresponding upstream services.

## Features

- **Real-time Model Monitoring**: Continuously polls the inference service for available models
- **Dynamic Configuration Updates**: Automatically generates and applies NGINX configuration changes
- **Robust Error Handling**: Implements retry logic and graceful degradation
- **Kubernetes Integration**: Works seamlessly with Kubernetes ConfigMaps
- **Model Change Detection**: Only updates when model configurations actually change

## How It Works

1. The service polls the inference service at regular intervals (default: 30 seconds)
2. It fetches the list of available models including their port numbers
3. It generates NGINX configuration with location blocks for each model
4. It updates the NGINX ConfigMap with the new configuration
5. The NGINX deployment automatically reloads the configuration

## Configuration

The service can be configured using environment variables:

- `INFERENCE_SERVICE_URL`: URL of the inference service (default: http://localhost:5002)
- `CONFIGMAP_NAME`: Name of the NGINX ConfigMap (default: nginx-config-map)
- `CONFIGMAP_NAMESPACE`: Namespace of the ConfigMap (default: default)
- `CHECK_INTERVAL`: Polling interval in seconds (default: 30)
- `MAX_RETRIES`: Maximum retry attempts for API calls (default: 3)
- `RETRY_DELAY`: Delay between retries in seconds (default: 5)

## Deployment

This service is designed to run as a Kubernetes deployment. It requires:
- Access to the Kubernetes API
- Read/write permissions for the specified ConfigMap
- Network access to the inference service

## Usage

```bash
# Run locally (requires kubeconfig)
python nginx_configmap_updater.py

# Or build and run as a Docker container
docker build -t nginx-configmap-updater .
docker run nginx-configmap-updater
```

## Example Configuration

The service expects the inference service to return models in this format:
```json
{
  "models": [
    {
      "model_name": "model1",
      "port": "8080"
    },
    {
      "model_name": "model2", 
      "port": "8081"
    }
  ]
}
```

This will generate NGINX location blocks like:
```
location /model1/ {
    proxy_pass http://localhost:8080/;
    ...
}

location /model2/ {
    proxy_pass http://localhost:8081/;
    ...
}
```
