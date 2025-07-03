"""
Network client for PeripheralShare.
Handles connection to server and message transmission.
"""

import socket
import threading
import json
import logging
from typing import Dict, Optional
from PyQt6.QtCore import QObject, pyqtSignal
import platform
try:
    from screeninfo import get_monitors
except ImportError:
    get_monitors = None

class PeripheralClient(QObject):
    """Client for connecting to PeripheralShare server."""
    
    # Signals
    connected = pyqtSignal(dict)       # server_info
    disconnected = pyqtSignal(str)     # reason
    data_received = pyqtSignal(dict)   # message
    
    def __init__(self, config):
        """Initialize the client."""
        super().__init__()
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        self.socket = None
        self.server_address = None
        self.connected_status = False
        self._receive_thread = None
    
    def connect(self, host: str, port: int) -> bool:
        """Connect to server."""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(10)  # 10 second timeout
            
            self.socket.connect((host, port))
            self.server_address = (host, port)
            self.connected_status = True
            
            # Send device info after connecting
            self.send_device_info()
            
            # Start receive thread
            self._receive_thread = threading.Thread(target=self._receive_messages)
            self._receive_thread.daemon = True
            self._receive_thread.start()
            
            server_info = {
                'address': f"{host}:{port}",
                'device_name': 'Server Device'
            }
            self.connected.emit(server_info)
            
            self.logger.info(f"Connected to server at {host}:{port}")
            return True
            
        except OSError as e:
            # Windows socket permission errors
            if e.errno == 10013:  # WinError 10013
                self.logger.error(f"Socket permission denied (WinError 10013) connecting to {host}:{port}")
                self.logger.error("This may be a firewall issue or the server is not accessible")
                self.logger.error("Run 'python troubleshoot_network.py' for detailed diagnosis")
            elif e.errno == 10061:  # Connection refused
                self.logger.error(f"Connection refused to {host}:{port}")
                self.logger.error("Server may not be running or port is incorrect")
            elif e.errno == 10060:  # Connection timed out
                self.logger.error(f"Connection timed out to {host}:{port}")
                self.logger.error("Check if the server IP and port are correct")
            else:
                self.logger.error(f"Socket error {e.errno} connecting to {host}:{port}: {e}")
            self.connected_status = False
            return False
        except Exception as e:
            self.logger.error(f"Failed to connect to {host}:{port}: {e}")
            self.connected_status = False
            return False
    
    def disconnect(self):
        """Disconnect from server."""
        self.connected_status = False
        
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
        
        self.disconnected.emit("User requested disconnect")
        self.logger.info("Disconnected from server")
    
    def send_message(self, message: dict):
        """Send message to server."""
        if not self.connected_status or not self.socket:
            return
        
        try:
            # Add newline delimiter for message framing
            data = (json.dumps(message) + '\n').encode('utf-8')
            self.socket.send(data)
        except Exception as e:
            self.logger.error(f"Failed to send message: {e}")
            self._handle_disconnect("Send error")
    
    def _receive_messages(self):
        """Receive messages from server."""
        buffer = ""
        
        while self.connected_status and self.socket:
            try:
                data = self.socket.recv(4096)
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
                            self.data_received.emit(message)
                        except json.JSONDecodeError as e:
                            self.logger.error(f"Invalid JSON from server: {line[:100]}... Error: {e}")
                    
            except Exception as e:
                if self.connected_status:
                    self.logger.error(f"Error receiving data: {e}")
                break
        
        if self.connected_status:
            self._handle_disconnect("Connection lost")
    
    def _handle_disconnect(self, reason: str):
        """Handle disconnection."""
        self.connected_status = False
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
        
        self.disconnected.emit(reason)
        self.logger.warning(f"Disconnected: {reason}")
    
    def get_info(self) -> Dict:
        """Get client information."""
        return {
            'connected': self.connected_status,
            'server_address': self.server_address
        }
    
    def send_device_info(self):
        """Send device info to server after connecting."""
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
        self.send_message(info) 