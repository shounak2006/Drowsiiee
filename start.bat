@echo off
title Drowsiiee AI System Launcher
echo ===================================================
echo     STARTING DROWSIIEE AI SYSTEM (Backend + UI)
echo ===================================================
echo.

:: Clean up old ports (5000 and 5173) to prevent conflicts
echo [0/2] Cleaning up old background sessions...
for /f "tokens=5" %%a in ('netstat -aon ^| find "5000" ^| find "LISTENING"') do taskkill /F /PID %%a 2>nul
for /f "tokens=5" %%a in ('netstat -aon ^| find "5173" ^| find "LISTENING"') do taskkill /F /PID %%a 2>nul

:: Start Python Backend using the correct virtual environment
echo [1/2] Starting Python AI Engine (Port 5000)...
start "Drowsiiee Backend" cmd /k "title Backend && .\venv310\Scripts\activate && python app.py"

:: Start React Frontend
echo [2/2] Starting React Dashboard (Port 5173)...
start "Drowsiiee Frontend" cmd /k "title Frontend && cd react-ui && npm run dev"

echo.
echo ===================================================
echo System successfully launched in separate windows!
echo It may take a few seconds for the dashboard to appear.
echo Go to your browser to view the Dashboard at:
echo http://localhost:5173
echo ===================================================
echo.
pause
