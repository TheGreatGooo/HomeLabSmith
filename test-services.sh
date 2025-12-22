#!/bin/bash

# Test script to verify Home Lab Services are properly configured

echo "Testing Home Lab Services Configuration..."

# Check if systemd service files exist

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

# Check if user exists
echo ""
echo "Checking user account..."
if id "home-lab-services" &>/dev/null; then
    echo "✓ home-lab-services user exists"
else
    echo "✗ home-lab-services user missing"
fi

# Check directories
echo ""
echo "Checking directories..."
if [ -d "/var/lib/home-lab-services" ]; then
    echo "✓ /var/lib/home-lab-services exists"
else
    echo "✗ /var/lib/home-lab-services missing"
fi

if [ -d "/home/abc/models/configs" ]; then
    echo "✓ /home/abc/models/configs exists"
else
    echo "✗ /home/abc/models/configs missing"
fi

# Check service status (only if services are enabled)
echo ""
echo "Checking service status..."

if systemctl is-enabled inference-service.service &>/dev/null; then
    echo "✓ inference-service.service is enabled"
else
    echo "✗ inference-service.service is not enabled"
fi

if systemctl is-enabled home-lab-services.service &>/dev/null; then
    echo "✓ home-lab-services.service is enabled"
else
    echo "✗ home-lab-services.service is not enabled"
fi

echo ""
echo "Test completed."