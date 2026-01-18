"""
Otomatik Indexleme Modülü
Sık sorgulanan kolonları tespit edip otomatik index oluşturur
"""
from sqlalchemy import text, inspect
from sqlalchemy.orm import Session
from typing import List, Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)

class AutoIndexer:
    """Otomatik indexleme yöneticisi"""
    
    def __init__(self, engine):
        self.engine = engine
        self.inspector = inspect(engine)
    
    def analyze_query_patterns(self, table_name: str) -> List[Dict]:
        """
        Tabloda sık sorgulanan kolonları analiz et
        pg_stat_user_indexes ve pg_stats kullanarak
        """
        with self.engine.connect() as conn:
            try:
                # pg_stat_statements extension kontrol et
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_stat_statements"))
                conn.commit()
            except Exception as e:
                logger.warning(f"pg_stat_statements extension: {e}")
            
            # Tablodaki kolon ve istatistikleri al
            query = text("""
                SELECT 
                    column_name,
                    n_distinct,
                    correlation
                FROM pg_stats
                WHERE tablename = :table_name
                ORDER BY n_distinct DESC, correlation
                LIMIT 20
            """)
            
            result = conn.execute(query, {"table_name": table_name})
            columns = []
            
            for row in result:
                columns.append({
                    'column': row[0],
                    'distinct_values': row[1],
                    'correlation': row[2]
                })
            
            return columns
    
    def get_existing_indexes(self, table_name: str) -> List[str]:
        """Mevcut index'leri al"""
        indexes = self.inspector.get_indexes(table_name)
        column_names = []
        
        for index in indexes:
            # Index'deki kolonları al
            for col in index.get('column_names', []):
                if col not in column_names:
                    column_names.append(col)
        
        return column_names
    
    def suggest_indexes(self, table_name: str, min_distinct: float = 10) -> List[Dict]:
        """
        Eksik index önerileri oluştur
        
        Parametreler:
        - min_distinct: En az kaç farklı değere sahip kolonlar için index (varsayılan: 10)
        """
        # Sık sorgulanan kolonları al
        analyzed_columns = self.analyze_query_patterns(table_name)
        
        # Mevcut index'leri al
        existing_indexes = self.get_existing_indexes(table_name)
        
        # Index önerileri
        suggestions = []
        
        for col_info in analyzed_columns:
            column = col_info['column']
            distinct = col_info.get('distinct_values', 0)
            
            # Index önermek için kriterler:
            # 1. Zaten index yok
            # 2. Yeterli distinct değer var
            # 3. Primary key değil
            if (column not in existing_indexes and 
                distinct is not None and 
                distinct >= min_distinct and
                not column.endswith('_id') and  # Foreign key'ler zaten index'lenir
                column != 'id'):  # Primary key'leri atla
                
                suggestions.append({
                    'table': table_name,
                    'column': column,
                    'distinct_values': distinct,
                    'index_name': f'idx_{table_name}_{column}',
                    'priority': 'high' if distinct > 1000 else 'medium'
                })
        
        return suggestions
    
    def create_suggested_indexes(self, table_name: Optional[str] = None) -> Dict:
        """
        Önerilen index'leri oluştur
        
        Parametreler:
        - table_name: Belirli bir tablo için index oluştur (None ise tüm tablolar)
        """
        if table_name:
            tables = [table_name]
        else:
            tables = self.inspector.get_table_names()
        
        created = []
        failed = []
        
        for table in tables:
            try:
                suggestions = self.suggest_indexes(table)
                
                for suggestion in suggestions:
                    try:
                        self.create_index(
                            suggestion['table'],
                            suggestion['column'],
                            suggestion['index_name']
                        )
                        created.append(suggestion)
                        logger.info(f"Index oluşturuldu: {suggestion['index_name']}")
                    except Exception as e:
                        failed.append({
                            **suggestion,
                            'error': str(e)
                        })
                        logger.error(f"Index oluşturma hatası: {suggestion['index_name']} - {e}")
            except Exception as e:
                logger.error(f"Tablo analiz hatası: {table} - {e}")
        
        return {
            'created': created,
            'failed': failed,
            'total_created': len(created),
            'total_failed': len(failed)
        }
    
    def create_index(self, table_name: str, column: str, index_name: str) -> bool:
        """Index oluştur"""
        with self.engine.connect() as conn:
            query = text(f"CREATE INDEX IF NOT EXISTS {index_name} ON {table_name} ({column})")
            conn.execute(query)
            conn.commit()
        
        return True
    
    def analyze_table_performance(self, table_name: str) -> Dict:
        """
        Tablo performansını analiz et
        
        Returns:
        - Table size (heap)
        - Index size
        - Row count
        - Index usage statistics
        """
        with self.engine.connect() as conn:
            # Tablo boyutu
            size_query = text("""
                SELECT 
                    pg_size_pretty(pg_total_relation_size(:table_name)) as total_size,
                    pg_size_pretty(pg_relation_size(:table_name)) as table_size,
                    (SELECT pg_size_pretty(pg_total_relation_size(:table_name) - pg_relation_size(:table_name))) as index_size,
                    (SELECT reltuples FROM pg_class WHERE relname = :table_name) as estimated_rows
            """)
            
            result = conn.execute(size_query, {"table_name": table_name})
            size_info = result.fetchone()
            
            # Index kullanım istatistikleri
            index_query = text("""
                SELECT 
                    indexrelname as index_name,
                    idx_scan as scans,
                    idx_tup_read as tuples_read,
                    idx_tup_fetch as tuples_fetched
                FROM pg_stat_user_indexes
                WHERE schemaname = 'public' AND tablename = :table_name
                ORDER BY idx_scan DESC
            """)
            
            index_result = conn.execute(index_query, {"table_name": table_name})
            index_stats = [{
                'index_name': row[0],
                'scans': row[1],
                'tuples_read': row[2],
                'tuples_fetched': row[3]
            } for row in index_result]
            
            # Mevcut index'ler
            indexes = self.inspector.get_indexes(table_name)
            
            return {
                'table': table_name,
                'total_size': size_info[0] if size_info else 'N/A',
                'table_size': size_info[1] if size_info else 'N/A',
                'index_size': size_info[2] if size_info else 'N/A',
                'estimated_rows': int(size_info[3]) if size_info and size_info[3] else 0,
                'index_count': len(indexes),
                'index_usage': index_stats
            }
    
    def get_missing_indexes_from_queries(self) -> List[Dict]:
        """
        pg_stat_statements'ten eksik index önerileri al
        """
        with self.engine.connect() as conn:
            try:
                # pg_stat_statements extension olduğundan emin ol
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_stat_statements"))
                conn.commit()
                
                # Sık çalışan ancak yavaş sorguları bul
                query = text("""
                    SELECT 
                        query,
                        calls,
                        total_exec_time / 1000 as total_time_ms,
                        mean_exec_time / 1000 as mean_time_ms
                    FROM pg_stat_statements
                    WHERE query LIKE '%FROM %'
                    AND mean_exec_time > 100  -- 100ms'den yavaş sorgular
                    AND calls > 100  -- En az 100 kez çalışan
                    ORDER BY (total_exec_time / calls) DESC
                    LIMIT 20
                """)
                
                result = conn.execute(query)
                slow_queries = []
                
                for row in result:
                    slow_queries.append({
                        'query': row[0][:200],  # İlk 200 karakter
                        'calls': row[1],
                        'total_time_ms': round(row[2], 2),
                        'mean_time_ms': round(row[3], 2)
                    })
                
                return slow_queries
                
            except Exception as e:
                logger.error(f"Query analiz hatası: {e}")
                return []
