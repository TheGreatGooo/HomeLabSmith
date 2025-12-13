# Shutdown Service

A Python Flask service that exposes endpoints to manage system shutdowns.

## Endpoints

- `POST /shutdown/schedule` - Schedule a shutdown
  - Request body: `{"minutes": <number>}` (default: 1)
  - Response: Scheduled shutdown information

- `GET /shutdown/next` - Get the next scheduled shutdown

- `POST /shutdown/cancel` - Cancel the next scheduled shutdown

- `GET /shutdown/status` - Get current shutdown status

## Usage Examples

### Schedule a shutdown in 10 minutes:
```bash
curl -X POST http://localhost:5001/shutdown/schedule \
  -H "Content-Type: application/json" \
  -d '{"minutes": 10}'
```

### Get next shutdown:
```bash
curl http://localhost:5001/shutdown/next
```

### Cancel next shutdown:
```bash
curl -X POST http://localhost:5001/shutdown/cancel
```

## Requirements

- Python 3.6+
- Flask
- psutil