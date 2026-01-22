-- EXFIN Restaurant Management System - PostgreSQL Veritabanı Kurulum Scripti
-- Veritabanı: exfin_rest
-- Bu script tüm tabloları siler ve yeniden oluşturur

-- =====================================================
-- MEVCUT TABLOLARI TEMİZLE
-- =====================================================

-- Tüm tabloları sil (CASCADE ile bağımlılıkları da sil)
DROP TABLE IF EXISTS order_items CASCADE;
DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS reservations CASCADE;
DROP TABLE IF EXISTS stock_movements CASCADE;
DROP TABLE IF EXISTS product_ingredients CASCADE;
DROP TABLE IF EXISTS ingredients CASCADE;
DROP TABLE IF EXISTS products CASCADE;
DROP TABLE IF EXISTS categories CASCADE;
DROP TABLE IF EXISTS tables CASCADE;
DROP TABLE IF EXISTS regions CASCADE;
DROP TABLE IF EXISTS customers CASCADE;
DROP TABLE IF EXISTS daily_sales CASCADE;
DROP TABLE IF EXISTS settings CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- Tüm fonksiyonları sil
DROP FUNCTION IF EXISTS generate_fatura_kodu(INTEGER) CASCADE;
DROP FUNCTION IF EXISTS set_fatura_kodu() CASCADE;
DROP FUNCTION IF EXISTS update_updated_at_column() CASCADE;

-- =====================================================
-- YENİ TABLOLARI OLUŞTUR
-- =====================================================

-- =====================================================
-- KULLANICI YÖNETİMİ
-- =====================================================

-- Users tablosu
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(100) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'user',
    is_active BOOLEAN DEFAULT true,
    email VARCHAR(100),
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    phone VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- BÖLGE VE MASA YÖNETİMİ
-- =====================================================

