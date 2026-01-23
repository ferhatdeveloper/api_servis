import pystray
from pystray import MenuItem as item
from PIL import Image, ImageDraw
import threading
import time
import requests
import subprocess
import os
import signal
import sys
import webbrowser
import tkinter as tk
from tkinter import simpledialog, messagebox
import ctypes
import json
import logging
import psutil

def hide_console():
    """Hides the console window on Windows"""
    try:
        import ctypes
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if hwnd:
            ctypes.windll.user32.ShowWindow(hwnd, 0) # SW_HIDE = 0
    except:
        pass

# hide_console() # Let main() or if __name__ call it later

# Setup logging
base_dir = os.path.dirname(os.path.abspath(__file__))
log_dir = os.path.join(base_dir, "logs")
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

log_file = os.path.join(log_dir, "tray_debug.log")
logging.basicConfig(
    filename=log_file,
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
try:
    logging.info("Tray App starting...")
    logging.debug(f"Current Directory: {os.getcwd()}")
    logging.debug(f"Python Executable: {sys.executable}")
except Exception as e:
    print(f"Startup logging error: {e}")

# Configuration
DEFAULT_PORT = 8000
PORT = DEFAULT_PORT
HEALTH_URL = f"http://localhost:{PORT}/health"
DOCS_URL = f"http://localhost:{PORT}/docs"
APP_NAME = "EXFIN OPS Backend"
USE_HTTPS = False

# Global State
is_running = False
icon = None
company_name = "EXFIN OPS"
LOCK_FILE = os.path.join(log_dir, "tray_app.lock")
ICON_PATH = os.path.join(base_dir, "assets", "icon.ico")

def get_db_path():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "api.db")

def load_company_name_from_db():
    """Loads active company name from PostgreSQL via local settings or direct query if possible."""
    global company_name
    db_path = get_db_path()
    try:
        import sqlite3
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            # Try to get company name from settings first
            res = conn.execute("SELECT value FROM settings WHERE key='ActiveCompanyName'").fetchone()
            if res: 
                company_name = res[0]
            conn.close()
    except: pass

def verify_password(title="Güvenlik Doğrulaması"):
    """Prompts user for a password before sensitive actions."""
    # Check for bypass flag or env var
    if "--no-password" in sys.argv or os.environ.get("EXFIN_NO_PWD") == "true":
        logging.info("Password verification bypassed (flag/env).")
        return True

    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    
    # Default password is 'admin' OR '123456' as per user's likely intent for simple setup
    # In a real app we'd load this from config
    pwd = simpledialog.askstring(title, "Lütfen yönetici şifresini giriniz:", show='*', parent=root)
    root.destroy()
    
    if pwd in ['admin', '123456']:
        return True
    
    if pwd is not None:
        messagebox.showerror("Hata", "Hatalı şifre!")
    return False

def check_existing_instance():
    """Checks if another instance is running using lock file and process check."""
    current_pid = os.getpid()
    logging.debug(f"Checking for existing instance... (My PID: {current_pid})")
    
    try:
        found_proc = None
        
        # 1. Try Lock File first (Fastest)
        if os.path.exists(LOCK_FILE):
            try:
                with open(LOCK_FILE, "r") as f:
                    old_pid = int(f.read().strip())
                if old_pid != current_pid and psutil.pid_exists(old_pid):
                    proc = psutil.Process(old_pid)
                    if any("tray_app.py" in arg for arg in proc.cmdline()):
                        found_proc = proc
                        logging.info(f"Existing instance found via LOCK FILE: PID {old_pid}")
            except: pass


        if found_proc:
            # 2. Check for force flag
            if "--force" in sys.argv or "--force-restart" in sys.argv:
                logging.info(f"Force killing existing instance (PID {found_proc.pid}) due to --force flag.")
                try:
                    found_proc.kill()
                    time.sleep(1.0)
                    if os.path.exists(LOCK_FILE):
                        try: os.remove(LOCK_FILE)
                        except: pass
                    return False # No existing instance left
                except Exception as e:
                    logging.error(f"Force kill error: {e}")

            # Found another instance! Ask user
            root = tk.Tk()
            root.withdraw()
            root.attributes("-topmost", True)
            
            # Use a slightly delayed focus to ensure it's on top of setup wizard etc.
            root.after(100, lambda: (root.lift(), root.focus_force()))
            
            response = messagebox.askyesno(
                "Uygulama Çalışıyor", 
                "EXFIN OPS Tray zaten arka planda çalışıyor.\n\nMevcut olanı kapatıp yenisini başlatmak ister misiniz?",
                parent=root
            )
            
            if response:
                if verify_password("Mevcut Uygulamayı Kapat"):
                    try:
                        logging.info(f"Killing old process {found_proc.pid}...")
                        found_proc.kill()
                        time.sleep(1.0) # wait for release
                        if os.path.exists(LOCK_FILE):
                             try: os.remove(LOCK_FILE)
                             except: pass
                        logging.info("Old instance killed. Continuing...")
                    except Exception as e:
                        logging.error(f"Kill error: {e}")
                        messagebox.showerror("Hata", f"Durdurma hatası: {e}")
                        sys.exit(0)
                else:
                    logging.info("Restart declined (password cancel/fail).")
                    sys.exit(0)
            else:
                logging.info("Restart declined by user.")
                sys.exit(0)
            root.destroy()
            return True
            
    except Exception as e:
        logging.error(f"Instance check error: {e}")
        
    logging.debug("No active existing instance found.")
    return False

