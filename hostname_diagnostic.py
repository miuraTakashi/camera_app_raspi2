#!/usr/bin/env python3
"""
Hostname Conflict Diagnostic Tool
Helps identify why .local hostnames are getting -2 suffix
"""

import subprocess
import socket
import time
import os

def run_command(cmd, description=""):
    """Run a command and return result"""
    print(f"\n{'='*60}")
    if description:
        print(f"🔍 {description}")
    print(f"Command: {cmd}")
    print(f"{'='*60}")
    
    try:
        if isinstance(cmd, str):
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        else:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        print(f"Return code: {result.returncode}")
        if result.stdout:
            print("Output:", result.stdout)
        if result.stderr:
            print("Error:", result.stderr)
        return result
    except Exception as e:
        print(f"Error: {e}")
        return None

def check_hostname_info():
    """Check hostname and network identity"""
    print("\n" + "🏷️ HOSTNAME INFORMATION" + "="*40)
    
    # Basic hostname info
    hostname = socket.gethostname()
    print(f"System hostname: {hostname}")
    
    try:
        fqdn = socket.getfqdn()
        print(f"FQDN: {fqdn}")
    except:
        print("FQDN: Could not determine")
    
    # Check files
    files_to_check = ['/etc/hostname', '/etc/hosts']
    for file_path in files_to_check:
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    content = f.read().strip()
                print(f"{file_path}: {content}")
            except Exception as e:
                print(f"{file_path}: Error reading - {e}")

def check_machine_ids():
    """Check for duplicate machine IDs"""
    print("\n" + "🔑 MACHINE ID CHECK" + "="*44)
    
    id_files = ['/etc/machine-id', '/var/lib/dbus/machine-id']
    machine_ids = {}
    
    for id_file in id_files:
        if os.path.exists(id_file):
            try:
                with open(id_file, 'r') as f:
                    machine_id = f.read().strip()
                machine_ids[id_file] = machine_id
                print(f"{id_file}: {machine_id}")
            except Exception as e:
                print(f"{id_file}: Error reading - {e}")
    
    # Check if IDs are identical (they should be)
    if len(set(machine_ids.values())) == 1:
        print("✅ Machine IDs are consistent")
    else:
        print("⚠️ Machine IDs differ - this could cause issues")

def check_network_interfaces():
    """Check network interfaces and their status"""
    print("\n" + "🌐 NETWORK INTERFACES" + "="*42)
    
    run_command("ip addr show", "Network interfaces")
    run_command("ip route show", "Routing table")

def check_avahi_status():
    """Check Avahi daemon status and configuration"""
    print("\n" + "🔊 AVAHI DAEMON STATUS" + "="*40)
    
    run_command("systemctl status avahi-daemon", "Avahi daemon status")
    run_command("avahi-browse -a -t | head -20", "Active mDNS services")
    
    # Check configuration
    config_file = "/etc/avahi/avahi-daemon.conf"
    if os.path.exists(config_file):
        print(f"\n📄 Avahi configuration ({config_file}):")
        try:
            with open(config_file, 'r') as f:
                lines = f.readlines()
            for line in lines:
                if not line.strip().startswith('#') and line.strip():
                    print(f"  {line.strip()}")
        except Exception as e:
            print(f"Error reading config: {e}")

def check_hostname_resolution():
    """Test hostname resolution"""
    print("\n" + "🔍 HOSTNAME RESOLUTION TEST" + "="*35)
    
    hostname = socket.gethostname()
    local_hostname = f"{hostname}.local"
    
    # Test resolution
    run_command(f"avahi-resolve -n {local_hostname}", f"Resolve {local_hostname}")
    run_command(f"avahi-resolve -4 -n {local_hostname}", f"Resolve {local_hostname} (IPv4)")
    run_command(f"avahi-resolve -6 -n {local_hostname}", f"Resolve {local_hostname} (IPv6)")
    
    # Check for conflicts
    run_command(f"avahi-browse -a -t | grep -i {hostname}", f"Search for {hostname} in mDNS")

def check_dhcp_info():
    """Check DHCP lease information"""
    print("\n" + "🌐 DHCP INFORMATION" + "="*43)
    
    dhcp_files = [
        "/var/lib/dhcp/dhclient.leases",
        "/var/lib/dhcpcd5/dhcpcd.leases"
    ]
    
    for dhcp_file in dhcp_files:
        if os.path.exists(dhcp_file):
            run_command(f"tail -20 {dhcp_file}", f"Recent DHCP leases from {dhcp_file}")

def monitor_mdns_traffic():
    """Monitor mDNS traffic for conflicts"""
    print("\n" + "📡 MDNS TRAFFIC MONITORING" + "="*35)
    print("Monitoring mDNS traffic for 10 seconds...")
    print("Look for duplicate announcements or conflicts...")
    
    cmd = "timeout 10 tcpdump -i any port 5353 -c 20 2>/dev/null || echo 'tcpdump not available or no traffic'"
    run_command(cmd, "Monitor mDNS traffic")

def main():
    """Main diagnostic function"""
    print("🔧 HOSTNAME CONFLICT DIAGNOSTIC TOOL")
    print("="*60)
    print("Diagnosing why .local hostnames get -2 suffix...")
    print("="*60)
    
    check_hostname_info()
    check_machine_ids()
    check_network_interfaces()
    check_avahi_status()
    check_hostname_resolution()
    check_dhcp_info()
    monitor_mdns_traffic()
    
    print("\n" + "📋 ANALYSIS SUMMARY" + "="*44)
    print("Common causes of persistent -2.local suffix:")
    print("1. 📡 Multiple network interfaces advertising same hostname")
    print("2. 🔄 mDNS cache not cleared properly")
    print("3. 🏷️ Duplicate machine IDs from cloned SD cards")
    print("4. 🌐 Router/network infrastructure caching old entries")
    print("5. ⏰ Race conditions during boot/network startup")
    print("6. 🔧 Avahi daemon configuration issues")
    
    print("\n" + "🔧 RECOMMENDED ACTIONS" + "="*40)
    print("1. Stop all camera processes and avahi:")
    print("   sudo pkill -f camera")
    print("   sudo systemctl stop avahi-daemon")
    print("2. Clear all caches:")
    print("   sudo rm -rf /var/run/avahi-daemon/*")
    print("3. Restart networking:")
    print("   sudo systemctl restart networking")
    print("   sudo systemctl start avahi-daemon")
    print("4. If problem persists, regenerate machine ID:")
    print("   sudo rm /etc/machine-id /var/lib/dbus/machine-id")
    print("   sudo systemd-machine-id-setup")
    print("   sudo reboot")

if __name__ == "__main__":
    main() 