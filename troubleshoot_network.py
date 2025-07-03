#!/usr/bin/env python3
"""
Network Troubleshooting Script for PeripheralShare
Diagnoses and fixes common Windows socket permission issues.
"""

import socket
import subprocess
import sys
import os
import ctypes
import platform
from typing import List, Tuple, Dict

class NetworkTroubleshooter:
    """Diagnose and fix network issues for PeripheralShare."""
    
    def __init__(self):
        self.issues_found = []
        self.solutions_applied = []
        
    def run_full_diagnosis(self) -> Dict:
        """Run complete network diagnosis."""
        print("🔍 PeripheralShare Network Troubleshooter")
        print("=" * 50)
        
        results = {
            'admin_check': self.check_admin_privileges(),
            'port_availability': self.check_port_availability([8888, 12345]),
            'firewall_status': self.check_firewall_status(),
            'network_interfaces': self.check_network_interfaces(),
            'socket_test': self.test_socket_creation()
        }
        
        self.suggest_solutions()
        return results
    
    def check_admin_privileges(self) -> bool:
        """Check if running with administrator privileges."""
        print("\n📋 Checking administrator privileges...")
        
        try:
            is_admin = ctypes.windll.shell32.IsUserAnAdmin()
            if is_admin:
                print("✅ Running with administrator privileges")
                return True
            else:
                print("⚠️  NOT running with administrator privileges")
                self.issues_found.append("No admin privileges")
                return False
        except Exception as e:
            print(f"❌ Could not check admin status: {e}")
            return False
    
    def check_port_availability(self, ports: List[int]) -> Dict[int, bool]:
        """Check if ports are available for binding."""
        print(f"\n🔌 Checking port availability...")
        
        results = {}
        for port in ports:
            try:
                # Test if we can bind to the port
                test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                test_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                test_socket.bind(('127.0.0.1', port))
                test_socket.close()
                
                print(f"✅ Port {port} is available")
                results[port] = True
                
            except OSError as e:
                print(f"❌ Port {port} is NOT available: {e}")
                results[port] = False
                self.issues_found.append(f"Port {port} unavailable")
                
                # Check what's using the port
                self.check_port_usage(port)
        
        return results
    
    def check_port_usage(self, port: int):
        """Check what process is using a specific port."""
        try:
            result = subprocess.run(
                ['netstat', '-ano', '|', 'findstr', f':{port}'],
                shell=True, capture_output=True, text=True
            )
            
            if result.stdout:
                print(f"   📝 Port {port} usage:")
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        print(f"      {line.strip()}")
        except Exception as e:
            print(f"   ⚠️  Could not check port usage: {e}")
    
    def check_firewall_status(self) -> Dict:
        """Check Windows Firewall status."""
        print("\n🛡️  Checking Windows Firewall...")
        
        try:
            # Check firewall status
            result = subprocess.run(
                ['netsh', 'advfirewall', 'show', 'allprofiles'],
                capture_output=True, text=True, shell=True
            )
            
            if result.returncode == 0:
                output = result.stdout.lower()
                domain_on = 'state                                 on' in output
                private_on = 'state                                 on' in output
                public_on = 'state                                 on' in output
                
                if any([domain_on, private_on, public_on]):
                    print("⚠️  Windows Firewall is enabled")
                    self.issues_found.append("Firewall enabled")
                    return {'enabled': True, 'status': output}
                else:
                    print("✅ Windows Firewall is disabled")
                    return {'enabled': False, 'status': output}
            else:
                print("❌ Could not check firewall status")
                return {'enabled': None, 'error': result.stderr}
                
        except Exception as e:
            print(f"❌ Firewall check failed: {e}")
            return {'enabled': None, 'error': str(e)}
    
    def check_network_interfaces(self) -> List[str]:
        """Get available network interfaces."""
        print("\n🌐 Checking network interfaces...")
        
        try:
            # Get local IP addresses
            hostname = socket.gethostname()
            local_ips = socket.gethostbyname_ex(hostname)[2]
            local_ips = [ip for ip in local_ips if not ip.startswith("127.")]
            
            print(f"✅ Hostname: {hostname}")
            for ip in local_ips:
                print(f"✅ Local IP: {ip}")
            
            return local_ips
            
        except Exception as e:
            print(f"❌ Could not get network interfaces: {e}")
            return []
    
    def test_socket_creation(self) -> Dict:
        """Test socket creation and binding."""
        print("\n🔌 Testing socket operations...")
        
        results = {}
        
        # Test TCP socket creation
        try:
            test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            test_socket.close()
            print("✅ TCP socket creation: OK")
            results['tcp_creation'] = True
        except Exception as e:
            print(f"❌ TCP socket creation failed: {e}")
            results['tcp_creation'] = False
            self.issues_found.append("Socket creation failed")
        
        # Test binding to localhost
        try:
            test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            test_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            test_socket.bind(('127.0.0.1', 0))  # Bind to any available port
            port = test_socket.getsockname()[1]
            test_socket.close()
            print(f"✅ Localhost binding: OK (got port {port})")
            results['localhost_bind'] = True
        except Exception as e:
            print(f"❌ Localhost binding failed: {e}")
            results['localhost_bind'] = False
            self.issues_found.append("Localhost binding failed")
        
        # Test binding to all interfaces
        try:
            test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            test_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            test_socket.bind(('0.0.0.0', 0))  # Bind to all interfaces
            port = test_socket.getsockname()[1]
            test_socket.close()
            print(f"✅ All interfaces binding: OK (got port {port})")
            results['all_interfaces_bind'] = True
        except Exception as e:
            print(f"❌ All interfaces binding failed: {e}")
            results['all_interfaces_bind'] = False
            self.issues_found.append("All interfaces binding failed")
        
        return results
    
    def suggest_solutions(self):
        """Suggest solutions based on found issues."""
        print("\n🛠️  Suggested Solutions:")
        print("=" * 30)
        
        if not self.issues_found:
            print("✅ No issues found! Network should work correctly.")
            return
        
        solutions = []
        
        if "No admin privileges" in self.issues_found:
            solutions.append("""
1. Run as Administrator:
   - Right-click on PowerShell/Command Prompt
   - Select "Run as administrator"
   - Navigate to your project directory
   - Run: python src/main.py
            """)
        
        if any("Port" in issue for issue in self.issues_found):
            solutions.append("""
2. Fix Port Issues:
   - Use different ports (try 8888 instead of 12345)
   - Kill processes using the port:
     > netstat -ano | findstr :12345
     > taskkill /PID <process_id> /F
            """)
        
        if "Firewall enabled" in self.issues_found:
            solutions.append("""
3. Configure Windows Firewall:
   Option A - Add firewall exception:
   > netsh advfirewall firewall add rule name="PeripheralShare" dir=in action=allow protocol=TCP localport=8888
   
   Option B - Temporarily disable firewall (NOT RECOMMENDED):
   > netsh advfirewall set allprofiles state off
            """)
        
        if any("binding failed" in issue for issue in self.issues_found):
            solutions.append("""
4. Fix Socket Binding Issues:
   - Run Windows Network Reset:
     > netsh winsock reset
     > netsh int ip reset
   - Restart computer after running these commands
            """)
        
        for i, solution in enumerate(solutions, 1):
            print(solution)
    
    def apply_firewall_fix(self, port: int = 8888) -> bool:
        """Apply firewall exception for PeripheralShare."""
        print(f"\n🛡️  Adding firewall exception for port {port}...")
        
        try:
            # Check if running as admin
            if not ctypes.windll.shell32.IsUserAnAdmin():
                print("❌ Administrator privileges required for firewall changes")
                return False
            
            # Add inbound rule
            cmd_in = [
                'netsh', 'advfirewall', 'firewall', 'add', 'rule',
                'name=PeripheralShare-Inbound',
                'dir=in', 'action=allow', 'protocol=TCP',
                f'localport={port}'
            ]
            
            result_in = subprocess.run(cmd_in, capture_output=True, text=True)
            
            # Add outbound rule  
            cmd_out = [
                'netsh', 'advfirewall', 'firewall', 'add', 'rule',
                'name=PeripheralShare-Outbound', 
                'dir=out', 'action=allow', 'protocol=TCP',
                f'localport={port}'
            ]
            
            result_out = subprocess.run(cmd_out, capture_output=True, text=True)
            
            if result_in.returncode == 0 and result_out.returncode == 0:
                print(f"✅ Firewall exception added for port {port}")
                self.solutions_applied.append(f"Firewall exception for port {port}")
                return True
            else:
                print(f"❌ Failed to add firewall exception")
                print(f"   Inbound: {result_in.stderr}")
                print(f"   Outbound: {result_out.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Firewall configuration failed: {e}")
            return False


def main():
    """Main troubleshooting function."""
    troubleshooter = NetworkTroubleshooter()
    
    print("🚀 Starting PeripheralShare Network Diagnosis...")
    
    # Run diagnosis
    results = troubleshooter.run_full_diagnosis()
    
    # Ask if user wants to apply automatic fixes
    if troubleshooter.issues_found:
        print(f"\n❓ Found {len(troubleshooter.issues_found)} issue(s).")
        
        try:
            if input("\nApply automatic firewall fix? (y/n): ").lower().startswith('y'):
                troubleshooter.apply_firewall_fix(8888)
                troubleshooter.apply_firewall_fix(12345)
        except KeyboardInterrupt:
            print("\n👋 Troubleshooting cancelled by user")
    
    print(f"\n📊 Diagnosis complete!")
    print(f"   Issues found: {len(troubleshooter.issues_found)}")
    print(f"   Solutions applied: {len(troubleshooter.solutions_applied)}")


if __name__ == "__main__":
    main() 