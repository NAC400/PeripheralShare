"""
Main GUI window for PeripheralShare application.
Provides the primary user interface for device connection and management.
"""

import logging
from typing import Dict, Optional
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QLineEdit, QListWidget, QListWidgetItem, QTabWidget,
    QGroupBox, QCheckBox, QSpinBox, QTextEdit, QStatusBar,
    QMessageBox, QSystemTrayIcon, QMenu, QApplication
)
from PyQt6.QtCore import Qt, QTimer, pyqtSlot
from PyQt6.QtGui import QIcon, QPixmap, QPainter

class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self, app_manager, config):
        """Initialize the main window."""
        super().__init__()
        self.app_manager = app_manager
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Window state
        self.is_server_mode = False
        self.connection_status = False
        
        # Setup UI
        self._setup_ui()
        self._setup_system_tray()
        self._connect_signals()
        
        # Restore window settings
        self._restore_window_settings()
        
        self.logger.info("Main window initialized")
    
    def _setup_ui(self):
        """Setup the user interface."""
        self.setWindowTitle("PeripheralShare")
        self.setMinimumSize(800, 600)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        layout = QVBoxLayout(central_widget)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Create tabs
        self._create_connection_tab()
        self._create_devices_tab()
        self._create_settings_tab()
        self._create_logs_tab()
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self._update_status("Ready")
    
    def _create_connection_tab(self):
        """Create the connection management tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Connection mode selection
        mode_group = QGroupBox("Connection Mode")
        mode_layout = QVBoxLayout(mode_group)
        
        self.server_button = QPushButton("Start as Server (Primary Device)")
        self.server_button.clicked.connect(self._start_server)
        mode_layout.addWidget(self.server_button)
        
        client_layout = QHBoxLayout()
        self.client_button = QPushButton("Connect as Client")
        self.host_input = QLineEdit()
        self.host_input.setPlaceholderText("Server IP Address")
        self.port_input = QSpinBox()
        self.port_input.setRange(1024, 65535)
        self.port_input.setValue(self.config.get('network.port', 8888))
        
        client_layout.addWidget(QLabel("Host:"))
        client_layout.addWidget(self.host_input)
        client_layout.addWidget(QLabel("Port:"))
        client_layout.addWidget(self.port_input)
        client_layout.addWidget(self.client_button)
        
        self.client_button.clicked.connect(self._connect_client)
        
        mode_layout.addLayout(client_layout)
        layout.addWidget(mode_group)
        
        # Connection status
        status_group = QGroupBox("Connection Status")
        status_layout = QVBoxLayout(status_group)
        
        self.status_label = QLabel("Disconnected")
        self.status_label.setStyleSheet("color: red; font-weight: bold;")
        status_layout.addWidget(self.status_label)
        
        self.connected_device_label = QLabel("")
        status_layout.addWidget(self.connected_device_label)
        
        self.disconnect_button = QPushButton("Disconnect")
        self.disconnect_button.setEnabled(False)
        self.disconnect_button.clicked.connect(self._disconnect)
        status_layout.addWidget(self.disconnect_button)
        
        layout.addWidget(status_group)
        
        # Input controls
        input_group = QGroupBox("Input Control")
        input_layout = QVBoxLayout(input_group)
        
        self.mouse_enabled_cb = QCheckBox("Enable Mouse Sharing")
        self.mouse_enabled_cb.setChecked(self.config.get('input.mouse_enabled', True))
        input_layout.addWidget(self.mouse_enabled_cb)
        
        self.keyboard_enabled_cb = QCheckBox("Enable Keyboard Sharing")
        self.keyboard_enabled_cb.setChecked(self.config.get('input.keyboard_enabled', True))
        input_layout.addWidget(self.keyboard_enabled_cb)
        
        layout.addWidget(input_group)
        
        # Add stretch
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "Connection")
    
    def _create_devices_tab(self):
        """Create the device discovery tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Discovery controls
        discovery_layout = QHBoxLayout()
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self._refresh_devices)
        discovery_layout.addWidget(self.refresh_button)
        discovery_layout.addStretch()
        
        layout.addLayout(discovery_layout)
        
        # Discovered devices list
        devices_group = QGroupBox("Discovered Devices")
        devices_layout = QVBoxLayout(devices_group)
        
        self.devices_list = QListWidget()
        self.devices_list.itemDoubleClicked.connect(self._connect_to_device)
        devices_layout.addWidget(self.devices_list)
        
        layout.addWidget(devices_group)
        
        self.tab_widget.addTab(tab, "Devices")
    
    def _create_settings_tab(self):
        """Create the settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Network settings
        network_group = QGroupBox("Network Settings")
        network_layout = QVBoxLayout(network_group)
        
        port_layout = QHBoxLayout()
        port_layout.addWidget(QLabel("Default Port:"))
        self.default_port_spin = QSpinBox()
        self.default_port_spin.setRange(1024, 65535)
        self.default_port_spin.setValue(self.config.get('network.port', 8888))
        port_layout.addWidget(self.default_port_spin)
        port_layout.addStretch()
        network_layout.addLayout(port_layout)
        
        layout.addWidget(network_group)
        
        # Audio settings
        audio_group = QGroupBox("Audio Settings")
        audio_layout = QVBoxLayout(audio_group)
        
        self.audio_enabled_cb = QCheckBox("Enable Audio Sharing")
        self.audio_enabled_cb.setChecked(self.config.get('audio.enabled', True))
        audio_layout.addWidget(self.audio_enabled_cb)
        
        layout.addWidget(audio_group)
        
        # File transfer settings
        file_group = QGroupBox("File Transfer Settings")
        file_layout = QVBoxLayout(file_group)
        
        self.file_transfer_enabled_cb = QCheckBox("Enable File Transfer")
        self.file_transfer_enabled_cb.setChecked(self.config.get('file_transfer.enabled', True))
        file_layout.addWidget(self.file_transfer_enabled_cb)
        
        layout.addWidget(file_group)
        
        # Save button
        save_button = QPushButton("Save Settings")
        save_button.clicked.connect(self._save_settings)
        layout.addWidget(save_button)
        
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "Settings")
    
    def _create_logs_tab(self):
        """Create the logs tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Log controls
        log_controls = QHBoxLayout()
        clear_button = QPushButton("Clear Logs")
        clear_button.clicked.connect(self._clear_logs)
        log_controls.addWidget(clear_button)
        log_controls.addStretch()
        
        layout.addLayout(log_controls)
        
        # Log display
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setFont(self.font())
        layout.addWidget(self.log_display)
        
        self.tab_widget.addTab(tab, "Logs")
    
    def _setup_system_tray(self):
        """Setup system tray icon."""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
        
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setToolTip("PeripheralShare")
        
        # Create tray menu
        tray_menu = QMenu()
        
        show_action = tray_menu.addAction("Show")
        show_action.triggered.connect(self.show)
        
        tray_menu.addSeparator()
        
        quit_action = tray_menu.addAction("Quit")
        quit_action.triggered.connect(QApplication.quit)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self._tray_icon_activated)
        
        # Create a simple icon
        pixmap = QPixmap(16, 16)
        pixmap.fill(Qt.GlobalColor.blue)
        self.tray_icon.setIcon(QIcon(pixmap))
        
        self.tray_icon.show()
    
    def _connect_signals(self):
        """Connect application signals to UI slots."""
        if self.app_manager:
            self.app_manager.connection_status_changed.connect(
                self.update_connection_status
            )
            self.app_manager.device_discovered.connect(
                self.add_discovered_device
            )
            self.app_manager.error_occurred.connect(
                self._show_error
            )
    
    def _restore_window_settings(self):
        """Restore window position and size."""
        pos = self.config.get('display.window_position', [100, 100])
        size = self.config.get('display.window_size', [800, 600])
        
        self.move(pos[0], pos[1])
        self.resize(size[0], size[1])
    
    def _save_window_settings(self):
        """Save window position and size."""
        pos = self.pos()
        size = self.size()
        
        self.config.set('display.window_position', [pos.x(), pos.y()])
        self.config.set('display.window_size', [size.width(), size.height()])
        self.config.save()
    
    # Slot implementations
    @pyqtSlot()
    def _start_server(self):
        """Start as server."""
        port = self.port_input.value()
        if self.app_manager.start_as_server(port):
            self.is_server_mode = True
            self._update_ui_connection_state(True)
            self._update_status(f"Server started on port {port}")
        else:
            self._show_error("Server Error", "Failed to start server")
    
    @pyqtSlot()
    def _connect_client(self):
        """Connect as client."""
        host = self.host_input.text().strip()
        port = self.port_input.value()
        
        if not host:
            self._show_error("Connection Error", "Please enter a host address")
            return
        
        if self.app_manager.connect_to_server(host, port):
            self.is_server_mode = False
            self._update_status(f"Connecting to {host}:{port}...")
        else:
            self._show_error("Connection Error", f"Failed to connect to {host}:{port}")
    
    @pyqtSlot()
    def _disconnect(self):
        """Disconnect from current session."""
        self.app_manager.disconnect()
        self._update_ui_connection_state(False)
        self._update_status("Disconnected")
    
    @pyqtSlot()
    def _refresh_devices(self):
        """Refresh discovered devices."""
        self.devices_list.clear()
        if self.app_manager.network_discovery:
            self.app_manager.network_discovery.refresh_discovery()
    
    @pyqtSlot()
    def _save_settings(self):
        """Save application settings."""
        # Update config with UI values
        self.config.set('network.port', self.default_port_spin.value())
        self.config.set('input.mouse_enabled', self.mouse_enabled_cb.isChecked())
        self.config.set('input.keyboard_enabled', self.keyboard_enabled_cb.isChecked())
        self.config.set('audio.enabled', self.audio_enabled_cb.isChecked())
        self.config.set('file_transfer.enabled', self.file_transfer_enabled_cb.isChecked())
        
        self.config.save()
        self._update_status("Settings saved")
    
    @pyqtSlot()
    def _clear_logs(self):
        """Clear the log display."""
        self.log_display.clear()
    
    @pyqtSlot(QListWidgetItem)
    def _connect_to_device(self, item):
        """Connect to a discovered device."""
        device_data = item.data(Qt.ItemDataRole.UserRole)
        if device_data:
            host = device_data['ip']
            port = device_data['port']
            self.host_input.setText(host)
            self.port_input.setValue(port)
            self._connect_client()
    
    @pyqtSlot(bool, str)
    def update_connection_status(self, connected: bool, device_name: str):
        """Update connection status display."""
        if connected:
            self.status_label.setText("Connected")
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
            self.connected_device_label.setText(f"Connected to: {device_name}")
            self._update_status(f"Connected to {device_name}")
        else:
            self.status_label.setText("Disconnected")
            self.status_label.setStyleSheet("color: red; font-weight: bold;")
            self.connected_device_label.setText("")
            self._update_status("Disconnected")
        
        self.connection_status = connected
        self._update_ui_connection_state(connected)
    
    @pyqtSlot(str, str, int)
    def add_discovered_device(self, device_name: str, ip: str, port: int):
        """Add discovered device to the list."""
        item_text = f"{device_name} ({ip}:{port})"
        item = QListWidgetItem(item_text)
        item.setData(Qt.ItemDataRole.UserRole, {
            'name': device_name,
            'ip': ip,
            'port': port
        })
        self.devices_list.addItem(item)
    
    def _update_ui_connection_state(self, connected: bool):
        """Update UI elements based on connection state."""
        self.server_button.setEnabled(not connected)
        self.client_button.setEnabled(not connected)
        self.host_input.setEnabled(not connected)
        self.port_input.setEnabled(not connected)
        self.disconnect_button.setEnabled(connected)
    
    def _update_status(self, message: str):
        """Update status bar message."""
        self.status_bar.showMessage(message)
    
    def _show_error(self, title: str, message: str):
        """Show error message."""
        QMessageBox.critical(self, title, message)
        self.logger.error(f"{title}: {message}")
    
    def _tray_icon_activated(self, reason):
        """Handle tray icon activation."""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show()
            self.raise_()
            self.activateWindow()
    
    def closeEvent(self, event):
        """Handle window close event."""
        if self.config.get('display.minimize_to_tray', True) and self.tray_icon.isVisible():
            self.hide()
            event.ignore()
        else:
            self._save_window_settings()
            if self.app_manager:
                self.app_manager.shutdown()
            event.accept() 