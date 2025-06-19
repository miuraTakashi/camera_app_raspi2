#!/usr/bin/env python3
"""
Raspberry Pi 2 Camera Application - Headless Version
Works without GUI - uses terminal for controls
- Camera preview shows on screen (if available) or can be disabled
- Take photos with Enter key
- Record videos with 'v' + Enter
- Uses raspistill and raspivid for old camera modules
"""

import subprocess
import threading
import time
from datetime import datetime, timezone, timedelta
import os
import sys
import select
import termios
import tty
import shutil
import glob
import builtins

class TerminalOutputManager:
    """Manages terminal output to handle raw mode properly"""
    def __init__(self, camera_app):
        self.camera_app = camera_app
        self.original_print = builtins.print
        
    def managed_print(self, *args, **kwargs):
        """Print function that handles terminal raw mode"""
        if hasattr(self.camera_app, 'quiet_mode') and self.camera_app.quiet_mode:
            # Check if this is a forced output or error
            force = kwargs.pop('force', False)
            if not force and not any('✗' in str(arg) or '❌' in str(arg) or '⚠' in str(arg) for arg in args):
                return
                
        if hasattr(self.camera_app, 'old_settings') and self.camera_app.old_settings:
            try:
                # Temporarily restore normal terminal
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.camera_app.old_settings)
                self.original_print(*args, **kwargs, flush=True)
                # Restore raw mode
                tty.setraw(sys.stdin.fileno())
            except:
                # Fallback to original print
                self.original_print(*args, **kwargs, flush=True)
        else:
            self.original_print(*args, **kwargs, flush=True)

