@echo off
if /I "%~1"=="/u" (
  powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install.ps1" -Uninstall
) else (
  powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install.ps1"
)
pause
