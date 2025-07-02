import logging
from typing import Dict, Optional, Tuple
from PyQt6.QtCore import QObject, pyqtSignal
from pynput import mouse

class DeviceLayout:
    def __init__(self):
        self.devices = {}
        self.layout = {}
        self.logger = logging.getLogger(__name__)
    
    def add_device(self, device_id: str, position: str, screen_width: int, screen_height: int, ip: str = "local"):
        self.devices[device_id] = {
            "position": position,
            "width": screen_width,
            "height": screen_height,
            "ip": ip,
            "active": False
        }
        self.layout[position] = device_id
        self.logger.info(f"Added device {device_id} at {position}")
    
    def get_adjacent_device(self, current_device: str, direction: str) -> Optional[str]:
        if current_device not in self.devices:
            return None
        current_pos = self.devices[current_device]["position"]
        adjacency = {
            "left": {"middle": "left", "right": "middle"},
            "right": {"left": "middle", "middle": "right"},
            "middle": {"left": "left", "right": "right"}
        }
        if current_pos in adjacency and direction in adjacency[current_pos]:
            target_pos = adjacency[current_pos][direction]
            return self.layout.get(target_pos)
        return None

class EdgeDetector:
    def __init__(self, screen_width: int, screen_height: int, edge_threshold: int = 5):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.edge_threshold = edge_threshold
    
    def check_edge(self, x: int, y: int) -> Optional[str]:
        if x <= self.edge_threshold:
            return "left"
        elif x >= self.screen_width - self.edge_threshold:
            return "right"
        return None

class SeamlessDesktopManager(QObject):
    cursor_transition_requested = pyqtSignal(str, str, int, int)
    focus_changed = pyqtSignal(str)
    edge_hit = pyqtSignal(str, int, int)
    
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.logger = logging.getLogger(__name__)
        import tkinter as tk
        root = tk.Tk()
        self.screen_width = root.winfo_screenwidth()
        self.screen_height = root.winfo_screenheight()
        root.destroy()
        self.layout = DeviceLayout()
        self.edge_detector = EdgeDetector(self.screen_width, self.screen_height)
        self.current_device = "main"
        self.transition_in_progress = False
        self.mouse_listener = None
        self._setup_default_layout()
        self.logger.info(f"Seamless Desktop Manager initialized ({self.screen_width}x{self.screen_height})")
    
    def _setup_default_layout(self):
        self.layout.add_device("main", "middle", self.screen_width, self.screen_height)
        self.layout.add_device("laptop", "left", 1920, 1080, "unknown")
        self.layout.add_device("secondary", "right", 1920, 1080, "local")
    
    def start_edge_tracking(self):
        if self.mouse_listener:
            return
        self.mouse_listener = mouse.Listener(on_move=self._on_mouse_move, suppress=False)
        self.mouse_listener.start()
        self.logger.info("Edge tracking started")
    
    def _on_mouse_move(self, x, y):
        if self.transition_in_progress:
            return
        edge = self.edge_detector.check_edge(x, y)
        if edge:
            self._handle_edge_hit(edge, x, y)
    
    def _handle_edge_hit(self, direction: str, x: int, y: int):
        if direction not in ["left", "right"]:
            return
        target_device = self.layout.get_adjacent_device(self.current_device, direction)
        if not target_device:
            return
        device_info = self.layout.devices.get(target_device)
        if not device_info or not device_info.get("active", False):
            return
        self.logger.info(f"Edge hit: {direction} -> {target_device}")
        target_x, target_y = self._calculate_target_position(direction, x, y, device_info)
        self._initiate_cursor_transition(target_device, direction, target_x, target_y)
    
    def _calculate_target_position(self, direction: str, source_x: int, source_y: int, target_device_info: Dict) -> Tuple[int, int]:
        target_width = target_device_info["width"]
        target_height = target_device_info["height"]
        if direction == "left":
            target_x = target_width - 10
            target_y = int((source_y / self.screen_height) * target_height)
        elif direction == "right":
            target_x = 10
            target_y = int((source_y / self.screen_height) * target_height)
        else:
            target_x = target_width // 2
            target_y = target_height // 2
        target_x = max(0, min(target_x, target_width - 1))
        target_y = max(0, min(target_y, target_height - 1))
        return target_x, target_y
    
    def _initiate_cursor_transition(self, target_device: str, direction: str, target_x: int, target_y: int):
        self.transition_in_progress = True
        self.cursor_transition_requested.emit(target_device, direction, target_x, target_y)
        self.focus_changed.emit(target_device)
    
    def add_connected_device(self, device_id: str, position: str, width: int, height: int, ip: str):
        self.layout.add_device(device_id, position, width, height, ip)
        self.layout.devices[device_id]["active"] = True
        
    def get_screen_info(self) -> Dict:
        return {
            "width": self.screen_width,
            "height": self.screen_height,
            "device_id": "main",
            "position": "middle"
        }

