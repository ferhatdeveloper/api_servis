-- =====================================================
-- EXFIN OPS - MASTER DATABASE SCRIPT
-- Date: 2026-01-16
-- Database: EXFINOPS
-- Description: Creates DB, Schema, and Loads Data
-- =====================================================

-- 1. KILL CONNECTIONS & DROP DATABASE (If Exists)
-- (Bu bölümü pgAdmin gibi bir araçta çalıştırırken dikkatli olun, aktif bağlantıları koparır)
SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'EXFINOPS';
DROP DATABASE IF EXISTS "EXFINOPS";

-- 2. CREATE DATABASE
CREATE DATABASE "EXFINOPS"
    WITH 
    OWNER = postgres
    ENCODING = 'UTF8'
    CONNECTION LIMIT = -1;

-- 3. CONNECT TO DATABASE
\c "EXFINOPS";

-- =====================================================
-- 4. SCHEMA CREATION
-- =====================================================

-- ... (exfin_schema.sql içeriği buraya gelecek) ...

-- DB Version & Common Functions
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TABLE db_version (
    id SERIAL PRIMARY KEY,
    version INTEGER NOT NULL DEFAULT 1,
    description TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
INSERT INTO db_version (version, description) VALUES (1, 'Master Setup');

-- Users
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    email VARCHAR(100),
    role VARCHAR(20) DEFAULT 'user',
    is_active BOOLEAN DEFAULT true,
    logo_user_code VARCHAR(50),
    salesman_code VARCHAR(50),
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TABLE user_settings (
    user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    theme VARCHAR(20) DEFAULT 'light',
    language VARCHAR(10) DEFAULT 'tr',
    notifications_enabled BOOLEAN DEFAULT true,
    dashboard_layout JSONB,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Company & Period
CREATE TABLE companies (
    id SERIAL PRIMARY KEY,
    logo_nr INTEGER NOT NULL UNIQUE,
    code VARCHAR(50) NOT NULL,
    name VARCHAR(200) NOT NULL,
    tax_office VARCHAR(100),
    tax_number VARCHAR(50),
    address TEXT,
    is_active BOOLEAN DEFAULT true,
    is_default BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE periods (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    logo_period_nr INTEGER NOT NULL,
    code VARCHAR(50) NOT NULL,
    name VARCHAR(100),
    start_date DATE,
    end_date DATE,
    is_active BOOLEAN DEFAULT true,
    is_default BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_period_company_nr UNIQUE (company_id, logo_period_nr)
);

CREATE TABLE user_company_preferences (
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    company_id INTEGER REFERENCES companies(id),
    period_id INTEGER REFERENCES periods(id),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id)
);

-- Logo Master Data Cache
CREATE TABLE salesmen (
    id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES companies(id),
    code VARCHAR(50) NOT NULL,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100),
    tel_number VARCHAR(50),
    is_active BOOLEAN DEFAULT true,
    logo_ref INTEGER,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_salesman_company_code UNIQUE (company_id, code)
);

CREATE TABLE brands (
    id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES companies(id),
    code VARCHAR(50) NOT NULL,
    name VARCHAR(100) NOT NULL,
    logo_ref INTEGER,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_brand_company_code UNIQUE (company_id, code)
);

CREATE TABLE special_codes (
    id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES companies(id),
    specode_type VARCHAR(20) NOT NULL,
    code VARCHAR(50) NOT NULL,
    definition VARCHAR(200),
    logo_ref INTEGER,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_specode_company_type_code UNIQUE (company_id, specode_type, code)
);

CREATE TABLE campaigns (
    id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES companies(id),
    period_id INTEGER REFERENCES periods(id),
    code VARCHAR(50) NOT NULL,
    name VARCHAR(200) NOT NULL,
    start_date DATE,
    end_date DATE,
    is_active BOOLEAN DEFAULT true,
    priority INTEGER DEFAULT 0,
    logo_ref INTEGER,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE warehouses (
    id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES companies(id),
    code VARCHAR(50) NOT NULL,
    name VARCHAR(200) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    logo_ref INTEGER,
    cost_center VARCHAR(50),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_warehouse_company_code UNIQUE (company_id, code)
);

CREATE TABLE units (
    id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES companies(id),
    code VARCHAR(20) NOT NULL,
    name VARCHAR(50),
    logo_ref INTEGER,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE item_groups (
    id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES companies(id),
    code VARCHAR(50) NOT NULL,
    name VARCHAR(200),
    logo_ref INTEGER,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Operations
CREATE TABLE visits (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    customer_code VARCHAR(50) NOT NULL,
    customer_name VARCHAR(200),
    planned_date TIMESTAMP,
    check_in_time TIMESTAMP,
    check_out_time TIMESTAMP,
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    location_address TEXT,
    visit_type VARCHAR(50),
    status VARCHAR(20) DEFAULT 'planned',
    notes TEXT,
    voice_note_url TEXT,
    company_context_id INTEGER REFERENCES companies(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE visit_photos (
    id SERIAL PRIMARY KEY,
    visit_id INTEGER REFERENCES visits(id) ON DELETE CASCADE,
    photo_url TEXT NOT NULL,
    photo_type VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE tasks (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    assigned_to INTEGER REFERENCES users(id),
    created_by INTEGER REFERENCES users(id),
    due_date TIMESTAMP,
    priority VARCHAR(10) DEFAULT 'medium',
    status VARCHAR(20) DEFAULT 'pending',
    related_type VARCHAR(50),
    related_id INTEGER,
    company_context_id INTEGER REFERENCES companies(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    title VARCHAR(200) NOT NULL,
    body TEXT NOT NULL,
    type VARCHAR(50),
    is_read BOOLEAN DEFAULT false,
    data_payload JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Warehouse Transfers
CREATE TABLE warehouse_transfers (
    id SERIAL PRIMARY KEY,
    transfer_number VARCHAR(50) UNIQUE NOT NULL,
    user_id INTEGER NOT NULL REFERENCES users(id),
    from_warehouse_id INTEGER NOT NULL REFERENCES warehouses(id),
    to_warehouse_id INTEGER NOT NULL REFERENCES warehouses(id),
    transfer_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'pending',
    notes TEXT,
    logo_ref INTEGER,
    synced_to_logo BOOLEAN DEFAULT false,
    sync_date TIMESTAMP,
    approved_by INTEGER REFERENCES users(id),
    approved_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT check_different_warehouses CHECK (from_warehouse_id != to_warehouse_id)
);
CREATE TRIGGER update_warehouse_transfers_updated_at BEFORE UPDATE ON warehouse_transfers FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE OR REPLACE FUNCTION generate_transfer_number() RETURNS TRIGGER AS $$
BEGIN
    IF NEW.transfer_number IS NULL THEN
        NEW.transfer_number := 'TRF' || TO_CHAR(NOW(), 'YYYYMMDD') || LPAD(nextval('warehouse_transfers_id_seq')::TEXT, 6, '0');
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
CREATE TRIGGER set_transfer_number BEFORE INSERT ON warehouse_transfers FOR EACH ROW EXECUTE FUNCTION generate_transfer_number();

CREATE TABLE warehouse_transfer_lines (
    id SERIAL PRIMARY KEY,
    transfer_id INTEGER NOT NULL REFERENCES warehouse_transfers(id) ON DELETE CASCADE,
    line_number INTEGER NOT NULL,
    item_code VARCHAR(50) NOT NULL,
    item_name VARCHAR(200) NOT NULL,
    quantity DECIMAL(18, 3) NOT NULL,
    unit_code VARCHAR(20),
    unit_name VARCHAR(50),
    unit_price DECIMAL(18, 4),
    total_price DECIMAL(18, 4),
    currency VARCHAR(3) DEFAULT 'TRY',
    serial_numbers TEXT[],
    lot_number VARCHAR(50),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE offline_warehouse_transfers (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    from_warehouse_code VARCHAR(50) NOT NULL,
    from_warehouse_name VARCHAR(200),
    to_warehouse_code VARCHAR(50) NOT NULL,
    to_warehouse_name VARCHAR(200),
    transfer_date TIMESTAMP NOT NULL,
    notes TEXT,
    transfer_lines JSONB NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    sync_attempts INTEGER DEFAULT 0,
    last_sync_attempt TIMESTAMP,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    synced_at TIMESTAMP
);

-- Offline Sync
CREATE TABLE offline_orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    customer_code VARCHAR(50) NOT NULL,
    local_id VARCHAR(100) NOT NULL,
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    items JSONB NOT NULL,
    total_amount DECIMAL(18,2),
    notes TEXT,
    status VARCHAR(20) DEFAULT 'pending',
    logo_ref INTEGER,
    error_message TEXT,
    company_context_id INTEGER REFERENCES companies(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_offline_order_local UNIQUE (user_id, local_id)
);

CREATE TABLE offline_sync_queue (
    id SERIAL PRIMARY KEY,
    table_name VARCHAR(50) NOT NULL,
    record_id INTEGER NOT NULL,
    operation VARCHAR(20) DEFAULT 'INSERT',
    status VARCHAR(20) DEFAULT 'pending',
    priority INTEGER DEFAULT 1,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 5,
    last_error TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP
);

CREATE TABLE sync_metadata (
    user_id INTEGER REFERENCES users(id),
    entity_type VARCHAR(50) NOT NULL,
    last_sync_time TIMESTAMP,
    record_count INTEGER,
    last_error TEXT,
    PRIMARY KEY (user_id, entity_type)
);

-- =====================================================
-- 5. MOCK DATA LOADING
-- =====================================================

-- Users
INSERT INTO users (username, hashed_password, full_name, role, email, is_active, salesman_code, logo_user_code) VALUES
('admin', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxwKc.6IymCs7CN52old.kSj3jWay', 'Sistem Yöneticisi', 'admin', 'admin@exfin.com', true, NULL, NULL),
('supervisor', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxwKc.6IymCs7CN52old.kSj3jWay', 'Satış Müdürü', 'supervisor', 'mehmet@exfin.com', true, NULL, NULL),
('satis1', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxwKc.6IymCs7CN52old.kSj3jWay', 'Ali Kaya', 'salesman', 'ali@exfin.com', true, 'S001', 'ALI.KAYA'),
('satis2', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxwKc.6IymCs7CN52old.kSj3jWay', 'Ayşe Yılmaz', 'salesman', 'ayse@exfin.com', true, 'S002', 'AYSE.YILMAZ'),
('depo1', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxwKc.6IymCs7CN52old.kSj3jWay', 'Depo Sorumlusu', 'warehouse', 'depo@exfin.com', true, NULL, NULL);

-- Companies & Periods
INSERT INTO companies (logo_nr, code, name, is_default, tax_office, tax_number, address) VALUES
(1, '001', 'BERKEN TİCARET A.Ş.', true, 'Kadıköy', '1234567890', 'Bağdat Cad. No:1'),
(100, '100', 'EXFIN YAZILIM A.Ş.', false, 'Kozyatağı', '9876543210', 'Plaza A Blok Kat:5');

INSERT INTO periods (company_id, logo_period_nr, code, name, start_date, end_date, is_default) VALUES
((SELECT id FROM companies WHERE logo_nr=1), 1, '2024', '2024 Dönemi', '2024-01-01', '2024-12-31', false),
((SELECT id FROM companies WHERE logo_nr=1), 2, '2025', '2025 Dönemi', '2025-01-01', '2025-12-31', false),
((SELECT id FROM companies WHERE logo_nr=1), 3, '2026', '2026 Dönemi', '2026-01-01', '2026-12-31', true),
((SELECT id FROM companies WHERE logo_nr=100), 1, '2025', '2025 Mali Yıl', '2025-01-01', '2025-12-31', true);

-- User Preferences
INSERT INTO user_company_preferences (user_id, company_id, period_id) VALUES
((SELECT id FROM users WHERE username='satis1'), (SELECT id FROM companies WHERE logo_nr=1), (SELECT id FROM periods WHERE code='2026' AND company_id=(SELECT id FROM companies WHERE logo_nr=1))),
((SELECT id FROM users WHERE username='admin'), (SELECT id FROM companies WHERE logo_nr=1), (SELECT id FROM periods WHERE code='2026' AND company_id=(SELECT id FROM companies WHERE logo_nr=1)));

-- Master Data
INSERT INTO salesmen (company_id, code, name, logo_ref) VALUES
((SELECT id FROM companies WHERE logo_nr=1), 'S01', 'Ahmet Yılmaz', 101),
((SELECT id FROM companies WHERE logo_nr=1), 'S02', 'Mehmet Demir', 102);

INSERT INTO brands (company_id, code, name, logo_ref) VALUES
((SELECT id FROM companies WHERE logo_nr=1), 'BR01', 'Samsung', 201),
((SELECT id FROM companies WHERE logo_nr=1), 'BR02', 'Apple', 202);

INSERT INTO warehouses (company_id, code, name, logo_ref) VALUES
((SELECT id FROM companies WHERE logo_nr=1), '00', 'Merkez Depo', 1),
((SELECT id FROM companies WHERE logo_nr=1), '01', 'Şube 1 Depo', 2),
((SELECT id FROM companies WHERE logo_nr=1), '02', 'Şube 2 Depo', 3);

INSERT INTO units (company_id, code, name, logo_ref) VALUES
((SELECT id FROM companies WHERE logo_nr=1), 'ADT', 'Adet', 1);

-- Transfer Mock
INSERT INTO warehouse_transfers (transfer_number, user_id, from_warehouse_id, to_warehouse_id, transfer_date, status, notes) VALUES
('TRF202601160000001', (SELECT id FROM users WHERE username='satis1'), (SELECT id FROM warehouses WHERE code='00'), (SELECT id FROM warehouses WHERE code='01'), CURRENT_TIMESTAMP, 'pending', 'Acil');

INSERT INTO warehouse_transfer_lines (transfer_id, line_number, item_code, item_name, quantity, unit_code, total_price) VALUES
((SELECT id FROM warehouse_transfers WHERE transfer_number='TRF202601160000001'), 1, 'PRD001', 'Samsung TV', 5, 'ADT', 75000);

-- =====================================================
-- 6. SUMMARY
-- =====================================================
SELECT 'DATABASE EXFINOPS CREATED AND POPULATED SUCCESSFULLY' as result;
SELECT 'Table Counts:' as info;
SELECT 'Users: ' || COUNT(*) FROM users;
SELECT 'Companies: ' || COUNT(*) FROM companies;
SELECT 'Transfers: ' || COUNT(*) FROM warehouse_transfers;
