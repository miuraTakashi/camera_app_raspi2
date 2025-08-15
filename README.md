# Raspberry Pi 2 Camera Application with Google Drive Upload

A lightweight Python application for Raspberry Pi 2 that provides camera functionality without requiring a GUI or desktop environment. **Automatically uploads photos and videos to Google Drive!** Perfect for headless Pi setups! Uses the old camera module with `raspistill` and `raspivid` commands.

## ✨ Features

- **🎮 Single-Key Controls**: No Enter key required - just press and go!
- **📸 Instant Photos**: SPACE key for quick photo capture
- **🎥 Video Recording**: V key to start/stop video recording with fullscreen preview
- **🕐 Timestamped Files**: Automatic naming with JST timezone (e.g., `20250610_165315.jpg`)
- **🖥️ Headless Operation**: Works without X11 or desktop environment
- **🔄 Auto-Start**: Runs automatically on boot as a foreground system service
- **⚡ Fast Capture**: Optimized for minimal delay (1-2 seconds)
- **💾 Smart Storage**: Automatic disk space monitoring and cleanup
- **🔧 Robust Error Handling**: Comprehensive troubleshooting and process management
- **☁️ Google Drive Upload**: **NEW!** Automatically uploads photos and videos to Google Drive

## 🎮 Controls

| Key | Action |
|-----|--------|
| **SPACE** | Take photo |
| **v** | Start/stop video recording |
| **p** | Toggle camera preview |
| **s** | Show status and disk space |
| **h** | Open temporary shell session |
| **q** or **ESC** | Quit and return to shell |

## 📋 Requirements

### Hardware
- Raspberry Pi 2
- Raspberry Pi Camera Module (old version)
- Keyboard for controls
- **Internet connection** for Google Drive upload

### Software
- Raspberry Pi OS
- Python 3.x
- Google Drive API libraries
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

### 3. Set Up Google Drive API (Required for Upload)
```bash
# Google Cloud ConsoleでOAuth 2.0クライアントIDを作成
# 1. https://console.cloud.google.com/ にアクセス
# 2. 新しいプロジェクトを作成
# 3. Google Drive APIを有効化
# 4. OAuth 2.0クライアントIDを作成
# 5. credentials.jsonファイルをダウンロード
# 6. プロジェクトディレクトリに配置

# 認証ファイルを配置
cp ~/Downloads/credentials.json ~/camera_app_raspi2/
```

### 4. Test the Application
```bash
python3 camera_app.py
```

### 5. Set Up Autostart (Foreground Mode)
```bash
./install_foreground.sh
sudo reboot
```

## ☁️ Google Drive Setup

### Step 1: Create Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable Google Drive API
4. Go to "Credentials" section

### Step 2: Create OAuth 2.0 Client
1. Click "Create Credentials" → "OAuth 2.0 Client IDs"
2. Application type: "Desktop application"
3. Download the `credentials.json` file
4. Place it in your project directory

### Step 3: First Run Authentication
1. Run the camera app: `python3 camera_app.py`
2. A browser window will open for Google authentication
3. Sign in with your Google account
4. Grant permission to access Google Drive
5. The app will save authentication token for future use

### Step 4: Verify Upload Folder
- Photos and videos will be uploaded to the specified Google Drive folder
- Folder ID: `1ffVLu6KyQTnz_9ppsqVIGkCXXLdT90U7`
- You can change this in `camera_app.py` by modifying `FOLDER_ID`

## 📂 File Structure

```
camera_app_raspi2/
├── camera_app.py                    # Main application with Google Drive upload
├── cleanup_files.py                 # Standalone disk cleanup utility
├── requirements.txt                 # Python dependencies
├── setup.sh                        # Setup script
├── camera-app-foreground.service   # Systemd service for foreground operation
├── install_foreground.sh           # Foreground autostart installation
├── credentials.json                 # Google Drive API credentials (you need to add this)
├── token.pickle                     # Google Drive authentication token (auto-generated)
├── README.md                       # This file
├── .gitignore                      # Git ignore file
├── photos/                         # Auto-created for photos
└── videos/                         # Auto-created for videos
```

## ⚙️ Configuration

The application uses optimized settings for fast performance:

- **Photo Resolution**: 1920x1080 pixels (Full HD)
- **Photo Quality**: 90% (optimized for speed)
- **Video Resolution**: 1920x1080 pixels (Full HD)
- **Video Frame Rate**: 30 FPS
- **Capture Time**: 0.1 seconds for instant photos
- **Timezone**: JST (Japan Standard Time)
- **Google Drive**: Automatic upload after capture

## 🎯 Usage Examples

### Manual Operation
```bash
python3 camera_app.py
# Press SPACE for photos, V for video, Q to quit
# Photos and videos are automatically uploaded to Google Drive
```

### Autostart Service (Foreground)
```bash
# Check if running
sudo systemctl status camera-app-foreground.service

# View logs
sudo journalctl -u camera-app-foreground.service -f

# Stop/start manually
sudo systemctl stop camera-app-foreground.service
sudo systemctl start camera-app-foreground.service
```

### Standalone Disk Cleanup
```bash
python3 cleanup_files.py
# Interactive cleanup utility for managing storage space
```

## 📁 Output Files

Files are automatically saved with timestamp format in JST and uploaded to Google Drive:

- **Photos**: `photos/20250610_165315.jpg` → ☁️ Google Drive
- **Videos**: `videos/20250610_165315.h264` → ☁️ Google Drive

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

# Check camera processes
pgrep -f raspistill
pgrep -f raspivid
```

### Google Drive Upload Issues
```bash
# Check credentials file
ls -la credentials.json

# Check internet connection
ping google.com

# Check authentication token
ls -la token.pickle

# Remove token to re-authenticate
rm token.pickle
```

### Service Not Starting
```bash
# Check service status
sudo systemctl status camera-app-foreground.service

# Check logs
sudo journalctl -u camera-app-foreground.service
```

### Permission Issues
```bash
# Add user to video group
sudo usermod -a -G video $USER
# Log out and back in
```

### Disk Space Issues
```bash
# Check disk usage
df -h

# Run cleanup utility
python3 cleanup_files.py
```

## 🎨 Clean & Simple

This application is designed to be:
- **Lightweight** - Minimal dependencies
- **Fast** - Optimized for quick response
- **Reliable** - Robust error handling and auto-restart
- **User-friendly** - Simple single-key controls
- **Headless-ready** - Perfect for server/IoT deployments
- **Cloud-connected** - Automatic Google Drive backup
- **Storage-aware** - Automatic disk space management

Perfect for security cameras, time-lapse photography, or any automated camera application with cloud backup! 📷☁️✨

## 📝 Recent Updates

- ✅ **Google Drive Upload**: Automatic upload of photos and videos to Google Drive
- ✅ **Terminal Output Fix**: Resolved oblique/strange text display issues
- ✅ **Enhanced Process Management**: Better camera process cleanup and error handling
- ✅ **JST Timestamping**: Japan Standard Time support for file naming
- ✅ **Smart Storage**: Automatic disk space monitoring and cleanup
- ✅ **Foreground Service**: Improved autostart with keyboard input support 