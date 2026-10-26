@echo off
setlocal
cd /d "%~dp0"
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0Install-FarFarWestVR.ps1" %*
set "ffwExit=%errorlevel%"
echo.
pause
exit /b %ffwExit%
