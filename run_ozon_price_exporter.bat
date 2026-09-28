@echo off
setlocal
cd /d "%~dp0"
set "VENV_PY=tools\ozon_price_exporter\.venv\Scripts\python.exe"

if exist "%VENV_PY%" (
  "%VENV_PY%" -m tools.ozon_price_exporter
) else (
  echo Среда приложения не установлена.
  echo Сначала запустите tools\ozon_price_exporter\install.bat
  pause
  exit /b 1
)
