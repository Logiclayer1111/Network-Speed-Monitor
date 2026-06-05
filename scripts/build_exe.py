"""
Build script for creating standalone executables
Run this to package the application for distribution
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def run_command(cmd, cwd=None):
    """Run a command and print output"""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        return False
    print(result.stdout)
    return True

def main():
    # Get project root
    root_dir = Path(__file__).parent.parent
    build_dir = root_dir / "build"
    dist_dir = root_dir / "dist"
    
    # Clean previous builds
    if build_dir.exists():
        print("Cleaning previous build...")
        shutil.rmtree(build_dir)
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    
    build_dir.mkdir(exist_ok=True)
    
    # Check if PyInstaller is installed
    try:
        import PyInstaller
    except ImportError:
        print("Installing PyInstaller...")
        run_command("pip install pyinstaller")
    
    # Build Poller
    print("\n" + "="*50)
    print("Building Speed Poller EXE")
    print("="*50)
    
    poller_path = root_dir / "backend" / "poller" / "main.py"
    if not run_command(
        f'pyinstaller --onefile --noconsole '
        f'--name speed_poller '
        f'--add-data "{root_dir}/backend/db;db" '
        f'--hidden-import=wmi '
        f'--hidden-import=psutil '
        f'--hidden-import=requests '
        f'--hidden-import=speedtest '
        f'--distpath "{build_dir}" '
        f'--workpath "{build_dir}/build" '
        f'--specpath "{build_dir}" '
        f'"{poller_path}"'
    ):
        print("Failed to build poller")
        return False
    
    # Move poller exe
    if (build_dir / "speed_poller.exe").exists():
        shutil.move(str(build_dir / "speed_poller.exe"), str(build_dir / "speed_poller.exe"))
    
    # Build API Server
    print("\n" + "="*50)
    print("Building API Server EXE")
    print("="*50)
    
    api_path = root_dir / "backend" / "api" / "main.py"
    if not run_command(
        f'pyinstaller --onefile --noconsole '
        f'--name api_server '
        f'--add-data "{root_dir}/backend/db;db" '
        f'--hidden-import=uvicorn '
        f'--hidden-import=fastapi '
        f'--distpath "{build_dir}" '
        f'--workpath "{build_dir}/build" '
        f'--specpath "{build_dir}" '
        f'"{api_path}"'
    ):
        print("Failed to build API server")
        return False
    
    # Build Frontend
    print("\n" + "="*50)
    print("Building React Frontend")
    print("="*50)
    
    frontend_dir = root_dir / "frontend"
    if frontend_dir.exists():
        # Install dependencies if needed
        if not (frontend_dir / "node_modules").exists():
            print("Installing frontend dependencies...")
            run_command("npm install", cwd=frontend_dir)
        
        # Build React app
        print("Building React app...")
        if run_command("npm run build", cwd=frontend_dir):
            # Copy build to dist
            frontend_build = frontend_dir / "build"
            if frontend_build.exists():
                dest = build_dir / "frontend"
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.copytree(frontend_build, dest)
                print("Frontend copied to build directory")
    else:
        print("Warning: Frontend directory not found")
    
    # Create portable package
    print("\n" + "="*50)
    print("Creating Portable Package")
    print("="*50)
    
    portable_dir = root_dir / "NetworkSpeedMonitor"
    if portable_dir.exists():
        shutil.rmtree(portable_dir)
    
    # Copy files
    shutil.copytree(build_dir, portable_dir / "build")
    
    # Copy scripts
    scripts_dir = root_dir / "scripts"
    if scripts_dir.exists():
        for script in scripts_dir.glob("*.bat"):
            shutil.copy(script, portable_dir)
        for script in scripts_dir.glob("*.py"):
            if script.name != "build_exe.py":
                shutil.copy(script, portable_dir)
    
    # Create config file
    with open(portable_dir / "config.ini", "w") as f:
        f.write("""[NetworkSpeedMonitor]
# Configuration file for Network Speed Monitor

[API]
host = 127.0.0.1
port = 8000

[Poller]
interval_min = 3
interval_max = 5
vpn_filter = true

[Database]
max_days = 30
auto_vacuum = true

[Logging]
level = INFO
max_size_mb = 10
""")
    
    # Create README
    with open(portable_dir / "README.txt", "w") as f:
        f.write("""Network Speed Monitor - Portable Edition
===========================================

Quick Start:
1. Run start_portable.bat to launch the application
2. Open http://localhost:3000 in your browser
3. Close the command window to stop

Services:
- API Server: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Dashboard: http://localhost:3000

System Tray (if installed as service):
- Right-click tray icon for quick actions

For help: https://github.com/yourusername/network-speed-monitor
""")
    
    # Create zip archive
    print("\nCreating zip archive...")
    shutil.make_archive(
        base_name=str(root_dir / "NetworkSpeedMonitor_Portable"),
        format='zip',
        root_dir=str(root_dir),
        base_dir="NetworkSpeedMonitor"
    )
    
    print("\n" + "="*50)
    print("Build Complete!")
    print("="*50)
    print(f"Portable version: {root_dir}/NetworkSpeedMonitor/")
    print(f"Zip archive: {root_dir}/NetworkSpeedMonitor_Portable.zip")
    print(f"Build output: {build_dir}")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)