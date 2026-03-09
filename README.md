PeripheralShare
===============

PeripheralShare is a Python application for sharing your mouse and keyboard between multiple machines on the same network (for example, using your desktop PC’s peripherals to control a laptop).

The current implementation focuses on **mouse and keyboard sharing** with **edge‑based seamless switching** and support for **multi‑monitor layouts** on each machine.

---

## Requirements

- **Python**: 3.8 or higher
- **OS**: Designed and tested primarily on Windows
- **Permissions**: Running as Administrator on Windows is strongly recommended
  - Required for low‑level input capture/injection and for avoiding some socket permission issues
- **Network**: Both machines must be on the same LAN (Wi‑Fi or Ethernet)

Install dependencies on each machine:

```bash
cd D:\neman\Projects\project-share  # adjust path if different
pip install -r requirements.txt
```

---

## PC (Server) Setup – Primary Machine

Use this on the machine whose mouse and keyboard you want to share (typically your desktop PC).

1. **Open an elevated terminal (recommended)**
   - Search for *Command Prompt* or *PowerShell*
   - Right‑click → **Run as administrator**
2. **Change to the project folder**
   ```cmd
   cd "D:\neman\Projects\project-share"
   ```
3. **Run the server launcher**
   ```cmd
   python start_server.py
   ```
   - Follow the on‑screen prompts (you can optionally run the network troubleshooter first).
4. In the GUI that opens:
   - Go to the **Control** tab.
   - Choose the desired **Port** in **Settings → Network** (default: `8888`).
   - Click **“Start Seamless Desktop Server”**.
   - The status should show **“Server Running”** and the log should confirm that the server started on your chosen port.

Leave this window open while using PeripheralShare.

---

## Laptop (Client) Setup – Secondary Machine

Use this on the machine you want to control with the PC’s mouse/keyboard (typically your laptop).

1. **Install Python and dependencies** (same as PC).
2. **Get the PC’s IP address**
   - On the PC (server), you can run:
     ```cmd
     ipconfig
     ```
   - Look for the IPv4 address on the active network adapter, e.g. `192.168.1.50`.
3. **Start the client GUI on the laptop**
   ```cmd
   cd "D:\neman\Projects\project-share"   # adjust path
   python src/main.py
   ```
4. In the GUI:
   - Go to the **Settings → Network** tab and ensure the **Port** matches the server (default `8888`).
   - Go to the **Control** tab.
   - In the **Client Mode (Connect to Server)** section:
     - Enter the **Server IP** (PC’s IP, e.g. `192.168.1.50`).
     - Click **“Connect”**.
   - When successful, the status will change to **“Connected”**.

Leave this window open while sharing.

---

## Using Mouse & Keyboard Sharing

- With both applications running and connected:
  - Move your mouse **to the edge of the screen** on the active machine.
  - When the cursor hits the configured edge threshold, control will be **handed off** to the other machine.
  - The receiving side warps the cursor to the corresponding edge position and starts capturing input.
  - Keyboard and mouse events are then sent over the network to the active machine.

Edge sensitivity can be adjusted on the **Control** tab:

- **Edge Sensitivity**: number of pixels from the screen edge that triggers the hand‑off.

The edge detection uses the **full virtual desktop bounds**, so multiple monitors on a single machine are supported – hitting the outermost edge of your combined display area will trigger hand‑off.

---

## Network / Firewall Notes

If the client cannot connect or you see errors like **WinError 10013 (permission denied)**:

- Prefer running the app from an **elevated (Administrator)** terminal.
- Ensure Windows Firewall allows inbound and outbound TCP on your chosen port (default `8888`).
- For detailed troubleshooting steps, see `NETWORK_TROUBLESHOOTING.md` in the project root.

---

## Developer Notes / Project Layout

- `src/main.py` – Qt application entry point and window creation.
- `src/core/app_manager.py` – Orchestrates server/client, input manager, and seamless desktop logic.
- `src/core/desktop_manager.py` – Edge detection and multi‑monitor virtual desktop handling.
- `src/network/server.py` – TCP server for connected clients, device info and input relaying.
- `src/network/client.py` – TCP client for connecting to server and sending/receiving messages.
- `src/input/manager.py` – Input capture and injection using `pynput`.
- `src/gui/main_window.py` – PyQt6 GUI (control, settings, logs, layout views).
- `src/utils/config.py` – Configuration management (ports, input settings, etc.).
- `src/utils/logger.py` – Logging helpers.
