import sys
import os

sys.path.append(os.getcwd())

try:
    print("Attempting to import app.api.v1.api...")
    from app.api.v1.api import api_router
    print("SUCCESS: app.api.v1.api imported successfully.")
    
    print("Attempting to import app.main...")
    # This might trigger database connections, so we just want to see if it syntax errors out on imports
    # If app.main is too heavy, we can skip it, but api_router is the critical part I changed.
    pass

except ImportError as e:
    print(f"FAILED: ImportError: {e}")
    sys.exit(1)
except Exception as e:
    print(f"FAILED: Exception: {e}")
    sys.exit(1)
