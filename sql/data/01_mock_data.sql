-- =====================================================
-- EXFIN OPS - COMPLETE MOCK DATA
-- Date: 2026-01-16
-- Description: Test data for all tables
-- Usage: psql -U postgres -d exfin_db -f exfin_mock_data.sql
-- =====================================================

-- 1. TEMİZLİK (Önce eski verileri sil)
TRUNCATE TABLE 
    notifications, tasks, visit_photos, visits, 
    warehouse_transfer_lines, warehouse_transfers,
    user_company_preferences, salesman_targets, offline_orders,
    salesmen, brands, special_codes, campaigns, item_groups, units, warehouses,
    periods, companies, users 
RESTART IDENTITY CASCADE;

-- =====================================================
-- 2. KULLANICILAR
-- =====================================================

-- Admin
INSERT INTO users (username, password_hash, full_name, role, email, is_active)
VALUES ('admin', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxwKc.6IymCs7CN52old.kSj3jWay', 'Sistem Yöneticisi', 'admin', 'admin@exfin.com', true);

-- Supervisor
INSERT INTO users (username, password_hash, full_name, role, email, is_active)
VALUES ('supervisor', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxwKc.6IymCs7CN52old.kSj3jWay', 'Satış Müdürü', 'supervisor', 'mehmet@exfin.com', true);

-- Salesman 1
INSERT INTO users (username, password_hash, full_name, role, email, is_active, logo_salesman_code)
VALUES ('satis1', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxwKc.6IymCs7CN52old.kSj3jWay', 'Ali Kaya', 'salesman', 'ali@exfin.com', true, 'ALI.KAYA');

-- Salesman 2
INSERT INTO users (username, password_hash, full_name, role, email, is_active, logo_salesman_code)
VALUES ('satis2', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxwKc.6IymCs7CN52old.kSj3jWay', 'Ayşe Yılmaz', 'salesman', 'ayse@exfin.com', true, 'AYSE.YILMAZ');

-- Warehouse User
INSERT INTO users (username, password_hash, full_name, role, email, is_active)
VALUES ('depo1', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxwKc.6IymCs7CN52old.kSj3jWay', 'Depo Sorumlusu', 'warehouse', 'depo@exfin.com', true);

-- =====================================================
-- 3. FİRMA VE DÖNEM YÖNETİMİ
-- =====================================================

-- Firma 1: BERKEN TİCARET (Varsayılan)
INSERT INTO companies (logo_nr, code, name, is_default, tax_office, tax_number, address)
VALUES (1, '001', 'BERKEN TİCARET A.Ş.', true, 'Kadıköy', '1234567890', 'Bağdat Cad. No:1 Kadıköy/İSTANBUL');

-- Firma 2: EXFIN YAZILIM
INSERT INTO companies (logo_nr, code, name, is_default, tax_office, tax_number, address)
VALUES (100, '100', 'EXFIN YAZILIM A.Ş.', false, 'Kozyatağı', '9876543210', 'Plaza A Blok Kat:5 Ataşehir/İSTANBUL');

-- Firma 3: DEMO ŞİRKETİ
INSERT INTO companies (logo_nr, code, name, is_default)
VALUES (999, '999', 'DEMO ŞİRKETİ LTD.', false);

-- Dönemler (Berken Ticaret)
INSERT INTO periods (company_id, logo_period_nr, code, name, start_date, end_date, is_default)
VALUES 
((SELECT id FROM companies WHERE logo_nr=1), 1, '2024', '2024 Dönemi', '2024-01-01', '2024-12-31', false),
((SELECT id FROM companies WHERE logo_nr=1), 2, '2025', '2025 Dönemi', '2025-01-01', '2025-12-31', false),
((SELECT id FROM companies WHERE logo_nr=1), 3, '2026', '2026 Dönemi', '2026-01-01', '2026-12-31', true);

-- Dönemler (Exfin Yazılım)
INSERT INTO periods (company_id, logo_period_nr, code, name, start_date, end_date, is_default)
VALUES 
((SELECT id FROM companies WHERE logo_nr=100), 1, '2025', '2025 Mali Yıl', '2025-01-01', '2025-12-31', true);

-- Kullanıcı Tercihleri
INSERT INTO user_company_preferences (user_id, company_id, period_id)
VALUES 
((SELECT id FROM users WHERE username='satis1'), (SELECT id FROM companies WHERE logo_nr=1), (SELECT id FROM periods WHERE code='2026' AND company_id=(SELECT id FROM companies WHERE logo_nr=1))),
((SELECT id FROM users WHERE username='satis2'), (SELECT id FROM companies WHERE logo_nr=1), (SELECT id FROM periods WHERE code='2026' AND company_id=(SELECT id FROM companies WHERE logo_nr=1))),
((SELECT id FROM users WHERE username='admin'), (SELECT id FROM companies WHERE logo_nr=1), (SELECT id FROM periods WHERE code='2026' AND company_id=(SELECT id FROM companies WHERE logo_nr=1)));

-- =====================================================
-- 4. LOGO MASTER DATA (CACHE)
-- =====================================================

-- Satış Elemanları
INSERT INTO salesmen (company_id, code, name, email, tel_number, logo_ref)
VALUES 
((SELECT id FROM companies WHERE logo_nr=1), 'S01', 'Ahmet Yılmaz', 'ahmet@berken.com', '05321112233', 101),
((SELECT id FROM companies WHERE logo_nr=1), 'S02', 'Mehmet Demir', 'mehmet@berken.com', '05332223344', 102),
((SELECT id FROM companies WHERE logo_nr=1), 'S03', 'Ayşe Kaya', 'ayse@berken.com', '05445556677', 103);

-- Markalar
INSERT INTO brands (company_id, code, name, logo_ref)
VALUES 
((SELECT id FROM companies WHERE logo_nr=1), 'BR01', 'Samsung', 201),
((SELECT id FROM companies WHERE logo_nr=1), 'BR02', 'Apple', 202),
((SELECT id FROM companies WHERE logo_nr=1), 'BR03', 'LG', 203),
((SELECT id FROM companies WHERE logo_nr=1), 'BR04', 'Bosch', 204);

-- Depolar
INSERT INTO warehouses (company_id, code, name, cost_center, logo_ref)
VALUES 
((SELECT id FROM companies WHERE logo_nr=1), '00', 'Merkez Depo', 'M01', 1),
((SELECT id FROM companies WHERE logo_nr=1), '01', 'Şube 1 Depo', 'S01', 2),
((SELECT id FROM companies WHERE logo_nr=1), '02', 'Şube 2 Depo', 'S02', 3);

-- Birimler
INSERT INTO units (company_id, code, name, logo_ref)
VALUES 
((SELECT id FROM companies WHERE logo_nr=1), 'ADT', 'Adet', 1),
((SELECT id FROM companies WHERE logo_nr=1), 'KG', 'Kilogram', 2),
((SELECT id FROM companies WHERE logo_nr=1), 'KT', 'Kutu', 3);

-- Ürün Grupları
INSERT INTO item_groups (company_id, code, name, logo_ref)
VALUES 
((SELECT id FROM companies WHERE logo_nr=1), 'G01', 'Beyaz Eşya', 1),
((SELECT id FROM companies WHERE logo_nr=1), 'G02', 'Elektronik', 2),
((SELECT id FROM companies WHERE logo_nr=1), 'G03', 'Küçük Ev Aletleri', 3);

-- Kampanyalar
INSERT INTO campaigns (company_id, period_id, code, name, start_date, end_date, priority)
VALUES 
((SELECT id FROM companies WHERE logo_nr=1), (SELECT id FROM periods WHERE code='2026'), 'CMP01', 'Yılbaşı İndirimi %20', '2026-01-01', '2026-01-31', 1),
((SELECT id FROM companies WHERE logo_nr=1), (SELECT id FROM periods WHERE code='2026'), 'CMP02', 'Sevgililer Günü Özel', '2026-02-01', '2026-02-14', 2);

-- Özel Kodlar
INSERT INTO special_codes (company_id, specode_type, code, definition)
VALUES 
((SELECT id FROM companies WHERE logo_nr=1), 'CUSTOMER', 'VIP', 'Özel Müşteri'),
((SELECT id FROM companies WHERE logo_nr=1), 'CUSTOMER', 'BLK', 'Kara Liste'),
((SELECT id FROM companies WHERE logo_nr=1), 'ITEM', 'NEW', 'Yeni Ürün'),
((SELECT id FROM companies WHERE logo_nr=1), 'ITEM', 'OUT', 'Fırsat Ürünü');

-- =====================================================
-- 5. OPERASYONEL VERİLER (CRM)
-- =====================================================

-- Ziyaretler
INSERT INTO visits (user_id, customer_code, customer_name, planned_date, visit_type, status, notes, company_context_id)
VALUES 
((SELECT id FROM users WHERE username='satis1'), 'CARI001', 'ABC Ticaret', CURRENT_TIMESTAMP + INTERVAL '1 day', 'planned', 'planned', 'Yeni sezon ürün tanıtımı (Satış Görüşmesi)', (SELECT id FROM companies WHERE logo_nr=1)),
((SELECT id FROM users WHERE username='satis1'), 'CARI002', 'XYZ Limited', CURRENT_TIMESTAMP - INTERVAL '2 hours', 'regular', 'completed', 'Çek alındı (Tahsilat)', (SELECT id FROM companies WHERE logo_nr=1)),
((SELECT id FROM users WHERE username='satis2'), 'CARI003', 'Mehmet Bakkal', CURRENT_TIMESTAMP, 'regular', 'checked_in', 'Şu an görüşmedeyim (Rut Ziyareti)', (SELECT id FROM companies WHERE logo_nr=1));

-- Bildirimler
INSERT INTO notifications (user_id, title, body, type, is_read)
VALUES 
((SELECT id FROM users WHERE username='satis1'), 'Yeni Kampanya', 'Yılbaşı kampanyası başladı!', 'info', false),
((SELECT id FROM users WHERE username='satis1'), 'Onay Bekleyen Sipariş', 'Siparişiniz onay bekliyor.', 'warning', true),
((SELECT id FROM users WHERE username='admin'), 'Hata Raporu', 'Sync servisinde hata oluştu.', 'error', false);

-- Görevler
INSERT INTO tasks (title, description, assigned_to, created_by, due_date, priority, status)
VALUES 
('Müşteri Ziyareti', 'ABC Ticaret ile görüş', (SELECT id FROM users WHERE username='satis1'), (SELECT id FROM users WHERE username='supervisor'), CURRENT_TIMESTAMP + INTERVAL '2 days', 'high', 'pending'),
('Rapor Hazırla', 'Aylık satış raporu', (SELECT id FROM users WHERE username='satis1'), (SELECT id FROM users WHERE username='satis1'), CURRENT_TIMESTAMP + INTERVAL '5 days', 'normal', 'in_progress');

-- =====================================================
-- 6. DEPO TRANSFER VERİLERİ
-- =====================================================

-- Transfer 1: Beklemede
INSERT INTO warehouse_transfers (transfer_number, user_id, from_warehouse_id, to_warehouse_id, transfer_date, status, notes)
VALUES 
('TRF20260116001', (SELECT id FROM users WHERE username='satis1'), (SELECT id FROM warehouses WHERE code='00'), (SELECT id FROM warehouses WHERE code='01'), CURRENT_TIMESTAMP - INTERVAL '2 hours', 'pending', 'Acil stok');

INSERT INTO warehouse_transfer_lines (transfer_id, line_number, item_code, item_name, quantity, unit_code, unit_price, total_price)
VALUES 
((SELECT id FROM warehouse_transfers WHERE transfer_number='TRF20260116001'), 1, 'PRD001', 'Samsung TV', 5, 'ADT', 15000, 75000);

-- Transfer 2: Tamamlandı
INSERT INTO warehouse_transfers (transfer_number, user_id, from_warehouse_id, to_warehouse_id, transfer_date, status, notes, approved_by, approved_at)
VALUES 
('TRF20260115002', (SELECT id FROM users WHERE username='depo1'), (SELECT id FROM warehouses WHERE code='01'), (SELECT id FROM warehouses WHERE code='00'), CURRENT_TIMESTAMP - INTERVAL '1 day', 'completed', 'İade', (SELECT id FROM users WHERE username='admin'), CURRENT_TIMESTAMP - INTERVAL '20 hours');

INSERT INTO warehouse_transfer_lines (transfer_id, line_number, item_code, item_name, quantity, unit_code, unit_price, total_price)
VALUES 
((SELECT id FROM warehouse_transfers WHERE transfer_number='TRF20260115002'), 1, 'PRD005', 'Bozuk Ürün', 2, 'ADT', 500, 1000);

-- =====================================================
-- 7. ÖZET RAPOR
-- =====================================================

SELECT 'MOCK DATA LOADED SUCCESSFULLY' as status;
SELECT 'Users: ' || COUNT(*) FROM users;
SELECT 'Companies: ' || COUNT(*) FROM companies;
SELECT 'Periods: ' || COUNT(*) FROM periods;
SELECT 'Master Data (Salesmen): ' || COUNT(*) FROM salesmen;
SELECT 'Master Data (Brands): ' || COUNT(*) FROM brands;
SELECT 'Master Data (Warehouses): ' || COUNT(*) FROM warehouses;
SELECT 'Visits: ' || COUNT(*) FROM visits;
SELECT 'Transfers: ' || COUNT(*) FROM warehouse_transfers;
