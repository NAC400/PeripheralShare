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
        self.is_active_device = True  # Only the active device captures/sends input
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
            
            # Start input capture for sharing peripherals (only if active)
            if self.is_active_device:
                if self.input_manager.start_capture():
                    self.logger.info("Input capture started")
                    self.input_manager.input_captured.connect(self._send_input_to_clients)
                else:
                    self.logger.warning("Failed to start input capture")
            
            # Start edge tracking for seamless desktop
            self.desktop_manager.edge_reached.connect(self._on_edge_reached)
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
                self.is_active_device = False  # Client starts as inactive
                self.connection_status_changed.emit(True, f"Connected to {host}:{port}")
                self.logger.info(f"Successfully connected to {host}:{port}")
                # Start edge tracking for seamless desktop
                self.desktop_manager.edge_reached.connect(self._on_edge_reached)
                self.desktop_manager.start_edge_tracking()
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
        self.input_manager.stop_capture()
        if self.client:
            self.client.disconnect()
            self.client = None
        
        self.connection_status_changed.emit(False, "Disconnected from server")
        self.logger.info("Disconnected from server")
    
    def _on_client_connected(self, client_info):
        self.logger.info(f"Client connected: {client_info}")
    
    def _on_client_disconnected(self, client_info):
        self.logger.info(f"Client disconnected: {client_info}")
    
    def _on_server_data_received(self, message):
        self.logger.debug(f"Server received: {message}")
        try:
            msg_type = message.get('type')
            if msg_type == 'handoff':
                # Become inactive, stop capturing input, but DO NOT disconnect
                self.is_active_device = False
                self.input_manager.stop_capture()
                self.logger.info("Received handoff: now inactive, connection still open.")
            elif msg_type == 'input' and self.is_active_device:
                event_type = message.get('event_type')
                data = message.get('data', {})
                self.input_manager.inject_input(event_type, data)
            elif msg_type == 'ping':
                response = {'type': 'pong', 'timestamp': message.get('timestamp')}
                self.server.broadcast_message(response)
        except Exception as e:
            self.logger.error(f"Error processing server message: {e}")
    
    def _on_connected_to_server(self, server_info):
        self.logger.info(f"Connected to server: {server_info}")
    
    def _on_disconnected_from_server(self, reason):
        self.logger.warning(f"Disconnected from server: {reason}")
        self.connection_status_changed.emit(False, f"Disconnected: {reason}")
    
    def _on_client_data_received(self, message):
        self.logger.debug(f"Client received: {message}")
        try:
            msg_type = message.get('type')
            if msg_type == 'handoff':
                # Become active, start capturing input
                self.is_active_device = True
                if self.input_manager.start_capture():
                    self.input_manager.input_captured.connect(self.send_input_to_server)
                self.logger.info("Received handoff: now active, capturing input.")
            elif msg_type == 'input' and self.is_active_device:
                event_type = message.get('event_type')
                data = message.get('data', {})
                self.input_manager.inject_input(event_type, data)
            elif msg_type == 'pong':
                self.logger.debug("Received pong from server")
        except Exception as e:
            self.logger.error(f"Error processing client message: {e}")
    
    def _on_edge_reached(self, edge):
        """Handle edge reached event for handoff."""
        if self.is_active_device:
            self.logger.info(f"Edge reached: {edge}. Sending handoff.")
            # Send handoff to the other device
            if self.is_server_mode and self.server:
                self.server.broadcast_message({'type': 'handoff', 'edge': edge})
                self.is_active_device = False
                self.input_manager.stop_capture()
                self.logger.info(f"Sent handoff to client (edge: {edge}). Now inactive, but connection remains open.")
            elif not self.is_server_mode and self.client:
                self.client.send_message({'type': 'handoff', 'edge': edge})
                self.is_active_device = False
                self.input_manager.stop_capture()
                self.logger.info(f"Sent handoff to server (edge: {edge}). Now inactive, but connection remains open.")
    
    def _send_input_to_clients(self, event_type, data):
        if self.server and self.is_server_mode and self.is_active_device:
            message = {
                'type': 'input',
                'event_type': event_type,
                'data': data
            }
            self.server.broadcast_message(message)
            self.logger.debug(f"Sent input to clients: {event_type}")
    
    def send_input_to_server(self, event_type, data):
        if self.client and self.is_active_device:
            message = {
                'type': 'input',
                'event_type': event_type,
                'data': data
            }
            self.client.send_message(message)
            self.logger.debug(f"Sent input to server: {event_type}")
    
    def shutdown(self):
        if self.server:
            self.stop_server()
        if self.client:
            self.disconnect_from_server()
        self.logger.info("AppManager shutdown complete")
    
    def get_connected_devices(self):
        if self.server:
            return self.server.get_devices()
        return {} 