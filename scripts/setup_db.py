import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv

# Load params from .env
load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "admin")
TARGET_DB = os.getenv("DB_NAME", "EXFINOPS")

def run_sql_file(cursor, filename):
    with open(filename, 'r', encoding='utf-8', errors='replace') as f:
        sql = f.read()
        # MASTER.sql contains connection commands like \c which pyscopg2 doesn't understand.
        # We need to strip those specific psql commands or just execute the SQL parts.
        # Since we are already connected to the target DB, we can ignore \c commands.
        
        # Split by statements is safer but complex. 
        # For this specific case, we'll try execute current logic.
        # However, psycopg2 cannot handle "\c" meta-commands.
        # We should purely run SQL statements.
        
        # Let's remove lines starting with \
        clean_lines = [line for line in sql.splitlines() if not line.strip().startswith('\\')]
        clean_sql = '\n'.join(clean_lines)
        
        cursor.execute(clean_sql)

def setup():
    print(f"Connecting to PostgreSQL at {DB_HOST} as {DB_USER}...")
    
    # 1. Connect to 'postgres' DB to create new DB
    try:
        conn = psycopg2.connect(
            dbname="postgres", user=DB_USER, password=DB_PASSWORD, host=DB_HOST
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        
        # Check if DB exists
        cur.execute(f"SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{TARGET_DB}'")
        exists = cur.fetchone()
        
        if exists:
            print(f"Database {TARGET_DB} already exists. Dropping it to start fresh...")
            # Terminate connections first
            cur.execute(f"""
                SELECT pg_terminate_backend(pg_stat_activity.pid)
                FROM pg_stat_activity
                WHERE pg_stat_activity.datname = '{TARGET_DB}'
                AND pid <> pg_backend_pid();
            """)
            cur.execute(f"DROP DATABASE \"{TARGET_DB}\"")
            print("Dropped.")
        
        print(f"Creating database {TARGET_DB}...")
        cur.execute(f"CREATE DATABASE \"{TARGET_DB}\"")
        print("Created.")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"Error creating database: {e}")
        return

    # 2. Connect to the new DB and run schema
    print(f"Connecting to {TARGET_DB} to run definition...")
    try:
        conn = psycopg2.connect(
            dbname=TARGET_DB, user=DB_USER, password=DB_PASSWORD, host=DB_HOST
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        master_path = os.path.join(root_dir, "sql", "setup", "01_master_setup.sql")
        print(f"Executing {master_path} content...")
        run_sql_file(cur, master_path)
        
        print("Setup completed successfully! 🚀")
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"Error executing schema: {e}")

if __name__ == "__main__":
    setup()
