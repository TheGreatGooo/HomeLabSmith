# Home Lab Services Documentation

## Overview

This project provides a comprehensive systemd service configuration for managing multiple services in a home lab environment. The system consists of several interconnected services that work together to provide shutdown management, machine learning inference capabilities, model monitoring, and Kubernetes integration.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Home Lab Services                            │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌──────────────────┐    ┌─────────────┐ │
│  │ Shutdown Service│    │ Inference Service│    │             │ │
│  │ (shutdown.service)│  │ (inference.service)│  │             │ │
│  └─────────────────┘    └──────────────────┘    └─────────────┘ │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │ NGINX ConfigMap Updater Service                           │  │
│  │ (monitors inference service and updates NGINX configmap)  │  │
│  └─────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Services

### 1. Shutdown Service (`shutdown-service.service`)

**Purpose**: Exposes REST endpoints to manage system shutdowns

**Key Features**:
- Schedule shutdowns with configurable delay
- Cancel scheduled shutdowns
- View next scheduled shutdown
- Get system uptime information
- Uses sudo for actual shutdown execution

**Port**: 5001
**User**: `home-lab-services` (dedicated service user)

**Endpoints**:
- `POST /shutdown/schedule` - Schedule a shutdown
- `GET /shutdown/next` - Get the next scheduled shutdown
- `POST /shutdown/cancel` - Cancel the next scheduled shutdown
- `GET /shutdown/status` - Get current shutdown status

### 2. Inference Service (`inference-service.service`)

**Purpose**: Manages machine learning model services using systemctl

**Key Features**:
- List available inference models
- Start, stop, and restart models
- View currently running models
- Integrates with systemctl for service management

**Port**: 5002
**User**: `home-lab-services` (dedicated service user)

**Endpoints**:
- `GET /models` - Get list of available models
- `GET /models/running` - Get list of running models  
- `POST /models/<model_name>/start` - Start a specific model
- `POST /models/<model_name>/stop` - Stop a specific model
- `POST /models/<model_name>/restart` - Restart a specific model

### 4. NGINX ConfigMap Updater Service

**Purpose**: Dynamically updates NGINX configuration based on available inference models

**Key Features**:
- Monitors inference service for available models
- Automatically generates NGINX location blocks for each model
- Updates NGINX ConfigMap with new configuration
- Uses separate configmap for inference service URL to enable environment-specific configuration

## Kubernetes Integration

### NGINX Deployment

The system includes Kubernetes manifests for deploying NGINX with an endpoint activity monitor as a sidecar container:

- **Nginx Server**: Based on `lscr.io/linuxserver/nginx:latest` image
- **Sidecar Monitor**: `nginx-endpoint-activity-monitor` that monitors endpoint activity
- **ConfigMap**: Contains nginx configuration and monitor configuration

### NGINX ConfigMap Updater

This service runs as a Kubernetes deployment and:
- Continuously polls the inference service for available models
- Generates NGINX configuration with location blocks for each model
- Updates the NGINX ConfigMap with the new configuration
- Works seamlessly with Kubernetes ConfigMaps

## Installation

### Prerequisites
- systemd (systemd version 240 or higher)
- Python 3.8+
- Required Python packages listed in `requirements.txt`

### Installation Steps

1. Make the installation script executable:
   ```bash
   chmod +x install-services.sh
   ```

2. Run the installation script (requires sudo):
   ```bash
   sudo ./install-services.sh
   ```

3. The services will be automatically enabled to start on boot.

## Service Management

### Starting Services
```bash
sudo systemctl start shutdown-service.service
sudo systemctl start inference-service.service
sudo systemctl start model-monitor-service.service
```

### Stopping Services
```bash
sudo systemctl stop shutdown-service.service
sudo systemctl stop inference-service.service
sudo systemctl stop model-monitor-service.service
```

### Checking Status
```bash
sudo systemctl status shutdown-service.service
sudo systemctl status inference-service.service
sudo systemctl status model-monitor-service.service
```

### Viewing Logs
```bash
sudo journalctl -u shutdown-service.service -f
sudo journalctl -u inference-service.service -f
sudo journalctl -u model-monitor-service.service -f
```

## Security Considerations

1. **User Isolation**: All services run under the dedicated `home-lab-services` user account to limit system access.
2. **Resource Limits**: Configured with appropriate limits to prevent resource exhaustion.
3. **System Protection**: Uses `ProtectSystem=strict` and `PrivateTmp=true` for enhanced security.
4. **No New Privileges**: `NoNewPrivileges=true` prevents privilege escalation.
5. **Root Privilege Separation**: Only required for shutdown commands, not general operation.

## Configuration Files

### Service Configuration Locations:
- Shutdown service: `/etc/systemd/system/shutdown-service.service`
- Inference service: `/etc/systemd/system/inference-service.service`
- Model monitor service: `/etc/systemd/system/model-monitor-service.service`

### Service Directories:
- Shutdown service files: `/config/HomeLabSmith/shutdown-service/`
- Inference service files: `/config/HomeLabSmith/inference-service/`
- Model monitor service files: `/config/HomeLabSmith/model-monitor-service/`
- Shared data directory: `/var/lib/home-lab-services/`

## Maintenance

### Updating Services
1. Update the Python source files in their respective directories
2. Reload systemd configuration:
   ```bash
   sudo systemctl daemon-reload
   ```
3. Restart services:
   ```bash
   sudo systemctl restart shutdown-service.service
   sudo systemctl restart inference-service.service
   sudo systemctl restart model-monitor-service.service
   ```

### Service Logs
All service logs are managed by systemd and can be viewed with:
```bash
sudo journalctl -u shutdown-service.service
sudo journalctl -u inference-service.service
sudo journalctl -u model-monitor-service.service
```

## Troubleshooting

### Common Issues

1. **Service fails to start**:
   ```bash
   sudo journalctl -u shutdown-service.service --no-pager
   sudo journalctl -u inference-service.service --no-pager
   sudo journalctl -u model-monitor-service.service --no-pager
   ```

2. **Permission denied errors**:
   Check that the `home-lab-services` user has proper permissions on required directories.

3. **Network connectivity issues**:
   Verify network target dependencies are met before service startup.

### Verification Commands

```bash
# Check if services are enabled
systemctl is-enabled shutdown-service.service
systemctl is-enabled inference-service.service
systemctl is-enabled model-monitor-service.service

# List all services
systemctl list-unit-files | grep -E "(shutdown|inference|model-monitor)"
```

## Dependencies

- systemd (systemd version 240 or higher)
- Python 3.8+
- Required Python packages listed in `requirements.txt`
- systemctl (for inference service)
- Docker (for containerized services)

## License

This project is licensed under the MIT License - see the LICENSE file for details.