"""
Veritabanı bağlantı yönetimi
"""
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from typing import Dict, Any
import logging

from app.core.pdks_config import config_manager

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Çoklu veritabanı yöneticisi"""
    
    def __init__(self):
        self.engines: Dict[str, Any] = {}
        self.sessions: Dict[str, Any] = {}
        self.successful_connections: Dict[str, str] = {}
        self.failed_connections: Dict[str, str] = {}
        self._initialize_databases()
    
    def _initialize_databases(self):
        """Tüm veritabanı bağlantılarını başlat"""
        logger.info("🔄 Veritabanı bağlantıları başlatılıyor...")
        
        for db_name in config_manager.databases.keys():
            try:
                connection_string = config_manager.get_connection_string(db_name)
                db_type = config_manager.databases[db_name].Type
                
                # Veritabanı tipine göre özel ayarlar
                if db_type == "SQLite":
                    engine = create_engine(
                        connection_string,
                        poolclass=StaticPool,
                        connect_args={"check_same_thread": False}
                    )
                elif db_type == "PostgreSQL":
                    # PostgreSQL için optimize edilmiş pool ayarları
                    engine = create_engine(
                        connection_string,
                        pool_pre_ping=True,  # Bağlantı sağlığını kontrol et
                        pool_size=10,  # Pool boyutu
                        max_overflow=20,  # Maksimum overflow
                        pool_recycle=3600,  # 1 saatte bir bağlantıları yenile
                        echo=False  # SQL sorgularını loglama (production'da False)
                    )
                else:
                    # Diğer veritabanları için varsayılan ayarlar
                    engine = create_engine(connection_string, pool_pre_ping=True)
                
                # Bağlantı testi
                from sqlalchemy import text
                with engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                
                self.engines[db_name] = engine
                self.sessions[db_name] = sessionmaker(bind=engine)
                self.successful_connections[db_name] = db_type
                
                logger.info(f"✅ Veritabanı bağlantısı kuruldu: {db_name} ({db_type})")
                
            except Exception as e:
                self.failed_connections[db_name] = str(e)
                logger.error(f"❌ Veritabanı bağlantı hatası ({db_name}): {str(e)}")
        
        logger.info(f"📊 Başarılı: {len(self.successful_connections)}, Başarısız: {len(self.failed_connections)}")
    
    def get_connection_status(self) -> Dict[str, Any]:
        """Bağlantı durumlarını döndür"""
        return {
            "successful": self.successful_connections,
            "failed": self.failed_connections,
            "total": len(config_manager.databases),
            "connected": len(self.successful_connections),
            "default": config_manager.app_config.Default
        }
    
    def get_session(self, db_name: str = None) -> Session:
        """Veritabanı oturumu al"""
        if db_name is None:
            db_name = config_manager.app_config.Default
        
        # Veritabanı bağlı değilse kontrol et ve dene
        if db_name not in self.sessions:
            if db_name in self.failed_connections:
                raise ValueError(f"Veritabanı bağlantısı başarısız: {db_name}. Hata: {self.failed_connections[db_name]}")
            else:
                raise ValueError(f"Veritabanı oturumu bulunamadı: {db_name}")
        
        session = self.sessions[db_name]()
        return session
    
    def get_engine(self, db_name: str = None):
        """Veritabanı motoru al"""
        if db_name is None:
            db_name = config_manager.app_config.Default
        
        # Veritabanı bağlı değilse kontrol et
        if db_name not in self.engines:
            if db_name in self.failed_connections:
                raise ValueError(f"Veritabanı bağlantısı başarısız: {db_name}. Hata: {self.failed_connections[db_name]}")
            else:
                raise ValueError(f"Veritabanı motoru bulunamadı: {db_name}")
        
        return self.engines[db_name]
    
    def close_all(self):
        """Tüm bağlantıları kapat"""
        for engine in self.engines.values():
            engine.dispose()
        logger.info("Tüm veritabanı bağlantıları kapatıldı")


# Global veritabanı yöneticisi
database_manager = DatabaseManager()
