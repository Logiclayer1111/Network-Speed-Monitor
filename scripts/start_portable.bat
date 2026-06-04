@echo off
title Network Speed Monitor - Portable Mode
echo ========================================
echo Network Speed Monitor - Portable Edition
echo ========================================
echo.

REM Kill existing instances
echo Stopping existing instances...
taskkill /F /IM api_server.exe 2>nul
taskkill /F /IM speed_poller.exe 2>nul
timeout /t 1 /nobreak >nul

REM Get script directory
set SCRIPT_DIR=%~dp0
set ROOT_DIR=%SCRIPT_DIR%..
set BUILD_DIR=%ROOT_DIR%\build
set LOG_DIR=%ROOT_DIR%\logs

REM Create logs directory
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

REM Start API server
echo Starting API server...
start /B "%BUILD_DIR%\api_server.exe" > "%LOG_DIR%\api.log" 2>&1

REM Wait for API to initialize
timeout /t 3 /nobreak >nul

REM Start poller
echo Starting speed poller...
start /B "%BUILD_DIR%\speed_poller.exe" > "%LOG_DIR%\poller.log" 2>&1

REM Wait for services
timeout /t 2 /nobreak >nul

REM Open dashboard in browser
echo Opening dashboard...
start http://localhost:3000

echo.
echo ========================================
echo Network Speed Monitor is running!
echo ========================================
echo Dashboard: http://localhost:3000
echo API: http://localhost:8000/docs
echo.
echo Logs: %LOG_DIR%
echo.
echo Close this window to stop all services.
echo ========================================
echo.

pause >nul

REM Cleanup on exit
echo Stopping services...
taskkill /F /IM api_server.exe 2>nul
taskkill /F /IM speed_poller.exe 2>nul
echo Done.