"""
Input management for PeripheralShare.
Handles mouse and keyboard capture and injection across devices.
"""

import logging
import threading
import time
from typing import Dict, Any, Optional, Callable
from PyQt6.QtCore import QObject, pyqtSignal

try:
    from pynput import mouse, keyboard
    from pynput.mouse import Button, Listener as MouseListener
    from pynput.keyboard import Key, Listener as KeyboardListener
    PYNPUT_AVAILABLE = True
except ImportError:
    PYNPUT_AVAILABLE = False

class InputManager(QObject):
    """Manager for input capture and injection."""
    
    # Signals
    input_captured = pyqtSignal(str, dict)  # event_type, data
    
    def __init__(self, config):
        """Initialize input manager."""
        super().__init__()
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        if not PYNPUT_AVAILABLE:
            self.logger.error("pynput is not available. Input functionality will be disabled.")
            return
        
        # Listeners
        self.mouse_listener = None
        self.keyboard_listener = None
        
        # Controllers
        self.mouse_controller = mouse.Controller()
        self.keyboard_controller = keyboard.Controller()
        
        # State
        self.is_capturing = False
        self.mouse_enabled = config.get('input.mouse_enabled', True)
        self.keyboard_enabled = config.get('input.keyboard_enabled', True)
        self.sensitivity = config.get('input.sensitivity', 1.0)
        
        # Hotkeys
        self.hotkey_switch = config.get('input.hotkey_switch', 'ctrl+alt+s')
        self.hotkey_toggle = config.get('input.hotkey_toggle', 'ctrl+alt+t')
        
        # Threading
        self._capture_thread = None
        self._stop_event = threading.Event()
        
        self.logger.info("Input manager initialized")
    
    def start_capture(self) -> bool:
        """Start capturing input events."""
        if not PYNPUT_AVAILABLE:
            self.logger.error("Cannot start capture: pynput not available")
            return False
        
        if self.is_capturing:
            self.logger.warning("Input capture already active")
            return True
        
        try:
            self._stop_event.clear()
            
            # Start mouse listener
            if self.mouse_enabled:
                self.mouse_listener = MouseListener(
                    on_move=self._on_mouse_move,
                    on_click=self._on_mouse_click,
                    on_scroll=self._on_mouse_scroll
                )
                self.mouse_listener.start()
            
            # Start keyboard listener
            if self.keyboard_enabled:
                self.keyboard_listener = KeyboardListener(
                    on_press=self._on_key_press,
                    on_release=self._on_key_release
                )
                self.keyboard_listener.start()
            
            self.is_capturing = True
            self.logger.info("Input capture started")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start input capture: {e}")
            return False
    
    def stop_capture(self):
        """Stop capturing input events."""
        try:
            self.is_capturing = False
            self._stop_event.set()
            
            if self.mouse_listener:
                self.mouse_listener.stop()
                self.mouse_listener = None
            
            if self.keyboard_listener:
                self.keyboard_listener.stop()
                self.keyboard_listener = None
            
            self.logger.info("Input capture stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping input capture: {e}")
    
    def inject_input(self, event_type: str, data: Dict[str, Any]):
        """Inject input event from remote device."""
        if not PYNPUT_AVAILABLE:
            return
        
        try:
            if event_type == 'mouse_move':
                x = data.get('x', 0) * self.sensitivity
                y = data.get('y', 0) * self.sensitivity
                self.mouse_controller.position = (x, y)
            
            elif event_type == 'mouse_click':
                button_name = data.get('button', 'left')
                pressed = data.get('pressed', True)
                
                button = getattr(Button, button_name, Button.left)
                
                if pressed:
                    self.mouse_controller.press(button)
                else:
                    self.mouse_controller.release(button)
            
            elif event_type == 'mouse_scroll':
                dx = data.get('dx', 0)
                dy = data.get('dy', 0)
                self.mouse_controller.scroll(dx, dy)
            
            elif event_type == 'key_press':
                key_data = data.get('key')
                key = self._parse_key(key_data)
                if key:
                    self.keyboard_controller.press(key)
            
            elif event_type == 'key_release':
                key_data = data.get('key')
                key = self._parse_key(key_data)
                if key:
                    self.keyboard_controller.release(key)
            
        except Exception as e:
            self.logger.error(f"Failed to inject input event {event_type}: {e}")
    
    def _on_mouse_move(self, x, y):
        """Handle mouse move events."""
        if self.is_capturing:
            data = {'x': x, 'y': y}
            self.input_captured.emit('mouse_move', data)
    
    def _on_mouse_click(self, x, y, button, pressed):
        """Handle mouse click events."""
        if self.is_capturing:
            data = {
                'x': x,
                'y': y,
                'button': button.name,
                'pressed': pressed
            }
            self.input_captured.emit('mouse_click', data)
    
    def _on_mouse_scroll(self, x, y, dx, dy):
        """Handle mouse scroll events."""
        if self.is_capturing:
            data = {
                'x': x,
                'y': y,
                'dx': dx,
                'dy': dy
            }
            self.input_captured.emit('mouse_scroll', data)
    
    def _on_key_press(self, key):
        """Handle key press events."""
        if self.is_capturing:
            key_data = self._serialize_key(key)
            if key_data:
                data = {'key': key_data}
                self.input_captured.emit('key_press', data)
    
    def _on_key_release(self, key):
        """Handle key release events."""
        if self.is_capturing:
            key_data = self._serialize_key(key)
            if key_data:
                data = {'key': key_data}
                self.input_captured.emit('key_release', data)
    
    def _serialize_key(self, key) -> Optional[Dict[str, Any]]:
        """Serialize key object for transmission."""
        try:
            if hasattr(key, 'char') and key.char is not None:
                return {'type': 'char', 'value': key.char}
            elif hasattr(key, 'name'):
                return {'type': 'special', 'value': key.name}
            else:
                return {'type': 'unknown', 'value': str(key)}
        except Exception:
            return None
    
    def _parse_key(self, key_data: Dict[str, Any]):
        """Parse serialized key data back to key object."""
        try:
            if not key_data:
                return None
            
            key_type = key_data.get('type')
            value = key_data.get('value')
            
            if key_type == 'char':
                return keyboard.KeyCode.from_char(value)
            elif key_type == 'special':
                return getattr(Key, value, None)
            
        except Exception:
            pass
        
        return None
    
    def cleanup(self):
        """Cleanup input manager resources."""
        self.stop_capture()
        self.logger.info("Input manager cleanup completed") 