import logging
from PyQt6.QtCore import QObject, pyqtSignal
from pynput import mouse

try:
    from screeninfo import get_monitors
except ImportError:
    get_monitors = None


class SeamlessDesktopManager(QObject):
    edge_reached = pyqtSignal(str)  # 'left', 'right', 'top', 'bottom'

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.mouse_listener = None
        self.edge_threshold = config.get('input.edge_threshold', 5)
        self.remote_side = (config.get('layout.remote_side', 'right') or 'right').lower()

        # Determine the full virtual desktop bounds to support multi‑monitor setups
        self.screen_left = 0
        self.screen_top = 0
        self.screen_right = 1920
        self.screen_bottom = 1080

        if get_monitors:
            try:
                monitors = get_monitors()
                if monitors:
                    self.screen_left = min(m.x for m in monitors)
                    self.screen_top = min(m.y for m in monitors)
                    self.screen_right = max(m.x + m.width for m in monitors)
                    self.screen_bottom = max(m.y + m.height for m in monitors)
            except Exception as e:
                self.logger.warning(f"Could not determine screen layout from screeninfo: {e}")

        self.logger.info(
            "Seamless Desktop Manager initialized "
            f"with virtual bounds: left={self.screen_left}, top={self.screen_top}, "
            f"right={self.screen_right}, bottom={self.screen_bottom}, "
            f"edge_threshold={self.edge_threshold}"
        )

    def start_edge_tracking(self):
        self.logger.info("Edge tracking started - move mouse to edges!")
        self.mouse_listener = mouse.Listener(on_move=self._on_mouse_move)
        self.mouse_listener.start()

    def _on_mouse_move(self, x, y):
        # Emit signal only for the edge where the remote display is configured.
        if self.remote_side == 'left' and x <= self.screen_left + self.edge_threshold:
            self.logger.info("Mouse at left edge (remote_side=left)")
            self.edge_reached.emit('left')
        elif self.remote_side == 'right' and x >= self.screen_right - self.edge_threshold:
            self.logger.info("Mouse at right edge (remote_side=right)")
            self.edge_reached.emit('right')
        elif self.remote_side == 'top' and y <= self.screen_top + self.edge_threshold:
            self.logger.info("Mouse at top edge (remote_side=top)")
            self.edge_reached.emit('top')
        elif self.remote_side == 'bottom' and y >= self.screen_bottom - self.edge_threshold:
            self.logger.info("Mouse at bottom edge (remote_side=bottom)")
            self.edge_reached.emit('bottom')