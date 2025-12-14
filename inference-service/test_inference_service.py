#!/usr/bin/env python3

import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add the inference service directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from inference_service import get_available_models, get_running_models, systemctl_action

class TestInferenceService(unittest.TestCase):
    
    @patch('inference_service.os.path.exists')
    @patch('inference_service.os.listdir')
    @patch('inference_service.os.path.isfile')
    @patch('builtins.open', new_callable=unittest.mock.mock_open, read_data='PORT="8198"')
    def test_get_available_models(self, mock_open, mock_isfile, mock_listdir, mock_exists):
        """Test getting available models with port information"""
        mock_exists.return_value = True
        mock_listdir.return_value = ['model1.conf', 'model2.conf']
        mock_isfile.return_value = True
        
        models = get_available_models()
        self.assertEqual(len(models), 2)
        self.assertEqual(models[0]['model_name'], 'model1.conf')
        self.assertEqual(models[0]['port'], '8198')
        self.assertIn('model1.conf', models[0]['file_path'])
    
    @patch('inference_service.os.path.exists')
    @patch('inference_service.os.listdir')
    def test_get_available_models_empty(self, mock_listdir, mock_exists):
        """Test getting available models when directory is empty"""
        mock_exists.return_value = True
        mock_listdir.return_value = []
        
        models = get_available_models()
        self.assertEqual(models, [])
    
    @patch('inference_service.os.path.exists')
    def test_get_available_models_nonexistent(self, mock_exists):
        """Test getting available models when directory doesn't exist"""
        mock_exists.return_value = False
        
        models = get_available_models()
        self.assertEqual(models, [])
    
    @patch('inference_service.subprocess.run')
    def test_systemctl_action_success(self, mock_run):
        """Test successful systemctl action"""
        mock_run.return_value = MagicMock(returncode=0, stdout='', stderr='')
        
        success, message = systemctl_action('start', 'test-model')
        self.assertTrue(success)
        self.assertIn('Successfully started model test-model', message)
    
    @patch('inference_service.subprocess.run')
    def test_systemctl_action_failure(self, mock_run):
        """Test failed systemctl action"""
        mock_run.return_value = MagicMock(returncode=1, stdout='', stderr='Error occurred')
        
        success, message = systemctl_action('start', 'test-model')
        self.assertFalse(success)
        self.assertIn('Failed to start model test-model', message)

if __name__ == '__main__':
    unittest.main()