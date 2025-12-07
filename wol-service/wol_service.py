#!/usr/bin/env python3

import json
import os
import time
import regex
from flask import Flask, jsonify
from wakeonlan import send_magic_packet

app = Flask(__name__)

CONFIG_FILE = 'config.json'
LAST_REQUESTS_FILE = 'last_requests.json'
REQUEST_COOLDOWN = 300

def load_config():
    if not os.path.exists(CONFIG_FILE):
        raise FileNotFoundError(f"Config file {CONFIG_FILE} not found")
    
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)

def load_last_requests():
    if not os.path.exists(LAST_REQUESTS_FILE):
        return {}
    
    with open(LAST_REQUESTS_FILE, 'r') as f:
        return json.load(f)

def save_last_requests(last_requests):
    with open(LAST_REQUESTS_FILE, 'w') as f:
        json.dump(last_requests, f)

def should_send_wol(pattern, last_requests):
    current_time = time.time()
    
    if pattern not in last_requests:
        return True
    
    last_request_time = last_requests[pattern]
    time_diff = current_time - last_request_time
    
    return time_diff >= REQUEST_COOLDOWN

def update_last_request(pattern, last_requests):
    last_requests[pattern] = time.time()
    save_last_requests(last_requests)

def find_matching_pattern(path):
    config = load_config()
    
    for item in config:
        pattern = item['pattern']
        if regex.match(pattern, path):
            return item
    
    return None

@app.route('/<path:uri>', methods=['GET'])
def handle_request(uri):
    try:
        matching_item = find_matching_pattern(f"/{uri}")
        
        if not matching_item:
            return jsonify({"error": "No matching pattern found"}), 404
        
        pattern = matching_item['pattern']
        mac_address = matching_item['mac_address']
        
        last_requests = load_last_requests()
        
        if not should_send_wol(pattern, last_requests):
            return jsonify({"error": "WOL request already sent recently"}), 503
        
        try:
            send_magic_packet(mac_address)
            update_last_request(pattern, last_requests)
            return jsonify({"message": f"WOL packet sent to {mac_address}"})
        except Exception as e:
            return jsonify({"error": f"Failed to send WOL packet: {str(e)}"}), 500
            
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@app.route('/', methods=['GET'])
def home():
    config = load_config()
    endpoints = [item['pattern'] for item in config]
    return jsonify({
        "message": "Wake-on-LAN Service",
        "endpoints": endpoints
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)