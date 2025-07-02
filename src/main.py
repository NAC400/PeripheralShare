#!/usr/bin/env python3
"""
PeripheralShare - Main Application Entry Point
A cross-platform peripheral sharing application for mouse, keyboard, audio, and files.
"""

import sys
import os
import logging
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QThread, pyqtSignal

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import our modules
try:
    from src.utils.logger import setup_logging
    from src.utils.config import Config
except ImportError:
    # Fallback for basic logging if modules aren't available
    logging.basicConfig(level=logging.INFO)
    print("Warning: Some modules not available. Running in minimal mode.")

class PeripheralShareApp:
    """Main application class for PeripheralShare."""
    
    def __init__(self):
        """Initialize the PeripheralShare application."""
        self.app = None
        self.main_window = None
        self.app_manager = None
        
        # Basic config fallback
        try:
            self.config = Config()
            setup_logging(self.config.get('logging.level', 'INFO'))
        except:
            logging.basicConfig(level=logging.INFO)
            self.config = None
            
        self.logger = logging.getLogger(__name__)
        
    def initialize(self):
        """Initialize the application components."""
        try:
            # Create QApplication
            self.app = QApplication(sys.argv)
            self.app.setApplicationName("PeripheralShare")
            self.app.setApplicationVersion("1.0.0")
            self.app.setOrganizationName("PeripheralShare")
            
            # Try to initialize full application
            try:
                from src.core.app_manager import AppManager
                from src.gui.main_window import MainWindow
                
                self.app_manager = AppManager(self.config)
                self.main_window = MainWindow(self.app_manager, self.config)
                
                # Connect signals
                self._connect_signals()
                
            except ImportError as e:
                # Fallback to minimal window
                from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
                
                self.main_window = QWidget()
                layout = QVBoxLayout()
                
                label = QLabel("PeripheralShare - Basic Mode")
                label.setStyleSheet("font-size: 18px; font-weight: bold; padding: 20px;")
                layout.addWidget(label)
                
                status_label = QLabel(f"Missing modules: {str(e)}")
                layout.addWidget(status_label)
                
                install_button = QPushButton("Install Dependencies")
                install_button.clicked.connect(self._show_install_help)
                layout.addWidget(install_button)
                
                self.main_window.setLayout(layout)
                self.main_window.setWindowTitle("PeripheralShare")
                self.main_window.resize(400, 300)
            
            self.logger.info("PeripheralShare application initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize application: {e}")
            print(f"Error: {e}")
            return False
    
    def _connect_signals(self):
        """Connect application signals."""
        if hasattr(self.app, 'aboutToQuit'):
            self.app.aboutToQuit.connect(self._cleanup)
    
    def _show_install_help(self):
        """Show installation help."""
        from PyQt6.QtWidgets import QMessageBox
        
        msg = QMessageBox()
        msg.setWindowTitle("Install Dependencies")
        msg.setText("To run PeripheralShare, install the required dependencies:")
        msg.setDetailedText("""
Required packages:
- pynput>=1.7.6
- PyQt6>=6.5.0
- psutil>=5.9.0
- cryptography>=41.0.0
- zeroconf>=0.69.0

Install command:
pip install pynput PyQt6 psutil cryptography zeroconf
        """)
        msg.exec()
    
    def run(self):
        """Run the application main loop."""
        if not self.initialize():
            return 1
            
        try:
            # Show main window
            if self.main_window:
                self.main_window.show()
            
            # Start the application event loop
            return self.app.exec()
            
        except KeyboardInterrupt:
            self.logger.info("Application interrupted by user")
            return 0
        except Exception as e:
            self.logger.error(f"Application error: {e}")
            print(f"Error: {e}")
            return 1
    
    def _cleanup(self):
        """Cleanup application resources."""
        self.logger.info("Cleaning up application resources...")
        
        if self.app_manager:
            try:
                self.app_manager.shutdown()
            except:
                pass
            
        self.logger.info("Application cleanup completed")


def main():
    """Main entry point for the application."""
    print("Starting PeripheralShare...")
    
    # Ensure we have proper permissions on Windows
    if sys.platform == "win32":
        try:
            import ctypes
            is_admin = ctypes.windll.shell32.IsUserAnAdmin()
            if not is_admin:
                print("Warning: Running without administrator privileges.")
                print("Some features may not work properly.")
                print("Consider running as administrator for full functionality.")
        except:
            pass
    
    # Create and run the application
    app = PeripheralShareApp()
    exit_code = app.run()
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main() 