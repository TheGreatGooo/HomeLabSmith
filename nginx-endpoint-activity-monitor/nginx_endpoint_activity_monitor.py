#!/usr/bin/env python3
"""
Nginx Endpoint Activity Monitor
Monitors nginx access logs for endpoint activity and triggers configured endpoints when patterns are active.
Reports immediately when activity is detected, with debouncing to prevent calls more than once every 1 minutes.
"""

import asyncio
import json
import logging
import os
import re
import signal
import socket
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
        # Get config file path from environment variable or use default
        self.config_file = os.environ.get('CONFIG_FILE_PATH', config_file)
        self.config = self._load_config()
        self.running = False
        self.last_request_sent: Dict[str, datetime] = {}
        self.active_patterns: Dict[str, bool] = {}
        
        # Get MAC address for Wake-on-LAN from environment variable
        self.wol_mac_address = os.environ.get('WOL_MAC_ADDRESS')
        
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

    def _send_wol_packet(self, mac_address: str):
        """
        Send a Wake-on-LAN (WoL) packet to the specified MAC address
        
        Args:
            mac_address: MAC address of the target device
        """
        if not mac_address:
            logger.warning("No MAC address provided for Wake-on-LAN")
            return
        
        # Parse MAC address (format: xx:xx:xx:xx:xx:xx or xx-xx-xx-xx-xx-xx)
        mac = mac_address.replace('-', ':')
        mac_bytes = bytes.fromhex(mac.replace(':', ''))
        
        # Create Wake-on-LAN packet
        # 6 bytes of 0xFF followed by 16 repetitions of the MAC address
        wol_packet = b'\xff' * 6 + mac_bytes * 16
        
        try:
            # Create UDP socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            
            # Send packet to broadcast address on port 9
            sock.sendto(wol_packet, ('255.255.255.255', 9))
            logger.info(f'Wake-on-LAN packet sent to {mac_address}')
            
        except Exception as e:
            logger.error(f'Failed to send Wake-on-LAN packet: {e}')
        finally:
            sock.close()

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
        pattern = r'^(\S+) \S+ \S+ \[([^\]]+)\] "(\S+) (\S+) HTTP/\S+" (\d+) (\S+) "\S" "[^"]+"$'
        
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

    def _get_endpoint_for_status(self, rule: Dict, status_code: int) -> str:
        """
        Get the appropriate endpoint for a given status code
        
        Args:
            rule: Configuration rule
            status_code: HTTP status code
            
        Returns:
            Endpoint URL to call
        """
        # Check if there's a specific endpoint for this status code
        status_endpoint_key = f"endpoint_{status_code}"
        if status_endpoint_key in rule:
            return rule[status_endpoint_key]
        
        # Return the default endpoint if no status-specific endpoint exists
        return rule['endpoint']

    async def _check_endpoint(self, endpoint_config: Dict, status_code: int = None):
        """
        Make HTTP request to the defined endpoint
        
        Args:
            endpoint_config: Configuration for the endpoint to call
            status_code: HTTP status code (optional)
            
        Returns:
            bool: True if endpoint call was successful, False otherwise
        """
        # Determine which endpoint to use based on status code
        endpoint_url = endpoint_config['endpoint']
        if status_code is not None:
            endpoint_url = self._get_endpoint_for_status(endpoint_config, status_code)
        logger.info(f"Calling endpoint: {endpoint_url}")
        try:
            # Create a new session for each request to avoid connection pooling issues
            async with aiohttp.ClientSession() as session:
                # Make POST request to the endpoint
                async with session.post(
                    endpoint_url,
                    timeout=aiohttp.ClientTimeout(total=30),
                    headers={'User-Agent': 'nginx-endpoint-activity-monitor/1.0'},
                    data={'name': 'nginx'}
                ) as response:
                    if response.status == 200:
                        logger.info(f"Successfully called endpoint: {endpoint_url}")
                        return True
                    else:
                        logger.warning(f"Endpoint returned status code {response.status}: {endpoint_url}")
                        return True
                        
        except asyncio.TimeoutError:
            logger.error(f"Timeout calling endpoint {endpoint_url}")
            return False
        except aiohttp.ClientError as e:
            logger.error(f"Failed to call endpoint {endpoint_url}: {e}")
            return False

    def _should_call_endpoint(self, pattern: str, current_time: datetime) -> bool:
        """
        Check if we should call the endpoint based on debouncing (1 minute minimum interval)
        
        Args:
            pattern: The regex pattern that matched
            current_time: Current timestamp
            
        Returns:
            True if we should call the endpoint, False otherwise
        """
        last_seen = self.last_request_sent.get(pattern)
        if not last_seen:
            # If never seen before, we should call it
            return True
        
        # Check if 1 minutes have passed since last call
        ten_minutes = timedelta(minutes=1)
        if current_time - last_seen >= ten_minutes:
            return True
        
        return False

    async def _call_endpoint_immediately(self, endpoint_config: Dict, status_code: int = None):
        """
        Call the endpoint immediately with debouncing
        
        Args:
            endpoint_config: Configuration for the endpoint to call
            status_code: HTTP status code (optional)
            
        Returns:
            bool: True if endpoint call was successful, False otherwise
        """
        # Call the endpoint directly
        return await self._check_endpoint(endpoint_config, status_code)

    async def _process_log_line(self, line: str):
        """
        Process a single log line
        
        Args:
            line: Single nginx access log line
        """
        parsed = self._parse_nginx_log_line(line)
        if not parsed:
            return
            
        uri = parsed['uri']
        timestamp = datetime.now()
        status_code = parsed['status']
        
        # Check if this URI matches any configured pattern
        endpoint_config = self._should_check_endpoint(uri)
        if not endpoint_config:
            return
        logger.info(f"Processing log line for URI: {uri}")
        
        # Check if we should trigger the endpoint (debounced every 1 minutes)
        if self._should_call_endpoint(endpoint_config['pattern'], timestamp):
            # Mark pattern as active for immediate reporting
            self.active_patterns[endpoint_config['pattern']] = True
            # Update last seen timestamp for this endpoint
            self.last_request_sent[endpoint_config['pattern']] = timestamp
            # Call the endpoint immediately
            success = await self._call_endpoint_immediately(endpoint_config, status_code)
            # Send Wake-on-LAN packet if MAC address is configured and endpoint was unreachable
            if not success and self.wol_mac_address:
                # Add debouncing for WoL packets to prevent spamming during server startup
                wol_debounce_key = f"wol_{endpoint_config['pattern']}"
                wol_last_sent = self.last_request_sent.get(wol_debounce_key)
                wol_min_interval = timedelta(minutes=5)  # 5 minute debounce for WoL
                if not wol_last_sent or (timestamp - wol_last_sent) >= wol_min_interval:
                    self._send_wol_packet(self.wol_mac_address)
                    self.last_request_sent[wol_debounce_key] = timestamp
        else:
            logger.info(f"skipping endpoint call for {uri}")
            # Even if we don't call the endpoint, still mark as active for reporting
            self.active_patterns[endpoint_config['pattern']] = True


    async def _report_active_patterns(self):
        """
        [DEPRECATED] Old method for reporting patterns - now handled immediately in _process_log_line
        """
        # This method is no longer used in the new implementation
        pass

    async def _tail_log_file(self, log_file_path: str):
        """
        Tail a log file and process new lines as they appear
        
        Args:
            log_file_path: Path to the nginx access log file
        """
        while self.running:
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
                                await self._process_log_line(line_str)
                        else:
                            # No new data, wait a bit before checking again
                            await asyncio.sleep(0.1)
                            
            except FileNotFoundError:
                logger.warning(f"Log file not found, retrying in 5 seconds: {log_file_path}")
                await asyncio.sleep(5)
            except Exception as e:
                logger.error(f"Error tailing log file {log_file_path}: {e}")
                await asyncio.sleep(5)

    async def start(self):
        """
        Start the monitoring service
        """
        logger.info("Starting Nginx Endpoint Activity Monitor")
        self.running = True
        
        # Get log file path from environment or use default
        log_file_path = os.environ.get('NGINX_LOG_FILE', '/var/log/nginx/access.log')
        
        # Create task for log tailing only (no periodic monitoring)
        tasks = [
            self._tail_log_file(log_file_path)
        ]
        
        # Run the task
        await asyncio.gather(*tasks, return_exceptions=True)
        
        logger.info("Nginx Endpoint Activity Monitor stopped")



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