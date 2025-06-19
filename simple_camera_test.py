#!/usr/bin/env python3
"""
Simple Camera Test Script
Tests the exact same raspistill command that works manually
"""

import subprocess
import os
from datetime import datetime

def test_simple_photo():
    """Test the basic raspistill command that works manually"""
    print("🧪 Testing simple raspistill command...")
    print("=" * 50)
    
    # Get current working directory
    cwd = os.getcwd()
    print(f"Current directory: {cwd}")
    
    # Create photos directory if it doesn't exist
    photos_dir = os.path.join(cwd, "photos")
    os.makedirs(photos_dir, exist_ok=True)
    
    # Generate filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(photos_dir, f"simple_test_{timestamp}.jpg")
    
    print(f"Target file: {filename}")
    
    # Test 1: Exact same command that works manually
    print("\n📸 Test 1: Basic command (like manual test)")
    cmd1 = ['raspistill', '-o', 'test_basic.jpg']
    print(f"Command: {' '.join(cmd1)}")
    
    try:
        result = subprocess.run(cmd1, capture_output=True, text=True, timeout=10)
        print(f"Return code: {result.returncode}")
        if result.stdout:
            print(f"Stdout: {result.stdout}")
        if result.stderr:
            print(f"Stderr: {result.stderr}")
        
        if result.returncode == 0 and os.path.exists('test_basic.jpg'):
            size = os.path.getsize('test_basic.jpg')
            print(f"✅ SUCCESS: File created, size: {size/1024:.1f} KB")
        else:
            print("❌ FAILED: File not created or command failed")
    except Exception as e:
        print(f"❌ ERROR: {e}")
    
    # Test 2: Same command with full path
    print(f"\n📸 Test 2: With full path to photos directory")
    cmd2 = ['raspistill', '-o', filename]
    print(f"Command: {' '.join(cmd2)}")
    
    try:
        result = subprocess.run(cmd2, capture_output=True, text=True, timeout=10)
        print(f"Return code: {result.returncode}")
        if result.stdout:
            print(f"Stdout: {result.stdout}")
        if result.stderr:
            print(f"Stderr: {result.stderr}")
        
        if result.returncode == 0 and os.path.exists(filename):
            size = os.path.getsize(filename)
            print(f"✅ SUCCESS: File created, size: {size/1024:.1f} KB")
        else:
            print("❌ FAILED: File not created or command failed")
    except Exception as e:
        print(f"❌ ERROR: {e}")
    
    # Test 3: Add timing parameter
    print(f"\n📸 Test 3: With timing parameter")
    filename3 = os.path.join(photos_dir, f"timed_test_{timestamp}.jpg")
    cmd3 = ['raspistill', '-o', filename3, '-t', '2000']
    print(f"Command: {' '.join(cmd3)}")
    
    try:
        result = subprocess.run(cmd3, capture_output=True, text=True, timeout=10)
        print(f"Return code: {result.returncode}")
        if result.stdout:
            print(f"Stdout: {result.stdout}")
        if result.stderr:
            print(f"Stderr: {result.stderr}")
        
        if result.returncode == 0 and os.path.exists(filename3):
            size = os.path.getsize(filename3)
            print(f"✅ SUCCESS: File created, size: {size/1024:.1f} KB")
        else:
            print("❌ FAILED: File not created or command failed")
    except Exception as e:
        print(f"❌ ERROR: {e}")
    
    # Test 4: Check if any processes are interfering
    print(f"\n🔍 Test 4: Check for interfering processes")
    camera_processes = ['raspistill', 'raspivid']
    for process in camera_processes:
        try:
            result = subprocess.run(['pgrep', '-f', process], capture_output=True, text=True)
            if result.returncode == 0 and result.stdout:
                print(f"⚠️ Active {process} processes found:")
                print(result.stdout)
            else:
                print(f"✅ No {process} processes running")
        except:
            print(f"❓ Could not check {process} processes")
    
    print("\n" + "=" * 50)
    print("📋 Summary:")
    print("Compare the results above with your camera_app.py behavior")
    print("This will help identify what's different between manual and script execution")

if __name__ == "__main__":
    test_simple_photo() 