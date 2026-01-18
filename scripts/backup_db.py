import os
import datetime
import subprocess
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "admin")
DB_NAME = os.getenv("DB_NAME", "EXFINOPS")

def backup_db():
    try:
        # Create backups directory is not exists
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        backup_dir = os.path.join(base_dir, "backups")
        os.makedirs(backup_dir, exist_ok=True)
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{DB_NAME}_backup_{timestamp}.sql"
        filepath = os.path.join(backup_dir, filename)
        
        print(f"Starting backup for {DB_NAME}...")
        
        # Set password for pg_dump
        env = os.environ.copy()
        env["PGPASSWORD"] = DB_PASSWORD
        
        # Command: pg_dump -h localhost -U postgres -d EXFINOPS -f backup_file.sql
        cmd = [
            "pg_dump",
            "-h", DB_HOST,
            "-U", DB_USER,
            "-d", DB_NAME,
            "-f", filepath
        ]
        
        # Try finding pg_dump path if not in system path?
        # Usually checking default paths could be useful but let's assume it's in path or handled by OS
        
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"SUCCESS: Backup created at {filepath}")
            return True, filepath
        else:
            print(f"ERROR: {result.stderr}")
            return False, result.stderr

    except Exception as e:
        print(f"EXCEPTION: {e}")
        return False, str(e)

if __name__ == "__main__":
    backup_db()
