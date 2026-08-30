@echo off
title AI Content Studio - Docker Stop
cd /d "%~dp0"
echo Stopping and removing all containers ...
docker compose down
if errorlevel 1 (
  echo [FAIL] docker compose down failed. Make sure Docker Desktop is running.
  pause
  exit /b 1
)
pause
