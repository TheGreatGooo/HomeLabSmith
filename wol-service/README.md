# Wake-on-LAN HTTP Service

A simple HTTP service that sends Wake-on-LAN (WoL) packets based on URI patterns.

## Features

- HTTP server that listens for requests
- Regex pattern matching for URI paths
- Wake-on-LAN functionality using MAC addresses
- Cooldown period to prevent spamming WOL requests (5 minutes)
- Disk-based tracking of last WOL requests
- JSON configuration file for patterns and MAC addresses

## Installation

1. Install required packages:
   ```bash
   pip install flask regex wakeonlan
   ```

2. Configure patterns in `config.json`

## Usage

Start the service:
```bash
python wol_service.py
```

The service will listen on port 5000.

## Configuration

The `config.json` file contains the patterns and MAC addresses:
```json
[
  {
    "pattern": "^/wake/office$",
    "mac_address": "00:11:22:33:44:55"
  },
  {
    "pattern": "^/wake/living-room$",
    "mac_address": "AA:BB:CC:DD:EE:FF"
  }
]
```

## Endpoints

- `GET /<path>` - Matches the path against patterns and sends WoL if matched
- `GET /` - Shows available endpoints

## Behavior

- When a request matches a pattern, a Wake-on-LAN packet is sent to the associated MAC address
- If a WoL request was sent within the last 5 minutes for that pattern, a 503 error is returned
- The last request times are stored in `last_requests.json` on disk

## Testing

Run the test script to verify the service:
```bash
python test_service.py