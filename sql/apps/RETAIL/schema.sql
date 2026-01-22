-- ============================================================================
-- ExRetailOS - UNIVERSAL CORE TABLES (v3.0)
-- ----------------------------------------------------------------------------
-- This file defines the core schema compatible with:
-- 1. PostgreSQL (Supabase / Local)
-- 2. Microsoft SQL Server (MSSQL)
-- ============================================================================

-- ============================================================================
-- SECTION 1: ORGANIZATION & SYSTEM
-- ============================================================================

-- 1.1 Stores / Warehouses
CREATE TABLE stores (
  id UUID PRIMARY KEY,
  code VARCHAR(50) NOT NULL UNIQUE,
  name VARCHAR(255) NOT NULL,
  type VARCHAR(50),
  city VARCHAR(100),
  region VARCHAR(100),
  address TEXT,
  phone VARCHAR(50),
  email VARCHAR(100),
  tax_office VARCHAR(100),
  tax_number VARCHAR(50),
  is_main BOOLEAN DEFAULT false,
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 1.2 Users
CREATE TABLE users (
  id UUID PRIMARY KEY,
  username VARCHAR(100) NOT NULL UNIQUE,
  email VARCHAR(255) UNIQUE,
  password_hash VARCHAR(255),
  full_name VARCHAR(255) NOT NULL,
  role VARCHAR(50) DEFAULT 'cashier',
  store_id UUID REFERENCES stores(id),
  phone VARCHAR(50),
  is_active BOOLEAN DEFAULT true,
  last_login_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
  auth_user_id UUID
);

-- 1.3 Modules & Navigation
CREATE TABLE modules (
  id UUID PRIMARY KEY,
  code VARCHAR(100) NOT NULL UNIQUE,
  name VARCHAR(255) NOT NULL,
  description TEXT,
  icon VARCHAR(100),
  parent_id UUID REFERENCES modules(id),
  sort_order INTEGER DEFAULT 0,
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE permissions (
  id UUID PRIMARY KEY,
  code VARCHAR(100) NOT NULL UNIQUE,
  name VARCHAR(255) NOT NULL,
  module_id UUID REFERENCES modules(id),
  description TEXT,
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE role_permissions (
  id UUID PRIMARY KEY,
  role VARCHAR(50) NOT NULL,
  permission_id UUID REFERENCES permissions(id) ON DELETE CASCADE,
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(role, permission_id)
);

-- ============================================================================
-- SECTION 2: PRODUCTS & INVENTORY
-- ============================================================================

-- 2.1 Brands
CREATE TABLE brands (
  id UUID PRIMARY KEY,
  code VARCHAR(50) NOT NULL UNIQUE,
  name VARCHAR(255) NOT NULL,
  description TEXT,
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 2.2 Product Groups
CREATE TABLE product_groups (
  id UUID PRIMARY KEY,
  code VARCHAR(50) NOT NULL UNIQUE,
  name VARCHAR(255) NOT NULL,
  description TEXT,
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 2.3 Units
CREATE TABLE units (
  id UUID PRIMARY KEY,
  code VARCHAR(20) NOT NULL UNIQUE,
  name VARCHAR(100) NOT NULL,
  description TEXT,
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 2.4 Tax Rates
CREATE TABLE tax_rates (
  id UUID PRIMARY KEY,
  rate DECIMAL(5,2) NOT NULL UNIQUE,
  description VARCHAR(255),
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 2.5 Categories
CREATE TABLE categories (
  id UUID PRIMARY KEY,
  code VARCHAR(50) NOT NULL UNIQUE,
  name VARCHAR(255) NOT NULL,
  parent_id UUID REFERENCES categories(id),
  level INTEGER DEFAULT 0,
  path TEXT,
  sort_order INTEGER DEFAULT 0,
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 2.6 Products
CREATE TABLE products (
  id UUID PRIMARY KEY,
  code VARCHAR(100),
  barcode VARCHAR(100) NOT NULL UNIQUE,
  name VARCHAR(255) NOT NULL,
  category_id UUID REFERENCES categories(id),
  brand_id UUID REFERENCES brands(id),
  group_id UUID REFERENCES product_groups(id),
  unit VARCHAR(50), -- Simple unit name for demo/backward compatibility
  unit_id UUID REFERENCES units(id),
  tax_rate_id UUID REFERENCES tax_rates(id),
  price DECIMAL(15,2) NOT NULL DEFAULT 0,
  cost DECIMAL(15,2) NOT NULL DEFAULT 0,
  stock INTEGER NOT NULL DEFAULT 0,
  min_stock INTEGER DEFAULT 0,
  max_stock INTEGER DEFAULT 0,
  has_variants BOOLEAN DEFAULT false,
  description TEXT,
  image_url VARCHAR(255),
  ozelkod1 VARCHAR(100),
  ozelkod2 VARCHAR(100),
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 2.3 Variants
CREATE TABLE product_variants (
  id UUID PRIMARY KEY,
  product_id UUID REFERENCES products(id) ON DELETE CASCADE,
  variant_name VARCHAR(255) NOT NULL,
  sku VARCHAR(100) UNIQUE,
  barcode VARCHAR(100) UNIQUE,
  attributes JSONB,
  price DECIMAL(15,2),
  cost DECIMAL(15,2),
  stock INTEGER DEFAULT 0,
  min_stock INTEGER DEFAULT 0,
  image_url VARCHAR(255),
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- SECTION 3: SALES & CUSTOMERS
-- ============================================================================

-- 3.1 Customers
CREATE TABLE customers (
  id UUID PRIMARY KEY,
  code VARCHAR(50) UNIQUE,
  name VARCHAR(255) NOT NULL,
  phone VARCHAR(50),
  email VARCHAR(255),
  address TEXT,
  city VARCHAR(100),
  points INTEGER DEFAULT 0,
  total_spent DECIMAL(15,2) DEFAULT 0,
  discount_rate DECIMAL(5,2) DEFAULT 0,
  customer_group VARCHAR(50),
  customer_type VARCHAR(50) DEFAULT 'retail',
  credit_limit DECIMAL(15,2) DEFAULT 0,
  balance DECIMAL(15,2) DEFAULT 0,
  tax_number VARCHAR(50),
  tax_office VARCHAR(100),
  is_active BOOLEAN DEFAULT true,
  notes TEXT,
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 3.2 Sales
CREATE TABLE sales (
  id UUID PRIMARY KEY,
  sale_number VARCHAR(100) NOT NULL UNIQUE,
  customer_id UUID REFERENCES customers(id) ON DELETE SET NULL,
  store_id UUID REFERENCES stores(id) ON DELETE SET NULL,
  cashier VARCHAR(100),
  user_id UUID REFERENCES users(id),
  subtotal DECIMAL(15,2) NOT NULL DEFAULT 0,
  discount DECIMAL(15,2) DEFAULT 0,
  tax DECIMAL(15,2) DEFAULT 0,
  total DECIMAL(15,2) NOT NULL DEFAULT 0,
  payment_method VARCHAR(50),
  status VARCHAR(50) DEFAULT 'completed',
  notes TEXT,
  date TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE sale_items (
  id UUID PRIMARY KEY,
  sale_id UUID REFERENCES sales(id) ON DELETE CASCADE,
  product_id UUID REFERENCES products(id),
  variant_id UUID REFERENCES product_variants(id),
  product_name VARCHAR(255) NOT NULL,
  product_barcode VARCHAR(100),
  quantity INTEGER NOT NULL,
  price DECIMAL(15,2) NOT NULL,
  discount DECIMAL(15,2) DEFAULT 0,
  tax DECIMAL(15,2) DEFAULT 0,
  total DECIMAL(15,2) NOT NULL,
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- SECTION 4: ENTERPRISE ACCOUNTING (LOGO STYLE)
-- ============================================================================

-- 4.1 Master Definitions (CAPI)
CREATE TABLE ROS_CAPIFIRM (
  logicalref INTEGER PRIMARY KEY,
  nr SMALLINT NOT NULL UNIQUE,
  name VARCHAR(255),
  title VARCHAR(255),
  street VARCHAR(255),
  city VARCHAR(100),
  country VARCHAR(100),
  taxoff VARCHAR(100),
  taxnr VARCHAR(50),
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE ROS_CAPIPERIOD (
  logicalref INTEGER PRIMARY KEY,
  firmnr SMALLINT NOT NULL,
  nr SMALLINT NOT NULL,
  begdate DATE,
  enddate DATE,
  active SMALLINT DEFAULT 0,
  UNIQUE(firmnr, nr)
);

-- Note: Static definitions for CAPI tables found in shared logic
CREATE TABLE FN_CAPIFIRM (
  logicalref INTEGER PRIMARY KEY,
  nr SMALLINT NOT NULL UNIQUE,
  name VARCHAR(255),
  title VARCHAR(255)
);

-- ============================================================================
-- SECTION 5: CURRENCY & FINANCE
-- ============================================================================

-- 5.1 Multi-Currency System
CREATE TABLE currencies (
  id UUID PRIMARY KEY,
  code VARCHAR(10) NOT NULL UNIQUE,
  name VARCHAR(100) NOT NULL,
  symbol VARCHAR(10),
  precision INTEGER DEFAULT 2,
  thousands_sep VARCHAR(5) DEFAULT '.',
  decimal_sep VARCHAR(5) DEFAULT ',',
  exchange_rate DECIMAL(18,6) DEFAULT 1.0000,
  is_base_currency BOOLEAN DEFAULT false,
  is_active BOOLEAN DEFAULT true,
  sort_order INTEGER DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE currency_rates (
  id UUID PRIMARY KEY,
  date DATE NOT NULL,
  currency_code VARCHAR(10) NOT NULL,
  buying_rate DECIMAL(18,6) NOT NULL,
  selling_rate DECIMAL(18,6) NOT NULL,
  effective_buying DECIMAL(18,6),
  effective_selling DECIMAL(18,6),
  source VARCHAR(50) DEFAULT 'manual',
  is_approved BOOLEAN DEFAULT false,
  approved_by_user VARCHAR(100),
  approved_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (date, currency_code)
);

CREATE TABLE currency_rates_history (
  id UUID PRIMARY KEY,
  rate_id UUID REFERENCES currency_rates(id) ON DELETE CASCADE,
  old_buying DECIMAL(18,6),
  new_buying DECIMAL(18,6),
  old_selling DECIMAL(18,6),
  new_selling DECIMAL(18,6),
  changed_by UUID REFERENCES users(id),
  change_reason TEXT,
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- SECTION 6: PURCHASES & SUPPLIERS
-- ============================================================================

-- 6.1 Suppliers
CREATE TABLE suppliers (
  id UUID PRIMARY KEY,
  code VARCHAR(50) UNIQUE,
  name VARCHAR(255) NOT NULL,
  phone VARCHAR(50),
  email VARCHAR(255),
  address TEXT,
  city VARCHAR(100),
  payment_terms INTEGER DEFAULT 30,
  credit_limit DECIMAL(15,2) DEFAULT 0,
  balance DECIMAL(15,2) DEFAULT 0,
  tax_number VARCHAR(50),
  tax_office VARCHAR(100),
  is_active BOOLEAN DEFAULT true,
  notes TEXT,
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 6.2 Purchases
CREATE TABLE purchases (
  id UUID PRIMARY KEY,
  purchase_number VARCHAR(100) NOT NULL UNIQUE,
  supplier_id UUID REFERENCES suppliers(id) ON DELETE SET NULL,
  store_id UUID REFERENCES stores(id) ON DELETE SET NULL,
  subtotal DECIMAL(15,2) NOT NULL DEFAULT 0,
  discount DECIMAL(15,2) DEFAULT 0,
  tax DECIMAL(15,2) DEFAULT 0,
  total DECIMAL(15,2) NOT NULL DEFAULT 0,
  payment_method VARCHAR(50),
  status VARCHAR(50) DEFAULT 'completed',
  notes TEXT,
  date TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE purchase_items (
  id UUID PRIMARY KEY,
  purchase_id UUID REFERENCES purchases(id) ON DELETE CASCADE,
  product_id UUID REFERENCES products(id),
  product_name VARCHAR(255) NOT NULL,
  product_barcode VARCHAR(100),
  quantity INTEGER NOT NULL,
  cost DECIMAL(15,2) NOT NULL,
  total DECIMAL(15,2) NOT NULL,
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- SECTION 7: STOCK MANAGEMENT
-- ============================================================================

-- 7.1 Stock Movements
CREATE TABLE stock_movements (
  id UUID PRIMARY KEY,
  movement_no VARCHAR(100) NOT NULL UNIQUE,
  product_id UUID REFERENCES products(id),
  variant_id UUID REFERENCES product_variants(id),
  store_id UUID REFERENCES stores(id),
  movement_type VARCHAR(50) NOT NULL, -- IN, OUT, TRANSFER, ADJUSTMENT
  quantity INTEGER NOT NULL,
  reference_no VARCHAR(100),
  reference_type VARCHAR(50),
  notes TEXT,
  date TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 7.2 Stock Counts
CREATE TABLE stock_counts (
  id UUID PRIMARY KEY,
  count_no VARCHAR(100) NOT NULL UNIQUE,
  store_id UUID REFERENCES stores(id),
  status VARCHAR(50) DEFAULT 'draft',
  counted_by UUID REFERENCES users(id),
  approved_by UUID REFERENCES users(id),
  count_date TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
  approved_date TIMESTAMPTZ,
  notes TEXT,
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE stock_count_details (
  id UUID PRIMARY KEY,
  count_id UUID REFERENCES stock_counts(id) ON DELETE CASCADE,
  product_id UUID REFERENCES products(id),
  variant_id UUID REFERENCES product_variants(id),
  system_qty INTEGER NOT NULL,
  counted_qty INTEGER NOT NULL,
  difference INTEGER NOT NULL,
  notes TEXT,
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- SECTION 8: TRANSFERS
-- ============================================================================

CREATE TABLE transfers (
  id UUID PRIMARY KEY,
  transfer_number VARCHAR(100) NOT NULL UNIQUE,
  from_store_id UUID REFERENCES stores(id),
  to_store_id UUID REFERENCES stores(id),
  status VARCHAR(50) DEFAULT 'pending',
  notes TEXT,
  date TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE transfer_items (
  id UUID PRIMARY KEY,
  transfer_id UUID REFERENCES transfers(id) ON DELETE CASCADE,
  product_id UUID REFERENCES products(id),
  variant_id UUID REFERENCES product_variants(id),
  product_code VARCHAR(100),
  product_name VARCHAR(255) NOT NULL,
  quantity INTEGER NOT NULL,
  unit_cost DECIMAL(15,2),
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- SECTION 9: CAMPAIGNS & DISCOUNTS
-- ============================================================================

CREATE TABLE campaigns (
  id UUID PRIMARY KEY,
  code VARCHAR(100) UNIQUE,
  name VARCHAR(255) NOT NULL,
  description TEXT,
  campaign_type VARCHAR(50) NOT NULL, -- buy_x_get_y, percentage_off, fixed_amount_off
  discount_type VARCHAR(50), -- percentage, amount
  discount_value DECIMAL(10,2),
  priority INTEGER DEFAULT 0,
  conditions JSONB, -- Custom logic for campaign application (e.g. min_qty, max_uses)
  applicable_products JSONB, -- List of product IDs or categories
  min_purchase_amount DECIMAL(15,2),
  start_date TIMESTAMPTZ,
  end_date TIMESTAMPTZ,
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE campaign_products (
  id UUID PRIMARY KEY,
  campaign_id UUID REFERENCES campaigns(id) ON DELETE CASCADE,
  product_id UUID REFERENCES products(id) ON DELETE CASCADE,
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(campaign_id, product_id)
);

-- 9.4 Discount Logs
CREATE TABLE discount_logs (
  id UUID PRIMARY KEY,
  sale_id UUID REFERENCES sales(id),
  product_id UUID REFERENCES products(id),
  campaign_id UUID REFERENCES campaigns(id),
  discount_amount DECIMAL(15,2) NOT NULL,
  reason TEXT,
  approved_by UUID REFERENCES users(id),
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- SECTION 10: NOTIFICATIONS & MESSAGING
-- ============================================================================

CREATE TABLE notifications (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  title VARCHAR(255) NOT NULL,
  message TEXT NOT NULL,
  type VARCHAR(50) NOT NULL,
  priority VARCHAR(20) DEFAULT 'normal',
  is_read BOOLEAN DEFAULT false,
  action_url VARCHAR(255),
  metadata JSONB,
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE whatsapp_messages (
  id UUID PRIMARY KEY,
  customer_id UUID REFERENCES customers(id),
  phone VARCHAR(50) NOT NULL,
  message TEXT NOT NULL,
  message_type VARCHAR(20) DEFAULT 'text',
  status VARCHAR(20) DEFAULT 'pending',
  sent_at TIMESTAMPTZ,
  delivered_at TIMESTAMPTZ,
  read_at TIMESTAMPTZ,
  error_message TEXT,
  metadata JSONB,
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- SECTION 11: EXPENSES & PAYMENTS
-- ============================================================================

CREATE TABLE expenses (
  id UUID PRIMARY KEY,
  expense_number VARCHAR(100) NOT NULL UNIQUE,
  category VARCHAR(100) NOT NULL,
  description TEXT,
  amount DECIMAL(15,2) NOT NULL,
  payment_method VARCHAR(50),
  store_id UUID REFERENCES stores(id),
  approved_by UUID REFERENCES users(id),
  date TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
  notes TEXT
);

CREATE TABLE payment_gateways (
  id UUID PRIMARY KEY,
  code VARCHAR(100) NOT NULL UNIQUE,
  name VARCHAR(255) NOT NULL,
  provider VARCHAR(100) NOT NULL,
  api_key VARCHAR(255),
  api_secret VARCHAR(255),
  is_active BOOLEAN DEFAULT true,
  config JSONB,
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- SECTION 12: CASH REGISTER & SESSIONS
-- ============================================================================

CREATE TABLE cash_register_sessions (
  id UUID PRIMARY KEY,
  session_no VARCHAR(100) NOT NULL UNIQUE,
  store_id UUID REFERENCES stores(id),
  cashier_id UUID REFERENCES users(id),
  opening_balance DECIMAL(15,2) DEFAULT 0,
  closing_balance DECIMAL(15,2),
  expected_balance DECIMAL(15,2),
  difference DECIMAL(15,2),
  opened_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
  closed_at TIMESTAMPTZ,
  status VARCHAR(50) DEFAULT 'open',
  notes TEXT,
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE cash_transactions (
  id UUID PRIMARY KEY,
  session_id UUID REFERENCES cash_register_sessions(id),
  transaction_type VARCHAR(50) NOT NULL,
  amount DECIMAL(15,2) NOT NULL,
  payment_method VARCHAR(50),
  reference_no VARCHAR(100),
  notes TEXT,
  created_by UUID REFERENCES users(id),
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
-- ============================================================================
-- SECTION 13: WMS (WAREHOUSE MANAGEMENT)
-- ============================================================================

-- 13.1 Locations
CREATE TABLE wms_locations (
  id UUID PRIMARY KEY,
  store_id UUID REFERENCES stores(id),
  code VARCHAR(50) NOT NULL, -- Zone-Aisle-Rack-Shelf
  name VARCHAR(100),
  description TEXT,
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(store_id, code)
);

-- 13.2 Vehicles
CREATE TABLE wms_vehicles (
  id UUID PRIMARY KEY,
  plate VARCHAR(20) NOT NULL UNIQUE,
  driver_name VARCHAR(100),
  type VARCHAR(50),
  capacity_m3 DECIMAL(10,2),
  status VARCHAR(20) DEFAULT 'idle', -- idle, on_route
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- SECTION 14: AUDIT & MENU
-- ============================================================================

-- 14.1 Menu Items
CREATE TABLE menu_items (
  id UUID PRIMARY KEY,
  menu_type VARCHAR(20) NOT NULL, -- section, main, sub
  label VARCHAR(200) NOT NULL,
  label_tr VARCHAR(200),
  label_en VARCHAR(200),
  label_ar VARCHAR(200),
  label_ku VARCHAR(200),
  parent_id UUID REFERENCES menu_items(id),
  screen_id VARCHAR(100),
  icon_name VARCHAR(100),
  sort_order INTEGER DEFAULT 0,
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 14.2 Audit Logs
CREATE TABLE audit_logs (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  table_name VARCHAR(100) NOT NULL,
  record_id UUID NOT NULL,
  action VARCHAR(20) NOT NULL, -- insert, update, delete
  old_data JSONB,
  new_data JSONB,
  ip_address VARCHAR(45),
  user_agent TEXT,
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 14.3 Special Codes
CREATE TABLE special_codes (
  id UUID PRIMARY KEY,
  code VARCHAR(50) NOT NULL UNIQUE,
  name VARCHAR(255) NOT NULL,
  description TEXT,
  module_type VARCHAR(50), 
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- SECTION 15: PERFORMANCE INDEXES
-- ============================================================================

-- 15.1 Core Indexes
CREATE INDEX IF NOT EXISTS idx_users_store_id ON users(store_id);
CREATE INDEX IF NOT EXISTS idx_products_category_id ON products(category_id);
CREATE INDEX IF NOT EXISTS idx_products_brand_id ON products(brand_id);
CREATE INDEX IF NOT EXISTS idx_products_barcode ON products(barcode);
CREATE INDEX IF NOT EXISTS idx_products_is_active ON products(is_active);

-- 15.2 Sales & Finance
CREATE INDEX IF NOT EXISTS idx_sales_customer_id ON sales(customer_id);
CREATE INDEX IF NOT EXISTS idx_sales_store_id ON sales(store_id);
CREATE INDEX IF NOT EXISTS idx_sales_date ON sales(date);
CREATE INDEX IF NOT EXISTS idx_sale_items_sale_id ON sale_items(sale_id);
CREATE INDEX IF NOT EXISTS idx_sale_items_product_id ON sale_items(product_id);

-- 15.3 Inventory & Stock
CREATE INDEX IF NOT EXISTS idx_stock_movements_product_id ON stock_movements(product_id);
CREATE INDEX IF NOT EXISTS idx_stock_movements_store_id ON stock_movements(store_id);
CREATE INDEX IF NOT EXISTS idx_stock_movements_date ON stock_movements(date);

-- 15.4 WMS & Locations
CREATE INDEX IF NOT EXISTS idx_wms_locations_store_id ON wms_locations(store_id);
CREATE INDEX IF NOT EXISTS idx_wms_locations_code ON wms_locations(code);

-- 15.5 Notifications
CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_is_read ON notifications(is_read);

-- ============================================================================
-- SECTION 16: SYSTEM VIEWS
-- ============================================================================

-- 16.1 Stock Summary View
CREATE OR REPLACE VIEW vw_stock_summary AS
SELECT 
    p.id as product_id,
    p.barcode,
    p.name as product_name,
    c.name as category_name,
    b.name as brand_name,
    p.stock,
    p.price,
    p.cost,
    (p.stock * p.price) as total_value_sale,
    (p.stock * p.cost) as total_value_cost
FROM products p
LEFT JOIN categories c ON p.category_id = c.id
LEFT JOIN brands b ON p.brand_id = b.id;

-- 16.2 Daily Sales View
CREATE OR REPLACE VIEW vw_daily_sales AS
SELECT 
    date(date) as sale_date,
    SUM(total) as daily_total,
    COUNT(*) as sale_count
FROM sales
GROUP BY date(date);
