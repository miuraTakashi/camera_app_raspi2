#!/usr/bin/env python3
"""
Simple test script to diagnose photo saving issues
"""

import os
import subprocess
import sys
from datetime import datetime

def test_photo_save():
    print("🔧 Testing photo save functionality...")
    print("=" * 50)
    
    # Get script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    photos_dir = os.path.join(script_dir, "photos")
    
    print(f"Script directory: {script_dir}")
    print(f"Photos directory: {photos_dir}")
    
    # Test 1: Check directory creation
    print("\n1. Testing directory creation...")
    try:
        os.makedirs(photos_dir, exist_ok=True)
        os.chmod(photos_dir, 0o755)
        print(f"✓ Directory created: {photos_dir}")
        print(f"   Exists: {os.path.exists(photos_dir)}")
        print(f"   Writable: {os.access(photos_dir, os.W_OK)}")
    except Exception as e:
        print(f"✗ Directory creation failed: {e}")
        return False
    
    # Test 2: Check if raspistill is available
    print("\n2. Testing raspistill availability...")
    try:
        result = subprocess.run(['which', 'raspistill'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ raspistill found at: {result.stdout.strip()}")
        else:
            print("✗ raspistill not found in PATH")
            print("   Install with: sudo apt-get install libraspberrypi-bin")
            return False
    except Exception as e:
        print(f"✗ Error checking raspistill: {e}")
        return False
    
    # Test 3: Try to create a test file
    print("\n3. Testing file creation...")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    test_filename = os.path.join(photos_dir, f"test_{timestamp}.txt")
    
    try:
        with open(test_filename, 'w') as f:
            f.write("Test file for photo directory")
        
        if os.path.exists(test_filename):
            size = os.path.getsize(test_filename)
            print(f"✓ Test file created: {test_filename}")
            print(f"   File size: {size} bytes")
            
            # Clean up test file
            os.remove(test_filename)
            print("✓ Test file removed")
        else:
            print(f"✗ Test file not found after creation: {test_filename}")
            return False
            
    except Exception as e:
        print(f"✗ File creation test failed: {e}")
        return False
    
    # Test 4: Try a mock raspistill command (dry run)
    print("\n4. Testing raspistill command (dry run)...")
    mock_filename = os.path.join(photos_dir, f"mock_{timestamp}.jpg")
    
    try:
        # Use raspistill help command to test if it works
        result = subprocess.run(['raspistill', '--help'], 
                              capture_output=True, text=True, timeout=5)
        
        if result.returncode == 0:
            print("✓ raspistill responds to --help")
            print("✓ Camera tools appear to be working")
        else:
            print(f"✗ raspistill --help failed: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("✗ raspistill command timed out")
        return False
    except FileNotFoundError:
        print("✗ raspistill command not found")
        return False
    except Exception as e:
        print(f"✗ Error testing raspistill: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("✅ All tests passed! Photo saving should work.")
    print("\nIf photos still aren't saving, the issue might be:")
    print("- Camera hardware not connected")
    print("- Camera not enabled (run: sudo raspi-config)")
    print("- Insufficient lighting for camera")
    print("- SD card full or read-only")
    
    return True

if __name__ == "__main__":
    success = test_photo_save()
    sys.exit(0 if success else 1) 