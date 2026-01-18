from fastapi import APIRouter, Depends, HTTPException, Header, Query, Response, UploadFile, File
from app.services.logo_service import logo_service
from app.services.xml_service import xml_service
from app.core.security import get_current_userModel
from pydantic import BaseModel
from typing import Optional, List

router = APIRouter()

class LogoCustomerBase(BaseModel):
    code: str
    name: str
    address: Optional[str] = None
    city: Optional[str] = None
    tax_office: Optional[str] = None
    tax_number: Optional[str] = None

@router.get("/customers")
async def get_logo_customers(
    search: Optional[str] = Query(None),
    x_firma: Optional[str] = Header(None)
):
    return await logo_service.get_customers(search, firma=x_firma)

@router.post("/customers")
async def create_logo_customer(customer: LogoCustomerBase):
    success = await logo_service.create_customer(customer.dict())
    if not success:
        raise HTTPException(status_code=500, detail="Failed to create customer in Logo")
    return {"status": "success", "message": "Customer created in Logo"}

@router.put("/customers/{erp_code}")
async def update_logo_customer(erp_code: str, customer: LogoCustomerBase):
    success = await logo_service.update_customer(erp_code, customer.dict())
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update customer in Logo")
    return {"status": "success", "message": "Customer updated in Logo"}

@router.get("/items")
async def read_logo_items(search: Optional[str] = None):
    return await logo_service.get_items(search)

@router.get("/services")
async def read_logo_services(search: Optional[str] = None):
    return await logo_service.get_services(search)

@router.post("/invoices")
async def create_logo_invoice(
    local_invoice_id: str, 
    type: str = Query("wholesale", description="wholesale, retail, or service")
):
    success = await logo_service.transfer_invoice_to_logo(local_invoice_id, invoice_type=type)
    if not success:
         raise HTTPException(status_code=500, detail="Failed to transfer invoice to Logo")
    success = await logo_service.transfer_invoice_to_logo(local_invoice_id, invoice_type=type)
    if not success:
         raise HTTPException(status_code=500, detail="Failed to transfer invoice to Logo")
    return {"status": "success", "message": f"Invoice ({type}) transferred to Logo"}

@router.post("/clients/sync")
async def create_logo_client(client_data: dict, mode: str = Query("objects", description="objects or sql")):
    """Direct Client Creation via Objects"""
    if mode == "objects":
        success, ref = await logo_service._transfer_client_via_objects(client_data)
        if success: return {"status": "success", "ref": ref}
        raise HTTPException(status_code=500, detail=f"Client creation failed: {ref}")
    # Fallback to SQL (existing create_customer logic)
    await logo_service.create_customer(client_data)
    return {"status": "success", "message": "Client created via SQL"}

@router.post("/items/sync")
async def create_logo_item(item_data: dict):
    """Direct Item Creation via Objects"""
    success, ref = await logo_service._transfer_item_via_objects(item_data)
    if success: return {"status": "success", "ref": ref}
    raise HTTPException(status_code=500, detail=f"Item creation failed: {ref}")

@router.post("/import/xml")
async def import_logo_xml(file: UploadFile = File(...)):
    """
    Import standard Logo XML via Unity Objects (DataFromXML).
    This acts as a 'Mini LogoConnect'.
    """
    try:
        content = await file.read()
        # Decode - try utf-8, fallback to windows-1254 (turkish)
        try:
            xml_str = content.decode("utf-8")
        except UnicodeDecodeError:
             xml_str = content.decode("cp1254")

        success, msg = logo_service.import_xml_data(xml_str)
        if success:
             return {"status": "success", "message": "XML Import Successful"}
        else:
             raise HTTPException(status_code=400, detail=msg)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/export/xml/{type}/{id}")
