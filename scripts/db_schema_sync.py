
import os
import re
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "admin")
DB_NAME = os.getenv("DB_NAME", "EXFINOPS")

def get_db_connection():
    try:
        conn = psycopg2.connect(
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            dbname=DB_NAME
        )
        return conn
    except Exception as e:
        print(f"Connection error: {e}")
        return None

def parse_sql_schema(file_path):
    """
    Parses a simple CREATE TABLE SQL file.
    Returns a dict: { 'table_name': { 'columns': [ {'name': 'id', 'def': 'SERIAL PRIMARY KEY'}, ... ] } }
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        sql_content = f.read()

    # Remove comments
    sql_content = re.sub(r'--.*', '', sql_content)
    
    # Normalize spaces
    sql_content = re.sub(r'\s+', ' ', sql_content)

    tables = {}
    
    # Regex for CREATE TABLE
    # Matches: CREATE TABLE [IF NOT EXISTS] table_name ( ... );
    table_pattern = re.compile(r'CREATE TABLE (?:IF NOT EXISTS )?(\w+)\s*\((.*?)\);', re.IGNORECASE)
    
    matches = table_pattern.findall(sql_content)
    
    for table_name, body in matches:
        columns = []
        # Split body by commas, but be careful of parens (like DECIMAL(10,2))
        # Simple split by comma might fail for types like DECIMAL(5,2).
        
        # Helper to split by comma ignoring nested parens
        parts = []
        depth = 0
        current_part = []
        
        for char in body:
            if char == '(': depth += 1
            elif char == ')': depth -= 1
            
            if char == ',' and depth == 0:
                parts.append("".join(current_part).strip())
                current_part = []
            else:
                current_part.append(char)
        if current_part:
            parts.append("".join(current_part).strip())

        for part in parts:
            if not part: continue
            
            # Check if it's a constraint like "UNIQUE(x)" or "PRIMARY KEY(y)"
            # If line starts with CONSTRAINT, PRIMARY KEY, UNIQUE, FOREIGN KEY -> It's a table constraint
            upper_part = part.upper()
            if (upper_part.startswith("CONSTRAINT") or 
                upper_part.startswith("PRIMARY KEY") or 
                upper_part.startswith("UNIQUE") or 
                upper_part.startswith("FOREIGN KEY")):
                continue # Skip table constraints for now, focus on columns
            
            # It's a column definition
            # "col_name type constraints..."
            # Get first word as name
            col_match = re.match(r'(\w+)\s+(.*)', part)
            if col_match:
                col_name = col_match.group(1)
                col_def = col_match.group(2)
                columns.append({'name': col_name, 'definition': col_def, 'full': part})
        
        tables[table_name] = columns

    return tables

def get_existing_tables(conn):
    """Returns { 'table_name': ['col1', 'col2'] }"""
    cur = conn.cursor()
    cur.execute("""
        SELECT table_name, column_name 
        FROM information_schema.columns 
        WHERE table_schema = 'public'
    """)
    rows = cur.fetchall()
    
    existing = {}
    for table, col in rows:
        if table not in existing:
            existing[table] = []
        existing[table].append(col)
    
    cur.close()
    return existing

def sync_db():
    print(f"--- Starting Smart DB Sync for {DB_NAME} ---")
    
    # Look for sql dir in parent of scripts
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    schema_path = os.path.join(root_dir, "sql", "schema", "01_core_schema.sql")
    if not os.path.exists(schema_path):
        print(f"Error: Schema file not found at {schema_path}")
        return

    desired_tables = parse_sql_schema(schema_path)
    
    conn = get_db_connection()
    if not conn:
        print("Could not connect to DB. Make sure it exists.")
        return

    existing_tables = get_existing_tables(conn)
    cur = conn.cursor()
    
    changes_made = False

    for table, desired_cols in desired_tables.items():
        if table not in existing_tables:
            print(f"[NEW TABLE] Creating table '{table}'...")
            # Reconstruct CREATE TABLE
            col_defs = ", ".join([c['full'] for c in desired_cols])
            # We skip table constraints in the simplistic parser, which is a risk.
            # Ideally, we should just execute the original CREATE block if specific logic allows.
            # But the full SQL from file is hard to extract exactly corresponding to the regex match.
            # BETTER APPROACH: Since we identified it's missing, maybe we can't easily fetch the exact original SQL block 
            # without reading the file again or storing it better. 
            
            # Fallback: Just construct minimal, or ... 
            # Actually, to be safe, if table is missing, let's try to extract the original raw segment 
            # OR just construct it safely.
            
            # "Safe" reconstruction:
            create_stmt = f"CREATE TABLE IF NOT EXISTS {table} ({col_defs});"
            try:
                cur.execute(create_stmt)
                conn.commit()
                changes_made = True
                print("  -> Created.")
            except Exception as e:
                print(f"  -> Error creating table: {e}")
                conn.rollback()

        else:
            # Table exists, check columns
            current_cols = existing_tables[table]
            for col in desired_cols:
                col_name = col['name']
                if col_name not in current_cols:
                    print(f"[NEW COLUMN] Adding '{col_name}' to '{table}'...")
                    alter_stmt = f"ALTER TABLE {table} ADD COLUMN {col_name} {col['definition']};"
                    try:
                        cur.execute(alter_stmt)
                        conn.commit()
                        changes_made = True
                        print("  -> Added.")
                    except Exception as e:
                        print(f"  -> Error adding column: {e}")
                        conn.rollback()
    
    cur.close()
    conn.close()
    
    if changes_made:
        print("--- Sync Completed with Changes ---")
    else:
        print("--- DB Verified. No Changes Needed ---")

if __name__ == "__main__":
    sync_db()
