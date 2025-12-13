# Nginx Deployment with Sidecar Monitor

This directory contains Kubernetes manifests for deploying an nginx server with an endpoint activity monitor as a sidecar container.

## Components

1. **Nginx Server**: Based on `lscr.io/linuxserver/nginx:latest` image
2. **Sidecar Monitor**: `nginx-endpoint-activity-monitor` that monitors endpoint activity
3. **ConfigMap**: Contains nginx configuration and monitor configuration

## Features

- Uses ConfigMap for configuration management
- Mounts nginx logs for monitoring
- Sidecar container pattern for monitoring
- Proper volume mounting for configuration files
- LoadBalancer service for external access

## Deployment

To deploy:

```bash
chmod +x deploy.sh
./deploy.sh
```

Or manually:

```bash
kubectl apply -f k8s/nginx/nginx-configmap.yaml
kubectl apply -f k8s/nginx/nginx-deployment.yaml
```

## Configuration

The nginx configuration is in `nginx.conf` and the monitor configuration is in `config.json`. Both are stored in a single ConfigMap.

## Monitoring

The sidecar container monitors nginx access logs for specific URI patterns and triggers HTTP endpoints when those patterns haven't been active for 10 minutes.