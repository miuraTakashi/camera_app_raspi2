#!/bin/bash

# Install Camera App as Foreground Service

echo "=== Installing Raspberry Pi Camera App (Foreground) ==="
echo

# Get the current directory and user
CURRENT_DIR=$(pwd)
CURRENT_USER=$(whoami)
echo "Current directory: $CURRENT_DIR"
echo "Current user: $CURRENT_USER"

# Check if we're in the right directory
if [ ! -f "camera_app.py" ]; then
    echo "✗ Error: camera_app.py not found in current directory"
    echo "Please run this script from the camera_app_raspi2 directory"
    exit 1
fi

# Stop and disable the background service if it exists
echo "Stopping background service (if running)..."
sudo systemctl stop camera-app.service 2>/dev/null
sudo systemctl disable camera-app.service 2>/dev/null

# Update the foreground service file with correct paths and user
echo "Updating foreground service file paths..."
sed -i "s|/home/pi/camera_app_raspi2|$CURRENT_DIR|g" camera-app-foreground.service
sed -i "s|User=pi|User=$CURRENT_USER|g" camera-app-foreground.service
sed -i "s|Group=pi|Group=$CURRENT_USER|g" camera-app-foreground.service

# Copy service file to systemd directory
echo "Installing foreground service file..."
sudo cp camera-app-foreground.service /etc/systemd/system/

# Set proper permissions
sudo chmod 644 /etc/systemd/system/camera-app-foreground.service

# Reload systemd
echo "Reloading systemd..."
sudo systemctl daemon-reload

# Enable the foreground service
echo "Enabling camera app foreground service..."
sudo systemctl enable camera-app-foreground.service

echo
echo "=== Installation Complete! ==="
echo
echo "The camera app will now run in FOREGROUND on the main console (tty1)"
echo "You will have full keyboard control:"
echo "  SPACE - Take Photo"
echo "  v     - Start/Stop Video"
echo "  p     - Toggle Preview"
echo "  s     - Show Status"
echo "  q/ESC - Quit (will restart automatically)"
echo
echo "Service management commands:"
echo "  Check status:     sudo systemctl status camera-app-foreground.service"
echo "  View logs:        sudo journalctl -u camera-app-foreground.service -f"
echo "  Stop service:     sudo systemctl stop camera-app-foreground.service"
echo "  Disable autostart: sudo systemctl disable camera-app-foreground.service"
echo
echo "Reboot to test: sudo reboot"
echo "After reboot, the camera app will appear on your main console!" 