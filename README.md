# Home Lab Services

This project provides a comprehensive systemd service configuration for managing both a shutdown service and an inference service in a home lab environment.

## Overview

The system consists of three main systemd services:
1. **Shutdown Service** - Manages system shutdown operations
2. **Inference Service** - Runs machine learning inference models
3. **Home Lab Services Manager** - Coordinates both services

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Home Lab Services                            │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌──────────────────┐    ┌─────────────┐ │
│  │ Shutdown Service│    │ Inference Service│    │ Manager     │ │
│  │ (shutdown.service)│  │ (inference.service)│  │ (manager)   │ │
│  └─────────────────┘    └──────────────────┘    └─────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Service Configuration Details

### Shutdown Service (`shutdown-service.service`)

**Purpose**: Manages system shutdown operations with proper dependencies and restart policies.

**Key Features**:
- Runs under dedicated `home-lab-services` user account for security isolation
- Requires network target before starting
- Uses restart policy with 10-second delay on failure
- Configured with resource limits (65536 file descriptors, 4096 processes)
- Secure system protection with private temporary directories
- Environment variables: PYTHONPATH=/config/HomeLabSmith, FLASK_ENV=production

### Inference Service (`inference-service.service`)

**Purpose**: Runs machine learning inference models with optimized performance.

**Key Features**:
- Runs under dedicated `home-lab-services` user account for security isolation
- Requires network target before starting
- Uses restart policy with 10-second delay on failure
- Configured with resource limits (65536 file descriptors, 4096 processes)
- Secure system protection with private temporary directories
- Environment variables: PYTHONPATH=/config/HomeLabSmith, FLASK_ENV=production, MODELS_CONFIG_DIR=/home/abc/models/configs

### Manager Service (`home-lab-services.service`)

**Purpose**: Coordinates both services and ensures proper startup/shutdown order.

**Key Features**:
- Runs under root account for system-level operations
- Starts both shutdown and inference services on boot
- Stops both services when manager stops
- Uses restart policy with 30-second delay on failure
- Configured with appropriate resource limits
- Environment variables: PYTHONPATH=/config/HomeLabSmith
- Environment variables: PYTHONPATH=/config/HomeLabSmith, FLASK_ENV=production

### Inference Service (`inference-service.service`)

**Purpose**: Runs machine learning inference models with optimized performance.

**Key Features**:
- Runs under dedicated `home-lab-services` user account for security isolation
- Requires network target before starting
- Uses restart policy with 10-second delay on failure
- Configured with resource limits (65536 file descriptors, 4096 processes)
- Secure system protection with private temporary directories
- Environment variables: PYTHONPATH=/config/HomeLabSmith, FLASK_ENV=production, MODELS_CONFIG_DIR=/config/models

### Manager Service (`home-lab-services.service`)

**Purpose**: Coordinates both services and ensures proper startup/shutdown order.

**Key Features**:
- Runs under root account for system-level operations
- Starts both shutdown and inference services on boot
- Stops both services when manager stops
- Uses restart policy with 30-second delay on failure
- Configured with appropriate resource limits

## Installation

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
sudo systemctl start home-lab-services.service
```

### Stopping Services
```bash
sudo systemctl stop shutdown-service.service
sudo systemctl stop inference-service.service
sudo systemctl stop home-lab-services.service
```

### Checking Status
```bash
sudo systemctl status shutdown-service.service
sudo systemctl status inference-service.service
sudo systemctl status home-lab-services.service
```

### Viewing Logs
```bash
sudo journalctl -u shutdown-service.service -f
sudo journalctl -u inference-service.service -f
sudo journalctl -u home-lab-services.service -f
```

## Security Considerations

1. **User Isolation**: Both services run under the dedicated `home-lab-services` user account to limit system access.
2. **Resource Limits**: Configured with appropriate limits to prevent resource exhaustion.
3. **System Protection**: Uses `ProtectSystem=strict` and `PrivateTmp=true` for enhanced security.
4. **No New Privileges**: `NoNewPrivileges=true` prevents privilege escalation.

## Dependencies

- systemd (systemd version 240 or higher)
- Python 3.8+
- Required Python packages listed in `requirements.txt`

## Troubleshooting

### Common Issues

1. **Service fails to start**:
   ```bash
   sudo journalctl -u shutdown-service.service --no-pager
   sudo journalctl -u inference-service.service --no-pager
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
systemctl is-enabled home-lab-services.service

# List all services
systemctl list-unit-files | grep -E "(shutdown|inference|home-lab)"
```

## Configuration Files

### Service Configuration Locations:
- Shutdown service: `/etc/systemd/system/shutdown-service.service`
- Inference service: `/etc/systemd/system/inference-service.service`
- Manager service: `/etc/systemd/system/home-lab-services.service`

### Service Directories:
- Shutdown service files: `/config/HomeLabSmith/shutdown-service/`
- Inference service files: `/config/HomeLabSmith/inference-service/`
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
   ```

### Service Logs
All service logs are managed by systemd and can be viewed with:
```bash
sudo journalctl -u shutdown-service.service
sudo journalctl -u inference-service.service
sudo journalctl -u home-lab-services.service
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.