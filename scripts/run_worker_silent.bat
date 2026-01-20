@echo off
cd /d %~dp0\..
call venv\Scripts\activate
python dashboard_app/worker.py
