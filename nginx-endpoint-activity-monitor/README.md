# Nginx Endpoint Activity Monitor

A Python service that monitors nginx access logs for endpoint activity and triggers configured HTTP endpoints when URI patterns haven't been active for a specified period.

## Features

- Tails nginx access log file
- Monitors specific URI patterns defined in configuration
- Checks every 30 seconds if a pattern has been seen in the last 10 minutes
- Makes HTTP requests to configured endpoints when patterns are inactive
- Logs all activities to file and stdout

## Configuration

The service uses a `config.json` file to define monitoring rules:

```json
[
    {
        "pattern": "/api/users",
        "endpoint": "http://localhost:8080/health"
    },
    {
        "pattern": "/api/products",
        "endpoint": "http://localhost:8080/heartbeat"
    }
]
```

Each rule consists of:
- `pattern`: A regex pattern to match against URIs in the access log
- `endpoint`: The HTTP endpoint to call when the pattern hasn't been seen for 10 minutes

## Installation

1. Build the Docker image:
   ```bash
   docker build -t nginx-endpoint-activity-monitor .
   ```

2. Run the service:
   ```bash
   docker run -d \
     --name nginx-endpoint-activity-monitor \
     -v /var/log/nginx:/var/log/nginx:ro \
     -v $(pwd)/config.json:/config.json:ro \
     nginx-endpoint-activity-monitor
   ```

## Usage

The service will automatically:
1. Tail the nginx access log file
2. Monitor for specified URI patterns
3. Check every 30 seconds if any pattern has been seen in the last 10 minutes
4. Call configured endpoints when patterns are stale

## Logging

All logs are written to `/var/log/nginx-endpoint-activity-monitor.log` and stdout.