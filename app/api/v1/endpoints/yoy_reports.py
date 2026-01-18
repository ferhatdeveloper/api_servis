from fastapi import APIRouter, HTTPException
from app.services.logo_service import logo_service
from loguru import logger

router = APIRouter()

@router.get("/yoy/daily")
async def get_yoy_daily_comparison(firma: str = None, period: str = None):
    """
    Year-over-Year Daily Comparison
    
    Compares today's performance vs same day last year:
    - Invoice count
    - Total revenue
    - Average order value
    - Active customers
    - Stock movements
    """
    try:
        result = await logo_service.get_yoy_daily_comparison(firma, period)
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        logger.error(f"YoY Daily Comparison API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/yoy/weekly")
async def get_yoy_weekly_comparison(firma: str = None, period: str = None):
    """
    Year-over-Year Weekly Comparison
    
    Compares this week's performance vs same week last year:
    - Invoice count
    - Total revenue
    - Collections
    - Active customers
    """
    try:
        result = await logo_service.get_yoy_weekly_comparison(firma, period)
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        logger.error(f"YoY Weekly Comparison API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/yoy/monthly")
async def get_yoy_monthly_comparison(firma: str = None, period: str = None):
    """
    Year-over-Year Monthly Comparison
    
    Compares this month's performance vs same month last year:
    - Invoice count
    - Total revenue
    - Collections
    - Stock movements
    - New customers
    """
    try:
        result = await logo_service.get_yoy_monthly_comparison(firma, period)
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        logger.error(f"YoY Monthly Comparison API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
