#!/usr/bin/env python3

import requests
import time
from datetime import datetime

# Test the shutdown service
BASE_URL = "http://localhost:5001"

def test_endpoints():
    print("Testing Shutdown Service Endpoints")
    print("=" * 40)
    
    # Test home endpoint
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"Home endpoint: {response.status_code}")
        if response.status_code == 200:
            print(f"  Response: {response.json()}")
    except Exception as e:
        print(f"Home endpoint failed: {e}")
    
    # Test system info
    try:
        response = requests.get(f"{BASE_URL}/shutdown/system")
        print(f"System info: {response.status_code}")
        if response.status_code == 200:
            print(f"  Response: {response.json()}")
    except Exception as e:
        print(f"System info failed: {e}")
    
    # Test status when no shutdown scheduled
    try:
        response = requests.get(f"{BASE_URL}/shutdown/status")
        print(f"Status endpoint: {response.status_code}")
        if response.status_code == 200:
            print(f"  Response: {response.json()}")
    except Exception as e:
        print(f"Status endpoint failed: {e}")
    
    # Test schedule shutdown
    try:
        response = requests.post(f"{BASE_URL}/shutdown/schedule", 
                               json={"minutes": 1})
        print(f"Schedule shutdown: {response.status_code}")
        if response.status_code == 200:
            print(f"  Response: {response.json()}")
    except Exception as e:
        print(f"Schedule shutdown failed: {e}")
    
    # Test get next shutdown
    try:
        response = requests.get(f"{BASE_URL}/shutdown/next")
        print(f"Next shutdown: {response.status_code}")
        if response.status_code == 200:
            print(f"  Response: {response.json()}")
    except Exception as e:
        print(f"Next shutdown failed: {e}")
    
    # Test status after scheduling
    try:
        response = requests.get(f"{BASE_URL}/shutdown/status")
        print(f"Status after scheduling: {response.status_code}")
        if response.status_code == 200:
            print(f"  Response: {response.json()}")
    except Exception as e:
        print(f"Status after scheduling failed: {e}")

    # Test cancel shutdown
    try:
        response = requests.post(f"{BASE_URL}/shutdown/cancel")
        print(f"Cancel shutdown: {response.status_code}")
        if response.status_code == 200:
            print(f"  Response: {response.json()}")
    except Exception as e:
        print(f"Cancel shutdown failed: {e}")

if __name__ == "__main__":
    test_endpoints()