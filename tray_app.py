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

# Global State
is_running = False
icon = None

def get_config_path():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "db_config.json")

def load_port_from_config():
    """Loads API_PORT from db_config.json if exists."""
    global PORT
    config_path = get_config_path()
    try:
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list) and len(data) > 0:
                    global_settings = data[0]
                    PORT = int(global_settings.get("Api_Port", DEFAULT_PORT))
    except Exception as e:
        print(f"Config load error: {e}")

def save_port_to_config(new_port):
    """Saves new port to db_config.json, preserving other settings."""
    config_path = get_config_path()
    data = []
    
    # Try to load existing
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except: pass
    
    # Ensure structure
    if not isinstance(data, list) or len(data) == 0:
        data = [{}] # Init global settings dict
    
    # Update Port
    data[0]["Api_Port"] = new_port
    # Ensure default fields if missing
    if "DeveloperMode" not in data[0]: data[0]["DeveloperMode"] = True
    if "Default" not in data[0]: data[0]["Default"] = "PostgreSQLDatabase"

    try:
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        return True
    except Exception as e:
        print(f"Config save error: {e}")
        return False


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
    
    # 1. Try Standard HTTP
    try:
        response = requests.get(f"http://127.0.0.1:{PORT}{HEALTH_URL}", timeout=1)
        if response.status_code == 200:
            return True
    except:
        pass

    # 2. Try HTTPS (Self-Signed)
    try:
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        response = requests.get(f"https://127.0.0.1:{PORT}{HEALTH_URL}", timeout=1, verify=False)
        if response.status_code == 200:
            return True
    except:
        pass
    
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
        # Run hidden
        subprocess.Popen(bat_path, shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
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
    
    # Prompt
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    try:
        root.lift()
        root.focus_force()
    except: pass

    new_port_str = simpledialog.askstring("Port Değiştir", f"Mevcut Port: {PORT}\nYeni Port Numarası giriniz:", parent=root)
    root.destroy()

    if new_port_str and new_port_str.isdigit():
        new_port = int(new_port_str)
        if 1024 <= new_port <= 65535:
            if save_port_to_config(new_port):
                PORT = new_port
                # Update URLs
                global HEALTH_URL, DOCS_URL
                HEALTH_URL = f"http://localhost:{PORT}/health"
                DOCS_URL = f"http://localhost:{PORT}/docs"
                
                # Ask to restart
                should_restart = messagebox.askyesno("Yeniden Başlat", "Port değişikliği için servisin yeniden başlatılması gerekiyor.\nŞimdi yapılsın mı?")
                if should_restart:
                    restart_backend(icon, item)
                else:
                    messagebox.showinfo("Bilgi", "Değişiklik bir sonraki başlangıçta aktif olacak.")
            else:
                messagebox.showerror("Hata", "Ayarlar kaydedilemedi!")
        else:
            messagebox.showerror("Hata", "Geçersiz Port! (1024 - 65535 arası olmalı)")
    elif new_port_str:
        messagebox.showerror("Hata", "Lütfen sayısal bir değer girin.")

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
    
    # Also try killing by process name as a fallback/additional measure
    try:
        # This command targets python.exe processes that have "main.py" in their window title
        # This is a common pattern for processes started by the .bat script
        subprocess.run("taskkill /F /IM python.exe /FI \"WINDOWTITLE eq main.py*\"", shell=True, capture_output=True)
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
    webbrowser.open(f"http://127.0.0.1:{PORT}/docs")

def exit_app(icon, item):
    icon.stop()
    sys.exit()

def main():
    global is_running
    
    # Load config first
    load_port_from_config()
    
    # Initial status check
    is_running = check_backend_status()
    initial_icon = create_image('green' if is_running else 'red')
    
    menu = pystray.Menu(
        item('Durum: ' + ('Çalışıyor' if is_running else 'Durdu'), lambda i, it: None, enabled=False),
        item('Swagger UI Aç', open_docs),
        pystray.Menu.SEPARATOR,
        item('Başlat', start_backend, enabled=lambda i: not is_running),
        item('Durdur', stop_backend, enabled=lambda i: is_running),
        item('Yeniden Başlat', restart_backend),
        pystray.Menu.SEPARATOR,
        item('Sistem Loglarını Gör', open_logs),
        item('Veritabanı Yedeği Al', backup_database),
        pystray.Menu.SEPARATOR,
        item('Port Değiştir', change_port_action),
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
