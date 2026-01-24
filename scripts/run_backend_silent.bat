@echo off
cd /d "%~dp0\.."

REM Use explicit python path (Check for custom runner first for branding)
if exist "venv\Scripts\ExfinOpsService.exe" (
    set PYTHON_EXE=venv\Scripts\ExfinOpsService.exe
) else if exist "venv\Scripts\python.exe" (
    set PYTHON_EXE=venv\Scripts\python.exe
) else (
    set PYTHON_EXE=python
)

REM Run silently in background
start /b "" "%PYTHON_EXE%" main.py > logs\startup.log 2>&1
exit
