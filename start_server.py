#!/usr/bin/env python3
"""
PeripheralShare Server Starter
Runs network diagnostics and starts the server with proper error handling.
"""

import sys
import os
import subprocess
import ctypes
import platform

def check_admin_privileges():
    """Check if running with administrator privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_troubleshooter():
    """Run the network troubleshooter."""
    print("🔧 Running network troubleshooter...")
    try:
        result = subprocess.run([sys.executable, "troubleshoot_network.py"], 
                              cwd=os.path.dirname(__file__))
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Could not run troubleshooter: {e}")
        return False

def start_server():
    """Start the PeripheralShare server."""
    print("\n🚀 Starting PeripheralShare server...")
    
    # Change to project directory
    project_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_dir)
    
    try:
        # Run the main application
        subprocess.run([sys.executable, "src/main.py"], cwd=project_dir)
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")

def main():
    """Main function."""
    print("=" * 60)
    print("🖥️  PeripheralShare Server Starter")
    print("=" * 60)
    
    # Check Windows version
    if platform.system() != "Windows":
        print("⚠️  This script is designed for Windows")
        print("   You can still try running: python src/main.py")
        return
    
    # Check admin privileges
    is_admin = check_admin_privileges()
    if not is_admin:
        print("⚠️  NOT running as administrator")
        print("   Some network features may not work properly")
        print("   Consider running as administrator for best results")
        print()
        
        response = input("Continue anyway? (y/n): ").lower()
        if not response.startswith('y'):
            print("👋 Exiting. Run as administrator for full functionality.")
            return
    
    # Ask if user wants to run troubleshooter
    print("\n❓ Network troubleshooting options:")
    print("   1. Run troubleshooter first (recommended)")
    print("   2. Start server directly")
    print("   3. Run troubleshooter only")
    
    try:
        choice = input("\nChoose option (1-3): ").strip()
        
        if choice == "1":
            # Run troubleshooter then start server
            run_troubleshooter()
            print("\n" + "="*40)
            start_server()
        elif choice == "2":
            # Start server directly
            start_server()
        elif choice == "3":
            # Run troubleshooter only
            run_troubleshooter()
        else:
            print("❌ Invalid choice. Starting server directly...")
            start_server()
            
    except KeyboardInterrupt:
        print("\n👋 Cancelled by user")

if __name__ == "__main__":
    main() 