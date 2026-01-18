
import sys
import os
from fastapi import FastAPI

# Add project root to sys.path
sys.path.append(os.path.abspath("d:/Developer/App/EXFIN_OPS/backend"))

try:
    from app.api.v1.api import api_router
    print("SUCCESS: Imported api_router")
    
    app = FastAPI()
    app.include_router(api_router, prefix="/api/v1")
    
    found_pdks = False
    print("\nChecking for PDKS routes:")
    for route in app.routes:
        if hasattr(route, "path") and "/pdks" in route.path:
            # Print only a few examples
            if "pdks" in route.path:
                found_pdks = True
                print(f"  FOUND: {route.path}")
                break
    
    if found_pdks:
        print("\nSUCCESS: PDKS routes are registered.")
    else:
        print("\nFAILURE: PDKS routes NOT found.")

except Exception as e:
    print(f"\nFAILURE: Import or Setup Error: {e}")
    import traceback
    traceback.print_exc()
