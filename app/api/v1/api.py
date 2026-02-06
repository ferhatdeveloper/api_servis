from fastapi import APIRouter
from app.api.v1.endpoints.core import auth, companies, database, system
from app.api.v1.endpoints.analytics import general as reports, custom as custom_reports, yoy as yoy_reports, bi as metabase
from app.api.v1.endpoints.inventory import general as inventory, transfers as warehouse_transfers
from app.api.v1.endpoints.logo import erp as logo_erp, data as logo_data
from app.api.v1.endpoints.retail import (
    products as retail_products, sales as retail_sales, 
    customers as retail_customers, reports as retail_reports, payment as retail_payment,
    accounting as retail_accounting, ecommerce as retail_ecommerce, websocket as retail_websocket,
    duplicate_check as retail_duplicate_check, ai_reports as retail_ai, cost_accounting as retail_cost,
    notifications as retail_notifications, vpn as retail_vpn
)
from app.api.v1.endpoints import sync, operations, invoice_pdf, crm, pdks

api_router = APIRouter()

# --- CORE ---
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(system.router, prefix="/system", tags=["System Management"])
api_router.include_router(database.router, prefix="/database", tags=["Database Management"])
api_router.include_router(companies.router, prefix="/companies", tags=["Company & Period Management"])

# --- ANALYTICS ---
api_router.include_router(reports.router, prefix="/reports", tags=["Reports"])
api_router.include_router(custom_reports.router, prefix="/custom-reports", tags=["Custom Reports Builder"])
api_router.include_router(yoy_reports.router, prefix="/yoy-reports", tags=["YoY Reports"])
api_router.include_router(metabase.router, prefix="/bi", tags=["Business Intelligence"])

# --- INVENTORY ---
api_router.include_router(inventory.router, prefix="/inventory", tags=["Inventory"])
api_router.include_router(warehouse_transfers.router, prefix="/warehouse", tags=["Warehouse Transfers"])

# --- CRM & OPERATIONS ---
api_router.include_router(crm.router, prefix="/crm", tags=["CRM"])
api_router.include_router(operations.router, prefix="/operations", tags=["Operations"])
api_router.include_router(invoice_pdf.router, prefix="/documents", tags=["Document Generation"])

# --- LOGO INTEGRATION ---
# Consolidating all Logo operations under /logo
logo_router = APIRouter(prefix="/logo", tags=["Logo Integration"])
logo_router.include_router(logo_erp.router, prefix="/erp", tags=["Logo ERP"])   # /api/v1/logo/erp
logo_router.include_router(logo_data.router, prefix="/data", tags=["Logo Data"]) # /api/v1/logo/data
logo_router.include_router(sync.router, prefix="/sync", tags=["Logo Sync"])      # /api/v1/logo/sync

api_router.include_router(logo_router)

# --- PDKS (Flattened) ---
from app.api.v1.endpoints.pdks import (
    departments, performance, auto_index, file_upload, 
    hikvision, email_settings, realtime, health as pdks_health, 
    database as pdks_database
)

# --- SYSTEM & INFRASTRUCTURE ---
# Consolidated system-wide utilities
api_router.include_router(retail_vpn.router, tags=["VPN Manager"]) # Internal prefix: /vpn
api_router.include_router(file_upload.router, prefix="/upload", tags=["File Upload"])
api_router.include_router(email_settings.router, prefix="/email-settings", tags=["Email Settings"])
api_router.include_router(auto_index.router, prefix="/auto-index", tags=["Auto Index"])

# --- HEALTH & MONITORING ---
api_router.include_router(pdks_health.router, tags=["System Health"]) # Internal prefix: /health
api_router.include_router(pdks_database.router, prefix="/pdks-database", tags=["PDKS Database Config"])

# --- COMMUNICATION ---
# Consolidated Realtime & Messaging
comm_router = APIRouter(prefix="/communication", tags=["Communication"])
comm_router.include_router(realtime.router, prefix="/realtime", tags=["System Broadcasts"]) # /api/v1/communication/realtime
comm_router.include_router(retail_websocket.router, prefix="/sync", tags=["Data Sync (WS)"]) # /api/v1/communication/sync
comm_router.include_router(retail_notifications.router, prefix="/notifications", tags=["Notifications"]) # /api/v1/communication/notifications

api_router.include_router(comm_router)

# --- PDKS (Core Modules) ---
api_router.include_router(departments.router, prefix="/departments", tags=["Departments"])
api_router.include_router(performance.router, prefix="/performance", tags=["Performance"])
api_router.include_router(hikvision.router, prefix="/hikvision", tags=["Hikvision"])
# realtime moved to Communication

# --- RETAIL (Core Modules) ---
api_router.include_router(retail_products.router, prefix="/products", tags=["Retail Products"])
api_router.include_router(retail_sales.router, prefix="/sales", tags=["Retail Sales"])
api_router.include_router(retail_customers.router, prefix="/retail-customers", tags=["Retail Customers"])
api_router.include_router(retail_reports.router, prefix="/retail-reports", tags=["Retail Reports"])
api_router.include_router(retail_payment.router, prefix="/payment", tags=["Retail Payment"])
api_router.include_router(retail_accounting.router, prefix="/accounting", tags=["Retail Accounting"])
api_router.include_router(retail_ecommerce.router, prefix="/ecommerce", tags=["Retail E-commerce"])
# websocket moved to Communication
api_router.include_router(retail_duplicate_check.router, prefix="/duplicate-check", tags=["Retail Checks"])
api_router.include_router(retail_ai.router, prefix="/ai-analysis", tags=["Retail AI"])
api_router.include_router(retail_cost.router, prefix="/cost-accounting", tags=["Retail Cost Accounting"])
# notifications moved to Communication
# VPN moved to System
# whatsapp moved to Communication


