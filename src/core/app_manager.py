import logging
from PyQt6.QtCore import QObject, pyqtSignal
from src.network.server import PeripheralServer
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
        self.logger.info("AppManager initialized")
    
    def start_as_server(self):
        self.logger.info("Starting seamless desktop server...")
        self.desktop_manager.start_edge_tracking()
        self.connection_status_changed.emit(True, "Seamless Desktop Server Active")
        print("Move mouse to edges to switch devices!")
        return True 