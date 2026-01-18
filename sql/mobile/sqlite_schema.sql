-- =====================================================
-- EXFIN OPS - Mobile SQLite Database Schema
-- =====================================================
-- Purpose: Offline-first mobile database
-- Platform: Flutter Mobile (Android/iOS)
-- Database: SQLite (localdb.db)
-- Sync: Bidirectional with PostgreSQL backend
-- =====================================================

-- =====================================================
-- 1. KULLANICI & AYARLAR
-- =====================================================

-- Kullanıcı bilgileri (cache)
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    full_name TEXT,
    email TEXT,
    role TEXT,
    logo_salesman_code TEXT,
    department TEXT,
    is_active INTEGER DEFAULT 1,
    last_sync TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Kullanıcı ayarları
CREATE TABLE IF NOT EXISTS user_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    setting_key TEXT NOT NULL,
    setting_value TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, setting_key),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_user_settings_key ON user_settings(setting_key);

-- =====================================================
-- 2. OFFLINE SENKRONIZASYON KUYRUĞU
-- =====================================================

-- Genel offline işlem kuyruğu
CREATE TABLE IF NOT EXISTS offline_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    operation_type TEXT NOT NULL, -- 'order', 'collection', 'visit', 'stock_count'
    entity_id TEXT,               -- İlgili kayıt ID'si
    payload TEXT NOT NULL,        -- JSON data
    status TEXT DEFAULT 'pending', -- 'pending', 'syncing', 'synced', 'failed'
    retry_count INTEGER DEFAULT 0,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    synced_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_queue_status ON offline_queue(status, created_at);
CREATE INDEX IF NOT EXISTS idx_queue_type ON offline_queue(operation_type);

-- =====================================================
-- 3. MÜŞTERİ CACHE
-- =====================================================

