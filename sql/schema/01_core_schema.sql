-- =====================================================
-- EXFIN OPS - KOMPLE VERİTABANI ŞEMASI
-- Versiyon: 1.0 - Birleştirilmiş
-- Tarih: 2026-01-16
-- Açıklama: Tüm tablolar tek dosyada
-- =====================================================

-- Veritabanı Extension'ları yükle
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- =====================================================
-- 1. KULLANICI YÖNETİMİ
-- =====================================================

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    phone VARCHAR(20),
    role VARCHAR(20) DEFAULT 'salesman' CHECK (role IN ('admin', 'supervisor', 'salesman', 'warehouse')),
    logo_salesman_code VARCHAR(20),
    is_active BOOLEAN DEFAULT true,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_settings (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE UNIQUE,
    default_printer_address VARCHAR(100),
    theme VARCHAR(20) DEFAULT 'dark' CHECK (theme IN ('light', 'dark')),
    language VARCHAR(10) DEFAULT 'tr' CHECK (language IN ('tr', 'en', 'ar')),
    notification_enabled BOOLEAN DEFAULT true,
    gps_tracking_enabled BOOLEAN DEFAULT true,
    settings JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- 1.1 FİRMA VE DÖNEM YÖNETİMİ (MASTER)
-- =====================================================

CREATE TABLE IF NOT EXISTS companies (
    id SERIAL PRIMARY KEY,
    logo_nr INTEGER NOT NULL,
    code VARCHAR(20) NOT NULL,
    name VARCHAR(200) NOT NULL,
    is_default BOOLEAN DEFAULT false,
    tax_office VARCHAR(100),
    tax_number VARCHAR(20),
    address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS periods (
    id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES companies(id) ON DELETE CASCADE,
    logo_period_nr INTEGER NOT NULL,
    code VARCHAR(20) NOT NULL,
    name VARCHAR(100),
    start_date DATE,
    end_date DATE,
    is_default BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_company_preferences (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    company_id INTEGER REFERENCES companies(id) ON DELETE CASCADE,
    period_id INTEGER REFERENCES periods(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id)
);

-- =====================================================
-- 1.2 MASTER DATA (LOGO ENTEGRASYON)
-- =====================================================

CREATE TABLE IF NOT EXISTS salesmen (
    id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES companies(id) ON DELETE CASCADE,
    code VARCHAR(50) NOT NULL,
    name VARCHAR(100),
    email VARCHAR(100),
    tel_number VARCHAR(20),
    logo_ref INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS brands (
    id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES companies(id) ON DELETE CASCADE,
    code VARCHAR(50) NOT NULL,
    name VARCHAR(100),
    logo_ref INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS warehouses (
    id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES companies(id) ON DELETE CASCADE,
    code VARCHAR(50) NOT NULL,
    name VARCHAR(100),
    cost_center VARCHAR(50),
    logo_ref INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS units (
    id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES companies(id) ON DELETE CASCADE,
    code VARCHAR(50) NOT NULL,
    name VARCHAR(100),
    logo_ref INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS item_groups (
    id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES companies(id) ON DELETE CASCADE,
    code VARCHAR(50) NOT NULL,
    name VARCHAR(100),
    logo_ref INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS campaigns (
    id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES companies(id) ON DELETE CASCADE,
    period_id INTEGER REFERENCES periods(id) ON DELETE CASCADE,
    code VARCHAR(50),
    name VARCHAR(200),
    start_date DATE,
    end_date DATE,
    priority INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS special_codes (
    id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES companies(id) ON DELETE CASCADE,
    specode_type VARCHAR(50), -- CUSTOMER, ITEM, etc.
    code VARCHAR(50),
    definition VARCHAR(200),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS salesman_targets (
    id SERIAL PRIMARY KEY,
    salesman_id INTEGER REFERENCES salesmen(id) ON DELETE CASCADE,
    period_id INTEGER REFERENCES periods(id) ON DELETE CASCADE,
    target_type VARCHAR(50), -- 'monthly_sales', 'yearly_sales', 'visit_count', etc.
    target_amount DECIMAL(15, 2) DEFAULT 0,
    currency VARCHAR(3) DEFAULT 'TRY',
    start_date DATE,
    end_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- 2. SAHA OPERASYONLARI
-- =====================================================

CREATE TABLE IF NOT EXISTS visits (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    customer_code VARCHAR(20) NOT NULL,
    customer_name VARCHAR(100),
    visit_type VARCHAR(20) DEFAULT 'regular' CHECK (visit_type IN ('regular', 'emergency', 'planned')),
    status VARCHAR(20) DEFAULT 'planned' CHECK (status IN ('planned', 'checked_in', 'completed', 'cancelled')),
    planned_date TIMESTAMP,
    check_in_time TIMESTAMP,
    check_out_time TIMESTAMP,
    check_in_lat DECIMAL(10, 8),
    check_in_lng DECIMAL(11, 8),
    check_out_lat DECIMAL(10, 8),
    check_out_lng DECIMAL(11, 8),
    notes TEXT,
    photos JSONB,
    company_context_id INTEGER REFERENCES companies(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS gps_tracks (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    latitude DECIMAL(10, 8) NOT NULL,
    longitude DECIMAL(11, 8) NOT NULL,
    accuracy DECIMAL(5, 2),
    speed DECIMAL(5, 2),
    heading DECIMAL(5, 2),
    timestamp TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_gps_user_time ON gps_tracks(user_id, timestamp DESC);

-- =====================================================
-- 3. OFFLINE SENKRONIZASYON
-- =====================================================

CREATE TABLE IF NOT EXISTS offline_sync_queue (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    operation_type VARCHAR(50) NOT NULL,
    payload JSONB NOT NULL,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'synced', 'failed')),
    retry_count INTEGER DEFAULT 0,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    synced_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_sync_status ON offline_sync_queue(user_id, status, created_at DESC);

-- =====================================================
-- 4. BİLDİRİMLER
-- =====================================================

CREATE TABLE IF NOT EXISTS notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(100) NOT NULL,
    body TEXT NOT NULL,
    type VARCHAR(20) DEFAULT 'info' CHECK (type IN ('info', 'warning', 'error', 'success')),
    priority VARCHAR(10) DEFAULT 'normal' CHECK (priority IN ('low', 'normal', 'high', 'urgent')),
    is_read BOOLEAN DEFAULT false,
    action_url VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    read_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_notif_user_read ON notifications(user_id, is_read, created_at DESC);

-- =====================================================
-- 5. RAPOR ÖNBELLEK
-- =====================================================

CREATE TABLE IF NOT EXISTS report_snapshots (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    report_code VARCHAR(50) NOT NULL,
    report_name VARCHAR(100),
    report_data JSONB NOT NULL,
    row_count INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_report_user_code ON report_snapshots(user_id, report_code, created_at DESC);

-- =====================================================
-- 6. PERFORMANS & ANALİTİK
-- =====================================================

CREATE TABLE IF NOT EXISTS user_activity_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    action VARCHAR(50) NOT NULL,
    entity_type VARCHAR(50),
    entity_id VARCHAR(50),
    details JSONB,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_activity_user_time ON user_activity_logs(user_id, created_at DESC);

-- =====================================================
-- 7. GÖREV YÖNETİMİ
-- =====================================================

CREATE TABLE IF NOT EXISTS tasks (
    id SERIAL PRIMARY KEY,
    assigned_to INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    priority VARCHAR(10) DEFAULT 'normal' CHECK (priority IN ('low', 'normal', 'high', 'urgent')),
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed', 'cancelled')),
    due_date TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- 8. GÜVENLİK & FIREWALL
-- =====================================================

CREATE TABLE IF NOT EXISTS device_security_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    device_id VARCHAR(100) NOT NULL,
    device_name VARCHAR(100),
    security_check_type VARCHAR(50) NOT NULL,
    is_passed BOOLEAN NOT NULL,
    details JSONB,
    ip_address VARCHAR(45),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_security_user_device ON device_security_logs(user_id, device_id, created_at DESC);

CREATE TABLE IF NOT EXISTS firewall_rules (
    id SERIAL PRIMARY KEY,
    rule_name VARCHAR(100) NOT NULL,
    rule_type VARCHAR(50) NOT NULL,
    rule_value TEXT NOT NULL,
    is_active BOOLEAN DEFAULT true,
    priority INTEGER DEFAULT 0,
    description TEXT,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS blocked_devices (
    id SERIAL PRIMARY KEY,
    device_id VARCHAR(100) UNIQUE NOT NULL,
    device_name VARCHAR(100),
    user_id INTEGER REFERENCES users(id),
    reason VARCHAR(255),
    blocked_by INTEGER REFERENCES users(id),
    blocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    unblocked_at TIMESTAMP,
    is_active BOOLEAN DEFAULT true
);

-- =====================================================
-- 9. CANLI KONUM
-- =====================================================

CREATE TABLE IF NOT EXISTS live_location_snapshots (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE UNIQUE,
    latitude DECIMAL(10, 8) NOT NULL,
    longitude DECIMAL(11, 8) NOT NULL,
    accuracy DECIMAL(5, 2),
    speed DECIMAL(5, 2),
    heading DECIMAL(5, 2),
    battery_level INTEGER,
    is_online BOOLEAN DEFAULT true,
    last_update TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_live_location_update ON live_location_snapshots(last_update DESC);

CREATE TABLE IF NOT EXISTS location_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    latitude DECIMAL(10, 8) NOT NULL,
    longitude DECIMAL(11, 8) NOT NULL,
    accuracy DECIMAL(5, 2),
    speed DECIMAL(5, 2),
    heading DECIMAL(5, 2),
    altitude DECIMAL(7, 2),
    battery_level INTEGER,
    is_moving BOOLEAN DEFAULT false,
    address TEXT,
    timestamp TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_location_user_time ON location_history(user_id, timestamp DESC);

-- =====================================================
-- 10. SİPARİŞ & SATIŞ (OFFLINE)
-- =====================================================

CREATE TABLE IF NOT EXISTS offline_orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    customer_code VARCHAR(20) NOT NULL,
    customer_name VARCHAR(100),
    order_date TIMESTAMP NOT NULL,
    total_amount DECIMAL(15, 2),
    currency VARCHAR(3) DEFAULT 'TRY',
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'synced', 'failed')),
    logo_ref VARCHAR(50),
    order_lines JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    synced_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_offline_orders_status ON offline_orders(user_id, status, created_at DESC);

CREATE TABLE IF NOT EXISTS offline_collections (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    customer_code VARCHAR(20) NOT NULL,
    customer_name VARCHAR(100),
    amount DECIMAL(15, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'TRY',
    payment_type VARCHAR(20) DEFAULT 'cash' CHECK (payment_type IN ('cash', 'credit_card', 'bank_transfer', 'check')),
    collection_date TIMESTAMP NOT NULL,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'synced', 'failed')),
    logo_ref VARCHAR(50),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    synced_at TIMESTAMP
);

-- =====================================================
-- 11. STOK SAYIM
-- =====================================================

CREATE TABLE IF NOT EXISTS offline_stock_counts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    warehouse_code VARCHAR(20),
    warehouse_name VARCHAR(100),
    count_date TIMESTAMP NOT NULL,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'synced', 'failed')),
    logo_ref VARCHAR(50),
    count_lines JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    synced_at TIMESTAMP
);

-- =====================================================
-- 11.1 DEPO TRANSFERLERİ
-- =====================================================

CREATE TABLE IF NOT EXISTS warehouse_transfers (
    id SERIAL PRIMARY KEY,
    transfer_number VARCHAR(50) UNIQUE NOT NULL,
    user_id INTEGER REFERENCES users(id),
    from_warehouse_id INTEGER REFERENCES warehouses(id),
    to_warehouse_id INTEGER REFERENCES warehouses(id),
    transfer_date TIMESTAMP NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    notes TEXT,
    approved_by INTEGER REFERENCES users(id),
    approved_at TIMESTAMP,
    logo_ref VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS warehouse_transfer_lines (
    id SERIAL PRIMARY KEY,
    transfer_id INTEGER REFERENCES warehouse_transfers(id) ON DELETE CASCADE,
    line_number INTEGER,
    item_code VARCHAR(50),
    item_name VARCHAR(200),
    quantity DECIMAL(15, 2),
    unit_code VARCHAR(20),
    unit_price DECIMAL(15, 2),
    total_price DECIMAL(15, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- 12. RAPORLAMA
-- =====================================================

CREATE TABLE IF NOT EXISTS favorite_reports (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    report_code VARCHAR(50) NOT NULL,
    report_name VARCHAR(100),
    filters JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, report_code)
);

CREATE TABLE IF NOT EXISTS report_access_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    report_code VARCHAR(50) NOT NULL,
    execution_time_ms INTEGER,
    row_count INTEGER,
    filters JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_report_access ON report_access_logs(user_id, report_code, created_at DESC);

-- =====================================================
-- 13. BİLDİRİM GEÇMİŞİ
-- =====================================================

CREATE TABLE IF NOT EXISTS push_notification_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    notification_id INTEGER REFERENCES notifications(id) ON DELETE SET NULL,
    fcm_token VARCHAR(255),
    title VARCHAR(100),
    body TEXT,
    data JSONB,
    status VARCHAR(20) DEFAULT 'sent' CHECK (status IN ('sent', 'delivered', 'failed')),
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    delivered_at TIMESTAMP
);

-- =====================================================
-- 14. SİSTEM AYARLARI
-- =====================================================

CREATE TABLE IF NOT EXISTS system_settings (
    id SERIAL PRIMARY KEY,
    setting_key VARCHAR(100) UNIQUE NOT NULL,
    setting_value TEXT,
    setting_type VARCHAR(20) DEFAULT 'string' CHECK (setting_type IN ('string', 'number', 'boolean', 'json')),
    description TEXT,
    is_public BOOLEAN DEFAULT false,
    updated_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- 15. MULTI-TENANT
-- =====================================================

CREATE TABLE IF NOT EXISTS tenants (
    id SERIAL PRIMARY KEY,
    tenant_code VARCHAR(50) UNIQUE NOT NULL,
    tenant_name VARCHAR(100) NOT NULL,
    logo_firma_no VARCHAR(10),
    logo_period_no VARCHAR(10),
    logo_db_name VARCHAR(100),
    is_active BOOLEAN DEFAULT true,
    subscription_expires_at TIMESTAMP,
    settings JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_visits_user_date ON visits(user_id, check_in_time);

CREATE TABLE IF NOT EXISTS visit_photos (
    id SERIAL PRIMARY KEY,
    visit_id INTEGER REFERENCES visits(id) ON DELETE CASCADE,
    photo_url TEXT NOT NULL,
    photo_type VARCHAR(20) DEFAULT 'check_in' CHECK (photo_type IN ('check_in', 'check_out', 'general')),
    taken_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    gps_lat DOUBLE PRECISION,
    gps_lng DOUBLE PRECISION
);

CREATE TABLE IF NOT EXISTS user_tenants (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    tenant_id INTEGER REFERENCES tenants(id) ON DELETE CASCADE,
    is_default BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, tenant_id)
);

-- =====================================================
-- 16. CACHE
-- =====================================================

CREATE TABLE IF NOT EXISTS cache_entries (
    id SERIAL PRIMARY KEY,
    cache_key VARCHAR(255) UNIQUE NOT NULL,
    cache_value TEXT,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_cache_key_expires ON cache_entries(cache_key, expires_at);

-- =====================================================
-- 17. DOSYA YÖNETİMİ
-- =====================================================

CREATE TABLE IF NOT EXISTS uploaded_files (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    file_name VARCHAR(255) NOT NULL,
    file_path TEXT NOT NULL,
    file_type VARCHAR(50),
    file_size BIGINT,
    mime_type VARCHAR(100),
    entity_type VARCHAR(50),
    entity_id VARCHAR(50),
    is_public BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_files_entity ON uploaded_files(entity_type, entity_id);

-- =====================================================
-- 18. TRIGGER'LAR
-- =====================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_user_settings_updated_at ON user_settings;
CREATE TRIGGER update_user_settings_updated_at BEFORE UPDATE ON user_settings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_tasks_updated_at ON tasks;
CREATE TRIGGER update_tasks_updated_at BEFORE UPDATE ON tasks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_warehouse_transfers_updated_at ON warehouse_transfers;
CREATE TRIGGER update_warehouse_transfers_updated_at BEFORE UPDATE ON warehouse_transfers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_companies_updated_at ON companies;
CREATE TRIGGER update_companies_updated_at BEFORE UPDATE ON companies
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_periods_updated_at ON periods;
CREATE TRIGGER update_periods_updated_at BEFORE UPDATE ON periods
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_firewall_rules_updated_at ON firewall_rules;
CREATE TRIGGER update_firewall_rules_updated_at BEFORE UPDATE ON firewall_rules
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_system_settings_updated_at ON system_settings;
CREATE TRIGGER update_system_settings_updated_at BEFORE UPDATE ON system_settings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_tenants_updated_at ON tenants;
CREATE TRIGGER update_tenants_updated_at BEFORE UPDATE ON tenants
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- 19. CLEANUP FONKSİYONU
-- =====================================================

CREATE OR REPLACE FUNCTION cleanup_expired_cache()
RETURNS void AS $$
BEGIN
    DELETE FROM cache_entries WHERE expires_at < CURRENT_TIMESTAMP;
    DELETE FROM report_snapshots WHERE expires_at < CURRENT_TIMESTAMP;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- 20. LOGO ERP RAPORLAMA VIEW'LARI (YoY Comparison)
-- =====================================================
-- NOT: Bu view'lar Logo ERP veritabanında çalıştırılmalıdır
-- EXFIN_API üzerinden Logo DB'ye bağlanarak kullanılır

-- YoY Günlük Karşılaştırma View'ı
-- CREATE OR REPLACE VIEW V_YOY_DAILY_COMPARISON AS
-- (Logo ERP veritabanında çalıştırılacak)

-- YoY Haftalık Karşılaştırma View'ı  
-- CREATE OR REPLACE VIEW V_YOY_WEEKLY_COMPARISON AS
-- (Logo ERP veritabanında çalıştırılacak)

-- YoY Aylık Karşılaştırma View'ı
-- CREATE OR REPLACE VIEW V_YOY_MONTHLY_COMPARISON AS
-- (Logo ERP veritabanında çalıştırılacak)

-- NOT: YoY view'ları için Backend/EXFIN_API/yoy_comparison_views.sql dosyasına bakın
-- Bu view'lar Logo ERP SQL Server veritabanında oluşturulmalıdır

-- =====================================================
-- KURULUM TAMAMLANDI
-- =====================================================

SELECT 'Veritabanı şeması başarıyla oluşturuldu!' as status;
SELECT 'Toplam ' || COUNT(*) || ' tablo oluşturuldu.' as info
FROM information_schema.tables
WHERE table_schema = 'public' AND table_type = 'BASE TABLE';
DROP TRIGGER IF EXISTS update_salesman_targets_updated_at ON salesman_targets;
CREATE TRIGGER update_salesman_targets_updated_at BEFORE UPDATE ON salesman_targets
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
