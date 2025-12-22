#!/bin/bash

# Verify Home Lab Services Configuration
# This script checks that the systemd services are properly configured

echo "Verifying Home Lab Services configuration..."

# Check if service files exist
echo "Checking service files..."

if [ -f "/etc/systemd/system/inference-service.service" ]; then
    echo "✓ inference-service.service exists"
else
    echo "✗ inference-service.service missing"
fi

if [ -f "/etc/systemd/system/home-lab-services.service" ]; then
    echo "✓ home-lab-services.service exists"
else
    echo "✗ home-lab-services.service missing"
fi

# Check systemd configuration
echo ""
echo "Checking systemd configuration..."
sudo systemctl daemon-reload > /dev/null 2>&1 && echo "✓ Systemd configuration reloaded successfully" || echo "✗ Failed to reload systemd configuration"

# List services
echo ""
echo "Available Home Lab Services:"
sudo systemctl list-unit-files | grep -E "(shutdown|inference|home-lab)" || echo "No Home Lab services found"

# Check if services are enabled
echo ""
echo "Service Enablement Status:"
sudo systemctl is-enabled inference-service.service 2>/dev/null && echo "✓ inference-service.service is enabled" || echo "✗ inference-service.service is not enabled"
sudo systemctl is-enabled home-lab-services.service 2>/dev/null && echo "✓ home-lab-services.service is enabled" || echo "✗ home-lab-services.service is not enabled"

echo ""
echo "Verification complete!"