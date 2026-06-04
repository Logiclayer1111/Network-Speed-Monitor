import subprocess
import sys
import os
import signal

def main():
    # Start API server
    api_process = subprocess.Popen([
        sys.executable, "backend/api/main.py"
    ])
    
    # Start poller
    poller_process = subprocess.Popen([
        sys.executable, "backend/poller/main.py"
    ])
    
    # Serve frontend (simple HTTP server)
    os.chdir("frontend/build")
    frontend_process = subprocess.Popen([
        "python", "-m", "http.server", "3000"
    ])
    
    print("All services started!")
    print("Dashboard: http://localhost:3000")
    print("API: http://localhost:8000/docs")
    
    def signal_handler(sig, frame):
        print("Shutting down...")
        api_process.terminate()
        poller_process.terminate()
        frontend_process.terminate()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Keep running
    api_process.wait()

if __name__ == "__main__":
    main()