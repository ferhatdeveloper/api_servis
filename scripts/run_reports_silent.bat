@echo off
cd /d %~dp0\..
call venv\Scripts\activate
python scripts/launch_dashboard.py
