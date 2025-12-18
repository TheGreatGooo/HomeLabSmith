#!/usr/bin/env python3
"""
Test script to verify duplicate location handling in NGINX ConfigMap Updater service
"""

import sys
import os
import unittest
from unittest.mock import Mock, patch

# Add the service directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from nginx_configmap_updater import NGINXConfigMapUpdater

class TestDuplicateHandling(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        # Mock the Kubernetes config loading
        with patch('nginx_configmap_updater.config.load_incluster_config'):
            with patch('nginx_configmap_updater.config.load_kube_config'):
                self.updater = NGINXConfigMapUpdater()
    
    def test_duplicate_location_handling(self):
        """Test that duplicate locations are properly replaced"""
        # Create a mock existing nginx.conf with duplicate locations
        existing_conf = """events {
    worker_connections 1024;
}

http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;
    
    server {
        listen 80;
        server_name localhost;
        
        location /api/ {
            proxy_pass http://backend-service:8080/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }
        
        location /model1/ {
            proxy_pass http://localhost:8080/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }
    }
}"""
        
        # Mock the configmap response
        mock_configmap = Mock()
        mock_configmap.data = {
            'nginx.conf': existing_conf
        }
        
        # Mock the Kubernetes API call
        with patch.object(self.updater.api_instance, 'read_namespaced_config_map', return_value=mock_configmap):
            # Test with models that would create duplicates
            models = [
                {"model_name": "model1", "port": "8081"},  # This should replace the existing one
                {"model_name": "model2", "port": "8082"}   # This should be added
            ]
            
            # Generate new config
            new_config = self.updater.generate_nginx_config(models)
            
            # Verify that the duplicate location was replaced (model1 should now use port 8081)
            self.assertIn("proxy_pass http://localhost:8081/", new_config)
            # Verify that the new location was added (model2)
            self.assertIn("location /model2/", new_config)
            # Verify that the old location is no longer there (or replaced)
            self.assertIn("location /model1/", new_config)
            
            # Count occurrences to make sure we don't have duplicates
            location_count = new_config.count("location /model1/")
            self.assertEqual(location_count, 1, "There should be exactly one location /model1/ block")

if __name__ == '__main__':
    unittest.main()