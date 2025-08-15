#!/bin/bash

# Raspberry Pi Camera App Setup Script
# Installs dependencies for the headless camera application

echo "🚀 Raspberry Pi Camera App Setup"
echo "================================"

# Update package list
echo "📦 Updating package list..."
sudo apt-get update

# Install camera tools
echo "📷 Installing camera tools..."
if ! command -v raspistill &> /dev/null; then
    echo "Installing libraspberrypi-bin..."
    sudo apt-get install -y libraspberrypi-bin
else
    echo "Camera tools already installed"
fi

# Install Python dependencies
echo "🐍 Installing Python dependencies..."
if command -v pip3 &> /dev/null; then
    echo "Installing Google Drive API libraries..."
    pip3 install google-auth==2.23.4 google-auth-oauthlib==1.1.0 google-auth-httplib2==0.1.1 google-api-python-client==2.108.0
else
    echo "Installing pip3 and Google Drive API libraries..."
    sudo apt-get install -y python3-pip
    pip3 install google-auth==2.23.4 google-auth-oauthlib==1.1.0 google-auth-httplib2==0.1.1 google-api-python-client==2.108.0
fi

# Install additional system dependencies
echo "🔧 Installing system dependencies..."
sudo apt-get install -y ffmpeg

# Create directories
echo "📁 Creating directories..."
mkdir -p photos videos

# Set permissions
echo "🔐 Setting permissions..."
chmod 755 photos videos

# Check camera module
echo "📷 Checking camera module..."
if [ -e /dev/video0 ]; then
    echo "✅ Camera module detected"
else
    echo "⚠️  Camera module not detected"
    echo "   Make sure camera is enabled in raspi-config"
fi

# Check internet connection
echo "🌐 Checking internet connection..."
if ping -c 1 google.com &> /dev/null; then
    echo "✅ Internet connection available"
else
    echo "⚠️  No internet connection"
    echo "   Google Drive upload will not work without internet"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Place your credentials.json file in this directory"
echo "2. Run: python3 camera_app.py"
echo "3. Follow Google authentication prompts"
echo ""
echo "🔗 Google Cloud Console: https://console.cloud.google.com/"
echo "📖 Setup guide: See README.md for detailed instructions" 