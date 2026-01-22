from fastapi import APIRouter, HTTPException, Depends
from loguru import logger
from app.services.logo_service import logo_service
from app.core.database import db_manager
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()

# =====================================================
# SCHEMAS
# =====================================================

class Company(BaseModel):
    id: int
    logo_nr: int
    code: str
    name: str
    is_active: bool
    is_default: bool

class Period(BaseModel):
    id: int
    company_id: int
    logo_period_nr: int
    code: str
    name: str
    start_date: Optional[str]
    end_date: Optional[str]
    is_active: bool
    is_default: bool

# =====================================================
# ENDPOINTS
# =====================================================

@router.get("/companies", response_model=List[Company])
async def get_companies():
    """
    Get all companies from EXFIN database
    """
    try:
        query = """
            SELECT id, logo_nr, code, name, is_active, is_default
            FROM companies
            WHERE is_active = true
            ORDER BY is_default DESC, name ASC
        """
        results = db_manager.execute_pg_query(query)
        return results
    except Exception as e:
        logger.error(f"Get companies error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/companies/{company_id}/periods", response_model=List[Period])
async def get_periods(company_id: int):
    """
    Get all periods for a company
    """
    try:
        query = f"""
            SELECT id, company_id, logo_period_nr, code, name, 
                   start_date::text, end_date::text, is_active, is_default
            FROM periods
            WHERE company_id = {company_id} AND is_active = true
            ORDER BY is_default DESC, logo_period_nr DESC
        """
        results = db_manager.execute_pg_query(query)
        return results
    except Exception as e:
        logger.error(f"Get periods error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/default")
async def get_default_company_period():
    """
    Get default company and period
    
    Returns the default company and its default period.
    Used for initial login.
    """
    try:
        query = """
            SELECT 
                c.id as company_id,
                c.logo_nr,
                c.code as company_code,
                c.name as company_name,
                p.id as period_id,
                p.logo_period_nr,
                p.code as period_code,
                p.name as period_name
            FROM companies c
            JOIN periods p ON p.company_id = c.id AND p.is_default = true
            WHERE c.is_default = true
            LIMIT 1
        """
        results = db_manager.execute_pg_query(query)
        
        if not results:
            raise HTTPException(
                status_code=404,
                detail="No default company/period found. Please run sync first."
            )
        
        return {
            "success": True,
            "data": results[0]
        }
    except Exception as e:
        logger.error(f"Get default company/period error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync/from-logo")
