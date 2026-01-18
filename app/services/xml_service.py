import xml.etree.ElementTree as ET
from datetime import datetime
from loguru import logger
from ..core.database import db_manager

class XmlService:
    def __init__(self):
        pass

    def _prettify(self, elem):
        """Return a pretty-printed XML string for the Element."""
        from xml.dom import minidom
        rough_string = ET.tostring(elem, 'utf-8')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ")

    async def generate_sales_invoice_xml(self, invoice_id: str):
        """Generates Logo XML for a Sales Invoice (Verilen Hizmet / Toptan Satış)"""
        # Fetch Data
        order_query = "SELECT * FROM sales_orders WHERE id = %s"
        order_res = db_manager.execute_pg_query(order_query, (invoice_id,))
        if not order_res: return None, "Invoice not found"
        order = order_res[0]
        
        items_query = "SELECT * FROM sales_order_items WHERE order_id = %s"
        items = db_manager.execute_pg_query(items_query, (invoice_id,))
        
        customer_id = order['customer_id']
        cust_res = db_manager.execute_pg_query(f"SELECT * FROM customers WHERE id = {customer_id}")
        customer = cust_res[0] if cust_res else {}

        # Build XML
        root = ET.Element("SALES_INVOICES")
        invoice = ET.SubElement(root, "INVOICE")
        inv_no = order.get('order_number') or f"INV{datetime.now().strftime('%d%H%M')}"
        
        # Header
        ET.SubElement(invoice, "TYPE").text = "8" # 8=Wholesale, 9=Service
        ET.SubElement(invoice, "NUMBER").text = inv_no
        ET.SubElement(invoice, "DATE").text = order['created_at'].strftime("%d.%m.%Y")
        ET.SubElement(invoice, "ARP_CODE").text = customer.get('code', '')
        ET.SubElement(invoice, "TOTAL_NET").text = str(order['total_amount'])
        
        # Transactions
        trans_node = ET.SubElement(invoice, "TRANSACTIONS")
        
        for item in items:
            product_id = item['product_id']
            # Fetch Product Code
            p_res = db_manager.execute_pg_query(f"SELECT code FROM products WHERE id = {product_id}")
            p_code = p_res[0]['code'] if p_res else "UNKNOWN"
            
            line = ET.SubElement(trans_node, "TRANSACTION")
            ET.SubElement(line, "TYPE").text = "0" # 0=Material, 4=Service (Logic needed)
            ET.SubElement(line, "MASTER_CODE").text = p_code
            ET.SubElement(line, "QUANTITY").text = str(item['quantity'])
            ET.SubElement(line, "PRICE").text = str(item['unit_price'])
            ET.SubElement(line, "TOTAL").text = str(item['total_price'])
            ET.SubElement(line, "UNIT_CODE").text = "ADET" # Default
            
        return self._prettify(root)

    async def generate_client_xml(self, customer_id: int):
        """Generates Logo XML for a Client (AR/AP)"""
        cust_res = db_manager.execute_pg_query(f"SELECT * FROM customers WHERE id = {customer_id}")
        if not cust_res: return None, "Customer not found"
        client = cust_res[0]

        root = ET.Element("AR_APS")
        clcard = ET.SubElement(root, "AR_AP")
        
        ET.SubElement(clcard, "CODE").text = client['code']
        ET.SubElement(clcard, "TITLE").text = client['name']
        ET.SubElement(clcard, "ADDRESS1").text = client.get('address', '')
        ET.SubElement(clcard, "CITY").text = client.get('city', '')
        ET.SubElement(clcard, "TAX_OFFICE").text = client.get('tax_office', '')
        ET.SubElement(clcard, "TAX_ID").text = client.get('tax_number', '')
        ET.SubElement(clcard, "CARD_TYPE").text = "3" # Buyer+Seller

        return self._prettify(root)

xml_service = XmlService()
