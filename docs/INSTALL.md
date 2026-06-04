---

## `INSTALL.md`

```markdown
# Installation Guide – Network Speed Monitor

This document covers two installation methods:

- **Portable (no installation)** – run from USB or any folder  
- **Windows Service** – runs in the background, starts automatically with Windows

---

## Requirements

- Windows 10 / Windows 11 (64‑bit recommended)
- No administrator rights required for **portable** mode
- Administrator rights required for **service** installation
- .NET Framework (not needed – the app is native Python compiled)

---

## Option 1: Portable Mode (Recommended for testing)

1. Download `NetworkSpeedMonitor_Portable.zip` from the [releases page](https://github.com/yourusername/network-speed-monitor/releases).
2. Extract the zip to any folder (e.g., `C:\tools\NetworkSpeedMonitor` or a USB drive).
3. Open the folder and double‑click **`start_portable.bat`**.
4. A command window will open – wait a few seconds.
5. Your default browser will open the dashboard at `http://localhost:3000`.
6. To stop, close the command window.

> **Note:** The portable version does not auto‑start with Windows. You must run `start_portable.bat` each time.

---

## Option 2: Install as Windows Service (Auto‑start)

> **Administrator rights required**

1. Download the same zip and extract it to a permanent location (e.g., `C:\Program Files\NetworkSpeedMonitor`).
2. **Right‑click** on `install_service.bat` and select **Run as administrator**.
3. The script will:
   - Download the NSSM utility (if missing)
   - Build the executables
   - Create two Windows services:
     - `NetworkSpeedMonitorPoller` – collects speed samples every 3‑5 minutes
     - `NetworkSpeedMonitorAPI` – serves the dashboard API
   - Start both services automatically.
4. After installation, open your browser and go to `http://localhost:3000`.

**To uninstall the services**, run `uninstall_service.bat` as administrator.

---

## Firewall & Anti‑virus Notes

- The API server listens on `127.0.0.1:8000` – no inbound network access needed from other machines.
- Your firewall may ask for permission when the poller runs the first speed test. Allow it.
- Some anti‑virus software may flag the PyInstaller‑generated `.exe` files as suspicious. This is a false positive. You can add the installation folder to the exclusion list.

---

## Configuration

Edit `config.ini` (created after first run) to adjust polling intervals, retention days, etc.

```ini
[Poller]
interval_min = 3
interval_max = 5
vpn_filter = true

[API]
host = 127.0.0.1
port = 8000

[Database]
max_days = 30
```
