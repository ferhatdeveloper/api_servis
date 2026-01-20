import os
import datetime
import subprocess
import zipfile
import json
import pymssql
from loguru import logger
from dotenv import load_dotenv

load_dotenv()

# Postgres Env
PG_HOST = os.getenv("DB_HOST", "localhost")
PG_USER = os.getenv("DB_USER", "postgres")
PG_PASSWORD = os.getenv("DB_PASSWORD", "admin")
PG_NAME = os.getenv("DB_NAME", "EXFINOPS")

def get_db_config():
    """Reads SQLite exfin.db for MSSQL credentials, falls back to JSON"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(base_dir, "exfin.db")
    
    # 1. Try SQLite
    try:
        if os.path.exists(db_path):
            import sqlite3
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM api_connections WHERE name LIKE '%LOGO%' OR db_type LIKE '%MSSQL%' LIMIT 1").fetchone()
            conn.close()
            if row:
                res = dict(row)
                # Map to standard and legacy keys
                res["ms_host"] = res.get("db_host")
                res["ms_user"] = res.get("db_user")
                res["ms_pass"] = res.get("db_pass")
                res["ms_db"] = res.get("db_name")
                res["Server"] = res.get("db_host")
                res["Username"] = res.get("db_user")
                res["Password"] = res.get("db_pass")
                res["Database"] = res.get("db_name")
                return res
    except Exception as e:
        logger.warning(f"Failed to read exfin.db: {e}")

    # 2. Fallback to legacy JSON
    config_path = os.path.join(base_dir, "db_config.json")
    try:
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if data and len(data) > 0:
                    for item in data:
                        if isinstance(item, dict) and ("ms_host" in item or "Server" in item):
                             return item
                    if len(data) > 1: return data[1] 
    except Exception as e:
        logger.error(f"Failed to load db_config.json fallback: {e}")
    return None

def compress_file(filepath):
    """Zips a single file and removes the original"""
    if not filepath or not os.path.exists(filepath):
        return None
        
    try:
        dir_name = os.path.dirname(filepath)
        base_name = os.path.basename(filepath)
        name_no_ext = os.path.splitext(base_name)[0]
        zip_path = os.path.join(dir_name, f"{name_no_ext}.zip")
        
        logger.info(f"Compressing {base_name} to {os.path.basename(zip_path)}...")
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(filepath, base_name)
            
        try:
            os.remove(filepath) # Remove raw file
            logger.info(f"Removed raw file: {base_name}")
        except Exception as e:
            logger.warning(f"Could not remove raw file {base_name}: {e}")
            
        return zip_path
    except Exception as e:
        logger.error(f"Compression failed for {filepath}: {e}")
        return None

def backup_postgres(backup_dir, timestamp):
    """Backs up Postgres DB and zips it"""
    try:
        filename = f"{PG_NAME}_pg_{timestamp}.sql"
        filepath = os.path.join(backup_dir, filename)
        
        logger.info(f"Backing up PostgreSQL: {PG_NAME}...")
        
        env = os.environ.copy()
        env["PGPASSWORD"] = PG_PASSWORD
        
        cmd = [
            "pg_dump",
            "-h", PG_HOST,
            "-U", PG_USER,
            "-d", PG_NAME,
            "-f", filepath
        ]
        
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info(f"Postgres backup success. Zipping...")
            return compress_file(filepath)
        else:
            logger.error(f"Postgres backup failed: {result.stderr}")
            return None
    except Exception as e:
        logger.error(f"Postgres backup exception: {e}")
        return None

def backup_mssql(backup_dir, timestamp):
    """Backs up MSSQL DB and zips it"""
    config = get_db_config()
    if not config:
        logger.info("No MSSQL configuration found. Skipping MSSQL backup.")
        return None

    try:
        # Extract MSSQL details
        # Check standard keys or wizard specific keys
        server = config.get("Server") or config.get("ms_host")
        user = config.get("Username") or config.get("ms_user")
        password = config.get("Password") or config.get("ms_pass")
        db_name = config.get("Database") or config.get("ms_db")
        
        if not (server and user and password and db_name):
            #logger.warning("Incomplete MSSQL config. Skipping.")
            return None

        filename = f"{db_name}_ms_{timestamp}.bak"
        filepath = os.path.abspath(os.path.join(backup_dir, filename))
        
        logger.info(f"Backing up MSSQL: {db_name} to {filepath}...")
        
        # Connect to master to backup target DB
        conn = pymssql.connect(server=server, user=user, password=password, database="master", autocommit=True)
        cursor = conn.cursor()
        
        sql = f"BACKUP DATABASE [{db_name}] TO DISK = '{filepath}' WITH FORMAT, INIT, NAME = '{db_name}-Full Database Backup'"
        cursor.execute(sql)
        conn.close()
        
        if os.path.exists(filepath):
             logger.info(f"MSSQL backup success. Zipping...")
             return compress_file(filepath)
        else:
             logger.warning(f"MSSQL backup file not found at {filepath}")
             return None
             
    except Exception as e:
        logger.error(f"MSSQL backup exception: {e}")
        return None

def main():
    try:
        # Config setup
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        backup_dir = os.path.join(base_dir, "backups")
        
        # Read backup_config.json for dir override
        bkp_config_path = os.path.join(base_dir, "backup_config.json")
        try:
             if os.path.exists(bkp_config_path):
                with open(bkp_config_path, "r", encoding="utf-8") as f:
                    d = json.load(f)
                    if d.get("backup_dir"): backup_dir = d.get("backup_dir")
        except: pass

        os.makedirs(backup_dir, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 1. Postgres
        pg_zip = backup_postgres(backup_dir, timestamp)
        
        # 2. MSSQL
        ms_zip = backup_mssql(backup_dir, timestamp)
        
        if pg_zip or ms_zip:
            print("SUCCESS: Backup process completed.")
            if pg_zip: print(f"Postgres: {pg_zip}")
            if ms_zip: print(f"MSSQL: {ms_zip}")
        else:
            print("WARNING: No backups were generated (check logs).")

    except Exception as e:
        logger.error(f"Backup process failed: {e}")
        print(f"ERROR: {e}")

if __name__ == "__main__":
    main()
