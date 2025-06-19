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
from datetime import datetime
import os
import sys
import select
import termios
import tty

class RPiCameraHeadless:
    def __init__(self):
        print("Raspberry Pi Camera App - Headless Version")
        print("=" * 50)
        
        # Status variables
        self.recording = False
        self.preview_active = False
        self.preview_process = None
        self.video_process = None
        self.running = True
        
        # Terminal settings for single keypress input
        self.old_settings = None
        
        # Quiet mode - suppress output during preview
        self.quiet_mode = True
        
        # Ensure we're in the correct working directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        os.chdir(script_dir)
        print(f"Working directory: {os.getcwd()}")
        
        # Create directories for photos and videos with full paths
        self.photos_dir = os.path.join(script_dir, "photos")
        self.videos_dir = os.path.join(script_dir, "videos")
        
        try:
            os.makedirs(self.photos_dir, exist_ok=True)
            os.makedirs(self.videos_dir, exist_ok=True)
            
            # Set proper permissions for directories
            os.chmod(self.photos_dir, 0o755)
            os.chmod(self.videos_dir, 0o755)
            
            print(f"Photos directory: {self.photos_dir}")
            print(f"Videos directory: {self.videos_dir}")
            
        except PermissionError as e:
            print(f"✗ ERROR: Permission denied creating directories: {e}")
            print(f"   Try running with sudo or check parent directory permissions")
            sys.exit(1)
        except Exception as e:
            print(f"✗ ERROR: Failed to create directories: {e}")
            print(f"   Attempted to create: {self.photos_dir}")
            print(f"   Attempted to create: {self.videos_dir}")
            sys.exit(1)
        
    def get_timestamp(self):
        """Generate timestamp in format: YYYYMMDD_HHMMSS"""
        return datetime.now().strftime("%Y%m%d_%H%M%S")
    
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
                print(f"✗ Error starting preview: {e}")
                print("  Preview will be disabled, but photo/video capture will still work")
    
    def stop_preview(self):
        """Stop camera preview"""
        if self.preview_process:
            try:
                # First try gentle termination
                self.preview_process.terminate()
                try:
                    self.preview_process.wait(timeout=2)
                    print("   📷 Preview terminated gracefully")
                except subprocess.TimeoutExpired:
                    # Force kill if it doesn't stop
                    print("   ⚡ Force killing preview process")
                    self.preview_process.kill()
                    self.preview_process.wait(timeout=1)
            except Exception as e:
                print(f"   ⚠️ Error stopping preview: {e}")
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
                print(f"   ⚠️ Found lingering raspistill processes: {result.stdout.strip()}")
                print("   🔧 Cleaning up...")
                subprocess.run(['sudo', 'pkill', '-9', '-f', 'raspistill'], timeout=5)
        except:
            pass
            
        self.preview_active = False
    
    def take_photo(self):
        """Take a photo using raspistill"""
        timestamp = self.get_timestamp()
        filename = os.path.join(self.photos_dir, f"{timestamp}.jpg")
        
        # Always show debug info for photo attempts
        print(f"\n📸 Taking photo...")
        print(f"   Target file: {filename}")
        print(f"   Photos dir exists: {os.path.exists(self.photos_dir)}")
        print(f"   Photos dir writable: {os.access(self.photos_dir, os.W_OK)}")
        print(f"   Current working dir: {os.getcwd()}")
        
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
            
            print(f"   Running command: {' '.join(cmd)}")
            print(f"   Working directory: {os.getcwd()}")
            
            # Run with more verbose output
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            print(f"   Return code: {result.returncode}")
            if result.stdout:
                print(f"   Stdout: {result.stdout}")
            if result.stderr:
                print(f"   Stderr: {result.stderr}")
            
            if result.returncode == 0:
                # Check if file was actually created
                if os.path.exists(filename):
                    size = os.path.getsize(filename)
                    print(f"✅ Photo saved: {filename}")
                    print(f"   File size: {size/1024:.1f} KB")
                    
                    # Test different optimizations one by one
                    print(f"   📁 Full path: {os.path.abspath(filename)}")
                    
                else:
                    print(f"❌ Command succeeded but file not found: {filename}")
                    print(f"   Check if file was created elsewhere...")
                    # Look for any jpg files created recently
                    import glob
                    recent_files = glob.glob("*.jpg") + glob.glob("/home/*/camera_app_raspi2/*.jpg")
                    if recent_files:
                        print(f"   Recent JPG files found: {recent_files}")
            else:
                # Always show camera errors, even in quiet mode
                print(f"❌ Camera command failed - Return code: {result.returncode}")
                if result.stderr:
                    print(f"   Error details: {result.stderr.strip()}")
                
                # Specific error code handling
                if result.returncode == 64:
                    print("\n🔧 ERROR CODE 64 - Camera Initialization Failed")
                    print("   This usually means the camera hardware cannot be detected.")
                    print("   But since 'raspistill -o test.jpg' works, this might be a parameter issue.")
                    print("   Troubleshooting steps:")
                    print("   1. Try running the exact same command manually:")
                    print(f"      cd {os.getcwd()}")
                    print(f"      {' '.join(cmd)}")
                    print("   2. Check if preview is interfering")
                    print("   3. Check file permissions in target directory")
                elif result.returncode == 1:
                    print("\n🔧 ERROR CODE 1 - General Camera Error")
                    print("   Try: sudo modprobe bcm2835-v4l2")
                elif result.returncode == 70:
                    print("\n🔧 ERROR CODE 70 - Software Error")
                    print("   Camera software issue. Try: sudo apt-get update && sudo apt-get install --reinstall libraspberrypi-bin")
                elif result.returncode == 130:
                    print("\n🔧 ERROR CODE 130 - Interrupted")
                    print("   Camera command was interrupted")
                
                if "not found" in result.stderr.lower():
                    print("   📦 Install camera tools: sudo apt-get install libraspberrypi-bin")
                elif "permission" in result.stderr.lower():
                    print(f"   🔐 Check permissions: sudo chown -R $USER:$USER {self.photos_dir}")
                elif "busy" in result.stderr.lower():
                    print("   📷 Camera busy - close other camera applications")
                    print("   Try: sudo pkill -f raspistill")
                elif "timeout" in result.stderr.lower():
                    print("   ⏱️ Camera timeout - check hardware connection")
            
            # Restart preview quickly
            if was_active:
                time.sleep(0.5)  # Give more time for camera to be ready
                self.start_preview()
                
        except subprocess.TimeoutExpired:
            print("❌ Photo capture timed out")
        except FileNotFoundError:
            print("❌ raspistill command not found")
            print("   Install with: sudo apt-get install libraspberrypi-bin")
        except Exception as e:
            print(f"❌ Unexpected error taking photo: {e}")
            import traceback
            traceback.print_exc()
    
    def start_video_recording(self):
        """Start video recording using raspivid"""
        if self.recording:
            print("⚠️ Already recording!")
            return
        
        timestamp = self.get_timestamp()
        filename = os.path.join(self.videos_dir, f"{timestamp}.h264")
        
        # Always show debug info for video recording
        print(f"\n🎥 Starting video recording...")
        print(f"   Target file: {filename}")
        print(f"   Videos dir exists: {os.path.exists(self.videos_dir)}")
        print(f"   Videos dir writable: {os.access(self.videos_dir, os.W_OK)}")
        
        # Check for existing raspivid processes
        try:
            result = subprocess.run(['pgrep', '-f', 'raspivid'], capture_output=True, text=True)
            if result.returncode == 0 and result.stdout:
                print(f"⚠️ Found existing raspivid processes: {result.stdout.strip()}")
                print("🔧 Cleaning up existing video processes...")
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
            
            print(f"   Running command: {' '.join(cmd)}")
            
            # Start recording process
            self.video_process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Give it a moment to start
            time.sleep(0.5)
            
            # Check if process is still running (didn't immediately fail)
            if self.video_process.poll() is None:
                print("✅ Video recording started successfully")
                self.recording = True
            else:
                # Process failed immediately
                stdout, stderr = self.video_process.communicate()
                print(f"❌ Video recording failed to start")
                print(f"   Return code: {self.video_process.returncode}")
                if stdout:
                    print(f"   Stdout: {stdout.decode()}")
                if stderr:
                    print(f"   Stderr: {stderr.decode()}")
                
                # Handle specific error codes
                if self.video_process.returncode == 64:
                    print("\n🔧 ERROR CODE 64 - Camera Initialization Failed")
                    print("   Camera busy or hardware issue")
                    print("   Try: sudo pkill -f raspistill && sudo pkill -f raspivid")
                
                self.video_process = None
                self.recording = False
            
        except Exception as e:
            print(f"❌ Error starting video recording: {e}")
            self.video_process = None
            self.recording = False
    
    def stop_video_recording(self):
        """Stop video recording"""
        if not self.recording or not self.video_process:
            print("⚠️ Not currently recording!")
            return
        
        print("\n🛑 Stopping video recording...")
        
        try:
            # First try gentle termination (SIGTERM)
            print("   📤 Sending termination signal...")
            self.video_process.terminate()
            
            try:
                self.video_process.wait(timeout=5)
                print("   ✅ Video process terminated gracefully")
            except subprocess.TimeoutExpired:
                # Force kill if it doesn't stop (SIGKILL)
                print("   ⚡ Force killing video process...")
                self.video_process.kill()
                try:
                    self.video_process.wait(timeout=2)
                    print("   ✅ Video process killed")
                except subprocess.TimeoutExpired:
                    print("   ⚠️ Video process may still be running")
            
            # Check for video file and report size
            try:
                import glob
                videos = glob.glob(f"{self.videos_dir}/*.h264")
                if videos:
                    latest_video = max(videos, key=os.path.getctime)
                    if os.path.exists(latest_video):
                        size = os.path.getsize(latest_video)
                        print(f"✅ Video saved: {latest_video}")
                        print(f"   File size: {size/1024/1024:.1f} MB")
                    else:
                        print("⚠️ Video file not found")
                else:
                    print("⚠️ No video files found in directory")
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
    
    def setup_terminal(self):
        """Set up terminal for single keypress input"""
        try:
            self.old_settings = termios.tcgetattr(sys.stdin)
            tty.setraw(sys.stdin.fileno())
        except:
            print("⚠ Warning: Could not set up raw terminal input")
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
            # Move to new line, clear it, and show prompt
            status = '📹REC' if self.recording else '👁PREV' if self.preview_active else 'READY'
            print(f"\nPress key (current: {status}): ", end='', flush=True)
    
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
                print("\n⏸ Preview stopped")
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
            print("\n🐚 Opening shell...")
            print("Type 'exit' to return to camera app")
            self.open_shell()
            
        elif key == 'q' or key == 'esc':
            self.quiet_mode = False
            print("\n👋 Quitting...")
            self.running = False
            
        else:
            if key and key.isprintable() and not self.quiet_mode:
                print(f"\n❓ Unknown key: '{key}' - Press 's' for help")
            
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
        print("\nInitializing camera...")
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
                    print("\n\n⚠ Interrupted by user")
                    break
                    
        except Exception as e:
            print(f"\n✗ Error in main loop: {e}")
        finally:
            # Always restore terminal
            self.restore_terminal()
        
        # Cleanup
        self.cleanup()
    
    def cleanup(self):
        """Clean up resources"""
        print("\n🧹 Cleaning up...")
        
        # Stop all camera processes
        if self.recording:
            self.stop_video_recording()
        self.stop_preview()
        
        # Aggressively kill any remaining camera processes
        print("🔧 Ensuring all camera processes are stopped...")
        camera_commands = ['raspistill', 'raspivid']
        for cmd in camera_commands:
            try:
                # Check if any processes are running
                result = subprocess.run(['pgrep', '-f', cmd], capture_output=True, text=True)
                if result.returncode == 0 and result.stdout:
                    pids = result.stdout.strip().split('\n')
                    print(f"   Killing {cmd} processes: {pids}")
                    subprocess.run(['sudo', 'pkill', '-9', '-f', cmd], timeout=5)
            except Exception as e:
                print(f"   Warning: Could not clean up {cmd} processes: {e}")
        
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