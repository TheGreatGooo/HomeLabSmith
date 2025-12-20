# HomeLabSmith

HomeLabSmith is a collection of services for managing and orchestrating AI models in a home lab environment.

## Services

1. **Inference Service** - Core service for running AI models
2. **Model Monitor Service** - Monitors model usage and performance
3. **Nginx Configmap Updater Service** - Updates nginx configuration dynamically
4. **Nginx Endpoint Activity Monitor** - Monitors nginx endpoint activity
5. **Shutdown Service** - Handles graceful shutdown of services
6. **Wake-on-LAN Service** - Handles wake-on-lan functionality
7. **Model Starter Service** - Starts and manages model inference endpoints automatically

## Architecture Overview

This system is designed to run in a Kubernetes environment with services communicating through nginx as a reverse proxy. The Model Starter Service acts as an upstream that ensures models are started when requested.

## Getting Started

1. Deploy the services using the provided Kubernetes manifests
2. Configure the services according to your environment
3. Access the services through nginx

## Contributing

Please read CONTRIBUTING.md for details on our code of conduct, and the process for submitting pull requests.

## License

This project is licensed under the MIT License - see the LICENSE file for details.