class RPiCameraHeadless:
    def __init__(self):
        """Initialize camera app"""
        print("Raspberry Pi Camera App - Headless Version")
        print("=" * 50)
        
        # Store original print function for restoration
        self.original_print = print
        
        # Replace built-in print with our safe version after initialization
        self._setup_safe_printing = False
        
        # Set up directories
        home_dir = os.path.expanduser("~")
        base_dir = os.path.join(home_dir, "camera_app_raspi2")
        
        self.photos_dir = os.path.join(base_dir, "photos")
        self.videos_dir = os.path.join(base_dir, "videos")
        
        # Store original terminal settings
        self.old_settings = None
        
        # State variables
        self.preview_process = None
        self.video_process = None
        self.recording = False
        self.preview_active = False
        self.running = True
        self.quiet_mode = False
        
        # Create directories
        try:
            os.makedirs(self.photos_dir, exist_ok=True)
            os.makedirs(self.videos_dir, exist_ok=True)
            print(f"Working directory: {os.getcwd()}")
            
            # Test absolute paths
            abs_photos = os.path.abspath(self.photos_dir)
            abs_videos = os.path.abspath(self.videos_dir)
            
            print(f"Photos directory: {self.photos_dir}")
            print(f"Videos directory: {self.videos_dir}")
            
            # Check disk space
            self.check_disk_space()
            
        except PermissionError as e:
            print(f"✗ ERROR: Permission denied creating directories: {e}")
            print(f"   Try running with sudo or check parent directory permissions")
            sys.exit(1)
        except Exception as e:
            print(f"✗ ERROR: Failed to create directories: {e}")
            print(f"   Attempted to create: {self.photos_dir}")
            print(f"   Attempted to create: {self.videos_dir}")
            sys.exit(1)
        
    def safe_print(self, *args, **kwargs):
        """Safe print function that handles terminal mode properly"""
        message = ' '.join(str(arg) for arg in args)
        
        # Check if we should output (respect quiet mode unless forced)
        force_output = kwargs.pop('force', False)
        if self.quiet_mode and not force_output:
            return
            
        # Handle terminal formatting
        if hasattr(self, 'old_settings') and self.old_settings:
            try:
                # Temporarily restore normal terminal mode
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.old_settings)
                self.original_print(message, **kwargs, flush=True)
                # Restore raw mode
                tty.setraw(sys.stdin.fileno())
            except:
                # Fallback - print with manual formatting
                self.original_print(message.replace('\n', '\r\n'), **kwargs, flush=True)
        else:
            self.original_print(message, **kwargs, flush=True)
    
    def get_timestamp(self):
        """Generate timestamp in format: YYYYMMDD_HHMMSS using JST (Japan Standard Time)"""
        # JST is UTC+9
        jst = timezone(timedelta(hours=9))
        return datetime.now(jst).strftime("%Y%m%d_%H%M%S")
    
    def check_disk_space(self):
        """Check available disk space and warn if low"""
        try:
            # Get disk usage for current directory
            total, used, free = shutil.disk_usage(os.getcwd())
            
            # Convert to MB
            free_mb = free // (1024 * 1024)
            total_mb = total // (1024 * 1024)
            used_percent = (used / total) * 100
            
            self.safe_print(f"💾 Disk space: {free_mb}MB free / {total_mb}MB total ({used_percent:.1f}% used)")
            
            # Warning thresholds
            if free_mb < 100:  # Less than 100MB
                self.safe_print("🚨 CRITICAL: Very low disk space!")
                self.safe_print("   Consider cleaning up old files")
                return False
            elif free_mb < 500:  # Less than 500MB
                self.safe_print("⚠️ WARNING: Low disk space")
                self.safe_print("   You may want to clean up soon")
                return True
            else:
                self.safe_print("✅ Disk space OK")
                return True
                
        except Exception as e:
            self.safe_print(f"⚠️ Could not check disk space: {e}")
            return True

    def cleanup_old_files(self, max_photos=100, max_videos=20):
        """Clean up old files to free space"""
        self.safe_print("🧹 Cleaning up old files...")
        
        try:
            # Clean up old photos
            photos = glob.glob(os.path.join(self.photos_dir, "*.jpg"))
            if len(photos) > max_photos:
                # Sort by modification time (oldest first)
                photos.sort(key=os.path.getmtime)
                to_remove = photos[:-max_photos]  # Keep only the newest max_photos
                
                for photo in to_remove:
                    try:
                        os.remove(photo)
                        self.safe_print(f"   🗑️ Removed old photo: {os.path.basename(photo)}")
                    except:
                        pass
                        
                self.safe_print(f"   📸 Kept {max_photos} newest photos, removed {len(to_remove)} old ones")
            
            # Clean up old videos
            videos = glob.glob(os.path.join(self.videos_dir, "*.h264"))
            if len(videos) > max_videos:
                # Sort by modification time (oldest first)
                videos.sort(key=os.path.getmtime)
                to_remove = videos[:-max_videos]  # Keep only the newest max_videos
                
                for video in to_remove:
                    try:
                        # Videos are large, show size before removing
                        size = os.path.getsize(video) // (1024 * 1024)  # MB
                        os.remove(video)
                        self.safe_print(f"   🗑️ Removed old video: {os.path.basename(video)} ({size}MB)")
                    except:
                        pass
                        
                self.safe_print(f"   🎥 Kept {max_videos} newest videos, removed {len(to_remove)} old ones")
            
            return True
            
        except Exception as e:
            self.safe_print(f"⚠️ Error during cleanup: {e}")
            return False
    
    def start_preview(self):
        """Start camera preview using raspistill"""
        try:
            # Kill any existing preview
            self.stop_preview()
            
            # Build preview command
            preview_cmd = ['raspistill', '-t', '0', '-f']  # -f for fullscreen
            
            # Add recording indicator if recording
            if self.recording:
                # Add red dot annotation in top-left corner
                preview_cmd.extend([
                    '-a', '12',  # Enable custom text annotation
                    '-ae', '16,0xff0000,0x808000',  # Text size 16, red text, transparent background
                    '-at', '●REC'  # Red dot and REC text
                ])
            
            # Start preview with raspistill
            self.preview_process = subprocess.Popen(
                preview_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            self.preview_active = True
            
        except Exception as e:
            if not self.quiet_mode:
                self.safe_print(f"✗ Error starting preview: {e}")
                self.safe_print("  Preview will be disabled, but photo/video capture will still work")
    
    def stop_preview(self):
        """Stop camera preview"""
        if self.preview_process:
            try:
                # First try gentle termination
                self.preview_process.terminate()
                try:
                    self.preview_process.wait(timeout=2)
                    self.safe_print("   📷 Preview terminated gracefully")
                except subprocess.TimeoutExpired:
                    # Force kill if it doesn't stop
                    self.safe_print("   ⚡ Force killing preview process")
                    self.preview_process.kill()
                    self.preview_process.wait(timeout=1)
            except Exception as e:
                self.safe_print(f"   ⚠️ Error stopping preview: {e}")
                # Force kill any remaining processes
                try:
                    subprocess.run(['sudo', 'pkill', '-f', 'raspistill'], timeout=5)
                except:
                    pass
            finally:
                self.preview_process = None
        
        # Double-check no raspistill processes are running
        try:
            result = subprocess.run(['pgrep', '-f', 'raspistill'], capture_output=True, text=True)
            if result.returncode == 0 and result.stdout:
                self.safe_print(f"   ⚠️ Found lingering raspistill processes: {result.stdout.strip()}")
                self.safe_print("   🔧 Cleaning up...")
                subprocess.run(['sudo', 'pkill', '-9', '-f', 'raspistill'], timeout=5)
        except:
            pass
            
        self.preview_active = False
    
    def take_photo(self):
        """Take a photo using raspistill"""
        timestamp = self.get_timestamp()
        filename = os.path.join(self.photos_dir, f"{timestamp}.jpg")
        
        # Always show debug info for photo attempts
        self.print_formatted(f"\n📸 Taking photo...", force_output=True)
        self.print_formatted(f"   Target file: {filename}", force_output=True)
        self.print_formatted(f"   Photos dir exists: {os.path.exists(self.photos_dir)}", force_output=True)
        self.print_formatted(f"   Photos dir writable: {os.access(self.photos_dir, os.W_OK)}", force_output=True)
        self.print_formatted(f"   Current working dir: {os.getcwd()}", force_output=True)
        
        try:
            # Temporarily stop preview
            was_active = self.preview_active
            if was_active:
                self.stop_preview()
            
            # Start with SIMPLE command that matches your working test
            # We'll use basic parameters first, then add complexity if needed
            cmd = [
                'raspistill', 
                '-o', filename,
                '-t', '2000'  # 2 seconds like your test command
            ]
            
            self.print_formatted(f"   Running command: {' '.join(cmd)}", force_output=True)
            self.print_formatted(f"   Working directory: {os.getcwd()}", force_output=True)
            
            # Run with more verbose output
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            self.print_formatted(f"   Return code: {result.returncode}", force_output=True)
            if result.stdout:
                self.print_formatted(f"   Stdout: {result.stdout}", force_output=True)
            if result.stderr:
                self.print_formatted(f"   Stderr: {result.stderr}", force_output=True)
            
            if result.returncode == 0:
                # Check if file was actually created
                if os.path.exists(filename):
                    size = os.path.getsize(filename)
                    self.print_formatted(f"✅ Photo saved: {filename}", force_output=True)
                    self.print_formatted(f"   File size: {size/1024:.1f} KB", force_output=True)
                    
                    # Test different optimizations one by one
                    self.print_formatted(f"   📁 Full path: {os.path.abspath(filename)}", force_output=True)
                    
                else:
                    self.print_formatted(f"❌ Command succeeded but file not found: {filename}", force_output=True)
                    self.print_formatted(f"   Check if file was created elsewhere...", force_output=True)
                    # Look for any jpg files created recently
                    recent_files = glob.glob("*.jpg") + glob.glob("/home/*/camera_app_raspi2/*.jpg")
                    if recent_files:
                        self.print_formatted(f"   Recent JPG files found: {recent_files}", force_output=True)
            else:
                # Always show camera errors, even in quiet mode
                self.print_formatted(f"❌ Camera command failed - Return code: {result.returncode}", force_output=True)
                if result.stderr:
                    self.print_formatted(f"   Error details: {result.stderr.strip()}", force_output=True)
                
                # Specific error code handling
                if result.returncode == 64:
                    self.print_formatted("\n🔧 ERROR CODE 64 - Camera Initialization Failed", force_output=True)
                    self.print_formatted("   This usually means the camera hardware cannot be detected.", force_output=True)
                    self.print_formatted("   But since 'raspistill -o test.jpg' works, this might be a parameter issue.", force_output=True)
                    self.print_formatted("   Troubleshooting steps:", force_output=True)
                    self.print_formatted("   1. Try running the exact same command manually:", force_output=True)
                    self.print_formatted(f"      cd {os.getcwd()}", force_output=True)
                    self.print_formatted(f"      {' '.join(cmd)}", force_output=True)
                    self.print_formatted("   2. Check if preview is interfering", force_output=True)
                    self.print_formatted("   3. Check file permissions in target directory", force_output=True)
                elif result.returncode == 1:
                    self.print_formatted("\n🔧 ERROR CODE 1 - General Camera Error", force_output=True)
                    self.print_formatted("   Try: sudo modprobe bcm2835-v4l2", force_output=True)
                elif result.returncode == 70:
                    self.print_formatted("\n🔧 ERROR CODE 70 - Software Error", force_output=True)
                    self.print_formatted("   Camera software issue. Try: sudo apt-get update && sudo apt-get install --reinstall libraspberrypi-bin", force_output=True)
                elif result.returncode == 130:
                    self.print_formatted("\n🔧 ERROR CODE 130 - Interrupted", force_output=True)
                    self.print_formatted("   Camera command was interrupted", force_output=True)
                
                if "not found" in result.stderr.lower():
                    self.print_formatted("   📦 Install camera tools: sudo apt-get install libraspberrypi-bin", force_output=True)
                elif "permission" in result.stderr.lower():
                    self.print_formatted(f"   🔐 Check permissions: sudo chown -R $USER:$USER {self.photos_dir}", force_output=True)
                elif "busy" in result.stderr.lower():
                    self.print_formatted("   📷 Camera busy - close other camera applications", force_output=True)
                    self.print_formatted("   Try: sudo pkill -f raspistill", force_output=True)
                elif "timeout" in result.stderr.lower():
                    self.print_formatted("   ⏱️ Camera timeout - check hardware connection", force_output=True)
            
            # Restart preview quickly
            if was_active:
                time.sleep(0.5)  # Give more time for camera to be ready
                self.start_preview()
                
        except subprocess.TimeoutExpired:
            self.print_formatted("❌ Photo capture timed out", force_output=True)
        except FileNotFoundError:
            self.print_formatted("❌ raspistill command not found", force_output=True)
            self.print_formatted("   Install with: sudo apt-get install libraspberrypi-bin", force_output=True)
        except Exception as e:
            self.print_formatted(f"❌ Unexpected error taking photo: {e}", force_output=True)
            import traceback
            traceback.print_exc()
    
    def start_video_recording(self):
        """Start video recording using raspivid"""
        if self.recording:
            self.safe_print("⚠️ Already recording!")
            return
        
        timestamp = self.get_timestamp()
        filename = os.path.join(self.videos_dir, f"{timestamp}.h264")
        
        # Always show debug info for video recording
        self.safe_print(f"\n🎥 Starting video recording...")
        self.safe_print(f"   Target file: {filename}")
        self.safe_print(f"   Videos dir exists: {os.path.exists(self.videos_dir)}")
        self.safe_print(f"   Videos dir writable: {os.access(self.videos_dir, os.W_OK)}")
        
        # Check for existing raspivid processes
        try:
            result = subprocess.run(['pgrep', '-f', 'raspivid'], capture_output=True, text=True)
            if result.returncode == 0 and result.stdout:
                self.safe_print(f"⚠️ Found existing raspivid processes: {result.stdout.strip()}")
                self.safe_print("🔧 Cleaning up existing video processes...")
                subprocess.run(['sudo', 'pkill', '-9', '-f', 'raspivid'], timeout=5)
                time.sleep(1)  # Give time for cleanup
        except:
            pass
        
        try:
            # Stop preview first (raspivid will handle its own preview)
            self.stop_preview()
            
            # Start with simpler command first, then add complexity if needed
            cmd = [
                'raspivid', 
                '-o', filename, 
                '-t', '0',  # Continuous recording
                '-f'  # Fullscreen preview
            ]
            
            self.safe_print(f"   Running command: {' '.join(cmd)}")
            
            # Start recording process
            self.video_process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Give it a moment to start
            time.sleep(0.5)
            
            # Check if process is still running (didn't immediately fail)
            if self.video_process.poll() is None:
                self.safe_print("✅ Video recording started successfully")
                self.recording = True
            else:
                # Process failed immediately
                stdout, stderr = self.video_process.communicate()
                self.safe_print(f"❌ Video recording failed to start")
                self.safe_print(f"   Return code: {self.video_process.returncode}")
                if stdout:
                    self.safe_print(f"   Stdout: {stdout.decode()}")
                if stderr:
                    self.safe_print(f"   Stderr: {stderr.decode()}")
                
                # Handle specific error codes
                if self.video_process.returncode == 64:
                    self.safe_print("\n🔧 ERROR CODE 64 - Camera Initialization Failed")
                    self.safe_print("   Camera busy or hardware issue")
                    self.safe_print("   Try: sudo pkill -f raspistill && sudo pkill -f raspivid")
                
                self.video_process = None
                self.recording = False
            
        except Exception as e:
            self.safe_print(f"❌ Error starting video recording: {e}")
            self.video_process = None
            self.recording = False
    
    def stop_video_recording(self):
        """Stop video recording"""
        if not self.recording or not self.video_process:
            self.safe_print("⚠️ Not currently recording!")
            return
        
        self.safe_print("\n🛑 Stopping video recording...")
        
        try:
            # First try gentle termination (SIGTERM)
            self.safe_print("   📤 Sending termination signal...")
            self.video_process.terminate()
            
            try:
                self.video_process.wait(timeout=5)
                self.safe_print("   ✅ Video process terminated gracefully")
            except subprocess.TimeoutExpired:
                # Force kill if it doesn't stop (SIGKILL)
                self.safe_print("   ⚡ Force killing video process...")
                self.video_process.kill()
                try:
                    self.video_process.wait(timeout=2)
                    self.safe_print("   ✅ Video process killed")
                except subprocess.TimeoutExpired:
                    self.safe_print("   ⚠️ Video process may still be running")
            
            # Check for video file and report size
            try:
                videos = glob.glob(f"{self.videos_dir}/*.h264")
                if videos:
                    latest_video = max(videos, key=os.path.getctime)
                    if os.path.exists(latest_video):
                        size = os.path.getsize(latest_video)
                        self.safe_print(f"✅ Video saved: {latest_video}")
                        self.safe_print(f"   File size: {size/1024/1024:.1f} MB")
                    else:
                        self.safe_print("⚠️ Video file not found")
                else:
                    self.safe_print("⚠️ No video files found in directory")
            except Exception as e:
                print(f"   ⚠️ Could not check video file: {e}")
            
            # Clean up any remaining raspivid processes
            try:
                result = subprocess.run(['pgrep', '-f', 'raspivid'], capture_output=True, text=True)
                if result.returncode == 0 and result.stdout:
                    pids = result.stdout.strip().split('\n')
                    print(f"   🔧 Cleaning up remaining raspivid processes: {pids}")
                    subprocess.run(['sudo', 'pkill', '-9', '-f', 'raspivid'], timeout=5)
            except:
                pass
            
            self.video_process = None
            self.recording = False
            
            # Restart preview after a brief pause
            print("   🔄 Restarting preview...")
            time.sleep(1)  # Give camera time to be available
            self.start_preview()
            
        except Exception as e:
            print(f"❌ Error stopping video recording: {e}")
            # Force cleanup anyway
            self.video_process = None
            self.recording = False
            # Try to kill any raspivid processes
            try:
                subprocess.run(['sudo', 'pkill', '-9', '-f', 'raspivid'], timeout=5)
            except:
                pass
    
    def show_status(self):
        """Show current status"""
        print("\n" + "=" * 50)
        if self.recording:
            print("📹 STATUS: RECORDING VIDEO")
        elif self.preview_active:
            print("👁  STATUS: PREVIEW ACTIVE")
        else:
            print("⚫ STATUS: STANDBY")
        
        print("\nCONTROLS:")
        print("  SPACE      - Take Photo")
        print("  v          - Start/Stop Video Recording")
        print("  p          - Toggle Preview")
        print("  s          - Show Status")
        print("  h          - Open Shell (exit with 'exit')")
        print("  q/ESC      - Quit")
        print("=" * 50)
    
    def print_formatted(self, message, force_output=False):
        """Print message with proper terminal formatting in raw mode"""
        if self.quiet_mode and not force_output:
            return
            
        # Temporarily restore terminal for clean output
        if self.old_settings:
            try:
                # Save current raw settings
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.old_settings)
                print(message, flush=True)
                # Restore raw mode immediately
                tty.setraw(sys.stdin.fileno())
            except:
                # Fallback - just print with manual line endings
                print(message.replace('\n', '\r\n') + '\r\n', end='', flush=True)
        else:
            print(message, flush=True)

    def print_always(self, message):
        """Print message that always shows, even in quiet mode, with proper formatting"""
        # This function is for critical messages that must always appear
        if self.old_settings:
            try:
                # Save current raw settings
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.old_settings)
                print(message, flush=True)
                # Restore raw mode immediately
                tty.setraw(sys.stdin.fileno())
            except:
                # Fallback - just print with manual line endings
                print(message.replace('\n', '\r\n') + '\r\n', end='', flush=True)
        else:
            print(message, flush=True)

    def setup_terminal(self):
        """Set up terminal for single keypress input"""
        try:
            self.old_settings = termios.tcgetattr(sys.stdin)
            tty.setraw(sys.stdin.fileno())
            # Enable safe print patching to fix oblique output display
            self.monkey_patch_print()
        except:
            self.print_always("⚠ Warning: Could not set up raw terminal input")
            self.old_settings = None
    
    def restore_terminal(self):
        """Restore terminal to original settings"""
        if self.old_settings:
            try:
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.old_settings)
            except:
                pass
    
    def show_prompt(self):
        """Show the input prompt with proper cursor positioning"""
        if self.running and not self.quiet_mode:
            # Temporarily restore terminal for clean prompt
            if self.old_settings:
                try:
                    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.old_settings)
                    status = '📹REC' if self.recording else '👁PREV' if self.preview_active else 'READY'
                    print(f"\nPress key (current: {status}): ", end='', flush=True)
                    tty.setraw(sys.stdin.fileno())
                except:
                    pass
    
    def get_keypress(self):
        """Get a single keypress without Enter"""
        try:
            ch = sys.stdin.read(1)
            # Handle escape sequences
            if ord(ch) == 27:  # ESC key
                return 'esc'
            elif ord(ch) == 32:  # Space key
                return 'space'
            else:
                return ch.lower()
        except:
            return None
    
    def process_keypress(self, key):
        """Process single keypress"""
        if key == 'space':
            threading.Thread(target=self.take_photo).start()
            
        elif key == 'v':
            if self.recording:
                self.stop_video_recording()
            else:
                self.start_video_recording()
                
        elif key == 'p':
            if self.preview_active:
                self.stop_preview()
                # Switch to non-quiet mode when preview is off
                self.quiet_mode = False
                self.print_formatted("\n⏸ Preview stopped", force_output=True)
            else:
                # Switch to quiet mode when preview is on
                self.quiet_mode = True
                self.start_preview()
                
        elif key == 's':
            # Temporarily disable quiet mode to show status
            was_quiet = self.quiet_mode
            self.quiet_mode = False
            self.show_status()
            self.quiet_mode = was_quiet
            
        elif key == 'h':
            self.quiet_mode = False
            self.print_formatted("\n🐚 Opening shell...", force_output=True)
            self.print_formatted("Type 'exit' to return to camera app", force_output=True)
            self.open_shell()
            
        elif key == 'q' or key == 'esc':
            self.quiet_mode = False
            self.print_formatted("\n👋 Quitting...", force_output=True)
            self.running = False
            
        else:
            if key and key.isprintable() and not self.quiet_mode:
                self.print_formatted(f"\n❓ Unknown key: '{key}' - Press 's' for help", force_output=True)
            
        # Show prompt again
        self.show_prompt()
    
    def open_shell(self):
        """Open a shell session"""
        try:
            # Stop all camera processes
            self.stop_preview()
            if self.recording:
                self.stop_video_recording()
            
            # Restore terminal settings
            self.restore_terminal()
            
            print("\n" + "="*50)
            print("🐚 SHELL MODE - Camera app paused")
            print("Type 'exit' to return to camera app")
            print("="*50)
            
            # Launch shell
            subprocess.run(['/bin/bash'], stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr)
            
            print("\n📷 Returning to camera app...")
            
            # Restart camera app components
            self.setup_terminal()
            self.start_preview()
            self.quiet_mode = False
            self.show_status()
            self.quiet_mode = True
            
        except Exception as e:
            print(f"Error in shell mode: {e}")
            self.setup_terminal()
    
    def run(self):
        """Main application loop"""
        self.print_formatted("\nInitializing camera...", force_output=True)
        self.start_preview()
        
        # Only show initial status, then go quiet
        self.quiet_mode = False
        self.show_status()
        self.quiet_mode = True  # Enable quiet mode after showing initial status
        
        # Set up terminal for single keypress input
        self.setup_terminal()
        
        try:
            while self.running:
                try:
                    # Get single keypress
                    key = self.get_keypress()
                    if key:
                        self.process_keypress(key)
                    
                except KeyboardInterrupt:
                    # Handle Ctrl+C
                    self.print_formatted("\n\n⚠ Interrupted by user", force_output=True)
                    break
                    
        except Exception as e:
            self.print_formatted(f"\n✗ Error in main loop: {e}", force_output=True)
        finally:
            # Always restore terminal
            self.restore_terminal()
        
        # Cleanup
        self.cleanup()
    
    def cleanup(self):
        """Clean up resources"""
        self.print_formatted("\n🧹 Cleaning up...", force_output=True)
        
        # Stop all camera processes
        if self.recording:
            self.stop_video_recording()
        self.stop_preview()
        
        # Aggressively kill any remaining camera processes
        self.print_formatted("🔧 Ensuring all camera processes are stopped...", force_output=True)
        camera_commands = ['raspistill', 'raspivid']
        for cmd in camera_commands:
            try:
                # Check if any processes are running
                result = subprocess.run(['pgrep', '-f', cmd], capture_output=True, text=True)
                if result.returncode == 0 and result.stdout:
                    pids = result.stdout.strip().split('\n')
                    self.print_formatted(f"   Killing {cmd} processes: {pids}", force_output=True)
                    subprocess.run(['sudo', 'pkill', '-9', '-f', cmd], timeout=5)
            except Exception as e:
                self.print_formatted(f"   Warning: Could not clean up {cmd} processes: {e}", force_output=True)
        
        # Restore terminal settings
        self.restore_terminal()
        
        print("✅ Cleanup complete")
        print("\n🐚 Dropping to shell...")
        print("Camera app has exited. You now have shell access.")
        print("Type 'sudo systemctl restart camera-app-foreground.service' to restart the camera app")
        print("Or type 'sudo systemctl stop camera-app-foreground.service' to prevent auto-restart")
        
        # Launch a shell so user has access
        try:
            subprocess.run(['/bin/bash'], stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr)
        except:
            # If shell fails, at least restore terminal
            pass

    def monkey_patch_print(self):
        """Replace the global print function with our safe version"""
        def safe_global_print(*args, **kwargs):
            # Convert args to message string
            sep = kwargs.get('sep', ' ')
            message = sep.join(str(arg) for arg in args)
            
            # Check for critical messages that should always show
            is_critical = any(marker in message for marker in ['✗', '❌', '⚠', '🚨', '🔧', 'ERROR', 'Warning'])
            
            if is_critical or not self.quiet_mode:
                if self.old_settings:
                    try:
                        # Temporarily restore normal terminal
                        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.old_settings)
                        self.original_print(*args, **kwargs, flush=True)
                        # Restore raw mode
                        tty.setraw(sys.stdin.fileno())
                    except:
                        # Fallback
                        self.original_print(*args, **kwargs, flush=True)
                else:
                    self.original_print(*args, **kwargs, flush=True)
        
        # Replace builtins.print with our safe version
        builtins.print = safe_global_print

    def restore_print(self):
        """Restore the original print function"""
        import builtins
        builtins.print = self.original_print

