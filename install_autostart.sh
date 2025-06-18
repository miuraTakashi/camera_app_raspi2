#!/bin/bash

# Install Camera App as System Service

echo "=== Installing Raspberry Pi Camera App Autostart ==="
echo

# Get the current directory
CURRENT_DIR=$(pwd)
echo "Current directory: $CURRENT_DIR"

# Check if we're in the right directory
if [ ! -f "camera_app.py" ]; then
    echo "✗ Error: camera_app.py not found in current directory"
    echo "Please run this script from the camera_app_raspi2 directory"
    exit 1
fi

# Update the service file with correct paths
echo "Updating service file paths..."
sed -i "s|/home/pi/camera_app_raspi2|$CURRENT_DIR|g" camera-app.service

# Copy service file to systemd directory
echo "Installing service file..."
sudo cp camera-app.service /etc/systemd/system/

# Set proper permissions
sudo chmod 644 /etc/systemd/system/camera-app.service

# Reload systemd
echo "Reloading systemd..."
sudo systemctl daemon-reload

# Enable the service (start on boot)
echo "Enabling camera app service..."
sudo systemctl enable camera-app.service

echo
echo "=== Installation Complete! ==="
echo
echo "Service management commands:"
echo "  Start service:    sudo systemctl start camera-app.service"
echo "  Stop service:     sudo systemctl stop camera-app.service"
echo "  Restart service:  sudo systemctl restart camera-app.service"
echo "  Check status:     sudo systemctl status camera-app.service"
echo "  View logs:        sudo journalctl -u camera-app.service -f"
echo "  Disable autostart: sudo systemctl disable camera-app.service"
echo
echo "The camera app will now start automatically on boot!"
echo "Reboot to test: sudo reboot" 