def write_pid_to_lock():
    """Writes current PID to lock file."""
    try:
        with open(LOCK_FILE, "w") as f:
            f.write(str(os.getpid()))
    except Exception as e:
        logging.error(f"Could not write lock file: {e}")

def create_desktop_shortcut():
    """Creates a shortcut on the User's Desktop."""
    try:
        import winshell
        desktop_path = winshell.desktop()
    except:
        # Fallback to standard path
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        
    if not os.path.exists(desktop_path):
        logging.warning(f"Desktop path not found: {desktop_path}")
        return False
        
    # Cleanup old shortcut name if it exists
    old_path = os.path.join(desktop_path, "EXFIN OPS.lnk")
    if os.path.exists(old_path):
        try: os.remove(old_path)
        except: pass
        
    try:
        from win32com.client import Dispatch
        path = os.path.join(desktop_path, "EXFIN API SERVICES.lnk")
        target = sys.executable
        arguments = f'"{os.path.abspath(__file__)}"'
        
        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(path)
        shortcut.Targetpath = target
        shortcut.Arguments = arguments
        shortcut.WorkingDirectory = os.path.dirname(os.path.abspath(__file__))
        if os.path.exists(ICON_PATH):
            shortcut.IconLocation = ICON_PATH
        else:
            shortcut.IconLocation = target
        shortcut.save()
        logging.info("Desktop shortcut created successfully.")
        return True
    except Exception as e:
        logging.error(f"Desktop shortcut creation error: {e}")
        return False

def add_to_startup():
    """Adds the Tray App to Windows Startup via Registry and Startup Folder Shortcut."""
    success = False
    
    # 1. Method 1: Registry (HKCU\Run)
    try:
        import winreg as reg
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        app_name = "EXFIN_OPS_Tray"
        # Using sys.executable to ensure we use the same venv python
        app_path = f'"{sys.executable}" "{os.path.abspath(__file__)}"'
        
        key = reg.OpenKey(reg.HKEY_CURRENT_USER, key_path, 0, reg.KEY_WRITE)
        reg.SetValueEx(key, app_name, 0, reg.REG_SZ, app_path)
        reg.CloseKey(key)
        success = True
        logging.info("Startup registration successful (Registry).")
    except Exception as e:
        logging.error(f"Registry startup registration error: {e}")

    # 2. Method 2: Startup Folder Shortcut (More visible to user)
    try:
        import winshell
        startup_path = winshell.startup()
    except:
        # Fallback to APPDATA environment variable
        app_data = os.environ.get('APPDATA')
        if app_data:
            startup_path = os.path.join(app_data, 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup')
        else:
            startup_path = None

    if startup_path and os.path.exists(startup_path):
        try:
            from win32com.client import Dispatch
            path = os.path.join(startup_path, "EXFIN_API_SERVICES_Tray.lnk")
            target = sys.executable
            arguments = f'"{os.path.abspath(__file__)}"'
            
            shell = Dispatch('WScript.Shell')
            shortcut = shell.CreateShortCut(path)
            shortcut.Targetpath = target
            shortcut.Arguments = arguments
            shortcut.WorkingDirectory = os.path.dirname(os.path.abspath(__file__))
            if os.path.exists(ICON_PATH):
                shortcut.IconLocation = ICON_PATH
            else:
                shortcut.IconLocation = target
            shortcut.save()
            success = True
            logging.info("Startup registration successful (Startup Folder).")
        except Exception as e:
            logging.debug(f"Startup folder shortcut error: {e}")

    # 3. Method 3: Desktop Shortcut
    if create_desktop_shortcut():
        success = True

    return success

def load_port_from_config():
    """Loads API_PORT from SQLite."""
    global PORT
    db_path = get_db_path()
    try:
        import sqlite3
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            # API Port
            res = conn.execute("SELECT value FROM settings WHERE key='Api_Port'").fetchone()
            if res: PORT = int(res[0])
            conn.close()
    except: pass

def load_current_dev_mode():
    db_path = get_db_path()
    try:
        import sqlite3
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            res = conn.execute("SELECT value FROM settings WHERE key='DeveloperMode'").fetchone()
            conn.close()
            if res:
                return res[0].lower() == "true"
    except: pass
    return True

def save_port_to_config(new_port, port_key='Api_Port'):
    """Saves new port to SQLite."""
    db_path = get_db_path()
    try:
        import sqlite3
        conn = sqlite3.connect(db_path)
        conn.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)")
        conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (port_key, str(new_port)))
        conn.commit()
        conn.close()
        return True
    except: return False


