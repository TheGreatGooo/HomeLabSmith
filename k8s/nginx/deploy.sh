#!/bin/bash

# Deploy nginx with sidecar monitor to Kubernetes
echo "Deploying nginx with sidecar monitor..."

# Create the config map first
kubectl apply -f k8s/nginx/nginx-configmap.yaml

# Wait a moment for the config map to be created
sleep 2

# Deploy the application
kubectl apply -f k8s/nginx/nginx-deployment.yaml

echo "Deployment completed!"
echo "Check status with: kubectl get pods"
echo "Check services with: kubectl get svc"