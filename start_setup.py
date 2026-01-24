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

def ensure_custom_runner(venv_scripts_dir, original_exe_name, custom_exe_name):
    """Creates a copy of the python interpreter with a custom name to show in Task Manager"""
    import shutil
    try:
        source = os.path.join(venv_scripts_dir, original_exe_name)
        target = os.path.join(venv_scripts_dir, custom_exe_name)
        
        if os.path.exists(source) and not os.path.exists(target):
            logging.info(f"Creating custom runner: {custom_exe_name}")
            shutil.copy2(source, target)
        return target if os.path.exists(target) else source
    except Exception as e:
        logging.error(f"Error creating custom runner: {e}")
        return os.path.join(venv_scripts_dir, original_exe_name)

def auto_launch_tray(base_dir):
    """Launches the Tray App automatically in the background"""
    logging.info("Attempting to auto-launch Tray App...")
    print("Tray App (Saatin yanındaki simge) başlatılıyor...")
    try:
        venv_dir = os.path.join(base_dir, "venv", "Scripts")
        tray_script = os.path.join(base_dir, "tray_app.py")
        
        # Ensure custom runner for Tray
        custom_exec = ensure_custom_runner(venv_dir, "pythonw.exe", "ExfinOpsTray.exe")
        
        logging.info(f"Launching Tray with custom exec: {custom_exec} {tray_script} --force --no-password")
        print(f"Tray App başlatılıyor: {custom_exec}")
        
        subprocess.Popen([custom_exec, tray_script, "--force", "--no-password"], 
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

    # Parse deployment mode (1=Service, 2=Tray)
    deployment_mode = "1"
    if "--mode" in sys.argv:
        try:
            m_idx = sys.argv.index("--mode")
            if len(sys.argv) > m_idx + 1:
                deployment_mode = sys.argv[m_idx + 1]
        except: pass

    # Persist choice for wizard
    try:
        import sqlite3
        db_path = os.path.join(base_dir, "api.db")
        conn = sqlite3.connect(db_path)
        conn.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)")
        conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('DeploymentMode', ?)", (deployment_mode,))
        conn.commit()
        conn.close()
    except Exception as e:
        logging.error(f"Error saving deployment mode: {e}")

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

    # 3. Prepare Custom Runner for Service (used by tray_app or bats)
    venv_scripts = os.path.join(base_dir, "venv", "Scripts")
    ensure_custom_runner(venv_scripts, "python.exe", "ExfinOpsService.exe")

    # 4. Auto-launch Tray App (User request: Launch immediately)
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
