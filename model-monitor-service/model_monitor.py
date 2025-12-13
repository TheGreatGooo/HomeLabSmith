#!/usr/bin/env python3

import json
import os
import requests
import threading
import time
from datetime import datetime, timedelta
from flask import Flask, jsonify, request
import psutil

app = Flask(__name__)

# Load configuration
def load_config():
    config_file = 'config.json'
    if not os.path.exists(config_file):
        # Return default configuration
        return {
            "service": {
                "port": 5003,
                "host": "0.0.0.0"
            },
            "monitoring": {
                "reporting_interval_minutes": 10,
                "shutdown_check_interval_minutes": 10,
                "idle_threshold_minutes": 30,
                "active_threshold_minutes": 10
            },
            "inference_service": {
                "base_url": "http://localhost:5002"
            }
        }
    
    with open(config_file, 'r') as f:
        return json.load(f)

config = load_config()

# Global variable to track last activity timestamps
last_activity_timestamps = {}

def get_inference_models():
    """Get list of available inference models from the inference service"""
    try:
        response = requests.get(f"{config['inference_service']['base_url']}/models")
        if response.status_code == 200:
            data = response.json()
            return data.get('models', [])
        else:
            print(f"Error fetching models: {response.status_code} - {response.text}")
            return []
    except Exception as e:
        print(f"Error connecting to inference service: {e}")
        return []

def get_running_models():
    """Get list of currently running models from the inference service"""
    try:
        response = requests.get(f"{config['inference_service']['base_url']}/models/running")
        if response.status_code == 200:
            data = response.json()
            return data.get('running_models', [])
        else:
            print(f"Error fetching running models: {response.status_code} - {response.text}")
            return []
    except Exception as e:
        print(f"Error connecting to inference service: {e}")
        return []

def update_last_activity(model_name):
    """Update the last activity timestamp for a model"""
    last_activity_timestamps[model_name] = datetime.now()

def get_last_activity(model_name):
    """Get the last activity timestamp for a model"""
    return last_activity_timestamps.get(model_name, None)

def is_model_active(model_name):
    """Check if a model has been active within the last X minutes"""
    last_activity = get_last_activity(model_name)
    if not last_activity:
        return False
    
    threshold = timedelta(minutes=config['monitoring']['active_threshold_minutes'])
    return datetime.now() - last_activity <= threshold

def is_model_idle(model_name):
    """Check if a model has been idle for more than the threshold"""
    last_activity = get_last_activity(model_name)
    if not last_activity:
        # If no activity recorded, consider it idle
        return True
    
    threshold = timedelta(minutes=config['monitoring']['idle_threshold_minutes'])
    return datetime.now() - last_activity > threshold

