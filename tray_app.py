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
from tkinter import simpledialog
import ctypes

# Configuration
PORT = 8000
HEALTH_URL = f"http://localhost:{PORT}/health"
DOCS_URL = f"http://localhost:{PORT}/docs"
APP_NAME = "EXFIN OPS Backend"

# Global State
is_running = False
icon = None

def create_image(color):
    """Generates a simple circular icon with the given color."""
    width = 64
    height = 64
    image = Image.new('RGB', (width, height), (255, 255, 255))
    dc = ImageDraw.Draw(image)
    dc.rectangle((0, 0, width, height), fill=(255, 255, 255))
    dc.ellipse((10, 10, width-10, height-10), fill=color, outline=color)
    return image

def check_backend_status():
    """Checks if the backend is reachable via HTTP."""
    global is_running
    try:
        response = requests.get(HEALTH_URL, timeout=1)
        if response.status_code == 200:
            return True
    except:
        pass
    
    # Second check: is port open?
    import socket
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('127.0.0.1', PORT))
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

def check_password():
    """Asks for password and returns True if correct."""
    # Hide main root window
    try:
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        
        # Bring to front hack
        try:
             root.lift()
             root.focus_force()
        except: pass

        pwd = simpledialog.askstring("Güvenlik Kontrolü", "Servisi durdurmak için şifreyi girin:", show='*', parent=root)
        root.destroy()
        
        if pwd == "1993":
            return True
        elif pwd is not None: # Not cancelled, but wrong
             # Beep or show error?
             pass
    except Exception as e:
        print(f"Dialog error: {e}")
        # Fail safe: refuse if GUI fails? or allow? 
        # Refuse is safer.
        pass
        
    return False

def stop_backend(icon, item):
    """Stops the backend process by killing port user."""
    global is_running
    
    # Password Check
    if not check_password():
        return False
    
    icon.icon = create_image('orange')
    icon.title = "Durduruluyor..."
    
    kill_process_by_port(PORT)

    time.sleep(2)
    is_running = check_backend_status()
    update_icon_visuals(icon)
    return True

def restart_backend(icon, item):
    # Only proceed if stop was successful (password correct)
    if stop_backend(icon, item):
        time.sleep(2)
        start_backend(icon, item)

def open_docs(icon, item):
    webbrowser.open(DOCS_URL)

def exit_app(icon, item):
    icon.stop()
    # Ensure backend stops on exit? Optional.
    # kill_process_by_port(PORT) 
    os._exit(0)

def main():
    global is_running
    
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
