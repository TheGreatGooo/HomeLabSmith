#!/usr/bin/env python3

import json
import os
import time
import requests
import yaml
from kubernetes import client, config
from kubernetes.client.rest import ApiException
import logging
import threading

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NGINXConfigMapUpdater:
    def __init__(self):
        # Load configuration
        self.config = self.load_config()
        
        # Initialize Kubernetes client
        try:
            config.load_incluster_config()  # For running inside a pod
        except:
            config.load_kube_config()  # For local development
        
        self.api_instance = client.CoreV1Api()
        
        # Set up inference service URL
        self.inference_service_url = self.config.get('inference_service_url', 'http://localhost:5002')
        
        # Track last successful update to avoid unnecessary updates
        self.last_models = []
        self.last_update_time = 0
        
        # Store the config.json content to avoid unnecessary updates
        self.last_config_json = []
        
    def load_config(self):
        """Load configuration from environment or default values"""
        return {
            'inference_service_url': os.environ.get('INFERENCE_SERVICE_URL', 'http://localhost:5002'),
            'configmap_name': os.environ.get('CONFIGMAP_NAME', 'nginx-config-map'),
            'configmap_namespace': os.environ.get('CONFIGMAP_NAMESPACE', 'default'),
            'check_interval': int(os.environ.get('CHECK_INTERVAL', '30')),
            'max_retries': int(os.environ.get('MAX_RETRIES', '3')),
            'retry_delay': int(os.environ.get('RETRY_DELAY', '5')),
            'health_check_interval': int(os.environ.get('HEALTH_CHECK_INTERVAL', '60'))
        }
    
    def get_available_models(self):
        """Fetch available models from inference service with retry logic"""
        for attempt in range(self.config['max_retries']):
            try:
                response = requests.get(
                    f"{self.inference_service_url}/models",
                    timeout=10
                )
                if response.status_code == 200:
                    data = response.json()
                    models = data.get('models', [])
                    logger.info(f"Successfully fetched {len(models)} models from inference service")
                    return models
                else:
                    logger.warning(f"Failed to fetch models (attempt {attempt + 1}): {response.status_code} - {response.text}")
            except Exception as e:
                logger.warning(f"Error connecting to inference service (attempt {attempt + 1}): {e}")
            
            if attempt < self.config['max_retries'] - 1:
                time.sleep(self.config['retry_delay'])
        
        logger.error("Failed to fetch models after all retries")
        return []
    
    def create_nginx_location_block(self, model_name, port):
        """Create NGINX location block for a model"""
        # Get hostname from environment variable or default to localhost
        hostname = os.environ.get('PROXY_HOSTNAME', 'localhost')
        return f"""
            location /{model_name}/ {{
                proxy_pass http://{hostname}:{port}/;
                proxy_set_header Host $host;
                proxy_set_header X-Real-IP $remote_addr;
                proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
                proxy_set_header X-Forwarded-Proto $scheme;
            }}"""
    
    def generate_nginx_config(self, models):
        """Generate complete NGINX configuration with location blocks for all models"""
        # Read the existing configmap to get base configuration
        try:
            configmap = self.api_instance.read_namespaced_config_map(
                name=self.config['configmap_name'],
                namespace=self.config['configmap_namespace']
            )
            
            # Get the existing nginx.conf content
            existing_nginx_conf = configmap.data.get('nginx.conf', '')
            
            # Parse existing configuration to find the server block
            lines = existing_nginx_conf.split('\n')
            server_block_start = -1
            server_block_end = -1
            
            # Find the server block
            for i, line in enumerate(lines):
                if 'server {' in line:
                    server_block_start = i
                elif server_block_start != -1 and '}' in line and not line.strip().startswith('//'):
                    server_block_end = i
                    break
            
            # Extract the server block content
            server_block_content = []
            if server_block_start != -1 and server_block_end != -1:
                server_block_content = lines[server_block_start:server_block_end+1]
            
            # Create new location blocks for each model
            location_blocks = []
            for model in models:
                model_name = model.get('model_name')
                port = model.get('port')
                if model_name and port:
                    location_blocks.append(self.create_nginx_location_block(model_name, port))
            
            # Build the new configuration
            new_config_lines = []
            in_server_block = False
            server_block_processed = False
            
            for i, line in enumerate(lines):
                if 'server {' in line:
                    in_server_block = True
                    new_config_lines.append(line)
                    # Add location blocks after the server block starts
                    for location_block in location_blocks:
                        new_config_lines.append(location_block)
                elif in_server_block and '}' in line and not line.strip().startswith('//'):
                    in_server_block = False
                    new_config_lines.append(line)
                    server_block_processed = True
                elif not in_server_block:
                    new_config_lines.append(line)
                elif in_server_block and server_block_processed:
                    # Skip the original server block content after we've added our location blocks
                    continue
                else:
                    new_config_lines.append(line)
            
            # If we didn't find a server block, add one at the end
            if not server_block_processed:
                # Find the end of the http block
                http_block_end = -1
                for i, line in enumerate(lines):
                    if 'http {' in line:
                        http_block_end = i
                if http_block_end != -1:
                    # Insert server block after http block
                    new_config_lines = lines[:http_block_end+1] + [
                        "    server {",
                        "        listen 80;",
                        "        server_name localhost;",
                        ""
                    ] + location_blocks + [
                        "    }",
                        ""
                    ] + lines[http_block_end+1:]
                else:
                    # If no http block, just add the server block at the end
                    new_config_lines = lines + [
                        "    server {",
                        "        listen 80;",
                        "        server_name localhost;",
                        ""
                    ] + location_blocks + [
                        "    }",
                        ""
                    ]
            
            return '\n'.join(new_config_lines)
            
        except Exception as e:
            logger.error(f"Error reading existing configmap: {e}")
            # Return a basic configuration if we can't read the existing one
            return self.generate_basic_nginx_config(models)
    
    def generate_basic_nginx_config(self, models):
        """Generate a basic NGINX configuration if we can't read the existing one"""
        location_blocks = []
        for model in models:
            model_name = model.get('model_name')
            port = model.get('port')
            if model_name and port:
                location_blocks.append(self.create_nginx_location_block(model_name, port))
        
        return f"""events {{
    worker_connections 1024;
}}

http {{
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;
    
    server {{
        listen 80;
        server_name localhost;
        
        location / {{
            root   /usr/share/nginx/html;
            index  index.html index.htm;
        }}
        
        location /api/ {{
            proxy_pass http://backend-service:8080/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }}
        
        {''.join(location_blocks)}
    }}
}}"""
    
    def generate_config_json_entries(self, models):
        """Generate config.json entries for NGINX location patterns and endpoints"""
        config_entries = []
        for model in models:
            model_name = model.get('model_name')
            # Pattern should be the location path (e.g., /model_name/)
            pattern = f"/{model_name}/"
            # Endpoint should be http://<INFERENCE_SERVICE_URL>:5002/models/<model_name>/start
            endpoint = f"{self.inference_service_url}/models/{model_name}/start"
            config_entries.append({
                "pattern": pattern,
                "endpoint": endpoint
            })
        return config_entries
    
    def should_update_config_json(self, models):
        """Check if we should update the config.json content based on model changes"""
        # Generate current config entries
        current_config = self.generate_config_json_entries(models)
        
        # If no previous config or different from previous, update needed
        if not self.last_config_json:
            return True
        
        # Compare the config entries
        return current_config != self.last_config_json
    
    def update_configmap(self, models):
        """Update the NGINX ConfigMap with new configuration"""
        try:
            # Generate new configuration
            new_nginx_conf = self.generate_nginx_config(models)
            
            # Generate new config.json entries
            config_entries = self.generate_config_json_entries(models)
            
            # Read existing configmap
            configmap = self.api_instance.read_namespaced_config_map(
                name=self.config['configmap_name'],
                namespace=self.config['configmap_namespace']
            )
            
            # Update the nginx.conf content
            configmap.data['nginx.conf'] = new_nginx_conf
            
            # Update the config.json content
            configmap.data['config.json'] = json.dumps(config_entries, indent=4)
            
            # Update the configmap
            api_response = self.api_instance.patch_namespaced_config_map(
                name=self.config['configmap_name'],
                namespace=self.config['configmap_namespace'],
                body=configmap
            )
            
            logger.info("Successfully updated NGINX ConfigMap")
            # Store the current config entries for future comparison
            self.last_config_json = config_entries
            return True
            
        except ApiException as e:
            logger.error(f"Exception when updating ConfigMap: {e}")
            return False
        except Exception as e:
            logger.error(f"Error updating ConfigMap: {e}")
            return False
    
    def should_update_config(self, models):
        """Check if we should update the config based on model changes"""
        # If no models, no update needed
        if not models:
            return False
            
        # If no previous models, update needed
        if not self.last_models:
            return True
            
        # Compare models - if different, update needed
        current_model_names = {model.get('model_name') for model in models}
        last_model_names = {model.get('model_name') for model in self.last_models}
        
        return current_model_names != last_model_names
    
    def run(self):
        """Main loop to continuously monitor and update"""
        logger.info("Starting NGINX ConfigMap Updater service")
        
        while True:
            try:
                # Get available models from inference service
                models = self.get_available_models()
                logger.info(f"Found {len(models)} models")
                
                # Update ConfigMap with new configuration if needed
                if models and self.should_update_config(models):
                    success = self.update_configmap(models)
                    if success:
                        logger.info("ConfigMap updated successfully")
                        self.last_models = models
                        self.last_update_time = time.time()
                    else:
                        logger.error("Failed to update ConfigMap")
                elif not models:
                    logger.info("No models found")
                else:
                    logger.info("No changes in models, skipping ConfigMap update")
                
                # Wait for next check
                time.sleep(self.config['check_interval'])
                
            except KeyboardInterrupt:
                logger.info("Service stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                time.sleep(self.config['retry_delay'])

if __name__ == "__main__":
    service = NGINXConfigMapUpdater()
    service.run()
