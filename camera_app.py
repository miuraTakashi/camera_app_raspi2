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
                self.preview_process.terminate()
                self.preview_process.wait(timeout=2)
            except:
                self.preview_process.kill()
            self.preview_process = None
        self.preview_active = False
    
    def take_photo(self):
        """Take a photo using raspistill"""
        timestamp = self.get_timestamp()
        filename = os.path.join(self.photos_dir, f"{timestamp}.jpg")
        
        try:
            # Temporarily stop preview
            was_active = self.preview_active
            if was_active:
                self.stop_preview()
            
            # Take photo with optimized settings for speed
            cmd = [
                'raspistill', '-o', filename, 
                '-t', '100',  # Very short capture time (0.1 seconds)
                '-q', '90',   # Slightly reduced quality for speed (90% vs 100%)
                '-w', '1920', '-h', '1080', 
                '--nopreview',
                '--immediate'  # Take photo immediately without delay
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                # Check if file was actually created
                if os.path.exists(filename):
                    size = os.path.getsize(filename)
                    if not self.quiet_mode:
                        print(f"✓ Photo saved: {filename}")
                        print(f"  File size: {size/1024:.1f} KB")
                else:
                    # Always show this error, even in quiet mode
                    print(f"✗ ERROR: Command succeeded but file not found: {filename}")
                    print(f"   Check directory permissions: {self.photos_dir}")
            else:
                # Always show camera errors, even in quiet mode
                print(f"✗ ERROR: Camera command failed - Return code: {result.returncode}")
                if result.stderr:
                    print(f"   Error details: {result.stderr.strip()}")
                if "not found" in result.stderr.lower():
                    print("   Try running: sudo apt-get install libraspberrypi-bin")
                elif "permission" in result.stderr.lower():
                    print(f"   Check file permissions on: {self.photos_dir}")
            
            # Restart preview quickly
            if was_active:
                time.sleep(0.1)
                self.start_preview()
                
        except subprocess.TimeoutExpired:
            print("✗ ERROR: Photo capture timed out")
        except FileNotFoundError:
            print("✗ ERROR: raspistill command not found")
            print("   Install with: sudo apt-get install libraspberrypi-bin")
        except Exception as e:
            print(f"✗ ERROR: Unexpected error taking photo: {e}")
            import traceback
            traceback.print_exc()
    
    def start_video_recording(self):
        """Start video recording using raspivid"""
        if self.recording:
            if not self.quiet_mode:
                print("⚠ Already recording!")
            return
        
        timestamp = self.get_timestamp()
        filename = os.path.join(self.videos_dir, f"{timestamp}.h264")
        
        try:
            # Stop preview first (raspivid will handle its own preview)
            self.stop_preview()
            
            # Start recording with fullscreen preview (no red dot)
            self.video_process = subprocess.Popen([
                'raspivid', '-o', filename, '-t', '0',  # -t 0 for continuous recording
                '-w', '1920', '-h', '1080', '-fps', '30',
                '-f'  # Fullscreen preview
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            self.recording = True
            
        except Exception as e:
            if not self.quiet_mode:
                print(f"✗ Error starting video recording: {e}")
    
    def stop_video_recording(self):
        """Stop video recording"""
        if not self.recording or not self.video_process:
            if not self.quiet_mode:
                print("⚠ Not currently recording!")
            return
        
        try:
            # Send SIGINT to stop recording gracefully
            self.video_process.terminate()
            self.video_process.wait(timeout=5)
            
            # Try to find the video file that was just created
            if not self.quiet_mode:
                try:
                    import glob
                    videos = glob.glob(f"{self.videos_dir}/*.h264")
                    if videos:
                        latest_video = max(videos, key=os.path.getctime)
                        size = os.path.getsize(latest_video)
                        print(f"✓ Video saved: {latest_video}")
                        print(f"  File size: {size/1024/1024:.1f} MB")
                except:
                    print("✓ Video recording stopped")
            
            self.video_process = None
            self.recording = False
            
            # Restart preview without recording indicator
            time.sleep(0.5)
            self.start_preview()
            
        except subprocess.TimeoutExpired:
            # Force kill if it doesn't stop gracefully
            self.video_process.kill()
            self.video_process = None
            self.recording = False
            if not self.quiet_mode:
                print("✓ Video recording force stopped")
            # Still restart preview
            time.sleep(0.5)
            self.start_preview()
        except Exception as e:
            if not self.quiet_mode:
                print(f"✗ Error stopping video: {e}")
            # Set recording to false anyway
            self.recording = False
    
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
        
        # Restore terminal settings
        self.restore_terminal()
        
        print("✓ Cleanup complete")
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