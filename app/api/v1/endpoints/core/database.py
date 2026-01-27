from fastapi import APIRouter, HTTPException
from loguru import logger
import psycopg2
from pathlib import Path
from app.core.config import settings

router = APIRouter()

@router.post("/migrations/run")
async def run_migrations(target_version: int = None):
    """
    Run PostgreSQL migrations
    
    Automatically creates/updates database tables and columns.
    
    Parameters:
    - target_version: Run migrations up to this version (default: latest)
    
    Example:
    POST /api/v1/database/migrations/run?target_version=2
    """
    try:
        # Get PostgreSQL connection from db_config.json
        pg_config = next(
            (c for c in settings.DB_CONFIGS if c.get("Type") == "PostgreSQL"),
            None
        )
        
        if not pg_config:
            raise HTTPException(
                status_code=500,
                detail="PostgreSQL configuration not found in db_config.json"
            )
        
        # Connect to PostgreSQL
        conn = psycopg2.connect(
            host=pg_config["Server"],
            database=pg_config["Database"],
            user=pg_config["Username"],
            password=pg_config["Password"],
            port=pg_config.get("Port", 5432)
        )
        
        cursor = conn.cursor()
        
        # Get current version
        cursor.execute("SELECT version FROM db_version WHERE id = 1")
        current_version = cursor.fetchone()[0]
        
        logger.info(f"Current database version: {current_version}")
        
        # Determine target version
        if target_version is None:
            # Find latest migration file
            migrations_dir = Path(__file__).parent.parent.parent.parent.parent / "migrations" / "postgresql"
            migration_files = sorted(migrations_dir.glob("v*_*.sql"))
            if migration_files:
                # Extract version from filename (e.g., v2_add_priority.sql -> 2)
                latest_file = migration_files[-1]
                target_version = int(latest_file.stem.split('_')[0][1:])
            else:
                target_version = current_version
        
        logger.info(f"Target version: {target_version}")
        
        # Run migrations
        applied_migrations = []
        migrations_dir = Path(__file__).parent.parent.parent.parent.parent / "migrations" / "postgresql"
        
        for version in range(current_version + 1, target_version + 1):
            migration_file = next(migrations_dir.glob(f"v{version}_*.sql"), None)
            
            if migration_file:
                logger.info(f"Applying migration: {migration_file.name}")
                
                # Read and execute migration
                with open(migration_file, 'r', encoding='utf-8') as f:
                    migration_sql = f.read()
                
                cursor.execute(migration_sql)
                conn.commit()
                
                applied_migrations.append({
                    "version": version,
                    "file": migration_file.name,
                    "status": "applied"
                })
                
                logger.info(f"✅ Migration v{version} applied successfully")
            else:
                logger.warning(f"⚠️ Migration file for v{version} not found")
        
        # Get final version
        cursor.execute("SELECT version FROM db_version WHERE id = 1")
        final_version = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        return {
            "success": True,
            "message": f"Migrations completed",
            "previous_version": current_version,
            "current_version": final_version,
            "applied_migrations": applied_migrations
        }
        
    except Exception as e:
        logger.error(f"Migration error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/migrations/status")
