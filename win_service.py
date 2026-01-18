import win32serviceutil
import win32service
import win32event
import servicemanager
import socket
import sys
import os
import subprocess
import time
from pathlib import Path

# Service Settings
SERVICE_NAME = "ExfinApiService"
SERVICE_DISPLAY_NAME = "EXFIN OPS API Service"
SERVICE_DESCRIPTION = "EXFIN API ve Logo ERP Entegrasyon Servisi (FastAPI/Uvicorn)"

class ExfinService(win32serviceutil.ServiceFramework):
    _svc_name_ = SERVICE_NAME
    _svc_display_name_ = SERVICE_DISPLAY_NAME
    _svc_description_ = SERVICE_DESCRIPTION

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        self.process = None

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
        
        # Terminate Uvicorn process
        if self.process:
            self.process.terminate()
            
    def SvcDoRun(self):
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                              servicemanager.PYS_SERVICE_STARTED,
                              (self._svc_name_, ''))
        self.main()

    def main(self):
        try:
            # Determine paths
            current_dir = str(Path(__file__).parent.absolute())
            python_exe = sys.executable
            
            # Application Entry Point
            # We run uvicorn as a subprocess to keep the service wrapper stable
            # and to allow uvicorn to handle its own async loop.
            cmd = [
                python_exe, "-m", "uvicorn", 
                "main:app", 
                "--host", "0.0.0.0", 
                "--port", "8000"
            ]
            
            # Start Process
            self.process = subprocess.Popen(
                cmd, 
                cwd=current_dir,
                stdout=open(os.path.join(current_dir, "logs", "service_stdout.log"), "a"),
                stderr=open(os.path.join(current_dir, "logs", "service_stderr.log"), "a")
            )
            
            # Wait for stop signal
            win32event.WaitForSingleObject(self.hWaitStop, win32event.INFINITE)
            
        except Exception as e:
            servicemanager.LogErrorMsg(f"Service Error: {str(e)}")

if __name__ == '__main__':
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(ExfinService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(ExfinService)
