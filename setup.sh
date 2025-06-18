#!/bin/bash

# Raspberry Pi 2 Camera App Setup Script

echo "=== Raspberry Pi 2 Camera App Setup ==="
echo

# Check if running on Raspberry Pi
if ! grep -q "BCM" /proc/cpuinfo; then
    echo "Warning: This doesn't appear to be a Raspberry Pi"
    echo "Some functions may not work properly"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Update system packages
echo "Updating system packages..."
sudo apt-get update
sudo apt-get upgrade -y

# Check and install camera tools if needed
echo "Checking camera tools..."
if ! command -v raspistill &> /dev/null; then
    echo "Installing camera tools..."
    # On older Raspberry Pi OS versions, try libraspberrypi-bin
    sudo apt-get install -y libraspberrypi-bin || echo "Camera tools may already be installed or available"
else
    echo "Camera tools already available"
fi

# Install Python3 if not present
echo "Installing Python dependencies..."
sudo apt-get install -y python3

# No additional Python packages needed - using standard library only
echo "✓ No additional Python packages required"

# Create directories
echo "Creating output directories..."
mkdir -p photos
mkdir -p videos

# Set permissions
echo "Setting up permissions..."
sudo usermod -a -G video $USER

# Make the main script executable
chmod +x camera_app.py

echo
echo "=== Setup Complete! ==="
echo
echo "Next steps:"
echo "1. Enable camera module: sudo raspi-config"
echo "   -> Interface Options -> Camera -> Enable"
echo "2. Reboot the Pi: sudo reboot"
echo "3. Test camera: raspistill -o test.jpg -t 2000"
echo "4. Run the app: python3 camera_app.py"
echo
echo "Note: You may need to log out and back in for group permissions to take effect." 