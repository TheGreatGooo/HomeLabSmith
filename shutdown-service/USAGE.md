# Shutdown Service Usage Guide

This service provides REST endpoints to manage system shutdowns programmatically.

## Prerequisites

- Python 3.6+
- sudo access (for executing shutdown commands)
- Docker (optional, for containerized deployment)

## Installation

### Direct Installation
```bash
cd shutdown-service
pip install -r requirements.txt
python shutdown_service.py
```

### Docker Installation
```bash
cd shutdown-service
docker build -t shutdown-service .
docker run -p 5001:5001 shutdown-service
```

## API Endpoints

### 1. Schedule Shutdown
**POST** `/shutdown/schedule`
- Body: `{"minutes": <number>}` (default: 1)
- Response: Success or error message with scheduled time

### 2. Get Next Shutdown
**GET** `/shutdown/next`
- Response: Information about the next scheduled shutdown or "No shutdown scheduled"

### 3. Cancel Shutdown
**POST** `/shutdown/cancel`
- Response: Success message and cancelled shutdown details

### 4. Get Shutdown Status
**GET** `/shutdown/status`
- Response: Current shutdown status (has_shutdown, next_shutdown)

### 5. System Information
**GET** `/shutdown/system`
- Response: System uptime information

### 6. Service Home
**GET** `/`
- Response: Service information and available endpoints

## Usage Examples

### Schedule a shutdown in 10 minutes:
```bash
curl -X POST http://localhost:5001/shutdown/schedule \
  -H "Content-Type: application/json" \
  -d '{"minutes": 10}'
```

### Get next scheduled shutdown:
```bash
curl http://localhost:5001/shutdown/next
```

### Cancel the next shutdown:
```bash
curl -X POST http://localhost:5001/shutdown/cancel
```

## Configuration

The service uses `config.json` for configuration:
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

## Security Notes

- The service requires sudo access to execute shutdown commands
- Ensure proper permissions are set for the service user
- Consider using authentication in production environments

## Troubleshooting

### Common Issues:
1. **sudo access denied**: Make sure the service has appropriate sudo permissions
2. **Port already in use**: Change the port in config.json or stop existing processes
3. **File permission errors**: Ensure the service can read/write to its working directory

### Testing:
Run the integration test to verify all functionality works:
```bash
python integration_test.py