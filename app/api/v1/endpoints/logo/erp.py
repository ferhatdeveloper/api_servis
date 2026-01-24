from fastapi import APIRouter, Depends, HTTPException, Header, Query, Response, UploadFile, File
from app.services.logo_service import logo_service
from app.services.xml_service import xml_service
from app.core.security import get_current_userModel
from pydantic import BaseModel, Field
from typing import Optional, List

router = APIRouter()

class LogoCustomerBase(BaseModel):
    code: str = Field(..., description="Müşteri Kodu")
    name: str = Field(..., description="Müşteri Ünvanı")
    address: Optional[str] = Field(None, description="Adres")
    city: Optional[str] = Field(None, description="Şehir")
    tax_office: Optional[str] = Field(None, description="Vergi Dairesi")
    tax_number: Optional[str] = Field(None, description="Vergi/TC Kimlik No")

@router.get("/firms")
async def get_firms():
    """
    **Firma Listesi (L_CAPIFIRM)**

    Logo veritabanındaki kayıtlı firmaları listeler.
    Kurulum sihirbazında veya firma seçim ekranlarında kullanılır.
    """
    return await logo_service.get_available_firms()

@router.get("/customers")
async def get_logo_customers(
    search: Optional[str] = Query(None, description="Arama metni (Kod veya Ünvan)"),
    x_firma: Optional[str] = Header(None, description="Hedef Firma No")
):
    """
    **Logo Müşteri Ara**

    Doğrudan Logo veritabanından (CLCARD) canlı müşteri araması yapar.
    """
    return await logo_service.get_customers(search, firma=x_firma)

@router.post("/customers")
async def create_logo_customer(customer: LogoCustomerBase):
    """
    **Logo Müşteri Oluştur**

    SQL insert yöntemiyle Logo'da yeni bir cari kart (CLCARD) oluşturur.
    """
    success = await logo_service.create_customer(customer.dict())
    if not success:
        raise HTTPException(status_code=500, detail="Failed to create customer in Logo")
    return {"status": "success", "message": "Customer created in Logo"}

@router.put("/customers/{erp_code}")
async def update_logo_customer(erp_code: str, customer: LogoCustomerBase):
    """
    **Logo Müşteri Güncelle**

    Mevcut cari kartı günceller.
    """
    success = await logo_service.update_customer(erp_code, customer.dict())
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update customer in Logo")
    return {"status": "success", "message": "Customer updated in Logo"}

@router.get("/items")
async def read_logo_items(search: Optional[str] = Query(None, description="Malzeme arama")):
    """
    **Malzeme Ara (ITEMS)**

    Logo'daki malzemeleri (ITEMS) listeler. Stok durumu, fiyat vb. içerir.
    """
    return await logo_service.get_items(search)

@router.get("/services")
async def read_logo_services(search: Optional[str] = Query(None, description="Hizmet arama")):
    """
    **Hizmet Kartları (SRVCARD)**

    Logo'daki hizmet kartlarını listeler.
    """
    return await logo_service.get_services(search)

@router.post("/invoices")
async def create_logo_invoice(
    local_invoice_id: str = Query(..., description="Yerel Fatura ID"), 
    type: str = Query("wholesale", description="Fatura Tipi: 'wholesale' (Toptan), 'retail' (Perakende), 'service' (Hizmet)")
):
    """
    **Fatura Aktarımı (Logo Objects)**

    Yerel veritabanındaki bir faturayı Logo REST Objects aracılığıyla Logo'ya aktarır.
    İşlem başarılı olursa Fiş Numarasını döner.
    """
    success = await logo_service.transfer_invoice_to_logo(local_invoice_id, invoice_type=type)
    if not success:
         raise HTTPException(status_code=500, detail="Failed to transfer invoice to Logo")
    # Duplicate call removed in cleanup
    return {"status": "success", "message": f"Invoice ({type}) transferred to Logo"}

