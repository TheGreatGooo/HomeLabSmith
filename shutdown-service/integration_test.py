#!/usr/bin/env python3

"""
Integration test for shutdown service demonstrating the complete workflow.
This script simulates the full functionality of scheduling, checking, and canceling shutdowns.
"""

import subprocess
import time
import requests
from datetime import datetime

def run_command(command):
    """Run a shell command and return result"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def test_shutdown_workflow():
    """Test the complete shutdown workflow"""
    print("Testing Shutdown Service Workflow")
    print("=" * 40)
    
    # Test 1: Check if service is running
    try:
        response = requests.get("http://localhost:5001/", timeout=5)
        if response.status_code == 200:
            print("✓ Service is running")
        else:
            print(f"✗ Service not responding: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Service not accessible: {e}")
        return False
    
    # Test 2: Check initial status (no shutdown scheduled)
    try:
        response = requests.get("http://localhost:5001/shutdown/status")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Initial status check: {data}")
        else:
            print(f"✗ Status check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Status check error: {e}")
        return False
    
    # Test 3: Schedule a shutdown
    try:
        response = requests.post("http://localhost:5001/shutdown/schedule", 
                               json={"minutes": 2})
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Shutdown scheduled: {data}")
        else:
            print(f"✗ Failed to schedule shutdown: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Schedule error: {e}")
        return False
    
    # Test 4: Check next shutdown
    try:
        response = requests.get("http://localhost:5001/shutdown/next")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Next shutdown check: {data}")
        else:
            print(f"✗ Next shutdown check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Next shutdown error: {e}")
        return False
    
    # Test 5: Check status after scheduling
    try:
        response = requests.get("http://localhost:5001/shutdown/status")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Status after scheduling: {data}")
        else:
            print(f"✗ Status check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Status error: {e}")
        return False
    
    # Test 6: Cancel the shutdown
    try:
        response = requests.post("http://localhost:5001/shutdown/cancel")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Shutdown cancelled: {data}")
        else:
            print(f"✗ Failed to cancel shutdown: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Cancel error: {e}")
        return False
    
    # Test 7: Final status check
    try:
        response = requests.get("http://localhost:5001/shutdown/status")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Final status check: {data}")
        else:
            print(f"✗ Final status check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Final status error: {e}")
        return False
    
    print("\n✓ All tests passed successfully!")
    return True

if __name__ == "__main__":
    test_shutdown_workflow()