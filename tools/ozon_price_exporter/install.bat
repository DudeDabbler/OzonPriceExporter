@echo off
setlocal
cd /d "%~dp0\..\.."

where py >nul 2>nul
if errorlevel 1 (
  set "PY=python"
) else (
  set "PY=py -3"
)

%PY% -m venv "tools\ozon_price_exporter\.venv"
if errorlevel 1 goto :error

"tools\ozon_price_exporter\.venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 goto :error

"tools\ozon_price_exporter\.venv\Scripts\python.exe" -m pip install -r "tools\ozon_price_exporter\requirements.txt"
if errorlevel 1 goto :error

echo.
echo Установка завершена.
echo Приложение использует установленный Google Chrome или Microsoft Edge.
echo Запустите run_ozon_price_exporter.bat из корня проекта.
pause
exit /b 0

:error
echo.
echo Установка завершилась с ошибкой. Скопируйте текст выше для диагностики.
pause
exit /b 1
