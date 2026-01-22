import os
import sys
import subprocess
import time
import ctypes

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
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{script}" {params}', None, 1)
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

def main():
    # 0. Request Admin
    run_as_admin()
    
    # 0.1 Hide Console (as requested by user)
    hide_console()

    print("=========================================")
    print("   EXFIN OPS - Modern Setup Wizard 🚀    ")
    print("=========================================")
    
    # 1. Check/Install Dependencies
    try:
        install_dependencies()
    except Exception as e:
        print(f"Error installing dependencies: {e}")
        input("Press Enter to exit...")
        sys.exit(1)

    # 2. Add scripts/web_installer to path
    base_dir = os.path.dirname(os.path.abspath(__file__))
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
