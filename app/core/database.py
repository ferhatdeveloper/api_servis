import pymssql
import psycopg2
from psycopg2.extras import RealDictCursor
from loguru import logger
from .config import settings

class DatabaseManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._instance.connections = {}
        return cls._instance
    
    def get_connection(self, name: str):
        """Get or create a connection by its Name from db_config.json"""
        if name in self.connections:
            conn = self.connections[name]
            # Check if closed
            if hasattr(conn, 'closed') and conn.closed:
                del self.connections[name]
            else:
                return conn
                
        # Connection not found or closed, create new
        config = next((c for c in settings.DB_CONFIGS if c.get("Name") == name), None)
        
        # Fallback to Env Variables if not found in db_config.json
        if not config:
            if name == "PostgreSQLDatabase" or name == settings.DEFAULT_DB:
                config = {
                    "Type": "PostgreSQL",
                    "Server": settings.DB_HOST,
                    "Port": settings.DB_PORT,
                    "Database": settings.DB_NAME,
                    "Username": settings.DB_USER,
                    "Password": settings.DB_PASSWORD
                }
            elif name == "LOGO_Database":
                if settings.LOGO_DB_HOST:
                    config = {
                        "Type": "MSSQL",
                        "Server": settings.LOGO_DB_HOST,
                        # Assuming DB name is handled or default, or added to env later
                        "Database": settings.LOGO_DB_NAME, 
                        "Username": settings.LOGO_DB_USER,
                        "Password": settings.LOGO_DB_PASSWORD
                    }
                else:
                    logger.warning(f"Database configuration '{name}' not found.")
                    return None
            else:
                logger.error(f"Database configuration '{name}' not found.")
                return None
            
        try:
            db_type = config.get("Type")
            if db_type == "PostgreSQL":
                conn = psycopg2.connect(
                    user=config.get("Username"),
                    password=config.get("Password"),
                    host=config.get("Server"),
                    port=config.get("Port", 5432),
                    database=config.get("Database")
                )
            elif db_type == "MSSQL":
                # Prefer pyodbc on Windows for stability
                import platform
                use_pyodbc = platform.system() == "Windows"
                
                if use_pyodbc:
                    try:
                        import pyodbc
                        server = config.get("Server")
                        port = config.get("Port", 1433)
                        database = config.get("Database")
                        user = config.get("Username")
                        password = config.get("Password")
                        
                        # Try commonly installed drivers
                        drivers = [
                            'ODBC Driver 17 for SQL Server',
                            'ODBC Driver 18 for SQL Server',
                            'SQL Server Native Client 11.0',
                            'SQL Server'
                        ]
                        
                        conn = None
                        for driver in drivers:
                            try:
                                conn_str = f'DRIVER={{{driver}}};SERVER={server},{port};DATABASE={database};UID={user};PWD={password};TrustServerCertificate=yes;Connection Timeout=10;'
                                conn = pyodbc.connect(conn_str)
                                if conn: 
                                    logger.info(f"Connected to MSSQL using pyodbc ({driver})")
                                    break
                            except:
                                continue
                        
                        if not conn:
                            # Fallback to pymssql if pyodbc drivers failed
                            import pymssql
                            conn = pymssql.connect(
                                server=server,
                                user=user,
                                password=password,
                                database=database,
                                timeout=10
                            )
                    except ImportError:
                        import pymssql
                        conn = pymssql.connect(
                            server=config.get("Server"),
                            user=config.get("Username"),
                            password=config.get("Password"),
                            database=config.get("Database"),
                            timeout=10
                        )
                else:
                    import pymssql
                    conn = pymssql.connect(
                        server=config.get("Server"),
                        user=config.get("Username"),
                        password=config.get("Password"),
                        database=config.get("Database"),
                        timeout=10
                    )
            else:
                logger.error(f"Unsupported database type: {db_type}")
                return None
                
            self.connections[name] = conn
            logger.info(f"Connected to {name} ({db_type}) successfully.")
            return conn
        except Exception as e:
            logger.error(f"Connection failed for {name}: {e}")
            return None

    def execute_pg_query(self, query: str, params: tuple = None, fetch: bool = True):
        """Execute PostgreSQL query using default DB"""
        conn = self.get_connection(settings.DEFAULT_DB)
        if not conn: return None
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                if fetch:
                    return cur.fetchall()
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"PostgreSQL execution error: {e}")
            conn.rollback()
            return None

    def execute_ms_query(self, query: str, params: tuple = None, fetch: bool = True, db_name: str = "LOGO_Database"):
        """Execute MSSQL query using named DB"""
        conn = self.get_connection(db_name)
        if not conn: return None
        try:
            with conn.cursor(as_dict=True) as cur:
                cur.execute(query, params)
                if fetch:
                    return cur.fetchall()
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"MSSQL ({db_name}) execution error: {e}")
            return None

db_manager = DatabaseManager()

# Synchronous Dependency for FastAPI
def get_db():
    """Synchronous database session dependency"""
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import create_url
    
    # We use the default DB config for this sync dependency
    # This is typically the PostgreSQL Central DB
    from .config import settings
    
    engine = db_manager._get_sync_engine(settings.DEFAULT_DB)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Helper to get sync engine (internal)
def _get_sync_engine(self, name):
    from sqlalchemy import create_engine
    config = next((c for c in settings.DB_CONFIGS if c.get("Name") == name), None)
    if not config:
        # Fallback to defaults (already handled in get_connection, but we need engine here)
        url = settings.CENTRAL_DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
        return create_engine(url)
    
    if config.get("Type") == "PostgreSQL":
        url = f"postgresql://{config['Username']}:{config['Password']}@{config['Server']}:{config.get('Port', 5432)}/{config['Database']}"
        return create_engine(url)
    # Add MSSQL if needed, but for now we focus on PG Central DB
    return create_engine(settings.CENTRAL_DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://"))

DatabaseManager._get_sync_engine = _get_sync_engine
