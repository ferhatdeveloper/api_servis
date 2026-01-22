"""
Veritabanı Utility Fonksiyonları - Performans Araçları
"""
from sqlalchemy import text, inspect
from sqlalchemy.orm import Session
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)


class DatabaseUtils:
    """Veritabanı yardımcı araçları"""
    
    @staticmethod
    def create_index(db: Session, table: str, column: str, index_name: str = None):
        """
        Performanslı index oluşturma
        
        Args:
            db: Database session
            table: Tablo adı
            column: Sütun adı
            index_name: İndex adı (opsiyonel)
        
        Returns:
            bool: Başarı durumu
        """
        try:
            if not index_name:
                index_name = f"idx_{table}_{column}"
            
            sql = f"CREATE INDEX IF NOT EXISTS {index_name} ON {table}({column})"
            
            db.execute(text(sql))
            db.commit()
            
            logger.info(f"Index olusturuldu: {index_name} on {table}({column})")
            return True
            
        except Exception as e:
            logger.error(f"Index olusturma hatasi: {str(e)}")
            return False
    
    @staticmethod
    def create_composite_index(db: Session, table: str, columns: List[str], index_name: str):
        """
        Composite index oluşturma (Birden fazla sütun)
        
        Args:
            db: Database session
            table: Tablo adı
            columns: Sütun listesi
            index_name: Index adı
        
        Returns:
            bool: Başarı durumu
        """
        try:
            columns_str = ", ".join(columns)
            sql = f"CREATE INDEX IF NOT EXISTS {index_name} ON {table}({columns_str})"
            
            db.execute(text(sql))
            db.commit()
            
            logger.info(f"Composite index olusturuldu: {index_name}")
            return True
            
        except Exception as e:
            logger.error(f"Composite index olusturma hatasi: {str(e)}")
            return False
    
    @staticmethod
    def add_column(db: Session, table: str, column_name: str, column_type: str, default_value: str = None):
        """
        Performanslı sütun ekleme
        
        Args:
            db: Database session
            table: Tablo adı
            column_name: Sütun adı
            column_type: Sütun tipi (VARCHAR, TEXT, INTEGER, etc.)
            default_value: Varsayılan değer
        
        Returns:
            bool: Başarı durumu
        """
        try:
            sql = f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {column_name} {column_type}"
            
            if default_value:
                sql += f" DEFAULT {default_value}"
            
            db.execute(text(sql))
            db.commit()
            
            logger.info(f"Sutun eklendi: {column_name} to {table}")
            return True
            
        except Exception as e:
            logger.error(f"Sutun ekleme hatasi: {str(e)}")
            return False
    
    @staticmethod
    def get_table_info(db: Session, table_name: str) -> Dict[str, Any]:
        """
        Tablo bilgilerini getir (sütunlar, tipler, indexler)
        
        Args:
            db: Database session
            table_name: Tablo adı
        
        Returns:
            dict: Tablo bilgileri
        """
        try:
            from sqlalchemy import MetaData
            
            metadata = MetaData()
            metadata.reflect(bind=db.bind, only=[table_name])
            
            table = metadata.tables.get(table_name)
            
            if not table:
                return {"error": "Table not found"}
            
            columns = []
            for col in table.columns:
                columns.append({
                    "name": col.name,
                    "type": str(col.type),
                    "nullable": col.nullable,
                    "primary_key": col.primary_key
                })
            
            return {
                "table": table_name,
                "columns": columns,
                "row_count": db.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()
            }
            
        except Exception as e:
            logger.error(f"Tablo bilgisi alma hatasi: {str(e)}")
            return {"error": str(e)}
    
    @staticmethod
    def analyze_table(db: Session, table_name: str):
        """
        Tablo analizi (PostgreSQL ANALYZE)
        
        Args:
            db: Database session
            table_name: Tablo adı
        """
        try:
            db.execute(text(f"ANALYZE {table_name}"))
            db.commit()
            logger.info(f"Tablo analiz edildi: {table_name}")
            
        except Exception as e:
            logger.error(f"Tablo analiz hatasi: {str(e)}")
    
    @staticmethod
    def optimize_table(db: Session, table_name: str):
        """
        Tablo optimizasyonu (VACUUM ANALYZE)
        
        Args:
            db: Database session
            table_name: Tablo adı
        """
        try:
            # VACUUM ANALYZE - Gereksiz alanları temizle
            db.execute(text(f"VACUUM ANALYZE {table_name}"))
            db.commit()
            
            logger.info(f"Tablo optimize edildi: {table_name}")
            return True
            
        except Exception as e:
            logger.error(f"Tablo optimize hatasi: {str(e)}")
            return False
    
    @staticmethod
    def get_table_size(db: Session, table_name: str) -> Dict[str, Any]:
        """
        Tablo boyutu bilgileri
        
        Args:
            db: Database session
            table_name: Tablo adı
        
        Returns:
            dict: Boyut bilgileri
        """
        try:
            # PostgreSQL için
            result = db.execute(text(f"""
                SELECT 
                    pg_size_pretty(pg_total_relation_size('{table_name}')) AS total_size,
                    pg_size_pretty(pg_relation_size('{table_name}')) AS table_size,
                    pg_size_pretty(pg_indexes_size('{table_name}')) AS indexes_size
            """))
            
            row = result.fetchone()
            
            return {
                "table": table_name,
                "total_size": row[0],
                "table_size": row[1],
                "indexes_size": row[2]
            }
            
        except Exception as e:
            logger.error(f"Boyut bilgisi alma hatasi: {str(e)}")
            return {"error": str(e)}
    
    @staticmethod
    def explain_query(db: Session, query: str) -> Dict[str, Any]:
        """
        Query plan analizi (EXPLAIN)
        
        Args:
            db: Database session
            query: SQL sorgusu
        
        Returns:
            dict: Query plan bilgileri
        """
        try:
            explain_query = f"EXPLAIN ANALYZE {query}"
            result = db.execute(text(explain_query))
            
            plan = "\n".join([row[0] for row in result])
            
            return {
                "query": query,
                "plan": plan
            }
            
        except Exception as e:
            return {"error": str(e)}