async def sync_companies_from_logo():
    """
    Sync companies and periods from Logo ERP
    
    Reads L_CAPIFIRM table from Logo and syncs to EXFIN database.
    """
    try:
        # Logo'dan firmaları çek
        logo_query = """
            SELECT 
                NR as logo_nr,
                CODE as code,
                NAME as name,
                TAXOFFICE as tax_office,
                TAXNR as tax_number,
                ADDR1 as address
            FROM L_CAPIFIRM WITH (NOLOCK)
            WHERE NR > 0
            ORDER BY NR
        """
        
        logo_companies = db_manager.execute_ms_query(logo_query)
        
        if not logo_companies:
            raise HTTPException(
                status_code=404,
                detail="No companies found in Logo ERP"
            )
        
        synced_companies = []
        synced_periods = []
        
        for logo_company in logo_companies:
            # EXFIN DB'ye ekle/güncelle
            pg_query = f"""
                INSERT INTO companies (logo_nr, code, name, tax_office, tax_number, address, is_active)
                VALUES (
                    {logo_company['logo_nr']},
                    '{logo_company['code']}',
                    '{logo_company['name'].replace("'", "''")}',
                    '{logo_company.get('tax_office', '') or ''}',
                    '{logo_company.get('tax_number', '') or ''}',
                    '{logo_company.get('address', '') or ''}',
                    true
                )
                ON CONFLICT (logo_nr) DO UPDATE SET
                    name = EXCLUDED.name,
                    tax_office = EXCLUDED.tax_office,
                    tax_number = EXCLUDED.tax_number,
                    address = EXCLUDED.address,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING id, logo_nr, code, name
            """
            
            company_result = db_manager.execute_pg_query(pg_query)
            synced_companies.append(company_result[0])
            
            # Dönemleri çek (L_CAPIPERIOD)
            periods_query = f"""
                SELECT 
                    PERNR as period_nr,
                    BEGDATE as start_date,
                    ENDDATE as end_date
                FROM L_CAPIPERIOD WITH (NOLOCK)
                WHERE FIRMNR = {logo_company['logo_nr']}
                ORDER BY PERNR
            """
            
            logo_periods = db_manager.execute_ms_query(periods_query)
            
            for logo_period in logo_periods:
                # Dönem adını yıldan çıkar
                year = logo_period['start_date'].year if logo_period.get('start_date') else logo_period['period_nr']
                
                period_insert = f"""
                    INSERT INTO periods (
                        company_id, logo_period_nr, code, name, 
                        start_date, end_date, is_active
                    )
                    SELECT 
                        {company_result[0]['id']},
                        {logo_period['period_nr']},
                        '{logo_period['period_nr']:02d}',
                        '{year}',
                        '{logo_period.get('start_date', '')}',
                        '{logo_period.get('end_date', '')}',
                        true
                    ON CONFLICT (company_id, logo_period_nr) DO UPDATE SET
                        start_date = EXCLUDED.start_date,
                        end_date = EXCLUDED.end_date,
                        updated_at = CURRENT_TIMESTAMP
                    RETURNING id, logo_period_nr, name
                """
                
                period_result = db_manager.execute_pg_query(period_insert)
                synced_periods.append(period_result[0])
        
        return {
            "success": True,
            "message": "Companies and periods synced from Logo ERP",
            "synced_companies": len(synced_companies),
            "synced_periods": len(synced_periods),
            "companies": synced_companies
        }
        
    except Exception as e:
        logger.error(f"Sync from Logo error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/companies/{company_id}/set-default")
async def set_default_company(company_id: int):
    """
    Set a company as default
    """
    try:
        # Önce tüm firmaların default'unu kaldır
        db_manager.execute_pg_query("UPDATE companies SET is_default = false")
        
        # Seçili firmayı default yap
        query = f"""
            UPDATE companies 
            SET is_default = true, updated_at = CURRENT_TIMESTAMP
            WHERE id = {company_id}
            RETURNING id, code, name
        """
        result = db_manager.execute_pg_query(query)
        
        if not result:
            raise HTTPException(status_code=404, detail="Company not found")
        
        return {
            "success": True,
            "message": "Default company updated",
            "company": result[0]
        }
    except Exception as e:
        logger.error(f"Set default company error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/periods/{period_id}/set-default")
async def set_default_period(period_id: int):
    """
    Set a period as default for its company
    """
    try:
        # Önce dönemin company_id'sini al
        get_company_query = f"""
            SELECT company_id FROM periods WHERE id = {period_id}
        """
        company_result = db_manager.execute_pg_query(get_company_query)
        
        if not company_result:
            raise HTTPException(status_code=404, detail="Period not found")
        
        company_id = company_result[0]['company_id']
        
        # O firmadaki tüm dönemlerin default'unu kaldır
        db_manager.execute_pg_query(
            f"UPDATE periods SET is_default = false WHERE company_id = {company_id}"
        )
        
        # Seçili dönemi default yap
        query = f"""
            UPDATE periods 
            SET is_default = true, updated_at = CURRENT_TIMESTAMP
            WHERE id = {period_id}
            RETURNING id, code, name
        """
        result = db_manager.execute_pg_query(query)
        
        return {
            "success": True,
            "message": "Default period updated",
            "period": result[0]
        }
    except Exception as e:
        logger.error(f"Set default period error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
