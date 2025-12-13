# Home Lab Services Systemd Configuration Summary

## Overview

This project provides a comprehensive systemd service configuration for managing two critical services in a home lab environment:
1. **Shutdown Service** - Manages system shutdown scheduling and execution
2. **Inference Service** - Manages machine learning model services via systemctl

## Service Architecture

### Shutdown Service (`shutdown-service.service`)
- **Purpose**: Exposes REST endpoints to manage system shutdowns
- **Port**: 5001
- **User**: `abc` (regular user)
- **Key Features**:
  - Schedule shutdowns with configurable delay
  - Cancel scheduled shutdowns
  - View next scheduled shutdown
  - Get system uptime information
  - Uses sudo for actual shutdown execution

### Inference Service (`inference-service.service`)
- **Purpose**: Manages machine learning model services using systemctl
- **Port**: 5002
- **User**: `abc` (regular user)
- **Key Features**:
  - List available inference models
  - Start, stop, and restart models
  - View currently running models
  - Integrates with systemctl for service management

### Manager Service (`home-lab-services.service`)
- **Purpose**: Acts as a coordinator for both services
- **Dependencies**: Ensures proper startup order and service coordination
- **Restart Policy**: Always restart with 10-second delay

## Configuration Details

### Security Features
- **User Isolation**: Both services run under the `abc` user for security
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

1. **Copy Service Files**:
   ```bash
   sudo cp shutdown-service.service /etc/systemd/system/
   sudo cp inference-service.service /etc/systemd/system/
   sudo cp home-lab-services.service /etc/systemd/system/
   ```

2. **Reload Configuration**:
   ```bash
   sudo systemctl daemon-reload
   ```

3. **Enable Services**:
   ```bash
   sudo systemctl enable shutdown-service.service
   sudo systemctl enable inference-service.service
   sudo systemctl enable home-lab-services.service
   ```

4. **Start Services**:
   ```bash
   sudo systemctl start shutdown-service.service
   sudo systemctl start inference-service.service
   sudo systemctl start home-lab-services.service
   ```

## Management Commands

### Status and Logs
```bash
# Check status
sudo systemctl status shutdown-service.service
sudo systemctl status inference-service.service

# View logs
sudo journalctl -u shutdown-service.service -f
sudo journalctl -u inference-service.service -f
```

### Control Services
```bash
# Restart services
sudo systemctl restart shutdown-service.service
sudo systemctl restart inference-service.service

# Stop services
sudo systemctl stop shutdown-service.service
sudo systemctl stop inference-service.service
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
- systemctl (for inference service)

## Security Considerations

1. **User Permissions**: Services run under dedicated user accounts for isolation
2. **Privilege Escalation**: Only minimal root privileges required for shutdown operations
3. **Network Isolation**: Services bind to localhost by default
4. **Resource Constraints**: Prevents services from consuming excessive system resources

## Troubleshooting

### Common Issues:
1. **Permission Denied**: Ensure proper file permissions and user ownership
2. **Port Conflicts**: Verify ports 5001 and 5002 are not in use
3. **Service Failures**: Check logs with `journalctl` for detailed error information
4. **Configuration Errors**: Validate JSON configuration files

This systemd configuration provides a robust, secure, and maintainable way to manage both the shutdown and inference services in a home lab environment.