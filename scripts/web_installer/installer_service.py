import os
import sys
import subprocess
import ctypes
import shutil
import logging

logger = logging.getLogger("InstallerService")

class InstallerService:
    def __init__(self):
        self.project_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
    def check_admin(self) -> bool:
        """Checks if the script is running with Admin privileges"""
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False

    def check_prerequisites(self):
        """Checks Python version and other system requirements"""
        checks = {
            "is_admin": self.check_admin(),
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}",
            "ram_gb": 0 # Placeholder
        }
        
        # Check RAM
        try:
            import psutil
            mem = psutil.virtual_memory()
            checks["ram_gb"] = round(mem.total / (1024**3), 2)
        except ImportError:
            checks["ram_gb"] = 0
            checks["ram_warning"] = "psutil not installed"
        except Exception:
            checks["ram_gb"] = 0

        return checks
            
    def setup_postgresql(self, host, port, user, pwd, dbname, app_type="OPS", load_demo=False):
        """Creates the database if it doesn't exist"""
        import psycopg2
        from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
        
        # Connect to 'postgres' system db
        conn = psycopg2.connect(host=host, port=port, user=user, password=pwd, database="postgres", client_encoding='utf8')
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        
        # Create DB
        cur.execute(f'CREATE DATABASE "{dbname}"')
        cur.close()
        conn.close()
        
        # Now run schema migration
        self.run_schema_migration(host, port, user, pwd, dbname, app_type, load_demo)

    def run_schema_migration(self, host, port, user, pwd, dbname, app_type="OPS", load_demo=False):
        import psycopg2
        conn = psycopg2.connect(host=host, port=port, user=user, password=pwd, database=dbname)
        conn.autocommit = True
        cur = conn.cursor()
        
        def safe_read(file_path):
            if not os.path.exists(file_path):
                return None
            # Try UTF-8 with replacement for resilience
            try:
                with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                    return f.read()
            except:
                # Fallback to CP1254 (Turkish Windows) if UTF-8 fails hard
                with open(file_path, "r", encoding="cp1254", errors="replace") as f:
                    return f.read()

        # 1. Base Core Schema (Legacy/Default)
        core_path = os.path.join(self.project_dir, "sql", "schema", "01_core_schema.sql")
        content = safe_read(core_path)
        if content:
            cur.execute(content)

        # 2. App Specific Schema
        app_schema_path = os.path.join(self.project_dir, "sql", "apps", app_type, "schema.sql")
        content = safe_read(app_schema_path)
        if content:
            cur.execute(content)
        
        # 3. Optional Demo Data
        if load_demo:
            demo_path = os.path.join(self.project_dir, "sql", "apps", app_type, "demo_data.sql")
            content = safe_read(demo_path)
            if content:
                # Some demo data files might be large, execute in chunks if needed
                cur.execute(content)
        
        cur.close()
        conn.close()

    def test_db_connection(self, config: dict):
        """Tests connection to PostgreSQL or MSSQL"""
        db_type = config.get("type", "").lower()
        host = config.get("host")
        port = int(config.get("port", 0))
        user = config.get("username")
        pwd = config.get("password")
        dbname = config.get("database")
        app_type = config.get("app_type", "OPS")
        load_demo = config.get("load_demo", False)

        if "postgres" in db_type:
                import psycopg2
                conn = psycopg2.connect(host=host, port=port, user=user, password=pwd, database=dbname, connect_timeout=3, client_encoding='utf8')
                conn.close()
                return {"success": True, "message": "PostgreSQL Bağlantısı Başarılı! 🐘✅"}
            except Exception as e:
                # Robust error message handling for encoding issues
                try:
                    err_msg = str(e)
                except UnicodeDecodeError:
                    # Fallback for binary error messages sometimes returned by drivers in different locales
                    err_msg = repr(e)
                
                if getattr(e, 'pgcode', None) == '3D000' or ("database" in err_msg.lower() and "does not exist" in err_msg.lower()):
                    try:
                        self.setup_postgresql(host, port, user, pwd, dbname, app_type, load_demo)
                        return {"success": True, "message": f"'{dbname}' veritabanı ve '{app_type}' şeması başarıyla oluşturuldu! ✅"}
                    except Exception as create_err:
                        return {"success": False, "error": f"Veritabanı oluşturulamadı: {str(create_err)}"}
                return {"success": False, "error": str(e)}

        elif "mssql" in db_type or "logo" in db_type:
            try:
                import pymssql
                # Try direct connection first
                try:
                    conn = pymssql.connect(server=host, user=user, password=pwd, database=dbname, timeout=3, charset='UTF-8')
                    conn.close()
                    return {"success": True, "message": "Logo (MSSQL) Bağlantısı Başarılı! 🏢✅"}
                except Exception as e:
                    err_msg = str(e)
                    # If it's a login failure or connection failure, we might want to check if the server is even there
                    # Try connecting to 'master' to see if the server/auth is OK but DB is missing
                    try:
                        conn_master = pymssql.connect(server=host, user=user, password=pwd, database='master', timeout=2, charset='UTF-8')
                        conn_master.close()
                        return {
                            "success": False, 
                            "error": f"MSSQL Sunucusu ve Kimlik Bilgileri Doğru, ancak '{dbname}' veritabanı bulunamadı. "
                                     "Lütfen veritabanı adını kontrol edin veya veritabanını oluşturun."
                        }
                    except Exception as master_e:
                        # If even master fails, it's likely auth or connection issue
                        if "18456" in err_msg:
                            return {
                                "success": False, 
                                "error": "MSSQL Login Hatası (18456): Kullanıcı adı veya şifre hatalı olabilir. "
                                         "Ayrıca SQL Server'ın 'SQL Server and Windows Authentication mode'u desteklediğinden emin olun."
                            }
                        elif "20002" in err_msg or "connection failed" in err_msg.lower():
                            return {
                                "success": False,
                                "error": f"MSSQL Bağlantı Hatası: Sunucuya ulaşılamıyor ({host}). "
                                         "SQL Server'ın çalıştığinden ve TCP/IP protokolünün aktif olduğundan emin olun."
                            }
                        return {"success": False, "error": f"MSSQL Hatası: {err_msg}"}
            except Exception as fatal_e:
                return {"success": False, "error": f"Kritik MSSQL Hatası: {str(fatal_e)}"}
        
        return {"success": False, "error": "Bilinmeyen veritabanı tipi"}

    def get_logo_firms(self, config: dict):
        """Fetches firms list from Logo ERP (MSSQL)"""
        try:
            import pymssql
            host = config.get("host")
            user = config.get("username")
            pwd = config.get("password")
            db = config.get("database")
            
            conn = pymssql.connect(server=host, user=user, password=pwd, database=db, timeout=5, charset='UTF-8')
            cur = conn.cursor()
            # Fetch firm number (NR) and name (NAME)
            cur.execute("SELECT LTRIM(STR(NR, 3, 0)), NAME FROM L_CAPIFIRM ORDER BY NR")
            firms = [{"id": str(row[0]).zfill(3), "name": row[1]} for row in cur.fetchall()]
            conn.close()
            return {"success": True, "firms": firms}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def sync_logo_data(self, pg_config: dict, ms_config: dict, selected_firm: str):
        """Transfers basic master data from Logo ERP to PostgreSQL"""
        try:
            import pymssql
            import psycopg2
            
            # MSSQL Connection
            ms_conn = pymssql.connect(
                server=ms_config["host"],
                user=ms_config["username"],
                password=ms_config["password"],
                database=ms_config["database"],
                charset='UTF-8'
            )
            ms_cur = ms_conn.cursor(as_dict=True)
            
            # PG Connection
            pg_conn = psycopg2.connect(
                host=pg_config["host"],
                port=pg_config["port"],
                user=pg_config["username"],
                password=pg_config["password"],
                database=pg_config["database"]
            )
            pg_cur = pg_conn.cursor()
            
            # 1. Sync Selected Firm
            ms_cur.execute(f"SELECT NR, NAME FROM L_CAPIFIRM WHERE NR={int(selected_firm)}")
            firm = ms_cur.fetchone()
            if firm:
                nr = firm['NR']
                name = firm['NAME']
                pg_cur.execute("""
                    INSERT INTO companies (logo_nr, name, is_active)
                    VALUES (%s, %s, true)
                    ON CONFLICT (logo_nr) DO UPDATE SET name=EXCLUDED.name
                    RETURNING id
                """, (nr, name))
                company_id = pg_cur.fetchone()[0]
                
                # Sync Periods
                ms_cur.execute(f"SELECT NR, BEGDATE, ENDDATE FROM L_CAPIPERIOD WHERE FIRMNR={nr} ORDER BY NR")
                for p in ms_cur.fetchall():
                    pnr = p['NR']
                    pg_cur.execute("""
                        INSERT INTO periods (company_id, logo_period_nr, code, name, start_date, end_date)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT DO NOTHING
                    """, (company_id, pnr, str(pnr).zfill(2), f"Period {pnr}", p['BEGDATE'], p['ENDDATE']))

            # 2. Sync Salesmen (LG_SLSMAN)
            ms_cur.execute("SELECT CODE, DEFINITION_, EMAILADDR FROM LG_SLSMAN WHERE ACTIVE=0")
            for s in ms_cur.fetchall():
                code = s['CODE']
                name = s['DEFINITION_']
                email = s['EMAILADDR'] or f"{code}@example.com"
                pg_cur.execute("""
                    INSERT INTO salesmen (company_id, code, name, email)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                """, (company_id, code, name, email))

            # 3. Sync Warehouses (L_CAPIWHOUSE)
            ms_cur.execute(f"SELECT NR, NAME FROM L_CAPIWHOUSE WHERE FIRMNR={int(selected_firm)} ORDER BY NR")
            for w in ms_cur.fetchall():
                nr = w['NR']
                name = w['NAME']
                pg_cur.execute("""
                    INSERT INTO warehouses (company_id, code, name, logo_ref)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                """, (company_id, str(nr).zfill(2), name, nr))

            pg_conn.commit()
            ms_conn.close()
            pg_conn.close()
            return {"success": True, "message": "Logo verileri başarıyla aktarıldı."}
        except Exception as e:
            return {"success": False, "error": f"Veri aktarım hatası: {str(e)}"}

    def get_logo_schema_info(self, ms_config: dict, firm_id: str):
        """Fetches lists of salesmen and warehouses for a specific firm"""
        try:
            import pymssql
            conn = pymssql.connect(
                server=ms_config["host"],
                user=ms_config["username"],
                password=ms_config["password"],
                database=ms_config["database"],
                charset='UTF-8'
            )
            cur = conn.cursor(as_dict=True)
            
            # 1. Fetch Salesmen
            cur.execute("SELECT CODE, DEFINITION_ FROM LG_SLSMAN WHERE ACTIVE=0 ORDER BY CODE")
            salesmen = [{"id": r['CODE'], "name": r['DEFINITION_']} for r in cur.fetchall()]
            
            # 2. Fetch Warehouses for Firm
            cur.execute(f"SELECT NR, NAME FROM L_CAPIWHOUSE WHERE FIRMNR={int(firm_id)} ORDER BY NR")
            warehouses = [{"id": r['NR'], "name": r['NAME']} for r in cur.fetchall()]
            
            conn.close()
            return {"success": True, "salesmen": salesmen, "warehouses": warehouses}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def sync_logo_data_selective(self, pg_config: dict, ms_config: dict, firm_id: str, salesmen_ids: list, warehouse_ids: list):
        """Transfers EXPLICITLY SELECTED master data from Logo to Postgres"""
        try:
            import pymssql
            import psycopg2
            
            # MSSQL Connection
            ms_conn = pymssql.connect(
                server=ms_config["host"], user=ms_config["username"], password=ms_config["password"],
                database=ms_config["database"], charset='UTF-8'
            )
            ms_cur = ms_conn.cursor(as_dict=True)
            
            # PG Connection
            pg_conn = psycopg2.connect(
                host=pg_config["host"], port=pg_config["port"], user=pg_config["username"],
                password=pg_config["password"], database=pg_config["database"]
            )
            pg_cur = pg_conn.cursor()
            
            # 1. Always Sync Selected Firm and Periods first (Basic Core)
            ms_cur.execute(f"SELECT NR, NAME FROM L_CAPIFIRM WHERE NR={int(firm_id)}")
            firm = ms_cur.fetchone()
            if not firm: return {"success": False, "error": "Firma bulunamadı."}
            
            pg_cur.execute("INSERT INTO companies (logo_nr, name, is_active) VALUES (%s, %s, true) ON CONFLICT (logo_nr) DO UPDATE SET name=EXCLUDED.name RETURNING id", (firm['NR'], firm['NAME']))
            company_id = pg_cur.fetchone()[0]
            
            # 2. Selective Salesmen
            if salesmen_ids:
                placeholders = ', '.join(['%s'] * len(salesmen_ids))
                ms_cur.execute(f"SELECT CODE, DEFINITION_, EMAILADDR FROM LG_SLSMAN WHERE CODE IN ({placeholders})", tuple(salesmen_ids))
                for s in ms_cur.fetchall():
                    pg_cur.execute("INSERT INTO salesmen (company_id, code, name, email) VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING", 
                                   (company_id, s['CODE'], s['DEFINITION_'], s['EMAILADDR'] or f"{s['CODE']}@example.com"))

            # 3. Selective Warehouses
            if warehouse_ids:
                placeholders = ', '.join(['%d'] * len(warehouse_ids))
                ms_cur.execute(f"SELECT NR, NAME FROM L_CAPIWHOUSE WHERE FIRMNR={int(firm_id)} AND NR IN ({placeholders})", tuple(warehouse_ids))
                for w in ms_cur.fetchall():
                    pg_cur.execute("INSERT INTO warehouses (company_id, code, name, logo_ref) VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING", 
                                   (company_id, str(w['NR']).zfill(2), w['NAME'], w['NR']))

            pg_conn.commit()
            ms_conn.close()
            pg_conn.close()
            return {"success": True, "message": "Seçili veriler başarıyla aktarıldı."}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _get_db_connection(self, conn_str: str):
        """Helper to create a connection from a URL-style string"""
        try:
            from sqlalchemy import create_engine
            # We use sqlalchemy for connection parsing but raw connections for performance/control
            engine = create_engine(conn_str)
            url = engine.url
            
            if url.drivername.startswith("postgresql") or url.drivername.startswith("postgres"):
                import psycopg2
                return psycopg2.connect(
                    host=url.host, port=url.port, user=url.username, 
                    password=url.password, database=url.database, 
                    client_encoding='utf8'
                ), "postgres"
            elif url.drivername.startswith("mysql"):
                import pymysql
                return pymysql.connect(
                    host=url.host, port=url.port or 3306, user=url.username, 
                    password=url.password, database=url.database,
                    charset='utf8mb4'
                ), "mysql"
            elif url.drivername.startswith("mssql"):
                import pymssql
                return pymssql.connect(
                    server=url.host, port=url.port or 1433, user=url.username, 
                    password=url.password, database=url.database,
                    charset='UTF-8'
                ), "mssql"
            return None, None
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            raise

    def analyze_remote_db(self, remote_conn_str: str, local_config: dict):
        """Universal introspection for Remote DB"""
        try:
            remote_conn, dialect = self._get_db_connection(remote_conn_str)
            remote_cur = remote_conn.cursor()
            
            # Universal Schema Query (Common to PSQL, MySQL, MSSQL via information_schema)
            query = """
                SELECT table_name, column_name, data_type 
                FROM information_schema.columns 
                WHERE table_schema NOT IN ('information_schema', 'performance_schema', 'sys', 'mysql')
                AND table_schema = (SELECT CASE 
                    WHEN %s = 'postgres' THEN 'public' 
                    WHEN %s = 'mysql' THEN DATABASE()
                    ELSE 'dbo' END)
                ORDER BY table_name, ordinal_position
            """
            
            # Adjust query based on dialect if needed
            if dialect == "postgres":
                remote_cur.execute(query, ("postgres", "postgres"))
            elif dialect == "mysql":
                remote_cur.execute("SELECT table_name, column_name, data_type FROM information_schema.columns WHERE table_schema = DATABASE() ORDER BY table_name, ordinal_position")
            elif dialect == "mssql":
                remote_cur.execute("SELECT table_name, column_name, data_type FROM information_schema.columns WHERE table_schema = 'dbo' ORDER BY table_name, ordinal_position")

            remote_schema = {}
            for row in remote_cur.fetchall():
                t, c, d = row
                if t not in remote_schema: remote_schema[t] = []
                remote_schema[t].append({"name": c, "type": d})
            
            # Build Local Conn Str dynamically
            db_type = local_config.get("type", "PostgreSQL").lower()
            if "mssql" in db_type:
                local_conn_str = f"mssql+pymssql://{local_config['username']}:{local_config['password']}@{local_config['host']}:{local_config.get('port', 1433)}/{local_config['database']}"
            else:
                local_conn_str = f"postgresql://{local_config['username']}:{local_config['password']}@{local_config['host']}:{local_config['port']}/{local_config['database']}"
            
            local_conn, _ = self._get_db_connection(local_conn_str)
            local_cur = local_conn.cursor()
            local_cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
            local_tables = [r[0] for r in local_cur.fetchall()]
            
            analysis = {
                "missing_tables": [t for t in remote_schema.keys() if t not in local_tables],
                "tables_to_sync": list(remote_schema.keys()),
                "source_dialect": dialect
            }
            
            remote_conn.close()
            local_conn.close()
            return {"success": True, "tables": list(remote_schema.keys()), "analysis": analysis}
        except Exception as e:
            return {"success": False, "error": f"Analiz Hatası: {str(e)}"}

    def migrate_cloud_data(self, remote_conn_str: str, local_config: dict, selected_tables: list):
        """Universal migration and type mapping"""
        try:
            remote_conn, source_dialect = self._get_db_connection(remote_conn_str)
            remote_cur = remote_conn.cursor()
            
            # Build Local Conn Str dynamically
            db_type = local_config.get("type", "PostgreSQL").lower()
            if "mssql" in db_type:
                local_conn_str = f"mssql+pymssql://{local_config['username']}:{local_config['password']}@{local_config['host']}:{local_config.get('port', 1433)}/{local_config['database']}"
            else:
                local_conn_str = f"postgresql://{local_config['username']}:{local_config['password']}@{local_config['host']}:{local_config['port']}/{local_config['database']}"
            
            local_conn, target_dialect = self._get_db_connection(local_conn_str)
            local_cur = local_conn.cursor()
            
            # Basic Type Mapper (Source -> Postgres)
            type_map = {
                "int": "INTEGER", "bigint": "BIGINT", "nvarchar": "TEXT", "varchar": "TEXT", 
                "text": "TEXT", "datetime": "TIMESTAMP", "timestamp": "TIMESTAMP", 
                "decimal": "NUMERIC", "float": "DOUBLE PRECISION", "bit": "BOOLEAN",
                "tinyint": "SMALLINT", "longtext": "TEXT", "mediumtext": "TEXT"
            }

            for table in selected_tables:
                # 1. Fetch Remote Metadata
                if source_dialect == "mysql":
                    remote_cur.execute(f"SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_name='{table}' AND table_schema = DATABASE()")
                else:
                    remote_cur.execute(f"SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_name='{table}'")
                
                cols = remote_cur.fetchall()
                col_defs = []
                for c in cols:
                    name, dtype, nullable = c
                    pg_type = type_map.get(dtype.lower(), "TEXT") # Default to text if unknown
                    col_defs.append(f'"{name}" {pg_type} {"NULL" if nullable == "YES" else "NOT NULL"}')
                
                # 2. Apply DDL (Local is Postgres)
                local_cur.execute(f'CREATE TABLE IF NOT EXISTS "{table}" ({", ".join(col_defs)})')
                
                # 3. Data Transfer
                local_cur.execute(f'TRUNCATE TABLE "{table}"')
                remote_cur.execute(f'SELECT * FROM "{table}"')
                
                while True:
                    batch = remote_cur.fetchmany(1000)
                    if not batch: break
                    
                    placeholders = ", ".join(["%s"] * len(batch[0]))
                    insert_query = f'INSERT INTO "{table}" VALUES ({placeholders})'
                    local_cur.executemany(insert_query, batch)
            
            local_conn.commit()
            remote_conn.close()
            local_conn.close()
            return {"success": True, "message": f"{len(selected_tables)} tablo başarıyla aktarıldı."}
        except Exception as e:
            return {"success": False, "error": f"Aktarım Hatası: {str(e)}"}

    def get_supabase_projects(self, token: str):
        """Fetches list of projects from Supabase Management API"""
        try:
            import requests
            headers = {"Authorization": f"Bearer {token}"}
            res = requests.get("https://api.supabase.com/v1/projects", headers=headers, timeout=5)
            if res.status_code == 200:
                projects = res.json()
                return {"success": True, "projects": projects}
            else:
                return {"success": False, "error": f"Supabase API Hatası ({res.status_code}): {res.text}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def create_shortcuts(self):
        """Creates desktop shortcut for the Tray App"""
        try:
            import winshell
            from win32com.client import Dispatch
            import os

            desktop = winshell.desktop()
            path = os.path.join(desktop, "EXFIN Control Panel.lnk")
            target = os.path.join(self.project_dir, "venv", "Scripts", "python.exe")
            script = os.path.join(self.project_dir, "tray_app.py")
            
            shell = Dispatch('WScript.Shell')
            shortcut = shell.CreateShortCut(path)
            shortcut.Targetpath = target
            shortcut.Arguments = f'"{script}"'
            shortcut.WorkingDirectory = self.project_dir
            shortcut.IconLocation = os.path.join(self.project_dir, "modern_database_icon_v2.png")
            shortcut.save()
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def save_config(self, config: dict):
        """Saves configuration to api.db"""
        try:
            import sqlite3
            db_path = os.path.join(self.project_dir, "api.db")
            conn = sqlite3.connect(db_path)
            cur = conn.cursor()
            
            # Create Schema
            cur.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)")
            cur.execute('''CREATE TABLE IF NOT EXISTS db_connections 
                            (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                             name TEXT UNIQUE, 
                             type TEXT, 
                             host TEXT, 
                             port INTEGER, 
                             database TEXT, 
                             username TEXT, 
                             password TEXT)''')

            # 1. Save Global Settings
            settings = config.get("settings", {})
            for k, v in settings.items():
                cur.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (k, str(v)))

            # 2. Save Connections
            connections = config.get("connections", [])
            for conn_data in connections:
                 cur.execute("""
                    INSERT OR REPLACE INTO db_connections (id, name, type, host, port, database, username, password) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    conn_data.get("id"),
                    conn_data.get("name"),
                    conn_data.get("type"),
                    conn_data.get("host"),
                    conn_data.get("port"),
                    conn_data.get("database"),
                    conn_data.get("username"),
                    conn_data.get("password")
                ))

            conn.commit()
            conn.close()
            
            # 3. Create .env file for legacy support / frameworks
            env_path = os.path.join(self.project_dir, ".env")
            pg = next((c for c in connections if c["type"] == "PostgreSQL"), None)
            if pg:
                with open(env_path, "w", encoding="utf-8") as f:
                    f.write(f"DATABASE_URL=postgresql://{pg['username']}:{pg['password']}@{pg['host']}:{pg['port']}/{pg['database']}\n")
                    f.write(f"API_PORT={settings.get('Api_Port', '8000')}\n")
            
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

installer = InstallerService()

