# Network Troubleshooting Guide for PeripheralShare

## Problem: WinError 10013 Socket Permission Denied

If you're seeing the error:
```
src.network.client - error - failed to connect to IP address [WinError 10013] an attempt was made to access a socket in a way forbidden by its access permissions
```

This is a common Windows socket permission issue. Here's how to fix it:

## Quick Fix Solutions

### 1. **Run the Automated Troubleshooter (Recommended)**
```bash
# Run from project directory
python troubleshoot_network.py
```
This will automatically diagnose and suggest fixes for common issues.

### 2. **Use the Easy Starter Script**
```bash
# Run from project directory  
python start_server.py
```
This script will check your system and guide you through the setup.

## Manual Solutions

### Solution 1: Run as Administrator
**Most Common Fix** - Windows requires administrator privileges for some network operations.

1. Right-click on **Command Prompt** or **PowerShell**
2. Select **"Run as administrator"**
3. Navigate to your project directory:
   ```cmd
   cd "D:\neman\Projects\project-share"
   ```
4. Run the application:
   ```cmd
   python src/main.py
   ```

### Solution 2: Configure Windows Firewall
Windows Firewall may be blocking the connection.

**Option A: Add Firewall Exception (Recommended)**
```cmd
# Run as Administrator
netsh advfirewall firewall add rule name="PeripheralShare-In" dir=in action=allow protocol=TCP localport=8888
netsh advfirewall firewall add rule name="PeripheralShare-Out" dir=out action=allow protocol=TCP localport=8888
```

**Option B: Temporarily Disable Firewall (NOT RECOMMENDED)**
```cmd
# Only for testing - re-enable afterwards!
netsh advfirewall set allprofiles state off

# To re-enable:
netsh advfirewall set allprofiles state on
```

### Solution 3: Check Port Availability
The default port (8888) might be in use by another application.

**Check what's using the port:**
```cmd
netstat -ano | findstr :8888
```

**Kill the process using the port (if needed):**
```cmd
taskkill /PID <process_id> /F
```

**Or use a different port:**
- In the GUI, change the port number from 8888 to something else (e.g., 9999)
- Make sure both server and client use the same port

### Solution 4: Reset Windows Network Stack
If all else fails, reset the Windows network stack:

```cmd
# Run as Administrator
netsh winsock reset
netsh int ip reset
```
**⚠️ Restart your computer after running these commands**

## Configuration Settings

The application now uses **port 8888** by default (changed from 12345) to match the configuration file.

### Default Ports:
- **Primary communication**: 8888
- **Service discovery**: 8889

### To change ports:
1. Open the GUI application
2. Go to the Network settings
3. Change the port number
4. Make sure both server and client use the same port

## Network Requirements

### Server Requirements:
- Port 8888 (or chosen port) available for binding
- Windows Firewall exception for the port
- Administrator privileges (recommended)

### Client Requirements:
- Network connectivity to server IP
- Port 8888 (or chosen port) not blocked by firewall
- Correct server IP address

## Testing Network Connectivity

### Test from server machine:
```cmd
# Test if server can bind to port
python -c "import socket; s=socket.socket(); s.bind(('0.0.0.0', 8888)); print('Port 8888 available'); s.close()"
```

### Test from client machine:
```cmd
# Test if client can reach server (replace SERVER_IP)
telnet SERVER_IP 8888
```

## Common Error Codes

| Error Code | Description | Solution |
|------------|-------------|----------|
| 10013 | Permission denied | Run as administrator |
| 10048 | Address already in use | Change port or kill process |
| 10061 | Connection refused | Check server is running |
| 10060 | Connection timed out | Check IP address and firewall |

## Advanced Diagnostics

### Get detailed network information:
```cmd
# Show all network interfaces
ipconfig /all

# Show all listening ports
netstat -an | findstr LISTENING

# Show firewall status
netsh advfirewall show allprofiles
```

### Check Windows services:
```cmd
# Ensure Windows Firewall service is running
sc query MpsSvc

# Ensure TCP/IP NetBIOS Helper is running  
sc query lmhosts
```

## If Nothing Works

1. **Restart as Administrator**: Close everything, restart Command Prompt as admin
2. **Restart Windows**: Some network changes require a full restart
3. **Check Antivirus**: Temporarily disable antivirus software
4. **Use Different Port**: Try ports like 9999, 7777, or 6666
5. **Contact Support**: Run `python troubleshoot_network.py` and share the output

## Success Checklist

✅ Running as Administrator  
✅ Port 8888 is available  
✅ Windows Firewall exception added  
✅ Server shows "Server started on port 8888"  
✅ Client can ping server IP  
✅ Both machines on same network  

---

**Need help?** Run the troubleshooter: `python troubleshoot_network.py` 