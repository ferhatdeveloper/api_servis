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
        """Checks if the script is running with Admin privileges with multi-factor probe"""
        # Phase 1: Standard API
        try:
            if ctypes.windll.shell32.IsUserAnAdmin():
                return True
        except:
            pass
            
        # Phase 2: Disk Write Test Fallback (Reliable on Windows)
        # Attempt to write to a protected directory
        try:
            test_file = os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'temp_admin_test.txt')
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
            return True
        except:
            return False

    def check_prerequisites(self):
        """Checks Python version and other system requirements"""
        is_admin = self.check_admin()
        if not is_admin:
             print("\n" + "!"*60)
             print("UYARI: BU PROGRAM YÖNETİCİ HAKLARI OLMADAN ÇALIŞTIRILIYOR!")
             print("Servis kurulumu ve sistem ayarları başarısız olabilir.")
             print("Lütfen terminali 'Yönetici Olarak Çalıştır' komutuyla açın.")
             print("!   " + "!"*56 + "\n")

        checks = {
            "is_admin": is_admin,
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

        # Check Deployment Mode (from start_setup)
        deployment_mode = "1" # Default to Service
        try:
            import sqlite3
            db_path = os.path.join(self.project_dir, "api.db")
            if os.path.exists(db_path):
                conn = sqlite3.connect(db_path)
                row = conn.execute("SELECT value FROM settings WHERE key = 'DeploymentMode'").fetchone()
                if row:
                    deployment_mode = row[0]
                conn.close()
        except: pass

        checks["deployment_mode"] = deployment_mode
        return checks
            
    def setup_postgresql(self, host, port, user, pwd, dbname, app_type="OPS", load_demo=False):
        """Creates the database if it doesn't exist with encoding resilience"""
        import psycopg2
        from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
        
        # Connect to 'postgres' system db with encoding fallbacks
        conn = None
        for enc in ['utf8', 'win1254', 'latin5']:
            try:
                conn = psycopg2.connect(
                    host=host, port=port, user=user, password=pwd, 
                    database="postgres", connect_timeout=3,
                    client_encoding=enc
                )
                break
            except Exception as e:
                if enc == 'latin5': # Last attempt
                    raise Exception(f"Sistem veritabanına bağlanılamadı: {self._extract_error(e)}")
        
        if not conn:
            return

        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        
        # Create DB
        try:
            # Check if exists first to avoid double-create errors
            cur.execute(f"SELECT 1 FROM pg_database WHERE datname='{dbname}'")
            if not cur.fetchone():
                cur.execute(f'CREATE DATABASE "{dbname}"')
        except Exception as e:
            # If it already exists for some reason, just continue
            pass
        finally:
            cur.close()
            conn.close()
        
        # Now run schema migration
        return self.run_schema_migration(host, port, user, pwd, dbname, app_type, load_demo)

    def run_schema_migration(self, host, port, user, pwd, dbname, app_type="OPS", load_demo=False):
        import psycopg2
        import re
        
        conn = psycopg2.connect(host=host, port=port, user=user, password=pwd, database=dbname)
        conn.autocommit = True
        cur = conn.cursor()
        
        logs = []
        
        def safe_read(file_path):
            if not os.path.exists(file_path):
                return None
            
            # Try multiple encodings for Turkish compatibility
            for enc in ['utf-8', 'cp1254', 'iso-8859-9', 'latin-1']:
                try:
                    with open(file_path, "r", encoding=enc) as f:
                        return f.read()
                except UnicodeDecodeError:
                    continue
            
            # Final fallback with replacement
            try:
                with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                    return f.read()
            except:
                return "" # Return empty string instead of None

        def idempotent_execute(sql_content, step_name):
            if not sql_content or not sql_content.strip():
                return
            
            # Split by semicolon followed by whitespace then newline, OR simply semicolon at end of string
            # Also handle just semicolon if on same line (basic split as fallback)
            statements = re.split(r';\s*(?=\r?\n|$)', sql_content)
            
            # If we only got 1 statement and it's long, try a more aggressive split
            if len(statements) <= 1 and len(sql_content) > 1000:
                statements = sql_content.split(';')
            
            success_count = 0
            skip_count = 0
            error_count = 0
            
            print(f"DEBUG: {step_name} SQL dosyasında {len(statements)} ifade bulundu.")
            
            for stmt in statements:
                stmt = stmt.strip()
                if not stmt:
                    continue
                
                # Extract object name for better logging
                obj_match = re.search(r'(?:CREATE|ALTER|DROP|INSERT)\s+(?:TABLE|INDEX|SEQUENCE|VIEW|FUNCTION|EXTENSION|TYPE)?\s*(?:IF NOT EXISTS)?\s*"?([\w-]+)"?', stmt, re.I)
                obj_name = obj_match.group(1) if obj_match else stmt[:30].replace('\n', ' ')

                try:
                    cur.execute(stmt)
                    logs.append(f"  OK: {obj_name} oluşturuldu/güncellendi.")
                    success_count += 1
                except Exception as e:
                    err_msg = self._extract_error(e)
                    pgcode = getattr(e, 'pgcode', None)
                    
                    is_ignorable = False
                    if pgcode in ['42P07', '42710', '23505']:
                        is_ignorable = True
                    elif "zaten mevcut" in err_msg.lower() or "already exists" in err_msg.lower():
                        is_ignorable = True
                    
                    if is_ignorable:
                        logs.append(f"  SKIP: {obj_name} zaten mevcut.")
                        skip_count += 1
                    else:
                        logs.append(f"  HATA: {obj_name} oluşturulamadı: {err_msg}")
                        error_count += 1
            
            logs.append(f"Özet: {success_count} başarılı, {skip_count} atlandı, {error_count} hata.")

        # 1. Base Core Schema
        core_path = os.path.join(self.project_dir, "sql", "schema", "01_core_schema.sql")
        content = safe_read(core_path)
        if content:
            idempotent_execute(content, "Çekirdek (Core)")

        # 2. App Specific Schema
        app_schema_path = os.path.join(self.project_dir, "sql", "apps", app_type, "schema.sql")
        content = safe_read(app_schema_path)
        if content:
            idempotent_execute(content, app_type)
        
        # 3. Optional Demo Data
        if load_demo:
            demo_path = os.path.join(self.project_dir, "sql", "apps", app_type, "demo_data.sql")
            content = safe_read(demo_path)
            if content:
                idempotent_execute(content, f"{app_type} Demo Verileri")
        
        cur.close()
        conn.close()
        return logs

    def _probe_socket(self, host, port):
        """Low-level socket probe to verify reachability without driver crashes"""
        import socket
        try:
            with socket.create_connection((host, port), timeout=2):
                return True
        except:
            return False

    def _extract_error(self, e: Exception) -> str:
        """Absolute error extractor that avoids UnicodeDecodeError at all costs"""
        if not e: return "Bilinmeyen hata"
        
        # 1. Harvest potential binary data BEFORE string conversion
        try:
            potential_bytes = []
            # Check args
            if hasattr(e, 'args') and e.args:
                for arg in e.args:
                    if isinstance(arg, bytes): potential_bytes.append(arg)
            # Check common psycopg2 attributes
            for attr in ['pgerror', 'diag.message_primary']:
                try:
                    val = getattr(e, attr, None)
                    if isinstance(val, bytes): potential_bytes.append(val)
                except: pass
            
            for b_data in potential_bytes:
                for enc in ['cp1254', 'iso-8859-9', 'utf-8', 'latin-1']:
                    try:
                        decoded = b_data.decode(enc).strip()
                        if decoded: return decoded
                    except: continue
        except:
            pass

        # 2. Specialized handling for UnicodeDecodeError itself
        if isinstance(e, UnicodeDecodeError):
            return f"Karakter Çözümleme Hatası ({e.encoding}): Sunucudan gelen mesaj (muhtemelen Türkçe hata mesajı) çözülemedi. Lütfen bilgilerin doğruluğunu kontrol edin."

        # 3. Last stand: try str conversion, fallback to repr
        try:
            return str(e)
        except:
            try:
                return repr(e).encode('ascii', 'xmlcharrefreplace').decode('ascii')
            except:
                return "Bağlantı sırasında açıklanamayan bir hata oluştu."

    def test_db_connection(self, config: dict):
        """Tests connection with ultra-resilient socket-first multi-phase probe"""
        import os
        # Set environment variable to force UTF-8 client side
        os.environ["PGCLIENTENCODING"] = "UTF8"
        
        db_type = config.get("type", "").lower()
        host = config.get("host", "localhost")
        port = int(config.get("port", 0) or (5432 if "postgres" in db_type else 1433))
        username = config.get("username")
        password = config.get("password")
        target_dbname = config.get("database")
        
        if "postgres" in db_type:
            import psycopg2
            
            # PHASE 0: Socket Probe (Safe from encoding errors)
            if not self._probe_socket(host, port):
                # Try 127.0.0.1 if localhost fails
                if host.lower() == "localhost" and self._probe_socket("127.0.0.1", port):
                    host = "127.0.0.1"
                else:
                    return {"success": False, "error": f"Sunucuya hiçbir şekilde ulaşılamadı: {host}:{port} (Bağlantı reddedildi veya zaman aşımı)"}
            
            # PHASE 1: Probe the server using 'postgres' system DB
            probe_conn = None
            probe_err = None
            # Try multiple encodings for the CLIENT
            for enc in ['utf8', 'win1254', 'latin5']:
                try:
                    probe_conn = psycopg2.connect(
                        host=host, port=port, user=username, password=password, 
                        database="postgres", connect_timeout=3,
                        client_encoding=enc
                    )
                    break
                except Exception as e:
                    probe_err = e
                    # If we get a password error, don't keep trying encodings
                    if "password" in self._extract_error(e).lower() or "parola" in self._extract_error(e).lower():
                        break
            
            if not probe_conn:
                return {"success": False, "error": f"Veritabanı sunucusu yanıt verdi ancak bağlanılamadı: {self._extract_error(probe_err)}"}
            
            # PHASE 2: Check Target DB via SQL
            try:
                cur = probe_conn.cursor()
                cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (target_dbname,))
                exists = cur.fetchone()
                cur.close()
                probe_conn.close()
                
                if not exists:
                    return {
                        "success": False, 
                        "db_missing": True, 
                        "error": f"'{target_dbname}' veritabanı sunucuda bulunamadı. Otomatik oluşturulsun mu?"
                    }
                
                # PHASE 3: Connect to Target DB and check for tables
                try:
                    final_conn = psycopg2.connect(
                        host=host, port=port, user=username, password=password, 
                        database=target_dbname, connect_timeout=3
                    )
                    f_cur = final_conn.cursor()
                    f_cur.execute("""
                        SELECT count(*) FROM information_schema.tables 
                        WHERE table_schema = 'public'
                    """)
                    table_count = f_cur.fetchone()[0]
                    f_cur.close()
                    final_conn.close()
                    
                    if table_count == 0:
                        return {
                            "success": False,
                            "db_empty": True,
                            "error": f"'{target_dbname}' veritabanı mevcut ancak boş. Şemalar oluşturulsun mu?"
                        }
                        
                    return {"success": True, "message": f"PostgreSQL Bağlantısı Başarılı! ({table_count} tablo) 🐘✅"}
                except Exception as e:
                    return {"success": False, "error": f"Hedef veritabanına erişim yetkisi yok: {self._extract_error(e)}"}
                    
            except Exception as e:
                if probe_conn: probe_conn.close()
                return {"success": False, "error": f"Metaveri sorgulama hatası: {self._extract_error(e)}"}

        elif "mssql" in db_type or "logo" in db_type:
            try:
                import pymssql
                # Try direct connection first
                try:
                    conn = pymssql.connect(server=host, user=username, password=password, database=target_dbname, timeout=3, charset='UTF-8')
                    conn.close()
                    return {"success": True, "message": "Logo (MSSQL) Bağlantısı Başarılı! 🏢✅"}
                except Exception as e:
                    err_msg = self._extract_error(e)
                    # If it's a login failure or connection failure, we might want to check if the server is even there
                    # Try connecting to 'master' to see if the server/auth is OK but DB is missing
                    try:
                        conn_master = pymssql.connect(server=host, user=username, password=password, database='master', timeout=2, charset='UTF-8')
                        conn_master.close()
                        return {
                            "success": False, 
                            "error": f"MSSQL Sunucusu ve Kimlik Bilgileri Doğru, ancak '{target_dbname}' veritabanı bulunamadı. "
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
                return {"success": False, "error": f"Kritik MSSQL Hatası: {self._extract_error(fatal_e)}"}
        
        return {"success": False, "error": "Bilinmeyen veritabanı tipi"}

    def get_logo_firms(self, config: dict):
        """Fetches firms list from Logo ERP (MSSQL)"""
        try:
            import pymssql
            host = config.get("host")
            user = config.get("username")
            pwd = config.get("password")
            db = config.get("database")
            
            conn = pymssql.connect(server=host, user=user, password=pwd, database=db, timeout=10, charset='cp1256')
            cur = conn.cursor()
            # Fetch firm number (NR) and name (NAME)
            cur.execute("SELECT LTRIM(STR(NR, 3, 0)), NAME FROM L_CAPIFIRM ORDER BY NR")
            firms = [{"id": str(row[0]).zfill(3), "name": str(row[1]).strip()} for row in cur.fetchall()]
            conn.close()
            return {"success": True, "firms": firms}
        except Exception as e:
            return {"success": False, "error": self._extract_error(e)}

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
            return {"success": False, "error": f"Veri aktarım hatası: {self._extract_error(e)}"}

    def get_logo_schema_info(self, ms_config: dict, firm_id: str):
        """Fetches lists of salesmen and warehouses for a specific firm with Arabic support and deduplication"""
        if not firm_id or not str(firm_id).strip():
            return {"success": False, "error": "Logo Firma Numarası belirtilmedi. Lütfen bir firma seçin."}
            
        try:
            import pymssql
            # Use cp1256 for Arabic support. Many Logo installations use this for VARCHAR.
            # If UTF-8 fails to show Arabic, CP1256 is the usual candidate.
            conn = pymssql.connect(
                server=ms_config["host"],
                user=ms_config["username"],
                password=ms_config["password"],
                database=ms_config["database"],
                charset='cp1256',
                timeout=10
            )
            cur = conn.cursor(as_dict=True)
            
            # 1. Fetch Salesmen (Deduplicated via DISTINCT and Python set)
            cur.execute("SELECT DISTINCT CODE, DEFINITION_ FROM LG_SLSMAN WHERE ACTIVE=0 ORDER BY CODE")
            salesmen = []
            seen_sls = set()
            for r in cur.fetchall():
                sid = str(r['CODE'] or "").strip()
                name = str(r['DEFINITION_'] or "").strip()
                if sid and sid != '0' and sid not in seen_sls:
                    salesmen.append({"id": sid, "name": name})
                    seen_sls.add(sid)
            
            # 2. Fetch Warehouses (Deduplicated via DISTINCT and Python set)
            try:
                f_id = int(firm_id)
            except:
                f_id = 0
                
            cur.execute(f"SELECT DISTINCT NR, NAME FROM L_CAPIWHOUSE WHERE FIRMNR={f_id} ORDER BY NR")
            warehouses = []
            seen_wh = set()
            for r in cur.fetchall():
                wid = str(r['NR'] or "").strip()
                name = str(r['NAME'] or "").strip()
                if wid and wid != '0' and wid not in seen_wh:
                    warehouses.append({"id": wid, "name": name})
                    seen_wh.add(wid)
            
            conn.close()
            return {"success": True, "salesmen": salesmen, "warehouses": warehouses}
        except Exception as e:
            # Fallback attempt with UTF-8 if CP1256 fails to connect
            try:
                import pymssql
                conn = pymssql.connect(
                    server=ms_config["host"], user=ms_config["username"], password=ms_config["password"],
                    database=ms_config["database"], charset='UTF-8', timeout=5
                )
                cur = conn.cursor(as_dict=True)
                salesmen = [{"id": str(r['CODE']).strip(), "name": str(r['DEFINITION_']).strip()} for r in cur.fetchall() if str(r['CODE']).strip() != '0']
                cur.execute(f"SELECT DISTINCT NR, NAME FROM L_CAPIWHOUSE WHERE FIRMNR={int(firm_id)} ORDER BY NR")
                warehouses = [{"id": str(r['NR']).strip(), "name": str(r['NAME']).strip()} for r in cur.fetchall() if str(r['NR']).strip() != '0']
                conn.close()
                return {"success": True, "salesmen": salesmen, "warehouses": warehouses}
            except:
                return {"success": False, "error": self._extract_error(e)}

    def generate_credentials_pdf(self, salesmen_data):
        """Generates a PDF report for salesman credentials"""
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.pdfgen import canvas
            from reportlab.lib import colors
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            import io

            # Ensure reports directory exists
            reports_dir = os.path.join(self.project_dir, "reports")
            if not os.path.exists(reports_dir):
                os.makedirs(reports_dir)
            
            pdf_path = os.path.join(reports_dir, "salesman_credentials.pdf")
            
            c = canvas.Canvas(pdf_path, pagesize=A4)
            width, height = A4
            
            # Header
            c.setFont("Helvetica-Bold", 16)
            c.drawCentredString(width/2, height - 50, "EXFIN OPS - Satisci Giris Bilgileri")
            c.setFont("Helvetica", 10)
            c.drawCentredString(width/2, height - 70, f"Olusturulma Tarihi: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Table Header
            y = height - 120
            c.setFont("Helvetica-Bold", 10)
            c.drawString(50, y, "Logo Kod")
            c.drawString(150, y, "Isim")
            c.drawString(350, y, "Kullanici Adi")
            c.drawString(480, y, "Sifre")
            
            c.line(50, y - 5, 550, y - 5)
            
            # Rows
            y -= 25
            c.setFont("Helvetica", 10)
            for s in salesmen_data:
                if y < 100: # New page
                    c.showPage()
                    y = height - 50
                    c.setFont("Helvetica-Bold", 10)
                    c.drawString(50, y, "Logo Kod")
                    c.drawString(150, y, "Isim")
                    c.drawString(350, y, "Kullanici Adi")
                    c.drawString(480, y, "Sifre")
                    c.line(50, y - 5, 550, y - 5)
                    y -= 25
                    c.setFont("Helvetica", 10)
                
                c.drawString(50, y, str(s.get('id', '')))
                c.drawString(150, y, str(s.get('name', ''))[:35])
                c.drawString(350, y, str(s.get('username', '')))
                c.drawString(480, y, str(s.get('password', '')))
                y -= 20
            
            c.save()
            return "/reports/salesman_credentials.pdf"
        except Exception as e:
            logger.error(f"PDF Generation Error: {e}")
            return None


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
            return {"success": False, "error": f"Aktarım Hatası: {self._extract_error(e)}"}

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

    def install_windows_service(self):
        """Installs and starts the EXFIN API Windows Service"""
        try:
            venv_python = os.path.join(self.project_dir, "venv", "Scripts", "python.exe")
            if not os.path.exists(venv_python):
                venv_python = sys.executable
                
            service_script = os.path.join(self.project_dir, "scripts", "windows_service.py")
            
            # Use subprocess to run service commands
            # Step 1: Remove existing if any
            subprocess.run([venv_python, service_script, "remove"], capture_output=True)
            
            # Step 2: Install
            res = subprocess.run([venv_python, service_script, "--startup", "delayed", "install"], capture_output=True, text=True)
            if res.returncode != 0 and "already exists" not in res.stderr:
                return {"success": False, "error": f"Servis yükleme başarısız: {res.stderr}"}
                
            # Step 3: Start
            subprocess.run([venv_python, service_script, "start"], capture_output=True)
            
            return {"success": True, "message": "Windows Servisi başarıyla kuruldu ve başlatıldı. ✅"}
        except Exception as e:
            return {"success": False, "error": f"Servis kurulumunda kritik hata: {str(e)}"}

    def sync_logo_data_selective(self, pg_config, ms_config, firm_id, salesmen, warehouses):
        """Syncs selected salesmen and warehouses from Logo to PostgreSQL"""
        logs = []
        try:
            import pymssql
            import psycopg2
            from passlib.context import CryptContext
            
            pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
            
            logs.append(f"Logo ERP Bağlantısı kuruluyor ({ms_config['host']})...")
            # MSSQL Connection
            ms_conn = pymssql.connect(
                server=ms_config["host"],
                user=ms_config["username"],
                password=ms_config["password"],
                database=ms_config["database"],
                charset='UTF-8'
            )
            ms_cur = ms_conn.cursor(as_dict=True)
            
            logs.append(f"PostgreSQL Bağlantısı kuruluyor ({pg_config['host']})...")
            # PG Connection
            pg_conn = psycopg2.connect(
                host=pg_config["host"],
                port=pg_config["port"],
                user=pg_config["username"],
                password=pg_config["password"],
                database=pg_config["database"]
            )
            pg_cur = pg_conn.cursor()
            
            # 1. Sync Firm (Enhanced with full details)
            logs.append(f"Firma bilgileri alınıyor (Logo No: {firm_id})...")
            ms_cur.execute(f"SELECT NR, NAME, TAXNR, STREET, CITY FROM L_CAPIFIRM WHERE NR={int(firm_id)}")
            firm = ms_cur.fetchone()
            if not firm:
                return {"success": False, "error": f"Firma {firm_id} bulunamadı", "logs": logs}
            
            # Build address
            address = f"{firm.get('STREET', '')} {firm.get('CITY', '')}".strip()
            
            logs.append(f"Firma kaydediliyor: {firm['NAME']}")
            pg_cur.execute("""
                INSERT INTO companies (logo_nr, code, name, tax_number, address, is_active)
                VALUES (%s, %s, %s, %s, %s, true)
                ON CONFLICT (logo_nr) DO UPDATE 
                SET name=EXCLUDED.name, tax_number=EXCLUDED.tax_number, address=EXCLUDED.address
                RETURNING id
            """, (firm['NR'], str(firm['NR']).zfill(3), firm['NAME'], firm.get('TAXNR'), address))
            company_id = pg_cur.fetchone()[0]

            # Update Active Company Name in api.db (SQLite)
            try:
                import sqlite3
                sqlite_path = os.path.join(self.project_dir, "api.db")
                s_conn = sqlite3.connect(sqlite_path)
                s_conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('ActiveCompanyName', ?)", (firm['NAME'],))
                s_conn.commit()
                s_conn.close()
            except Exception as e:
                logs.append(f"UYARI: SQLite güncellenemedi: {e}")
            
            # 1.5. Sync Periods for this company
            logs.append("Çalışma dönemleri aktarılıyor...")
            ms_cur.execute(f"SELECT NR, BEGDATE, ENDDATE FROM L_CAPIPERIOD WHERE FIRMNR={int(firm_id)} ORDER BY NR")
            periods = ms_cur.fetchall()
            for period in periods:
                period_nr = period['NR']
                period_code = str(period_nr).zfill(2)
                period_name = f"Period {period_code}"
                
                pg_cur.execute("""
                    INSERT INTO periods (company_id, logo_period_nr, code, name, start_date, end_date)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (company_id, logo_period_nr) DO UPDATE
                    SET start_date=EXCLUDED.start_date, end_date=EXCLUDED.end_date
                """, (company_id, period_nr, period_code, period_name, period.get('BEGDATE'), period.get('ENDDATE')))
            logs.append(f"  OK: {len(periods)} dönem aktarıldı.")
            
            # 2. Sync Salesmen
            logs.append(f"{len(salesmen)} Satış elemanı aktarılıyor...")
            user_credentials = []
            for salesman in salesmen:
                salesman_id = salesman['id']
                username = salesman['username']
                password = salesman['password']
                
                # Get salesman details from Logo
                ms_cur.execute(f"""
                    SELECT CODE, DEFINITION_, EMAILADDR 
                    FROM LG_{firm_id}_SLSMAN 
                    WHERE CODE='{salesman_id}' AND ACTIVE=0
                """)
                s = ms_cur.fetchone()
                if not s:
                    logs.append(f"  UYARI: Satış elemanı {salesman_id} Logo'da bulunamadı.")
                    continue
                
                # Insert into salesmen table
                pg_cur.execute("""
                    INSERT INTO salesmen (company_id, logo_code, name, email, is_active)
                    VALUES (%s, %s, %s, %s, true)
                    ON CONFLICT (company_id, logo_code) DO UPDATE 
                    SET name=EXCLUDED.name, email=EXCLUDED.email
                    RETURNING id
                """, (company_id, s['CODE'], s['DEFINITION_'], s.get('EMAILADDR')))
                salesman_db_id = pg_cur.fetchone()[0]
                
                # Create user account
                hashed_password = pwd_context.hash(password)
                pg_cur.execute("""
                    INSERT INTO users (username, password_hash, full_name, email, role, salesman_id, is_active)
                    VALUES (%s, %s, %s, %s, 'salesman', %s, true)
                    ON CONFLICT (username) DO UPDATE 
                    SET password_hash=EXCLUDED.password_hash, salesman_id=EXCLUDED.salesman_id
                    RETURNING id
                """, (username, hashed_password, s['DEFINITION_'], s.get('EMAILADDR'), salesman_db_id))
                
                logs.append(f"  OK: {s['DEFINITION_']} (Kullanıcı: {username})")
                user_credentials.append({
                    'code': s['CODE'],
                    'name': s['DEFINITION_'],
                    'username': username,
                    'password': password
                })
            
            # 3. Sync Warehouses
            logs.append(f"{len(warehouses)} Ambar aktarılıyor...")
            for warehouse_id in warehouses:
                ms_cur.execute(f"""
                    SELECT NR, NAME 
                    FROM L_CAPIWHOUSE 
                    WHERE NR={int(warehouse_id)} AND FIRMNR={int(firm_id)}
                """)
                w = ms_cur.fetchone()
                if not w:
                    logs.append(f"  UYARI: Ambar No {warehouse_id} Logo'da bulunamadı.")
                    continue
                
                pg_cur.execute("""
                    INSERT INTO warehouses (company_id, logo_nr, name, is_active)
                    VALUES (%s, %s, %s, true)
                    ON CONFLICT (company_id, logo_nr) DO UPDATE 
                    SET name=EXCLUDED.name
                """, (company_id, w['NR'], w['NAME']))
                logs.append(f"  OK: {w['NAME']}")
            
            pg_conn.commit()
            pg_cur.close()
            pg_conn.close()
            ms_cur.close()
            ms_conn.close()
            
            # Generate PDF report
            pdf_url = None
            if user_credentials:
                try:
                    logs.append("Kimlik bilgileri PDF raporu oluşturuluyor...")
                    pdf_url = self._generate_credentials_pdf(user_credentials, firm['NAME'])
                except Exception as e:
                    logs.append(f"  HATA: PDF oluşturulamadı: {e}")
            
            return {
                "success": True,
                "message": f"{len(salesmen)} satışçı ve {len(warehouses)} ambar aktarıldı",
                "pdf_url": pdf_url,
                "logs": logs
            }
            
        except Exception as e:
            return {"success": False, "error": self._extract_error(e), "logs": logs}
    
    def _generate_credentials_pdf(self, credentials, firm_name):
        """Generates a PDF report with user credentials"""
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib import colors
            from reportlab.lib.units import cm
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.enums import TA_CENTER
            import datetime
            
            # Create PDF in static folder
            pdf_filename = f"salesman_credentials_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            pdf_path = os.path.join(self.project_dir, "scripts", "web_installer", "static", pdf_filename)
            
            doc = SimpleDocTemplate(pdf_path, pagesize=A4)
            elements = []
            styles = getSampleStyleSheet()
            
            # Title
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=18,
                textColor=colors.HexColor('#1a237e'),
                spaceAfter=30,
                alignment=TA_CENTER
            )
            elements.append(Paragraph(f"EXFIN OPS - Kullanıcı Bilgileri", title_style))
            elements.append(Paragraph(f"Firma: {firm_name}", styles['Normal']))
            elements.append(Spacer(1, 0.5*cm))
            
            # Table
            table_data = [['Kod', 'İsim', 'Kullanıcı Adı', 'Şifre']]
            for cred in credentials:
                table_data.append([
                    cred['code'],
                    cred['name'],
                    cred['username'],
                    cred['password']
                ])
            
            table = Table(table_data, colWidths=[3*cm, 6*cm, 4*cm, 3*cm])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a237e')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            elements.append(table)
            doc.build(elements)
            
            return f"/static/{pdf_filename}"
            
        except Exception as e:
            print(f"PDF generation error: {e}")
            return None
    
    def get_logo_preview(self, ms_config, firm_id, data_type):
        """Preview Logo data before sync"""
        try:
            import pymssql
            
            ms_conn = pymssql.connect(
                server=ms_config["host"],
                user=ms_config["username"],
                password=ms_config["password"],
                database=ms_config["database"],
                charset='UTF-8'
            )
            ms_cur = ms_conn.cursor(as_dict=True)
            
            results = []
            
            if data_type == "companies":
                ms_cur.execute("SELECT TOP 50 NR, NAME, TAXNR FROM L_CAPIFIRM ORDER BY NR")
                for row in ms_cur.fetchall():
                    results.append({
                        "nr": row['NR'],
                        "name": row.get('NAME'),
                        "tax_nr": row.get('TAXNR')
                    })
            
            elif data_type == "salesmen":
                ms_cur.execute(f"SELECT TOP 50 CODE, DEFINITION_, EMAILADDR FROM LG_{firm_id}_SLSMAN WHERE ACTIVE=0 ORDER BY CODE")
                for row in ms_cur.fetchall():
                    results.append({
                        "code": row['CODE'],
                        "name": row.get('DEFINITION_'),
                        "email": row.get('EMAILADDR')
                    })
            
            elif data_type == "warehouses":
                ms_cur.execute(f"SELECT TOP 50 NR, NAME FROM L_CAPIWHOUSE WHERE FIRMNR={int(firm_id)} ORDER BY NR")
                for row in ms_cur.fetchall():
                    results.append({
                        "nr": row['NR'],
                        "name": row.get('NAME')
                    })
            
            ms_conn.close()
            return {"success": True, "data": results}
            
        except Exception as e:
            return {"success": False, "error": self._extract_error(e)}
    
    def save_backup_config(self, config):
        """Save backup configuration to backup_config.json"""
        try:
            import json
            
            backup_config = {
                "backup_dir": config.get("backup_dir"),
                "backup_interval": config.get("backup_interval", "off"),
                "backup_time": config.get("backup_time", "23:00"),
                "backup_hours": config.get("backup_hours", "1"),
                "backup_days": config.get("backup_days", [])
            }
            
            config_path = os.path.join(self.project_dir, "backup_config.json")
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(backup_config, f, indent=4)
            
            return {"success": True, "message": "Backup configuration saved"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def generate_ssl_certificate(self):
        """Generate self-signed SSL certificate"""
        try:
            cert_script = os.path.join(self.project_dir, "scripts", "generate_cert.py")
            
            if not os.path.exists(cert_script):
                return {"success": False, "error": "generate_cert.py not found"}
            
            import sys
            sys.path.insert(0, os.path.join(self.project_dir, "scripts"))
            import generate_cert
            
            cert_file, key_file = generate_cert.generate_self_signed_cert()
            
            env_path = os.path.join(self.project_dir, ".env")
            env_content = ""
            
            if os.path.exists(env_path):
                with open(env_path, "r") as f:
                    env_content = f.read()
            
            lines = env_content.split("\n")
            lines = [l for l in lines if not l.startswith("SSL_CERT_FILE=") and not l.startswith("SSL_KEY_FILE=") and not l.startswith("USE_HTTPS=")]
            
            lines.append(f"SSL_CERT_FILE={cert_file}")
            lines.append(f"SSL_KEY_FILE={key_file}")
            lines.append("USE_HTTPS=True")
            
            with open(env_path, "w") as f:
                f.write("\n".join(lines))
            
            return {
                "success": True,
                "cert_file": cert_file,
                "key_file": key_file,
                "message": "SSL certificate generated and .env updated"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}


installer = InstallerService()


