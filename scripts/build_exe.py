import PyInstaller.__main__
import sys
import os

# Build poller
PyInstaller.__main__.run([
    'backend/poller/main.py',
    '--name=speed_poller',
    '--onefile',
    '--noconsole',
    '--add-data=backend/db;db',
    '--hidden-import=wmi',
    '--hidden-import=psutil'
])

# Build API server
PyInstaller.__main__.run([
    'backend/api/main.py',
    '--name=api_server',
    '--onefile',
    '--noconsole',
    '--add-data=backend/db;db'
])

# Build frontend
os.system('cd frontend && npm run build')
os.system('xcopy frontend\\build build\\frontend\\ /E /I')