@router.post("/clients/sync")
async def create_logo_client(client_data: dict, mode: str = Query("objects", description="'objects' (Rest) veya 'sql' (Direct DB)")):
    """
    **Cari Kart Aktarımı (Senkron)**

    Logo Objects kullanarak yeni cari kart açar.
    `mode=objects` önerilen yöntemdir.
    """
    if mode == "objects":
        success, ref = await logo_service._transfer_client_via_objects(client_data)
        if success: return {"status": "success", "ref": ref}
        raise HTTPException(status_code=500, detail=f"Client creation failed: {ref}")
    # Fallback to SQL (existing create_customer logic)
    await logo_service.create_customer(client_data)
    return {"status": "success", "message": "Client created via SQL"}

@router.post("/items/sync")
async def create_logo_item(item_data: dict):
    """
    **Malzeme Kartı Aktarımı**

    Logo Objects üzerinden yeni malzeme kartı (ITEMS) oluşturur.
    """
    success, ref = await logo_service._transfer_item_via_objects(item_data)
    if success: return {"status": "success", "ref": ref}
    raise HTTPException(status_code=500, detail=f"Item creation failed: {ref}")

@router.post("/import/xml")
async def import_logo_xml(file: UploadFile = File(..., description="Logo XML Dosyası")):
    """
    **XML İçe Aktar (Mini LogoConnect)**

    Standart Logo XML formatındaki veriyi doğrudan Logo'ya işler (DataFromXML).
    Fatura, Sipariş, Cari vb. tüm XML tiplerini destekler.
    Windows-1254 (Türkçe) encoding desteği vardır.
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
async def export_xml(
    type: str, 
    id: str
):
    """
    **XML Dışa Aktar**

    Belirtilen kaydı Logo XML formatında indirir.
    
    **Type:**
    - `invoice`: Satış Faturası
    - `client`: Cari Kart
    """
    xml_content = None
    filename = f"{type}_{id}.xml"
    
    if type == "invoice":
        xml_content = await xml_service.generate_sales_invoice_xml(id)
        
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
    """
    **İrsaliye Aktarımı**
    """
    success, ref = await logo_service._transfer_dispatch_via_objects(dispatch_data, items)
    if success: return {"status": "success", "ref": ref}
    raise HTTPException(status_code=500, detail=f"Dispatch creation failed: {ref}")

@router.post("/collections/sync")
async def create_logo_collection_sync(collection_data: dict):
    """
    **Tahsilat Aktarımı (Objects)**
    
    Nakit veya Kredi Kartı tahsilatlarını Logo'ya işler.
    """
    success, ref = await logo_service._transfer_collection_via_objects(collection_data)
    if success: return {"status": "success", "ref": ref}
    raise HTTPException(status_code=500, detail=f"Collection failed: {ref}")

@router.get("/orders")
async def read_logo_orders(customer_code: Optional[str] = Query(None, description="Müşteri Kodu")):
    """
    **Sipariş Listesi (ORFICHE)**

    Logo'daki bekleyen siparişleri listeler.
    """
    return await logo_service.get_orders(customer_code)

class LogoPaymentCreate(BaseModel):
    customer_code: str = Field(..., description="Cari Kodu")
    amount: float = Field(..., description="Tutar")

@router.post("/collections")
async def create_logo_collection(payment: LogoPaymentCreate):
    """
    **Basit Tahsilat (SQL)**
    
    Doğrudan veritabanına nakit tahsilat kaydı atar (Kasa Fişi).
    """
    success = await logo_service.create_payment(payment.dict())
    if not success:
        raise HTTPException(status_code=500, detail="Failed to record payment in Logo")
    return {"status": "success", "message": "Payment recorded in Logo"}

@router.get("/stock/{item_code}")
async def read_logo_stock(item_code: str):
    """
    **Stok Durumu**

    Belirli bir malzemenin ambar bazlı stok miktarlarını döner.
    """
    return await logo_service.get_logo_stock_status(item_code)

# --- REPORTING ENDPOINTS ---

@router.get("/reports/sales")
async def get_logo_sales_report(
    start_date: str = Query(..., description="YYYY-MM-DD"),
    end_date: str = Query(..., description="YYYY-MM-DD"),
    x_firma: Optional[str] = Header(None),
    x_period: Optional[str] = Header(None)
):
    """
    **Satış Raporu**

    Tarih aralığındaki satışları fatura bazında listeler.
    """
    return await logo_service.get_sales_report(start_date, end_date, firma=x_firma, period=x_period)

@router.get("/reports/collections")
async def get_logo_collection_report(
    start_date: str,
    end_date: str,
    x_firma: Optional[str] = Header(None)
):
    """
    **Tahsilat Raporu**

    Nakit, Çek, Senet, Kredi Kartı tahsilatlarını raporlar.
    """
    return await logo_service.get_collection_report(start_date, end_date, firma=x_firma)

@router.get("/reports/balances")
async def get_logo_customer_balances(
    x_firma: Optional[str] = Header(None),
    x_period: Optional[str] = Header(None)
):
    """
    **Cari Bakiye Raporu**

    Tüm müşterilerin güncel borç/alacak bakiyelerini döner.
    """
    return await logo_service.get_customer_balances(firma=x_firma, period=x_period)

@router.get("/reports/inventory")
async def get_logo_inventory_report(
    x_firma: Optional[str] = Header(None),
    x_period: Optional[str] = Header(None)
):
    """
    **Envanter Raporu**

    Stoktaki ürünlerin miktar ve maliyet değerlerini raporlar.
    """
    return await logo_service.get_inventory_status(firma=x_firma, period=x_period)

@router.get("/reports/top-selling")
async def get_logo_top_selling_report(
    limit: int = 10,
    x_firma: Optional[str] = Header(None),
    x_period: Optional[str] = Header(None)
):
    """
    **En Çok Satanlar**

    Miktar veya ciro bazında en çok satan ürünleri listeler.
    """
    return await logo_service.get_top_selling_products(limit, firma=x_firma, period=x_period)

@router.get("/reports/visits")
async def get_logo_visit_report(start_date: str, end_date: str):
    """
    **Ziyaret Performansı**

    Satış temsilcilerinin müşteri ziyaret sayılarını raporlar.
    (Eğer sistemde ziyaret modülü aktifse)
    """
    return await logo_service.get_visit_performance_report(start_date, end_date)

@router.get("/reports/order-tracking")
async def get_logo_order_tracking_report(
    start_date: str, 
    end_date: str,
    x_firma: Optional[str] = Header(None)
):
    """
    **Sipariş Karşılama Raporu**

    Alınan siparişlerin ne kadarının sevk edildiğini (karşılama oranı) gösterir.
    """
    return await logo_service.get_order_tracking_report(start_date, end_date, firma=x_firma)

@router.get("/reports/leaderboard")
async def get_logo_leaderboard(
    start_date: str, 
    end_date: str,
    x_firma: Optional[str] = Header(None),
    x_period: Optional[str] = Header(None)
):
    """
    **Plasiyer Sıralaması (Leaderboard)**

    Satış temsilcilerini ciroya göre sıralar.
    """
    return await logo_service.get_salesman_leaderboard(start_date, end_date, firma=x_firma, period=x_period)

@router.get("/reports/aging")
async def get_logo_aging_report(
    x_firma: Optional[str] = Header(None),
    x_period: Optional[str] = Header(None)
):
    """
    **Yaşlandırma Raporu (Aging)**

    Borçların vadesine göre dağılımını (0-30, 30-60, 60-90, 90+ gün) gösterir.
    """
    return await logo_service.get_debt_aging_report(firma=x_firma, period=x_period)

@router.get("/reports/categories")
async def get_logo_category_analysis(
    start_date: str, 
    end_date: str,
    x_firma: Optional[str] = Header(None),
    x_period: Optional[str] = Header(None)
):
    """
    **Kategori Analizi**

    Ürün grubu (STGRPCODE) bazında satış dağılımı.
    """
    return await logo_service.get_category_sales_analysis(start_date, end_date, firma=x_firma, period=x_period)

@router.get("/reports/churn")
async def get_logo_churn_report(
    x_firma: Optional[str] = Header(None),
    x_period: Optional[str] = Header(None)
):
    """
    **Churn (Riskli Müşteri) Analizi**

    Uzun süredir sipariş vermeyen müşterileri tespit eder.
    """
    return await logo_service.get_churn_risk_report(firma=x_firma, period=x_period)

@router.get("/reports/profitability")
async def get_logo_profitability_analysis(
    start_date: str, 
    end_date: str,
    x_firma: Optional[str] = Header(None),
    x_period: Optional[str] = Header(None)
):
    """
    **Karlılık Analizi**

    Fatura maliyetleri üzerinden brüt kar marjını hesaplar.
    """
    return await logo_service.get_profitability_analysis(start_date, end_date, firma=x_firma, period=x_period)

@router.get("/reports/targets")
async def get_logo_target_achievement(
    x_firma: Optional[str] = Header(None),
    x_period: Optional[str] = Header(None)
):
    """
    **Hedef Gerçekleşme**

    Aylık satış hedeflerine göre gerçekleşme oranlarını raporlar.
    """
    return await logo_service.get_target_achievement_report(firma=x_firma, period=x_period)

@router.get("/reports/cross-history")
async def get_logo_cross_history(
    customer_code: str,
    item_code: str,
    x_firma: Optional[str] = Header(None),
    x_period: Optional[str] = Header(None)
):
    """
    **Ürün-Müşteri Tarihçesi**

    Bir müşterinin belirli bir ürünü en son ne zaman, kaça aldığı bilgisi.
    """
    return await logo_service.get_customer_product_history(customer_code, item_code, firma=x_firma, period=x_period)

@router.get("/reports/doc-chain")
async def get_logo_doc_chain(
    start_date: str, 
    end_date: str,
    x_firma: Optional[str] = Header(None),
    x_period: Optional[str] = Header(None)
):
    """
    **Belge Bağlantı Raporu**

    Sipariş -> İrsaliye -> Fatura zincirini takip eder.
    """
    return await logo_service.get_document_chain_report(start_date, end_date, firma=x_firma, period=x_period)

@router.get("/reports/lines")
async def get_logo_lines(
    type: str,
    fiche_no: str,
    x_firma: Optional[str] = Header(None),
    x_period: Optional[str] = Header(None)
):
    """
    **Fiş Satır Detayları**

    Fatura veya siparişin satırlarını (ürün, miktar, fiyat) döner.
    """
    return await logo_service.get_detailed_line_report(type, fiche_no, firma=x_firma, period=x_period)

@router.get("/reports/pos-daily")
async def get_logo_pos_daily(
    date: str,
    x_firma: Optional[str] = Header(None),
    x_period: Optional[str] = Header(None)
):
    """
    **Günlük Kasa Raporu**
    """
    return await logo_service.get_pos_daily_report(date, firma=x_firma, period=x_period)

@router.get("/reports/lot-expiry")
async def get_logo_lot_expiry(
    days: int = 30,
    x_firma: Optional[str] = Header(None),
    x_period: Optional[str] = Header(None)
):
    """
    **SKT Yaklaşanlar (Lot/Seri)**
    """
    return await logo_service.get_lot_expiry_report(days, firma=x_firma, period=x_period)

@router.get("/reports/transfers")
async def get_logo_transfers(
    start_date: str, 
    end_date: str,
    x_firma: Optional[str] = Header(None),
    x_period: Optional[str] = Header(None)
):
    """
    **Depo Transfer Raporu**
    """
    return await logo_service.get_stock_transfer_report(start_date, end_date, firma=x_firma, period=x_period)

@router.get("/reports/cashflow")
async def get_logo_cashflow(
    x_firma: Optional[str] = Header(None),
    x_period: Optional[str] = Header(None)
):
    """
    **Nakit Akış Raporu**
    """
    return await logo_service.get_cashflow_report(firma=x_firma, period=x_period)

@router.get("/reports/generic/{report_code}")
async def get_logo_generic_report(
    report_code: str,
    x_firma: Optional[str] = Header(None),
    x_period: Optional[str] = Header(None)
):
    """
    **Genel Rapor Getir**

    Tanımlı özel SQL raporlarını (Generic Reports) çalıştırır.
    """
    return await logo_service.get_report_data(report_code, firma=x_firma, period=x_period)

@router.get("/reports/yoy-comparison")
async def get_yoy_comparison(
    period: str = Query("daily", description="Periyot: daily, weekly, monthly")
):
    """
    **Yıllık Karşılaştırma (YoY)**

    Bu yılın satışlarını geçen yılın aynı dönemiyle kıyaslar.
    """
    return await logo_service.get_yoy_comparison(period)
