#!/usr/bin/env python3
"""
Camera Files Cleanup Script
Helps resolve ENOSPC (no space left on device) errors
"""

import os
import glob
import shutil

def check_disk_space():
    """Check available disk space"""
    try:
        total, used, free = shutil.disk_usage(os.getcwd())
        
        # Convert to MB
        free_mb = free // (1024 * 1024)
        total_mb = total // (1024 * 1024)
        used_percent = (used / total) * 100
        
        print(f"💾 Current disk usage:")
        print(f"   Total: {total_mb}MB")
        print(f"   Used: {used_percent:.1f}%")
        print(f"   Free: {free_mb}MB")
        
        return free_mb, total_mb, used_percent
        
    except Exception as e:
        print(f"❌ Error checking disk space: {e}")
        return 0, 0, 0

def count_files():
    """Count current photos and videos"""
    try:
        photos = glob.glob("photos/*.jpg")
        videos = glob.glob("videos/*.h264")
        
        photo_size = sum(os.path.getsize(f) for f in photos) // (1024 * 1024)  # MB
        video_size = sum(os.path.getsize(f) for f in videos) // (1024 * 1024)  # MB
        
        print(f"\n📊 Current files:")
        print(f"   📸 Photos: {len(photos)} files ({photo_size}MB)")
        print(f"   🎥 Videos: {len(videos)} files ({video_size}MB)")
        print(f"   📁 Total: {photo_size + video_size}MB")
        
        return len(photos), len(videos), photo_size + video_size
        
    except Exception as e:
        print(f"❌ Error counting files: {e}")
        return 0, 0, 0

def cleanup_old_files(max_photos=50, max_videos=10, confirm=True):
    """Clean up old files to free space"""
    
    if confirm:
        print(f"\n🧹 Cleanup plan:")
        print(f"   📸 Keep newest {max_photos} photos")
        print(f"   🎥 Keep newest {max_videos} videos")
        
        response = input("\nProceed with cleanup? (y/N): ").lower()
        if response != 'y':
            print("❌ Cleanup cancelled")
            return False
    
    print("\n🧹 Starting cleanup...")
    
    try:
        # Clean up old photos
        photos = glob.glob("photos/*.jpg")
        if len(photos) > max_photos:
            # Sort by modification time (oldest first)
            photos.sort(key=os.path.getmtime)
            to_remove = photos[:-max_photos]  # Keep only the newest max_photos
            
            removed_size = 0
            for photo in to_remove:
                try:
                    size = os.path.getsize(photo)
                    os.remove(photo)
                    removed_size += size
                    print(f"   🗑️ Removed: {os.path.basename(photo)}")
                except Exception as e:
                    print(f"   ❌ Failed to remove {photo}: {e}")
                    
            print(f"   📸 Removed {len(to_remove)} old photos ({removed_size//1024//1024}MB)")
        else:
            print(f"   📸 Only {len(photos)} photos, no cleanup needed")
        
        # Clean up old videos
        videos = glob.glob("videos/*.h264")
        if len(videos) > max_videos:
            # Sort by modification time (oldest first)
            videos.sort(key=os.path.getmtime)
            to_remove = videos[:-max_videos]  # Keep only the newest max_videos
            
            removed_size = 0
            for video in to_remove:
                try:
                    size = os.path.getsize(video)
                    os.remove(video)
                    removed_size += size
                    print(f"   🗑️ Removed: {os.path.basename(video)} ({size//1024//1024}MB)")
                except Exception as e:
                    print(f"   ❌ Failed to remove {video}: {e}")
                    
            print(f"   🎥 Removed {len(to_remove)} old videos ({removed_size//1024//1024}MB)")
        else:
            print(f"   🎥 Only {len(videos)} videos, no cleanup needed")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
        return False

def main():
    """Main cleanup function"""
    print("🧹 CAMERA FILES CLEANUP TOOL")
    print("=" * 40)
    print("Helps resolve ENOSPC (No space left on device) errors")
    print()
    
    # Check if we're in the right directory
    if not os.path.exists("photos") or not os.path.exists("videos"):
        print("❌ Error: photos/ and videos/ directories not found")
        print("   Run this script from your camera_app_raspi2 directory")
        return
    
    # Show current status
    free_mb, total_mb, used_percent = check_disk_space()
    photo_count, video_count, total_size = count_files()
    
    # Recommendations
    print(f"\n💡 Recommendations:")
    if free_mb < 100:
        print("🚨 CRITICAL: Very low disk space - cleanup needed immediately!")
        cleanup_old_files(max_photos=20, max_videos=5)
    elif free_mb < 500:
        print("⚠️ WARNING: Low disk space - cleanup recommended")
        cleanup_old_files(max_photos=50, max_videos=10)
    elif photo_count > 100 or video_count > 20:
        print("📁 Large number of files - consider cleanup for organization")
        cleanup_old_files(max_photos=100, max_videos=20)
    else:
        print("✅ Disk space looks OK")
        print("   You can still run manual cleanup if needed:")
        print("   python3 cleanup_files.py")
    
    # Final status
    print(f"\n📊 Final status:")
    check_disk_space()
    count_files()

if __name__ == "__main__":
    main() 