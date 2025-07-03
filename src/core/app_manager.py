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
    
    def start_as_server(self, port=8888):
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
            
            # Start input capture for sharing peripherals
            if self.input_manager.start_capture():
                self.logger.info("Input capture started")
                # Connect input signals to send to clients
                self.input_manager.input_captured.connect(self._send_input_to_clients)
            else:
                self.logger.warning("Failed to start input capture")
            
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
        
        # Stop input capture
        self.input_manager.stop_capture()
        
        if self.desktop_manager.mouse_listener:
            self.desktop_manager.mouse_listener.stop()
            self.desktop_manager.mouse_listener = None
        
        self.is_server_mode = False
        self.connection_status_changed.emit(False, "Server stopped")
        self.logger.info("Server stopped")
    
    def connect_to_server(self, host, port=8888):
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
                # Start input capture for client mode
                self.start_client_input_capture()
                
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
        # Stop client input capture
        self.stop_client_input_capture()
        
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
        # Process input events from clients
        try:
            msg_type = message.get('type')
            if msg_type == 'input':
                event_type = message.get('event_type')
                data = message.get('data', {})
                # Inject input locally (server receives input from client)
                self.input_manager.inject_input(event_type, data)
            elif msg_type == 'ping':
                # Respond to ping to keep connection alive
                response = {'type': 'pong', 'timestamp': message.get('timestamp')}
                self.server.broadcast_message(response)
        except Exception as e:
            self.logger.error(f"Error processing server message: {e}")
        
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
        # Process input events from server
        try:
            msg_type = message.get('type')
            if msg_type == 'input':
                event_type = message.get('event_type')
                data = message.get('data', {})
                # Inject input locally (client receives input from server)
                self.input_manager.inject_input(event_type, data)
            elif msg_type == 'pong':
                # Connection is alive
                self.logger.debug("Received pong from server")
        except Exception as e:
            self.logger.error(f"Error processing client message: {e}")
    
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
    
    def _send_input_to_clients(self, event_type, data):
        """Send input event to connected clients."""
        if self.server and self.is_server_mode:
            message = {
                'type': 'input',
                'event_type': event_type,
                'data': data
            }
            self.server.broadcast_message(message)
            self.logger.debug(f"Sent input to clients: {event_type}")
    
    def send_input_to_server(self, event_type, data):
        """Send input event to server (from client)."""
        if self.client:
            message = {
                'type': 'input',
                'event_type': event_type,
                'data': data
            }
            self.client.send_message(message)
            self.logger.debug(f"Sent input to server: {event_type}")
    
    def start_client_input_capture(self):
        """Start input capture for client mode."""
        if self.input_manager.start_capture():
            self.logger.info("Client input capture started")
            # Connect input signals to send to server
            self.input_manager.input_captured.connect(self.send_input_to_server)
            return True
        else:
            self.logger.warning("Failed to start client input capture")
            return False
    
    def stop_client_input_capture(self):
        """Stop input capture for client mode."""
        self.input_manager.stop_capture()
        self.logger.info("Client input capture stopped")

    def shutdown(self):
        """Shutdown the application."""
        if self.server:
            self.stop_server()
        if self.client:
            self.disconnect_from_server()
        self.logger.info("AppManager shutdown complete") 