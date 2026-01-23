import ctypes
import sys

def check():
    try:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
        print(f"IsUserAnAdmin: {is_admin}")
        return is_admin != 0
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    print(f"Python Version: {sys.version}")
    print(f"Is Admin: {check()}")