async def get_migration_status():
    """
    Get current database version and available migrations
    """
    try:
        # Get PostgreSQL connection
        pg_config = next(
            (c for c in settings.DB_CONFIGS if c.get("Type") == "PostgreSQL"),
            None
        )
        
        if not pg_config:
            raise HTTPException(
                status_code=500,
                detail="PostgreSQL configuration not found"
            )
        
        # Connect
        conn = psycopg2.connect(
            host=pg_config["Server"],
            database=pg_config["Database"],
            user=pg_config["Username"],
            password=pg_config["Password"],
            port=pg_config.get("Port", 5432)
        )
        
        cursor = conn.cursor()
        
        # Get current version
        cursor.execute("SELECT version, updated_at FROM db_version WHERE id = 1")
        result = cursor.fetchone()
        current_version = result[0]
        updated_at = result[1]
        
        # Get table count
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
        """)
        table_count = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        # Find available migrations
        migrations_dir = Path(__file__).parent.parent.parent.parent.parent / "migrations" / "postgresql"
        available_migrations = []
        
        if migrations_dir.exists():
            for migration_file in sorted(migrations_dir.glob("v*_*.sql")):
                version = int(migration_file.stem.split('_')[0][1:])
                available_migrations.append({
                    "version": version,
                    "file": migration_file.name,
                    "applied": version <= current_version
                })
        
        return {
            "success": True,
            "current_version": current_version,
            "updated_at": str(updated_at),
            "table_count": table_count,
            "available_migrations": available_migrations
        }
        
    except Exception as e:
        logger.error(f"Migration status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/migrations/rollback")
async def rollback_migration(target_version: int):
    """
    Rollback to a specific version
    
    Parameters:
    - target_version: Version to rollback to
    
    Example:
    POST /api/v1/database/migrations/rollback?target_version=1
    """
    try:
        # Get PostgreSQL connection
        pg_config = next(
            (c for c in settings.DB_CONFIGS if c.get("Type") == "PostgreSQL"),
            None
        )
        
        if not pg_config:
            raise HTTPException(
                status_code=500,
                detail="PostgreSQL configuration not found"
            )
        
        # Connect
        conn = psycopg2.connect(
            host=pg_config["Server"],
            database=pg_config["Database"],
            user=pg_config["Username"],
            password=pg_config["Password"],
            port=pg_config.get("Port", 5432)
        )
        
        cursor = conn.cursor()
        
        # Get current version
        cursor.execute("SELECT version FROM db_version WHERE id = 1")
        current_version = cursor.fetchone()[0]
        
        if target_version >= current_version:
            raise HTTPException(
                status_code=400,
                detail=f"Target version {target_version} must be less than current version {current_version}"
            )
        
        # Rollback migrations
        rolled_back = []
        migrations_dir = Path(__file__).parent.parent.parent.parent.parent / "migrations" / "postgresql"
        
        for version in range(current_version, target_version, -1):
            rollback_file = migrations_dir / f"rollback_v{version}.sql"
            
            if rollback_file.exists():
                logger.info(f"Rolling back v{version}")
                
                with open(rollback_file, 'r', encoding='utf-8') as f:
                    rollback_sql = f.read()
                
                cursor.execute(rollback_sql)
                conn.commit()
                
                rolled_back.append({
                    "version": version,
                    "file": rollback_file.name,
                    "status": "rolled_back"
                })
                
                logger.info(f"✅ Rollback v{version} completed")
            else:
                logger.warning(f"⚠️ Rollback file for v{version} not found")
        
        # Get final version
        cursor.execute("SELECT version FROM db_version WHERE id = 1")
        final_version = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        return {
            "success": True,
            "message": f"Rollback completed",
            "previous_version": current_version,
            "current_version": final_version,
            "rolled_back": rolled_back
        }
        
    except Exception as e:
        logger.error(f"Rollback error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/query/{database_type}")
async def get_database_query(database_type: str, query: str):
    """
    Execute a raw SQL query on the specified database
    """
    try:
        if database_type != "PostgreSQLDatabase":
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported database type: {database_type}"
            )

        # Get PostgreSQL connection
        pg_config = next(
            (c for c in settings.DB_CONFIGS if c.get("Type") == "PostgreSQL"),
            None
        )
        
        if not pg_config:
            raise HTTPException(
                status_code=500,
                detail="PostgreSQL configuration not found"
            )
        
        # Connect
        conn = psycopg2.connect(
            host=pg_config["Server"],
            database=pg_config["Database"],
            user=pg_config["Username"],
            password=pg_config["Password"],
            port=pg_config.get("Port", 5432)
        )
        
        cursor = conn.cursor()
        
        # Execute query
        cursor.execute(query)
        
        # specific logic for SELECT queries to return dicts
        if query.strip().upper().startswith("SELECT"):
            columns = [desc[0] for desc in cursor.description]
            results = []
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
                
            response_data = {
                "status": "success",
                "data": results,
                "row_count": len(results)
            }
        else:
            conn.commit()
            response_data = {
                "status": "success",
                "message": "Query executed successfully",
                "row_count": cursor.rowcount
            }
        
        cursor.close()
        conn.close()
        
        return response_data
        
    except Exception as e:
        logger.error(f"Database query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# --- Connection Management ---

from pydantic import BaseModel, Field
import sqlite3
import os

class DBConnection(BaseModel):
    Name: str = Field(..., description="Unique name for the connection")
    Type: str = Field(..., description="PostgreSQL, MSSQL, MySQL, etc.")
    Server: str
    Port: int
    Database: str
    Username: str
    Password: str

def get_api_db_path():
    # api.db is at project root
    return os.path.join(os.getcwd(), "api.db")

def ensure_connections_table():
    try:
        with sqlite3.connect(get_api_db_path()) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS db_connections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    type TEXT NOT NULL,
                    host TEXT NOT NULL,
                    port INTEGER,
                    database TEXT,
                    username TEXT,
                    password TEXT
                )
            """)
            conn.commit()
    except Exception as e:
        logger.error(f"Failed to ensure db_connections table: {e}")

