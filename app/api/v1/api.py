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
    notifications as retail_notifications, vpn as retail_vpn, whatsapp as retail_whatsapp  
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

# --- LOGO ERP ---
api_router.include_router(logo_erp.router, prefix="/logo", tags=["Logo ERP Integration"])
api_router.include_router(logo_data.router, prefix="/logo-data", tags=["Logo Master Data"])
api_router.include_router(sync.router, prefix="/sync", tags=["Report Sync"])

# --- PDKS ---
api_router.include_router(pdks.router, prefix="/pdks", tags=["PDKS Integration"])

# --- RETAIL (Prefix: /retail) ---
# Grouping retail endpoints under /retail to keep main namespace clean, but sub-routes are short.
# User asked for short URLs, so we avoid deep nesting like /retail/api/v1/...
retail_router = APIRouter(prefix="/retail", tags=["Retail Protocol"])

retail_router.include_router(retail_products.router, prefix="/products", tags=["Retail Products"])
retail_router.include_router(retail_sales.router, prefix="/sales", tags=["Retail Sales"])
retail_router.include_router(retail_customers.router, prefix="/customers", tags=["Retail Customers"])
retail_router.include_router(retail_reports.router, prefix="/reports", tags=["Retail Reports"])
retail_router.include_router(retail_payment.router, prefix="/payment", tags=["Retail Payment"])
retail_router.include_router(retail_accounting.router, prefix="/accounting", tags=["Retail Accounting"])
retail_router.include_router(retail_ecommerce.router, prefix="/ecommerce", tags=["Retail E-commerce"])
retail_router.include_router(retail_websocket.router, prefix="/ws", tags=["Retail WebSocket"])
retail_router.include_router(retail_duplicate_check.router, prefix="/check", tags=["Retail Checks"])
retail_router.include_router(retail_ai.router, prefix="/ai", tags=["Retail AI"])
retail_router.include_router(retail_cost.router, prefix="/cost", tags=["Retail Cost Accounting"])
retail_router.include_router(retail_notifications.router, prefix="/notifications", tags=["Retail Notifications"])
retail_router.include_router(retail_vpn.router, prefix="/vpn", tags=["Retail VPN"])
retail_router.include_router(retail_whatsapp.router, prefix="/whatsapp", tags=["Retail WhatsApp"])

api_router.include_router(retail_router)


