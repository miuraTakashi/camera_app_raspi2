# Raspberry Pi 2 Camera Application (Headless)

A lightweight Python application for Raspberry Pi 2 that provides camera functionality without requiring a GUI or desktop environment. Perfect for headless Pi setups! Uses the old camera module with `raspistill` and `raspivid` commands.

## ✨ Features

- **🎮 Single-Key Controls**: No Enter key required - just press and go!
- **📸 Instant Photos**: SPACE key for quick photo capture
- **🎥 Video Recording**: V key to start/stop video recording with fullscreen preview
- **🕐 Timestamped Files**: Automatic naming with date-time format (e.g., `20250610_165315.jpg`)
- **🖥️ Headless Operation**: Works without X11 or desktop environment
- **🔄 Auto-Start**: Runs automatically on boot as a system service
- **⚡ Fast Capture**: Optimized for minimal delay (1-2 seconds)

## 🎮 Controls

| Key | Action |
|-----|--------|
| **SPACE** | Take photo |
| **v** | Start/stop video recording |
| **p** | Toggle camera preview |
| **s** | Show status |
| **q** or **ESC** | Quit |

## 📋 Requirements

### Hardware
- Raspberry Pi 2
- Raspberry Pi Camera Module (old version)
- Keyboard for controls

### Software
- Raspberry Pi OS
- Python 3.x (standard library only)
- Camera tools (`raspistill`, `raspivid`)
- **No GUI/X11 required!**

## 🚀 Quick Start

### 1. Enable Camera Module
```bash
sudo raspi-config
# Navigate to Interface Options > Camera > Enable
sudo reboot
```

### 2. Install Dependencies
```bash
./setup.sh
```

### 3. Test the Application
```bash
python3 camera_app.py
```

### 4. Set Up Autostart (Optional)
```bash
./install_autostart.sh
sudo reboot
```

## 📂 File Structure

```
camera_app_raspi2/
├── camera_app.py          # Main headless application
├── requirements.txt       # Dependencies (none needed)
├── setup.sh              # Setup script
├── camera-app.service     # Systemd service file
├── install_autostart.sh   # Autostart installation
├── README.md             # This file
├── photos/               # Auto-created for photos
└── videos/               # Auto-created for videos
```

## ⚙️ Configuration

The application uses optimized settings for fast performance:

- **Photo Resolution**: 1920x1080 pixels (Full HD)
- **Photo Quality**: 90% (optimized for speed)
- **Video Resolution**: 1920x1080 pixels (Full HD)
- **Video Frame Rate**: 30 FPS
- **Capture Time**: 0.1 seconds for instant photos

## 🎯 Usage Examples

### Manual Operation
```bash
python3 camera_app.py
# Press SPACE for photos, V for video, Q to quit
```

### Autostart Service
```bash
# Check if running
sudo systemctl status camera-app.service

# View logs
sudo journalctl -u camera-app.service -f

# Stop/start manually
sudo systemctl stop camera-app.service
sudo systemctl start camera-app.service
```

## 📁 Output Files

Files are automatically saved with timestamp format:

- **Photos**: `photos/20250610_165315.jpg`
- **Videos**: `videos/20250610_165315.h264`

### Convert Videos to MP4
```bash
# Install ffmpeg
sudo apt-get install ffmpeg

# Convert to MP4
ffmpeg -i videos/20250610_165315.h264 -c copy videos/20250610_165315.mp4
```

## 🔧 Troubleshooting

### Camera Not Working
```bash
# Test camera directly
raspistill -o test.jpg -t 2000
```

### Service Not Starting
```bash
# Check service status
sudo systemctl status camera-app.service

# Check logs
sudo journalctl -u camera-app.service
```

### Permission Issues
```bash
# Add user to video group
sudo usermod -a -G video $USER
# Log out and back in
```

## 🎨 Clean & Simple

This application is designed to be:
- **Lightweight** - No unnecessary dependencies
- **Fast** - Optimized for quick response
- **Reliable** - Robust error handling and auto-restart
- **User-friendly** - Simple single-key controls
- **Headless-ready** - Perfect for server/IoT deployments

Perfect for security cameras, time-lapse photography, or any automated camera application! 📷✨ 