-- Regions tablosu
CREATE TABLE IF NOT EXISTS regions (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tables tablosu
CREATE TABLE IF NOT EXISTS tables (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    capacity INTEGER NOT NULL DEFAULT 4,
    status VARCHAR(20) DEFAULT 'Available',
    location VARCHAR(100),
    region_id INTEGER REFERENCES regions(id),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- MENÜ VE ÜRÜN YÖNETİMİ
-- =====================================================

-- Categories tablosu
CREATE TABLE IF NOT EXISTS categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    name_en VARCHAR(100), -- İngilizce isim
    name_ar VARCHAR(100), -- Arapça isim
    name_ku VARCHAR(100), -- Kürtçe (Kurmanci) isim
    name_sr VARCHAR(100), -- Kürtçe (Sorani) isim
    description TEXT,
    description_en TEXT, -- İngilizce açıklama
    description_ar TEXT, -- Arapça açıklama
    description_ku TEXT, -- Kürtçe (Kurmanci) açıklama
    description_sr TEXT, -- Kürtçe (Sorani) açıklama
    icon VARCHAR(50), -- kategori ikonu
    color VARCHAR(7), -- kategori rengi (#RRGGBB)
    sort_order INTEGER DEFAULT 0, -- sıralama
    is_active BOOLEAN DEFAULT true,
    is_featured BOOLEAN DEFAULT false, -- öne çıkan kategori
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Products tablosu
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    name_en VARCHAR(100), -- İngilizce isim
    name_ar VARCHAR(100), -- Arapça isim
    name_ku VARCHAR(100), -- Kürtçe (Kurmanci) isim
    name_sr VARCHAR(100), -- Kürtçe (Sorani) isim
    description TEXT,
    description_en TEXT, -- İngilizce açıklama
    description_ar TEXT, -- Arapça açıklama
    description_ku TEXT, -- Kürtçe (Kurmanci) açıklama
    description_sr TEXT, -- Kürtçe (Sorani) açıklama
    price DECIMAL(10,2) NOT NULL,
    category_id INTEGER REFERENCES categories(id),
    is_active BOOLEAN DEFAULT true,
    image_url VARCHAR(255),
    preparation_time INTEGER DEFAULT 15, -- dakika
    spice_level INTEGER DEFAULT 0, -- 0-5 arası acı seviyesi
    is_vegetarian BOOLEAN DEFAULT false,
    is_vegan BOOLEAN DEFAULT false,
    is_gluten_free BOOLEAN DEFAULT false,
    is_hot BOOLEAN DEFAULT false, -- sıcak servis
    is_cold BOOLEAN DEFAULT false, -- soğuk servis
    calories INTEGER, -- kalori
    allergens TEXT, -- alerjenler
    origin_country VARCHAR(50), -- menşei ülke
    chef_special BOOLEAN DEFAULT false, -- şef özel
    popular BOOLEAN DEFAULT false, -- popüler ürün
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- SİPARİŞ YÖNETİMİ
-- =====================================================

-- Orders tablosu
CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    fatura_kodu VARCHAR(20) UNIQUE NOT NULL,
    table_id INTEGER REFERENCES tables(id),
    waiter_id INTEGER REFERENCES users(id),
    customer_name VARCHAR(100),
    customer_phone VARCHAR(20),
    status VARCHAR(20) DEFAULT 'pending', -- pending, confirmed, preparing, ready, served, completed, cancelled
    total_amount DECIMAL(10,2) DEFAULT 0,
    tax_amount DECIMAL(10,2) DEFAULT 0,
    discount_amount DECIMAL(10,2) DEFAULT 0,
    final_amount DECIMAL(10,2) DEFAULT 0,
    payment_method VARCHAR(20), -- cash, card, online
    payment_status VARCHAR(20) DEFAULT 'pending', -- pending, paid, refunded
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- OrderItems tablosu
CREATE TABLE IF NOT EXISTS order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(id) ON DELETE CASCADE,
    product_id INTEGER REFERENCES products(id),
    quantity INTEGER NOT NULL DEFAULT 1,
    unit_price DECIMAL(10,2) NOT NULL,
    total_price DECIMAL(10,2) NOT NULL,
    notes TEXT,
    status VARCHAR(20) DEFAULT 'pending', -- pending, preparing, ready, served
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- REZERVASYON YÖNETİMİ
-- =====================================================

-- Reservations tablosu
CREATE TABLE IF NOT EXISTS reservations (
    id SERIAL PRIMARY KEY,
    table_id INTEGER REFERENCES tables(id),
    customer_name VARCHAR(100) NOT NULL,
    customer_phone VARCHAR(20),
    customer_email VARCHAR(100),
    reservation_date DATE NOT NULL,
    reservation_time TIME NOT NULL,
    party_size INTEGER NOT NULL,
    status VARCHAR(20) DEFAULT 'confirmed', -- confirmed, seated, completed, cancelled, no_show
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- STOK YÖNETİMİ
-- =====================================================

-- Ingredients tablosu
CREATE TABLE IF NOT EXISTS ingredients (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    unit VARCHAR(20) DEFAULT 'kg', -- kg, gr, lt, ml, adet
    current_stock DECIMAL(10,3) DEFAULT 0,
    min_stock DECIMAL(10,3) DEFAULT 0,
    max_stock DECIMAL(10,3) DEFAULT 0,
    unit_price DECIMAL(10,2) DEFAULT 0,
    supplier VARCHAR(100),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ProductIngredients tablosu (ürün-malzeme ilişkisi)
CREATE TABLE IF NOT EXISTS product_ingredients (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
    ingredient_id INTEGER REFERENCES ingredients(id) ON DELETE CASCADE,
    quantity DECIMAL(10,3) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- StockMovements tablosu
CREATE TABLE IF NOT EXISTS stock_movements (
    id SERIAL PRIMARY KEY,
    ingredient_id INTEGER REFERENCES ingredients(id),
    movement_type VARCHAR(20) NOT NULL, -- in, out, adjustment
    quantity DECIMAL(10,3) NOT NULL,
    reason VARCHAR(100),
    reference_id INTEGER, -- sipariş ID veya diğer referans
    reference_type VARCHAR(20), -- order, manual, purchase
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- MÜŞTERİ YÖNETİMİ
-- =====================================================

-- Customers tablosu
CREATE TABLE IF NOT EXISTS customers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    email VARCHAR(100),
    address TEXT,
    birth_date DATE,
    total_orders INTEGER DEFAULT 0,
    total_spent DECIMAL(10,2) DEFAULT 0,
    loyalty_points INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- RAPORLAMA VE İSTATİSTİKLER
-- =====================================================

-- DailySales tablosu
CREATE TABLE IF NOT EXISTS daily_sales (
    id SERIAL PRIMARY KEY,
    sale_date DATE NOT NULL,
    total_orders INTEGER DEFAULT 0,
    total_revenue DECIMAL(10,2) DEFAULT 0,
    total_tax DECIMAL(10,2) DEFAULT 0,
    total_discount DECIMAL(10,2) DEFAULT 0,
    average_order_value DECIMAL(10,2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- AYARLAR VE KONFİGÜRASYON
-- =====================================================

-- Settings tablosu
CREATE TABLE IF NOT EXISTS settings (
    id SERIAL PRIMARY KEY,
    setting_key VARCHAR(100) UNIQUE NOT NULL,
    setting_value TEXT,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- TRIGGER FONKSİYONLARI
-- =====================================================

-- Fatura kodu oluşturma fonksiyonu
CREATE OR REPLACE FUNCTION generate_fatura_kodu(p_table_id INTEGER)
RETURNS VARCHAR(20) AS $$
DECLARE
    table_name VARCHAR(50);
    current_date_str VARCHAR(8);
    sequence_number INTEGER;
    fatura_kodu VARCHAR(20);
BEGIN
    -- Masa adını al
    SELECT name INTO table_name FROM tables WHERE id = p_table_id;
    
    -- Bugünün tarihini al (YYYYMMDD formatında)
    current_date_str := TO_CHAR(CURRENT_DATE, 'YYYYMMDD');
    
    -- Bugün bu masa için kaç sipariş var
    SELECT COALESCE(COUNT(*), 0) + 1 INTO sequence_number
    FROM orders 
    WHERE table_id = p_table_id 
    AND DATE(created_at) = CURRENT_DATE;
    
    -- Fatura kodunu oluştur: TABLO_ADI + TARIH + SIRA_NO
    fatura_kodu := table_name || current_date_str || LPAD(sequence_number::TEXT, 3, '0');
    
    RETURN fatura_kodu;
END;
$$ LANGUAGE plpgsql;

-- Fatura kodu otomatik oluşturma trigger fonksiyonu
CREATE OR REPLACE FUNCTION set_fatura_kodu()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.fatura_kodu IS NULL THEN
        NEW.fatura_kodu := generate_fatura_kodu(NEW.table_id);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- UpdatedAt trigger fonksiyonu
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger'ları oluştur
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_regions_updated_at BEFORE UPDATE ON regions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tables_updated_at BEFORE UPDATE ON tables
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_categories_updated_at BEFORE UPDATE ON categories
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_products_updated_at BEFORE UPDATE ON products
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_orders_updated_at BEFORE UPDATE ON orders
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER set_orders_fatura_kodu BEFORE INSERT ON orders
    FOR EACH ROW EXECUTE FUNCTION set_fatura_kodu();

CREATE TRIGGER update_order_items_updated_at BEFORE UPDATE ON order_items
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_reservations_updated_at BEFORE UPDATE ON reservations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_ingredients_updated_at BEFORE UPDATE ON ingredients
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_customers_updated_at BEFORE UPDATE ON customers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_settings_updated_at BEFORE UPDATE ON settings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- TEST VERİLERİ
-- =====================================================

-- Test kullanıcıları ekle
INSERT INTO users (username, password, role, email, first_name, last_name) VALUES
('admin', 'admin123', 'admin', 'admin@exfin.com', 'Admin', 'User'),
('manager', 'password', 'manager', 'manager@exfin.com', 'Manager', 'User'),
('cashier', 'password', 'cashier', 'cashier@exfin.com', 'Cashier', 'User'),
('waiter', 'password', 'waiter', 'waiter@exfin.com', 'Waiter', 'User'),
('kitchen', 'password', 'kitchen', 'kitchen@exfin.com', 'Kitchen', 'Staff'),
('guest', 'password', 'guest', 'guest@exfin.com', 'Guest', 'User')
ON CONFLICT (username) DO NOTHING;

-- Bölgeleri ekle
INSERT INTO regions (name, description) VALUES
('Bahçe', 'Dış mekan bahçe bölgesi'),
('İç Mekan', 'Ana salon iç mekan bölgesi'),
('Teras', 'Üst kat teras bölgesi'),
('Bar', 'Bar ve içecek bölgesi'),
('Özel Bölüm', 'VIP ve özel bölümler')
ON CONFLICT DO NOTHING;

-- Kategorileri ekle (Çok Dilli)
INSERT INTO categories (name, name_en, name_ar, name_ku, name_sr, description, description_en, description_ar, description_ku, description_sr, icon, color, sort_order, is_featured) VALUES
-- İçecekler
('İçecekler', 'Beverages', 'مشروبات', 'Şerab', 'شەراب', 'Soğuk ve sıcak içecekler', 'Cold and hot beverages', 'مشروبات باردة وساخنة', 'Şerabên sar û germ', 'شەرابە سارد و گەرمەکان', 'local_drink', '#2196F3', 1, true),
('Kahve & Çay', 'Coffee & Tea', 'قهوة وشاي', 'Qehwe û Çay', 'قەهوە و چای', 'Sıcak içecekler', 'Hot beverages', 'مشروبات ساخنة', 'Şerabên germ', 'شەرابە گەرمەکان', 'coffee', '#795548', 2, true),
('Alkollü İçecekler', 'Alcoholic Beverages', 'مشروبات كحولية', 'Şerabên Alkolî', 'شەرابە ئەلکۆلییەکان', 'Bira, şarap ve kokteyl', 'Beer, wine and cocktails', 'بيرة ونبيذ وكوكتيل', 'Bîra, mey û kokteyl', 'بیرە و مەی و کۆکتەیل', 'local_bar', '#8BC34A', 3, false),

-- Başlangıçlar
('Çorbalar', 'Soups', 'حساء', 'Şorba', 'شۆربا', 'Sıcak ve soğuk çorbalar', 'Hot and cold soups', 'حساء ساخن وبارد', 'Şorba germ û sar', 'شۆربای گەرم و سارد', 'soup_kitchen', '#FF9800', 4, true),
('Salatalar', 'Salads', 'سلطات', 'Salata', 'سەلاتە', 'Taze salatalar', 'Fresh salads', 'سلطات طازجة', 'Salata taze', 'سەلاتەی تازە', 'eco', '#4CAF50', 5, true),
('Mezeler', 'Appetizers', 'مقبلات', 'Meze', 'مەزە', 'Geleneksel mezeler', 'Traditional appetizers', 'مقبلات تقليدية', 'Mezeyên kevneşopî', 'مەزەی کۆنەپارێز', 'tapas', '#9C27B0', 6, true),

-- Ana Yemekler
('Türk Mutfağı', 'Turkish Cuisine', 'المطبخ التركي', 'Pêjgeha Tirkî', 'پێشگەی تورکی', 'Geleneksel Türk yemekleri', 'Traditional Turkish dishes', 'أطباق تركية تقليدية', 'Xwarinên kevneşopî yên Tirkî', 'خواردنە کۆنەپارێزە تورکییەکان', 'restaurant', '#E91E63', 7, true),
('İtalyan Mutfağı', 'Italian Cuisine', 'المطبخ الإيطالي', 'Pêjgeha Îtalî', 'پێشگەی ئیتاڵی', 'İtalyan yemekleri', 'Italian dishes', 'أطباق إيطالية', 'Xwarinên Îtalî', 'خواردنە ئیتاڵییەکان', 'pizza', '#F44336', 8, true),
('Çin Mutfağı', 'Chinese Cuisine', 'المطبخ الصيني', 'Pêjgeha Çînî', 'پێشگەی چینی', 'Çin yemekleri', 'Chinese dishes', 'أطباق صينية', 'Xwarinên Çînî', 'خواردنە چینییەکان', 'ramen_dining', '#FF5722', 9, true),
('Hint Mutfağı', 'Indian Cuisine', 'المطبخ الهندي', 'Pêjgeha Hindî', 'پێشگەی هیندی', 'Hint yemekleri', 'Indian dishes', 'أطباق هندية', 'Xwarinên Hindî', 'خواردنە هیندییەکان', 'curry', '#FF9800', 10, true),
('Japon Mutfağı', 'Japanese Cuisine', 'المطبخ الياباني', 'Pêjgeha Japonî', 'پێشگەی ژاپۆنی', 'Japon yemekleri', 'Japanese dishes', 'أطباق يابانية', 'Xwarinên Japonî', 'خواردنە ژاپۆنییەکان', 'sushi', '#3F51B5', 11, true),
('Meksika Mutfağı', 'Mexican Cuisine', 'المطبخ المكسيكي', 'Pêjgeha Meksîkî', 'پێشگەی مەکسیکی', 'Meksika yemekleri', 'Mexican dishes', 'أطباق مكسيكية', 'Xwarinên Meksîkî', 'خواردنە مەکسیکییەکان', 'taco', '#4CAF50', 12, true),
('Fransız Mutfağı', 'French Cuisine', 'المطبخ الفرنسي', 'Pêjgeha Fransî', 'پێشگەی فەرەنسی', 'Fransız yemekleri', 'French dishes', 'أطباق فرنسية', 'Xwarinên Fransî', 'خواردنە فەرەنسییەکان', 'bakery_dining', '#9C27B0', 13, true),
('Amerikan Mutfağı', 'American Cuisine', 'المطبخ الأمريكي', 'Pêjgeha Amerîkî', 'پێشگەی ئەمریکی', 'Amerikan yemekleri', 'American dishes', 'أطباق أمريكية', 'Xwarinên Amerîkî', 'خواردنە ئەمریکییەکان', 'fastfood', '#607D8B', 14, true),
('Arap Mutfağı', 'Arabic Cuisine', 'المطبخ العربي', 'Pêjgeha Erebî', 'پێشگەی عەرەبی', 'Arap yemekleri', 'Arabic dishes', 'أطباق عربية', 'Xwarinên Erebî', 'خواردنە عەرەبییەکان', 'kebab_dining', '#795548', 15, true),
('Yunan Mutfağı', 'Greek Cuisine', 'المطبخ اليوناني', 'Pêjgeha Yewnanî', 'پێشگەی یۆنانی', 'Yunan yemekleri', 'Greek dishes', 'أطباق يونانية', 'Xwarinên Yewnanî', 'خواردنە یۆنانییەکان', 'mediterranean', '#00BCD4', 16, true),

-- Özel Kategoriler
('Deniz Ürünleri', 'Seafood', 'مأكولات بحرية', 'Xwarinên Deryayî', 'خواردنە دەریایییەکان', 'Balık ve deniz ürünleri', 'Fish and seafood', 'أسماك ومأكولات بحرية', 'Masî û xwarinên deryayî', 'ماسی و خواردنە دەریایییەکان', 'set_meal', '#03A9F4', 17, true),
('Vejetaryen', 'Vegetarian', 'نباتي', 'Giyanî', 'گیانی', 'Vejetaryen yemekler', 'Vegetarian dishes', 'أطباق نباتية', 'Xwarinên giyanî', 'خواردنە گیانییەکان', 'eco', '#8BC34A', 18, true),
('Vegan', 'Vegan', 'نباتي صرف', 'Giyanî Saf', 'گیانی ساف', 'Vegan yemekler', 'Vegan dishes', 'أطباق نباتية صرفة', 'Xwarinên giyanî saf', 'خواردنە گیانی سافەکان', 'grass', '#4CAF50', 19, false),
('Glutensiz', 'Gluten Free', 'خالي من الغلوتين', 'Bê Gluten', 'بێ گلوتن', 'Glutensiz yemekler', 'Gluten free dishes', 'أطباق خالية من الغلوتين', 'Xwarinên bê gluten', 'خواردنە بێ گلوتنەکان', 'no_food', '#FF9800', 20, false),

-- Tatlılar
('Tatlılar', 'Desserts', 'حلويات', 'Şîrînî', 'شیرینی', 'Tatlı ve dondurma çeşitleri', 'Desserts and ice cream', 'حلويات وآيس كريم', 'Şîrînî û dondurma', 'شیرینی و دۆندوورما', 'cake', '#E91E63', 21, true),
('Dondurma', 'Ice Cream', 'آيس كريم', 'Dondurma', 'دۆندوورما', 'Dondurma çeşitleri', 'Ice cream varieties', 'أنواع الآيس كريم', 'Cureyên dondurmayê', 'جۆرەکانی دۆندوورما', 'icecream', '#2196F3', 22, true),

-- Kahvaltı
('Kahvaltı', 'Breakfast', 'فطور', 'Taştê', 'تاشتێ', 'Kahvaltı menüsü', 'Breakfast menu', 'قائمة الفطور', 'Menuyê taştêyê', 'مێنیوی تاشتێ', 'breakfast_dining', '#FFC107', 23, true),

-- Fast Food
('Pizzalar', 'Pizzas', 'بيتزا', 'Pîzza', 'پیتزا', 'Çeşitli pizza türleri', 'Various pizza types', 'أنواع البيتزا', 'Cureyên pîzzayê', 'جۆرەکانی پیتزا', 'local_pizza', '#F44336', 24, true),
('Burgerler', 'Burgers', 'برغر', 'Burger', 'بۆرگەر', 'Hamburger çeşitleri', 'Hamburger varieties', 'أنواع البرغر', 'Cureyên burgerê', 'جۆرەکانی بۆرگەر', 'lunch_dining', '#FF5722', 25, true),
('Sandviçler', 'Sandwiches', 'سندويتش', 'Sandwîç', 'ساندویچ', 'Sandviç çeşitleri', 'Sandwich varieties', 'أنواع السندويتش', 'Cureyên sandwîçê', 'جۆرەکانی ساندویچ', 'bakery_dining', '#795548', 26, true),

-- Özel Menüler
('Şef Özel', 'Chef Special', 'خاص الشيف', 'Taybetiya Şef', 'تایبەتی شێف', 'Şef özel yemekleri', 'Chef special dishes', 'أطباق خاصة بالشيف', 'Xwarinên taybet ên şef', 'خواردنە تایبەتەکانی شێف', 'star', '#FFD700', 27, true),
('Çocuk Menüsü', 'Kids Menu', 'قائمة الأطفال', 'Menuyê Zarokan', 'مێنیوی منداڵان', 'Çocuklar için özel menü', 'Special menu for kids', 'قائمة خاصة للأطفال', 'Menuyê taybet ji bo zarokan', 'مێنیوی تایبەت بۆ منداڵان', 'child_care', '#FF9800', 28, false)
ON CONFLICT DO NOTHING;

-- Ürünleri ekle (Çok Dilli - İçecekler)
INSERT INTO products (name, name_en, name_ar, name_ku, name_sr, description, description_en, description_ar, description_ku, description_sr, price, category_id, spice_level, is_vegetarian, is_vegan, is_gluten_free, is_cold, calories, origin_country, popular) VALUES
-- İçecekler (Kategori 1)
('Coca Cola', 'Coca Cola', 'كوكا كولا', 'Coca Cola', 'کۆکا کۆلا', '330ml Coca Cola', '330ml Coca Cola', 'كوكا كولا 330 مل', 'Coca Cola 330ml', 'کۆکا کۆلای 330 مل', 15.00, 1, 0, true, true, true, true, 140, 'USA', true),
('Pepsi', 'Pepsi', 'بيبسي', 'Pepsi', 'پێپسی', '330ml Pepsi', '330ml Pepsi', 'بيبسي 330 مل', 'Pepsi 330ml', 'پێپسی 330 مل', 15.00, 1, 0, true, true, true, true, 150, 'USA', true),
('Fanta', 'Fanta', 'فانتا', 'Fanta', 'فانتا', '330ml Fanta Portakal', '330ml Fanta Orange', 'فانتا برتقال 330 مل', 'Fanta Porteqal 330ml', 'فانتای پرتەقاڵی 330 مل', 15.00, 1, 0, true, true, true, true, 160, 'Germany', true),
('Sprite', 'Sprite', 'سبرايت', 'Sprite', 'سپرایت', '330ml Sprite', '330ml Sprite', 'سبرايت 330 مل', 'Sprite 330ml', 'سپرایتی 330 مل', 15.00, 1, 0, true, true, true, true, 140, 'USA', true),
('Ayran', 'Ayran', 'عيران', 'Ayrûn', 'ئەیران', '500ml Taze Ayran', '500ml Fresh Ayran', 'عيران طازج 500 مل', 'Ayrûn taze 500ml', 'ئەیرانی تازەی 500 مل', 12.00, 1, 0, true, true, true, true, 60, 'Turkey', true),
('Su', 'Water', 'ماء', 'Av', 'ئاو', '500ml Doğal Su', '500ml Natural Water', 'ماء طبيعي 500 مل', 'Av xwezayî 500ml', 'ئاوی سروشتی 500 مل', 5.00, 1, 0, true, true, true, true, 0, 'Turkey', true),
('Meyve Suyu', 'Fruit Juice', 'عصير فواكه', 'Şîrê Mêweyan', 'شیری میوەکان', '250ml Karışık Meyve Suyu', '250ml Mixed Fruit Juice', 'عصير فواكه مختلط 250 مل', 'Şîrê mêweyan tevlihev 250ml', 'شیری میوە تێکەڵەکان 250 مل', 18.00, 1, 0, true, true, true, true, 120, 'Turkey', true),
('Limonata', 'Lemonade', 'ليموناضة', 'Lîmonata', 'لیمۆناتە', '300ml Taze Limonata', '300ml Fresh Lemonade', 'ليموناضة طازجة 300 مل', 'Lîmonata taze 300ml', 'لیمۆناتەی تازەی 300 مل', 20.00, 1, 0, true, true, true, true, 90, 'Turkey', true)
ON CONFLICT DO NOTHING;

-- Kahve & Çay (Kategori 2)
INSERT INTO products (name, name_en, name_ar, name_ku, name_sr, description, description_en, description_ar, description_ku, description_sr, price, category_id, spice_level, is_vegetarian, is_vegan, is_gluten_free, is_hot, calories, origin_country, popular) VALUES
('Türk Kahvesi', 'Turkish Coffee', 'قهوة تركية', 'Qehweya Tirkî', 'قەهوەی تورکی', 'Geleneksel Türk Kahvesi', 'Traditional Turkish Coffee', 'قهوة تركية تقليدية', 'Qehweya kevneşopî ya Tirkî', 'قەهوەی کۆنەپارێزی تورکی', 12.00, 2, 0, true, true, true, true, 5, 'Turkey', true),
('Espresso', 'Espresso', 'اسبريسو', 'Espresso', 'ئێسپرێسۆ', 'Tek Shot Espresso', 'Single Shot Espresso', 'اسبريسو شوت واحد', 'Espresso tek shot', 'ئێسپرێسۆی تەک شۆت', 15.00, 2, 0, true, true, true, true, 5, 'Italy', true),
('Cappuccino', 'Cappuccino', 'كابتشينو', 'Cappuccino', 'کاپۆچینۆ', 'Espresso, Süt, Süt Köpüğü', 'Espresso, Milk, Milk Foam', 'اسبريسو وحليب ورغوة الحليب', 'Espresso, şîr, kefşîr', 'ئێسپرێسۆ، شیر، کەفشیر', 18.00, 2, 0, true, true, true, true, 80, 'Italy', true),
('Latte', 'Latte', 'لاتيه', 'Latte', 'لاتە', 'Espresso ve Buharlanmış Süt', 'Espresso and Steamed Milk', 'اسبريسو وحليب مبخر', 'Espresso û şîrê biharî', 'ئێسپرێسۆ و شیری بەهار', 20.00, 2, 0, true, true, true, true, 120, 'Italy', true),
('Çay', 'Tea', 'شاي', 'Çay', 'چای', 'Sıcak Çay', 'Hot Tea', 'شاي ساخن', 'Çay germ', 'چای گەرم', 8.00, 2, 0, true, true, true, true, 2, 'Turkey', true),
('Yeşil Çay', 'Green Tea', 'شاي اخضر', 'Çaya Kesk', 'چای سەوز', 'Sıcak Yeşil Çay', 'Hot Green Tea', 'شاي اخضر ساخن', 'Çaya kesk germ', 'چای سەوزی گەرم', 10.00, 2, 0, true, true, true, true, 2, 'China', true),
('Nane Çayı', 'Mint Tea', 'شاي نعناع', 'Çaya Pûng', 'چای پوونگ', 'Sıcak Nane Çayı', 'Hot Mint Tea', 'شاي نعناع ساخن', 'Çaya pûng germ', 'چای پوونگی گەرم', 12.00, 2, 0, true, true, true, true, 3, 'Morocco', true),
('Ihlamur Çayı', 'Linden Tea', 'شاي زيزفون', 'Çaya Gulî', 'چای گوڵی', 'Sıcak Ihlamur Çayı', 'Hot Linden Tea', 'شاي زيزفون ساخن', 'Çaya gulî germ', 'چای گوڵی گەرم', 10.00, 2, 0, true, true, true, true, 2, 'Turkey', true)
ON CONFLICT DO NOTHING;

-- Türk Mutfağı (Kategori 7)
INSERT INTO products (name, name_en, name_ar, name_ku, name_sr, description, description_en, description_ar, description_ku, description_sr, price, category_id, spice_level, is_vegetarian, is_vegan, is_gluten_free, is_hot, calories, origin_country, popular, chef_special) VALUES
('İskender Döner', 'Iskender Doner', 'دونر اسكندر', 'Dönerê Îskender', 'دۆنەری ئیسکەندەر', 'Özel soslu et döner', 'Special sauce meat doner', 'دونر لحم بصلصة خاصة', 'Dönerê goştê bi sosê taybet', 'دۆنەری گۆشتی بە سۆسی تایبەت', 85.00, 7, 1, false, false, false, true, 650, 'Turkey', true, true),
('Adana Kebap', 'Adana Kebab', 'كباب أضنة', 'Kebaba Edene', 'کەبابی ئەدەنە', 'Acılı kıyma kebap', 'Spicy minced meat kebab', 'كباب لحم مفروم حار', 'Kebaba goştê hûrkirî ya tûj', 'کەبابی گۆشتی هەڵکوتراوەی تۆژ', 75.00, 7, 3, false, false, false, true, 580, 'Turkey', true, false),
('Urfa Kebap', 'Urfa Kebab', 'كباب أورفة', 'Kebaba Riha', 'کەبابی ڕەها', 'Az acılı kıyma kebap', 'Mild spicy minced meat kebab', 'كباب لحم مفروم خفيف', 'Kebaba goştê hûrkirî ya nerm', 'کەبابی گۆشتی هەڵکوتراوەی نەرم', 70.00, 7, 2, false, false, false, true, 550, 'Turkey', true, false),
('Tavuk Şiş', 'Chicken Shish', 'شيش دجاج', 'Şîşê Mirîşk', 'شیشی مریشک', 'Izgara tavuk şiş', 'Grilled chicken shish', 'شيش دجاج مشوي', 'Şîşê mirîşkê biraştî', 'شیشی مریشکی براژت', 65.00, 7, 1, false, false, false, true, 420, 'Turkey', true, false),
('Kuzu Pirzola', 'Lamb Chops', 'قطع لحم الضأن', 'Pirzolaya Berx', 'پیرزۆلای بەرز', 'Izgara kuzu pirzola', 'Grilled lamb chops', 'قطع لحم الضأن مشوية', 'Pirzolayên berxê biraştî', 'پیرزۆلای بەرزی براژت', 120.00, 7, 1, false, false, false, true, 680, 'Turkey', true, true),
('Mantı', 'Manti', 'منتو', 'Mantî', 'مانتی', 'El açması mantı', 'Hand-rolled manti', 'منتو يدوي', 'Mantî destan', 'مانتی دەستە', 45.00, 7, 0, false, false, false, true, 380, 'Turkey', true, false),
('Lahmacun', 'Lahmacun', 'لحم بعجين', 'Lahmacûn', 'لەحمەجون', 'İnce hamur üzerine kıyma', 'Minced meat on thin dough', 'لحم مفروم على عجين رقيق', 'Goştê hûrkirî li ser hevîrê tenik', 'گۆشتی هەڵکوتراوە لەسەر هەویری تەنک', 25.00, 7, 1, false, false, false, true, 320, 'Turkey', true, false),
('Pide', 'Pide', 'بيضة', 'Pîde', 'پیدە', 'Türk pizzası', 'Turkish pizza', 'بيتزا تركية', 'Pîzzaya Tirkî', 'پیتزای تورکی', 35.00, 7, 0, false, false, false, true, 450, 'Turkey', true, false),
('Karnıyarık', 'Karniyarik', 'كرني يارك', 'Karniyarîk', 'کارنیارک', 'Patlıcan dolması', 'Stuffed eggplant', 'باذنجان محشي', 'Bacanaşê tije', 'باژەنگانی پڕکراوە', 40.00, 7, 1, true, false, false, true, 280, 'Turkey', true, false),
('İmambayıldı', 'Imam Bayildi', 'إمام بايلدي', 'Îmam Bayildî', 'ئیمام بەیڵدی', 'Soğanlı patlıcan', 'Eggplant with onions', 'باذنجان بالبصل', 'Bacanaş bi pîvaz', 'باژەنگان بە پیاز', 35.00, 7, 0, true, true, false, true, 220, 'Turkey', true, false)
ON CONFLICT DO NOTHING;

-- İtalyan Mutfağı (Kategori 8)
INSERT INTO products (name, name_en, name_ar, name_ku, name_sr, description, description_en, description_ar, description_ku, description_sr, price, category_id, spice_level, is_vegetarian, is_vegan, is_gluten_free, is_hot, calories, origin_country, popular, chef_special) VALUES
('Spaghetti Carbonara', 'Spaghetti Carbonara', 'سباغيتي كاربونارا', 'Spaghetti Carbonara', 'سپاگێتی کاربۆنارا', 'Yumurta, peynir, pastırma soslu makarna', 'Pasta with egg, cheese, bacon sauce', 'معكرونة بالبيض والجبن ولحم الخنزير', 'Makarnaya bi hêlke, penîr û sosê pastîrmayê', 'ماکارۆنای بە هێلکە، پەنیر و سۆسی پاسترما', 75.00, 8, 1, false, false, false, true, 650, 'Italy', true, true),
('Penne Arrabbiata', 'Penne Arrabbiata', 'بيني أرابياتا', 'Penne Arrabbiata', 'پێنەی ئەرەبیاتا', 'Acılı domates soslu makarna', 'Spicy tomato sauce pasta', 'معكرونة بصلصة طماطم حارة', 'Makarnaya bi sosê bacanaşê tûj', 'ماکارۆنای بە سۆسی باژەنگە تۆژ', 65.00, 8, 3, true, true, false, true, 480, 'Italy', true, false),
('Risotto ai Funghi', 'Mushroom Risotto', 'ريسوتو بالفطر', 'Risotto bi Kûvark', 'ریسۆتۆ بە کەوەرک', 'Mantarlı risotto', 'Mushroom risotto', 'ريسوتو بالفطر', 'Risotto bi kûvark', 'ریسۆتۆ بە کەوەرک', 70.00, 8, 0, true, false, false, true, 420, 'Italy', true, false),
('Osso Buco', 'Osso Buco', 'أوسو بوكو', 'Osso Buco', 'ئۆسۆ بۆکۆ', 'Dana incik eti', 'Veal shank', 'لحم عجل', 'Goştê golikê', 'گۆشتی گۆلک', 95.00, 8, 1, false, false, false, true, 720, 'Italy', true, true),
('Tiramisu', 'Tiramisu', 'تيراميسو', 'Tiramisu', 'تیڕامیسو', 'İtalyan tatlısı', 'Italian dessert', 'حلويات إيطالية', 'Şîrînîya Îtalî', 'شیرینی ئیتاڵی', 45.00, 8, 0, true, false, false, false, 350, 'Italy', true, false),
('Bruschetta', 'Bruschetta', 'بروشيتا', 'Bruschetta', 'بڕۆشێتا', 'Domatesli ekmek', 'Tomato bread', 'خبز بالطماطم', 'Nan bi bacanaş', 'نان بە باژەنگ', 25.00, 8, 0, true, true, false, false, 180, 'Italy', true, false),
('Minestrone', 'Minestrone', 'مينسترون', 'Minestrone', 'مینەسترۆن', 'Sebze çorbası', 'Vegetable soup', 'حساء خضار', 'Şorbaya sebzeyan', 'شۆربای سەوزەوات', 35.00, 8, 0, true, true, false, true, 220, 'Italy', true, false),
('Gnocchi', 'Gnocchi', 'نيوكي', 'Gnocchi', 'نیۆکی', 'Patates hamuru', 'Potato dumplings', 'كراتون بطاطس', 'Hêlkeyên patatêsê', 'هێلکەی پەتاتە', 55.00, 8, 0, true, false, false, true, 380, 'Italy', true, false)
ON CONFLICT DO NOTHING;

-- Malzemeleri ekle
INSERT INTO ingredients (name, description, unit, current_stock, min_stock, max_stock, unit_price, supplier) VALUES
('Tavuk Eti', 'Taze tavuk eti', 'kg', 50.0, 10.0, 100.0, 45.00, 'Et Tedarikçisi'),
('Dana Eti', 'Taze dana eti', 'kg', 30.0, 5.0, 80.0, 120.00, 'Et Tedarikçisi'),
('Domates', 'Taze domates', 'kg', 25.0, 5.0, 50.0, 8.00, 'Sebze Tedarikçisi'),
('Soğan', 'Taze soğan', 'kg', 20.0, 3.0, 40.0, 4.00, 'Sebze Tedarikçisi'),
('Patates', 'Taze patates', 'kg', 40.0, 10.0, 80.0, 6.00, 'Sebze Tedarikçisi'),
('Pirinç', 'Beyaz pirinç', 'kg', 100.0, 20.0, 200.0, 15.00, 'Temel Gıda'),
('Un', 'Buğday unu', 'kg', 80.0, 15.0, 150.0, 8.00, 'Temel Gıda'),
('Yağ', 'Ayçiçek yağı', 'lt', 50.0, 10.0, 100.0, 25.00, 'Yağ Tedarikçisi'),
('Süt', 'Taze süt', 'lt', 30.0, 5.0, 60.0, 12.00, 'Süt Ürünleri'),
('Yumurta', 'Taze yumurta', 'adet', 500.0, 100.0, 1000.0, 2.50, 'Yumurta Tedarikçisi')
ON CONFLICT DO NOTHING;

-- Masaları sıfırla ve yeniden ekle
TRUNCATE TABLE tables RESTART IDENTITY CASCADE;

-- Her bölge için 20 masa ekle
INSERT INTO tables (name, capacity, status, location, region_id) VALUES
-- Bahçe Masaları (B01-B20)
('B01', 4, 'Available', 'Bahçe', 1),
('B02', 6, 'occupied', 'Bahçe', 1),
('B03', 4, 'Available', 'Bahçe', 1),
('B04', 8, 'Available', 'Bahçe', 1),
('B05', 6, 'reserved', 'Bahçe', 1),
('B06', 4, 'Available', 'Bahçe', 1),
('B07', 6, 'Available', 'Bahçe', 1),
('B08', 8, 'occupied', 'Bahçe', 1),
('B09', 4, 'Available', 'Bahçe', 1),
('B10', 6, 'Available', 'Bahçe', 1),
('B11', 4, 'reserved', 'Bahçe', 1),
('B12', 8, 'Available', 'Bahçe', 1),
('B13', 6, 'Available', 'Bahçe', 1),
('B14', 4, 'occupied', 'Bahçe', 1),
('B15', 6, 'Available', 'Bahçe', 1),
('B16', 8, 'Available', 'Bahçe', 1),
('B17', 4, 'reserved', 'Bahçe', 1),
('B18', 6, 'Available', 'Bahçe', 1),
('B19', 4, 'Available', 'Bahçe', 1),
('B20', 8, 'occupied', 'Bahçe', 1),

-- İç Mekan Masaları (I01-I20)
('I01', 4, 'Available', 'İç Mekan', 2),
('I02', 6, 'occupied', 'İç Mekan', 2),
('I03', 8, 'Available', 'İç Mekan', 2),
('I04', 4, 'reserved', 'İç Mekan', 2),
('I05', 6, 'Available', 'İç Mekan', 2),
('I06', 8, 'Available', 'İç Mekan', 2),
('I07', 4, 'occupied', 'İç Mekan', 2),
('I08', 6, 'Available', 'İç Mekan', 2),
('I09', 8, 'reserved', 'İç Mekan', 2),
('I10', 4, 'Available', 'İç Mekan', 2),
('I11', 6, 'Available', 'İç Mekan', 2),
('I12', 8, 'occupied', 'İç Mekan', 2),
('I13', 4, 'Available', 'İç Mekan', 2),
('I14', 6, 'reserved', 'İç Mekan', 2),
('I15', 8, 'Available', 'İç Mekan', 2),
('I16', 4, 'Available', 'İç Mekan', 2),
('I17', 6, 'occupied', 'İç Mekan', 2),
('I18', 8, 'Available', 'İç Mekan', 2),
('I19', 4, 'reserved', 'İç Mekan', 2),
('I20', 6, 'Available', 'İç Mekan', 2),

-- Teras Masaları (T01-T20)
('T01', 6, 'Available', 'Teras', 3),
('T02', 4, 'occupied', 'Teras', 3),
('T03', 8, 'Available', 'Teras', 3),
('T04', 6, 'reserved', 'Teras', 3),
('T05', 4, 'Available', 'Teras', 3),
('T06', 8, 'Available', 'Teras', 3),
('T07', 6, 'occupied', 'Teras', 3),
('T08', 4, 'Available', 'Teras', 3),
('T09', 8, 'reserved', 'Teras', 3),
('T10', 6, 'Available', 'Teras', 3),
('T11', 4, 'Available', 'Teras', 3),
('T12', 8, 'occupied', 'Teras', 3),
('T13', 6, 'Available', 'Teras', 3),
('T14', 4, 'reserved', 'Teras', 3),
('T15', 8, 'Available', 'Teras', 3),
('T16', 6, 'Available', 'Teras', 3),
('T17', 4, 'occupied', 'Teras', 3),
('T18', 8, 'Available', 'Teras', 3),
('T19', 6, 'reserved', 'Teras', 3),
('T20', 4, 'Available', 'Teras', 3),

-- Bar Masaları (BR01-BR20)
('BR01', 4, 'Available', 'Bar', 4),
('BR02', 6, 'occupied', 'Bar', 4),
('BR03', 8, 'Available', 'Bar', 4),
('BR04', 4, 'reserved', 'Bar', 4),
('BR05', 6, 'Available', 'Bar', 4),
('BR06', 8, 'Available', 'Bar', 4),
('BR07', 4, 'occupied', 'Bar', 4),
('BR08', 6, 'Available', 'Bar', 4),
('BR09', 8, 'reserved', 'Bar', 4),
('BR10', 4, 'Available', 'Bar', 4),
('BR11', 6, 'Available', 'Bar', 4),
('BR12', 8, 'occupied', 'Bar', 4),
('BR13', 4, 'Available', 'Bar', 4),
('BR14', 6, 'reserved', 'Bar', 4),
('BR15', 8, 'Available', 'Bar', 4),
('BR16', 4, 'Available', 'Bar', 4),
('BR17', 6, 'occupied', 'Bar', 4),
('BR18', 8, 'Available', 'Bar', 4),
('BR19', 4, 'reserved', 'Bar', 4),
('BR20', 6, 'Available', 'Bar', 4),

-- Özel Bölüm Masaları (O01-O20)
('O01', 8, 'Available', 'Özel Bölüm', 5),
('O02', 10, 'occupied', 'Özel Bölüm', 5),
('O03', 6, 'Available', 'Özel Bölüm', 5),
('O04', 8, 'reserved', 'Özel Bölüm', 5),
('O05', 10, 'Available', 'Özel Bölüm', 5),
('O06', 6, 'Available', 'Özel Bölüm', 5),
('O07', 8, 'occupied', 'Özel Bölüm', 5),
('O08', 10, 'Available', 'Özel Bölüm', 5),
('O09', 6, 'reserved', 'Özel Bölüm', 5),
('O10', 8, 'Available', 'Özel Bölüm', 5),
('O11', 10, 'Available', 'Özel Bölüm', 5),
('O12', 6, 'occupied', 'Özel Bölüm', 5),
('O13', 8, 'Available', 'Özel Bölüm', 5),
('O14', 10, 'reserved', 'Özel Bölüm', 5),
('O15', 6, 'Available', 'Özel Bölüm', 5),
('O16', 8, 'Available', 'Özel Bölüm', 5),
('O17', 10, 'occupied', 'Özel Bölüm', 5),
('O18', 6, 'Available', 'Özel Bölüm', 5),
('O19', 8, 'reserved', 'Özel Bölüm', 5),
('O20', 10, 'Available', 'Özel Bölüm', 5);

-- Test müşterileri ekle
INSERT INTO customers (name, phone, email, total_orders, total_spent, loyalty_points) VALUES
('Ahmet Yılmaz', '0532 123 4567', 'ahmet@email.com', 15, 1250.00, 125),
('Fatma Demir', '0533 234 5678', 'fatma@email.com', 8, 650.00, 65),
('Mehmet Kaya', '0534 345 6789', 'mehmet@email.com', 12, 980.00, 98),
('Ayşe Özkan', '0535 456 7890', 'ayse@email.com', 5, 420.00, 42),
('Ali Çelik', '0536 567 8901', 'ali@email.com', 20, 1800.00, 180)
ON CONFLICT DO NOTHING;

-- Test rezervasyonları ekle
INSERT INTO reservations (table_id, customer_name, customer_phone, reservation_date, reservation_time, party_size, status) VALUES
(1, 'Ahmet Yılmaz', '0532 123 4567', CURRENT_DATE + INTERVAL '1 day', '19:00:00', 4, 'confirmed'),
(5, 'Fatma Demir', '0533 234 5678', CURRENT_DATE + INTERVAL '2 days', '20:00:00', 6, 'confirmed'),
(10, 'Mehmet Kaya', '0534 345 6789', CURRENT_DATE, '18:30:00', 2, 'seated')
ON CONFLICT DO NOTHING;

-- Test siparişleri ekle (fatura kodu otomatik oluşturulacak)
INSERT INTO orders (table_id, waiter_id, customer_name, status, total_amount, final_amount, payment_method, payment_status) VALUES
(2, 4, 'Garson Siparişi', 'served', 150.00, 150.00, 'cash', 'paid'),
(6, 4, 'Garson Siparişi', 'preparing', 85.00, 85.00, 'card', 'pending'),
(15, 4, 'Garson Siparişi', 'confirmed', 220.00, 220.00, 'cash', 'pending')
ON CONFLICT DO NOTHING;

-- Test sipariş kalemleri ekle
INSERT INTO order_items (order_id, product_id, quantity, unit_price, total_price, status) VALUES
(1, 1, 2, 15.00, 30.00, 'served'),
(1, 6, 1, 25.00, 25.00, 'served'),
(1, 9, 1, 65.00, 65.00, 'served'),
(1, 15, 1, 25.00, 25.00, 'served'),
(2, 2, 1, 12.00, 12.00, 'preparing'),
(2, 7, 1, 30.00, 30.00, 'preparing'),
(2, 10, 1, 55.00, 55.00, 'preparing'),
(3, 3, 1, 8.00, 8.00, 'pending'),
(3, 8, 1, 35.00, 35.00, 'pending'),
(3, 11, 1, 120.00, 120.00, 'pending'),
(3, 16, 1, 45.00, 45.00, 'pending')
ON CONFLICT DO NOTHING;

-- Sistem ayarları ekle
INSERT INTO settings (setting_key, setting_value, description) VALUES
('restaurant_name', 'EXFIN Restaurant', 'Restoran adı'),
('tax_rate', '8.0', 'KDV oranı (%)'),
('currency', 'TL', 'Para birimi'),
('timezone', 'Europe/Istanbul', 'Zaman dilimi'),
('max_reservation_days', '30', 'Maksimum rezervasyon günü'),
('auto_table_status', 'true', 'Otomatik masa durumu güncelleme'),
('notification_enabled', 'true', 'Bildirim sistemi aktif'),
('backup_enabled', 'true', 'Otomatik yedekleme aktif')
ON CONFLICT (setting_key) DO NOTHING;

-- =====================================================
-- VERİ KONTROLÜ
-- =====================================================

-- Verileri kontrol et
SELECT 'Users' as table_name, COUNT(*) as count FROM users
UNION ALL
SELECT 'Regions' as table_name, COUNT(*) as count FROM regions
UNION ALL
SELECT 'Tables' as table_name, COUNT(*) as count FROM tables
UNION ALL
SELECT 'Categories' as table_name, COUNT(*) as count FROM categories
UNION ALL
SELECT 'Products' as table_name, COUNT(*) as count FROM products
UNION ALL
SELECT 'Ingredients' as table_name, COUNT(*) as count FROM ingredients
UNION ALL
SELECT 'Customers' as table_name, COUNT(*) as count FROM customers
UNION ALL
SELECT 'Orders' as table_name, COUNT(*) as count FROM orders
UNION ALL
SELECT 'OrderItems' as table_name, COUNT(*) as count FROM order_items
UNION ALL
SELECT 'Reservations' as table_name, COUNT(*) as count FROM reservations
UNION ALL
SELECT 'Settings' as table_name, COUNT(*) as count FROM settings;

-- Bölge bazında masa sayıları
SELECT r.name as region_name, COUNT(t.id) as table_count
FROM regions r
LEFT JOIN tables t ON r.id = t.region_id
WHERE r.is_active = true AND t.is_active = true
GROUP BY r.id, r.name
ORDER BY r.name;

-- Kategori bazında ürün sayıları
SELECT c.name as category_name, COUNT(p.id) as product_count
FROM categories c
LEFT JOIN products p ON c.id = p.category_id
WHERE c.is_active = true AND p.is_active = true
GROUP BY c.id, c.name
ORDER BY c.name;

-- Günlük satış raporu
SELECT 
    DATE(created_at) as sale_date,
    COUNT(*) as total_orders,
    SUM(final_amount) as total_revenue,
    AVG(final_amount) as average_order_value
FROM orders 
WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY DATE(created_at)
ORDER BY sale_date DESC; 