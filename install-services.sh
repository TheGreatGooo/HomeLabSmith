#!/bin/bash

# Home Lab Services Installation Script
# This script installs and configures the systemd services for shutdown and inference services

set -e  # Exit on any error

echo "Installing Home Lab Services..."

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo "This script should not be run as root"
   exit 1
fi

# Create dedicated user and group for home lab services if they don't exist
echo "Creating dedicated user and group for Home Lab Services..."
if ! id "home-lab-services" &>/dev/null; then
    sudo useradd -r -s /bin/false -d /var/lib/home-lab-services home-lab-services
    echo "Created user: home-lab-services"
else
    echo "User home-lab-services already exists"
fi

# Create necessary directories for services
echo "Creating required directories..."
sudo mkdir -p /var/lib/home-lab-services
sudo mkdir -p /config/models
sudo chown home-lab-services:home-lab-services /var/lib/home-lab-services
sudo chown home-lab-services:home-lab-services /config/models

# Create directories for service code if they don't exist
echo "Creating service code directories..."
sudo mkdir -p /config/HomeLabSmith/shutdown-service
sudo mkdir -p /config/HomeLabSmith/inference-service

# Create virtual environments for services
echo "Creating virtual environments..."
sudo -u home-lab-services python3 -m venv /var/lib/home-lab-services/shutdown-venv
sudo -u home-lab-services python3 -m venv /var/lib/home-lab-services/inference-venv

# Install requirements in virtual environments
echo "Installing requirements in virtual environments..."
sudo -u home-lab-services /var/lib/home-lab-services/shutdown-venv/bin/pip install flask psutil gunicorn
sudo -u home-lab-services /var/lib/home-lab-services/inference-venv/bin/pip install flask gunicorn

# Copy service files to systemd directory (requires sudo)
echo "Copying service files to systemd directory..."
sudo cp shutdown-service/systemd/shutdown-service.service /etc/systemd/system/
sudo cp inference-service/systemd/inference-service.service /etc/systemd/system/

# Copy Python service files to expected locations
echo "Copying Python service files..."
sudo cp shutdown-service/shutdown_service.py /config/HomeLabSmith/shutdown-service/
sudo cp inference-service/inference_service.py /config/HomeLabSmith/inference-service/

# Set proper permissions on service files
sudo chown home-lab-services:home-lab-services /config/HomeLabSmith/shutdown-service/shutdown_service.py
sudo chown home-lab-services:home-lab-services /config/HomeLabSmith/inference-service/inference_service.py

# Reload systemd configuration
echo "Reloading systemd configuration..."
sudo systemctl daemon-reload

# Enable services to start on boot
echo "Enabling services to start on boot..."
sudo systemctl enable shutdown-service.service
sudo systemctl enable inference-service.service

echo "Services installed and enabled successfully!"
echo ""
echo "To start the services now, run:"
echo "  sudo systemctl start shutdown-service.service"
echo "  sudo systemctl start inference-service.service"
echo ""
echo "To check service status:"
echo "  sudo systemctl status shutdown-service.service"
echo "  sudo systemctl status inference-service.service"
echo ""
echo "For logs:"
echo "  sudo journalctl -u shutdown-service.service -f"
echo "  sudo journalctl -u inference-service.service -f"
echo ""
echo "Environment variable MODELS_CONFIG_DIR is set to /config/models in the inference service."
echo "This can be overridden by setting the environment variable before starting the service."