def shutdown_model(model_name):
    """Shutdown a model using the inference service"""
    try:
        response = requests.post(f"{config['inference_service']['base_url']}/models/{model_name}/stop")
        if response.status_code == 200:
            print(f"Successfully stopped model: {model_name}")
            return True
        else:
            print(f"Error stopping model {model_name}: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"Error connecting to inference service while stopping {model_name}: {e}")
        return False

def check_and_shutdown_idle_models():
    """Periodically check for idle models and shut them down"""
    print("Checking for idle models...")
    
    # Get all available models
    available_models = get_inference_models()
    
    # Get currently running models
    running_models = get_running_models()
    
    # Check each model that's running but not active
    for model_name in running_models:
        if is_model_idle(model_name):
            print(f"Model {model_name} has been idle for too long, shutting down...")
            shutdown_model(model_name)
        else:
            print(f"Model {model_name} is still active")

def reporting_thread():
    """Thread to periodically report model activity"""
    while True:
        try:
            # Get all available models
            available_models = get_inference_models()
            
            # Get currently running models
            running_models = get_running_models()
            
            # Check which models are active (recently used)
            active_models = []
            for model_name in available_models:
                if is_model_active(model_name):
                    active_models.append(model_name)
            
            print(f"Reporting: Available models: {available_models}")
            print(f"Reporting: Running models: {running_models}")
            print(f"Reporting: Active models (last 10 minutes): {active_models}")
            
            # Wait for the reporting interval
            time.sleep(config['monitoring']['reporting_interval_minutes'] * 60)
        except Exception as e:
            print(f"Error in reporting thread: {e}")
            time.sleep(60)  # Wait a minute before retrying

def shutdown_check_thread():
    """Thread to periodically check for and shutdown idle models"""
    while True:
        try:
            check_and_shutdown_idle_models()
            
            # Wait for the shutdown check interval
            time.sleep(config['monitoring']['shutdown_check_interval_minutes'] * 60)
        except Exception as e:
            print(f"Error in shutdown check thread: {e}")
            time.sleep(60)  # Wait a minute before retrying

@app.route('/models/active', methods=['GET'])
def get_active_models():
    """Get list of models that have been active in the last 10 minutes"""
    try:
        available_models = get_inference_models()
        active_models = []
        
        for model_name in available_models:
            if is_model_active(model_name):
                active_models.append(model_name)
        
        return jsonify({
            "status": "success",
            "active_models": active_models,
            "timestamp": datetime.now().isoformat()
        }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/models/idle', methods=['GET'])
def get_idle_models():
    """Get list of models that have been idle for more than 30 minutes"""
    try:
        available_models = get_inference_models()
        running_models = get_running_models()
        
        idle_models = []
        for model_name in running_models:
            if is_model_idle(model_name):
                idle_models.append(model_name)
        
        return jsonify({
            "status": "success",
            "idle_models": idle_models,
            "timestamp": datetime.now().isoformat()
        }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/models/activity', methods=['GET'])
def get_model_activity():
    """Get activity status for all models"""
    try:
        available_models = get_inference_models()
        running_models = get_running_models()
        
        activity_status = {}
        for model_name in available_models:
            last_activity = get_last_activity(model_name)
            is_active = is_model_active(model_name)
            is_idle = is_model_idle(model_name)
            
            activity_status[model_name] = {
                "last_activity": last_activity.isoformat() if last_activity else None,
                "is_active": is_active,
                "is_idle": is_idle
            }
        
        return jsonify({
            "status": "success",
            "activity_status": activity_status,
            "timestamp": datetime.now().isoformat()
        }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/models/<model_name>/report', methods=['POST'])
def report_model_activity(model_name):
    """Report that a model has been used (updates last activity timestamp)"""
    try:
        update_last_activity(model_name)
        
        return jsonify({
            "status": "success",
            "message": f"Activity reported for model {model_name}",
            "timestamp": datetime.now().isoformat()
        }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        # Try to connect to inference service
        response = requests.get(f"{config['inference_service']['base_url']}/models", timeout=5)
        inference_service_status = "healthy" if response.status_code == 200 else "unhealthy"
        
        return jsonify({
            "status": "healthy",
            "service": "Model Monitor Service",
            "inference_service": inference_service_status,
            "timestamp": datetime.now().isoformat()
        }), 200
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/', methods=['GET'])
def home():
    """Home endpoint with API information"""
    return jsonify({
        "service": "Model Monitor Service",
        "endpoints": {
            "GET /models/active": "Get list of active models (used in last 10 minutes)",
            "GET /models/idle": "Get list of idle models (not used for more than 30 minutes)",
            "GET /models/activity": "Get activity status for all models",
            "POST /models/<model_name>/report": "Report that a model has been used",
            "GET /health": "Health check endpoint"
        },
        "config": config
    })

if __name__ == '__main__':
    # Start monitoring threads in background
    reporting_thread_obj = threading.Thread(target=reporting_thread, daemon=True)
    reporting_thread_obj.start()
    
    shutdown_check_thread_obj = threading.Thread(target=shutdown_check_thread, daemon=True)
    shutdown_check_thread_obj.start()
    
    app.run(host=config['service']['host'], port=config['service']['port'], debug=False)