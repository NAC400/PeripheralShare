import logging
from PyQt6.QtCore import QObject, pyqtSignal
from src.network.server import PeripheralServer
from src.network.client import PeripheralClient
from src.input.manager import InputManager
from src.core.desktop_manager import SeamlessDesktopManager

class AppManager(QObject):
    connection_status_changed = pyqtSignal(bool, str)
    
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.desktop_manager = SeamlessDesktopManager(config)
        self.input_manager = InputManager(config)
        self.server = None
        self.client = None
        self.is_server_mode = False
        self.logger.info("AppManager initialized")
    
    def start_as_server(self, port=12345):
        """Start the application as a server."""
        try:
            self.logger.info("Starting seamless desktop server...")
            
            # Start network server
            self.server = PeripheralServer(self.config, port)
            if not self.server.start():
                self.logger.error("Failed to start network server")
                return False
            
            # Connect server signals
            self.server.client_connected.connect(self._on_client_connected)
            self.server.client_disconnected.connect(self._on_client_disconnected)
            self.server.data_received.connect(self._on_server_data_received)
            
            # Start edge tracking for seamless desktop
            self.desktop_manager.start_edge_tracking()
            
            self.is_server_mode = True
            self.connection_status_changed.emit(True, f"Server running on port {port}")
            self.logger.info(f"Server started successfully on port {port}")
            print("Move mouse to edges to switch devices!")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start server: {e}")
            self.connection_status_changed.emit(False, f"Server start failed: {e}")
            return False
    
    def stop_server(self):
        """Stop the server."""
        if self.server:
            self.server.stop()
            self.server = None
        
        if self.desktop_manager.mouse_listener:
            self.desktop_manager.mouse_listener.stop()
            self.desktop_manager.mouse_listener = None
        
        self.is_server_mode = False
        self.connection_status_changed.emit(False, "Server stopped")
        self.logger.info("Server stopped")
    
    def connect_to_server(self, host, port=12345):
        """Connect to a server as a client."""
        try:
            self.logger.info(f"Connecting to server at {host}:{port}...")
            
            # Create client if it doesn't exist
            if not self.client:
                self.client = PeripheralClient(self.config)
                self.client.connected.connect(self._on_connected_to_server)
                self.client.disconnected.connect(self._on_disconnected_from_server)
                self.client.data_received.connect(self._on_client_data_received)
            
            # Attempt connection
            success = self.client.connect(host, port)
            if success:
                self.connection_status_changed.emit(True, f"Connected to {host}:{port}")
                self.logger.info(f"Successfully connected to {host}:{port}")
                return True
            else:
                self.connection_status_changed.emit(False, f"Failed to connect to {host}:{port}")
                self.logger.error(f"Failed to connect to {host}:{port}")
                return False
                
        except Exception as e:
            self.logger.error(f"Connection error: {e}")
            self.connection_status_changed.emit(False, f"Connection error: {e}")
            return False
    
    def disconnect_from_server(self):
        """Disconnect from server."""
        if self.client:
            self.client.disconnect()
            self.client = None
        
        self.connection_status_changed.emit(False, "Disconnected from server")
        self.logger.info("Disconnected from server")
    
    def _on_client_connected(self, client_info):
        """Handle client connection to our server."""
        self.logger.info(f"Client connected: {client_info}")
        
    def _on_client_disconnected(self, client_info):
        """Handle client disconnection from our server."""
        self.logger.info(f"Client disconnected: {client_info}")
        
    def _on_server_data_received(self, message):
        """Handle data received by our server."""
        self.logger.debug(f"Server received: {message}")
        # Handle cursor transitions, input events, etc.
        
    def _on_connected_to_server(self, server_info):
        """Handle successful connection to server."""
        self.logger.info(f"Connected to server: {server_info}")
        
    def _on_disconnected_from_server(self, reason):
        """Handle disconnection from server."""
        self.logger.warning(f"Disconnected from server: {reason}")
        self.connection_status_changed.emit(False, f"Disconnected: {reason}")
        
    def _on_client_data_received(self, message):
        """Handle data received from server."""
        self.logger.debug(f"Client received: {message}")
        # Handle cursor transitions, input events, etc.
    
    def get_server_info(self):
        """Get server information."""
        if self.server:
            return self.server.get_info()
        return None
    
    def get_client_info(self):
        """Get client information."""
        if self.client:
            return self.client.get_info()
        return None
    
    def shutdown(self):
        """Shutdown the application."""
        if self.server:
            self.stop_server()
        if self.client:
            self.disconnect_from_server()
        self.logger.info("AppManager shutdown complete") 