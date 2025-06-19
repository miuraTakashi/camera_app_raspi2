#!/usr/bin/env python3
"""
Raspberry Pi Camera Diagnostic Tool
Specifically designed to troubleshoot error code 64 and other camera issues
"""

import subprocess
import sys
import os
import time

def run_command(cmd, description=""):
    """Run a command and return result with nice formatting"""
    print(f"\n{'='*60}")
    if description:
        print(f"🔍 {description}")
    print(f"Command: {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    print(f"{'='*60}")
    
    try:
        if isinstance(cmd, str):
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        else:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        print(f"Return code: {result.returncode}")
        
        if result.stdout:
            print("STDOUT:")
            print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
            
        return result
        
    except subprocess.TimeoutExpired:
        print("❌ Command timed out")
        return None
    except Exception as e:
        print(f"❌ Error running command: {e}")
        return None

def check_camera_hardware():
    """Check camera hardware detection"""
    print("\n" + "🔧 CAMERA HARDWARE DETECTION" + "="*40)
    
    # Check camera detection
    result = run_command("vcgencmd get_camera", "Check camera detection")
    if result and result.returncode == 0:
        if "detected=1" in result.stdout:
            print("✅ Camera hardware detected")
        else:
            print("❌ Camera hardware NOT detected")
            print("   → Check camera cable connection")
            print("   → Try different camera module")
            return False
    
    # Check camera interface
    result = run_command("ls -la /dev/video*", "Check video devices")
    if result and result.returncode == 0:
        print("✅ Video devices found")
    else:
        print("❌ No video devices found")
    
    # Check GPU memory split
    result = run_command("vcgencmd get_mem gpu", "Check GPU memory")
    if result and result.returncode == 0:
        try:
            gpu_mem = int(result.stdout.strip().replace('gpu=', '').replace('M', ''))
            if gpu_mem >= 128:
                print(f"✅ GPU memory OK: {gpu_mem}MB")
            else:
                print(f"⚠️ GPU memory low: {gpu_mem}MB (recommend 128MB+)")
                print("   → Increase GPU memory: sudo raspi-config → Advanced → Memory Split")
        except:
            print("❓ Could not parse GPU memory")
    
    return True

def check_camera_config():
    """Check camera configuration"""
    print("\n" + "⚙️ CAMERA CONFIGURATION" + "="*42)
    
    # Check config.txt
    config_files = ['/boot/config.txt', '/boot/firmware/config.txt']
    config_found = False
    
    for config_file in config_files:
        if os.path.exists(config_file):
            config_found = True
            print(f"📄 Checking {config_file}")
            try:
                with open(config_file, 'r') as f:
                    config_content = f.read()
                
                if 'camera_auto_detect=1' in config_content:
                    print("✅ Camera auto-detect enabled")
                elif 'start_x=1' in config_content:
                    print("✅ Camera enabled (legacy method)")
                else:
                    print("❌ Camera not enabled in config")
                    print(f"   → Add 'camera_auto_detect=1' to {config_file}")
                    print("   → Or run: sudo raspi-config → Interface Options → Camera")
                    
                if 'gpu_mem=' in config_content:
                    gpu_mem_line = [line for line in config_content.split('\n') if 'gpu_mem=' in line and not line.strip().startswith('#')]
                    if gpu_mem_line:
                        print(f"📊 GPU memory setting: {gpu_mem_line[0]}")
                    
            except Exception as e:
                print(f"❌ Error reading {config_file}: {e}")
            break
    
    if not config_found:
        print("❌ Could not find config file")
    
    # Check if camera interface enabled via raspi-config
    result = run_command("raspi-config nonint get_camera", "Check camera interface status")
    if result and result.returncode == 0:
        if result.stdout.strip() == "0":
            print("✅ Camera interface enabled")
        else:
            print("❌ Camera interface disabled")
            print("   → Enable: sudo raspi-config → Interface Options → Camera")

def test_camera_commands():
    """Test basic camera commands"""
    print("\n" + "📷 CAMERA COMMAND TESTS" + "="*41)
    
    # Test raspistill help
    result = run_command(['raspistill', '--help'], "Test raspistill availability")
    if result and result.returncode == 0:
        print("✅ raspistill command available")
    else:
        print("❌ raspistill command failed")
        print("   → Install: sudo apt-get install libraspberrypi-bin")
        return False
    
    # Test camera detection with raspistill
    result = run_command(['raspistill', '-t', '1'], "Test basic camera detection")
    if result:
        if result.returncode == 0:
            print("✅ Basic camera test passed")
        elif result.returncode == 64:
            print("❌ ERROR CODE 64 - Camera initialization failed")
            print("   → Camera hardware cannot be detected")
            print("   → Check all troubleshooting steps below")
        else:
            print(f"❌ Camera test failed with code {result.returncode}")
    
    return True

def check_processes():
    """Check for processes that might be using the camera"""
    print("\n" + "🔍 PROCESS CHECK" + "="*48)
    
    camera_processes = ['raspistill', 'raspivid', 'libcamera', 'motion', 'cheese']
    
    for process in camera_processes:
        result = run_command(f"pgrep -f {process}", f"Check for {process} processes")
        if result and result.returncode == 0 and result.stdout:
            print(f"⚠️ Found {process} processes:")
            print(result.stdout)
            print(f"   → Kill with: sudo pkill -9 {process}")
        else:
            print(f"✅ No {process} processes found")

def main():
    """Main diagnostic function"""
    print("🔧 RASPBERRY PI CAMERA DIAGNOSTIC TOOL")
    print("=" * 60)
    print("This tool helps diagnose camera issues, especially error code 64")
    print("=" * 60)
    
    # System info
    result = run_command("uname -a", "System information")
    result = run_command("cat /etc/os-release | head -n 2", "OS version")
    
    # Run diagnostics
    check_camera_hardware()
    check_camera_config()
    check_processes()
    test_camera_commands()
    
    # Summary and recommendations
    print("\n" + "📋 TROUBLESHOOTING SUMMARY" + "="*35)
    print("If you're still getting error code 64, try these steps IN ORDER:")
    print("\n1. 🔌 HARDWARE CHECK:")
    print("   • Shut down Pi completely: sudo shutdown -h now")
    print("   • Disconnect power cable")
    print("   • Remove and reconnect camera cable (both ends)")
    print("   • Ensure cable is inserted correctly (blue side to board)")
    print("   • Power on and test")
    
    print("\n2. ⚙️ SOFTWARE CHECK:")
    print("   • Enable camera: sudo raspi-config → Interface Options → Camera")
    print("   • Reboot: sudo reboot")
    print("   • Update firmware: sudo apt-get update && sudo apt-get upgrade")
    print("   • Reinstall camera tools: sudo apt-get install --reinstall libraspberrypi-bin")
    
    print("\n3. 🧪 TESTING:")
    print("   • Test detection: vcgencmd get_camera")
    print("   • Simple test: raspistill -o test.jpg -t 2000")
    print("   • Check test.jpg was created and view it")
    
    print("\n4. 🆘 IF STILL FAILING:")
    print("   • Try different camera module")
    print("   • Try different camera cable")
    print("   • Check Pi camera connector for damage")
    print("   • Test with fresh Raspberry Pi OS installation")
    
    print("\n" + "="*60)
    print("💡 TIP: Error code 64 is almost always a hardware connection issue!")
    print("="*60)

if __name__ == "__main__":
    main() 