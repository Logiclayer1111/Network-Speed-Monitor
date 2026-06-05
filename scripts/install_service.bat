@echo off
title Network Speed Monitor - Service Installer
echo ========================================
echo Network Speed Monitor Service Installer
echo ========================================
echo.

REM Check for admin privileges
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: This script requires Administrator privileges.
    echo Right-click and select "Run as Administrator"
    pause
    exit /b 1
)

REM Set paths
set SERVICE_NAME_POLLER=NetworkSpeedMonitorPoller
set SERVICE_NAME_API=NetworkSpeedMonitorAPI
set INSTALL_DIR=%CD%
set NSSM_URL=https://nssm.cc/release/nssm-2.24.zip
set NSSM_DIR=%INSTALL_DIR%\nssm

echo Installing Network Speed Monitor services...
echo.

REM Download nssm if not present
if not exist "%NSSM_DIR%\nssm.exe" (
    echo Downloading nssm (service wrapper)...
    powershell -Command "Invoke-WebRequest %NSSM_URL% -OutFile %INSTALL_DIR%\nssm.zip"
    powershell -Command "Expand-Archive %INSTALL_DIR%\nssm.zip -DestinationPath %INSTALL_DIR%"
    move "%INSTALL_DIR%\nssm-2.24" "%NSSM_DIR%" 2>nul
    del "%INSTALL_DIR%\nssm.zip" 2>nul
)

REM Build executables
echo Building executables...
cd "%INSTALL_DIR%\.."
python scripts\build_exe.py
cd "%INSTALL_DIR%"

REM Install Poller Service
echo Installing Poller Service...
"%NSSM_DIR%\nssm.exe" install %SERVICE_NAME_POLLER% "%INSTALL_DIR%\..\build\speed_poller.exe"
"%NSSM_DIR%\nssm.exe" set %SERVICE_NAME_POLLER% DisplayName "Network Speed Monitor - Poller"
"%NSSM_DIR%\nssm.exe" set %SERVICE_NAME_POLLER% Description "Collects network speed samples every 3-5 minutes"
"%NSSM_DIR%\nssm.exe" set %SERVICE_NAME_POLLER% Start SERVICE_AUTO_START
"%NSSM_DIR%\nssm.exe" set %SERVICE_NAME_POLLER% AppStdout "%INSTALL_DIR%\..\logs\poller.log"
"%NSSM_DIR%\nssm.exe" set %SERVICE_NAME_POLLER% AppStderr "%INSTALL_DIR%\..\logs\poller_error.log"

REM Install API Service
echo Installing API Service...
"%NSSM_DIR%\nssm.exe" install %SERVICE_NAME_API% "%INSTALL_DIR%\..\build\api_server.exe"
"%NSSM_DIR%\nssm.exe" set %SERVICE_NAME_API% DisplayName "Network Speed Monitor - API"
"%NSSM_DIR%\nssm.exe" set %SERVICE_NAME_API% Description "REST API for speed monitoring dashboard"
"%NSSM_DIR%\nssm.exe" set %SERVICE_NAME_API% Start SERVICE_AUTO_START
"%NSSM_DIR%\nssm.exe" set %SERVICE_NAME_API% AppStdout "%INSTALL_DIR%\..\logs\api.log"
"%NSSM_DIR%\nssm.exe" set %SERVICE_NAME_API% AppStderr "%INSTALL_DIR%\..\logs\api_error.log"

REM Start services
echo Starting services...
net start %SERVICE_NAME_POLLER%
net start %SERVICE_NAME_API%

echo.
echo ========================================
echo Installation Complete!
echo ========================================
echo Services installed:
echo   - %SERVICE_NAME_POLLER%
echo   - %SERVICE_NAME_API%
echo.
echo Dashboard: http://localhost:3000
echo API Docs: http://localhost:8000/docs
echo.
echo Logs: %INSTALL_DIR%\..\logs\
echo.
pause