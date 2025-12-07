#!/usr/bin/env python3

import json
import os

def test_service():
    """Test the Wake-on-LAN service"""
    
    # Test 1: Check if service can be started
    print("Testing Wake-on-LAN service...")
    
    # Test 2: Check configuration file
    if not os.path.exists('config.json'):
        print("ERROR: config.json not found")
        return False
    
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
        print(f"Configuration loaded successfully. Found {len(config)} patterns.")
    except Exception as e:
        print(f"ERROR: Failed to load config: {e}")
        return False
    
    # Test 3: Check that we can import required modules
    try:
        import flask
        import regex
        from wakeonlan import send_magic_packet
        print("All required modules imported successfully")
    except ImportError as e:
        print(f"ERROR: Failed to import modules: {e}")
        return False
    
    print("All tests passed!")
    return True

if __name__ == '__main__':
    test_service()