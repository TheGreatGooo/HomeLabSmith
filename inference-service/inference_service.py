#!/usr/bin/env python3

import json
import os
import subprocess
import threading
import time
from datetime import datetime, timedelta
from flask import Flask, jsonify, request
import requests

app = Flask(__name__)

# Create WSGI application object for production use with Gunicorn
application = app

# Directory where model configuration files are stored
MODELS_DIR = os.environ.get('MODELS_CONFIG_DIR', os.path.expanduser("~/models/configs"))

# Load configuration
def load_config():
    config_file = 'config.json'
    if not os.path.exists(config_file):
        # Return default configuration
        return {
            "service": {
                "port": 5002,
                "host": "0.0.0.0"
            },
            "monitoring": {
                "reporting_interval_minutes": 10,
                "shutdown_check_interval_minutes": 10,
                "idle_threshold_minutes": 10,
                "active_threshold_minutes": 10
            }
        }
    
    with open(config_file, 'r') as f:
        return json.load(f)

config = load_config()

# Global variable to track last activity timestamps
last_activity_timestamps = {}

def get_running_models():
    """Get list of currently running inference models by checking systemd service status"""
    try:
        running_models = []
        # Get available models to know what models we should check
        available_models = get_available_models()
        
        # Extract model names from available models
        model_names = [model['model_name'] for model in available_models]
        
        # Check each model's systemd service status
        for model_name in model_names:
            try:
                # Execute systemctl status command to check if the service is running
                result = subprocess.run(
                    ['systemctl', 'is-active', f'model@{model_name}'],
                    capture_output=True,
                    text=True
                )
                
                # If the service is active, add it to running models
                if result.returncode == 0 and result.stdout.strip() == 'active':
                    running_models.append(model_name)
            except Exception as e:
                # If there's an error checking a specific model, continue with others
                print(f"Error checking status for model {model_name}: {e}")
                continue
        
        return running_models
    except Exception as e:
        print(f"Error getting running models: {e}")
        return []

