@echo off
setlocal
title AI Content Studio Launcher
cd /d "%~dp0backend"

rem ---- silent mode: start-hidden.vbs sets ACP_SILENT=1 -> no console, no pause ----
rem ---- visible mode: double-click start.bat -> console stays for debugging ----

echo ============================================================
echo    AI Content Studio - One-Click Launcher
echo    (Chinese banner is printed by start.py below)
echo ============================================================

rem ---- locate python: try launcher first, then python, then python3 (ASCII only for max compat)
set "PYCMD="
where py >nul 2>nul
if not errorlevel 1 set "PYCMD=py -3"
if not defined PYCMD (
  where python >nul 2>nul
  if not errorlevel 1 set "PYCMD=python"
)
if not defined PYCMD (
  where python3 >nul 2>nul
  if not errorlevel 1 set "PYCMD=python3"
)
if not defined PYCMD (
  echo.
  echo [ERROR] Python 3.10+ not found. Please install Python and add it to PATH:
  echo         https://www.python.org/downloads/
  echo         Or double-click backend\start.py after install.
  if not "%ACP_SILENT%"=="1" pause
  exit /b 1
)

echo [INFO] Using Python: %PYCMD%
%PYCMD% start.py %*
if errorlevel 1 (
  echo.
  echo [FAIL] Startup failed. Read the messages above for details.
  echo [TIP] Silent mode log: backend\logs\launcher.log
  if not "%ACP_SILENT%"=="1" pause
)
endlocal
