from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import io
import os
from datetime import datetime

class PdfService:
    def __init__(self):
        # Register a font that supports Turkish characters if available
        # Using Helvetica (standard) which has limited char support, 
        # or try to use a standard path if needed. 
        # For simplicity in this env, we use standard fonts but may map chars.
        pass

    def create_statement_pdf(self, customer_info, transactions):
        """
        Generates a PDF statement.
        customer_info: dict {name, code, address, current_balance}
        transactions: list of dicts {date, type, doc_no, debit, credit, balance}
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        elements = []
        styles = getSampleStyleSheet()
        
        # 1. Header
        title_style = styles["Heading1"]
        title_style.alignment = 1 # Center
        elements.append(Paragraph("CARI HESAP EKSTRESI", title_style))
        elements.append(Spacer(1, 20))
        
        # 2. Customer Info
        p_style = styles["Normal"]
        elements.append(Paragraph(f"<b>Musteri:</b> {customer_info.get('name')}", p_style))
        elements.append(Paragraph(f"<b>Kod:</b> {customer_info.get('code')}", p_style))
        elements.append(Paragraph(f"<b>Tarih:</b> {datetime.now().strftime('%d.%m.%Y')}", p_style))
        elements.append(Spacer(1, 20))
        
        # 3. Table Data
        data = [["Tarih", "Islem Turu", "Belge No", "Borc", "Alacak", "Bakiye"]]
        
        for t in transactions:
            data.append([
                t.get("date"),
                t.get("type"),
                t.get("doc_no"),
                f"{t.get('debit', 0):,.2f}",
                f"{t.get('credit', 0):,.2f}",
                f"{t.get('balance', 0):,.2f}"
            ])
            
        # 4. Table Styling
        t = Table(data)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(t)
        
        # 5. Footer / Final Balance
        elements.append(Spacer(1, 20))
        final_bal = customer_info.get('current_balance', 0)
        bal_text = f"Guncel Bakiye: {final_bal:,.2f} TL"
        elements.append(Paragraph(f"<b>{bal_text}</b>", styles["Heading2"]))
        
        doc.build(elements)
        buffer.seek(0)
        return buffer
