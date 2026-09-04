@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo [1/3] Closing old website server on port 8080...
for /f "tokens=5" %%P in ('netstat -ano ^| findstr ":8080" ^| findstr "LISTENING"') do (
  taskkill /PID %%P /F >nul 2>nul
)
timeout /t 1 /nobreak >nul

echo [2/3] Starting latest website...
where py >nul 2>nul
if not errorlevel 1 goto use_py
where python >nul 2>nul
if not errorlevel 1 goto use_python

echo.
echo [ERROR] Python 3 not found.
pause
exit /b 1

:use_py
start "ShouYing Website Server - LATEST" cmd /k "set PORT=8080&&py server.py"
goto open_site

:use_python
start "ShouYing Website Server - LATEST" cmd /k "set PORT=8080&&python server.py"

:open_site
timeout /t 2 /nobreak >nul
echo [3/3] Opening latest website...
start "" "http://127.0.0.1:8080/?v=20260904-realfix"
exit /b 0