def get_available_models():
    """
    Get list of available models from the configs directory.
    Reads configuration files from a specified directory, parses each file to extract
    the PORT value, and returns a list containing all discovered port numbers along
    with their corresponding model names and file paths.
    """
    if not os.path.exists(MODELS_DIR):
        return []
    
    # Get all files in the models directory (these represent model names)
    try:
        files = os.listdir(MODELS_DIR)
        # Filter out directories, keep only files
        model_configs = []
        
        for file in files:
            file_path = os.path.join(MODELS_DIR, file)
            if os.path.isfile(file_path):
                # Parse the configuration file to extract PORT value
                port = None
                try:
                    with open(file_path, 'r') as f:
                        for line in f:
                            if line.startswith('PORT='):
                                # Extract port value from line like PORT="8198"
                                port = line.split('=')[1].strip().strip('"')
                                break
                except Exception as e:
                    print(f"Error reading config file {file}: {e}")
                
                model_configs.append({
                    "model_name": file,
                    "file_path": file_path,
                    "port": port
                })
        
        return model_configs
    except Exception as e:
        print(f"Error reading models directory: {e}")
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
    """Shutdown a model using systemctl directly"""
    try:
        # Use systemctl to stop the model service directly
        result = subprocess.run(
            ['sudo', 'systemctl', 'stop', f'model@{model_name}'],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(f"Successfully stopped model: {model_name}")
            return True
        else:
            print(f"Error stopping model {model_name}: {result.stderr.strip()}")
            return False
    except Exception as e:
        print(f"Error stopping model {model_name}: {e}")
        return False

def check_and_shutdown_idle_models():
    """Periodically check for idle models and shut them down"""
    print("Checking for idle models...")
    
    # Get all available models
    available_models = get_available_models()
    
    # Get currently running models
    running_models = get_running_models()
    
    # Extract model names from the available models data structure
    available_model_names = [model['model_name'] for model in available_models]
    
    # Check each model that's running but not active
    for model_name in running_models:
        # Only process models that are in our available models list
        if model_name in available_model_names:
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
            available_models = get_available_models()
            
            # Get currently running models
            running_models = get_running_models()
            
            # Extract model names from the available models data structure
            available_model_names = [model['model_name'] for model in available_models]
            
            # Check which models are active (recently used)
            active_models = []
            for model in available_models:
                model_name = model['model_name']
                if is_model_active(model_name):
                    active_models.append(model_name)
            
            print(f"Reporting: Available models: {available_model_names}")
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

def systemctl_action(action, model_name):
    """Execute systemctl action on a model"""
    try:
        # Validate the action
        valid_actions = ['start', 'stop', 'restart']
        if action not in valid_actions:
            return False, f"Invalid action. Must be one of: {valid_actions}"
        
        # Validate model name (ensure it's a valid filename)
        if not model_name or '/' in model_name or '..' in model_name:
            return False, "Invalid model name"
        
        # Execute systemctl command
        result = subprocess.run(
            ['sudo', 'systemctl', action, f'model@{model_name}'],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            return True, f"Successfully {action}ed model {model_name}"
        else:
            return False, f"Failed to {action} model {model_name}: {result.stderr.strip()}"
            
    except Exception as e:
        return False, f"Error executing systemctl command: {str(e)}"

@app.route('/models', methods=['GET'])
def get_available_models_endpoint():
    """Get list of available inference models with their port information"""
    try:
        models = get_available_models()
        return jsonify({
            "status": "success",
            "models": models
        }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/models/running', methods=['GET'])
def get_running_models_endpoint():
    """Get list of currently running inference models"""
    try:
        running_models = get_running_models()
        return jsonify({
            "status": "success",
            "running_models": running_models
        }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/models/<model_name>/start', methods=['POST'])
def start_model(model_name):
    """Start an inference model"""
    try:
        success, message = systemctl_action('start', model_name)
        
        if success:
            return jsonify({
                "status": "success",
                "message": message
            }), 200
        else:
            return jsonify({
                "status": "error",
                "message": message
            }), 400
            
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/models/<model_name>/stop', methods=['POST'])
def stop_model(model_name):
    """Stop an inference model"""
    try:
        success, message = systemctl_action('stop', model_name)
        
        if success:
            return jsonify({
                "status": "success",
                "message": message
            }), 200
        else:
            return jsonify({
                "status": "error",
                "message": message
            }), 400
            
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/models/<model_name>/restart', methods=['POST'])
def restart_model(model_name):
    """Restart an inference model"""
    try:
        success, message = systemctl_action('restart', model_name)
        
        if success:
            return jsonify({
                "status": "success",
                "message": message
            }), 200
        else:
            return jsonify({
                "status": "error",
                "message": message
            }), 400
            
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/models/active', methods=['GET'])
def get_active_models():
    """Get list of models that have been active in the last 10 minutes"""
    try:
        available_models = get_available_models()
        
        # Extract model names from the available models data structure
        available_model_names = [model['model_name'] for model in available_models]
        
        active_models = []
        for model in available_models:
            model_name = model['model_name']
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
        available_models = get_available_models()
        running_models = get_running_models()
        
        # Extract model names from the available models data structure
        available_model_names = [model['model_name'] for model in available_models]
        
        idle_models = []
        for model_name in running_models:
            # Only process models that are in our available models list
            if model_name in available_model_names:
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
        available_models = get_available_models()
        running_models = get_running_models()
        
        # Extract model names from the available models data structure
        available_model_names = [model['model_name'] for model in available_models]
        
        activity_status = {}
        for model in available_models:
            model_name = model['model_name']
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
        response = get_available_models()
        
        return jsonify({
            "status": "healthy",
            "service": "Inference Model Service",
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
        "service": "Inference Model Service",
        "endpoints": {
            "GET /models": "Get list of available models",
            "GET /models/running": "Get list of running models",
            "POST /models/<model_name>/start": "Start a model",
            "POST /models/<model_name>/stop": "Stop a model",
            "POST /models/<model_name>/restart": "Restart a model",
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
    
    app.run(host='0.0.0.0', port=config['service']['port'], debug=True)