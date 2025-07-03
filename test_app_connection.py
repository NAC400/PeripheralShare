#!/usr/bin/env python3
"""
Test script that mimics PeripheralShare app connection logic exactly.
This will help isolate if the issue is in the app code or system level.
"""

import socket
import threading
import json
import time
import logging

# Set up logging like the app does
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestPeripheralServer:
    """Simplified version of PeripheralServer for testing."""
    
    def __init__(self, port=8888):
        self.port = port
        self.server_socket = None
        self.running = False
        
    def start(self):
        """Start the test server exactly like the real app."""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(('0.0.0.0', self.port))
            self.server_socket.listen(5)
            
            self.running = True
            logger.info(f"Test server started on port {self.port}")
            
            # Accept connections
            while self.running:
                try:
                    client_sock, address = self.server_socket.accept()
                    logger.info(f"Client connected from {address}")
                    
                    # Handle client in thread
                    client_thread = threading.Thread(
                        target=self.handle_client, 
                        args=(client_sock, address)
                    )
                    client_thread.daemon = True
                    client_thread.start()
                    
                except Exception as e:
                    if self.running:
                        logger.error(f"Error accepting connection: {e}")
                        
        except Exception as e:
            logger.error(f"Failed to start server: {e}")
            return False
            
    def handle_client(self, client_sock, address):
        """Handle client connection exactly like the real app."""
        try:
            while self.running:
                data = client_sock.recv(4096)
                if not data:
                    break
                
                try:
                    message = json.loads(data.decode('utf-8'))
                    logger.info(f"Received from {address}: {message}")
                    
                    # Send response
                    response = {"status": "received", "echo": message}
                    client_sock.send(json.dumps(response).encode('utf-8'))
                    
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON from {address}")
                    
        except Exception as e:
            logger.error(f"Error handling client {address}: {e}")
        finally:
            client_sock.close()
            logger.info(f"Client {address} disconnected")
    
    def stop(self):
        """Stop the server."""
        self.running = False
        if self.server_socket:
            self.server_socket.close()

class TestPeripheralClient:
    """Simplified version of PeripheralClient for testing."""
    
    def __init__(self):
        self.socket = None
        self.connected = False
        
    def connect(self, host, port):
        """Connect to server exactly like the real app."""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(10)  # 10 second timeout like the real app
            
            logger.info(f"Attempting to connect to {host}:{port}...")
            self.socket.connect((host, port))
            self.connected = True
            
            logger.info(f"Connected to {host}:{port}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to {host}:{port}: {e}")
            return False
    
    def send_message(self, message):
        """Send message exactly like the real app."""
        if not self.connected:
            return False
            
        try:
            data = json.dumps(message).encode('utf-8')
            self.socket.send(data)
            
            # Receive response
            response_data = self.socket.recv(4096)
            response = json.loads(response_data.decode('utf-8'))
            logger.info(f"Received response: {response}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from server."""
        self.connected = False
        if self.socket:
            self.socket.close()

def test_server_mode():
    """Test running as server."""
    print("🚀 Testing Server Mode...")
    server = TestPeripheralServer(8888)
    
    # Start server in thread
    server_thread = threading.Thread(target=server.start)
    server_thread.daemon = True
    server_thread.start()
    
    # Give server time to start
    time.sleep(2)
    
    print("✅ Server started, waiting for connections...")
    print("   (Server will run for 30 seconds)")
    
    # Keep server running for 30 seconds
    time.sleep(30)
    server.stop()
    print("🛑 Server stopped")

def test_client_mode(host):
    """Test running as client."""
    print(f"🔌 Testing Client Mode connecting to {host}...")
    
    client = TestPeripheralClient()
    
    # Try to connect
    if client.connect(host, 8888):
        # Send test messages
        test_messages = [
            {"type": "test", "message": "Hello from test client"},
            {"type": "ping", "timestamp": time.time()},
            {"type": "data", "payload": "Test payload data"}
        ]
        
        for msg in test_messages:
            print(f"📤 Sending: {msg}")
            if client.send_message(msg):
                print("✅ Message sent successfully")
            else:
                print("❌ Failed to send message")
            time.sleep(1)
        
        client.disconnect()
        print("✅ Client test completed")
        return True
    else:
        print("❌ Client test failed - could not connect")
        return False

def main():
    """Main test function."""
    print("🧪 PeripheralShare App Connection Test")
    print("=" * 50)
    
    # Get local IP
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    
    print(f"💻 Your PC IP: {local_ip}")
    print(f"🔧 Test Port: 8888")
    
    print("\nChoose test mode:")
    print("1. Server mode (run this on your PC)")
    print("2. Client mode (test connecting to your PC)")
    print("3. Localhost test (test both on this machine)")
    
    try:
        choice = input("\nEnter choice (1-3): ").strip()
        
        if choice == "1":
            print(f"\n🖥️  Starting SERVER mode...")
            print(f"   Your server IP: {local_ip}")
            print(f"   Connect from laptop using: {local_ip}:8888")
            test_server_mode()
            
        elif choice == "2":
            server_ip = input(f"\nEnter server IP (default {local_ip}): ").strip() or local_ip
            test_client_mode(server_ip)
            
        elif choice == "3":
            print(f"\n🔄 Running localhost test...")
            
            # Start server
            server = TestPeripheralServer(8888)
            server_thread = threading.Thread(target=server.start)
            server_thread.daemon = True
            server_thread.start()
            time.sleep(2)
            
            # Test client
            success = test_client_mode("127.0.0.1")
            
            server.stop()
            
            if success:
                print(f"\n✅ Localhost test PASSED!")
                print(f"   The app code works correctly")
                print(f"   Issue is likely network-related between PC and laptop")
            else:
                print(f"\n❌ Localhost test FAILED!")
                print(f"   Issue is in the app code or system configuration")
        else:
            print("Invalid choice")
            
    except KeyboardInterrupt:
        print("\n👋 Test cancelled by user")

if __name__ == "__main__":
    main() 