import logging
from PyQt6.QtCore import QObject, pyqtSignal
from pynput import mouse

class SeamlessDesktopManager(QObject):
    edge_reached = pyqtSignal(str)  # 'left', 'right', 'top', 'bottom'

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.mouse_listener = None
        self.logger.info("Seamless Desktop Manager initialized")
        self.screen_width = 1920  # TODO: get dynamically
        self.screen_height = 1080
        self.edge_threshold = config.get('input.edge_threshold', 5)
    
    def start_edge_tracking(self):
        self.logger.info("Edge tracking started - move mouse to edges!")
        self.mouse_listener = mouse.Listener(on_move=self._on_mouse_move)
        self.mouse_listener.start()
    
    def _on_mouse_move(self, x, y):
        # Emit signal if mouse is at edge
        if x <= self.edge_threshold:
            self.logger.info("Mouse at left edge")
            self.edge_reached.emit('left')
        elif x >= self.screen_width - self.edge_threshold:
            self.logger.info("Mouse at right edge")
            self.edge_reached.emit('right')
        elif y <= self.edge_threshold:
            self.logger.info("Mouse at top edge")
            self.edge_reached.emit('top')
        elif y >= self.screen_height - self.edge_threshold:
            self.logger.info("Mouse at bottom edge")
            self.edge_reached.emit('bottom') 