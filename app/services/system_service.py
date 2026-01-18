import os
import shutil
import subprocess
import sys
import glob
from datetime import datetime, timedelta
from loguru import logger
from ..core.config import settings

class SystemService:
    def __init__(self):
        self.root_dir = os.getcwd()
        self.backup_dir = os.path.join(self.root_dir, "backups")
        os.makedirs(self.backup_dir, exist_ok=True)

    def backup_current_version(self):
        """Creates a zip backup of the current application state"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        version = settings.VERSION.replace(".", "_")
        backup_name = f"v{version}_backup_{timestamp}"
        backup_path = os.path.join(self.backup_dir, backup_name)
        
        logger.info(f"Starting system backup: {backup_name}")
        
        try:
            # We use shutil.make_archive
            # But we need to exclude heavy folders (venv, .git, backups, logs)
            # shutil doesn't have an exclude filter easily.
            # Best way: Use 'zip' command or complex walk. 
            # For simplicity and cross-platform: manual walk or zip with ignore.
            
            # Simple approach: Walk and write to zip
            import zipfile
            
            zip_filename = f"{backup_path}.zip"
            
            with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(self.root_dir):
                    # Filtering directories in-place
                    dirs[:] = [d for d in dirs if d not in ['venv', '.git', '__pycache__', 'backups', 'logs', '.idea', '.vscode']]
                    
                    for file in files:
                        if file.endswith(('.pyc', '.log', '.zip')): continue
                        
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, self.root_dir)
                        zipf.write(file_path, arcname)
                        
            logger.info(f"Backup created successfully: {zip_filename}")
            return True, zip_filename
            
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            return False, str(e)

    def cleanup_old_backups(self, retention_days=10):
        """Removes backups older than retention_days"""
        logger.info("Cleaning up old backups...")
        now = datetime.now()
        retention = timedelta(days=retention_days)
        
        count = 0
        for backup_file in glob.glob(os.path.join(self.backup_dir, "*.zip")):
            try:
                creation_time = datetime.fromtimestamp(os.path.getctime(backup_file))
                if now - creation_time > retention:
                    os.remove(backup_file)
                    count += 1
                    logger.info(f"Deleted old backup: {backup_file}")
            except Exception as e:
                logger.error(f"Error deleting backup {backup_file}: {e}")
                
        return count

    async def perform_update(self):
        """Pull latest code from Git and Restart Service"""
        logger.info("Starting Auto-Update Sequence")
        
        # 1. Backup
        success, msg = self.backup_current_version()
        if not success:
            logger.error("Update aborted due to backup failure.")
            return False, f"Backup Failed: {msg}"
            
        # 2. Cleanup Old
        self.cleanup_old_backups()
        
        # 3. Git Pull
        try:
            # Check if git is clean (optional, maybe force?)
            # Usually 'git pull' is safe if no local changes.
            # We'll run 'git pull origin main' (or whatever branch)
            
            process = subprocess.run(["git", "pull"], cwd=self.root_dir, capture_output=True, text=True)
            
            if process.returncode != 0:
                logger.error(f"Git Pull Failed: {process.stderr}")
                return False, f"Git Error: {process.stderr}"
                
            if "Already up to date" in process.stdout:
                logger.info("System is already up to date.")
                # Run migrations even if code is same? Maybe manual trigger better.
                # But for safety, let's run it.
                self.migrate_database()
                return True, "No changes found. System is up to date."
                
            logger.info(f"Git Pull Success: {process.stdout}")
            
            # 4. Run Migrations
            self.migrate_database()
            
            # 5. Restart Logic
            # Since we are running as a service, we can't easily restart ourselves *from within*.
            # However, if we exit, the Windows Service Manager (Recovery Options) might restart us?
            # Or we can trigger a separate detached process to restart the service.
            
            # Best practice for self-update:
            # Trigger a small batch script or subprocess to restart the service service.
            # But the service name must be known.
            
            service_name = "ExfinApiService"
            
            # Using 'net stop' and 'net start' requires Admin privs. 
            # The service itself usually runs as System.
            
            cmd = f"net stop {service_name} && net start {service_name}"
            subprocess.Popen(cmd, shell=True) # Fire and forget
            
            return True, "Update downloaded. Service restarting..."
            
        except Exception as e:
            logger.error(f"Update Process Exception: {e}")
            return False, str(e)

    def backup_database_pg(self):
        """Backs up PostgreSQL specific DB (EXFINOPS) to Zip"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            dump_filename = f"pg_backup_{settings.DB_NAME}_{timestamp}.sql"
            dump_path = os.path.join(self.backup_dir, dump_filename)
            zip_path = dump_path + ".zip"
            
            # Locate pg_dump
            # Try Standard Paths
            pg_dump_cmd = "pg_dump" # Default path
            possible_paths = [
                r"C:\Program Files\PostgreSQL\18\bin\pg_dump.exe",
                r"C:\Program Files\PostgreSQL\16\bin\pg_dump.exe",
                r"C:\Program Files\PostgreSQL\15\bin\pg_dump.exe",
                r"C:\Program Files\PostgreSQL\14\bin\pg_dump.exe",
            ]
            for p in possible_paths:
                if os.path.exists(p):
                    pg_dump_cmd = f'"{p}"'
                    break
                    
            # Set PGPASSWORD env for this process
            env = os.environ.copy()
            env["PGPASSWORD"] = settings.DB_PASSWORD
            
            cmd = f'{pg_dump_cmd} -h {settings.DB_HOST} -p {settings.DB_PORT} -U {settings.DB_USER} -d {settings.DB_NAME} -f "{dump_path}"'
            
            logger.info(f"Starting DB Backup: {cmd}")
            process = subprocess.run(cmd, env=env, shell=True, capture_output=True, text=True)
            
            if process.returncode != 0:
                logger.error(f"PG Dump Failed: {process.stderr}")
                return False, f"PG Dump Failed: {process.stderr}"
                
            # Zip it
            import zipfile
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                zipf.write(dump_path, dump_filename)
                
            # Cleanup raw sql
            os.remove(dump_path)
            
            logger.info(f"DB Backup Success: {zip_path}")
            return True, zip_path
            
        except Exception as e:
            logger.error(f"DB Backup Exception: {e}")
            return False, str(e)

            logger.error(f"DB Backup Exception: {e}")
            return False, str(e)
            
    def migrate_database(self):
        """Runs SQL Migrations from sql/migrations folder"""
        from ..core.database import db_manager
        
        try:
            # 1. Ensure internal migration table exists
            init_query = """
            CREATE TABLE IF NOT EXISTS _schema_migrations (
                version VARCHAR(255) PRIMARY KEY,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
            db_manager.execute_pg_query(init_query, fetch=False)
            
            # 2. Get applied migrations
            applied = db_manager.execute_pg_query("SELECT version FROM _schema_migrations")
            applied_set = {row['version'] for row in applied} if applied else set()
            
            # 3. List entries in sql/migrations
            migrations_dir = os.path.join(self.root_dir, "sql", "migrations")
            if not os.path.exists(migrations_dir):
                os.makedirs(migrations_dir, exist_ok=True)
                return True, "No migrations directory found (created)."
                
            files = sorted([f for f in os.listdir(migrations_dir) if f.endswith(".sql")])
            count = 0
            
            for f in files:
                if f not in applied_set:
                    logger.info(f"Applying migration: {f}")
                    full_path = os.path.join(migrations_dir, f)
                    with open(full_path, 'r', encoding='utf-8') as sql_file:
                        sql_content = sql_file.read()
                        
                    # Execute
                    # Note: Need to handle multiple statements or robust execution
                    # execute_pg_query might handle it depending on driver (psycopg2 usually ok)
                    res = db_manager.execute_pg_query(sql_content, fetch=False)
                    
                    if res is not None: # None means error usually in my wrapper
                        # Log success
                        db_manager.execute_pg_query(
                            "INSERT INTO _schema_migrations (version) VALUES (%s)", 
                            (f,), fetch=False
                        )
                        count += 1
                        logger.info(f"Migration applied: {f}")
                    else:
                        return False, f"Migration failed: {f}"
                        
            return True, f"Applied {count} migrations."
            
        except Exception as e:
            logger.error(f"Migration Error: {e}")
            return False, str(e)

    def backup_database_mssql(self):
        """Backs up Logo MSSQL DB to Zip"""
        from ..core.database import db_manager
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            # Get Logo DB Config
            logo_config = next((c for c in settings.DB_CONFIGS if c.get("Name") == "LOGO_Database"), {})
            db_name = logo_config.get("Database", "LOGO")
            
            # Backup File Path (On SERVER)
            # Since we assume localhost, we can access it.
            # If server is remote, we can't zip it easily unless we use a share.
            # Assuming localhost for simplicity or shared path.
            
            # Default to backup folder app knows about
            # MSSQL usually needs absolute path on server filesystem
            bak_filename = f"logo_backup_{db_name}_{timestamp}.bak"
            bak_path = os.path.join(self.backup_dir, bak_filename)
            
            # Execute Backup Command
            # BACKUP DATABASE [Name] TO DISK = 'Path'
            backup_query = f"BACKUP DATABASE [{db_name}] TO DISK = '{bak_path}'"
            
            # Need to enable xp_cmdshell or just standard backup? Standard backup works if permissions ok.
            # execute_ms_query returns list or True.
            res = db_manager.execute_ms_query(backup_query, fetch=False)
            
            if res is None: # Error
                return False, "MSSQL Backup Query Failed (Check Logs)"
                
            # Verify file exists
            if not os.path.exists(bak_path):
                 return False, f"Backup file not found at {bak_path}. (Server might be remote?)"
                 
            # Zip it
            zip_filename = f"{bak_path}.zip"
            import zipfile
            with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
                 zipf.write(bak_path, bak_filename)
                 
            # Cleanup .bak
            os.remove(bak_path)
            
            return True, zip_filename
        except Exception as e:
            logger.error(f"MSSQL Backup Error: {e}")
            return False, str(e)

system_service = SystemService()
