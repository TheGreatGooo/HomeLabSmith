#!/usr/bin/env python3
"""
Test script to verify that duplicate location entries are properly handled
"""

import sys
import os
import unittest
from unittest.mock import Mock, patch

# Add the service directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from nginx_configmap_updater import NGINXConfigMapUpdater

class TestDuplicateFix(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        # Mock the Kubernetes config loading
        with patch('nginx_configmap_updater.config.load_incluster_config'):
            with patch('nginx_configmap_updater.config.load_kube_config'):
                self.updater = NGINXConfigMapUpdater()
    
    def test_no_duplicate_locations_created(self):
        """Test that no duplicate location entries are created in the nginx config"""
        # Create a mock existing nginx.conf similar to the one in the issue
        existing_conf = """events {
		    worker_connections 1024;
		}

		http {
		    include       /etc/nginx/mime.types;
		    default_type  application/octet-stream;
		    
		    access_log /var/log/nginx/access.log;
		    
		    server {

		            location /gpt-oss-XB-Q4_K---Medium/ {
		                proxy_pass http://inference.server:8194/;
		                proxy_set_header Host $host;
		                proxy_set_header X-Real-IP $remote_addr;
		                proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
		                proxy_set_header X-Forwarded-Proto $scheme;
		            }

		            location /mistral3-14B-Q4_K---Medium/ {
		                proxy_pass http://inference.server:8200/;
		                proxy_set_header Host $host;
		                proxy_set_header X-Real-IP $remote_addr;
		                proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
		                proxy_set_header X-Forwarded-Proto $scheme;
		            }

		            location /llama-13B-Q8_0/ {
		                proxy_pass http://inference.server:8090/;
		                proxy_set_header Host $host;
		                proxy_set_header X-Real-IP $remote_addr;
		                proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
		                proxy_set_header X-Forwarded-Proto $scheme;
		            }

		            location /gpu-deepseek2-671B-IQ2_XXS---2.0625-bpw/ {
		                proxy_pass http://inference.server:8094/;
		                proxy_set_header Host $host;
		                proxy_set_header X-Real-IP $remote_addr;
		                proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
		                proxy_set_header X-Forwarded-Proto $scheme;
		            }
		        location / {
		            root   /usr/share/nginx/html;
		            index  index.html index.htm;
		        }
		        listen 80;
		        server_name localhost;
		    }
		}
		daemon off;
		pid /run/nginx.pid;
		user abc abc;"""

        # Mock the configmap response
        mock_configmap = Mock()
        mock_configmap.data = {
            'nginx.conf': existing_conf
        }
        
        # Mock the Kubernetes API call
        with patch.object(self.updater.api_instance, 'read_namespaced_config_map', return_value=mock_configmap):
            # Test with models that would create duplicates (same names as existing)
            models = [
                {"model_name": "gpt-oss-XB-Q4_K---Medium", "port": "8195"},  # Should replace existing
                {"model_name": "mistral3-14B-Q4_K---Medium", "port": "8201"},  # Should replace existing
                {"model_name": "llama-13B-Q8_0", "port": "8091"},  # Should replace existing
                {"model_name": "gpu-deepseek2-671B-IQ2_XXS---2.0625-bpw", "port": "8095"},  # Should replace existing
                {"model_name": "new-model", "port": "8096"}  # Should be added
            ]
            
            # Generate new config
            new_config = self.updater.generate_nginx_config(models)
            
            # Verify that each location appears exactly once
            location_count = new_config.count("location /gpt-oss-XB-Q4_K---Medium/")
            self.assertEqual(location_count, 1, "There should be exactly one location /gpt-oss-XB-Q4_K---Medium/ block")
            
            location_count = new_config.count("location /mistral3-14B-Q4_K---Medium/")
            self.assertEqual(location_count, 1, "There should be exactly one location /mistral3-14B-Q4_K---Medium/ block")
            
            location_count = new_config.count("location /llama-13B-Q8_0/")
            self.assertEqual(location_count, 1, "There should be exactly one location /llama-13B-Q8_0/ block")
            
            location_count = new_config.count("location /gpu-deepseek2-671B-IQ2_XXS---2.0625-bpw/")
            self.assertEqual(location_count, 1, "There should be exactly one location /gpu-deepseek2-671B-IQ2_XXS---2.0625-bpw/ block")
            
            # Verify the new model was added
            location_count = new_config.count("location /new-model/")
            self.assertEqual(location_count, 1, "There should be exactly one location /new-model/ block")
            
            # Verify that the ports were updated correctly
            self.assertIn("proxy_pass http://localhost:8195/", new_config)
            self.assertIn("proxy_pass http://localhost:8201/", new_config)
            self.assertIn("proxy_pass http://localhost:8091/", new_config)
            self.assertIn("proxy_pass http://localhost:8095/", new_config)
            
            print("Test passed: No duplicate location entries found in generated config")

if __name__ == '__main__':
    unittest.main()