def create_image(color):
    """Generates a database icon (cylinder stack) with the given color."""
    width = 64
    height = 64
    image = Image.new('RGBA', (width, height), (255, 255, 255, 0)) # Transparent background
    dc = ImageDraw.Draw(image)
    
    # Config
    fill = color
    outline = (80, 80, 80) if color != 'black' else (255,255,255)
    w_line = 2
    
    # Dimensions for cylinder
    # x1, y1, x2, y2
    
    # Bottom Base
    dc.pieslice((12, 44, 52, 58), 0, 180, fill=fill, outline=outline, width=w_line)
    dc.pieslice((12, 44, 52, 58), 180, 360, fill=fill, outline=outline, width=w_line)
    
    # Middle Section Body (Rect)
    dc.rectangle((12, 16, 52, 51), fill=fill)
    dc.line((12, 16, 12, 51), fill=outline, width=w_line) # Left wall
    dc.line((52, 16, 52, 51), fill=outline, width=w_line) # Right wall
    
    # Curve bands (Database layers)
    # Band 1 (Bottom curve of top layer)
    dc.arc((12, 28, 52, 42), 0, 180, fill=outline, width=w_line)
    
    # Band 2 (Bottom curve of middle layer)
    dc.arc((12, 14, 52, 28), 0, 180, fill=outline, width=w_line)

    # Top Cap (Full Ellipse)
    dc.ellipse((12, 6, 52, 20), fill=fill, outline=outline, width=w_line)
    
    # Re-draw outline of bottom arc to be clean overlying the rect
    dc.arc((12, 44, 52, 58), 0, 180, fill=outline, width=w_line)

    return image

def check_backend_status():
    """Checks if the backend is reachable via HTTP."""
    global is_running
    
    # 1. Try Standard Check based on current mode
    try:
        # We try the configured mode first
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        global HEALTH_URL
        # Ensure URL matches current config state if it wasn't updated yet (safety)
        protocol = "https" if USE_HTTPS else "http"
        HEALTH_URL = f"{protocol}://127.0.0.1:{PORT}/health"

        response = requests.get(HEALTH_URL, timeout=2, verify=False)
        if response.status_code == 200:
            return True
    except Exception as e:
        logging.debug(f"Health check failed: {e}")
        pass
    
    # 2. Fallback: Try the OTHER protocol just in case config mismatch
    try:
        other_proto = "http" if USE_HTTPS else "https"
        other_url = f"{other_proto}://127.0.0.1:{PORT}/health"
        requests.get(other_url, timeout=2, verify=False)
        # If this succeeds, running but on wrong proto? allow it as "running"
        return True 
    except: pass

    
    # 3. Socket Fallback (Port Open Check)
    import socket
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('127.0.0.1', int(PORT)))
        sock.close()
        if result == 0:
            return True
    except:
        pass

    return False

