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

# Create necessary directories
echo "Creating required directories..."
mkdir -p /home/abc/models/configs

# Copy service files to systemd directory (requires sudo)
echo "Copying service files to systemd directory..."
sudo cp shutdown-service/systemd/shutdown-service.service /etc/systemd/system/
sudo cp inference-service/systemd/inference-service.service /etc/systemd/system/
sudo cp home-lab-services.service /etc/systemd/system/

# Reload systemd configuration
echo "Reloading systemd configuration..."
sudo systemctl daemon-reload

# Enable services to start on boot
echo "Enabling services to start on boot..."
sudo systemctl enable shutdown-service.service
sudo systemctl enable inference-service.service
sudo systemctl enable home-lab-services.service

echo "Services installed and enabled successfully!"
echo ""
echo "To start the services now, run:"
echo "  sudo systemctl start shutdown-service.service"
echo "  sudo systemctl start inference-service.service"
echo "  sudo systemctl start home-lab-services.service"
echo ""
echo "To check service status:"
echo "  sudo systemctl status shutdown-service.service"
echo "  sudo systemctl status inference-service.service"
echo "  sudo systemctl status home-lab-services.service"
echo ""
echo "For logs:"
echo "  sudo journalctl -u shutdown-service.service -f"
echo "  sudo journalctl -u inference-service.service -f"
echo "  sudo journalctl -u home-lab-services.service -f"