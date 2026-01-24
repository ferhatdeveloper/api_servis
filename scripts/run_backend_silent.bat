@echo off
cd /d "%~dp0\.."

REM Priority: Portable Python (Preferred for isolation)
if exist "python\python.exe" (
    set PYTHON_DIR=%~dp0\..\python
    set PYTHON_EXE=!PYTHON_DIR!\python.exe
    set PATH=!PYTHON_DIR!;!PYTHON_DIR!\Scripts;!PATH!
) else if exist "venv\Scripts\python.exe" (
    set PYTHON_DIR=%~dp0\..\venv\Scripts
    set PYTHON_EXE=!PYTHON_DIR!\python.exe
    set PATH=!PYTHON_DIR!;!PATH!
) else (
    set PYTHON_EXE=python
)

REM Run silently in background
start /b "" "%PYTHON_EXE%" main.py > logs\startup.log 2>&1
exit
