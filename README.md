# Network Speed Monitor

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![React](https://img.shields.io/badge/react-18.x-blue.svg)](https://reactjs.org/)

**Monitor real internet speed while bypassing VPN tunnels.**

Network Speed Monitor is a lightweight Windows utility that measures your true physical network performance by automatically detecting and filtering out VPN and virtual adapters.

## How to run this project.

-Backend
python -m pip install -r requirements.txt
python backend/poller/main.py
python backend/api/main.py  
-frontend
cd frontend
npm start

## ✨ Features

- 🛡️ **VPN-Aware Polling** - Automatically filters virtual/VPN adapters
- ⏱️ **Randomized Intervals** - 3-5 minute polling prevents alignment with network events
- 📊 **Interactive Dashboard** - Real-time graphs with daily and weekly views
- 🔍 **Worst-Time Analysis** - Identifies slowest 15-minute windows
- 💾 **Low Resource Usage** - <30MB RAM, <0.5% CPU idle
- 📦 **Portable** - Single EXE + embedded React, runs from USB

## 🚀 Quick Start

### Option 1: Portable (No Installation)

```bash
# Download NetworkSpeedMonitor_Portable.zip
# Extract to USB drive or local folder
# Run start_portable.bat
# Open http://localhost:3000
```
