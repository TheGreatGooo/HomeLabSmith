#!/usr/bin/env python3

import json
import os
import subprocess
from flask import Flask, jsonify, request

app = Flask(__name__)

# Create WSGI application object for production use with Gunicorn
application = app

# Directory where model configuration files are stored
MODELS_DIR = os.environ.get('MODELS_CONFIG_DIR', os.path.expanduser("~/models/configs"))

def get_available_models():
    """Get list of available models from the configs directory"""
    if not os.path.exists(MODELS_DIR):
        return []
    
    # Get all files in the models directory (these represent model names)
    try:
        files = os.listdir(MODELS_DIR)
        # Filter out directories, keep only files
        models = [f for f in files if os.path.isfile(os.path.join(MODELS_DIR, f))]
        return models
    except Exception as e:
        print(f"Error reading models directory: {e}")
        return []

def get_running_models():
    """Get list of currently running models by checking systemctl status"""
    try:
        # Get all available models first
        available_models = get_available_models()
        
        running_models = []
        for model in available_models:
            # Check if the service is active
            result = subprocess.run(
                ['systemctl', 'is-active', f'model@{model}'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0 and result.stdout.strip() == 'active':
                running_models.append(model)
        
        return running_models
    except Exception as e:
        print(f"Error checking running models: {e}")
        return []

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
def get_available_models():
    """Get list of available inference models"""
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
            "POST /models/<model_name>/restart": "Restart a model"
        }
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)