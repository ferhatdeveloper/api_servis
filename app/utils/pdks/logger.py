"""
Logging yardımcı fonksiyonları
"""
import logging
import os
from datetime import datetime


def setup_logger(name: str, log_file: str = None) -> logging.Logger:
    """Logger kurulumu"""
    
    # Logger oluştur
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Mevcut handler varsa ekleme
    if logger.handlers:
        return logger
    
    # Format
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Konsol handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Dosya handler (opsiyonel)
    if log_file:
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str = __name__) -> logging.Logger:
    """Logger al"""
    return logging.getLogger(name)
