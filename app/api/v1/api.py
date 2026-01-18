from fastapi import APIRouter
from .endpoints import auth, crm, inventory, operations, logo_erp, sync, yoy_reports, database, companies, logo_data, warehouse_transfers, invoice_pdf, system, custom_reports, pdks

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(crm.router, prefix="/crm", tags=["CRM"])
api_router.include_router(inventory.router, prefix="/inventory", tags=["Inventory"])
api_router.include_router(operations.router, prefix="/operations", tags=["Operations"])
api_router.include_router(logo_erp.router, prefix="/logo", tags=["Logo ERP Integration"])
api_router.include_router(sync.router, prefix="/sync", tags=["Report Sync"])
api_router.include_router(yoy_reports.router, prefix="/reports", tags=["YoY Reports"])
api_router.include_router(database.router, prefix="/database", tags=["Database Management"])
api_router.include_router(companies.router, prefix="/companies", tags=["Company & Period Management"])
api_router.include_router(logo_data.router, prefix="/logo-data", tags=["Logo Master Data"])
api_router.include_router(warehouse_transfers.router, prefix="/warehouse", tags=["Warehouse Transfers"])
api_router.include_router(invoice_pdf.router, prefix="/documents", tags=["Document Generation"])
api_router.include_router(system.router, prefix="/system", tags=["System Management"])
api_router.include_router(custom_reports.router, prefix="/custom-reports", tags=["Custom Reports Builder"])
api_router.include_router(pdks.router, prefix="/pdks", tags=["PDKS"])