-- Müşteriler (Logo ERP'den çekilmiş)
CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    logo_ref INTEGER,             -- Logo LOGICALREF
    code TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    phone TEXT,
    email TEXT,
    address TEXT,
    city TEXT,
    district TEXT,
    tax_office TEXT,
    tax_number TEXT,
    balance REAL DEFAULT 0,       -- Cari bakiye
    credit_limit REAL DEFAULT 0,
    is_active INTEGER DEFAULT 1,
    last_sync TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_customer_code ON customers(code);
CREATE INDEX IF NOT EXISTS idx_customer_name ON customers(name);
CREATE INDEX IF NOT EXISTS idx_customer_active ON customers(is_active);

-- =====================================================
-- 4. ÜRÜN CACHE
-- =====================================================

-- Ürünler (Logo ERP'den çekilmiş)
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    logo_ref INTEGER,             -- Logo LOGICALREF
    code TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    barcode TEXT,
    price REAL DEFAULT 0,
    vat_rate REAL DEFAULT 18,
    stock REAL DEFAULT 0,
    unit TEXT DEFAULT 'ADET',
    category TEXT,
    is_active INTEGER DEFAULT 1,
    last_sync TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_product_code ON products(code);
CREATE INDEX IF NOT EXISTS idx_product_barcode ON products(barcode);
CREATE INDEX IF NOT EXISTS idx_product_name ON products(name);
CREATE INDEX IF NOT EXISTS idx_product_active ON products(is_active);

-- =====================================================
-- 5. ZİYARET KAYITLARI
-- =====================================================

-- Müşteri ziyaretleri (offline kaydedilir, sonra sync)
CREATE TABLE IF NOT EXISTS visits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    customer_code TEXT NOT NULL,
    customer_name TEXT,
    visit_type TEXT DEFAULT 'routine', -- 'routine', 'order', 'collection', 'complaint'
    check_in_time TIMESTAMP NOT NULL,
    check_out_time TIMESTAMP,
    check_in_lat REAL,
    check_in_lng REAL,
    check_out_lat REAL,
    check_out_lng REAL,
    notes TEXT,
    photos TEXT,                  -- JSON array of photo paths
    is_synced INTEGER DEFAULT 0,
    synced_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_visits_user ON visits(user_id);
CREATE INDEX IF NOT EXISTS idx_visits_customer ON visits(customer_code);
CREATE INDEX IF NOT EXISTS idx_visits_synced ON visits(is_synced);
CREATE INDEX IF NOT EXISTS idx_visits_date ON visits(check_in_time);

-- =====================================================
-- 6. OFFLINE SİPARİŞLER
-- =====================================================

-- Siparişler (offline oluşturulur, sonra Logo'ya gönderilir)
CREATE TABLE IF NOT EXISTS offline_orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    customer_code TEXT NOT NULL,
    customer_name TEXT,
    order_date TIMESTAMP NOT NULL,
    delivery_date TIMESTAMP,
    total_amount REAL DEFAULT 0,
    total_vat REAL DEFAULT 0,
    grand_total REAL DEFAULT 0,
    currency TEXT DEFAULT 'TRY',
    notes TEXT,
    order_lines TEXT NOT NULL,    -- JSON array of order lines
    is_synced INTEGER DEFAULT 0,
    logo_ref INTEGER,             -- Logo'dan dönen LOGICALREF
    synced_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_orders_user ON offline_orders(user_id);
CREATE INDEX IF NOT EXISTS idx_orders_customer ON offline_orders(customer_code);
CREATE INDEX IF NOT EXISTS idx_orders_synced ON offline_orders(is_synced);
CREATE INDEX IF NOT EXISTS idx_orders_date ON offline_orders(order_date);

-- =====================================================
-- 7. OFFLINE TAHSİLATLAR
-- =====================================================

-- Tahsilatlar (offline kaydedilir, sonra Logo'ya gönderilir)
CREATE TABLE IF NOT EXISTS offline_collections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    customer_code TEXT NOT NULL,
    customer_name TEXT,
    amount REAL NOT NULL,
    payment_type TEXT NOT NULL,  -- 'cash', 'credit_card', 'bank_transfer', 'check'
    payment_details TEXT,         -- JSON (kart bilgisi, çek no, vs.)
    collection_date TIMESTAMP NOT NULL,
    notes TEXT,
    receipt_photo TEXT,           -- Makbuz fotoğrafı
    is_synced INTEGER DEFAULT 0,
    logo_ref INTEGER,             -- Logo'dan dönen LOGICALREF
    synced_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_collections_user ON offline_collections(user_id);
CREATE INDEX IF NOT EXISTS idx_collections_customer ON offline_collections(customer_code);
CREATE INDEX IF NOT EXISTS idx_collections_synced ON offline_collections(is_synced);
CREATE INDEX IF NOT EXISTS idx_collections_date ON offline_collections(collection_date);

-- =====================================================
-- 8. OFFLINE STOK SAYIM
-- =====================================================

-- Stok sayım fişleri (offline kaydedilir)
CREATE TABLE IF NOT EXISTS offline_stock_counts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    warehouse_code TEXT,
    count_date TIMESTAMP NOT NULL,
    count_lines TEXT NOT NULL,    -- JSON array of counted items
    notes TEXT,
    is_synced INTEGER DEFAULT 0,
    logo_ref INTEGER,
    synced_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_stock_counts_user ON offline_stock_counts(user_id);
CREATE INDEX IF NOT EXISTS idx_stock_counts_synced ON offline_stock_counts(is_synced);

-- =====================================================
-- 9. RAPOR SNAPSHOT
-- =====================================================

-- Raporlar (offline görüntüleme için cache)
CREATE TABLE IF NOT EXISTS report_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    report_code TEXT NOT NULL,
    report_name TEXT,
    report_data TEXT,             -- JSON data
    row_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_report_code ON report_snapshots(report_code);
CREATE INDEX IF NOT EXISTS idx_report_user ON report_snapshots(user_id);
CREATE INDEX IF NOT EXISTS idx_report_expires ON report_snapshots(expires_at);

-- =====================================================
-- 10. GPS KONUM GEÇMİŞİ
-- =====================================================

-- GPS konum kayıtları (background tracking)
CREATE TABLE IF NOT EXISTS gps_tracks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    accuracy REAL,
    speed REAL,
    heading REAL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_synced INTEGER DEFAULT 0,
    synced_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_gps_user ON gps_tracks(user_id);
CREATE INDEX IF NOT EXISTS idx_gps_timestamp ON gps_tracks(timestamp);
CREATE INDEX IF NOT EXISTS idx_gps_synced ON gps_tracks(is_synced);

-- =====================================================
-- 11. BİLDİRİMLER
-- =====================================================

-- Push bildirimleri (cache)
CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    notification_type TEXT,       -- 'info', 'warning', 'error', 'success'
    data TEXT,                    -- JSON payload
    is_read INTEGER DEFAULT 0,
    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_read ON notifications(is_read);

-- =====================================================
-- 12. SENKRONIZASYON METADATA
-- =====================================================

-- Son senkronizasyon zamanları ve durumları
CREATE TABLE IF NOT EXISTS sync_metadata (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type TEXT UNIQUE NOT NULL, -- 'customers', 'products', 'orders', etc.
    last_sync TIMESTAMP,
    last_pull TIMESTAMP,              -- Son veri çekme
    last_push TIMESTAMP,              -- Son veri gönderme
    record_count INTEGER DEFAULT 0,
    sync_status TEXT DEFAULT 'idle',  -- 'idle', 'syncing', 'success', 'error'
    error_message TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- 13. CACHE YÖNETİMİ
-- =====================================================

-- Genel cache tablosu (key-value)
CREATE TABLE IF NOT EXISTS cache_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cache_key TEXT UNIQUE NOT NULL,
    cache_value TEXT,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_cache_key ON cache_entries(cache_key);
CREATE INDEX IF NOT EXISTS idx_cache_expires ON cache_entries(expires_at);

-- =====================================================
-- 14. UYGULAMA LOGLARI
-- =====================================================

-- Hata ve aktivite logları (debugging)
CREATE TABLE IF NOT EXISTS app_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    log_level TEXT NOT NULL,      -- 'debug', 'info', 'warning', 'error'
    message TEXT NOT NULL,
    stack_trace TEXT,
    context TEXT,                 -- JSON (ek bilgiler)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_logs_level ON app_logs(log_level);
CREATE INDEX IF NOT EXISTS idx_logs_date ON app_logs(created_at);

-- =====================================================
-- VERİTABANI VERSİYON
-- =====================================================

-- Veritabanı versiyonu (migration için)
CREATE TABLE IF NOT EXISTS db_version (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    version INTEGER NOT NULL DEFAULT 1,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT OR IGNORE INTO db_version (id, version) VALUES (1, 1);

-- =====================================================
-- KURULUM TAMAMLANDI
-- =====================================================

-- Başlangıç verisi: Sync metadata
INSERT OR IGNORE INTO sync_metadata (entity_type, sync_status) VALUES
    ('customers', 'idle'),
    ('products', 'idle'),
    ('orders', 'idle'),
    ('collections', 'idle'),
    ('visits', 'idle'),
    ('stock_counts', 'idle'),
    ('gps_tracks', 'idle');
