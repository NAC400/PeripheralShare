"""
Network server for PeripheralShare.
Handles incoming client connections and message routing.
"""

import socket
import threading
import json
import logging
from typing import Dict, List, Optional
from PyQt6.QtCore import QObject, pyqtSignal
import platform
try:
    from screeninfo import get_monitors
except ImportError:
    get_monitors = None

class PeripheralServer(QObject):
    """Server for handling client connections."""
    
    # Signals
    client_connected = pyqtSignal(dict)    # client_info
    client_disconnected = pyqtSignal(dict) # client_info
    data_received = pyqtSignal(dict)       # message
    
    def __init__(self, config, port: int = 8888):
        """Initialize the server."""
        super().__init__()
        self.config = config
        self.port = port
        self.logger = logging.getLogger(__name__)
        
        self.server_socket = None
        self.clients = {}
        self.running = False
        self._accept_thread = None
        self.devices = {}  # device_id -> info
    
    def start(self) -> bool:
        """Start the server."""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(('0.0.0.0', self.port))
            self.server_socket.listen(5)
            # Register own device info
            self.register_own_device()
            self.running = True
            self._accept_thread = threading.Thread(target=self._accept_connections)
            self._accept_thread.daemon = True
            self._accept_thread.start()
            self.logger.info(f"Server started on port {self.port}")
            return True
            
        except OSError as e:
            # Windows socket permission errors
            if e.errno == 10013:  # WinError 10013
                self.logger.error(f"Socket permission denied (WinError 10013) on port {self.port}")
                self.logger.error("Try running as administrator or use a different port")
                self.logger.error("Run 'python troubleshoot_network.py' for detailed diagnosis")
            elif e.errno == 10048:  # Address already in use
                self.logger.error(f"Port {self.port} is already in use")
                self.logger.error("Try using a different port or kill the process using this port")
            else:
                self.logger.error(f"Socket error {e.errno}: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Failed to start server: {e}")
            return False
    
    def stop(self):
        """Stop the server."""
        self.running = False
        
        if self.server_socket:
            self.server_socket.close()
        
        # Close all client connections
        for client_id in list(self.clients.keys()):
            self._disconnect_client(client_id)
        
        self.logger.info("Server stopped")
    
    def broadcast_message(self, message: dict):
        """Broadcast message to all connected clients."""
        for client_id, client_info in self.clients.items():
            self._send_to_client(client_id, message)
    
    def _accept_connections(self):
        """Accept incoming client connections."""
        while self.running:
            try:
                if self.server_socket:
                    client_sock, address = self.server_socket.accept()
                    client_id = f"{address[0]}:{address[1]}"
                    
                    self.clients[client_id] = {
                        'socket': client_sock,
                        'address': address,
                        'device_name': 'Unknown Device'
                    }
                    
                    # Start client handler thread
                    client_thread = threading.Thread(
                        target=self._handle_client, 
                        args=(client_id,)
                    )
                    client_thread.daemon = True
                    client_thread.start()
                    
                    self.client_connected.emit(self.clients[client_id])
                    
            except Exception as e:
                if self.running:
                    self.logger.error(f"Error accepting connection: {e}")
    
    def _handle_client(self, client_id: str):
        """Handle messages from a specific client."""
        client_info = self.clients.get(client_id)
        if not client_info:
            return
        
        client_sock = client_info['socket']
        buffer = ""
        
        try:
            while self.running and client_id in self.clients:
                data = client_sock.recv(4096)
                if not data:
                    break
                
                # Add received data to buffer
                buffer += data.decode('utf-8')
                
                # Process complete messages (delimited by newlines)
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    line = line.strip()
                    
                    if line:  # Skip empty lines
                        try:
                            message = json.loads(line)
                            # Handle device_info messages
                            if message.get('type') == 'device_info':
                                self.logger.info(f"Registered device info from {client_id}: {message}")
                                self.devices[client_id] = message
                            self.data_received.emit(message)
                        except json.JSONDecodeError as e:
                            self.logger.error(f"Invalid JSON from client {client_id}: {line[:100]}... Error: {e}")
                    
        except Exception as e:
            self.logger.error(f"Error handling client {client_id}: {e}")
        finally:
            self._disconnect_client(client_id)
    
    def _send_to_client(self, client_id: str, message: dict):
        """Send message to specific client."""
        client_info = self.clients.get(client_id)
        if not client_info:
            return
        
        try:
            # Add newline delimiter for message framing
            data = (json.dumps(message) + '\n').encode('utf-8')
            client_info['socket'].send(data)
        except Exception as e:
            self.logger.error(f"Failed to send to client {client_id}: {e}")
            self._disconnect_client(client_id)
    
    def _disconnect_client(self, client_id: str):
        """Disconnect a specific client."""
        if client_id in self.clients:
            client_info = self.clients.pop(client_id)
            try:
                client_info['socket'].close()
            except:
                pass
            
            self.client_disconnected.emit(client_info)
            self.logger.info(f"Client {client_id} disconnected")
    
    def get_info(self) -> Dict:
        """Get server information."""
        return {
            'port': self.port,
            'running': self.running,
            'client_count': len(self.clients)
        }
    
    def get_devices(self):
        return self.devices 
    
    def register_own_device(self):
        info = {
            'type': 'device_info',
            'hostname': platform.node(),
            'platform': platform.system(),
            'screen_count': 1,
            'screens': []
        }
        if get_monitors:
            screens = []
            for m in get_monitors():
                screens.append({
                    'width': m.width,
                    'height': m.height,
                    'x': m.x,
                    'y': m.y,
                    'name': getattr(m, 'name', None)
                })
            info['screen_count'] = len(screens)
            info['screens'] = screens
        self.devices['server'] = info 