#!/usr/bin/env python
"""
Production launcher for Network Speed Monitor.
Starts both the API server and the poller in a single process.
For development/testing only – for real deployment use Windows services or portable bat.
"""

import subprocess
import sys
import os
import signal
import time
from pathlib import Path

# Get project root directory
ROOT_DIR = Path(__file__).parent.parent
BACKEND_DIR = ROOT_DIR / "backend"
LOGS_DIR = ROOT_DIR / "logs"

def ensure_logs_directory():
    """Create logs directory if it doesn't exist"""
    LOGS_DIR.mkdir(exist_ok=True)

def start_api_server():
    """Start FastAPI server as subprocess"""
    api_script = BACKEND_DIR / "api" / "main.py"
    log_file = LOGS_DIR / "api.log"
    
    with open(log_file, "w") as log:
        proc = subprocess.Popen(
            [sys.executable, str(api_script)],
            stdout=log,
            stderr=log,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0
        )
    return proc

def start_poller():
    """Start poller service as subprocess"""
    poller_script = BACKEND_DIR / "poller" / "main.py"
    log_file = LOGS_DIR / "poller.log"
    
    with open(log_file, "w") as log:
        proc = subprocess.Popen(
            [sys.executable, str(poller_script)],
            stdout=log,
            stderr=log
        )
    return proc

def open_dashboard():
    """Open default browser to dashboard"""
    import webbrowser
    time.sleep(3)  # Wait for API to be ready
    webbrowser.open("http://localhost:3000")

def signal_handler(signum, frame):
    """Handle Ctrl+C gracefully"""
    print("\nShutting down Network Speed Monitor...")
    for proc in processes:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
    sys.exit(0)

if __name__ == "__main__":
    ensure_logs_directory()
    
    print("""
    ╔══════════════════════════════════════════════════╗
    ║     Network Speed Monitor - Production Mode      ║
    ╠══════════════════════════════════════════════════╣
    ║  Starting API server and poller...               ║
    ║  Dashboard: http://localhost:3000                ║
    ║  API Docs:   http://localhost:8000/docs          ║
    ║                                                  ║
    ║  Press Ctrl+C to stop.                           ║
    ╚══════════════════════════════════════════════════╝
    """)
    
    processes = []
    
    # Start services
    api_proc = start_api_server()
    processes.append(api_proc)
    print("[✓] API server started")
    
    poller_proc = start_poller()
    processes.append(poller_proc)
    print("[✓] Poller started")
    
    # Register signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Open dashboard in browser (optional)
    try:
        open_dashboard()
        print("[✓] Dashboard opened in browser")
    except Exception as e:
        print(f"[!] Could not open browser automatically: {e}")
    
    # Keep running until interrupted
    try:
        while True:
            # Check if subprocesses are still alive
            for proc in processes:
                if proc.poll() is not None:
                    print(f"[!] A service has stopped unexpectedly. Restarting...")
                    # Simple restart logic
                    if proc == api_proc:
                        api_proc = start_api_server()
                    elif proc == poller_proc:
                        poller_proc = start_poller()
            time.sleep(5)
    except KeyboardInterrupt:
        signal_handler(None, None)