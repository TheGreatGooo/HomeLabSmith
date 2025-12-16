#!/usr/bin/env python3
"""
Test script for the NGINX ConfigMap Updater service
"""

import unittest
from unittest.mock import Mock, patch
import sys
import os

# Add the service directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from nginx_configmap_updater import NGINXConfigMapUpdater

class TestNGINXConfigMapUpdater(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        # Mock the Kubernetes config loading
        with patch('nginx_configmap_updater.config.load_incluster_config'):
            with patch('nginx_configmap_updater.config.load_kube_config'):
                self.updater = NGINXConfigMapUpdater()
    
    @patch('nginx_configmap_updater.requests.get')
    def test_get_available_models_success(self, mock_get):
        """Test successful model fetching"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "models": [
                {"model_name": "test_model_1", "port": "8080"},
                {"model_name": "test_model_2", "port": "8081"}
            ]
        }
        mock_get.return_value = mock_response
        
        models = self.updater.get_available_models()
        self.assertEqual(len(models), 2)
        self.assertEqual(models[0]['model_name'], 'test_model_1')
        self.assertEqual(models[0]['port'], '8080')
    
    @patch('nginx_configmap_updater.requests.get')
    def test_get_available_models_failure(self, mock_get):
        """Test model fetching failure"""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_get.return_value = mock_response
        
        models = self.updater.get_available_models()
        self.assertEqual(len(models), 0)
    
    def test_create_nginx_location_block(self):
        """Test NGINX location block creation"""
        location_block = self.updater.create_nginx_location_block("test_model", "8080")
        self.assertIn("/test_model/", location_block)
        self.assertIn("proxy_pass http://localhost:8080/", location_block)
    
    def test_should_update_config(self):
        """Test model change detection"""
        # No previous models
        models = [{"model_name": "model1", "port": "8080"}]
        result = self.updater.should_update_config(models)
        self.assertTrue(result)
        
        # Same models
        self.updater.last_models = models
        result = self.updater.should_update_config(models)
        self.assertFalse(result)
        
        # Different models
        new_models = [{"model_name": "model2", "port": "8081"}]
        result = self.updater.should_update_config(new_models)
        self.assertTrue(result)

if __name__ == '__main__':
    unittest.main()
