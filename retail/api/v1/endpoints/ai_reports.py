"""
AI Reports Endpoint
ChatGPT ile rapor analizi ve Ã¶neriler
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import json
from datetime import datetime
from retail.core.config import settings

router = APIRouter(prefix="/ai-reports", tags=["AI Reports"])

# OpenAI API Key - Settings'den al
OPENAI_API_KEY = settings.OPENAI_API_KEY
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"

class ReportAnalysisRequest(BaseModel):
    question: str
    report_data: Dict[str, Any]
    conversation_history: Optional[List[Dict[str, str]]] = None

class ReportAnalysisResponse(BaseModel):
    answer: str
    suggested_reports: List[str]
    insights: Optional[List[str]] = None
    data_summary: Optional[Dict[str, Any]] = None

def format_report_data_for_ai(report_data: Dict[str, Any]) -> str:
    """Rapor verilerini AI iÃ§in formatla"""
    summary = []
    
    # SatÄ±ÅŸ Ã¶zeti
    if 'sales' in report_data:
        sales = report_data['sales']
        total_sales = len(sales) if isinstance(sales, list) else 0
        total_revenue = sum(s.get('total', 0) for s in sales) if isinstance(sales, list) else 0
        summary.append(f"Toplam SatÄ±ÅŸ: {total_sales} iÅŸlem, Toplam Ciro: {total_revenue:,.2f} â‚º")
    
    # GÃ¼nlÃ¼k satÄ±ÅŸlar
    if 'dailySales' in report_data:
        daily = report_data['dailySales']
        daily_count = len(daily) if isinstance(daily, list) else 0
        daily_total = report_data.get('dailyTotal', 0)
        summary.append(f"BugÃ¼nkÃ¼ SatÄ±ÅŸ: {daily_count} iÅŸlem, Ciro: {daily_total:,.2f} â‚º")
    
    # ÃœrÃ¼n satÄ±ÅŸlarÄ±
    if 'productSales' in report_data:
        products = report_data['productSales']
        if isinstance(products, list) and len(products) > 0:
            top_products = sorted(products, key=lambda x: x.get('revenue', 0), reverse=True)[:5]
            summary.append(f"En Ã§ok satan 5 Ã¼rÃ¼n: {', '.join([p.get('product', {}).get('name', 'N/A') for p in top_products])}")
    
    # Kasiyer performansÄ±
    if 'cashierPerformance' in report_data:
        cashiers = report_data['cashierPerformance']
        if isinstance(cashiers, list) and len(cashiers) > 0:
            top_cashier = max(cashiers, key=lambda x: x.get('totalRevenue', 0))
            summary.append(f"En iyi kasiyer: {top_cashier.get('name', 'N/A')} - {top_cashier.get('totalRevenue', 0):,.2f} â‚º")
    
    # Kategori analizi
    if 'categoryAnalysis' in report_data:
        categories = report_data['categoryAnalysis']
        if isinstance(categories, list) and len(categories) > 0:
            top_category = max(categories, key=lambda x: x.get('totalRevenue', 0))
            summary.append(f"En Ã§ok satan kategori: {top_category.get('name', 'N/A')} - {top_category.get('totalRevenue', 0):,.2f} â‚º")
    
    # Saatlik analiz
    if 'hourlyAnalysis' in report_data:
        hourly = report_data['hourlyAnalysis']
        if isinstance(hourly, list) and len(hourly) > 0:
            peak_hour = max(hourly, key=lambda x: x.get('revenue', 0))
            summary.append(f"En yoÄŸun saat: {peak_hour.get('hour', 'N/A')}:00 - {peak_hour.get('revenue', 0):,.2f} â‚º")
    
    return "\n".join(summary)

async def call_openai_api(
    question: str,
    report_data_summary: str,
    conversation_history: Optional[List[Dict[str, str]]] = None
) -> str:
    """OpenAI API'yi Ã§aÄŸÄ±r"""
    
    if not OPENAI_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="OpenAI API key yapÄ±landÄ±rÄ±lmamÄ±ÅŸ. LÃ¼tfen OPENAI_API_KEY environment variable'Ä±nÄ± ayarlayÄ±n."
        )
    
    import httpx
    
    # System prompt
    system_prompt = """Sen bir perakende satÄ±ÅŸ analiz uzmanÄ±sÄ±n. KullanÄ±cÄ±ya rapor verilerine dayalÄ± olarak:
1. Net ve anlaÅŸÄ±lÄ±r cevaplar ver
2. Verilerden Ã§Ä±karÄ±mlar yap
3. Ã–neriler sun
4. TÃ¼rkÃ§e yanÄ±t ver
5. SayÄ±sal verileri formatla (Ã¶rn: 1.234,56 â‚º)
6. Grafik ve tablo Ã¶nerileri yapabilirsin
"""
    
    # Conversation history oluÅŸtur
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "system", "content": f"Rapor Verileri Ã–zeti:\n{report_data_summary}"}
    ]
    
    # GeÃ§miÅŸ konuÅŸmalarÄ± ekle
    if conversation_history:
        for msg in conversation_history[-5:]:  # Son 5 mesaj
            messages.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", "")
            })
    
    # KullanÄ±cÄ± sorusu
    messages.append({
        "role": "user",
        "content": question
    })
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                OPENAI_API_URL,
                headers={
                    "Authorization": f"Bearer {OPENAI_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-4o-mini",  # Daha uygun fiyatlÄ± model
                    "messages": messages,
                    "temperature": 0.7,
                    "max_tokens": 1000
                }
            )
            
            if response.status_code != 200:
                error_data = response.json() if response.content else {}
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"OpenAI API hatasÄ±: {error_data.get('error', {}).get('message', 'Bilinmeyen hata')}"
                )
            
            result = response.json()
            return result["choices"][0]["message"]["content"]
            
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="OpenAI API zaman aÅŸÄ±mÄ±")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OpenAI API Ã§aÄŸrÄ±sÄ± baÅŸarÄ±sÄ±z: {str(e)}")

