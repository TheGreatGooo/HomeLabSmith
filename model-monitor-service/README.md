# Model Monitor Service

A Python Flask service that monitors model activity and automatically shuts down idle models to save resources.

## Features

- Reports active models (those that have received at least one request in the last 10 minutes)
- Periodically checks for idle models (those not used for more than 30 minutes) and shuts them down
- RESTful API endpoints for monitoring and reporting
- Health check endpoint to verify service status

## Endpoints

### Model Activity Reporting
- `GET /models/active` - Get list of models that have been active in the last 10 minutes
- `GET /models/idle` - Get list of models that have been idle for more than 30 minutes
- `GET /models/activity` - Get activity status for all models

### Model Reporting
- `POST /models/<model_name>/report` - Report that a model has been used (updates last activity timestamp)

### Health Check
- `GET /health` - Health check endpoint

## Configuration

The service uses a `config.json` file for configuration:

```json
{
  "service": {
    "port": 5003,
    "host": "0.0.0.0"
  },
  "monitoring": {
    "reporting_interval_minutes": 10,
    "shutdown_check_interval_minutes": 10,
    "idle_threshold_minutes": 30,
    "active_threshold_minutes": 10
  },
  "inference_service": {
    "base_url": "http://localhost:5002"
  }
}
```

## Usage

### Start the service
```bash
python model_monitor.py
```

### Report model usage
```bash
curl -X POST http://localhost:5003/models/my-model/report
```

### Get active models
```bash
curl http://localhost:5003/models/active
```

### Get idle models
```bash
curl http://localhost:5003/models/idle
```

### Get activity status for all models
```bash
curl http://localhost:5003/models/activity
```

## Docker Usage

Build the Docker image:
```bash
docker build -t model-monitor-service .
```

Run the container:
```bash
docker run -p 5003:5003 model-monitor-service
```

## How It Works

1. **Activity Reporting**: The service periodically reports which models have been active in the last 10 minutes
2. **Idle Detection**: The service checks for models that haven't been used for more than 30 minutes
3. **Automatic Shutdown**: When idle models are detected, they are automatically shut down via the inference service
4. **Manual Reporting**: Models can also be manually reported as active when used

## Dependencies

- Flask: Web framework
- requests: HTTP client for communicating with inference service
- psutil: System monitoring (not currently used but included for future expansion)

## Requirements

- Python 3.6+
- Access to the inference service on port 5002