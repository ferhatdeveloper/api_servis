from fastapi import APIRouter, HTTPException
from loguru import logger
from app.core.database import db_manager
from typing import List, Optional
from pydantic import BaseModel, Field

router = APIRouter()

# =====================================================
# SCHEMAS
# =====================================================

class Salesman(BaseModel):
    id: int = Field(..., description="Sistem ID")
    logo_ref: int = Field(..., description="Logo LOGICALREF")
    code: str = Field(..., description="Satış Elemanı Kodu")
    name: str = Field(..., description="Satış Elemanı Adı")
    email: Optional[str] = Field(None, description="E-posta Adresi")
    phone: Optional[str] = Field(None, description="Telefon Numarası")
    is_active: bool = Field(..., description="Aktiflik Durumu")

class Brand(BaseModel):
    id: int = Field(..., description="Sistem ID")
    logo_ref: int = Field(..., description="Logo LOGICALREF")
    code: str = Field(..., description="Marka Kodu")
    name: str = Field(..., description="Marka Adı")
    description: Optional[str] = Field(None, description="Açıklama")
    is_active: bool = Field(..., description="Aktiflik Durumu")

class SpecialCode(BaseModel):
    id: int = Field(..., description="Sistem ID")
    specode_type: str = Field(..., description="Kod Tipi: 'customer', 'item', 'invoice'")
    code_number: int = Field(..., description="Özel Kod Sırası (1-5)")
    code: str = Field(..., description="Özel Kod")
    name: str = Field(..., description="Açıklama/Tanım")
    is_active: bool = Field(..., description="Aktiflik Durumu")

class Campaign(BaseModel):
    id: int = Field(..., description="Sistem ID")
    logo_ref: int = Field(..., description="Logo LOGICALREF")
    code: str = Field(..., description="Kampanya Kodu")
    name: str = Field(..., description="Kampanya Adı")
    description: Optional[str] = Field(None, description="Kampanya Açıklaması")
    start_date: Optional[str] = Field(None, description="Başlangıç Tarihi")
    end_date: Optional[str] = Field(None, description="Bitiş Tarihi")
    discount_rate: Optional[float] = Field(None, description="İndirim Oranı")
    campaign_type: Optional[str] = Field(None, description="Kampanya Tipi")
    is_active: bool = Field(..., description="Aktiflik Durumu")

# =====================================================
# SYNC ENDPOINTS (Logo'dan Çek)
# =====================================================

@router.post("/sync/salesmen")
async def sync_salesmen(company_id: int):
    """
    **Satış Elemanlarını Senkronize Et**

    Logo ERP'den satış temsilcilerini (SALESMAN) çeker ve yerel veritabanına kaydeder.
    Sadece 'Aktif' statüsündeki kayıtlar çekilir.
    """
    try:
        # Get company info
        company_query = f"SELECT logo_nr FROM companies WHERE id = {company_id}"
        company_result = db_manager.execute_pg_query(company_query)
        
        if not company_result:
            raise HTTPException(status_code=404, detail="Company not found")
        
        firma_no = str(company_result[0]['logo_nr']).zfill(3)
        
        # Logo'dan satış elemanlarını çek
        logo_query = f"""
            SELECT 
                LOGICALREF as logo_ref,
                CODE as code,
                DEFINITION_ as name,
                EMAIL as email,
                TELEPHONE1 as phone
            FROM LG_{firma_no}_SALESMAN WITH (NOLOCK)
            WHERE ACTIVE = 0  -- 0 = aktif
            ORDER BY CODE
        """
        
        salesmen = db_manager.execute_ms_query(logo_query)
        
        synced_count = 0
        for salesman in salesmen:
            # EXFIN DB'ye ekle/güncelle
            pg_query = f"""
                INSERT INTO salesmen (
                    company_id, logo_ref, code, name, email, phone, is_active
                )
                VALUES (
                    {company_id},
                    {salesman['logo_ref']},
                    '{salesman['code']}',
                    '{salesman['name'].replace("'", "''")}',
                    '{salesman.get('email', '') or ''}',
                    '{salesman.get('phone', '') or ''}',
                    true
                )
                ON CONFLICT (company_id, logo_ref) DO UPDATE SET
                    name = EXCLUDED.name,
                    email = EXCLUDED.email,
                    phone = EXCLUDED.phone,
                    last_sync = CURRENT_TIMESTAMP
            """
            db_manager.execute_pg_query(pg_query)
            synced_count += 1
        
        return {
            "success": True,
            "message": f"{synced_count} satış elemanı başarıyla senkronize edildi.",
            "count": synced_count
        }
        
    except Exception as e:
        logger.error(f"Sync salesmen error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync/brands")
