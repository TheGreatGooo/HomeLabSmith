#!/usr/bin/env python3
"""
Idle Approot Notification Service
Tails nginx logs and checks for endpoints that haven't been called in the last 10 minutes.
If an endpoint hasn't been called, it makes an HTTP request to a defined endpoint.
"""

import asyncio
import json
import logging
import os
import re
import signal
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import aiohttp
from aiohttp import ClientSession


# Configure logging
log_handler = logging.StreamHandler(sys.stdout)
log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log_handler.setFormatter(log_formatter)

logging.basicConfig(
    level=logging.INFO,
    handlers=[log_handler]
)
logger = logging.getLogger(__name__)


class NginxMonitor:
    def __init__(self, config_file: str = 'config.json'):
        """
        Initialize the Nginx Monitor
        
        Args:
            config_file: Path to the configuration file
        """
        self.config_file = config_file
        self.config = self._load_config()
        self.running = False
        self.last_seen_timestamps: Dict[str, datetime] = {}
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)

    def _load_config(self) -> List[Dict]:
        """
        Load configuration from JSON file
        
        Returns:
            List of endpoint configurations
        """
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
            
            # Validate config structure
            if not isinstance(config, list):
                raise ValueError("Config must be a list of endpoint configurations")
            
            for i, item in enumerate(config):
                if not isinstance(item, dict):
                    raise ValueError(f"Config item {i} must be a dictionary")
                if 'pattern' not in item:
                    raise ValueError(f"Config item {i} must have a 'pattern' field")
                if 'endpoint' not in item:
                    raise ValueError(f"Config item {i} must have an 'endpoint' field")
            
            logger.info(f"Loaded configuration with {len(config)} endpoint rules")
            return config
            
        except FileNotFoundError:
            logger.error(f"Configuration file {self.config_file} not found")
            sys.exit(1)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in configuration file: {e}")
            sys.exit(1)
        except ValueError as e:
            logger.error(f"Invalid configuration: {e}")
            sys.exit(1)

    def _signal_handler(self, signum, frame):
        """
        Handle shutdown signals
        """
        logger.info("Received shutdown signal")
        self.running = False

    def _parse_nginx_log_line(self, line: str) -> Optional[Dict]:
        """
        Parse a single nginx access log line
        
        Args:
            line: Single log line from nginx
            
        Returns:
            Dictionary with parsed information or None if parsing fails
        """
        # Nginx common log format: IP - - [timestamp] "METHOD URI HTTP/1.1" STATUS SIZE
        # Example: 172.17.0.1 - - [07/Dec/2025:01:30:45 +0000] "GET /api/v1/users HTTP/1.1" 200 1234
        pattern = r'^(\S+) \S+ \S+ \[([^\]]+)\] "(\S+) (\S+) HTTP/\S+" (\d+) (\S+)$'
        
        match = re.match(pattern, line.strip())
        if not match:
            return None
            
        ip, timestamp_str, method, uri, status, size = match.groups()
        
        # Parse timestamp
        try:
            # Nginx uses format: 07/Dec/2025:01:30:45 +0000
            timestamp = datetime.strptime(timestamp_str.split()[0], '%d/%b/%Y:%H:%M:%S')
        except ValueError:
            return None
            
        return {
            'ip': ip,
            'timestamp': timestamp,
            'method': method,
            'uri': uri,
            'status': int(status),
            'size': size
        }

    def _should_check_endpoint(self, uri: str) -> Optional[Dict]:
        """
        Check if the URI matches any configured pattern
        
        Args:
            uri: Requested URI
            
        Returns:
            Configuration for matching endpoint or None
        """
        for rule in self.config:
            # Use regex pattern matching
            if re.search(rule['pattern'], uri):
                return rule
        return None

    async def _check_endpoint(self, endpoint_config: Dict):
        """
        Make HTTP request to the defined endpoint
        
        Args:
            endpoint_config: Configuration for the endpoint to call
        """
        try:
            # Create a new session for each request to avoid connection pooling issues
            async with aiohttp.ClientSession() as session:
                # Make GET request to the endpoint
                async with session.get(
                    endpoint_config['endpoint'],
                    timeout=aiohttp.ClientTimeout(total=30),
                    headers={'User-Agent': 'idle-approot-notification/1.0'}
                ) as response:
                    if response.status == 200:
                        logger.info(f"Successfully called endpoint: {endpoint_config['endpoint']}")
                    else:
                        logger.warning(f"Endpoint returned status code {response.status}: {endpoint_config['endpoint']}")
                        
        except asyncio.TimeoutError:
            logger.error(f"Timeout calling endpoint {endpoint_config['endpoint']}")
        except aiohttp.ClientError as e:
            logger.error(f"Failed to call endpoint {endpoint_config['endpoint']}: {e}")

    def _process_log_line(self, line: str):
        """
        Process a single log line
        
        Args:
            line: Single nginx access log line
        """
        parsed = self._parse_nginx_log_line(line)
        if not parsed:
            return
            
        uri = parsed['uri']
        timestamp = parsed['timestamp']
        
        # Check if this URI matches any configured pattern
        endpoint_config = self._should_check_endpoint(uri)
        if not endpoint_config:
            return
            
        logger.debug(f"Processing log line for URI: {uri}")
        
        # Update last seen timestamp for this endpoint
        self.last_seen_timestamps[endpoint_config['pattern']] = timestamp

    async def _check_stale_endpoints(self):
        """
        Check for endpoints that haven't been called in the last 10 minutes
        """
        current_time = datetime.now()
        ten_minutes_ago = current_time - timedelta(minutes=10)
        
        logger.debug(f"Checking for stale endpoints (last seen before {ten_minutes_ago})")
        
        # Create a list of tasks to run concurrently
        tasks = []
        for rule in self.config:
            pattern = rule['pattern']
            
            # Check if we have a timestamp for this pattern
            last_seen = self.last_seen_timestamps.get(pattern)
            
            # If no timestamp exists or it's older than 10 minutes, call the endpoint
            if not last_seen or last_seen < ten_minutes_ago:
                logger.info(f"Endpoint {pattern} hasn't been called since {last_seen or 'never'} - calling {rule['endpoint']}")
                tasks.append(self._check_endpoint(rule))
        
        # Run all HTTP requests concurrently
        await asyncio.gather(*tasks, return_exceptions=True)

    async def _tail_log_file(self, log_file_path: str):
        """
        Tail a log file and process new lines as they appear
        
        Args:
            log_file_path: Path to the nginx access log file
        """
        try:
            # Open the file in binary mode for better compatibility with tailing
            with open(log_file_path, 'rb') as f:
                # Go to the end of the file
                f.seek(0, os.SEEK_END)
                
                while self.running:
                    line = f.readline()
                    if line:
                        # Decode bytes to string and process
                        line_str = line.decode('utf-8', errors='ignore').strip()
                        if line_str:
                            self._process_log_line(line_str)
                    else:
                        # No new data, wait a bit before checking again
                        await asyncio.sleep(0.1)
                        
        except FileNotFoundError:
            logger.error(f"Log file not found: {log_file_path}")
        except Exception as e:
            logger.error(f"Error tailing log file {log_file_path}: {e}")

    async def start(self):
        """
        Start the monitoring service
        """
        logger.info("Starting Idle Approot Notification Service")
        self.running = True
        
        # Get log file path from environment or use default
        log_file_path = os.environ.get('NGINX_LOG_FILE', '/var/log/nginx/access.log')
        
        # Create tasks for both log tailing and endpoint checking
        tasks = [
            self._tail_log_file(log_file_path),
            self._monitor_loop()
        ]
        
        # Run both tasks concurrently
        await asyncio.gather(*tasks, return_exceptions=True)
        
        logger.info("Idle Approot Notification Service stopped")

    async def _monitor_loop(self):
        """
        Main monitoring loop that checks for stale endpoints every 30 seconds
        """
        while self.running:
            try:
                # Check for stale endpoints every 30 seconds
                await self._check_stale_endpoints()
                
                # Wait for 30 seconds before next check
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(5)  # Wait a bit before retrying


def main():
    """Main entry point"""
    # Create event loop and run the async monitor
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        monitor = NginxMonitor()
        loop.run_until_complete(monitor.start())
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    finally:
        loop.close()


if __name__ == "__main__":
    main()