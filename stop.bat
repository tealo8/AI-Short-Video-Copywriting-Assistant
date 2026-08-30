@echo off
title AI Content Studio - Stop Services
echo Stopping AI Content Studio services ...
for /f "usebackq tokens=2" %%i in (`wmic process where "CommandLine like '%%AI ???  ??????%%' and name='python.exe'" get ProcessId 2^>nul ^| findstr /r "[0-9]"`) do taskkill /PID %%i /T /F >nul 2>nul
for /f "usebackq tokens=2" %%i in (`wmic process where "CommandLine like '%%AI ???  ??????%%' and name='node.exe'" get ProcessId 2^>nul ^| findstr /r "[0-9]"`) do taskkill /PID %%i /T /F >nul 2>nul
echo Done. Ports 8000 / 5173 released.
pause
