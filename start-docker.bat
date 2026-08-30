@echo off
title AI Content Studio - Docker Launcher
cd /d "%~dp0"

where docker >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Docker not found. Please install Docker Desktop and keep it running:
  echo         https://www.docker.com/products/docker-desktop/
  pause
  exit /b 1
)

echo ============================================================
echo    AI Content Studio - Docker One-Click Deployment
echo    Building images and starting services (first build 3-8 min)
echo ============================================================
docker compose up -d --build
if errorlevel 1 (
  echo.
  echo [FAIL] Docker compose failed. Read the messages above.
  pause
  exit /b 1
)

echo.
echo [OK] Frontend: http://localhost
echo [OK] Backend API: http://localhost:8000/docs
echo [INFO] Stop with: docker compose down  (or double-click stop-docker.bat)
pause
