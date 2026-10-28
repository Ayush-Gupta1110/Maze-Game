@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>nul
if errorlevel 1 goto use_python_launcher

py -3 main.py
if errorlevel 1 (
    echo.
    echo The game exited with an error. Check that Python and the game dependencies are installed.
    pause
)
exit /b

:use_python_launcher
where python >nul 2>nul
if errorlevel 1 (
    echo Python 3 was not found. Install Python and make sure it is on PATH.
    pause
    exit /b 1
)

python main.py
if errorlevel 1 (
    echo.
    echo The game could not start. Check the error above and ensure dependencies are installed:
    echo python -m pip install -r requirements.txt
    pause
    exit /b 1
)
