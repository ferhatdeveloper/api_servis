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

# Configuration
DEFAULT_PORT = 8000
PORT = DEFAULT_PORT
HEALTH_URL = f"http://localhost:{PORT}/health"
DOCS_URL = f"http://localhost:{PORT}/docs"
APP_NAME = "EXFIN OPS Backend"
DEFAULT_REPORT_PORT = 8501
REPORT_PORT = DEFAULT_REPORT_PORT
REPORT_URL = f"http://localhost:{REPORT_PORT}"
USE_HTTPS = False

# Global State
is_running = False
icon = None

def get_db_path():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "api.db")

def load_port_from_config():
    """Loads API_PORT and STREAMLIT_PORT from SQLite."""
    global PORT, REPORT_PORT, REPORT_URL
    db_path = get_db_path()
    try:
        import sqlite3
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            # API Port
            res = conn.execute("SELECT value FROM settings WHERE key='Api_Port'").fetchone()
            if res: PORT = int(res[0])
            
            # Report Port
            res_rep = conn.execute("SELECT value FROM settings WHERE key='Streamlit_Port'").fetchone()
            if res_rep: 
                REPORT_PORT = int(res_rep[0])
                REPORT_URL = f"http://localhost:{REPORT_PORT}"
                
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
    # background color white
    bg = (255, 255, 255)
    
    image = Image.new('RGB', (width, height), bg)
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

        response = requests.get(HEALTH_URL, timeout=1, verify=False)
        if response.status_code == 200:
            return True
    except:
        pass
    
    # 2. Fallback: Try the OTHER protocol just in case config mismatch
    try:
        other_proto = "http" if USE_HTTPS else "https"
        other_url = f"{other_proto}://127.0.0.1:{PORT}/health"
        requests.get(other_url, timeout=1, verify=False)
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
        if current_status != is_running:
            is_running = current_status
            update_icon_visuals(icon)
        time.sleep(3)

def update_icon_visuals(icon):
    """Updates the icon image and tooltip based on state."""
    if is_running:
        icon.icon = create_image('green')
        icon.title = f"{APP_NAME}: ÇALIŞIYOR (Port {PORT})"
    else:
        icon.icon = create_image('red')
        icon.title = f"{APP_NAME}: DURDU"

def start_backend(icon, item):
    """Starts the backend process."""
    global is_running
    if is_running:
        return

    icon.icon = create_image('orange')
    icon.title = "Başlatılıyor..."
    
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
        
        # Run hidden Reports (Streamlit)
        reports_bat = os.path.join(base_dir, "scripts", "run_reports_silent.bat")
        if os.path.exists(reports_bat):
             subprocess.Popen(reports_bat, shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
             
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
    import psutil
    killed = False
    
    # Method 1: PSUtil (Elegant)
    try:
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                for conn in proc.connections(kind='inet'):
                    if conn.laddr.port == port:
                        print(f"Killing PID {proc.pid} ({proc.name()})")
                        proc.kill()
                        killed = True
            except: pass
    except Exception as e:
        print(f"PSUtil error: {e}")

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

def change_report_port_action(icon, item):
    """Prompts user to change the Streamlit port."""
    global REPORT_PORT, REPORT_URL
    
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    
    new_port_str = simpledialog.askstring("Rapor Portu Değiştir", f"Mevcut Port: {REPORT_PORT}\nYeni Port Numarası giriniz:", parent=root)
    root.destroy()

    if new_port_str and new_port_str.isdigit():
        new_port = int(new_port_str)
        if 1024 <= new_port <= 65535:
            if save_port_to_config(new_port, 'Streamlit_Port'):
                REPORT_PORT = new_port
                REPORT_URL = f"http://localhost:{REPORT_PORT}"
                messagebox.showinfo("Başarılı", f"Rapor portu {REPORT_PORT} olarak güncellendi.\nEtki etmesi için 'Yeniden Başlat' yapınız.")
            else:
                messagebox.showerror("Hata", "Ayarlar kaydedilemedi!")
        else:
            messagebox.showerror("Hata", "Geçersiz Port!")

def stop_backend(icon, item):
    """Stops the backend process."""
    global is_running
    
    # Confirm action
    if not messagebox.askyesno("Onay", "Servisi durdurmak istediğinize emin misiniz?"):
        return False
    
    icon.icon = create_image('orange')
    icon.title = "Durduruluyor..."
    
    # Kill process by port
    kill_process_by_port(PORT)
    kill_process_by_port(REPORT_PORT) # Kill Streamlit
    
    # Also try killing by process name as a fallback/additional measure
    try:
        # This command targets python.exe processes that have "main.py" in their window title
        subprocess.run("taskkill /F /IM python.exe /FI \"WINDOWTITLE eq main.py*\"", shell=True, capture_output=True)
         # Streamlit generic kill (might be aggressive but ensures cleanup)
        subprocess.run("taskkill /F /IM streamlit.exe", shell=True, capture_output=True)
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
    icon.stop()
    sys.exit()

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
    global is_running, USE_HTTPS, HEALTH_URL, DOCS_URL
    
    # Load config first
    load_port_from_config()
    USE_HTTPS = load_current_https_mode()
    
    # Init URLs based on config
    protocol = "https" if USE_HTTPS else "http"
    HEALTH_URL = f"{protocol}://localhost:{PORT}/health"
    DOCS_URL = f"{protocol}://localhost:{PORT}/docs"

    # Initial status check (function needs valid URLs)
    is_running = check_backend_status()
    initial_icon = create_image('green' if is_running else 'red')
    
    menu = pystray.Menu(
        item('EXFIN OPS API v2.1', lambda: None, enabled=False),
        pystray.Menu.SEPARATOR,
        item('Swagger UI Aç', open_docs),
        item('Rapor Panelini Aç', lambda i, x: webbrowser.open(REPORT_URL)),
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
        item('Rapor Portu Değiştir', change_report_port_action),
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
    main()
