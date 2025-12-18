# Home Lab Services Systemd Configuration Summary

## Overview

This project provides a comprehensive systemd service configuration for managing three critical services in a home lab environment:
1. **Shutdown Service** - Manages system shutdown scheduling and execution
2. **Inference Service** - Manages machine learning model services via systemctl
3. **Model Monitor Service** - Monitors model activity and automatically shuts down idle models to save resources

## Service Architecture

### Shutdown Service (`shutdown-service.service`)
- **Purpose**: Exposes REST endpoints to manage system shutdowns
- **Port**: 5001
- **User**: `home-lab-services` (dedicated service user)
- **Key Features**:
  - Schedule shutdowns with configurable delay
  - Cancel scheduled shutdowns
  - View next scheduled shutdown
  - Get system uptime information
  - Uses sudo for actual shutdown execution

### Inference Service (`inference-service.service`)
- **Purpose**: Manages machine learning model services using systemctl
- **Port**: 5002
- **User**: `home-lab-services` (dedicated service user)
- **Key Features**:
  - List available inference models
  - Start, stop, and restart models
  - View currently running models
  - Integrates with systemctl for service management

### Model Monitor Service (`model-monitor-service.service`)
- **Purpose**: Monitors model activity and automatically shuts down idle models to save resources
- **Port**: 5003
- **User**: `home-lab-services` (dedicated service user)
- **Key Features**:
  - Reports active models (those that have received at least one request in the last 10 minutes)
  - Periodically checks for idle models (those not used for more than 30 minutes) and shuts them down
  - RESTful API endpoints for monitoring and reporting
  - Health check endpoint to verify service status

### NGINX ConfigMap Updater Service
- **Purpose**: Dynamically updates NGINX configuration based on available inference models
- **Namespace**: `inference-manager`
- **Key Features**:
  - Monitors inference service for available models
  - Automatically generates NGINX location blocks for each model
  - Updates NGINX ConfigMap with new configuration
  - Uses separate configmap for inference service URL to enable environment-specific configuration

### Manager Service (`home-lab-services.service`)
- **Purpose**: Acts as a coordinator for both services
- **Dependencies**: Ensures proper startup order and service coordination
- **Restart Policy**: Always restart with 10-second delay

## Configuration Details

### Security Features
- **User Isolation**: Both services run under the dedicated `home-lab-services` user for security
- **Root Privilege Separation**: Only required for shutdown commands, not general operation
- **Resource Limits**: Configured with limits to prevent resource exhaustion
- **Security Hardening**: Uses systemd security features like `PrivateTmp=true`, `ProtectSystem=strict`

### Logging Configuration
- **Standard Output**: Journal logging
- **Standard Error**: Journal logging
- **Syslog Identifier**: Unique identifiers for each service
- **Log Management**: Integrated with system logging infrastructure

### Restart Policies
- **Always Restart**: Services will automatically restart if they fail
- **Restart Delay**: 10 seconds between restart attempts to prevent rapid cycling

## Installation Process

1. **Run the installation script** (creates dedicated user/group if needed):
   ```bash
   ./install-services.sh
   ```

2. **Reload Configuration**:
   ```bash
   sudo systemctl daemon-reload
   ```

3. **Enable Services**:
   ```bash
   sudo systemctl enable shutdown-service.service
   sudo systemctl enable inference-service.service
   sudo systemctl enable model-monitor-service.service
   sudo systemctl enable home-lab-services.service
   ```

4. **Start Services**:
   ```bash
   sudo systemctl start shutdown-service.service
   sudo systemctl start inference-service.service
   sudo systemctl start model-monitor-service.service
   sudo systemctl start home-lab-services.service
   ```

## Management Commands

### Status and Logs
```bash
# Check status
sudo systemctl status shutdown-service.service
sudo systemctl status inference-service.service
sudo systemctl status model-monitor-service.service

# View logs
sudo journalctl -u shutdown-service.service -f
sudo journalctl -u inference-service.service -f
sudo journalctl -u model-monitor-service.service -f
```

### Control Services
```bash
# Restart services
sudo systemctl restart shutdown-service.service
sudo systemctl restart inference-service.service
sudo systemctl restart model-monitor-service.service

# Stop services
sudo systemctl stop shutdown-service.service
sudo systemctl stop inference-service.service
sudo systemctl stop model-monitor-service.service
```

## Resource Limits

Both services are configured with resource limits to prevent abuse:
- `LimitNOFILE=65536` - Maximum number of open file descriptors
- `LimitNPROC=4096` - Maximum number of processes

## Dependencies

The services require:
- Python 3.6+
- Flask framework
- psutil (for shutdown service)
- requests (for model-monitor service)
- systemctl (for inference service)

## Security Considerations

1. **User Permissions**: Services run under dedicated user accounts for isolation
2. **Privilege Escalation**: Only minimal root privileges required for shutdown operations
3. **Network Isolation**: Services bind to localhost by default
4. **Resource Constraints**: Prevents services from consuming excessive system resources

## Troubleshooting

### Common Issues:
1. **Permission Denied**: Ensure proper file permissions and user ownership
2. **Port Conflicts**: Verify ports 5001, 5002, and 5003 are not in use
3. **Service Failures**: Check logs with `journalctl` for detailed error information
4. **Configuration Errors**: Validate JSON configuration files

This systemd configuration provides a robust, secure, and maintainable way to manage both the shutdown and inference services in a home lab environment.