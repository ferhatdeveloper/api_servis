# -*- coding: utf-8 -*-
import sys
import os
import time
import logging
import win32serviceutil
import win32service
import win32event
import servicemanager
import socket
import subprocess
from pathlib import Path

# --- BOOTSTRAP: ERROR LOGGING BEFORE ANYTHING ELSE ---
# This ensures we see errors even if the class fails to load
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
if not os.path.exists(LOG_DIR):
    try: os.makedirs(LOG_DIR)
    except: pass
BOOT_LOG = os.path.join(LOG_DIR, "boot_trace.log")

def boot_trace(msg):
    try:
        with open(BOOT_LOG, "a", encoding="utf-8") as f:
            f.write(f"{time.ctime()}: {msg}\n")
    except: pass

boot_trace(f"Service Module Loaded. CWD: {os.getcwd()}. Args: {sys.argv}")

# Proje dizinini Python path'ine ekle ve çalışma dizinini değiştir
try:
    project_dir = Path(__file__).parent.parent.absolute()
    sys.path.insert(0, str(project_dir))
    os.chdir(project_dir)
    boot_trace(f"Directory changed to: {project_dir}")
except Exception as e:
    boot_trace(f"Directory change failed: {e}")

# Default names
SERVICE_NAME = "Exfin_ApiService"
SERVICE_DISPLAY_NAME = "EXFIN OPS API Service"

# Try to load custom names from api.db (Set by installer if conflict occurs)
try:
    import sqlite3
    _db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "api.db")
    if os.path.exists(_db_path):
        _conn = sqlite3.connect(_db_path)
        _row = _conn.execute("SELECT value FROM settings WHERE key = 'ServiceName'").fetchone()
        if _row:
            SERVICE_NAME = str(_row[0])
            SERVICE_DISPLAY_NAME = f"EXFIN OPS API ({SERVICE_NAME})"
        _conn.close()
except: 
    pass

class ExfinApiService(win32serviceutil.ServiceFramework):
    _svc_name_ = SERVICE_NAME
    _svc_display_name_ = SERVICE_DISPLAY_NAME
    _svc_description_ = "EXFIN Operasyon Yönetimi ve Logo ERP Entegrasyon Servisi (FastAPI)"
    
    def __init__(self, args):
        boot_trace("__init__ started")
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        self.running = False
        self.process = None
        
        # Logs dizinini oluştur
        logs_dir = os.path.join(project_dir, 'logs')
        os.makedirs(logs_dir, exist_ok=True)
        
        # Logging ayarları
        # NOT: StreamHandler (stdout) servis modunda CRASH sebebidir! Kaldırıldı.
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(os.path.join(logs_dir, 'service.log'))
            ]
        )
        self.logger = logging.getLogger(__name__)
        boot_trace("__init__ completed")
    
    def SvcStop(self):
        """Servisi durdur"""
        boot_trace("SvcStop received")
        self.logger.info('Servis durdurma sinyali alındı')
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.stop_event)
        self.running = False
        
        if self.process:
            self.logger.info('Python süreci durduruluyor...')
            try:
                self.process.terminate()
                # self.process.wait(timeout=10) # Wait can block if IO is piped
            except:
                self.logger.warning('Süreç zorla durduruluyor...')
                try: self.process.kill()
                except: pass
        
        self.ReportServiceStatus(win32service.SERVICE_STOPPED)
    
    def SvcDoRun(self):
        """Servisi çalıştır"""
        boot_trace("SvcDoRun started")
        try:
            self.logger.info(f'{self._svc_name_} servisi başlatılıyor...')
            self.logger.info(f'Çalışma dizini: {os.getcwd()}')
            self.ReportServiceStatus(win32service.SERVICE_RUNNING)
            self.running = True
            
            # Python ve Script Yolları (Branded Runner Kullanımı)
            portable_py = os.path.join(project_dir, 'python')
            if os.path.exists(portable_py):
                py_scripts = portable_py
            else:
                py_scripts = os.path.join(project_dir, 'venv', 'Scripts')
            # 1. Taşınabilir (Portable) Python kontrolü
            venv_python = os.path.join(project_dir, "python", "python.exe")
            
            if not os.path.exists(venv_python):
                # Fallback: check if python.exe is directly in project_dir
                venv_python = os.path.join(project_dir, "python.exe")
                
            if not os.path.exists(venv_python):
                # Second Fallback: Use sys.executable (could be service host)
                venv_python = sys.executable
            
            self.logger.info(f'Process Runner: {venv_python}')
            
            # --- DLL/PATH HARDENING ---
            # Logo object.dll etc. may need python in PATH
            py_root = os.path.dirname(venv_python)
            pywin32_path = os.path.join(py_root, "Lib", "site-packages", "pywin32_system32")
            
            new_paths = [py_root, os.path.join(py_root, "Scripts"), pywin32_path]
            os.environ["PATH"] = os.pathsep.join(new_paths) + os.pathsep + os.environ.get("PATH", "")
            os.environ["PYTHONHOME"] = py_root
            # --------------------------
            
            # Port (api.db'den oku)
            api_port = "8000"
            try:
                import sqlite3
                db_path = os.path.join(project_dir, "api.db")
                if os.path.exists(db_path):
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    # SQLite is case-insensitive for table/column names usually, but let's be explicit
                    # Schema provided in installer uses 'settings' (lowercase) and 'value' (lowercase)
                    cursor.execute("SELECT value FROM settings WHERE key = 'Api_Port'")
                    row = cursor.fetchone()
                    if row:
                        api_port = str(row[0])
                    conn.close()
            except Exception as db_e:
                self.logger.warning(f"Could not read port from api.db: {db_e}")
            
            cmd = [venv_python, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", api_port]
            
            self.logger.info(f'Startup Command: {" ".join(cmd)}')
            
            # Subprocess ile main.py (Uvicorn) çalıştır
            # stdout/stderr redirect is important for capturing valid uvicorn logging
            logs_dir = os.path.join(project_dir, 'logs')
            out = open(os.path.join(logs_dir, "service_stdout.log"), "a", encoding="utf-8")
            err = open(os.path.join(logs_dir, "service_stderr.log"), "a", encoding="utf-8")

            self.process = subprocess.Popen(
                cmd,
                cwd=project_dir,
                stdout=out,
                stderr=err,
                creationflags=0x08000000 # CREATE_NO_WINDOW
            )
            
            self.logger.info(f'Python süreci başlatıldı (PID: {self.process.pid})')
            
            # Servis durdurma sinyali gelene kadar bekle
            while self.running:
                if win32event.WaitForSingleObject(self.stop_event, 1000) == win32event.WAIT_OBJECT_0:
                    self.logger.info("Stop event received.")
                    break
                
                # Süreç hala çalışıyor mu kontrol et
                if self.process.poll() is not None:
                    self.logger.error(f'Python süreci beklenmedik şekilde durdu. Return Code: {self.process.returncode}')
                    break
            
        except Exception as e:
            self.logger.error(f'Servis başlatma hatası: {e}')
            import traceback
            self.logger.error(f'Hata detayı: {traceback.format_exc()}')
            self.running = False
            self.SvcStop()

if __name__ == '__main__':
    boot_trace(f"__main__ with args: {sys.argv}")
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(ExfinApiService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(ExfinApiService)