async def export_xml(type: str, id: str):
    """
    Download Logo XML for an entity.
    type: invoice, client
    id: Entity ID (in local DB)
    """
    xml_content = None
    filename = f"{type}_{id}.xml"
    
    if type == "invoice":
        xml_content = await xml_service.generate_sales_invoice_xml(id)
        # xml_content is (str) or (None, err) -> Wait, logic returns valid XML string or tuple?
        # Let's fix service logic or check usage.
        # My service returns prettified string. If error?
        # Service logic: return self._prettify(root)
        # But wait, generate_sales_invoice_xml has error check 'if not order_res: return None, "Invoice not found"' -> Tuple
        pass
        
    elif type == "client":
        xml_content = await xml_service.generate_client_xml(int(id))
        
    # Check Result Type
    if isinstance(xml_content, tuple):
        # Error case
        raise HTTPException(status_code=404, detail=xml_content[1])
        
    if not xml_content:
        raise HTTPException(status_code=404, detail="Could not generate XML")
        
    return Response(content=xml_content, media_type="application/xml", headers={"Content-Disposition": f"attachment; filename={filename}"})

@router.post("/dispatches/sync")
async def create_logo_dispatch(dispatch_data: dict, items: list[dict]):
    """Direct Dispatch Creation via Objects"""
    success, ref = await logo_service._transfer_dispatch_via_objects(dispatch_data, items)
    if success: return {"status": "success", "ref": ref}
    raise HTTPException(status_code=500, detail=f"Dispatch creation failed: {ref}")

@router.post("/collections/sync")
async def create_logo_collection(collection_data: dict):
    """Direct Cash/Bank Collection via Objects"""
    success, ref = await logo_service._transfer_collection_via_objects(collection_data)
    if success: return {"status": "success", "ref": ref}
    raise HTTPException(status_code=500, detail=f"Collection failed: {ref}")

@router.get("/orders")
async def read_logo_orders(customer_code: Optional[str] = None):
    return await logo_service.get_orders(customer_code)

class LogoPaymentCreate(BaseModel):
    customer_code: str
    amount: float

@router.post("/collections")
async def create_logo_collection(payment: LogoPaymentCreate):
    success = await logo_service.create_payment(payment.dict())
    if not success:
        raise HTTPException(status_code=500, detail="Failed to record payment in Logo")
    return {"status": "success", "message": "Payment recorded in Logo"}

@router.get("/stock/{item_code}")
async def read_logo_stock(item_code: str):
    return await logo_service.get_logo_stock_status(item_code)

# --- REPORTING ENDPOINTS ---

@router.get("/reports/sales")
async def get_logo_sales_report(
    start_date: str,
    end_date: str,
    x_firma: Optional[str] = Header(None),
    x_period: Optional[str] = Header(None)
):
    """Start and end date format: YYYY-MM-DD"""
    return await logo_service.get_sales_report(start_date, end_date, firma=x_firma, period=x_period)

@router.get("/reports/collections")
async def get_logo_collection_report(
    start_date: str,
    end_date: str,
    x_firma: Optional[str] = Header(None)
):
    return await logo_service.get_collection_report(start_date, end_date, firma=x_firma)

@router.get("/reports/balances")
async def get_logo_customer_balances(
    x_firma: Optional[str] = Header(None),
    x_period: Optional[str] = Header(None)
):
    return await logo_service.get_customer_balances(firma=x_firma, period=x_period)

@router.get("/reports/inventory")
async def get_logo_inventory_report(
    x_firma: Optional[str] = Header(None),
    x_period: Optional[str] = Header(None)
):
    return await logo_service.get_inventory_status(firma=x_firma, period=x_period)

@router.get("/reports/top-selling")
async def get_logo_top_selling_report(
    limit: int = 10,
    x_firma: Optional[str] = Header(None),
    x_period: Optional[str] = Header(None)
):
    return await logo_service.get_top_selling_products(limit, firma=x_firma, period=x_period)

@router.get("/reports/visits")
async def get_logo_visit_report(start_date: str, end_date: str):
    return await logo_service.get_visit_performance_report(start_date, end_date)

@router.get("/reports/order-tracking")
async def get_logo_order_tracking_report(
    start_date: str, 
    end_date: str,
    x_firma: Optional[str] = Header(None)
):
    return await logo_service.get_order_tracking_report(start_date, end_date, firma=x_firma)

@router.get("/reports/leaderboard")
async def get_logo_leaderboard(
    start_date: str, 
    end_date: str,
    x_firma: Optional[str] = Header(None),
    x_period: Optional[str] = Header(None)
):
    return await logo_service.get_salesman_leaderboard(start_date, end_date, firma=x_firma, period=x_period)