def update_status(icon):
    """Periodic loop to update icon status."""
    global is_running
    while True:
        current_status = check_backend_status()
        load_company_name_from_db() # Periodically refresh company name
        if current_status != is_running:
            is_running = current_status
            update_icon_visuals(icon)
        time.sleep(5)

def update_icon_visuals(icon):
    """Updates the icon image and tooltip based on state."""
    if is_running:
        icon.icon = create_image('green')
        icon.title = f"{company_name}: ÇALIŞIYOR (Port {PORT})"
    else:
        icon.icon = create_image('red')
        icon.title = f"{company_name}: DURDU"

def start_backend(icon_arg, item):
    """Starts the backend process."""
    global is_running, icon
    if is_running:
        return

    target_icon = icon_arg if icon_arg else icon
    if target_icon:
        target_icon.icon = create_image('orange')
        target_icon.title = "Başlatılıyor..."
    
    # Launch logic
    base_dir = os.path.dirname(os.path.abspath(__file__))
    bat_path = os.path.join(base_dir, "scripts", "run_backend_silent.bat")
    
    # If bat doesn't exist, create it (fallback)
    if not os.path.exists(bat_path):
         bat_path = os.path.join(base_dir, "start_backend_fallback.bat")
         with open(bat_path, "w") as f:
             venv_python = os.path.join(base_dir, "venv", "Scripts", "python.exe")
             f.write('@echo off\n')
             f.write(f'"{venv_python}" main.py\n')
    
    try:
        # Run hidden Backend
        subprocess.Popen(bat_path, shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
             
        # Run hidden Watchdog Worker
        worker_bat = os.path.join(base_dir, "scripts", "run_worker_silent.bat")
        if os.path.exists(worker_bat):
             subprocess.Popen(worker_bat, shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
             
    except Exception as e:
        print(f"Start error: {e}")

    # Give it some time
    time.sleep(2)
    is_running = check_backend_status()
    update_icon_visuals(icon)

def kill_process_by_port(port):
    """Kills any process listening on the specified port."""
    killed = False
    
    # Method 1: PSUtil (Elegant)
    try:
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                # Use net_connections() instead of connections() to avoid deprecation warnings
                for conn in proc.net_connections(kind='inet'):
                    if conn.laddr.port == port:
                        print(f"Killing PID {proc.pid} ({proc.name()})")
                        proc.kill()
                        killed = True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
            except Exception as e:
                logging.debug(f"Process check error (PID {proc.pid}): {e}")
    except Exception as e:
        logging.error(f"PSUtil error in kill_process_by_port: {e}")

    # Method 2: Netstat + Taskkill (Forceful Fallback)
    if not killed:
        try:
            # Find PID
            cmd = f'netstat -ano | findstr :{port}'
            res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            for line in res.stdout.splitlines():
                if "LISTENING" in line:
                    parts = line.split()
                    pid = parts[-1]
                    if pid and pid != "0":
                         print(f"Taskkill PID {pid}")
                         subprocess.run(f'taskkill /F /PID {pid}', shell=True, capture_output=True)
                         killed = True
        except Exception as e:
            print(f"Taskkill error: {e}")
            
    return killed

def change_port_action(icon, item):
    """Prompts user to change the API port."""
    global PORT
    
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    
    new_port_str = simpledialog.askstring("API Port Değiştir", f"Mevcut Port: {PORT}\nYeni Port Numarası giriniz:", parent=root)
    root.destroy()

    if new_port_str and new_port_str.isdigit():
        new_port = int(new_port_str)
        if 1024 <= new_port <= 65535:
            if save_port_to_config(new_port, 'Api_Port'):
                PORT = new_port
                global HEALTH_URL, DOCS_URL
                HEALTH_URL = f"http://localhost:{PORT}/health"
                DOCS_URL = f"http://localhost:{PORT}/docs"
                
                if messagebox.askyesno("Yeniden Başlat", "API portu değiştirildi. Servis yeniden başlatılsın mı?"):
                    restart_backend(icon, item)
            else:
                messagebox.showerror("Hata", "Ayarlar kaydedilemedi!")
        else:
            messagebox.showerror("Hata", "Geçersiz Port!")


def stop_backend(icon_arg, item):
    """Stops the backend process with password protection."""
    global is_running, icon
    
    # Check if this is an automated call (no item) or password confirmed
    if item is not None and not verify_password("Servisi Durdur"):
        return False
    
    target_icon = icon_arg if icon_arg else icon
    if target_icon:
        target_icon.icon = create_image('orange')
        target_icon.title = "Durduruluyor..."
    
    # Kill process by port
    kill_process_by_port(PORT)
    
    # Also try killing by process name as a fallback/additional measure
    try:
        # This command targets python.exe processes that have "main.py" in their window title
        subprocess.run("taskkill /F /IM python.exe /FI \"WINDOWTITLE eq main.py*\"", shell=True, capture_output=True)
        # Also kill the installer just in case it's still running
        subprocess.run("taskkill /F /IM python.exe /FI \"WINDOWTITLE eq EXFIN OPS - Modern Setup Wizard*\"", shell=True, capture_output=True)
    except Exception as e:
        print(f"Taskkill by name error: {e}")

    time.sleep(2)
    is_running = check_backend_status()
    update_icon_visuals(icon)
    return True

def restart_backend(icon, item):
    if stop_backend(icon, item): # Only proceed if stop was confirmed/successful
        time.sleep(2) # Give some time for processes to fully terminate
        start_backend(icon, item)

def open_logs(icon, item):
    """Opens the logs directory."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    log_dir = os.path.join(base_dir, "logs")
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    os.startfile(log_dir)

def open_backup_folder(icon, item):
    """Opens the backup directory."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    # Default
    backup_dir = os.path.join(base_dir, "backups")
    
    # Try reading config
    try:
        config_path = os.path.join(base_dir, "backup_config.json")
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                custom = data.get("backup_dir")
                if custom and os.path.exists(custom):
                    backup_dir = custom
    except: pass
    
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    os.startfile(backup_dir)

def backup_database(icon, item):
    """Runs the backup script."""
    import threading
    def run_backup():
        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            script_path = os.path.join(base_dir, "scripts", "backup_db.py")
            
            # We run it using the venv python
            venv_python = os.path.join(base_dir, "venv", "Scripts", "python.exe")
            if not os.path.exists(venv_python):
                venv_python = "python" # Fallback
            
            result = subprocess.run([venv_python, script_path], capture_output=True, text=True)
            
            if result.returncode == 0:
                icon.notify("Yedekleme Başarılı!", "Veritabanı yedeği 'backups' klasörüne alındı.")
            else:
                icon.notify("Yedekleme Hatası", f"Hata oluştu:\n{result.stderr}")
        except Exception as e:
             icon.notify("Hata", str(e))

    threading.Thread(target=run_backup).start()

def open_docs(icon, item):
    global DOCS_URL
    webbrowser.open(DOCS_URL)

def toggle_dev_mode(icon, item):
    """Toggles the Developer Mode setting in SQLite."""
    db_path = get_db_path()
    try:
        import sqlite3
        conn = sqlite3.connect(db_path)
        res = conn.execute("SELECT value FROM settings WHERE key='DeveloperMode'").fetchone()
        current_state = res[0].lower() == "true" if res else True
        new_state = not current_state
        conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('DeveloperMode', ?)", (str(new_state),))
        conn.commit()
        conn.close()
        
        state_str = "Açık" if new_state else "Kapalı"
        icon.notify("Geliştirici Modu", f"Geliştirici modu {state_str} olarak değiştirildi.")
    except Exception as e:
        icon.notify("Hata", f"Ayarlar güncellenemedi: {str(e)}")

def exit_app(icon, item):
    """Steps to exit the application cleanly with password protection."""
    if not verify_password("Uygulamadan Çıkış"):
        return
        
    # Stop backend first using enhanced logic (bypassing password since we just verified)
    logging.info("Exiting app, stopping systems...")
    stop_backend(icon, None)
    
    icon.stop()

def toggle_startup_action(icon, item):
    """Enables/Disables auto-startup."""
    if add_to_startup():
        messagebox.showinfo("Başarılı", "Uygulama Windows Başlangıcına eklendi.")
    else:
        messagebox.showerror("Hata", "Başlangıca eklenemedi!")

def load_current_https_mode():
    db_path = get_db_path()
    try:
        import sqlite3
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            res = conn.execute("SELECT value FROM settings WHERE key='UseHTTPS'").fetchone()
            conn.close()
            if res:
                return res[0].lower() == "true"
    except: pass
    return False

def toggle_https_mode(icon, item):
    """Toggles the UseHTTPS setting in SQLite."""
    db_path = get_db_path()
    try:
        import sqlite3
        conn = sqlite3.connect(db_path)
        res = conn.execute("SELECT value FROM settings WHERE key='UseHTTPS'").fetchone()
        current_state = res[0].lower() == "true" if res else False
        new_state = not current_state
        conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('UseHTTPS', ?)", (str(new_state),))
        conn.commit()
        conn.close()
        
        global USE_HTTPS, HEALTH_URL, DOCS_URL
        USE_HTTPS = new_state
        protocol = "https" if USE_HTTPS else "http"
        HEALTH_URL = f"{protocol}://localhost:{PORT}/health"
        DOCS_URL = f"{protocol}://localhost:{PORT}/docs"

        state_str = "Aktif (HTTPS)" if new_state else "Pasif (HTTP)"
        icon.notify("HTTPS Ayarı", f"HTTPS {state_str} olarak değiştirildi.")
    except Exception as e:
        icon.notify("Hata", f"Ayarlar güncellenemedi: {str(e)}")

def main():
    logging.info("main() function entered.")
    global is_running, USE_HTTPS, HEALTH_URL, DOCS_URL
    
    # Load config first
    load_port_from_config()
    USE_HTTPS = load_current_https_mode()
    
    # Init URLs based on config
    protocol = "https" if USE_HTTPS else "http"
    HEALTH_URL = f"{protocol}://localhost:{PORT}/health"
    DOCS_URL = f"{protocol}://localhost:{PORT}/docs"
    
    # Auto-register for startup
    try:
        add_to_startup()
    except: pass
    
    # Refresh company name from DB
    load_company_name_from_db()

    # Initial status check (function needs valid URLs)
    is_running = check_backend_status()
    
    # User Request: If services aren't running on tray start (e.g. after PC restart), try to start them
    if not is_running:
        logging.info("Backend services not running on startup, attempting auto-start...")
        # Small delay to ensure DB and Network are ready on PC boot
        threading.Timer(5.0, lambda: start_backend(None, None)).start()
        # Note: icon is not yet created, so we pass None
    
    initial_icon = create_image('green' if is_running else 'red')
    
    menu = pystray.Menu(
        item('EXFIN OPS API v2.1', lambda: None, enabled=False),
        pystray.Menu.SEPARATOR,
        item('Swagger UI Aç', open_docs),
        pystray.Menu.SEPARATOR,
        item('Başlat', start_backend),
        item('Durdur', stop_backend, enabled=lambda i: is_running),
        item('Yeniden Başlat', restart_backend),
        pystray.Menu.SEPARATOR,
        item('Sistem Loglarını Gör', open_logs),
        item('Yedekleme Klasörüne Git', open_backup_folder),
        item('Veritabanı Yedeği Al', backup_database),
        pystray.Menu.SEPARATOR,
        item('API Port Değiştir', change_port_action),
        item('Otomatik Başlat (Windows)', toggle_startup_action),
        item('Geliştirici Modu', toggle_dev_mode, checked=lambda i: load_current_dev_mode()),
        item('HTTPS Kullan', toggle_https_mode, checked=lambda i: load_current_https_mode()),
        pystray.Menu.SEPARATOR,
        item('Çıkış', exit_app)
    )

    global icon
    icon = pystray.Icon("EXFIN OPS", initial_icon, f"{APP_NAME}", menu)
    
    # Start status checker thread
    t = threading.Thread(target=update_status, args=(icon,), daemon=True)
    t.start()
    
    icon.run()

if __name__ == "__main__":
    # Check for existing instance before doing anything else
    check_existing_instance()
    
    # Hide console ONLY AFTER instance check to ensure any errors during check are seen if run manually
    # But usually it's fine either way.
    hide_console()
    
    # Register this instance
    write_pid_to_lock()
    
    try:
        main()
    except Exception as e:
        import traceback
        logging.error(f"FATAL ERROR in Tray App: {e}")
        logging.error(traceback.format_exc())
        # If it's a GUI error, we might want to alert the user if possible, 
        # but since it's a background app, logging is best.
        print(f"Tray App Fatal Error: {e}")