def main():
    """Main function"""
    # Check if running on Raspberry Pi
    try:
        with open('/proc/cpuinfo', 'r') as f:
            cpuinfo = f.read()
            if 'BCM' not in cpuinfo:
                print("⚠ Warning: This doesn't appear to be a Raspberry Pi")
                print("Some camera functions may not work properly")
    except:
        pass
    
    # Check for existing camera processes and clean them up
    print("🔍 Checking for existing camera processes...")
    camera_commands = ['raspistill', 'raspivid']
    processes_killed = False
    
    for cmd in camera_commands:
        try:
            result = subprocess.run(['pgrep', '-f', cmd], capture_output=True, text=True)
            if result.returncode == 0 and result.stdout:
                pids = result.stdout.strip().split('\n')
                print(f"⚠️ Found existing {cmd} processes: {pids}")
                print(f"🔧 Cleaning up {cmd} processes...")
                subprocess.run(['sudo', 'pkill', '-9', '-f', cmd], timeout=5)
                processes_killed = True
        except Exception as e:
            print(f"Warning: Could not check for {cmd} processes: {e}")
    
    if processes_killed:
        print("✅ Cleaned up existing camera processes")
        print("⏱️ Waiting 2 seconds for camera to be ready...")
        import time
        time.sleep(2)
    else:
        print("✅ No existing camera processes found")
    
    # Check if camera tools are available
    try:
        result = subprocess.run(['which', 'raspistill'], 
                              capture_output=True, text=True)
        if result.returncode != 0:
            raise FileNotFoundError("raspistill not found in PATH")
        
        print(f"✓ Found raspistill at: {result.stdout.strip()}")
        
        result = subprocess.run(['which', 'raspivid'], 
                              capture_output=True, text=True)
        if result.returncode != 0:
            print("⚠ Warning: raspivid not found - video recording may not work")
        else:
            print(f"✓ Found raspivid at: {result.stdout.strip()}")
            
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("✗ Error: raspistill not found. Please install camera tools:")
        print("sudo apt-get update")
        print("sudo apt-get install libraspberrypi-bin")
        sys.exit(1)
    
    try:
        app = RPiCameraHeadless()
        app.run()
    except KeyboardInterrupt:
        print("\n\n👋 Application interrupted by user")
    except Exception as e:
        print(f"\n✗ Error running application: {e}")

if __name__ == "__main__":
    main() 