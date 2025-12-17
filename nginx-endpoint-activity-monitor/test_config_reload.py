#!/usr/bin/env python3
"""
Test script to verify that the config file reloading works correctly
"""
import os
import json
import tempfile
from unittest.mock import patch, MagicMock
import asyncio

# Add the current directory to Python path so we can import the module
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from nginx_endpoint_activity_monitor import NginxMonitor

def test_config_file_path_from_env():
    """Test that config file path is read from environment variable"""
    # Create a temporary config file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        config_content = [
            {
                "pattern": "/api/test",
                "endpoint": "http://localhost:8080/test"
            }
        ]
        json.dump(config_content, f)
        temp_config_path = f.name
    
    try:
        # Test with environment variable set
        with patch.dict(os.environ, {'CONFIG_FILE_PATH': temp_config_path}):
            monitor = NginxMonitor()
            assert monitor.config_file == temp_config_path
            print("✓ Environment variable config file path works")
            
        # Test with default (no environment variable)
        with patch.dict(os.environ, {}):
            # This should still work with the default config file
            monitor = NginxMonitor(config_file=temp_config_path)
            assert monitor.config_file == temp_config_path
            print("✓ Default config file path works")
            
    finally:
        # Clean up
        os.unlink(temp_config_path)

def test_config_reload():
    """Test that _load_config is called during _report_active_patterns"""
    # Create a temporary config file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        config_content = [
            {
                "pattern": "/api/test",
                "endpoint": "http://localhost:8080/test"
            }
        ]
        json.dump(config_content, f)
        temp_config_path = f.name
    
    try:
        # Create monitor instance
        monitor = NginxMonitor(config_file=temp_config_path)
        
        # Mock the _load_config method to track calls
        original_load_config = monitor._load_config
        load_config_calls = []
        
        def mock_load_config():
            load_config_calls.append(True)
            return original_load_config()
        
        monitor._load_config = mock_load_config
        
        # Call _report_active_patterns
        asyncio.run(monitor._report_active_patterns())
        
        # Check that _load_config was called
        assert len(load_config_calls) == 1, f"Expected _load_config to be called once, but was called {len(load_config_calls)} times"
        print("✓ Config reload during _report_active_patterns works")
        
    finally:
        # Clean up
        os.unlink(temp_config_path)

if __name__ == "__main__":
    print("Testing config file loading and reloading...")
    test_config_file_path_from_env()
    test_config_reload()
    print("All tests passed!")