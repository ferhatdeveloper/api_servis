import os
import sys
import webbrowser
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional
from installer_service import installer

# Ensure project root is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

app = FastAPI(title="EXFIN OPS Installer")


# Static mounting for UI (Moved to bottom)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")


@app.get("/api/check-prerequisites")
async def check_prerequisites():
    return installer.check_prerequisites()

class DBTestRequest(BaseModel):
    type: str
    host: str
    port: int
    username: str
    password: str
    database: str

@app.post("/api/test-db")
async def test_db(request: DBTestRequest):
    return installer.test_db_connection(request.dict())

@app.post("/api/logo-firms")
async def get_logo_firms(request: DBTestRequest):
    return installer.get_logo_firms(request.dict())

class SyncRequest(BaseModel):
    pg_config: dict
    ms_config: dict
    firm_id: str

@app.post("/api/sync-logo")
async def sync_logo(request: SyncRequest):
    return installer.sync_logo_data(request.pg_config, request.ms_config, request.firm_id)

@app.post("/api/logo-schema-info")
async def get_logo_schema_info(request: SyncRequest):
    return installer.get_logo_schema_info(request.ms_config, request.firm_id)

class SelectiveSyncRequest(SyncRequest):
    salesmen: list = []
    warehouses: list = []

@app.post("/api/sync-logo-selective")
async def sync_logo_selective(request: SelectiveSyncRequest):
    return installer.sync_logo_data_selective(
        request.pg_config, 
        request.ms_config, 
        request.firm_id,
        request.salesmen,
        request.warehouses
    )

class RemoteDBRequest(BaseModel):
    connection_string: str
    local_config: dict

@app.post("/api/analyze-remote-db")
async def analyze_remote_db(request: RemoteDBRequest):
    return installer.analyze_remote_db(request.connection_string, request.local_config)

class MigrationDataRequest(RemoteDBRequest):
    tables: list

@app.post("/api/migrate-cloud-data")
async def migrate_cloud_data(request: MigrationDataRequest):
    return installer.migrate_cloud_data(request.connection_string, request.local_config, request.tables)

@app.post("/api/create-shortcuts")
async def create_shortcuts():
    return installer.create_shortcuts()

class SupabaseProjectRequest(BaseModel):
    token: str

@app.post("/api/supabase-projects")
async def get_supabase_projects(request: SupabaseProjectRequest):
    return installer.get_supabase_projects(request.token)

@app.post("/api/launch-tray")
async def launch_tray():
    try:
        venv_python = os.path.join(installer.project_dir, "venv", "Scripts", "python.exe")
        tray_script = os.path.join(installer.project_dir, "tray_app.py")
        if not os.path.exists(venv_python):
             venv_python = sys.executable
        
        # Run detached
        subprocess.Popen([venv_python, tray_script], creationflags=subprocess.CREATE_NO_WINDOW)
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}

class ConfigRequest(BaseModel):
    settings: dict
    connections: list

@app.post("/api/save-config")
async def save_config(request: ConfigRequest):
    return installer.save_config(request.dict())

@app.post("/api/install-service")
async def install_service():
    return installer.install_windows_service()

# Mount static LAST to avoid overriding API routes
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")

def start_installer():
    """Launches the installer server and opens browser"""
    port = 8888
    url = f"http://localhost:{port}"
    print(f"Opening installer at {url}...")
    
    # Open browser after a slight delay to ensure server is up
    import threading
    def open_browser():
        import time
        time.sleep(1.5)
        webbrowser.open(url)
    
    threading.Thread(target=open_browser).start()
    
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")

if __name__ == "__main__":
    start_installer()
