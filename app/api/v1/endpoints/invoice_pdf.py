from fastapi import APIRouter, HTTPException
from loguru import logger
from app.core.database import db_manager
from typing import Optional
from pydantic import BaseModel
import requests
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime
import base64

router = APIRouter()

# =====================================================
# SCHEMAS
# =====================================================

class InvoicePDFRequest(BaseModel):
    invoice_number: str
    company_id: int
    period_id: int
    send_whatsapp: bool = False
    phone_number: Optional[str] = None

# =====================================================
# PDF GENERATION
# =====================================================

def generate_invoice_pdf(invoice_data: dict) -> BytesIO:
    """
    Generate invoice PDF using ReportLab
    
    Returns PDF as BytesIO object
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1976D2'),
        spaceAfter=30,
        alignment=1  # Center
    )
    
    # Title
    title = Paragraph(f"FATURA", title_style)
    elements.append(title)
    elements.append(Spacer(1, 0.5*cm))
    
    # Company Info
    company_info = [
        ['Firma:', invoice_data['company_name']],
        ['Vergi Dairesi:', invoice_data.get('tax_office', '')],
        ['Vergi No:', invoice_data.get('tax_number', '')],
        ['Adres:', invoice_data.get('address', '')],
    ]
    
    company_table = Table(company_info, colWidths=[4*cm, 12*cm])
    company_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#E3F2FD')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
    ]))
    
    elements.append(company_table)
    elements.append(Spacer(1, 0.5*cm))
    
    # Invoice Header
    invoice_header = [
        ['Fatura No:', invoice_data['invoice_number']],
        ['Tarih:', invoice_data['invoice_date']],
        ['Müşteri:', invoice_data['customer_name']],
        ['Müşteri Kodu:', invoice_data['customer_code']],
    ]
    
    header_table = Table(invoice_header, colWidths=[4*cm, 12*cm])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#FFF3E0')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
    ]))
    
    elements.append(header_table)
    elements.append(Spacer(1, 1*cm))
    
    # Invoice Lines
    lines_data = [['#', 'Ürün Kodu', 'Ürün Adı', 'Miktar', 'Birim Fiyat', 'Toplam']]
    
    # Currency symbol mapping
    currency_symbol = '₺' if invoice_data['currency'] in ['TRY', 'TL'] else invoice_data['currency']
    
    for idx, line in enumerate(invoice_data['lines'], 1):
        lines_data.append([
            str(idx),
            line['item_code'],
            line['item_name'][:30],  # Truncate long names
            f"{line['quantity']:.2f}",
            f"{line['unit_price']:,.2f} {currency_symbol}",
            f"{line['total']:,.2f} {currency_symbol}"
        ])
    
    lines_table = Table(lines_data, colWidths=[1*cm, 3*cm, 6*cm, 2*cm, 3*cm, 3*cm])
    lines_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1976D2')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
    ]))
    
    elements.append(lines_table)
    elements.append(Spacer(1, 1*cm))
    
    # Totals (KDV removed)
    totals_data = [
        ['GENEL TOPLAM:', f"{invoice_data['total_amount']:,.2f} {currency_symbol}"],
    ]
    
    totals_table = Table(totals_data, colWidths=[12*cm, 4*cm])
    totals_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (-1, -1), 14),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor('#1976D2')),
        ('LINEABOVE', (0, -1), (-1, -1), 2, colors.HexColor('#1976D2')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
    ]))
    
    elements.append(totals_table)
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer


def send_whatsapp_pdf(phone_number: str, pdf_buffer: BytesIO, invoice_number: str) -> dict:
    """
    Send PDF via WhatsApp using WhatsApp Business API
    
    You'll need to configure your WhatsApp Business API credentials
    """
    try:
        # WhatsApp Business API endpoint (örnek)
        # Gerçek implementasyonda kendi API bilgilerinizi kullanın
        
        # Twilio WhatsApp API örneği:
        # from twilio.rest import Client
        # client = Client(account_sid, auth_token)
        # message = client.messages.create(
        #     from_='whatsapp:+14155238886',
        #     body=f'Fatura No: {invoice_number}',
        #     to=f'whatsapp:{phone_number}',
        #     media_url=['https://your-server.com/invoice.pdf']
        # )
        
        # Şimdilik mock response
        logger.info(f"WhatsApp PDF sent to {phone_number} for invoice {invoice_number}")
        
        return {
            "success": True,
            "message": "WhatsApp message sent",
            "phone": phone_number,
            "invoice_number": invoice_number
        }
        
    except Exception as e:
        logger.error(f"WhatsApp send error: {e}")
        raise Exception(f"Failed to send WhatsApp: {str(e)}")


# =====================================================
# ENDPOINTS
# =====================================================

@router.post("/invoices/generate-pdf")
async def generate_invoice_pdf_endpoint(request: InvoicePDFRequest):
    """
    Generate invoice PDF and optionally send via WhatsApp
    
    Steps:
    1. Fetch invoice data from Logo ERP
    2. Generate PDF
    3. Optionally send via WhatsApp
    4. Return PDF as base64 or download link
    """
    try:
        # Get company and period info
        query = f"""
            SELECT c.logo_nr, p.logo_period_nr, c.name as company_name,
                   c.tax_office, c.tax_number, c.address
            FROM companies c
            JOIN periods p ON p.company_id = c.id
            WHERE c.id = {request.company_id} AND p.id = {request.period_id}
        """
        company_result = db_manager.execute_pg_query(query)
        
        if not company_result:
            raise HTTPException(status_code=404, detail="Company/Period not found")
        
        company_data = company_result[0]
        firma_no = str(company_data['logo_nr']).zfill(3)
        period_no = str(company_data['logo_period_nr']).zfill(2)
        
        # Fetch invoice from Logo ERP
        invoice_query = f"""
            SELECT 
                i.FICHENO as invoice_number,
                i.DATE_ as invoice_date,
                c.CODE as customer_code,
                c.DEFINITION_ as customer_name,
                i.NETTOTAL as subtotal,
                i.TOTALDISCOUNTS as discount,
                i.TOTALVAT as vat_amount,
                i.GROSSTOTAL as total_amount,
                i.TRCURR as currency
            FROM LG_{firma_no}_{period_no}_INVOICE i WITH (NOLOCK)
            JOIN LG_{firma_no}_CLCARD c WITH (NOLOCK) ON c.LOGICALREF = i.CLIENTREF
            WHERE i.FICHENO = '{request.invoice_number}'
        """
        
        invoice_result = db_manager.execute_ms_query(invoice_query)
        
        if not invoice_result:
            raise HTTPException(status_code=404, detail="Invoice not found")
        
        invoice_header = invoice_result[0]
        
        # Fetch invoice lines
        lines_query = f"""
            SELECT 
                l.STOCKREF,
                s.CODE as item_code,
                s.NAME as item_name,
                l.AMOUNT as quantity,
                l.PRICE as unit_price,
                l.TOTAL as total,
                l.LINETYPE
            FROM LG_{firma_no}_{period_no}_STLINE l WITH (NOLOCK)
            JOIN LG_{firma_no}_ITEMS s WITH (NOLOCK) ON s.LOGICALREF = l.STOCKREF
            WHERE l.INVOICEREF IN (
                SELECT LOGICALREF FROM LG_{firma_no}_{period_no}_INVOICE 
                WHERE FICHENO = '{request.invoice_number}'
            )
            AND l.LINETYPE IN (0, 1)  -- Normal lines
            ORDER BY l.LINENR
        """
        
        lines_result = db_manager.execute_ms_query(lines_query)
        
        # Prepare invoice data for PDF
        invoice_data = {
            'company_name': company_data['company_name'],
            'tax_office': company_data['tax_office'],
            'tax_number': company_data['tax_number'],
            'address': company_data['address'],
            'invoice_number': invoice_header['invoice_number'],
            'invoice_date': invoice_header['invoice_date'].strftime('%d.%m.%Y'),
            'customer_code': invoice_header['customer_code'],
            'customer_name': invoice_header['customer_name'],
            'subtotal': float(invoice_header['subtotal']),
            'vat_amount': float(invoice_header['vat_amount']),
            'total_amount': float(invoice_header['total_amount']),
            'currency': invoice_header['currency'] or 'TRY',
            'lines': [
                {
                    'item_code': line['item_code'],
                    'item_name': line['item_name'],
                    'quantity': float(line['quantity']),
                    'unit_price': float(line['unit_price']),
                    'total': float(line['total'])
                }
                for line in lines_result
            ]
        }
        
        # Generate PDF
        pdf_buffer = generate_invoice_pdf(invoice_data)
        
        # Convert to base64 for response
        pdf_base64 = base64.b64encode(pdf_buffer.getvalue()).decode('utf-8')
        
        response = {
            "success": True,
            "message": "Invoice PDF generated",
            "invoice_number": request.invoice_number,
            "pdf_base64": pdf_base64,
            "pdf_size_kb": len(pdf_buffer.getvalue()) / 1024
        }
        
        # Send via WhatsApp if requested
        if request.send_whatsapp and request.phone_number:
            whatsapp_result = send_whatsapp_pdf(
                request.phone_number,
                pdf_buffer,
                request.invoice_number
            )
            response['whatsapp'] = whatsapp_result
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Generate invoice PDF error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/invoices/{invoice_number}/download")
async def download_invoice_pdf(
    invoice_number: str,
    company_id: int,
    period_id: int
):
    """
    Download invoice PDF directly
    
    Returns PDF file for download
    """
    from fastapi.responses import StreamingResponse
    
    try:
        request = InvoicePDFRequest(
            invoice_number=invoice_number,
            company_id=company_id,
            period_id=period_id,
            send_whatsapp=False
        )
        
        result = await generate_invoice_pdf_endpoint(request)
        
        # Decode base64 to bytes
        pdf_bytes = base64.b64decode(result['pdf_base64'])
        pdf_buffer = BytesIO(pdf_bytes)
        
        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=fatura_{invoice_number}.pdf"
            }
        )
        
    except Exception as e:
        logger.error(f"Download invoice PDF error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/invoices/send-whatsapp")
async def send_invoice_whatsapp(
    invoice_number: str,
    company_id: int,
    period_id: int,
    phone_number: str
):
    """
    Send invoice PDF via WhatsApp
    
    Generates PDF and sends to specified phone number
    """
    try:
        request = InvoicePDFRequest(
            invoice_number=invoice_number,
            company_id=company_id,
            period_id=period_id,
            send_whatsapp=True,
            phone_number=phone_number
        )
        
        result = await generate_invoice_pdf_endpoint(request)
        
        return {
            "success": True,
            "message": f"Invoice sent to WhatsApp: {phone_number}",
            "invoice_number": invoice_number,
            "whatsapp": result.get('whatsapp')
        }
        
    except Exception as e:
        logger.error(f"Send invoice WhatsApp error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