async def sync_brands(company_id: int):
    """
    **Markaları Senkronize Et**
    
    Logo ERP'den ürün markalarını (MARK) çeker ve günceller.
    """
    try:
        company_query = f"SELECT logo_nr FROM companies WHERE id = {company_id}"
        company_result = db_manager.execute_pg_query(company_query)
        
        if not company_result:
            raise HTTPException(status_code=404, detail="Company not found")
        
        firma_no = str(company_result[0]['logo_nr']).zfill(3)
        
        logo_query = f"""
            SELECT 
                LOGICALREF as logo_ref,
                CODE as code,
                DESCR as name
            FROM LG_{firma_no}_MARK WITH (NOLOCK)
            WHERE ACTIVE = 0
            ORDER BY CODE
        """
        
        brands = db_manager.execute_ms_query(logo_query)
        
        synced_count = 0
        for brand in brands:
            pg_query = f"""
                INSERT INTO brands (company_id, logo_ref, code, name, is_active)
                VALUES (
                    {company_id},
                    {brand['logo_ref']},
                    '{brand['code']}',
                    '{brand['name'].replace("'", "''")}',
                    true
                )
                ON CONFLICT (company_id, logo_ref) DO UPDATE SET
                    name = EXCLUDED.name,
                    last_sync = CURRENT_TIMESTAMP
            """
            db_manager.execute_pg_query(pg_query)
            synced_count += 1
        
        return {
            "success": True,
            "message": f"{synced_count} marka başarıyla senkronize edildi.",
            "count": synced_count
        }
        
    except Exception as e:
        logger.error(f"Sync brands error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync/special-codes")
async def sync_special_codes(company_id: int, specode_type: str = "customer"):
    """
    **Özel Kodları Senkronize Et**
    
    Logo ERP'den Özel Kod (SPECODE) tanımlarını çeker.
    
    **Parametreler:**
    - `specode_type`: Çekilecek kod tipi ('customer', 'item', 'invoice', 'order')
    """
    try:
        company_query = f"SELECT logo_nr FROM companies WHERE id = {company_id}"
        company_result = db_manager.execute_pg_query(company_query)
        
        if not company_result:
            raise HTTPException(status_code=404, detail="Company not found")
        
        firma_no = str(company_result[0]['logo_nr']).zfill(3)
        
        # Tablo adını belirle
        table_map = {
            "customer": "CLSPECODE",
            "item": "ITSPECODE",
            "invoice": "INVOICESPECODE"
        }
        
        table_name = table_map.get(specode_type, "CLSPECODE")
        
        synced_count = 0
        
        # Her SPECODE için (1-5)
        for code_num in range(1, 6):
            logo_query = f"""
                SELECT 
                    LOGICALREF as logo_ref,
                    SPECODE as code,
                    DEFINITION_ as name,
                    CODETYPE as code_number
                FROM LG_{firma_no}_{table_name} WITH (NOLOCK)
                WHERE CODETYPE = {code_num}
                ORDER BY SPECODE
            """
            
            codes = db_manager.execute_ms_query(logo_query)
            
            for code in codes:
                pg_query = f"""
                    INSERT INTO special_codes (
                        company_id, logo_ref, specode_type, code_number, code, name, is_active
                    )
                    VALUES (
                        {company_id},
                        {code['logo_ref']},
                        '{specode_type}',
                        {code_num},
                        '{code['code']}',
                        '{code['name'].replace("'", "''")}',
                        true
                    )
                    ON CONFLICT (company_id, specode_type, code_number, logo_ref) DO UPDATE SET
                        name = EXCLUDED.name,
                        last_sync = CURRENT_TIMESTAMP
                """
                db_manager.execute_pg_query(pg_query)
                synced_count += 1
        
        return {
            "success": True,
            "message": f"{specode_type} için {synced_count} özel kod senkronize edildi.",
            "count": synced_count
        }
        
    except Exception as e:
        logger.error(f"Sync special codes error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync/campaigns")
