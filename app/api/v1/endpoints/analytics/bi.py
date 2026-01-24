import time
import jwt
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
from app.core.config import settings

router = APIRouter()

@router.get("/dashboard/{dashboard_id}", response_model=Dict[str, str])
def get_metabase_dashboard_url(
    dashboard_id: int,
    company_id: Optional[str] = None,
    branch_id: Optional[str] = None,
    period: Optional[str] = None
):
    """
    **Metabase Dashboard URL**

    Metabase panolarını gömülü (embed) olarak göstermek için imzalı URL oluşturur.
    
    **Filtreler:**
    - `company_id`: Firma bazlı filtre
    - `branch_id`: Şube bazlı filtre
    - `period`: Dönem filtresi
    
    Bu parametreler Metabase tarafında 'Locked Parameter' olarak tanımlanmalıdır.
    """
    
    if not settings.METABASE_SECRET_KEY or settings.METABASE_SECRET_KEY == "YOUR_METABASE_SECRET_KEY":
        raise HTTPException(status_code=500, detail="Metabase Secret Key is not configured.")

    payload = {
        "resource": {"dashboard": dashboard_id},
        "params": {},
        "exp": round(time.time()) + (60 * 60) # 1 hour expiration
    }

    # Add filters if they are provided (Locked Parameters in Metabase)
    # Ensure your Metabase Dashboard has these variables set up as locked parameters.
    if company_id:
        payload["params"]["company_id"] = company_id
    if branch_id:
        payload["params"]["branch"] = branch_id
    if period:
        payload["params"]["period"] = period

    try:
        token = jwt.encode(payload, settings.METABASE_SECRET_KEY, algorithm="HS256")
        
        # Determine strictness options (bordered, titled, etc.)
        # These controls can be exposed as query params if needed
        iframe_url = f"{settings.METABASE_SITE_URL}/embed/dashboard/{token}#bordered=true&titled=true"
        
        return {"iframe_url": iframe_url}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error signing URL: {str(e)}")
