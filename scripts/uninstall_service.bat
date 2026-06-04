@echo off
title Network Speed Monitor - Service Uninstaller
echo ========================================
echo Network Speed Monitor Service Uninstaller
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

set SERVICE_NAME_POLLER=NetworkSpeedMonitorPoller
set SERVICE_NAME_API=NetworkSpeedMonitorAPI

echo Stopping services...
net stop %SERVICE_NAME_POLLER% 2>nul
net stop %SERVICE_NAME_API% 2>nul

echo Removing services...
sc delete %SERVICE_NAME_POLLER% 2>nul
sc delete %SERVICE_NAME_API% 2>nul

echo.
echo Services removed successfully.
echo You may now delete the installation folder if desired.
pause