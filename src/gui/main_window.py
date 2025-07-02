from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QTabWidget, QGroupBox, QListWidget, 
                             QTextEdit, QLineEdit, QSpinBox, QCheckBox, 
                             QFormLayout, QGridLayout, QStatusBar, QSplitter,
                             QComboBox, QProgressBar)
from PyQt6.QtCore import pyqtSlot, QTimer, Qt
from PyQt6.QtGui import QFont, QPalette

class MainWindow(QWidget):
    def __init__(self, app_manager, config):
        super().__init__()
        self.app_manager = app_manager
        self.config = config
        self.is_server_running = False
        self.init_ui()
        self.setup_connections()
        
    def init_ui(self):
        self.setWindowTitle("PeripheralShare - Cross-Platform Peripheral Sharing")
        self.setGeometry(100, 100, 900, 700)
        
        # Main layout
        main_layout = QVBoxLayout()
        
        # Header
        header = self.create_header()
        main_layout.addWidget(header)
        
        # Tab widget for different sections
        tab_widget = QTabWidget()
        
        # Main Control Tab
        control_tab = self.create_control_tab()
        tab_widget.addTab(control_tab, "Control")
        
        # Device Management Tab
        devices_tab = self.create_devices_tab()
        tab_widget.addTab(devices_tab, "Devices")
        
        # Settings Tab
        settings_tab = self.create_settings_tab()
        tab_widget.addTab(settings_tab, "Settings")
        
        # Logs Tab
        logs_tab = self.create_logs_tab()
        tab_widget.addTab(logs_tab, "Logs")
        
        main_layout.addWidget(tab_widget)
        
        # Status bar
        self.status_bar = self.create_status_bar()
        main_layout.addWidget(self.status_bar)
        
        self.setLayout(main_layout)
        
    def create_header(self):
        header_widget = QWidget()
        header_layout = QHBoxLayout()
        
        # Title
        title = QLabel("PeripheralShare")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        
        # Connection status indicator
        self.connection_status = QLabel("Disconnected")
        self.connection_status.setStyleSheet("color: red; font-weight: bold;")
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(QLabel("Status:"))
        header_layout.addWidget(self.connection_status)
        
        header_widget.setLayout(header_layout)
        return header_widget
        
    def create_control_tab(self):
        control_widget = QWidget()
        layout = QVBoxLayout()
        
        # Mode Selection
        mode_group = QGroupBox("Operation Mode")
        mode_layout = QVBoxLayout()
        
        # Server Mode Section
        server_section = QGroupBox("Server Mode (This Device)")
        server_layout = QVBoxLayout()
        
        server_info = QLabel("Share this device's peripherals with other devices")
        server_info.setWordWrap(True)
        server_layout.addWidget(server_info)
        
        self.start_server_btn = QPushButton("Start Seamless Desktop Server")
        self.start_server_btn.clicked.connect(self.toggle_server)
        self.start_server_btn.setMinimumHeight(40)
        server_layout.addWidget(self.start_server_btn)
        
        self.server_ip_label = QLabel("Server will be available at: Not Started")
        server_layout.addWidget(self.server_ip_label)
        
        server_section.setLayout(server_layout)
        mode_layout.addWidget(server_section)
        
        # Client Mode Section
        client_section = QGroupBox("Client Mode (Connect to Server)")
        client_layout = QVBoxLayout()
        
        client_info = QLabel("Connect to another device to use their peripherals")
        client_info.setWordWrap(True)
        client_layout.addWidget(client_info)
        
        connection_layout = QHBoxLayout()
        connection_layout.addWidget(QLabel("Server IP:"))
        self.server_ip_input = QLineEdit()
        self.server_ip_input.setPlaceholderText("192.168.1.100")
        connection_layout.addWidget(self.server_ip_input)
        
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.clicked.connect(self.connect_to_server)
        connection_layout.addWidget(self.connect_btn)
        
        client_layout.addLayout(connection_layout)
        client_section.setLayout(client_layout)
        mode_layout.addWidget(client_section)
        
        mode_group.setLayout(mode_layout)
        layout.addWidget(mode_group)
        
        # Edge Detection Settings
        edge_group = QGroupBox("Seamless Desktop Settings")
        edge_layout = QFormLayout()
        
        self.edge_sensitivity = QSpinBox()
        self.edge_sensitivity.setRange(1, 20)
        self.edge_sensitivity.setValue(5)
        self.edge_sensitivity.setSuffix(" pixels")
        edge_layout.addRow("Edge Sensitivity:", self.edge_sensitivity)
        
        self.device_layout_combo = QComboBox()
        self.device_layout_combo.addItems([
            "Laptop ← Main → Secondary", 
            "Secondary ← Main → Laptop",
            "Main ← Laptop → Secondary"
        ])
        edge_layout.addRow("Device Layout:", self.device_layout_combo)
        
        edge_group.setLayout(edge_layout)
        layout.addWidget(edge_group)
        
        layout.addStretch()
        control_widget.setLayout(layout)
        return control_widget
        
    def create_devices_tab(self):
        devices_widget = QWidget()
        layout = QHBoxLayout()
        
        # Available Devices
        available_group = QGroupBox("Available Devices")
        available_layout = QVBoxLayout()
        
        self.available_devices = QListWidget()
        self.available_devices.addItem("Scanning for devices...")
        available_layout.addWidget(self.available_devices)
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_devices)
        available_layout.addWidget(refresh_btn)
        
        available_group.setLayout(available_layout)
        layout.addWidget(available_group)
        
        # Connected Devices
        connected_group = QGroupBox("Connected Devices")
        connected_layout = QVBoxLayout()
        
        self.connected_devices = QListWidget()
        self.connected_devices.addItem("No devices connected")
        connected_layout.addWidget(self.connected_devices)
        
        disconnect_btn = QPushButton("Disconnect Selected")
        disconnect_btn.clicked.connect(self.disconnect_device)
        connected_layout.addWidget(disconnect_btn)
        
        connected_group.setLayout(connected_layout)
        layout.addWidget(connected_group)
        
        devices_widget.setLayout(layout)
        return devices_widget
        
    def create_settings_tab(self):
        settings_widget = QWidget()
        layout = QVBoxLayout()
        
        # Network Settings
        network_group = QGroupBox("Network Settings")
        network_layout = QFormLayout()
        
        self.port_spinbox = QSpinBox()
        self.port_spinbox.setRange(1024, 65535)
        self.port_spinbox.setValue(self.config.get('network.port', 12345))
        network_layout.addRow("Port:", self.port_spinbox)
        
        self.encryption_checkbox = QCheckBox("Enable Encryption")
        self.encryption_checkbox.setChecked(True)
        network_layout.addRow("Security:", self.encryption_checkbox)
        
        network_group.setLayout(network_layout)
        layout.addWidget(network_group)
        
        # Input Settings
        input_group = QGroupBox("Input Settings")
        input_layout = QFormLayout()
        
        self.mouse_acceleration = QCheckBox("Mouse Acceleration")
        self.mouse_acceleration.setChecked(True)
        input_layout.addRow("Mouse:", self.mouse_acceleration)
        
        self.keyboard_passthrough = QCheckBox("Keyboard Passthrough")
        self.keyboard_passthrough.setChecked(True)
        input_layout.addRow("Keyboard:", self.keyboard_passthrough)
        
        input_group.setLayout(input_layout)
        layout.addWidget(input_group)
        
        # Audio Settings
        audio_group = QGroupBox("Audio Settings")
        audio_layout = QFormLayout()
        
        self.audio_quality = QComboBox()
        self.audio_quality.addItems(["Low (64kbps)", "Medium (128kbps)", "High (256kbps)"])
        self.audio_quality.setCurrentIndex(1)
        audio_layout.addRow("Quality:", self.audio_quality)
        
        self.audio_enabled = QCheckBox("Enable Audio Sharing")
        self.audio_enabled.setChecked(False)
        audio_layout.addRow("Audio:", self.audio_enabled)
        
        audio_group.setLayout(audio_layout)
        layout.addWidget(audio_group)
        
        # Save Settings Button
        save_btn = QPushButton("Save Settings")
        save_btn.clicked.connect(self.save_settings)
        layout.addWidget(save_btn)
        
        layout.addStretch()
        settings_widget.setLayout(layout)
        return settings_widget
        
    def create_logs_tab(self):
        logs_widget = QWidget()
        layout = QVBoxLayout()
        
        # Log controls
        controls_layout = QHBoxLayout()
        
        clear_btn = QPushButton("Clear Logs")
        clear_btn.clicked.connect(self.clear_logs)
        controls_layout.addWidget(clear_btn)
        
        controls_layout.addStretch()
        
        log_level_combo = QComboBox()
        log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        log_level_combo.setCurrentText("INFO")
        controls_layout.addWidget(QLabel("Log Level:"))
        controls_layout.addWidget(log_level_combo)
        
        layout.addLayout(controls_layout)
        
        # Log display
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        layout.addWidget(self.log_display)
        
        logs_widget.setLayout(layout)
        return logs_widget
        
    def create_status_bar(self):
        status_widget = QWidget()
        status_layout = QHBoxLayout()
        status_layout.setContentsMargins(5, 2, 5, 2)
        
        self.status_label = QLabel("Ready")
        status_layout.addWidget(self.status_label)
        
        status_layout.addStretch()
        
        # Network indicator
        self.network_indicator = QLabel("●")
        self.network_indicator.setStyleSheet("color: red; font-size: 16px;")
        self.network_indicator.setToolTip("Network Status")
        status_layout.addWidget(QLabel("Network:"))
        status_layout.addWidget(self.network_indicator)
        
        status_widget.setLayout(status_layout)
        return status_widget
        
    def setup_connections(self):
        # Connect app manager signals
        if hasattr(self.app_manager, 'connection_status_changed'):
            self.app_manager.connection_status_changed.connect(self.update_connection_status)
            
    @pyqtSlot()
    def toggle_server(self):
        if not self.is_server_running:
            self.start_server()
        else:
            self.stop_server()
            
    def start_server(self):
        print("Starting seamless desktop server...")
        self.log_message("Starting server...")
        
        success = self.app_manager.start_as_server()
        if success:
            self.is_server_running = True
            self.start_server_btn.setText("Stop Server")
            self.start_server_btn.setStyleSheet("background-color: #ff6b6b;")
            self.connection_status.setText("Server Running")
            self.connection_status.setStyleSheet("color: green; font-weight: bold;")
            self.network_indicator.setStyleSheet("color: green; font-size: 16px;")
            self.server_ip_label.setText(f"Server running on port {self.port_spinbox.value()}")
            self.status_label.setText("Server active - Move mouse to edges to switch devices")
            self.log_message("Server started successfully!")
        else:
            self.log_message("Failed to start server")
            
    def stop_server(self):
        self.log_message("Stopping server...")
        # Add server stop logic here
        self.is_server_running = False
        self.start_server_btn.setText("Start Seamless Desktop Server")
        self.start_server_btn.setStyleSheet("")
        self.connection_status.setText("Disconnected")
        self.connection_status.setStyleSheet("color: red; font-weight: bold;")
        self.network_indicator.setStyleSheet("color: red; font-size: 16px;")
        self.server_ip_label.setText("Server will be available at: Not Started")
        self.status_label.setText("Ready")
        self.log_message("Server stopped")
        
    @pyqtSlot()
    def connect_to_server(self):
        server_ip = self.server_ip_input.text().strip()
        if not server_ip:
            self.log_message("Please enter server IP address")
            return
            
        self.log_message(f"Connecting to server at {server_ip}...")
        # Add client connection logic here
        
    @pyqtSlot()
    def refresh_devices(self):
        self.log_message("Refreshing device list...")
        self.available_devices.clear()
        self.available_devices.addItem("Scanning for devices...")
        # Add device discovery logic here
        
    @pyqtSlot()
    def disconnect_device(self):
        current_item = self.connected_devices.currentItem()
        if current_item:
            device_name = current_item.text()
            self.log_message(f"Disconnecting from {device_name}")
            # Add disconnect logic here
            
    @pyqtSlot()
    def save_settings(self):
        self.log_message("Settings saved")
        # Add settings save logic here
        
    @pyqtSlot()
    def clear_logs(self):
        self.log_display.clear()
        
    def log_message(self, message):
        """Add a message to the log display"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_display.append(f"[{timestamp}] {message}")
        
    @pyqtSlot(bool, str)
    def update_connection_status(self, connected, message):
        """Update connection status from app manager"""
        if connected:
            self.connection_status.setText("Connected")
            self.connection_status.setStyleSheet("color: green; font-weight: bold;")
            self.network_indicator.setStyleSheet("color: green; font-size: 16px;")
        else:
            self.connection_status.setText("Disconnected")
            self.connection_status.setStyleSheet("color: red; font-weight: bold;")
            self.network_indicator.setStyleSheet("color: red; font-size: 16px;")
            
        self.status_label.setText(message)
        self.log_message(message) 