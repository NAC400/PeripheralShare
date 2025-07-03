#!/usr/bin/env python3
"""
Debug Connection Script for PeripheralShare
Tests each component step by step to identify exactly where issues occur.
"""

import sys
import socket
import json
import time
import threading
import logging

# Set up detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DebugServer:
    """Debug server with detailed logging."""
    
    def __init__(self, port=8888):
        self.port = port
        self.running = False
        self.clients = {}
        
    def start(self):
        """Start debug server."""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(('0.0.0.0', self.port))
            self.server_socket.listen(5)
            
            self.running = True
            logger.info(f"✅ Debug server started on port {self.port}")
            
            while self.running:
                try:
                    client_sock, address = self.server_socket.accept()
                    client_id = f"{address[0]}:{address[1]}"
                    logger.info(f"🔌 Client connected: {client_id}")
                    
                    # Handle client in thread
                    client_thread = threading.Thread(
                        target=self.handle_client, 
                        args=(client_sock, client_id)
                    )
                    client_thread.daemon = True
                    client_thread.start()
                    
                except Exception as e:
                    if self.running:
                        logger.error(f"❌ Error accepting connection: {e}")
                        
        except Exception as e:
            logger.error(f"❌ Failed to start server: {e}")
            
    def handle_client(self, client_sock, client_id):
        """Handle client with detailed debugging."""
        buffer = ""
        message_count = 0
        
        try:
            while self.running:
                data = client_sock.recv(4096)
                if not data:
                    logger.info(f"📪 Client {client_id} sent empty data (disconnected)")
                    break
                
                logger.debug(f"📥 Raw data from {client_id}: {data[:100]}...")
                
                # Add to buffer
                buffer += data.decode('utf-8')
                
                # Process messages
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    line = line.strip()
                    
                    if line:
                        message_count += 1
                        logger.info(f"📨 Message #{message_count} from {client_id}: {line[:100]}...")
                        
                        try:
                            message = json.loads(line)
                            logger.info(f"✅ Valid JSON: {message}")
                            
                            # Echo response
                            response = {
                                'type': 'echo',
                                'original': message,
                                'message_number': message_count,
                                'timestamp': time.time()
                            }
                            self.send_to_client(client_sock, response)
                            
                        except json.JSONDecodeError as e:
                            logger.error(f"❌ Invalid JSON from {client_id}: {e}")
                            logger.error(f"   Raw line: {repr(line)}")
                            
        except Exception as e:
            logger.error(f"❌ Error handling client {client_id}: {e}")
        finally:
            client_sock.close()
            logger.info(f"🔌 Client {client_id} disconnected (processed {message_count} messages)")
    
    def send_to_client(self, client_sock, message):
        """Send message to client."""
        try:
            data = (json.dumps(message) + '\n').encode('utf-8')
            client_sock.send(data)
            logger.debug(f"📤 Sent to client: {json.dumps(message)[:100]}...")
        except Exception as e:
            logger.error(f"❌ Failed to send message: {e}")
    
    def stop(self):
        """Stop server."""
        self.running = False
        if hasattr(self, 'server_socket'):
            self.server_socket.close()

