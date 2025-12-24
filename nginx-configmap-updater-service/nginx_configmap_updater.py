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
        
        # Set up Open WebUI URL
        self.open_webui_url = self.config.get('open_webui_url', 'http://localhost:8080')
        
        # Track last successful update to avoid unnecessary updates
        self.last_models = []
        self.last_update_time = 0
        
        # Store the config.json content to avoid unnecessary updates
        self.last_config_json = []
        
    def load_config(self):
        """Load configuration from environment or default values"""
        return {
            'inference_service_url': os.environ.get('INFERENCE_SERVICE_URL', 'http://localhost:5002'),
            'open_webui_url': os.environ.get('OPEN_WEBUI_URL', 'http://localhost:8080'),
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
        location_blocks = []
        for model in models:
            model_name = model.get('model_name')
            port = model.get('port')
            if model_name and port:
                location_blocks.append(self.create_nginx_location_block(model_name, port))
        return '\n'.join(location_blocks)
    
    def generate_config_json_entries(self, models):
        """Generate config.json entries for NGINX location patterns and endpoints"""
        config_entries = []
        for model in models:
            model_name = model.get('model_name')
            # Pattern should be the location path (e.g., /model_name/)
            pattern = f"/{model_name}/"
            # Endpoint should be http://<MODEL_MONITOR_SERVICE_URL>/models/<model_name>/report
            endpoint = f"{self.inference_service_url}/models/{model_name}/report"
            config_entries.append({
                "pattern": pattern,
                "endpoint": endpoint,
                "endpoint_502": f"{self.inference_service_url}/models/{model_name}/start"
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
    
    def send_models_to_open_webui(self, models):
        """Send all models to Open WebUI via its API"""
        if not models:
            logger.info("No models to send to Open WebUI")
            return True
            
        try:
            # Prepare the OpenAI API configuration for Open WebUI
            hostname = os.environ.get('NGINX_ROUTER_HOSTNAME', 'nginx-service.inference-manager')
            
            # Create base URLs for each model
            base_urls = []
            api_keys = []
            configs = {}
            
            for i, model in enumerate(models):
                model_name = model.get('model_name')
                port = model.get('port')
                if model_name and port:
                    # Create the base URL for this model's OpenAI API endpoint
                    base_url = f"http://{hostname}/{model_name}/v1"
                    base_urls.append(base_url)
                    api_keys.append("*")
                    
                    # Create config for this model (simplified structure)
                    configs[str(i)] = {
                        "enable": True,
                        "tags": [],
                        "prefix_id": "",
                        "model_ids": []
                    }
            
            # Send to Open WebUI API with the required structure
            headers = {'Content-Type': 'application/json'}
            payload = {
                "ENABLE_OPENAI_API": True,
                "OPENAI_API_BASE_URLS": base_urls,
                "OPENAI_API_KEYS": api_keys,
                "OPENAI_API_CONFIGS": configs
            }
            
            response = requests.post(
                f"{self.open_webui_url}/api/v1/openai/config",
                json=payload,
                headers=headers,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                logger.info(f"Successfully sent model configurations to Open WebUI for {len(models)} models")
                return True
            else:
                logger.error(f"Failed to send model configurations to Open WebUI: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending model configurations to Open WebUI: {e}")
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
                        # Also send models to Open WebUI
                        webui_success = self.send_models_to_open_webui(models)
                        if webui_success:
                            logger.info("Models successfully sent to Open WebUI")
                        else:
                            logger.error("Failed to send models to Open WebUI")
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