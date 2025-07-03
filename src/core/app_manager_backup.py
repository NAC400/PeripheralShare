"""
Main application manager for PeripheralShare.
Coordinates all subsystems including network, input, audio, and file transfer.
"""

import logging
import threading
import time
from typing import Dict, List, Optional, Callable
from PyQt6.QtCore import QObject, pyqtSignal

from src.network.server import PeripheralServer
from src.network.client import PeripheralClient
from src.network.discovery import NetworkDiscovery
from src.input.manager import InputManager
from src.audio.manager import AudioManager
from src.utils.logger import NetworkLogger, InputLogger, AudioLogger

class AppManager(QObject):
    """Main application manager coordinating all subsystems."""
    
    # Signals for UI updates
    connection_status_changed = pyqtSignal(bool, str)  # connected, device_name
    device_discovered = pyqtSignal(str, str, int)      # device_name, ip, port
    input_event_received = pyqtSignal(str, dict)       # event_type, data
    audio_status_changed = pyqtSignal(bool, str)       # enabled, device_name
    file_transfer_progress = pyqtSignal(str, int)      # filename, progress
    error_occurred = pyqtSignal(str, str)              # error_type, message
    
    def __init__(self, config):
        """Initialize the application manager."""
        super().__init__()
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Subsystem managers
        self.input_manager = None
        self.audio_manager = None
        self.network_discovery = None
        self.server = None
        self.client = None
        
        # State tracking
        self.is_server = False
        self.is_connected = False
        self.connected_device = None
        self.running = False
        
        # Threading
        self._main_thread = None
        self._shutdown_event = threading.Event()
        
        # Loggers
        self.network_logger = NetworkLogger()
        self.input_logger = InputLogger()
        self.audio_logger = AudioLogger()
        
        self._initialize_subsystems()
        self.logger.info("AppManager initialized successfully")
    
    def _initialize_subsystems(self):
        """Initialize all subsystem managers."""
        try:
            # Initialize input manager
            self.input_manager = InputManager(self.config)
            self.input_manager.input_captured.connect(self._on_input_captured)
            
            # Initialize audio manager
            if self.config.get('audio.enabled', True):
                self.audio_manager = AudioManager(self.config)
                self.audio_manager.status_changed.connect(self._on_audio_status_changed)
            
            # Initialize network discovery
            self.network_discovery = NetworkDiscovery(self.config)
            self.network_discovery.device_found.connect(self._on_device_discovered)
            
            self.logger.info("All subsystems initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize subsystems: {e}")
            self.error_occurred.emit("initialization", str(e))
    
    def start_as_server(self, port: Optional[int] = None) -> bool:
        """Start the application as a server (primary device)."""
        try:
            if self.is_connected:
                self.logger.warning("Already connected as client")
                return False
            
            port = port or self.config.get('network.port', 8888)
            
            self.logger.info(f"🚀 Starting REAL server on port {port}...")
            
            # Start server
            self.server = PeripheralServer(self.config, port)
            self.server.client_connected.connect(self._on_client_connected)
            self.server.client_disconnected.connect(self._on_client_disconnected)
            self.server.data_received.connect(self._on_data_received)
            
            if self.server.start():
                self.is_server = True
                self.running = True
                
                # Start network discovery for incoming connections
                self.network_discovery.start_advertising(port)
                
                # Start input capture
                self.input_manager.start_capture()
                
                # Start audio management
                if self.audio_manager:
                    self.audio_manager.start()
                
                self.logger.info(f"✅ Server started successfully on port {port}")
                self.connection_status_changed.emit(True, f"Server (Port {port})")
                return True
            else:
                self.logger.error("❌ Failed to start server")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error starting server: {e}")
            self.error_occurred.emit("server_start", str(e))
            return False
    
    def connect_to_server(self, host: str, port: int) -> bool:
        """Connect to a server as a client (secondary device)."""
        try:
            if self.is_connected:
                self.logger.warning("Already connected")
                return False
            
            self.logger.info(f"🔗 Connecting to server at {host}:{port}...")
            
            # Create client
            self.client = PeripheralClient(self.config)
            self.client.connected.connect(self._on_server_connected)
            self.client.disconnected.connect(self._on_server_disconnected)
            self.client.data_received.connect(self._on_data_received)
            
            if self.client.connect(host, port):
                self.is_server = False
                self.running = True
                
                # Start input capture
                self.input_manager.start_capture()
                
                # Start audio management
                if self.audio_manager:
                    self.audio_manager.start()
                
                self.logger.info(f"✅ Connected to server at {host}:{port}")
                return True
            else:
                self.logger.error(f"❌ Failed to connect to {host}:{port}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error connecting to server: {e}")
            self.error_occurred.emit("client_connect", str(e))
            return False
    
    def disconnect(self):
        """Disconnect from current session."""
        try:
            self.logger.info("Disconnecting...")
            
            # Stop input capture
            if self.input_manager:
                self.input_manager.stop_capture()
            
            # Stop audio management
            if self.audio_manager:
                self.audio_manager.stop()
            
            # Close network connections
            if self.server:
                self.server.stop()
                self.server = None
            
            if self.client:
                self.client.disconnect()
                self.client = None
            
            # Stop network discovery
            if self.network_discovery:
                self.network_discovery.stop()
            
            # Update state
            self.is_connected = False
            self.is_server = False
            self.connected_device = None
            self.running = False
            
            self.connection_status_changed.emit(False, "")
            self.logger.info("Disconnected successfully")
            
        except Exception as e:
            self.logger.error(f"Error during disconnect: {e}")
    
    def shutdown(self):
        """Shutdown the application manager."""
        self.logger.info("Shutting down application manager...")
        
        self._shutdown_event.set()
        self.disconnect()
        
        # Cleanup subsystems
        if self.input_manager:
            self.input_manager.cleanup()
        
        if self.audio_manager:
            self.audio_manager.cleanup()
        
        if self.network_discovery:
            self.network_discovery.cleanup()
        
        self.logger.info("Application manager shutdown complete")
    
    def send_input_event(self, event_type: str, data: dict):
        """Send input event to connected device."""
        if not self.is_connected:
            return
        
        try:
            message = {
                'type': 'input',
                'event_type': event_type,
                'data': data,
                'timestamp': time.time()
            }
            
            if self.is_server and self.server:
                self.server.broadcast_message(message)
            elif self.client:
                self.client.send_message(message)
                
            self.input_logger.mouse_event(event_type, data.get('x'), data.get('y'))
            
        except Exception as e:
            self.logger.error(f"Failed to send input event: {e}")
    
    def send_file(self, file_path: str, target_device: str = None):
        """Send file to connected device."""
        # Implementation for file transfer
        pass
    
    # Signal handlers
    def _on_input_captured(self, event_type: str, data: dict):
        """Handle input events captured locally."""
        # Send to connected clients if we're the server
        if self.is_server and self.server:
            message = {
                'type': 'input_event',
                'event_type': event_type,
                'data': data
            }
            self.server.broadcast_message(message)
        
        # Send to server if we're a client
        elif not self.is_server and self.client:
            message = {
                'type': 'input_event',
                'event_type': event_type,
                'data': data
            }
            self.client.send_message(message)
    
    def _on_client_connected(self, client_info: dict):
        """Handle client connection to our server."""
        device_name = client_info.get('device_name', 'Unknown Device')
        address = client_info.get('address', ['unknown', 0])
        self.logger.info(f"Client connected: {device_name} from {address[0]}")
        self.connection_status_changed.emit(True, device_name)
    
    def _on_client_disconnected(self, client_info: dict):
        """Handle client disconnection from our server."""
        device_name = client_info.get('device_name', 'Unknown Device')
        self.logger.info(f"Client disconnected: {device_name}")
        # Note: Keep server running for new connections
    
    def _on_server_connected(self, server_info: dict):
        """Handle successful connection to server."""
        device_name = server_info.get('device_name', 'Server Device')
        self.is_connected = True
        self.connected_device = device_name
        self.logger.info(f"Connected to server: {device_name}")
        self.connection_status_changed.emit(True, device_name)
    
    def _on_server_disconnected(self, reason: str):
        """Handle disconnection from server."""
        self.logger.warning(f"Disconnected from server: {reason}")
        self.is_connected = False
        self.connected_device = None
        self.connection_status_changed.emit(False, "")
    
    def _on_data_received(self, message: dict):
        """Handle data received from network."""
        try:
            msg_type = message.get('type')
            
            if msg_type == 'input_event':
                # Inject the input event locally
                event_type = message.get('event_type')
                data = message.get('data', {})
                
                if self.input_manager:
                    self.input_manager.inject_input(event_type, data)
                
                self.input_event_received.emit(event_type, data)
                
            elif msg_type == 'file_transfer':
                self._handle_file_transfer(message)
                
            else:
                self.logger.warning(f"Unknown message type: {msg_type}")
                
        except Exception as e:
            self.logger.error(f"Error processing received data: {e}")
    
    def _on_device_discovered(self, device_name: str, address: str, port: int):
        """Handle discovered network device."""
        self.device_discovered.emit(device_name, address, port)
    
    def _on_audio_status_changed(self, enabled: bool, device_name: str):
        """Handle audio status changes."""
        self.audio_status_changed.emit(enabled, device_name)
    
    def _handle_file_transfer(self, message: dict):
        """Handle file transfer messages."""
        # Placeholder for file transfer functionality
        self.logger.info("File transfer functionality not yet implemented")
    
    # Public API
    def get_status(self) -> Dict:
        """Get current application status."""
        return {
            'running': self.running,
            'is_server': self.is_server,
            'is_connected': self.is_connected,
            'connected_device': self.connected_device,
            'server_port': self.server.port if self.server else None,
            'input_capture_active': self.input_manager.is_capturing if self.input_manager else False
        }
    
    def get_network_info(self) -> Dict:
        """Get network connection information."""
        info = {}
        
        if self.server:
            info.update(self.server.get_info())
        elif self.client:
            info.update(self.client.get_info())
        
        return info 