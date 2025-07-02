"""
Network discovery service for PeripheralShare.
Handles automatic device discovery and service announcement on the local network.
"""

import socket
import threading
import time
import json
import logging
from typing import Dict, List, Optional, Callable
from PyQt6.QtCore import QObject, pyqtSignal
from zeroconf import ServiceInfo, Zeroconf, ServiceBrowser, ServiceListener
import platform

class PeripheralShareServiceListener(ServiceListener):
    """Service listener for PeripheralShare devices."""
    
    def __init__(self, discovery_manager):
        self.discovery_manager = discovery_manager
        self.logger = logging.getLogger(__name__)
    
    def add_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        """Called when a new service is discovered."""
        info = zc.get_service_info(type_, name)
        if info:
            self.discovery_manager._on_service_discovered(info)
    
    def remove_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        """Called when a service is removed."""
        self.discovery_manager._on_service_removed(name)
    
    def update_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        """Called when a service is updated."""
        info = zc.get_service_info(type_, name)
        if info:
            self.discovery_manager._on_service_updated(info)

class NetworkDiscovery(QObject):
    """Network discovery manager for finding PeripheralShare devices."""
    
    # Signals
    device_found = pyqtSignal(str, str, int)      # device_name, ip, port
    device_lost = pyqtSignal(str)                 # device_name
    device_updated = pyqtSignal(str, str, int)    # device_name, ip, port
    
    SERVICE_TYPE = "_peripheralshare._tcp.local."
    
    def __init__(self, config):
        """Initialize network discovery."""
        super().__init__()
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Zeroconf components
        self.zeroconf = None
        self.service_browser = None
        self.service_listener = None
        self.service_info = None
        
        # Discovery state
        self.discovered_devices = {}
        self.is_advertising = False
        self.is_browsing = False
        
        # Device information
        self.device_name = self._get_device_name()
        
        # Threading
        self._discovery_thread = None
        self._stop_event = threading.Event()
    
    def _get_device_name(self) -> str:
        """Get a friendly device name."""
        configured_name = self.config.get('security.device_name')
        if configured_name:
            return configured_name
        
        # Generate default name
        hostname = platform.node() or "Unknown"
        system = platform.system()
        return f"{hostname} ({system})"
    
    def start_discovery(self) -> bool:
        """Start discovering PeripheralShare devices on the network."""
        try:
            if self.is_browsing:
                self.logger.warning("Discovery already running")
                return True
            
            self.zeroconf = Zeroconf()
            self.service_listener = PeripheralShareServiceListener(self)
            self.service_browser = ServiceBrowser(
                self.zeroconf, 
                self.SERVICE_TYPE, 
                self.service_listener
            )
            
            self.is_browsing = True
            self.logger.info("Network discovery started")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start discovery: {e}")
            return False
    
    def stop_discovery(self):
        """Stop device discovery."""
        try:
            self.is_browsing = False
            
            if self.service_browser:
                self.service_browser.cancel()
                self.service_browser = None
            
            if self.zeroconf:
                self.zeroconf.close()
                self.zeroconf = None
            
            self.service_listener = None
            self.discovered_devices.clear()
            
            self.logger.info("Network discovery stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping discovery: {e}")
    
    def start_advertising(self, port: int) -> bool:
        """Start advertising this device as a PeripheralShare server."""
        try:
            if self.is_advertising:
                self.logger.warning("Already advertising")
                return True
            
            if not self.zeroconf:
                self.zeroconf = Zeroconf()
            
            # Get local IP address
            local_ip = self._get_local_ip()
            if not local_ip:
                self.logger.error("Could not determine local IP address")
                return False
            
            # Create service info
            properties = {
                'device_name': self.device_name,
                'version': self.config.get('application.version', '1.0.0'),
                'features': json.dumps([
                    'mouse', 'keyboard', 'audio', 'file_transfer'
                ]),
                'platform': platform.system()
            }
            
            # Convert properties to bytes
            properties_bytes = {k: v.encode('utf-8') for k, v in properties.items()}
            
            service_name = f"{self.device_name}.{self.SERVICE_TYPE}"
            self.service_info = ServiceInfo(
                self.SERVICE_TYPE,
                service_name,
                addresses=[socket.inet_aton(local_ip)],
                port=port,
                properties=properties_bytes,
                server=f"{self.device_name}.local."
            )
            
            self.zeroconf.register_service(self.service_info)
            self.is_advertising = True
            
            self.logger.info(f"Started advertising as '{self.device_name}' on {local_ip}:{port}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start advertising: {e}")
            return False
    
    def stop_advertising(self):
        """Stop advertising this device."""
        try:
            if not self.is_advertising:
                return
            
            self.is_advertising = False
            
            if self.service_info and self.zeroconf:
                self.zeroconf.unregister_service(self.service_info)
                self.service_info = None
            
            self.logger.info("Stopped advertising")
            
        except Exception as e:
            self.logger.error(f"Error stopping advertising: {e}")
    
    def start(self):
        """Start both discovery and advertising."""
        self.start_discovery()
    
    def stop(self):
        """Stop both discovery and advertising."""
        self.stop_advertising()
        self.stop_discovery()
    
    def cleanup(self):
        """Cleanup resources."""
        self.stop()
    
    def _get_local_ip(self) -> Optional[str]:
        """Get the local IP address."""
        try:
            # Connect to a remote address to determine local IP
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                return s.getsockname()[0]
        except Exception:
            try:
                # Fallback: get hostname IP
                return socket.gethostbyname(socket.gethostname())
            except Exception:
                return None
    
    def _on_service_discovered(self, info: ServiceInfo):
        """Handle discovered service."""
        try:
            if not info.addresses:
                return
            
            # Extract device information
            device_name = self._get_property_string(info, 'device_name') or info.name
            ip_address = socket.inet_ntoa(info.addresses[0])
            port = info.port
            
            # Don't discover ourselves
            if device_name == self.device_name:
                return
            
            # Store device info
            device_id = f"{ip_address}:{port}"
            self.discovered_devices[device_id] = {
                'name': device_name,
                'ip': ip_address,
                'port': port,
                'version': self._get_property_string(info, 'version'),
                'platform': self._get_property_string(info, 'platform'),
                'features': self._get_property_list(info, 'features'),
                'last_seen': time.time()
            }
            
            self.device_found.emit(device_name, ip_address, port)
            self.logger.info(f"Discovered device: {device_name} at {ip_address}:{port}")
            
        except Exception as e:
            self.logger.error(f"Error processing discovered service: {e}")
    
    def _on_service_removed(self, name: str):
        """Handle removed service."""
        try:
            # Find and remove device by name
            device_to_remove = None
            for device_id, device_info in self.discovered_devices.items():
                if device_info['name'] in name:
                    device_to_remove = device_id
                    break
            
            if device_to_remove:
                device_info = self.discovered_devices.pop(device_to_remove)
                self.device_lost.emit(device_info['name'])
                self.logger.info(f"Device lost: {device_info['name']}")
            
        except Exception as e:
            self.logger.error(f"Error processing removed service: {e}")
    
    def _on_service_updated(self, info: ServiceInfo):
        """Handle updated service."""
        # For now, treat updates as new discoveries
        self._on_service_discovered(info)
    
    def _get_property_string(self, info: ServiceInfo, key: str) -> Optional[str]:
        """Get string property from service info."""
        try:
            if info.properties and key.encode('utf-8') in info.properties:
                return info.properties[key.encode('utf-8')].decode('utf-8')
        except Exception:
            pass
        return None
    
    def _get_property_list(self, info: ServiceInfo, key: str) -> List[str]:
        """Get list property from service info."""
        try:
            prop_str = self._get_property_string(info, key)
            if prop_str:
                return json.loads(prop_str)
        except Exception:
            pass
        return []
    
    def get_discovered_devices(self) -> Dict[str, Dict]:
        """Get all discovered devices."""
        return self.discovered_devices.copy()
    
    def refresh_discovery(self):
        """Refresh device discovery."""
        if self.is_browsing:
            self.stop_discovery()
            time.sleep(0.5)
            self.start_discovery() 