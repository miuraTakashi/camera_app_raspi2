#!/usr/bin/env python3
"""
Simple Video Test Script
Tests basic raspivid command functionality
"""

import subprocess
import os
import time
from datetime import datetime

def test_simple_video():
    """Test the basic raspivid command"""
    print("🧪 Testing simple raspivid command...")
    print("=" * 50)
    
    # Get current working directory
    cwd = os.getcwd()
    print(f"Current directory: {cwd}")
    
    # Create videos directory if it doesn't exist
    videos_dir = os.path.join(cwd, "videos")
    os.makedirs(videos_dir, exist_ok=True)
    
    # Generate filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Test 1: Check for existing processes
    print("\n🔍 Test 1: Check for existing video processes")
    camera_processes = ['raspistill', 'raspivid']
    for process in camera_processes:
        try:
            result = subprocess.run(['pgrep', '-f', process], capture_output=True, text=True)
            if result.returncode == 0 and result.stdout:
                print(f"⚠️ Active {process} processes found:")
                print(result.stdout)
                print(f"   Kill with: sudo pkill -f {process}")
            else:
                print(f"✅ No {process} processes running")
        except:
            print(f"❓ Could not check {process} processes")
    
    # Test 2: Basic command (short duration)
    print("\n🎥 Test 2: Basic 5-second video recording")
    filename2 = os.path.join(videos_dir, f"short_test_{timestamp}.h264")
    cmd2 = ['raspivid', '-o', filename2, '-t', '5000']  # 5 seconds
    print(f"Command: {' '.join(cmd2)}")
    
    try:
        result = subprocess.run(cmd2, capture_output=True, text=True, timeout=10)
        print(f"Return code: {result.returncode}")
        if result.stdout:
            print(f"Stdout: {result.stdout}")
        if result.stderr:
            print(f"Stderr: {result.stderr}")
        
        if result.returncode == 0 and os.path.exists(filename2):
            size = os.path.getsize(filename2)
            print(f"✅ SUCCESS: Video created, size: {size/1024:.1f} KB")
        else:
            print("❌ FAILED: Video not created or command failed")
            if result.returncode == 64:
                print("   ERROR CODE 64: Camera hardware issue or busy")
    except Exception as e:
        print(f"❌ ERROR: {e}")
    
    # Test 3: With fullscreen preview (short duration)
    print(f"\n🎥 Test 3: With fullscreen preview (3-second recording)")
    filename3 = os.path.join(videos_dir, f"preview_test_{timestamp}.h264")
    cmd3 = ['raspivid', '-o', filename3, '-t', '3000', '-f']
    print(f"Command: {' '.join(cmd3)}")
    
    try:
        print("   📹 Recording for 3 seconds with preview...")
        result = subprocess.run(cmd3, capture_output=True, text=True, timeout=8)
        print(f"Return code: {result.returncode}")
        if result.stdout:
            print(f"Stdout: {result.stdout}")
        if result.stderr:
            print(f"Stderr: {result.stderr}")
        
        if result.returncode == 0 and os.path.exists(filename3):
            size = os.path.getsize(filename3)
            print(f"✅ SUCCESS: Video with preview created, size: {size/1024:.1f} KB")
        else:
            print("❌ FAILED: Video with preview failed")
    except Exception as e:
        print(f"❌ ERROR: {e}")
    
    # Test 4: Process start/stop simulation
    print(f"\n🔄 Test 4: Process start/stop simulation")
    filename4 = os.path.join(videos_dir, f"process_test_{timestamp}.h264")
    cmd4 = ['raspivid', '-o', filename4, '-t', '0']  # Continuous
    print(f"Command: {' '.join(cmd4)} (will run for 2 seconds then stop)")
    
    try:
        print("   🚀 Starting continuous recording process...")
        process = subprocess.Popen(cmd4, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Let it run for 2 seconds
        time.sleep(2)
        
        print("   🛑 Stopping process...")
        process.terminate()
        
        try:
            process.wait(timeout=3)
            print("   ✅ Process terminated gracefully")
        except subprocess.TimeoutExpired:
            print("   ⚡ Force killing process...")
            process.kill()
            process.wait()
            print("   ✅ Process killed")
        
        if os.path.exists(filename4):
            size = os.path.getsize(filename4)
            print(f"✅ SUCCESS: Process control test passed, size: {size/1024:.1f} KB")
        else:
            print("❌ FAILED: No video file created during process test")
    except Exception as e:
        print(f"❌ ERROR: {e}")
    
    # Final process check
    print(f"\n🔍 Final: Check for any remaining processes")
    for process in camera_processes:
        try:
            result = subprocess.run(['pgrep', '-f', process], capture_output=True, text=True)
            if result.returncode == 0 and result.stdout:
                print(f"⚠️ {process} processes still running:")
                print(result.stdout)
            else:
                print(f"✅ No {process} processes remaining")
        except:
            print(f"❓ Could not check {process} processes")
    
    print("\n" + "=" * 50)
    print("📋 Summary:")
    print("- Test basic video recording functionality")
    print("- Check for process conflicts and cleanup")
    print("- Compare results with camera_app.py video behavior")
    print("- All tests should pass for proper video recording")

if __name__ == "__main__":
    test_simple_video() 