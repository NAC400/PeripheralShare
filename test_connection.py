#!/usr/bin/env python3
"""
Simple connection test for PeripheralShare
Tests each step of the connection process to isolate the exact issue.
"""

import socket
import sys
import time
import threading

def test_server_bind(port=8888):
    """Test if we can bind to the server port."""
    print(f"🔍 Testing server bind on port {port}...")
    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(('0.0.0.0', port))
        server_socket.listen(1)
        print(f"✅ SUCCESS: Server can bind to port {port}")
        server_socket.close()
        return True
    except Exception as e:
        print(f"❌ FAILED: Cannot bind to port {port}: {e}")
        return False

def test_client_connect(host='127.0.0.1', port=8888):
    """Test if client can connect to localhost."""
    print(f"🔍 Testing client connection to {host}:{port}...")
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.settimeout(5)
        client_socket.connect((host, port))
        print(f"✅ SUCCESS: Client can connect to {host}:{port}")
        client_socket.close()
        return True
    except Exception as e:
        print(f"❌ FAILED: Cannot connect to {host}:{port}: {e}")
        return False

def start_test_server(port=8888):
    """Start a simple test server."""
    print(f"🚀 Starting test server on port {port}...")
    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(('0.0.0.0', port))
        server_socket.listen(1)
        print(f"✅ Test server listening on port {port}")
        
        # Accept one connection
        print("⏳ Waiting for connection...")
        client_socket, address = server_socket.accept()
        print(f"✅ Connection received from {address}")
        
        # Send a test message
        client_socket.send(b"Hello from test server!")
        data = client_socket.recv(1024)
        print(f"📨 Received: {data.decode()}")
        
        client_socket.close()
        server_socket.close()
        print("✅ Test server completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Test server failed: {e}")
        return False

def test_connection_full(host='127.0.0.1', port=8888):
    """Test full client-server connection."""
    print(f"🔍 Testing full connection to {host}:{port}...")
    
    def server_thread():
        try:
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind(('0.0.0.0', port))
            server_socket.listen(1)
            print(f"  📡 Server listening on port {port}")
            
            client_socket, address = server_socket.accept()
            print(f"  ✅ Server accepted connection from {address}")
            
            client_socket.send(b"Test message from server")
            data = client_socket.recv(1024)
            print(f"  📨 Server received: {data.decode()}")
            
            client_socket.close()
            server_socket.close()
            
        except Exception as e:
            print(f"  ❌ Server thread error: {e}")
    
    # Start server in background
    server = threading.Thread(target=server_thread)
    server.daemon = True
    server.start()
    
    # Give server time to start
    time.sleep(1)
    
    # Test client connection
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.settimeout(10)
        client_socket.connect((host, port))
        print(f"  ✅ Client connected to {host}:{port}")
        
        data = client_socket.recv(1024)
        print(f"  📨 Client received: {data.decode()}")
        
        client_socket.send(b"Test message from client")
        client_socket.close()
        print(f"  ✅ Full connection test successful")
        return True
        
    except Exception as e:
        print(f"  ❌ Client connection failed: {e}")
        return False

def get_local_ips():
    """Get local IP addresses."""
    print("🌐 Getting local IP addresses...")
    try:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        print(f"  📍 Hostname: {hostname}")
        print(f"  📍 Primary IP: {local_ip}")
        
        # Get all IPs
        try:
            all_ips = socket.gethostbyname_ex(hostname)[2]
            for ip in all_ips:
                if not ip.startswith("127."):
                    print(f"  📍 Network IP: {ip}")
        except:
            pass
            
        return local_ip
    except Exception as e:
        print(f"  ❌ Could not get local IP: {e}")
        return "127.0.0.1"

def main():
    """Run all connection tests."""
    print("🔍 PeripheralShare Connection Diagnostics")
    print("=" * 50)
    
    # Get network info
    local_ip = get_local_ips()
    
    print(f"\n📋 Test Summary:")
    print(f"  Local IP: {local_ip}")
    print(f"  Test Port: 8888")
    
    print(f"\n🧪 Running Tests:")
    
    # Test 1: Can we bind to the port?
    test1 = test_server_bind(8888)
    
    if test1:
        # Test 2: Full connection test
        print(f"\n" + "-" * 30)
        test2 = test_connection_full('127.0.0.1', 8888)
        
        if test2:
            print(f"\n✅ ALL TESTS PASSED!")
            print(f"Network setup is working correctly.")
            print(f"\nNext steps:")
            print(f"1. Start your server: python src/main.py")
            print(f"2. Connect from laptop using IP: {local_ip}")
            print(f"3. Use port: 8888")
        else:
            print(f"\n❌ Connection test failed")
            print(f"There may be a software issue blocking connections")
    else:
        print(f"\n❌ Cannot bind to port 8888")
        print(f"Try a different port or check what's using port 8888")
    
    print(f"\n" + "=" * 50)

if __name__ == "__main__":
    main() 