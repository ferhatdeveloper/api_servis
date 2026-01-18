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
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
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
    project_dir = Path(__file__).parent.absolute()
    sys.path.insert(0, str(project_dir))
    os.chdir(project_dir)
    boot_trace(f"Directory changed to: {project_dir}")
except Exception as e:
    boot_trace(f"Directory change failed: {e}")

SERVICE_NAME = "ExfinOPS_ApiService"
SERVICE_DISPLAY_NAME = "EXFIN OPS API Service"

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
            
            # Python ve Script Yolları
            # VENV kullanımı varsayılıyor
            venv_python = os.path.join(project_dir, 'venv', 'Scripts', 'python.exe')
            if not os.path.exists(venv_python):
                # Fallback to system python if venv not found (for reference project compat)
                venv_python = sys.executable
            
            main_script = os.path.join(project_dir, 'windows_service.py') # Trick: run ourselves or run uvicorn direct?
            # Kullanıcı uvicorn çalıştırmak istiyor.
            
            self.logger.info(f'Python Interpreter: {venv_python}')
            
            # Port
            api_port = "8000"
            try:
                env_path = os.path.join(project_dir, ".env")
                if os.path.exists(env_path):
                    with open(env_path, "r") as f:
                        for line in f:
                            if "API_PORT=" in line:
                                api_port = line.split("=")[1].strip()
            except: pass
            
            
            cmd = [venv_python, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", api_port]
            
            self.logger.info(f'Komut: {" ".join(cmd)}')
            
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
