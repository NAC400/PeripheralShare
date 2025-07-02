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
            data = json.dumps(message).encode('utf-8')
            self.socket.send(data)
        except Exception as e:
            self.logger.error(f"Failed to send message: {e}")
            self._handle_disconnect("Send error")
    
    def _receive_messages(self):
        """Receive messages from server."""
        while self.connected_status and self.socket:
            try:
                data = self.socket.recv(4096)
                if not data:
                    break
                
                try:
                    message = json.loads(data.decode('utf-8'))
                    self.data_received.emit(message)
                except json.JSONDecodeError:
                    self.logger.error("Invalid JSON from server")
                    
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