async def sync_campaigns(company_id: int, period_id: int):
    """
    **Kampanyaları Senkronize Et**

    Logo ERP üzerindeki kampanya kartlarını (CAMPAIGN) çeker.
    """
    try:
        # Get company and period info
        query = f"""
            SELECT c.logo_nr, p.logo_period_nr
            FROM companies c
            JOIN periods p ON p.company_id = c.id
            WHERE c.id = {company_id} AND p.id = {period_id}
        """
        result = db_manager.execute_pg_query(query)
        
        if not result:
            raise HTTPException(status_code=404, detail="Company/Period not found")
        
        firma_no = str(result[0]['logo_nr']).zfill(3)
        period_no = str(result[0]['logo_period_nr']).zfill(2)
        
        # Logo'dan kampanyaları çek (örnek - Logo'da kampanya yapısına göre değişir)
        logo_query = f"""
            SELECT 
                LOGICALREF as logo_ref,
                CODE as code,
                NAME as name,
                BEGDATE as start_date,
                ENDDATE as end_date,
                DISCRATE as discount_rate
            FROM LG_{firma_no}_{period_no}_CAMPAIGN WITH (NOLOCK)
            WHERE ACTIVE = 0
            ORDER BY CODE
        """
        
        try:
            campaigns = db_manager.execute_ms_query(logo_query)
        except:
            # Kampanya tablosu yoksa boş liste dön
            campaigns = []
        
        synced_count = 0
        for campaign in campaigns:
            pg_query = f"""
                INSERT INTO campaigns (
                    company_id, period_id, logo_ref, code, name, 
                    start_date, end_date, discount_rate, is_active
                )
                VALUES (
                    {company_id},
                    {period_id},
                    {campaign['logo_ref']},
                    '{campaign['code']}',
                    '{campaign['name'].replace("'", "''")}',
                    '{campaign.get('start_date', '')}',
                    '{campaign.get('end_date', '')}',
                    {campaign.get('discount_rate', 0)},
                    true
                )
                ON CONFLICT (company_id, period_id, logo_ref) DO UPDATE SET
                    name = EXCLUDED.name,
                    start_date = EXCLUDED.start_date,
                    end_date = EXCLUDED.end_date,
                    discount_rate = EXCLUDED.discount_rate,
                    last_sync = CURRENT_TIMESTAMP
            """
            db_manager.execute_pg_query(pg_query)
            synced_count += 1
        
        return {
            "success": True,
            "message": f"{synced_count} kampanya senkronize edildi.",
            "count": synced_count
        }
        
    except Exception as e:
        logger.error(f"Sync campaigns error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync/all")
async def sync_all_logo_data(company_id: int, period_id: int = None):
    """
    **Tüm Verileri Senkronize Et**
    
    Logo ERP'den tüm yardımcı verileri tek seferde çeker:
    - Satış Elemanları
    - Markalar
    - Özel Kodlar (Müşteri & Malzeme)
    - Kampanyalar (Dönem seçilirse)
    """
    try:
        results = {}
        
        # Salesmen
        salesmen_result = await sync_salesmen(company_id)
        results['salesmen'] = salesmen_result['count']
        
        # Brands
        brands_result = await sync_brands(company_id)
        results['brands'] = brands_result['count']
        
        # Special codes (customer)
        customer_codes = await sync_special_codes(company_id, "customer")
        results['customer_special_codes'] = customer_codes['count']
        
        # Special codes (item)
        item_codes = await sync_special_codes(company_id, "item")
        results['item_special_codes'] = item_codes['count']
        
        # Campaigns (if period provided)
        if period_id:
            campaigns_result = await sync_campaigns(company_id, period_id)
            results['campaigns'] = campaigns_result['count']
        
        return {
            "success": True,
            "message": "Tüm Logo verileri başarıyla senkronize edildi.",
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Sync all error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =====================================================
# GET ENDPOINTS (Cache'den Oku)
# =====================================================

@router.get("/salesmen", response_model=List[Salesman])
async def get_salesmen(company_id: int):
    """
    **Satış Elemanlarını Listele**

    Yerel veritabanındaki satış temsilcilerini döner.
    """
    try:
        query = f"""
            SELECT id, logo_ref, code, name, email, phone, is_active
            FROM salesmen
            WHERE company_id = {company_id} AND is_active = true
            ORDER BY name
        """
        results = db_manager.execute_pg_query(query)
        return results
    except Exception as e:
        logger.error(f"Get salesmen error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/brands", response_model=List[Brand])
async def get_brands(company_id: int):
    """
    **Markaları Listele**

    Yerel veritabanındaki markaları döner.
    """
    try:
        query = f"""
            SELECT id, logo_ref, code, name, description, is_active
            FROM brands
            WHERE company_id = {company_id} AND is_active = true
            ORDER BY name
        """
        results = db_manager.execute_pg_query(query)
        return results
    except Exception as e:
        logger.error(f"Get brands error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/special-codes", response_model=List[SpecialCode])
async def get_special_codes(company_id: int, specode_type: str = "customer"):
    """
    **Özel Kodları Listele**

    Belirtilen tipteki özel kodları listeler.
    """
    try:
        query = f"""
            SELECT id, specode_type, code_number, code, name, is_active
            FROM special_codes
            WHERE company_id = {company_id} 
              AND specode_type = '{specode_type}'
              AND is_active = true
            ORDER BY code_number, code
        """
        results = db_manager.execute_pg_query(query)
        return results
    except Exception as e:
        logger.error(f"Get special codes error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/campaigns", response_model=List[Campaign])
async def get_campaigns(company_id: int, period_id: int):
    """
    **Kampanyaları Listele**

    Aktif kampanyaları listeler.
    """
    try:
        query = f"""
            SELECT id, logo_ref, code, name, description, 
                   start_date::text, end_date::text, 
                   discount_rate, campaign_type, is_active
            FROM campaigns
            WHERE company_id = {company_id} 
              AND period_id = {period_id}
              AND is_active = true
            ORDER BY start_date DESC
        """
        results = db_manager.execute_pg_query(query)
        return results
    except Exception as e:
        logger.error(f"Get campaigns error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
