@echo off
REM Install as Windows service using NSSM
set SERVICE_NAME=NetworkSpeedMonitor
set POLLER_PATH=%CD%\build\speed_poller.exe
set API_PATH=%CD%\build\api_server.exe

REM Install poller service
nssm install %SERVICE_NAME%_Poller %POLLER_PATH%
nssm set %SERVICE_NAME%_Poller DisplayName "Network Speed Monitor - Poller"
nssm set %SERVICE_NAME%_Poller Start SERVICE_AUTO_START

REM Install API service
nssm install %SERVICE_NAME%_API %API_PATH%
nssm set %SERVICE_NAME%_API DisplayName "Network Speed Monitor - API"
nssm set %SERVICE_NAME%_API Start SERVICE_AUTO_START

REM Start services
net start %SERVICE_NAME%_Poller
net start %SERVICE_NAME%_API

echo Services installed and started.