@router.post("/analyze", response_model=ReportAnalysisResponse)
async def analyze_report_with_ai(request: ReportAnalysisRequest):
    """
    ChatGPT ile rapor analizi yap
    
    - Soruyu analiz eder
    - Rapor verilerine gÃ¶re cevap Ã¼retir
    - Ã–neriler sunar
    """
    
    try:
        # Rapor verilerini formatla
        report_summary = format_report_data_for_ai(request.report_data)
        
        # OpenAI API'yi Ã§aÄŸÄ±r
        ai_response = await call_openai_api(
            question=request.question,
            report_data_summary=report_summary,
            conversation_history=request.conversation_history
        )
        
        # Ã–nerilen raporlarÄ± Ã§Ä±kar (basit parsing)
        suggested_reports = []
        if "gÃ¼nlÃ¼k" in request.question.lower() or "bugÃ¼n" in request.question.lower():
            suggested_reports.append("GÃ¼nlÃ¼k Rapor")
        if "Ã¼rÃ¼n" in request.question.lower():
            suggested_reports.append("Top ÃœrÃ¼nler")
        if "kasiyer" in request.question.lower():
            suggested_reports.append("Kasiyer PerformansÄ±")
        if "kategori" in request.question.lower():
            suggested_reports.append("Kategori Analizi")
        if "stok" in request.question.lower():
            suggested_reports.append("Stok Durumu")
        
        if not suggested_reports:
            suggested_reports = ["GÃ¼nlÃ¼k Rapor", "Z Raporu"]
        
        return ReportAnalysisResponse(
            answer=ai_response,
            suggested_reports=suggested_reports,
            insights=None,
            data_summary=None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Rapor analizi baÅŸarÄ±sÄ±z: {str(e)}"
        )

@router.get("/health")
async def health_check():
    """AI servis saÄŸlÄ±k kontrolÃ¼"""
    return {
        "status": "ok",
        "openai_configured": bool(OPENAI_API_KEY),
        "timestamp": datetime.now().isoformat()
    }

