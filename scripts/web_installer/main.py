import os
import sys
import subprocess
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
    password: Optional[str] = ""
    database: str
    load_demo: Optional[bool] = False
    app_type: Optional[str] = "OPS"
    method: Optional[str] = "direct"

@app.post("/api/test-db")
async def test_db(request: DBTestRequest):
    try:
        return installer.test_db_connection(request.dict())
    except Exception as e:
        return {"success": False, "error": installer._extract_error(e)}

@app.post("/api/logo-firms")
async def get_logo_firms(request: DBTestRequest):
    try:
        return installer.get_logo_firms(request.dict())
    except Exception as e:
        return {"success": False, "error": installer._extract_error(e)}

@app.post("/api/setup-postgresql")
async def setup_postgresql(request: DBTestRequest):
    try:
        logs = installer.setup_postgresql(
            request.host, request.port, request.username, 
            request.password, request.database, 
            app_type=request.app_type,
            load_demo=request.load_demo
        )
        return {"success": True, "message": "Veritabanı ve şemalar başarıyla oluşturuldu!", "logs": logs}
    except Exception as e:
        return {"success": False, "error": installer._extract_error(e)}

class SyncRequest(BaseModel):
    pg_config: dict
    ms_config: dict
    firm_id: str

@app.post("/api/sync-logo")
async def sync_logo(request: SyncRequest):
    try:
        return installer.sync_logo_data(request.pg_config, request.ms_config, request.firm_id)
    except Exception as e:
        return {"success": False, "error": installer._extract_error(e)}

@app.post("/api/logo-schema-info")
async def get_logo_schema_info(request: SyncRequest):
    try:
        return installer.get_logo_schema_info(request.ms_config, request.firm_id)
    except Exception as e:
        return {"success": False, "error": installer._extract_error(e)}

class SelectiveSyncRequest(SyncRequest):
    salesmen: list = []
    warehouses: list = []
    customers: list = []

@app.post("/api/sync-logo-selective")
async def sync_logo_selective(request: SelectiveSyncRequest):
    try:
        return installer.sync_logo_data_selective(
            request.pg_config, 
            request.ms_config, 
            request.firm_id,
            request.salesmen,
            request.warehouses,
            request.customers
        )
    except Exception as e:
        return {"success": False, "error": installer._extract_error(e)}

class RemoteDBRequest(BaseModel):
    connection_string: str
    local_config: dict

@app.post("/api/analyze-remote-db")
async def analyze_remote_db(request: RemoteDBRequest):
    try:
        return installer.analyze_remote_db(request.connection_string, request.local_config)
    except Exception as e:
        return {"success": False, "error": installer._extract_error(e)}

class MigrationDataRequest(RemoteDBRequest):
    tables: list

@app.post("/api/migrate-cloud-data")
async def migrate_cloud_data(request: MigrationDataRequest):
    try:
        return installer.migrate_cloud_data(request.connection_string, request.local_config, request.tables)
    except Exception as e:
        return {"success": False, "error": installer._extract_error(e)}

@app.post("/api/create-shortcuts")
async def create_shortcuts():
    return installer.create_shortcuts()

# Phase 2: Data Preview
class PreviewRequest(BaseModel):
    ms_config: dict
    firm_id: str
    data_type: str  # "salesmen", "warehouses", "companies"

@app.post("/api/preview-logo-data")
async def preview_logo_data(request: PreviewRequest):
    try:
        return installer.get_logo_preview(request.ms_config, request.firm_id, request.data_type)
    except Exception as e:
        return {"success": False, "error": installer._extract_error(e)}

# Phase 3: Backup Configuration
class BackupConfigRequest(BaseModel):
    backup_dir: str
    backup_interval: str  # "off", "hourly", "daily", "weekly"
    backup_time: str = "23:00"
    backup_hours: str = "1"
    backup_days: list = []

@app.post("/api/save-backup-config")
async def save_backup_config(request: BackupConfigRequest):
    try:
        return installer.save_backup_config(request.dict())
    except Exception as e:
        return {"success": False, "error": str(e)}

# Phase 4: SSL Certificate Generation
@app.post("/api/generate-ssl")
async def generate_ssl():
    try:
        return installer.generate_ssl_certificate()
    except Exception as e:
        return {"success": False, "error": str(e)}

class SupabaseProjectRequest(BaseModel):
    token: str

@app.post("/api/supabase-projects")
@app.post("/api/supabase-projects/")
async def get_supabase_projects(request: SupabaseProjectRequest):
    print(f"DEBUG: Supabase project request received for token mask: {request.token[:5]}***")
    return installer.get_supabase_projects(request.token)

@app.post("/api/launch-tray")
async def launch_tray():
    try:
        # 1. Kill existing tray apps to avoid duplicates/confusion
        import psutil
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmd = proc.info.get('cmdline')
                if cmd and any('tray_app.py' in s for s in cmd):
                    print(f"Killing existing tray app PID {proc.info['pid']}")
                    proc.kill()
            except: pass

        # 2. Start new instance
        venv_python = os.path.join(installer.project_dir, "venv", "Scripts", "python.exe")
        tray_script = os.path.join(installer.project_dir, "tray_app.py")
        if not os.path.exists(venv_python):
             venv_python = sys.executable
        
        # Run detached using standard flags for Windows background apps
        DETACHED_PROCESS = 0x00000008
        subprocess.Popen([venv_python, tray_script], 
                         creationflags=DETACHED_PROCESS)
        
        return {"success": True, "message": "Tray App başlatıldı. Lütfen saatin yanındaki (Gizli simgeler okuna tıklayabilirsiniz) simgeyi kontrol edin."}
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

# Static mounting for UI
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
REPORTS_DIR = os.path.join(installer.project_dir, "reports")
if not os.path.exists(REPORTS_DIR):
    os.makedirs(REPORTS_DIR)

app.mount("/reports", StaticFiles(directory=REPORTS_DIR), name="reports")
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
        # Use os.system('start') as it's more reliable for elevated processes on Windows
        os.system(f"start {url}")
    
    threading.Thread(target=open_browser, daemon=True).start()
    
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")

if __name__ == "__main__":
    start_installer()
