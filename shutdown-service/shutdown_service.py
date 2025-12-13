#!/usr/bin/env python3

import json
import os
import subprocess
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
                "port": 5001,
                "host": "0.0.0.0"
            },
            "shutdown": {
                "default_minutes": 1,
                "lock_file": "shutdown.lock"
            }
        }
    
    with open(config_file, 'r') as f:
        return json.load(f)

config = load_config()

# File to store scheduled shutdowns
SHUTDOWN_FILE = 'scheduled_shutdowns.json'
LOCK_FILE = config['shutdown']['lock_file']

def load_scheduled_shutdowns():
    """Load scheduled shutdowns from file"""
    if not os.path.exists(SHUTDOWN_FILE):
        return []
    
    with open(SHUTDOWN_FILE, 'r') as f:
        return json.load(f)

def save_scheduled_shutdowns(shutdowns):
    """Save scheduled shutdowns to file"""
    with open(SHUTDOWN_FILE, 'w') as f:
        json.dump(shutdowns, f)

def get_next_shutdown():
    """Get the next scheduled shutdown"""
    shutdowns = load_scheduled_shutdowns()
    if not shutdowns:
        return None
    
    # Sort by scheduled time
    sorted_shutdowns = sorted(shutdowns, key=lambda x: x['scheduled_time'])
    return sorted_shutdowns[0]

def is_shutdown_scheduled():
    """Check if there's a shutdown scheduled"""
    next_shutdown = get_next_shutdown()
    return next_shutdown is not None

def cancel_shutdown():
    """Cancel the next scheduled shutdown"""
    shutdowns = load_scheduled_shutdowns()
    if not shutdowns:
        return False
    
    # Remove the first (next) shutdown
    cancelled = shutdowns.pop(0)
    save_scheduled_shutdowns(shutdowns)
    return cancelled

def execute_shutdown():
    """Execute the shutdown command"""
    try:
        # Use sudo to execute shutdown
        result = subprocess.run(['sudo', '/sbin/shutdown', '-h', 'now'],
                               capture_output=True, text=True, check=True)
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, str(e.stderr)
    except Exception as e:
        return False, str(e)

def is_sudo_available():
    """Check if sudo is available and working"""
    try:
        result = subprocess.run(['sudo', '-n', 'true'],
                               capture_output=True, check=True)
        return True
    except subprocess.CalledProcessError:
        return False
    except Exception:
        return False

def schedule_shutdown(minutes_from_now):
    """Schedule a shutdown for specified minutes from now"""
    try:
        # Calculate the scheduled time
        scheduled_time = datetime.now() + timedelta(minutes=minutes_from_now)
        
        # Create shutdown entry
        shutdown_entry = {
            'scheduled_time': scheduled_time.isoformat(),
            'minutes_from_now': minutes_from_now,
            'created_at': datetime.now().isoformat()
        }
        
        # Load existing shutdowns
        shutdowns = load_scheduled_shutdowns()
        
        # Add new shutdown
        shutdowns.append(shutdown_entry)
        
        # Save to file
        save_scheduled_shutdowns(shutdowns)
        
        return True, f"Shutdown scheduled for {scheduled_time.strftime('%Y-%m-%d %H:%M:%S')}"
    except Exception as e:
        return False, str(e)

def get_system_uptime():
    """Get system uptime information"""
    try:
        # Get boot time
        boot_time = psutil.boot_time()
        current_time = time.time()
        uptime_seconds = current_time - boot_time
        
        # Convert to days, hours, minutes, seconds
        days = int(uptime_seconds // 86400)
        hours = int((uptime_seconds % 86400) // 3600)
        minutes = int((uptime_seconds % 3600) // 60)
        
        return {
            "days": days,
            "hours": hours,
            "minutes": minutes,
            "seconds": int(uptime_seconds % 60),
            "total_seconds": int(uptime_seconds)
        }
    except Exception as e:
        return {"error": str(e)}

@app.route('/shutdown/schedule', methods=['POST'])
def schedule_shutdown_endpoint():
    """Schedule a shutdown"""
    try:
        # Check if sudo is available
        if not is_sudo_available():
            return jsonify({
                "status": "error",
                "message": "sudo access not available - cannot schedule shutdown"
            }), 500
        
        data = request.get_json()
        minutes = data.get('minutes', config['shutdown']['default_minutes'])
        
        success, message = schedule_shutdown(minutes)
        
        if success:
            return jsonify({
                "status": "success",
                "message": message
            }), 200
        else:
            return jsonify({
                "status": "error",
                "message": message
            }), 500
            
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Invalid request: {str(e)}"
        }), 400

@app.route('/shutdown/next', methods=['GET'])
def get_next_shutdown_endpoint():
    """Get the next scheduled shutdown"""
    try:
        next_shutdown = get_next_shutdown()
        
        if next_shutdown:
            return jsonify({
                "status": "success",
                "shutdown": next_shutdown
            }), 200
        else:
            return jsonify({
                "status": "success",
                "message": "No shutdown scheduled"
            }), 200
            
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/shutdown/cancel', methods=['POST'])
def cancel_shutdown_endpoint():
    """Cancel the next scheduled shutdown"""
    try:
        cancelled = cancel_shutdown()
        
        if cancelled:
            return jsonify({
                "status": "success",
                "message": "Shutdown cancelled successfully",
                "cancelled_shutdown": cancelled
            }), 200
        else:
            return jsonify({
                "status": "error",
                "message": "No shutdown to cancel"
            }), 404
            
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/shutdown/status', methods=['GET'])
def shutdown_status():
    """Get the status of scheduled shutdowns"""
    try:
        next_shutdown = get_next_shutdown()
        has_shutdown = is_shutdown_scheduled()
        
        return jsonify({
            "status": "success",
            "has_shutdown": has_shutdown,
            "next_shutdown": next_shutdown
        }), 200
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/shutdown/system', methods=['GET'])
def system_info():
    """Get system information"""
    try:
        uptime = get_system_uptime()
        return jsonify({
            "status": "success",
            "uptime": uptime,
            "service_config": config
        }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/', methods=['GET'])
def home():
    """Home endpoint with API information"""
    return jsonify({
        "service": "Shutdown Service",
        "endpoints": {
            "POST /shutdown/schedule": "Schedule a shutdown (requires minutes in body)",
            "GET /shutdown/next": "Get the next scheduled shutdown",
            "POST /shutdown/cancel": "Cancel the next scheduled shutdown",
            "GET /shutdown/status": "Get shutdown status",
            "GET /shutdown/system": "Get system information"
        },
        "config": config
    })

if __name__ == '__main__':
    app.run(host=config['service']['host'], port=config['service']['port'], debug=True)