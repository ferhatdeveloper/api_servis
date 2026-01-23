import os
import sys
import subprocess
import time
import ctypes
import logging

# Setup logging
base_dir = os.path.dirname(os.path.abspath(__file__))
log_dir = os.path.join(base_dir, "logs")
if not os.path.exists(log_dir):
    os.makedirs(log_dir)
logging.basicConfig(
    filename=os.path.join(log_dir, "setup_debug.log"),
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logging.info("--- start_setup.py script started ---")

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    """Relaunches the script with admin privileges"""
    if is_admin():
        return True
    
    print("Elevating privileges to Administrator...")
    # Get the current script path and arguments
    script = os.path.abspath(sys.argv[0])
    params = ' '.join(sys.argv[1:])
    
    # Relaunch using ShellExecute with 'runas' verb
    # Use SW_HIDE (0) so the newly elevated process window doesn't pop up
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{script}" {params}', os.path.dirname(script), 0)
    sys.exit(0)

def install_dependencies():
    """Ensures installer dependencies are present"""
    required = ["fastapi", "uvicorn", "pydantic", "psutil", "requests", "psycopg2-binary", "pymssql"]
    try:
        import fastapi
        import uvicorn
        import pydantic
        import psutil
        import psycopg2
        import pymssql
    except ImportError:
        print("Installing installer dependencies...")
        subprocess.check_call([sys.executable, "-m", "pip", "install"] + required)

def hide_console():
    """Hides the console window on Windows"""
    try:
        import ctypes
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if hwnd:
            ctypes.windll.user32.ShowWindow(hwnd, 0) # SW_HIDE = 0
    except:
        pass

def kill_port_owner(port):
    """Kills any process using the specified port on Windows"""
    try:
        import psutil
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                for conns in proc.net_connections(kind='inet'):
                    if conns.laddr.port == port:
                        print(f"Port {port} is busy. Killing existing process: {proc.info['name']} (PID: {proc.info['pid']})")
                        proc.terminate()
                        proc.wait(timeout=3)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
    except Exception as e:
        print(f"Warning: Could not check port {port} using psutil: {e}")
        # Fallback to netstat/taskkill
        try:
            cmd = f'netstat -ano | findstr :{port}'
            output = subprocess.check_output(cmd, shell=True).decode()
            for line in output.strip().split('\n'):
                parts = line.split()
                if len(parts) > 4:
                    pid = parts[-1]
                    print(f"Killing process using port {port} (PID: {pid})...")
                    subprocess.run(['taskkill', '/F', '/PID', pid], capture_output=True)
        except:
            pass

def auto_launch_tray(base_dir):
    """Launches the Tray App automatically in the background"""
    logging.info("Attempting to auto-launch Tray App...")
    print("Tray App (Saatin yanındaki simge) başlatılıyor...")
    try:
        venv_dir = os.path.join(base_dir, "venv", "Scripts")
        venv_pythonw = os.path.join(venv_dir, "pythonw.exe")
        tray_script = os.path.join(base_dir, "tray_app.py")
        
        # Use pythonw.exe if available to run without a console window gracefully
        python_exec = venv_pythonw if os.path.exists(venv_pythonw) else "pythonw"
        
        logging.info(f"Launching Tray with pythonw: {python_exec} {tray_script}")
        print(f"Tray App başlatılıyor: {python_exec}")
        
        subprocess.Popen([python_exec, tray_script], 
                         cwd=base_dir)
        logging.info("Tray App process started successfully.")
        print("Tray App launch command sent.")
    except Exception as e:
        logging.error(f"Tray App launch error: {e}")
        print(f"Uyarı: Tray App otomatik başlatılamadı: {e}")

def main():
    logging.info("main() started")
    # 0. Request Admin
    run_as_admin()
    logging.info("Privileges elevated (or already admin).")
    
    # 0.1 Hide Console
    hide_console()
    logging.info("Console hidden.")

    print("=========================================")
    print("   EXFIN OPS - Modern Setup Wizard 🚀    ")
    print("=========================================")
    
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # 1. Check/Install Dependencies
    try:
        install_dependencies()
    except Exception as e:
        print(f"Error installing dependencies: {e}")
        input("Press Enter to exit...")
        sys.exit(1)

    # 2. Manage Port Conflicts
    port = 8888
    kill_port_owner(port)

    # 3. Auto-launch Tray App (User request: Launch immediately)
    auto_launch_tray(base_dir)

    # 4. Add scripts/web_installer to path
    installer_dir = os.path.join(base_dir, "scripts", "web_installer")
    sys.path.insert(0, installer_dir)

    try:
        # 3. Import and Run
        import main as installer_app
        installer_app.start_installer()
    except KeyboardInterrupt:
        print("\nSetup cancelled.")
    except Exception as e:
        print(f"\nCritical Error: {e}")
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()
