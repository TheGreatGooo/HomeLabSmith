# Inference Model Service

A Python Flask service that exposes REST endpoints to manage inference models using systemctl.

## Features

- Get list of available inference models
- Start, stop, and restart inference models
- Get list of currently running models
- Uses systemctl to interact with model services

## Endpoints

- `GET /models` - Get list of available models
- `GET /models/running` - Get list of running models  
- `POST /models/<model_name>/start` - Start a specific model
- `POST /models/<model_name>/stop` - Stop a specific model
- `POST /models/<model_name>/restart` - Restart a specific model

## Usage

### Get available models
```bash
curl http://localhost:5002/models
```

### Get running models
```bash
curl http://localhost:5002/models/running
```

### Start a model
```bash
curl -X POST http://localhost:5002/models/my-model/start
```

### Stop a model
```bash
curl -X POST http://localhost:5002/models/my-model/stop
```

### Restart a model
```bash
curl -X POST http://localhost:5002/models/my-model/restart
```

## Configuration

Models are expected to be in `~/models/configs` directory, where each file represents a model name.

The service uses systemctl to manage models with the pattern: `model@<model-name>`.