class DebugClient:
    """Debug client with detailed logging."""
    
    def __init__(self):
        self.socket = None
        self.connected = False
        self.message_count = 0
        
    def connect(self, host, port):
        """Connect to server."""
        try:
            logger.info(f"🔌 Attempting to connect to {host}:{port}...")
            
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(10)
            self.socket.connect((host, port))
            
            self.connected = True
            logger.info(f"✅ Connected to {host}:{port}")
            
            # Start receive thread
            receive_thread = threading.Thread(target=self.receive_messages)
            receive_thread.daemon = True
            receive_thread.start()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to connect: {e}")
            return False
    
    def receive_messages(self):
        """Receive messages from server."""
        buffer = ""
        
        while self.connected:
            try:
                data = self.socket.recv(4096)
                if not data:
                    break
                
                logger.debug(f"📥 Raw data from server: {data[:100]}...")
                
                buffer += data.decode('utf-8')
                
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    line = line.strip()
                    
                    if line:
                        try:
                            message = json.loads(line)
                            logger.info(f"📨 Received from server: {message}")
                        except json.JSONDecodeError as e:
                            logger.error(f"❌ Invalid JSON from server: {e}")
                            logger.error(f"   Raw line: {repr(line)}")
                            
            except Exception as e:
                if self.connected:
                    logger.error(f"❌ Error receiving: {e}")
                break
        
        logger.info("📪 Receive loop ended")
    
    def send_message(self, message):
        """Send message to server."""
        if not self.connected:
            logger.error("❌ Not connected")
            return False
        
        try:
            self.message_count += 1
            message['client_message_number'] = self.message_count
            
            data = (json.dumps(message) + '\n').encode('utf-8')
            self.socket.send(data)
            logger.info(f"📤 Sent message #{self.message_count}: {json.dumps(message)[:100]}...")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from server."""
        self.connected = False
        if self.socket:
            self.socket.close()
        logger.info("🔌 Disconnected")

def test_server_mode():
    """Test server mode."""
    print("🖥️  Starting DEBUG SERVER mode...")
    print("   This will run a debug server and show detailed logs")
    print("   Connect from another machine to test")
    
    server = DebugServer(8888)
    
    try:
        server.start()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    finally:
        server.stop()

def test_client_mode():
    """Test client mode."""
    print("🔌 Starting DEBUG CLIENT mode...")
    
    host = input("Enter server IP (default: 192.168.1.100): ").strip() or "192.168.1.100"
    
    client = DebugClient()
    
    if client.connect(host, 8888):
        print("✅ Connected! Sending test messages...")
        
        # Send test messages
        test_messages = [
            {"type": "test", "message": "Hello from debug client"},
            {"type": "ping", "timestamp": time.time()},
            {"type": "input", "event_type": "mouse_move", "data": {"x": 100, "y": 200}},
            {"type": "input", "event_type": "mouse_click", "data": {"button": "left", "pressed": True}},
        ]
        
        for i, msg in enumerate(test_messages, 1):
            print(f"\n📤 Sending test message {i}/{len(test_messages)}...")
            if client.send_message(msg):
                time.sleep(2)  # Wait between messages
            else:
                print("❌ Failed to send message")
                break
        
        input("\nPress Enter to disconnect...")
        client.disconnect()
    else:
        print("❌ Failed to connect")

def test_local_loopback():
    """Test local loopback connection."""
    print("🔄 Starting LOCAL LOOPBACK test...")
    
    # Start server in thread
    server = DebugServer(8888)
    server_thread = threading.Thread(target=server.start)
    server_thread.daemon = True
    server_thread.start()
    
    time.sleep(2)  # Let server start
    
    # Test client connection
    client = DebugClient()
    if client.connect("127.0.0.1", 8888):
        print("✅ Loopback connection successful!")
        
        # Send a few test messages
        for i in range(3):
            msg = {"type": "test", "id": i, "message": f"Test message {i}"}
            client.send_message(msg)
            time.sleep(1)
        
        time.sleep(2)
        client.disconnect()
        
        print("✅ Loopback test completed successfully!")
    else:
        print("❌ Loopback test failed")
    
    server.stop()

def main():
    """Main debug function."""
    print("🔍 PeripheralShare Connection Debugger")
    print("=" * 50)
    
    print("Choose test mode:")
    print("1. Server mode (run this on server machine)")
    print("2. Client mode (connect to server)")
    print("3. Local loopback test (test on same machine)")
    print("4. Quick network test")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    if choice == "1":
        test_server_mode()
    elif choice == "2":
        test_client_mode()
    elif choice == "3":
        test_local_loopback()
    elif choice == "4":
        # Quick test
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        print(f"💻 Your machine:")
        print(f"   Hostname: {hostname}")
        print(f"   IP: {local_ip}")
        print(f"   Port 8888 test...")
        
        try:
            test_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            test_sock.bind(('0.0.0.0', 8888))
            test_sock.close()
            print("✅ Port 8888 is available")
        except Exception as e:
            print(f"❌ Port 8888 issue: {e}")
    else:
        print("Invalid choice")

if __name__ == "__main__":
    main() 