@router.get("/reports/aging")
async def get_logo_aging_report(
    x_firma: Optional[str] = Header(None),
    x_period: Optional[str] = Header(None)
):
    return await logo_service.get_debt_aging_report(firma=x_firma, period=x_period)

@router.get("/reports/categories")
async def get_logo_category_analysis(
    start_date: str, 
    end_date: str,
    x_firma: Optional[str] = Header(None),
    x_period: Optional[str] = Header(None)
):
    return await logo_service.get_category_sales_analysis(start_date, end_date, firma=x_firma, period=x_period)

@router.get("/reports/churn")
async def get_logo_churn_report(
    x_firma: Optional[str] = Header(None),
    x_period: Optional[str] = Header(None)
):
    return await logo_service.get_churn_risk_report(firma=x_firma, period=x_period)

@router.get("/reports/profitability")
async def get_logo_profitability_analysis(
    start_date: str, 
    end_date: str,
    x_firma: Optional[str] = Header(None),
    x_period: Optional[str] = Header(None)
):
    return await logo_service.get_profitability_analysis(start_date, end_date, firma=x_firma, period=x_period)

@router.get("/reports/targets")
async def get_logo_target_achievement(
    x_firma: Optional[str] = Header(None),
    x_period: Optional[str] = Header(None)
):
    return await logo_service.get_target_achievement_report(firma=x_firma, period=x_period)

@router.get("/reports/cross-history")
async def get_logo_cross_history(
    customer_code: str,
    item_code: str,
    x_firma: Optional[str] = Header(None),
    x_period: Optional[str] = Header(None)
):
    return await logo_service.get_customer_product_history(customer_code, item_code, firma=x_firma, period=x_period)

@router.get("/reports/doc-chain")
async def get_logo_doc_chain(
    start_date: str, 
    end_date: str,
    x_firma: Optional[str] = Header(None),
    x_period: Optional[str] = Header(None)
):
    return await logo_service.get_document_chain_report(start_date, end_date, firma=x_firma, period=x_period)

@router.get("/reports/lines")
async def get_logo_lines(
    type: str,
    fiche_no: str,
    x_firma: Optional[str] = Header(None),
    x_period: Optional[str] = Header(None)
):
    return await logo_service.get_detailed_line_report(type, fiche_no, firma=x_firma, period=x_period)

@router.get("/reports/pos-daily")
async def get_logo_pos_daily(
    date: str,
    x_firma: Optional[str] = Header(None),
    x_period: Optional[str] = Header(None)
):
    return await logo_service.get_pos_daily_report(date, firma=x_firma, period=x_period)

@router.get("/reports/lot-expiry")
async def get_logo_lot_expiry(
    days: int = 30,
    x_firma: Optional[str] = Header(None),
    x_period: Optional[str] = Header(None)
):
    return await logo_service.get_lot_expiry_report(days, firma=x_firma, period=x_period)

@router.get("/reports/transfers")
async def get_logo_transfers(
    start_date: str, 
    end_date: str,
    x_firma: Optional[str] = Header(None),
    x_period: Optional[str] = Header(None)
):
    return await logo_service.get_stock_transfer_report(start_date, end_date, firma=x_firma, period=x_period)

@router.get("/reports/cashflow")
async def get_logo_cashflow(
    x_firma: Optional[str] = Header(None),
    x_period: Optional[str] = Header(None)
):
    return await logo_service.get_cashflow_report(firma=x_firma, period=x_period)

@router.get("/reports/generic/{report_code}")
async def get_logo_generic_report(
    report_code: str,
    x_firma: Optional[str] = Header(None),
    x_period: Optional[str] = Header(None)
):
    return await logo_service.get_report_data(report_code, firma=x_firma, period=x_period)

@router.get("/reports/yoy-comparison")
async def get_yoy_comparison(
    period: str = Query("daily", description="Period type: daily, weekly, or monthly")
):
    """
    Year-over-Year comparison report.
    Compare current period vs same period last year.
    """
    return await logo_service.get_yoy_comparison(period)
