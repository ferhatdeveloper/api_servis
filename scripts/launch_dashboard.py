import os
import sys
import sqlite3
import subprocess

def get_db_path():
    # Helper to find exfin.db relative to this script
    # This script is in backend/scripts/
    # exfin.db is in backend/
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, "exfin.db")

def get_streamlit_port():
    db_path = get_db_path()
    port = 8501
    try:
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            res = conn.execute("SELECT value FROM settings WHERE key='Streamlit_Port'").fetchone()
            conn.close()
            if res:
                port = int(res[0])
    except Exception as e:
        print(f"Warning: Could not read port from DB, using default {port}. Error: {e}")
    return port

def main():
    port = get_streamlit_port()
    print(f"Starting Streamlit Dashboard on port {port}...")
    
    # Calculate paths
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    app_path = os.path.join(base_dir, "dashboard_app", "app.py")
    
    # Construct command
    # streamlit run dashboard_app/app.py --server.port PORT --server.runOnSave false --theme.base "light"
    
    # We use sys.executable to ensure we use the same python interpreter (venv)
    # Actually streamlit is a script in Scripts/ folder usually, but running via python -m streamlit is safer
    cmd = [
        sys.executable, "-m", "streamlit", "run", app_path,
        "--server.port", str(port),
        "--server.runOnSave", "false",
        "--theme.base", "light"
    ]
    
    subprocess.run(cmd, cwd=base_dir)

if __name__ == "__main__":
    main()
