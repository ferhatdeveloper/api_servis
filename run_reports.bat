@echo off
cd /d %~dp0
call venv\Scripts\activate
echo Starting Streamlit Dashboard...
streamlit run dashboard_app/app.py --server.port 8501 --server.runOnSave false --theme.base "light"
pause