@router.get("/connections")
async def list_connections():
    """List all saved database connections"""
    ensure_connections_table()
    try:
        with sqlite3.connect(get_api_db_path()) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT * FROM db_connections ORDER BY name").fetchall()
            return {
                "success": True,
                "connections": [dict(r) for r in rows]
            }
    except Exception as e:
        logger.error(f"List connections error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/connections")
async def save_connection(conn_data: DBConnection):
    """Save or Update a database connection"""
    ensure_connections_table()
    try:
        with sqlite3.connect(get_api_db_path()) as conn:
            # Upsert logic (replace if name exists)
            conn.execute("""
                INSERT OR REPLACE INTO db_connections (name, type, host, port, database, username, password)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                conn_data.Name, conn_data.Type, conn_data.Server, conn_data.Port, 
                conn_data.Database, conn_data.Username, conn_data.Password
            ))
            conn.commit()
            
            # Reload settings to apply immediately
            settings.load_db_config()
            
            return {"success": True, "message": f"Connection '{conn_data.Name}' saved successfully."}
    except Exception as e:
        logger.error(f"Save connection error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/connections/{name}")
async def delete_connection(name: str):
    """Delete a database connection"""
    ensure_connections_table()
    try:
        with sqlite3.connect(get_api_db_path()) as conn:
            cursor = conn.execute("DELETE FROM db_connections WHERE name = ?", (name,))
            conn.commit()
            
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Connection not found")

            # Reload settings
            settings.load_db_config()
            
            return {"success": True, "message": f"Connection '{name}' deleted."}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete connection error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/connections/test")
async def test_connection(conn_data: DBConnection):
    """Test a database connection without saving"""
    try:
        if "postgres" in conn_data.Type.lower():
            import psycopg2
            conn = psycopg2.connect(
                host=conn_data.Server,
                port=conn_data.Port,
                database=conn_data.Database,
                user=conn_data.Username,
                password=conn_data.Password,
                connect_timeout=3
            )
            conn.close()
            return {"success": True, "message": "PostgreSQL connection successful!"}
            
        elif "mssql" in conn_data.Type.lower():
            import platform
            if platform.system() == "Windows":
                try:
                    import pyodbc
                    drivers = [
                        'ODBC Driver 17 for SQL Server',
                        'ODBC Driver 18 for SQL Server',
                        'SQL Server Native Client 11.0',
                        'SQL Server'
                    ]
                    server_addr = f"{conn_data.Server},{conn_data.Port}" if conn_data.Port else conn_data.Server
                    conn = None
                    for driver in drivers:
                        try:
                            conn_str = f'DRIVER={{{driver}}};SERVER={server_addr};DATABASE={conn_data.Database};UID={conn_data.Username};PWD={conn_data.Password};TrustServerCertificate=yes;Connection Timeout=5;'
                            conn = pyodbc.connect(conn_str)
                            if conn: break
                        except: continue
                    
                    if conn:
                        conn.close()
                        return {"success": True, "message": "MSSQL (pyodbc) connection successful!"}
                except ImportError:
                    pass

            import pymssql
            conn = pymssql.connect(
                server=conn_data.Server,
                user=conn_data.Username,
                password=conn_data.Password,
                database=conn_data.Database,
                port=conn_data.Port,
                timeout=3
            )
            conn.close()
            return {"success": True, "message": "MSSQL (pymssql) connection successful!"}
            
        else:
            return {"success": False, "message": f"Driver for {conn_data.Type} not implemented yet."}
            
    except Exception as e:
        return {"success": False, "message": f"Connection failed: {str(e)}"}
