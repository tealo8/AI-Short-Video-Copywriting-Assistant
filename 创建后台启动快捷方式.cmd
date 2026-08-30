@echo off
chcp 65001 >nul
title 生成后台启动快捷方式
rem 在项目根目录生成「AI内容工场-后台启动.lnk」（pythonw 无控制台运行 start.py）
rem 换电脑/move 项目后双击本文件重新生成即可

set "ROOT=%~dp0"
set "PYW="
for /f "delims=" %%i in ('where pythonw.exe 2^>nul') do if not defined PYW set "PYW=%%i"

if not defined PYW (
  echo [ERROR] 未找到 pythonw.exe，请确认 Python 已安装并加入 PATH
  pause
  exit /b 1
)

echo [INFO] pythonw: %PYW%
powershell -NoProfile -Command ^
  "$ws = New-Object -ComObject WScript.Shell; " ^
  "$s = $ws.CreateShortcut('%~dp0AI内容工场-后台启动.lnk'); " ^
  "$s.TargetPath = '%PYW%'; " ^
  "$s.Arguments = '\"%~dp0backend\start.py\"'; " ^
  "$s.WorkingDirectory = '%~dp0backend'; " ^
  "$s.WindowStyle = 7; " ^
  "$s.Description = 'AI 内容工场 - 后台隐藏启动'; " ^
  "$s.Save()"

if exist "%~dp0AI内容工场-后台启动.lnk" (
  echo [OK] 快捷方式已生成：%~dp0AI内容工场-后台启动.lnk
) else (
  echo [FAIL] 生成失败，请手动检查路径
)
pause
