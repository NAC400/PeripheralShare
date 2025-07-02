# PeripheralShare

A cross-platform application for sharing peripherals (mouse, keyboard, audio, and files) between multiple devices over a network connection.

## Features

### ? Core Functionality
- **Bidirectional Mouse Sharing**: Share mouse input between PC and laptop
- **Bidirectional Keyboard Sharing**: Share keyboard input between devices
- **File & Clipboard Sharing**: Drag and drop files between devices
- **Multi-Display Support**: Seamless cursor movement across multiple monitors
- **Audio Device Routing**: Share headphones and microphone between devices

### ?? Advanced Features
- **Network Discovery**: Automatic device discovery on local network
- **Secure Connection**: Encrypted communication between devices
- **Hotkey Support**: Customizable shortcuts for switching between devices
- **Low Latency**: Optimized for real-time input sharing
- **Cross-Platform**: Works on Windows, macOS, and Linux

## Requirements

- Python 3.8 or higher
- Administrative privileges (for input capture/injection)
- Network connectivity between devices

## Installation

### Development Setup
`ash
# Clone the repository
git clone <your-repo-url>
cd project-share

# Install dependencies
pip install -r requirements.txt

# Run the application
python src/main.py
`

## Usage

### Quick Start
1. Run PeripheralShare on both devices
2. One device acts as "Server" (primary), other as "Client" (secondary)
3. Connect via IP address or automatic discovery
4. Start sharing peripherals!

## Architecture

- src/core/: Core functionality modules
- src/network/: Network communication and discovery
- src/input/: Input capture and injection
- src/audio/: Audio routing and management
- src/gui/: User interface components
- src/utils/: Utility functions and helpers
