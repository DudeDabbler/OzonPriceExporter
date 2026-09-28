@echo off
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0tools\ozon_price_exporter\build_portable.ps1"
exit /b %ERRORLEVEL%
