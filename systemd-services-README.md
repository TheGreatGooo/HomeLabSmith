# Home Lab Services Systemd Configuration

This documentation explains how to set up and manage the Home Lab services using systemd, including both the shutdown service and inference service.

## Overview

The system consists of two main services:
1. **Shutdown Service** - Manages system shutdown scheduling and execution
2. **Inference Service** - Manages machine learning model services via systemctl

Both services are configured to run as systemd services with proper dependencies, restart policies, user permissions, logging configuration, and resource limits.

## Service Files

### 1. Shutdown Service (`shutdown-service.service`)

This service manages system shutdown scheduling and execution.

#### Key Features:
- Runs on port 5001
- Requires root privileges for shutdown commands
- Uses a lock file to prevent multiple shutdown processes
- Stores scheduled shutdowns in JSON format
- Integrates with psutil for system information

#### Configuration:
- **User**: `abc` (regular user)
- **Group**: `abc`
- **Working Directory**: `/config/HomeLabSmith/shutdown-service`
- **Restart Policy**: Always restart with 10 second delay
- **Logging**: Journal logging with syslog identifier `shutdown-service`

### 2. Inference Service (`inference-service.service`)

This service manages machine learning model services using systemctl.

#### Key Features:
- Runs on port 5002
- Interacts with systemctl to manage model services
- Reads model configurations from `~/models/configs`
- Supports start, stop, and restart operations for models

#### Configuration:
- **User**: `abc` (regular user)
- **Group**: `abc`
- **Working Directory**: `/config/HomeLabSmith/inference-service`
- **Restart Policy**: Always restart with 10 second delay
- **Logging**: Journal logging with syslog identifier `inference-service`

### 3. Home Lab Services Manager (`home-lab-services.service`)

This service acts as a manager that ensures both services are running and properly configured.

#### Key Features:
- Manages dependencies between services
- Ensures proper startup order
- Provides unified restart and monitoring capabilities

## Installation Instructions

1. **Copy service files to systemd directory:**
   ```bash
   sudo cp shutdown-service.service /etc/systemd/system/
   sudo cp inference-service.service /etc/systemd/system/
   sudo cp home-lab-services.service /etc/systemd/system/
   ```

2. **Reload systemd configuration:**
   ```bash
   sudo systemctl daemon-reload
   ```

3. **Enable services to start on boot:**
   ```bash
   sudo systemctl enable shutdown-service.service
   sudo systemctl enable inference-service.service
   sudo systemctl enable home-lab-services.service
   ```

4. **Start the services:**
   ```bash
   sudo systemctl start shutdown-service.service
   sudo systemctl start inference-service.service
   sudo systemctl start home-lab-services.service
   ```

## Management Commands

### Check service status:
```bash
sudo systemctl status shutdown-service.service
sudo systemctl status inference-service.service
sudo systemctl status home-lab-services.service
```

### View logs:
```bash
sudo journalctl -u shutdown-service.service -f
sudo journalctl -u inference-service.service -f
sudo journalctl -u home-lab-services.service -f
```

### Restart services:
```bash
sudo systemctl restart shutdown-service.service
sudo systemctl restart inference-service.service
sudo systemctl restart home-lab-services.service
```

### Stop services:
```bash
sudo systemctl stop shutdown-service.service
sudo systemctl stop inference-service.service
sudo systemctl stop home-lab-services.service
```

## Security Considerations

1. **User Permissions**: Both services run under the `abc` user for security isolation
2. **Root Privileges**: The shutdown service requires root privileges only for shutdown commands, not for general operation
3. **Resource Limits**: Configured with limits to prevent resource exhaustion
4. **Security Hardening**: Uses `PrivateTmp=true`, `ProtectSystem=strict`, and `NoNewPrivileges=true`

## Dependencies

The services have the following dependencies:
- Python 3.6+
- Flask framework
- psutil (for shutdown service)
- systemctl (for inference service)

## Troubleshooting

### Common Issues:

1. **Service fails to start due to permissions**:
   ```bash
   sudo systemctl status shutdown-service.service
   sudo journalctl -u shutdown-service.service
   ```

2. **Port conflicts**:
   Check if ports 5001 or 5002 are already in use:
   ```bash
   sudo netstat -tulpn | grep :500[12]
   ```

3. **Configuration issues**:
   Verify configuration files exist and are properly formatted:
   ```bash
   cat /config/HomeLabSmith/shutdown-service/config.json
   cat /config/HomeLabSmith/inference-service/config.json
   ```

## Configuration Files

### Shutdown Service Configuration (`shutdown-service/config.json`):
```json
{
  "service": {
    "port": 5001,
    "host": "0.0.0.0"
  },
  "shutdown": {
    "default_minutes": 1,
    "lock_file": "shutdown.lock"
  }
}
```

### Inference Service Configuration:
The inference service does not require a separate configuration file, but expects model configurations in `~/models/configs`.

## Resource Limits

Both services are configured with resource limits to prevent abuse:
- `LimitNOFILE=65536` - Maximum number of open file descriptors
- `LimitNPROC=4096` - Maximum number of processes