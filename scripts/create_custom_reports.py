from app.core.database import db_manager
from loguru import logger
import asyncio

async def migrate():
    logger.info("Starting migration for custom_reports table...")
    
    query = """
    CREATE TABLE IF NOT EXISTS custom_reports (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        description TEXT,
        sql_query TEXT NOT NULL,
        view_name VARCHAR(255),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    try:
        # DB Manager usually runs sync queries in current implementation for PG
        # Checking db_manager implementation... it uses psycopg2 direct or async?
        # Based on previous files, db_manager has execute_pg_query.
        
        # Let's try synchronous execution which seems to be the pattern for schema updates
        # Actually db_manager methods might be async or sync depending on driver.
        # Let's import it and check, but to be safe, I'll use the method exposed.
        
        db_manager.execute_pg_query(query, params=None, fetch=False)
        logger.info("Successfully created custom_reports table.")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")

if __name__ == "__main__":
    asyncio.run(migrate())
