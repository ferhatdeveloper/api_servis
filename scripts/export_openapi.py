import json
import sys
import os

# Add backend root to python path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(backend_path)

try:
    from main import app
    
    print("Generating OpenAPI schema...")
    openapi_schema = app.openapi()
    
    output_path = os.path.join(backend_path, "openapi.json")
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(openapi_schema, f, ensure_ascii=False, indent=2)
        
    print(f"Successfully exported OpenAPI schema to: {output_path}")
    print("You can import this file directly into Postman.")
    
except Exception as e:
    print(f"Error exporting schema: {e}")
    sys.exit(1)
