from loguru import logger
from ..core.database import db_manager
from ..core.config import settings
from datetime import datetime
import sys

# Try to import win32com for Logo Objects
try:
    import win32com.client
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False
    logger.warning("pywin32 not found. Logo Objects mode will be disabled.")

class LogoIntegrationService:
    def __init__(self):
        # Load Integration Mode from JSON config if available
        logo_config = next((c for c in settings.DB_CONFIGS if c.get("Name") == "LOGO_Database"), {})
        
        # Priority: JSON > Settings/Env
        self.firma_no = logo_config.get("FirmaNo", settings.LOGO_FIRMA_NO)
        self.period_no = logo_config.get("DonemNo", settings.LOGO_PERIOD_NO)
        
        self.integration_mode = logo_config.get("IntegrationMode", settings.LOGO_INTEGRATION_MODE)
        self.app_user = logo_config.get("AppUser", settings.LOGO_APP_USER)
        self.app_pass = logo_config.get("AppPass", settings.LOGO_APP_PASS)
        
        logger.info(f"LogoIntegrationService initialized in '{self.integration_mode}' mode. (Firma: {self.firma_no}, Donem: {self.period_no})")
        
        # Check COM Availability
        if self.integration_mode == "LogoObjects" and not HAS_WIN32:
            logger.error("LogoObjects mode requested but pywin32 is missing. Falling back to DirectDB.")
            self.integration_mode = "DirectDB"

    def _get_unity_app(self):
        """Helper to create and login to Unity Application"""
        if not HAS_WIN32:
            return None
            
        try:
            unity = win32com.client.Dispatch("UnityObjects.UnityApplication")
            # Login credits should be in config, fetching from settings
            # Using placeholders or environment vars if not defined
            # Login credits from JSON config (or env fallback)
            u_user = self.app_user
            u_pass = self.app_pass
            
            # DYNAMIC SQL CONNECTION (Overrides LCONFIG.EXE)
            # This allows connecting to a remote Logo Server (Ankara) from a local API (Istanbul)
            logo_config = next((c for c in settings.DB_CONFIGS if c.get("Name") == "LOGO_Database"), {})
            db_server = logo_config.get("Server")
            db_name = logo_config.get("Database")
            db_user = logo_config.get("User")
            db_pass = logo_config.get("Password")
            
            if db_server and db_name:
                logger.info(f"Unity Objects: Overriding SQL Connection -> Server: {db_server}, DB: {db_name}")
                # SQLInfo format: (ServerName, DatabaseName, SQLUser, SQLPass)
                # UnityObjects.UnityApplication.SQLInfo prop setter
                # Some versions require explicit setter method depending on wrapper, but typically property assignment works.
                try:
                    unity.SQLInfo = (db_server, db_name, db_user, db_pass)
                except Exception as e:
                     logger.warning(f"Failed to set Unity SQLInfo (Might use LCONFIG defaults): {e}")

            if unity.Login(u_user, u_pass, int(self.firma_no), int(self.period_no)):
                return unity
            else:
                err = unity.GetLastError()
                logger.error(f"Unity Login Failed: {err} - {unity.GetLastErrorString()}")
                return None
        except Exception as e:
            logger.error(f"Unity Dispatch Failed: {e}")
            return None

    def import_xml_data(self, xml_content: str):
        """
        Imports Logo XML data directly into the database using Unity Objects.
        This acts as a 'Mini LogoConnect'.
        RETURNS: (bool, string_message)
        """
        if not HAS_WIN32:
             return False, "Logo Integration is not running on Windows Server (pywin32 missing)."

        unity = self._get_unity_app()
        if not unity:
            return False, "Could not connect to Unity Objects Application."
            
        try:
            logger.info("Starting XML Import via Unity Objects DataFromXML...")
            # DataFromXML returns boolean in most wrappers, logic 1=Success usually.
            result = unity.DataFromXML(xml_content)
            
            # Check result - DataFromXML returns True if successful, False if not.
            if result:
                logger.info("XML Import Successful")
                return True, "Import Successful"
            else:
                err = unity.GetLastError()
                err_str = unity.GetLastErrorString()
                logger.error(f"XML Import Failed: {err} - {err_str}")
                return False, f"Import Error: {err} - {err_str}"
        except Exception as e:
            logger.error(f"XML Import Exception: {e}")
            return False, f"System Error: {str(e)}"

    async def get_logo_stock_status(self, item_code: str = None, firma: str = None, period: str = None):
        """Get stock levels directly from Logo MSSQL"""
        f = firma or self.firma_no
        p = period or self.period_no
        query = f"""
            SELECT CODE, NAME, ONHAND AS STOCK_QTY 
            FROM LG_{f}_ITEMS (NOLOCK) 
            JOIN LG_{f}_{p}_GNTOTST (NOLOCK) ON ITEMREF = LOGICALREF
            WHERE INVENNO = 0 -- Main Warehouse
        """
        if item_code:
            query += f" AND CODE = '{item_code}'"
            
        try:
            results = db_manager.execute_ms_query(query)
            return results
        except Exception as e:
            logger.error(f"Logo stock check failed: {e}")
            return []

    async def transfer_order_to_logo(self, order_id: str):
        """
        Generic transition for Order Transfer with Mode detection.
        """
        logger.info(f"Initiating order transfer to Logo: {order_id} using {self.integration_mode} mode")
        
        if self.integration_mode == "DirectDB":
            # Current Implementation: Direct SQL Insert (e.g., L_ORFICHE)
            return await self._transfer_via_db(order_id)
        elif self.integration_mode == "LogoObjects":
            # Future Implementation: via COM Objects
            logger.warning("LogoObjects integration mode not yet fully implemented.")
            return False
        elif self.integration_mode == "RestAPI":
            # Future Implementation: via Logo Business Gateway or Custom REST API
            logger.warning("RestAPI integration mode not yet fully implemented.")
            return False
            
        return False

    async def _transfer_via_db(self, order_id: str):
        """Internal helper for DB-direct transfer"""
        # Fetch order from Postgres
        order_query = "SELECT * FROM sales_orders WHERE id = %s"
        order = db_manager.execute_pg_query(order_query, (order_id,))
        
        if not order:
            logger.error(f"Order not found: {order_id}")
            return False
            
    async def _transfer_via_objects(self, invoice_data, items_data, invoice_type="wholesale"):
        """
        Transfer invoice using Logo Unity Objects (COM/DLL).
        Returns: (success, result_message_or_ref)
        """
        if not HAS_WIN32:
            return False, "COM libraries not available"

        unity = self._get_unity_app()
        if not unity:
            return False, "Could not login to Logo Unity Application"
            
        try:
            # Create Invoice Object (SalesInvoice)
            inv_obj = unity.NewDataObject(3) # 3 = SalesInvoice (IInvoice)
            if not inv_obj:
                return False, "Could not create Invoice Object"
            
            # Header Mapping
            tr_code_map = {"wholesale": 8, "retail": 7, "service": 9}
            inv_obj.New()
            inv_obj.DataFields.FieldByName("TYPE").Value = tr_code_map.get(invoice_type, 8)
            inv_obj.DataFields.FieldByName("NUMBER").Value = invoice_data.get('formatted_number', '~')
            inv_obj.DataFields.FieldByName("DATE").Value = invoice_data['created_at'].strftime("%d.%m.%Y")
            inv_obj.DataFields.FieldByName("ARP_CODE").Value = invoice_data.get('customer_code') # Must be code, not Ref
            # inv_obj.DataFields.FieldByName("NOTES1").Value = invoice_data.get('notes', '')
            
            # Lines
            lines = inv_obj.DataFields.FieldByName("TRANSACTIONS").Lines
            for item in items_data:
                lines.AppendLine()
                # Determine Type (Material=0, Service=4) -> This logic usually handled by master code in Objects?
                # Actually, for objects, if we set MASTER_CODE, it auto-detects? 
                # Better to be explicit: Type 0 = Material, 4 = Service
                
                # We need to know if it is service or master.
                is_service = item.get('is_service', False) # Passed from caller
                
                lines.FieldByName("TYPE").Value = 4 if is_service else 0
                lines.FieldByName("MASTER_CODE").Value = item['product_code']
                lines.FieldByName("QUANTITY").Value = float(item['quantity'])
                lines.FieldByName("PRICE").Value = float(item['unit_price'])
                # VAT included/excluded logic usually depends on settings
                
            # Post
            if inv_obj.Post() == 1:
                ref = inv_obj.DataFields.FieldByName("INTERNAL_REFERENCE").Value
                return True, ref
            else:
                err_code = inv_obj.ErrorCode
                err_desc = inv_obj.ValidateErrors(0)
                logger.error(f"Unity Post Failed: {err_desc}")
                # unity.Disconnect() -> Handled by scope?
                return False, f"Logo Error: {err_desc}"
                
        except Exception as e:
            logger.error(f"Unity Exception: {e}")
            return False, str(e)
        finally:
            # Cleanup - Important for COM
            unity = None

    async def _transfer_dispatch_via_objects(self, dispatch_data, items_data, dispatch_type="wholesale"):
        """Transfer Dispatch (İrsaliye) via Unity Objects"""
        if not HAS_WIN32: return False, "COM lib missing"
        unity = self._get_unity_app()
        if not unity: return False, "Unity Login Failed"

        try:
            # 4 = Sales Dispatch (STFICHE) - For Purchase Dispatch use 4 but different TRCODE? No, Purchase Dispatch is usually different object or TRCODE.
            # Sales Dispatch TRCODEs: 8 (Wholesale), 7 (Retail), 9 (Consignment Out)
            # Purchase Dispatch TRCODEs: 1 (Purchase), 2 (Retail Purchase - rare), 6 (Purchase Return)
            
            do = unity.NewDataObject(4) # STFICHE
            do.New()
            
            # TRCODE: 8 (Wholesale Dispatch), 7 (Retail Dispatch)
            tr_code = 8 if dispatch_type == "wholesale" else 7
            
            do.DataFields.FieldByName("TRCODE").Value = tr_code
            do.DataFields.FieldByName("FICHENO").Value = dispatch_data.get('formatted_number', '~')
            do.DataFields.FieldByName("DATE_").Value = dispatch_data['created_at'].strftime("%d.%m.%Y")
            do.DataFields.FieldByName("CLIENTREF").Value = dispatch_data.get('customer_ref') # Needs REF or use ARP_CODE can work if set? Usually ARP_CODE works.
            do.DataFields.FieldByName("ARP_CODE").Value = dispatch_data.get('customer_code')
            
            # Important: Set IOCODE for Dispatches (1=In, 3=Out, 4=Out) - Sales is Out (Gen. 3 or 4)
            # 8 (Wholesale Dispatch) -> IOCODE = 4
            # 7 (Retail Dispatch) -> IOCODE = 4
            do.DataFields.FieldByName("IOCODE").Value = 4 

            lines = do.DataFields.FieldByName("TRANSACTIONS").Lines
            for item in items_data:
                lines.AppendLine()
                lines.FieldByName("TYPE").Value = 0 # Material
                lines.FieldByName("MASTER_CODE").Value = item['product_code']
                lines.FieldByName("AMOUNT").Value = float(item['quantity'])
                lines.FieldByName("PRICE").Value = float(item['unit_price'])
                lines.FieldByName("IOCODE").Value = 4 # Out
                
            if do.Post() == 1:
                return True, do.DataFields.FieldByName("INTERNAL_REFERENCE").Value
            else:
                 # Clean err desc
                err_desc = do.ValidateErrors(0)
                return False, err_desc
        except Exception as e:
            logger.error(f"Dispatch Error: {e}")
            return False, str(e)
        finally:
            unity.Disconnect()

    async def _transfer_client_via_objects(self, client_data):
        """Transfer Client (Cari) via Unity Objects"""
        if not HAS_WIN32: return False, "COM lib missing"
        unity = self._get_unity_app()
        if not unity: return False, "Unity Login Failed"

        try:
            # 1 = AR/AP (CLCARD)
            do = unity.NewDataObject(1) 
            do.New()
            
            do.DataFields.FieldByName("CODE").Value = client_data['code']
            do.DataFields.FieldByName("TITLE").Value = client_data['name']
            do.DataFields.FieldByName("ADDRESS1").Value = client_data.get('address', '')
            do.DataFields.FieldByName("CITY").Value = client_data.get('city', '')
            do.DataFields.FieldByName("TAX_OFFICE").Value = client_data.get('tax_office', '')
            do.DataFields.FieldByName("TAX_ID").Value = client_data.get('tax_number', '')
            do.DataFields.FieldByName("CARD_TYPE").Value = 3 # 3=Alıcı+Satıcı (Buyer+Seller)
            
            if do.Post() == 1:
                return True, do.DataFields.FieldByName("INTERNAL_REFERENCE").Value
            else:
                return False, do.ValidateErrors(0)
        except Exception as e:
            return False, str(e)
        finally:
            unity.Disconnect()

    async def _transfer_item_via_objects(self, item_data):
        """Transfer Item (Malzeme) via Unity Objects"""
        if not HAS_WIN32: return False, "COM lib missing"
        unity = self._get_unity_app()
        if not unity: return False, "Unity Login Failed"

        try:
            # 0 = Item (ITEMS)
            do = unity.NewDataObject(0)
            do.New()
            
            do.DataFields.FieldByName("CODE").Value = item_data['code']
            do.DataFields.FieldByName("NAME").Value = item_data['name']
            do.DataFields.FieldByName("CARD_TYPE").Value = 1 # 1=TM (Comm. Good)
            do.DataFields.FieldByName("UNITSET_CODE").Value = item_data.get('unit_set', '05') # '05' is usually ADET set code in demo data, but should be param.
            
            if do.Post() == 1:
                return True, do.DataFields.FieldByName("INTERNAL_REFERENCE").Value
            else:
                return False, do.ValidateErrors(0)
        except Exception as e:
            return False, str(e)
        finally:
            unity.Disconnect()

    async def _transfer_collection_via_objects(self, collection_data):
        """Transfer Cash Collection via Unity Objects"""
        if not HAS_WIN32: return False, "COM lib missing"
        unity = self._get_unity_app()
        if not unity: return False, "Unity Login Failed"

        try:
            # 10 = Safe Def (KSCARD)
            # For Transactions: 'Kasa Islemleri' -> Data Object 11 (KSLINES within KSCARD?) No.
            # Usually Kasa Islemleri is Data Object 19 on newer versions (7+), or via SD_TRANSACTIONS.
            # Let's try 19 (Safe Deposit Transaction) which is most common for cash collection.
            
            do = unity.NewDataObject(19) 
            do.New()
            
            # TRCODE: 11 (Tahsilat/Collection), 12 (Odeme/Payment)
            do.DataFields.FieldByName("TRCODE").Value = 11 
            do.DataFields.FieldByName("DATE_").Value = datetime.now().strftime("%d.%m.%Y")
            do.DataFields.FieldByName("CUST_TITLE").Value = collection_data.get('customer_name', '')
            do.DataFields.FieldByName("AMOUNT").Value = float(collection_data['amount'])
            do.DataFields.FieldByName("DESCRIPTION").Value = collection_data.get('description', 'API Collection')
            
            # Link to Customer (Compulsory for Collection)
            do.DataFields.FieldByName("ARP_CODE").Value = collection_data.get('customer_code')
            
            # Link to Safe (Kasa Kodu) - Required
            do.DataFields.FieldByName("CODE").Value = collection_data.get('safe_code', '01') # Default safe
            
            if do.Post() == 1:
                return True, do.DataFields.FieldByName("INTERNAL_REFERENCE").Value
            else:
                return False, do.ValidateErrors(0)
        except Exception as e:
            return False, str(e)
        finally:
            unity.Disconnect()

            
        # 1. Insert Header (ORFICHE)
        f = self.firma_no
        p = self.period_no
        client_code = db_manager.execute_pg_query(f"SELECT code FROM customers WHERE id = {order[0]['customer_id']}")[0]['code']
        
        fiche_no = order[0]['order_number']
        header_query = f"""
            INSERT INTO LG_{f}_{p}_ORFICHE (FICHENO, DATE_, TRCODE, CLIENTREF, SOURCEINDEX, BILLED)
            VALUES (%s, %s, 1, (SELECT LOGICALREF FROM LG_{f}_CLCARD WHERE CODE = %s), 0, 0)
        """
        db_manager.execute_ms_query(header_query, (fiche_no, order[0]['created_at'], client_code), fetch=False)
        
        # 2. Insert Lines (ORFLINE)
        items_query = "SELECT * FROM sales_order_items WHERE order_id = %s"
        items = db_manager.execute_pg_query(items_query, (order_id,))
        
        for item in items:
            product_code = db_manager.execute_pg_query(f"SELECT code FROM products WHERE id = {item['product_id']}")[0]['code']
            
            # Check if Item or Service
            # We need a way to know if it is a service. 
            # Assuming 'is_service' column in 'products' or 'sales_order_items' or via prefix check.
            # For now, let's query both ITEMS and SRVCARD to find the reference.
            
            is_service = False
            item_ref = db_manager.execute_ms_query(f"SELECT LOGICALREF FROM LG_{f}_ITEMS WHERE CODE = '{product_code}'")
            line_type = 0 # Material
            
            if not item_ref:
                # Check Service
                item_ref = db_manager.execute_ms_query(f"SELECT LOGICALREF FROM LG_{f}_SRVCARD WHERE CODE = '{product_code}'")
                if item_ref:
                    is_service = True
                    line_type = 4 # Service
            
            if item_ref:
                ref = item_ref[0]['LOGICALREF']
                table = "LG_{}_{}_ORFLINE".format(f, p)
                
                line_query = f"""
                    INSERT INTO {table} (STOCKREF, AMOUNT, PRICE, TOTAL, DATE_, TRCODE, ORFICHEREF, LINETYPE)
                    VALUES (%s, %s, %s, %s, %s, 1, 
                           (SELECT LOGICALREF FROM LG_{f}_{p}_ORFICHE WHERE FICHENO = %s),
                           %s)
                """
                db_manager.execute_ms_query(line_query, (
                    ref, item['quantity'], item['unit_price'], item['total_price'], 
                    order[0]['created_at'], fiche_no, line_type
                ), fetch=False)
        
        return True

    async def transfer_invoice_to_logo(self, local_invoice_id: str, invoice_type: str = "wholesale"):
        """
        Transfers a local invoice to Logo ERP as a Sales Invoice.
        
        Args:
            local_invoice_id: ID of the invoice in local DB (sales_invoices table)
            invoice_type: 'wholesale', 'retail', or 'service'
            
        TRCODE Mapping:
            - wholesale (Toptan Satış): 8
            - retail (Perakende Satış): 7
            - service (Verilen Hizmet): 9
        """
        logger.info(f"Initiating invoice transfer to Logo: {local_invoice_id} ({invoice_type})")
        
        # 0. Setup & Validation
        f = self.firma_no
        p = self.period_no
        
        tr_code_map = {
            "wholesale": 8,
            "retail": 7,
            "service": 9
        }
        tr_code = tr_code_map.get(invoice_type.lower(), 8)
        
        # 1. Fetch Invoice Header
        inv_query = "SELECT * FROM sales_invoices WHERE id = %s"
        # Assuming table sales_invoices exists, if not using sales_orders. 
        # Adapting to use sales_orders if sales_invoices not present, but based on request, we likely use orders structure or a new invoices table.
        # For now, let's assume we are transferring an ORDER *AS* an INVOICE or using a specific invoices table.
        # IF database table 'sales_invoices' does not exist in schema, we'd fallback to 'sales_orders'.
        # Let's check schema first? No, let's proceed with generic SQL that works if table exists. 
        # Actually, let's allow transferring an ORDER directly as an INVOICE.
        
        # OPTION A: Transfer from sales_orders
        inv_data = db_manager.execute_pg_query("SELECT * FROM sales_orders WHERE id = %s", (local_invoice_id,))
        tr_code = tr_code_map.get(invoice_type.lower(), 8)
        
        # --- STRATEGY: 1. Objects -> 2. REST -> 3. DB ---
        
        # Get Invoice Data First
        inv_data_sql = db_manager.execute_pg_query("SELECT * FROM sales_orders WHERE id = %s", (local_invoice_id,))
        if not inv_data_sql:
            logger.error(f"Invoice source not found: {local_invoice_id}")
            return False
        invoice = inv_data_sql[0]
        
        # Get Items
        items_sql = db_manager.execute_pg_query("SELECT * FROM sales_order_items WHERE order_id = %s", (local_invoice_id,))
        items_prepared = []

        # Pre-process items for finding codes and types (Common for all methods)
        for item in items_sql:
            p_code = db_manager.execute_pg_query(f"SELECT code FROM products WHERE id = {item['product_id']}")[0]['code']
             # Check Type (Material vs Service)
            is_srv = False
            # Check SRVCARD 
            if db_manager.execute_ms_query(f"SELECT LOGICALREF FROM LG_{f}_SRVCARD WHERE CODE = '{p_code}'"):
                is_srv = True
            
            items_prepared.append({
                "product_code": p_code,
                "quantity": item['quantity'],
                "unit_price": item['unit_price'],
                "total_price": item['total_price'],
                "is_service": is_srv
            })
            
        customer_code_res = db_manager.execute_pg_query(f"SELECT code FROM customers WHERE id = {invoice['customer_id']}")
        if not customer_code_res: return False
        
        invoice_prepared = {
            "created_at": invoice['created_at'],
            "formatted_number": invoice.get('order_number'),
            "customer_code": customer_code_res[0]['code'],
            "notes": invoice.get('notes')
        }

        # 1. Try Objects
        if HAS_WIN32 and self.integration_mode != "DirectDB": # Unless forced to DB
            logger.info("Attempting Transfer via Unity Objects...")
            success, msg = await self._transfer_via_objects(invoice_prepared, items_prepared, invoice_type)
            if success:
                logger.info(f"Unity Transfer Success. Ref: {msg}")
                return True
            else:
                logger.warning(f"Unity Transfer Failed ({msg}). Falling back...")

        # 2. Try REST (Placeholder)
        # if self.integration_mode == "RestAPI": ...

        # 3. Fallback to Direct DB
        logger.info("Fallback: Transferring via Direct SQL Insert...")
        
        # 1. Fetch Invoice Header (Already fetched above)
        # Re-using logic but mapped to prepared data
        
        # 2. Get Client Ref
        client_code = invoice_prepared['customer_code']
        client_ref_res = db_manager.execute_ms_query(f"SELECT LOGICALREF FROM LG_{f}_CLCARD WHERE CODE = '{client_code}'")
        if not client_ref_res:
             logger.error(f"Client not found in Logo: {client_code}")
             return False
        client_ref = client_ref_res[0]['LOGICALREF']
        
        # 3. Insert Invoice Header (INVOICE)
        fiche_no = invoice_prepared['formatted_number'] or f"INV{datetime.now().strftime('%Y%m%d%H%M')}"
        
        exists = db_manager.execute_ms_query(f"SELECT LOGICALREF FROM LG_{f}_{p}_INVOICE WHERE FICHENO = '{fiche_no}' AND TRCODE = {tr_code}")
        if exists: return True

        try:
             db_manager.execute_ms_query(f"""
                INSERT INTO LG_{f}_{p}_INVOICE (FICHENO, DATE_, TRCODE, CLIENTREF, GRPCODE, SOURCEINDEX, INVOICENO, DOCODE)
                VALUES (%s, %s, %s, %s, 2, 0, %s, %s)
            """, (fiche_no, invoice_prepared['created_at'], tr_code, client_ref, fiche_no, fiche_no), fetch=False)
            
             inv_ref_res = db_manager.execute_ms_query(f"SELECT LOGICALREF FROM LG_{f}_{p}_INVOICE WHERE FICHENO = '{fiche_no}' AND TRCODE = {tr_code}")
             invoice_ref = inv_ref_res[0]['LOGICALREF']
        except Exception as e:
            logger.error(f"Failed to insert invoice header: {e}")
            return False

        # 4. Insert Invoice Lines
        for item in items_prepared:
            stock_ref = 0
            line_type = 4 if item['is_service'] else 0
            
            table_source = "SRVCARD" if item['is_service'] else "ITEMS"
            ref_res = db_manager.execute_ms_query(f"SELECT LOGICALREF FROM LG_{f}_{table_source} WHERE CODE = '{item['product_code']}'")
            if ref_res:
                stock_ref = ref_res[0]['LOGICALREF']
            
            if stock_ref == 0: continue
                
            line_query = f"""
                INSERT INTO LG_{f}_{p}_STLINE (STOCKREF, AMOUNT, PRICE, TOTAL, DATE_, TRCODE, INVOICEREF, LINETYPE, CLIENTREF, SOURCEINDEX)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 0)
            """
            db_manager.execute_ms_query(line_query, (
                stock_ref, item['quantity'], item['unit_price'], item['total_price'],
                invoice_prepared['created_at'], tr_code, invoice_ref, line_type, client_ref
            ), fetch=False)
            
        logger.info(f"Direct SQL Transfer Success: {fiche_no}")
        return True
            
    # --- CUSTOMER (CLCARD) CRUD ---
    async def get_customers(self, search: str = None, firma: str = None):
        """Read customers from Logo"""
        f = firma or self.firma_no
        query = f"SELECT LOGICALREF, CODE, DEFINITION_ AS NAME, ADDR1 AS ADDRESS, CITY FROM LG_{f}_CLCARD (NOLOCK) WHERE CARDTYPE <> 22"
        if search:
            query += f" AND (CODE LIKE '%{search}%' OR DEFINITION_ LIKE '%{search}%')"
        return db_manager.execute_ms_query(query)

    async def create_customer(self, data: dict):
        """Insert a 'Draft' customer into Logo (Intermediary or direct table)"""
        # Note: Direct insert to CLCARD requires LOGICALREF management. 
        # Usually handled via Unity Objects, but here we provide a SQL structure.
        logger.info(f"Creating Logo customer: {data.get('code')}")
        query = f"""
            INSERT INTO LG_{self.firma_no}_CLCARD (CODE, DEFINITION_, ADDR1, CITY, TAXOFFICE, TAXNR, CARDTYPE)
            VALUES (%s, %s, %s, %s, %s, %s, 1)
        """
        params = (data['code'], data['name'], data.get('address', ''), data.get('city', ''), data.get('tax_office', ''), data.get('tax_number', ''))
        return db_manager.execute_ms_query(query, params, fetch=False)

    async def update_customer(self, erp_code: str, data: dict):
        """Update existing customer in Logo"""
        logger.info(f"Updating Logo customer: {erp_code}")
        query = f"UPDATE LG_{self.firma_no}_CLCARD SET DEFINITION_ = %s, ADDR1 = %s, CITY = %s WHERE CODE = %s"
        params = (data['name'], data.get('address', ''), data.get('city', ''), erp_code)
        return db_manager.execute_ms_query(query, params, fetch=False)

    # --- ITEM (ITEMS) CRUD ---
    async def get_items(self, search: str = None):
        """Read items from Logo"""
        query = f"SELECT LOGICALREF, CODE, NAME, STGRPCODE AS CATEGORY FROM LG_{self.firma_no}_ITEMS (NOLOCK) WHERE CARDTYPE = 1"
        if search:
            query += f" AND (CODE LIKE '%{search}%' OR NAME LIKE '%{search}%')"
        return db_manager.execute_ms_query(query)

    # --- SERVICE (SRVCARD) CRUD ---
    async def get_services(self, search: str = None):
        """Read services from Logo"""
        query = f"SELECT LOGICALREF, CODE, DEFINITION_ AS NAME, CARDTYPE FROM LG_{self.firma_no}_SRVCARD (NOLOCK) WHERE CARDTYPE IN (1, 2)"
        if search:
            query += f" AND (CODE LIKE '%{search}%' OR DEFINITION_ LIKE '%{search}%')"
        return db_manager.execute_ms_query(query)

    # --- ORDER (ORFICHE) CRUD ---
    async def get_orders(self, customer_code: str = None, firma: str = None, period: str = None):
        """Read orders from Logo"""
        f = firma or self.firma_no
        p = period or self.period_no
        query = f"SELECT LOGICALREF, FICHENO, DATE_, SOURCEINDEX, NETTOTAL FROM LG_{f}_{p}_ORFICHE (NOLOCK)"
        if customer_code:
            query += f" WHERE CLIENTREF = (SELECT LOGICALREF FROM LG_{f}_CLCARD WHERE CODE = '{customer_code}')"
        return db_manager.execute_ms_query(query)

    # --- STOCK (STFICHE) CRUD ---
    async def create_stock_count(self, items: list):
        """
        Create a Stock Count (Sayım Fişi - TRCODE 6) in Logo ERP.
        In real apps, Unity/Objects is preferred, but here we provide a DirectSQL blueprint.
        """
        logger.info(f"Creating Logo stock count with {len(items)} items")
        f = self.firma_no
        p = self.period_no
        
        # 1. Insert Header (STFICHE)
        # Using placeholder logic for LOGICALREF as it's usually auto-inc or handled by Unity.
        fiche_no = f"SYM{datetime.now().strftime('%m%d%H%M')}"
        header_query = f"""
            INSERT INTO LG_{f}_{p}_STFICHE (FICHENO, DATE_, TRCODE, SOURCEINDEX, BILLED)
            VALUES (%s, GETDATE(), 6, 0, 0)
        """
        db_manager.execute_ms_query(header_query, (fiche_no,), fetch=False)
        
        # 2. Insert Lines (STLINE)
        # In a production environment, we'd need the LOGICALREF from STFICHE.
        for item in items:
            line_query = f"""
                INSERT INTO LG_{f}_{p}_STLINE (STOCKREF, AMOUNT, DATE_, TRCODE, STFICHEREF, LINETYPE)
                VALUES ((SELECT LOGICALREF FROM LG_{f}_ITEMS WHERE CODE = %s), %s, GETDATE(), 6, 0, 0)
            """
            db_manager.execute_ms_query(line_query, (item['barcode'], item['qty']), fetch=False)
            
        return True

    # --- COLLECTION / PAYMENT (KSLINES) CRUD ---
    async def create_payment(self, data: dict):
        """Record a payment into Logo Safe Deposit (KSLINES)"""
        logger.info(f"Recording Logo payment for customer: {data.get('customer_code')}")
        # Simplistic SQL insert for draft payment. 
        # Real-world apps use Unity Objects for automatic account balancing.
        query = f"""
            INSERT INTO LG_{self.firma_no}_KSLINES (DATE_, AMOUNT, CLIENTREF, SOURCEINDEX, TRCODE)
            VALUES (%s, %s, (SELECT LOGICALREF FROM LG_{self.firma_no}_CLCARD WHERE CODE = %s), 0, 1)
        """
        params = (datetime.now(), data['amount'], data['customer_code'])
        return db_manager.execute_ms_query(query, params, fetch=False)

    async def get_yoy_comparison(self, period_type: str = "daily"):
        """
        Get Year-over-Year comparison data.
        period_type: 'daily', 'weekly', or 'monthly'
        """
        logger.info(f"Fetching YoY comparison for period: {period_type}")
        
        view_map = {
            "daily": "V_YOY_DAILY_COMPARISON",
            "weekly": "V_YOY_WEEKLY_COMPARISON",
            "monthly": "V_YOY_MONTHLY_COMPARISON"
        }
        
        view_name = view_map.get(period_type.lower(), "V_YOY_DAILY_COMPARISON")
        query = f"SELECT * FROM {view_name} (NOLOCK)"
        
        result = db_manager.execute_ms_query(query)
        if result and len(result) > 0:
            return result[0]  # Return first row as dict
        return {}

    # --- REPORTS & ANALYTICS ---
    async def get_sales_report(self, start_date: str, end_date: str, firma: str = None, period: str = None):
        """Detailed Sales Report from Logo INVOICE & STLINE"""
        f = firma or self.firma_no
        p = period or self.period_no
        query = f"""
            SELECT 
                INV.FICHENO, 
                INV.DATE_, 
                CLC.DEFINITION_ AS CUSTOMER_NAME,
                INV.NETTOTAL,
                (SELECT SUM(AMOUNT) FROM LG_{f}_{p}_STLINE WHERE INVOICEREF = INV.LOGICALREF) AS TOTAL_QUANTITY
            FROM LG_{f}_{p}_INVOICE INV (NOLOCK)
            JOIN LG_{f}_CLCARD CLC (NOLOCK) ON INV.CLIENTREF = CLC.LOGICALREF
            WHERE INV.DATE_ BETWEEN %s AND %s
            ORDER BY INV.DATE_ DESC
        """
        return db_manager.execute_ms_query(query, (start_date, end_date))

    async def get_collection_report(self, start_date: str, end_date: str):
        """Collection Report from Logo KSLINES"""
        query = f"""
            SELECT 
                KS.DATE_, 
                KS.AMOUNT, 
                CLC.DEFINITION_ AS CUSTOMER_NAME,
                KS.TRCODE
            FROM LG_{self.firma_no}_KSLINES KS (NOLOCK)
            LEFT JOIN LG_{self.firma_no}_CLCARD CLC (NOLOCK) ON KS.CLIENTREF = CLC.LOGICALREF
            WHERE KS.DATE_ BETWEEN %s AND %s
            ORDER BY KS.DATE_ DESC
        """
        return db_manager.execute_ms_query(query, (start_date, end_date))

    async def get_customer_balances(self, firma: str = None, period: str = None):
        """Current Debt/Credit Status for all customers"""
        f = firma or self.firma_no
        p = period or self.period_no
        query = f"""
            SELECT 
                CODE, 
                DEFINITION_ AS NAME, 
                (SELECT SUM(DEBIT - CREDIT) FROM LG_{f}_{p}_GNTOTCL WHERE CLIENTREF = LOGICALREF) AS BALANCE
            FROM LG_{f}_CLCARD (NOLOCK)
            WHERE CARDTYPE <> 22
            ORDER BY BALANCE DESC
        """
        return db_manager.execute_ms_query(query)

    async def get_visit_performance_report(self, start_date: str, end_date: str):
        """Field Visit Success Report"""
        # Note: Using the field_visits table from our new schema
        query = f"""
            SELECT 
                U.FULL_NAME AS SALESMAN,
                COUNT(V.ID) AS TOTAL_VISITS,
                COUNT(CASE WHEN V.CHECK_OUT_TIME IS NOT NULL THEN 1 END) AS COMPLETED_VISITS,
                COUNT(CASE WHEN V.STATUS = 'ordered' THEN 1 END) AS CONVERTED_VISITS
            FROM USERS U
            LEFT JOIN FIELD_VISITS V ON U.ID = V.SALESMAN_ID
            WHERE V.VISIT_DATE BETWEEN %s AND %s
            GROUP BY U.FULL_NAME
        """
        # This targets the main app DB (Postgres)
        return db_manager.execute_pg_query(query, (start_date, end_date))

    async def get_order_tracking_report(self, start_date: str, end_date: str):
        """Order Sync & Status Report from Logo & Local DB"""
        query = f"""
            SELECT 
                ORD.ORDER_NUMBER, 
                ORD.CREATED_AT, 
                CLC.NAME AS CUSTOMER_NAME,
                ORD.TOTAL_AMOUNT,
                ORD.SYNC_STATUS
            FROM SALES_ORDERS ORD
            JOIN CUSTOMERS CLC ON ORD.CUSTOMER_ID = CLC.ID
            WHERE ORD.CREATED_AT BETWEEN %s AND %s
            ORDER BY ORD.CREATED_AT DESC
        """
        return db_manager.execute_pg_query(query, (start_date, end_date))

    async def get_inventory_status(self, firma: str = None, period: str = None):
        """Full inventory status with values"""
        f = firma or self.firma_no
        p = period or self.period_no
        query = f"""
            SELECT 
                ITEM.CODE, 
                ITEM.NAME, 
                TOT.ONHAND AS QUANTITY,
                ITEM.STGRPCODE AS CATEGORY
            FROM LG_{f}_ITEMS ITEM (NOLOCK)
            JOIN LG_{f}_{p}_GNTOTST TOT (NOLOCK) ON ITEM.LOGICALREF = TOT.ITEMREF
            WHERE TOT.INVENNO = -1 -- All Warehouses sum
            ORDER BY QUANTITY DESC
        """
        return db_manager.execute_ms_query(query)

    async def get_top_selling_products(self, limit: int = 10, firma: str = None, period: str = None):
        """Top selling products by quantity"""
        f = firma or self.firma_no
        p = period or self.period_no
        query = f"""
            SELECT TOP {limit}
                ITEM.CODE, 
                ITEM.NAME, 
                SUM(STL.AMOUNT) AS TOTAL_QUANTITY
            FROM LG_{f}_{p}_STLINE STL (NOLOCK)
            JOIN LG_{f}_ITEMS ITEM (NOLOCK) ON STL.STOCKREF = ITEM.LOGICALREF
            WHERE STL.LINETYPE = 0 -- Material
            GROUP BY ITEM.CODE, ITEM.NAME
            ORDER BY TOTAL_QUANTITY DESC
        """
        return db_manager.execute_ms_query(query)

    async def get_salesman_leaderboard(self, start_date: str, end_date: str, firma: str = None, period: str = None):
        """Total Sales (TL) ranking for salesmen (from Logo SLSMAN)"""
        f = firma or self.firma_no
        p = period or self.period_no
        query = f"""
            SELECT 
                SLS.DEFINITION_ AS NAME,
                SUM(INV.NETTOTAL) AS TOTAL_SALES_TL,
                COUNT(INV.LOGICALREF) AS INVOICE_COUNT
            FROM LG_{f}_{p}_INVOICE INV (NOLOCK)
            JOIN LG_SLSMAN SLS (NOLOCK) ON INV.SALESMANREF = SLS.LOGICALREF
            WHERE INV.DATE_ BETWEEN %s AND %s
            GROUP BY SLS.DEFINITION_
            ORDER BY TOTAL_SALES_TL DESC
        """
        return db_manager.execute_ms_query(query, (start_date, end_date))

    async def get_debt_aging_report(self, firma: str = None, period: str = None):
        """Borç Yaşlandırma (Debt Aging) - 0-30, 31-60, 61-90, 90+ days"""
        # Note: This is a complex query simplified for generic ERP use cases.
        # Professional Logo implementations usually query PAYTRANS table.
        f = firma or self.firma_no
        p = period or self.period_no
        query = f"""
            SELECT 
                CLC.CODE, CLC.DEFINITION_ AS NAME,
                SUM(CASE WHEN DATEDIFF(DAY, DATE_, GETDATE()) <= 30 THEN BALANCE ELSE 0 END) AS AGE_30,
                SUM(CASE WHEN DATEDIFF(DAY, DATE_, GETDATE()) BETWEEN 31 AND 60 THEN BALANCE ELSE 0 END) AS AGE_60,
                SUM(CASE WHEN DATEDIFF(DAY, DATE_, GETDATE()) BETWEEN 61 AND 90 THEN BALANCE ELSE 0 END) AS AGE_90,
                SUM(CASE WHEN DATEDIFF(DAY, DATE_, GETDATE()) > 90 THEN BALANCE ELSE 0 END) AS AGE_PLUS
            FROM (
                SELECT CLIENTREF, DATE_, (DEBIT - CREDIT) AS BALANCE 
                FROM LG_{f}_{p}_CLFLINE (NOLOCK)
            ) AS FLOW
            JOIN LG_{f}_CLCARD CLC (NOLOCK) ON FLOW.CLIENTREF = CLC.LOGICALREF
            GROUP BY CLC.CODE, CLC.DEFINITION_
            HAVING SUM(BALANCE) > 0
        """
        return db_manager.execute_ms_query(query)

    async def get_category_sales_analysis(self, start_date: str, end_date: str, firma: str = None, period: str = None):
        """Sales distribution by product category (Stok Grup Kodu)"""
        f = firma or self.firma_no
        p = period or self.period_no
        query = f"""
            SELECT 
                ITEM.STGRPCODE AS CATEGORY,
                SUM(STL.LINENET) AS TOTAL_TL
            FROM LG_{f}_{p}_STLINE STL (NOLOCK)
            JOIN LG_{f}_ITEMS ITEM (NOLOCK) ON STL.STOCKREF = ITEM.LOGICALREF
            WHERE STL.DATE_ BETWEEN %s AND %s
            GROUP BY ITEM.STGRPCODE
            ORDER BY TOTAL_TL DESC
        """
        return db_manager.execute_ms_query(query, (start_date, end_date))

    async def get_churn_risk_report(self, firma: str = None, period: str = None):
        """Müşteri Kaybetme Riski - 30+ gündür sipariş vermeyenler"""
        f = firma or self.firma_no
        p = period or self.period_no
        query = f"""
            SELECT 
                CLC.CODE, 
                CLC.DEFINITION_ AS NAME,
                MAX(INV.DATE_) AS LAST_ORDER_DATE,
                DATEDIFF(DAY, MAX(INV.DATE_), GETDATE()) AS DAYS_SILENT,
                SUM(INV.NETTOTAL) AS LAST_YEAR_TOTAL
            FROM LG_{f}_CLCARD CLC (NOLOCK)
            LEFT JOIN LG_{f}_{p}_INVOICE INV (NOLOCK) ON CLC.LOGICALREF = INV.CLIENTREF
            WHERE CLC.CARDTYPE <> 22
            GROUP BY CLC.CODE, CLC.DEFINITION_
            HAVING DATEDIFF(DAY, MAX(INV.DATE_), GETDATE()) > 30 OR MAX(INV.DATE_) IS NULL
            ORDER BY DAYS_SILENT DESC
        """
        return db_manager.execute_ms_query(query)

    async def get_profitability_analysis(self, start_date: str, end_date: str, firma: str = None, period: str = None):
        """Brüt Karlılık Analizi - Satış vs Son Alış Maliyeti"""
        f = firma or self.firma_no
        p = period or self.period_no
        query = f"""
            SELECT 
                ITEM.CODE, 
                ITEM.NAME,
                SUM(STL.AMOUNT) AS QUANTITY,
                SUM(STL.LINENET) AS SALES_TOTAL,
                SUM(STL.AMOUNT * (
                    SELECT TOP 1 (VATMATRAH / NULLIF(AMOUNT, 0)) 
                    FROM LG_{f}_{p}_STLINE (NOLOCK) 
                    WHERE STOCKREF = ITEM.LOGICALREF AND TRCODE = 1 -- Purchase
                    ORDER BY DATE_ DESC
                )) AS COST_TOTAL
            FROM LG_{f}_{p}_STLINE STL (NOLOCK)
            JOIN LG_{f}_ITEMS ITEM (NOLOCK) ON STL.STOCKREF = ITEM.LOGICALREF
            WHERE STL.TRCODE IN (7, 8) -- Wholesale/Retail Sales
            AND STL.DATE_ BETWEEN %s AND %s
            GROUP BY ITEM.CODE, ITEM.NAME
            HAVING SUM(STL.LINENET) > 0
        """
        return db_manager.execute_ms_query(query, (start_date, end_date))

    async def get_target_achievement_report(self, firma: str = None, period: str = None):
        """Hedef Gerçekleşme - Cari Ay vs Geçen Yıl Aynı Ay + %10 Hedef"""
        f = firma or self.firma_no
        p = period or self.period_no
        query = f"""
            SELECT 
                SLS.DEFINITION_ AS NAME,
                SUM(CASE WHEN MONTH(INV.DATE_) = MONTH(GETDATE()) AND YEAR(INV.DATE_) = YEAR(GETDATE()) THEN INV.NETTOTAL ELSE 0 END) AS ACTUAL,
                SUM(CASE WHEN MONTH(INV.DATE_) = MONTH(GETDATE()) AND YEAR(INV.DATE_) = YEAR(GETDATE()) - 1 THEN INV.NETTOTAL ELSE 0 END) * 1.10 AS TARGET
            FROM LG_{f}_{p}_INVOICE INV (NOLOCK)
            JOIN LG_SLSMAN SLS (NOLOCK) ON INV.SALESMANREF = SLS.LOGICALREF
            GROUP BY SLS.DEFINITION_
        """
        return db_manager.execute_ms_query(query)

    async def get_customer_product_history(self, customer_code: str, item_code: str, firma: str = None, period: str = None):
        """Cari-Ürün Çapraz Hareket - Bu müşteri bu ürünü kaça almıştı?"""
        f = firma or self.firma_no
        p = period or self.period_no
        query = f"""
            SELECT TOP 20
                INV.FICHENO AS INVOICE_NO,
                INV.DATE_ AS DATE_,
                STL.AMOUNT AS QUANTITY,
                STL.PRICE AS UNIT_PRICE,
                STL.LINENET AS LINE_TOTAL,
                INV.NETTOTAL AS INV_TOTAL
            FROM LG_{f}_{p}_STLINE STL (NOLOCK)
            JOIN LG_{f}_{p}_INVOICE INV (NOLOCK) ON STL.INVOICEREF = INV.LOGICALREF
            JOIN LG_{f}_CLCARD CLC (NOLOCK) ON INV.CLIENTREF = CLC.LOGICALREF
            JOIN LG_{f}_ITEMS ITEM (NOLOCK) ON STL.STOCKREF = ITEM.LOGICALREF
            WHERE CLC.CODE = %s AND ITEM.CODE = %s
            ORDER BY INV.DATE_ DESC
        """
        return db_manager.execute_ms_query(query, (customer_code, item_code))

    async def get_document_chain_report(self, start_date: str, end_date: str, firma: str = None, period: str = None):
        """Belge Zinciri - Sipariş -> İrsaliye -> Fatura Takibi"""
        f = firma or self.firma_no
        p = period or self.period_no
        query = f"""
            SELECT 
                ORD.FICHENO AS ORDER_NO,
                ORD.DATE_ AS ORDER_DATE,
                STF.FICHENO AS SHIP_NO,
                STF.DATE_ AS SHIP_DATE,
                INV.FICHENO AS INV_NO,
                INV.DATE_ AS INV_DATE,
                CLC.DEFINITION_ AS CUSTOMER,
                ORD.NETTOTAL AS ORDER_TOTAL
            FROM LG_{f}_{p}_ORFICHE ORD (NOLOCK)
            LEFT JOIN LG_{f}_{p}_STFICHE STF (NOLOCK) ON ORD.LOGICALREF = STF.ORDERREF
            LEFT JOIN LG_{f}_{p}_INVOICE INV (NOLOCK) ON STF.INVOICEREF = INV.LOGICALREF
            JOIN LG_{f}_CLCARD CLC (NOLOCK) ON ORD.CLIENTREF = CLC.LOGICALREF
            WHERE ORD.DATE_ BETWEEN %s AND %s
            ORDER BY ORD.DATE_ DESC
        """
        return db_manager.execute_ms_query(query, (start_date, end_date))

    async def get_detailed_line_report(self, type: str, fiche_no: str, firma: str = None, period: str = None):
        """Fatura/İrsaliye Satır Dökümü"""
        f = firma or self.firma_no
        p = period or self.period_no
        # Determine table based on type
        table = f"LG_{f}_{p}_INVOICE" if type == 'invoice' else f"LG_{f}_{p}_STFICHE"
        query = f"""
            SELECT 
                ITEM.CODE, 
                ITEM.NAME, 
                STL.AMOUNT, 
                STL.PRICE, 
                STL.LINENET
            FROM LG_{f}_{p}_STLINE STL (NOLOCK)
            JOIN {table} FICH (NOLOCK) ON STL.INVOICEREF = FICH.LOGICALREF
            JOIN LG_{f}_ITEMS ITEM (NOLOCK) ON STL.STOCKREF = ITEM.LOGICALREF
            WHERE FICH.FICHENO = %s
        """
        return db_manager.execute_ms_query(query, (fiche_no,))

    async def get_pos_daily_report(self, date: str, firma: str = None, period: str = None):
        """POS Gün Sonu - Perakende Satışlar"""
        f = firma or self.firma_no
        p = period or self.period_no
        query = f"""
            SELECT 
                INV.FICHENO, 
                INV.DATE_, 
                CLC.DEFINITION_ AS CUSTOMER,
                INV.NETTOTAL
            FROM LG_{f}_{p}_INVOICE INV (NOLOCK)
            JOIN LG_{f}_CLCARD CLC (NOLOCK) ON INV.CLIENTREF = CLC.LOGICALREF
            WHERE INV.TRCODE = 7 -- Retail Invoice
            AND INV.DATE_ = %s
        """
        return db_manager.execute_ms_query(query, (date,))

    async def get_lot_expiry_report(self, days: int = 30, firma: str = None, period: str = None):
        """Lot/Seri SKT Takibi - Expiry Warning"""
        f = firma or self.firma_no
        p = period or self.period_no
        query = f"""
            SELECT 
                ITEM.CODE, 
                ITEM.NAME, 
                LT.LOTNO, 
                LT.EXPDATE, 
                DATEDIFF(DAY, GETDATE(), LT.EXPDATE) AS DAYS_LEFT
            FROM LG_{f}_{p}_LOTREC LT (NOLOCK)
            JOIN LG_{f}_ITEMS ITEM (NOLOCK) ON LT.ITEMREF = ITEM.LOGICALREF
            WHERE LT.EXPDATE IS NOT NULL
            AND LT.EXPDATE <= DATEADD(DAY, %s, GETDATE())
            ORDER BY LT.EXPDATE ASC
        """
        return db_manager.execute_ms_query(query, (days,))

    async def get_stock_transfer_report(self, start_date: str, end_date: str, firma: str = None, period: str = None):
        """Ambar Transferleri"""
        f = firma or self.firma_no
        p = period or self.period_no
        query = f"""
            SELECT 
                STF.FICHENO, 
                STF.DATE_, 
                W1.NAME AS FROM_WH, 
                W2.NAME AS TO_WH, 
                ITEM.NAME AS ITEM_NAME, 
                STL.AMOUNT
            FROM LG_{f}_{p}_STFICHE STF (NOLOCK)
            JOIN LG_{f}_{p}_STLINE STL (NOLOCK) ON STF.LOGICALREF = STL.STFICHEREF
            JOIN LG_{f}_ITEMS ITEM (NOLOCK) ON STL.STOCKREF = ITEM.LOGICALREF
            JOIN L_CAPIWHOUSE W1 (NOLOCK) ON STF.SOURCEINDEX = W1.NR AND W1.FIRMANR = %s
            JOIN L_CAPIWHOUSE W2 (NOLOCK) ON STF.DESTINDEX = W2.NR AND W2.FIRMANR = %s
            WHERE STF.TRCODE = 25 -- Stock Transfer
            AND STF.DATE_ BETWEEN %s AND %s
        """
        return db_manager.execute_ms_query(query, (f, f, start_date, end_date))

    async def get_cashflow_report(self, firma: str = None, period: str = None):
        """Nakit Akış Analizi (Kasa/Banka Özet)"""
        f = firma or self.firma_no
        p = period or self.period_no
        query = f"""
            SELECT 'KASA' AS TYPE, NAME, SUM(CASH.AMOUNT) AS BALANCE
            FROM LG_{f}_KSCARD KSC (NOLOCK)
            LEFT JOIN LG_{f}_{p}_KSLINES CASH (NOLOCK) ON KSC.LOGICALREF = CASH.CARDREF
            GROUP BY NAME
            UNION ALL
            SELECT 'BANKA' AS TYPE, DEFINITION_ AS NAME, SUM(BNT.DEBIT - BNT.CREDIT) AS BALANCE
            FROM LG_{f}_BANKACC BNC (NOLOCK)
            LEFT JOIN LG_{f}_{p}_BNTOT BNT (NOLOCK) ON BNC.LOGICALREF = BNT.BANKACCREF
            GROUP BY DEFINITION_
        """
        return db_manager.execute_ms_query(query)

    async def get_report_data(self, report_code: str, firma: str = None, period: str = None, params: dict = None):
        """160+ Rapor Şablonunu Logo Veritabanına Eşleyen Generic Motor"""
        f = firma or self.firma_no
        p = period or self.period_no
        
        # Report Registry: Mapping generic codes to Logo MSSQL
        registry = {
            # 1.1 Inventory (Stok)
            "INV_REPORT_01": f"SELECT ITEM.CODE, ITEM.NAME, SUM(GNT.ONHAND) AS VALUE FROM LG_{f}_ITEMS ITEM (NOLOCK) LEFT JOIN LG_{f}_{p}_GNTOTST GNT (NOLOCK) ON ITEM.LOGICALREF = GNT.STOCKREF GROUP BY ITEM.CODE, ITEM.NAME",
            "INV_REPORT_02": f"SELECT W.NAME AS WH_NAME, SUM(GNT.ONHAND) AS VALUE FROM L_CAPIWHOUSE W (NOLOCK) LEFT JOIN LG_{f}_{p}_GNTOTST GNT (NOLOCK) ON W.NR = GNT.INVENNO JOIN LG_{f}_ITEMS I (NOLOCK) ON GNT.STOCKREF = I.LOGICALREF WHERE W.FIRMANR = {f} GROUP BY W.NAME",
            "INV_REPORT_03": f"SELECT ITEM.STGRPCODE AS GROUP_CODE, SUM(GNT.ONHAND) AS VALUE FROM LG_{f}_ITEMS ITEM (NOLOCK) LEFT JOIN LG_{f}_{p}_GNTOTST GNT (NOLOCK) ON ITEM.LOGICALREF = GNT.STOCKREF GROUP BY ITEM.STGRPCODE",
            
            # 1.2 Sales (Satış)
            "SAL_REPORT_01": f"SELECT DATE_ AS REPORT_DATE, SUM(NETTOTAL) AS TOTAL_AMOUNT FROM LG_{f}_{p}_INVOICE (NOLOCK) WHERE TRCODE IN (7,8) GROUP BY DATE_",
            "SAL_REPORT_02": f"SELECT CLC.DEFINITION_ AS CUSTOMER, SUM(INV.NETTOTAL) AS TOTAL_AMOUNT FROM LG_{f}_{p}_INVOICE INV (NOLOCK) JOIN LG_{f}_CLCARD CLC (NOLOCK) ON INV.CLIENTREF = CLC.LOGICALREF WHERE INV.TRCODE IN (7,8) GROUP BY CLC.DEFINITION_",
            "SAL_REPORT_03": f"SELECT SLS.DEFINITION_ AS SALESMAN, SUM(INV.NETTOTAL) AS TOTAL_AMOUNT FROM LG_{f}_{p}_INVOICE INV (NOLOCK) JOIN LG_SLSMAN SLS (NOLOCK) ON INV.SALESMANREF = SLS.LOGICALREF WHERE INV.TRCODE IN (7,8) GROUP BY SLS.DEFINITION_",
            
            # 1.3 Purchase (Satın Alma)
            "PUR_REPORT_01": f"SELECT DATE_ AS REPORT_DATE, SUM(NETTOTAL) AS TOTAL_AMOUNT FROM LG_{f}_{p}_INVOICE (NOLOCK) WHERE TRCODE IN (1,2) GROUP BY DATE_",
            "PUR_REPORT_02": f"SELECT CLC.DEFINITION_ AS VENDOR, SUM(INV.NETTOTAL) AS TOTAL_AMOUNT FROM LG_{f}_{p}_INVOICE INV (NOLOCK) JOIN LG_{f}_CLCARD CLC (NOLOCK) ON INV.CLIENTREF = CLC.LOGICALREF WHERE INV.TRCODE IN (1,2) GROUP BY CLC.DEFINITION_",
            
            # 1.4 Finance (Finans)
            "FIN_REPORT_01": f"SELECT DATE_ AS REPORT_DATE, SUM(AMOUNT) AS TOTAL FROM LG_{f}_{p}_KSLINES (NOLOCK) GROUP BY DATE_",
            "FIN_REPORT_02": f"SELECT BN.DEFINITION_ AS BANK, SUM(BNT.DEBIT - BNT.CREDIT) AS BALANCE FROM LG_{f}_BANKACC BN (NOLOCK) LEFT JOIN LG_{f}_{p}_BNTOT BNT (NOLOCK) ON BN.LOGICALREF = BNT.BANKACCREF GROUP BY BN.DEFINITION_",
            "FIN_REPORT_03": f"SELECT CLC.DEFINITION_ AS CUSTOMER, SUM(CASE WHEN DATEDIFF(DAY, DATE_, GETDATE()) > 30 THEN NETTOTAL ELSE 0 END) AS OVER_30_DAYS, SUM(CASE WHEN DATEDIFF(DAY, DATE_, GETDATE()) > 60 THEN NETTOTAL ELSE 0 END) AS OVER_60_DAYS FROM LG_{f}_{p}_INVOICE INV (NOLOCK) JOIN LG_{f}_CLCARD CLC (NOLOCK) ON INV.CLIENTREF = CLC.LOGICALREF WHERE INV.TRCODE IN (7,8) GROUP BY CLC.DEFINITION_",
            "FIN_REPORT_04": f"SELECT INV.FICHENO, CLC.DEFINITION_ AS CUSTOMER, INV.DATE_ AS DOC_DATE, INV.NETTOTAL FROM LG_{f}_{p}_INVOICE INV (NOLOCK) JOIN LG_{f}_CLCARD CLC (NOLOCK) ON INV.CLIENTREF = CLC.LOGICALREF WHERE INV.NETTOTAL > 0 AND DATEDIFF(DAY, INV.DATE_, GETDATE()) > 90",
            
            # 1.5 Ops (Saha)
            "OPS_REPORT_01": f"SELECT DATE_ AS REPORT_DATE, COUNT(*) AS ORDER_COUNT FROM LG_{f}_{p}_ORFICHE (NOLOCK) WHERE TRCODE = 1 GROUP BY DATE_",
            "OPS_REPORT_02": f"SELECT device_id, sync_time, status, error_message FROM sync_logs (NOLOCK) WHERE status = 'ERROR' ORDER BY sync_time DESC",
            "OPS_REPORT_03": f"SELECT salesman_name, timestamp, latitude, longitude FROM gps_logs (NOLOCK) ORDER BY timestamp DESC",

            # 1.6 Production (Üretim)
            "PROD_REPORT_01": f"SELECT BOM.CODE AS BOM_CODE, ITEM.NAME AS ITEM_NAME, BOM.DEFINITION_ AS BOM_DESC FROM LG_{f}_BOMASTER BOM (NOLOCK) JOIN LG_{f}_ITEMS ITEM (NOLOCK) ON BOM.MAINITEMREF = ITEM.LOGICALREF",
            "PROD_REPORT_02": f"SELECT FICHENO, DATE_, LINE.PDBNAME AS DEPT, ITEM.NAME AS ITEM_NAME, AMOUNT FROM LG_{f}_{p}_PRODORD ORD (NOLOCK) JOIN LG_{f}_ITEMS ITEM (NOLOCK) ON ORD.ITEMREF = ITEM.LOGICALREF LEFT JOIN LG_{f}_WORKSTAT LINE (NOLOCK) ON ORD.WORKSTATREF = LINE.LOGICALREF",
            "PROD_REPORT_03": f"SELECT WS.CODE, WS.DEFINITION_, COUNT(ORD.LOGICALREF) AS ACTIVE_ORDERS FROM LG_{f}_WORKSTAT WS (NOLOCK) LEFT JOIN LG_{f}_{p}_PRODORD ORD (NOLOCK) ON WS.LOGICALREF = ORD.WORKSTATREF GROUP BY WS.CODE, WS.DEFINITION_",

            # 1.7 Advanced Analytics
            "SAL_REPORT_04": f"SELECT ITEM.CODE, ITEM.NAME, SUM(CASE WHEN YEAR(DATE_) = YEAR(GETDATE()) THEN NETTOTAL ELSE 0 END) AS THIS_YEAR, SUM(CASE WHEN YEAR(DATE_) = YEAR(GETDATE())-1 THEN NETTOTAL ELSE 0 END) AS LAST_YEAR FROM LG_{f}_{p}_STLINE STL (NOLOCK) JOIN LG_{f}_ITEMS ITEM (NOLOCK) ON STL.STOCKREF = ITEM.LOGICALREF GROUP BY ITEM.CODE, ITEM.NAME",
            "SAL_REPORT_05": f"SELECT DATEPART(week, DATE_) as WEEK_NO, SUM(NETTOTAL) FROM LG_{f}_{p}_STLINE (NOLOCK) WHERE TRCODE IN (7,8) GROUP BY DATEPART(week, DATE_)",
            "SAL_REPORT_10": f"SELECT CLC.DEFINITION_ AS CUSTOMER, SUM(STL.VATMATRAH) AS REVENUE, SUM(STL.OUTCOST) AS COST, (SUM(STL.VATMATRAH) - SUM(STL.OUTCOST)) AS PROFIT FROM LG_{f}_{p}_STLINE STL (NOLOCK) JOIN LG_{f}_CLCARD CLC (NOLOCK) ON STL.CLIENTREF = CLC.LOGICALREF GROUP BY CLC.DEFINITION_",
            "PUR_REPORT_03": f"SELECT CLC.DEFINITION_ AS VENDOR, COUNT(*) AS ORDER_COUNT, AVG(NETTOTAL) AS AVG_ORDER_VALUE FROM LG_{f}_{p}_INVOICE (NOLOCK) JOIN LG_{f}_CLCARD CLC (NOLOCK) ON CLIENTREF = CLC.LOGICALREF WHERE TRCODE = 1 GROUP BY CLC.DEFINITION_",
            "PUR_REPORT_04": f"SELECT FICHENO, CLC.DEFINITION_ AS VENDOR, DATE_, DATEDIFF(DAY, DATE_, GETDATE()) AS DAYS_OVERDUE FROM LG_{f}_{p}_ORFICHE (NOLOCK) JOIN LG_{f}_CLCARD CLC (NOLOCK) ON CLIENTREF = CLC.LOGICALREF WHERE TRCODE = 2 AND STATUS = 1",
            
            # 1.8 Inventory Depth
            "INV_REPORT_02": f"SELECT L.NAME AS WAREHOUSE, SUM(I.ONHAND) AS STOCK FROM LV_{f}_{p}_GNTOTST I (NOLOCK) JOIN L_CAPIWHOUSE L (NOLOCK) ON I.INVENNO = L.NR WHERE I.ITEMREF > 0 GROUP BY L.NAME",
            "INV_REPORT_04": f"SELECT ITEM.CODE, ITEM.NAME, SUM(I.RESERVED) AS RESERVED FROM LV_{f}_{p}_GNTOTST I (NOLOCK) JOIN LG_{f}_ITEMS ITEM (NOLOCK) ON I.ITEMREF = ITEM.LOGICALREF WHERE I.RESERVED > 0 GROUP BY ITEM.CODE, ITEM.NAME",
            
            # 1.9 Quality
            "QC_REPORT_01": f"SELECT ITEM.NAME, COUNT(*) AS REJECT_COUNT FROM LG_{f}_{p}_STLINE STL (NOLOCK) JOIN LG_{f}_ITEMS ITEM (NOLOCK) ON STL.STOCKREF = ITEM.LOGICALREF WHERE TRCODE = 3 GROUP BY ITEM.NAME",
        }

        # Fallback to generic code if not in registry for testing purposes
        # In production, we would map all 160 codes.
        sql = registry.get(report_code)
        if not sql:
            # If not mapped yet, provide a placeholder query for high codes
            sql = f"SELECT 'NOT_MAPPED' AS STATUS, '{report_code}' AS CODE"
            
        return db_manager.execute_ms_query(sql)

    async def get_unit_code(self, item_code: str):
        # Implementation remains the same
        query = f"""
            SELECT TOP 1 UNIT_CODE 
            FROM LG_{self.firma_no}_UNITSETL (NOLOCK)
            WHERE ITEMREF = (SELECT LOGICALREF FROM LG_{self.firma_no}_ITEMS (NOLOCK) WHERE CODE = '{item_code}')
            ORDER BY LINENR
        """
        result = db_manager.execute_ms_query(query)
        return result[0]['UNIT_CODE'] if result else "ADET"

    # =====================================================
    # YEAR-OVER-YEAR (YoY) COMPARISON REPORTS
    # =====================================================
    
    async def get_yoy_daily_comparison(self, firma: str = None, period: str = None):
        """
        Year-over-Year Daily Comparison
        Compares today vs same day last year
        """
        f = firma or self.firma_no
        p = period or self.period_no
        
        query = f"""
        WITH CurrentDay AS (
            SELECT 
                COUNT(DISTINCT I.LOGICALREF) AS invoice_count,
                ISNULL(SUM(I.NETTOTAL), 0) AS total_revenue,
                ISNULL(AVG(I.NETTOTAL), 0) AS avg_order_value,
                COUNT(DISTINCT I.CLIENTREF) AS active_customers,
                COUNT(DISTINCT ST.LOGICALREF) AS stock_movement_count,
                ISNULL(SUM(ST.AMOUNT * ST.PRICE), 0) AS stock_movement_value
            FROM LG_{f}_{p}_INVOICE I WITH (NOLOCK)
            LEFT JOIN LG_{f}_{p}_STLINE ST WITH (NOLOCK) ON ST.DATE_ = CAST(GETDATE() AS DATE)
            WHERE CAST(I.DATE_ AS DATE) = CAST(GETDATE() AS DATE)
        ),
        LastYearSameDay AS (
            SELECT 
                COUNT(DISTINCT I.LOGICALREF) AS invoice_count,
                ISNULL(SUM(I.NETTOTAL), 0) AS total_revenue,
                ISNULL(AVG(I.NETTOTAL), 0) AS avg_order_value,
                COUNT(DISTINCT I.CLIENTREF) AS active_customers,
                COUNT(DISTINCT ST.LOGICALREF) AS stock_movement_count,
                ISNULL(SUM(ST.AMOUNT * ST.PRICE), 0) AS stock_movement_value
            FROM LG_{f}_{p}_INVOICE I WITH (NOLOCK)
            LEFT JOIN LG_{f}_{p}_STLINE ST WITH (NOLOCK) 
                ON ST.DATE_ = DATEADD(YEAR, -1, CAST(GETDATE() AS DATE))
            WHERE CAST(I.DATE_ AS DATE) = DATEADD(YEAR, -1, CAST(GETDATE() AS DATE))
        )
        SELECT 
            'DAILY' AS period_type,
            CAST(GETDATE() AS DATE) AS current_date,
            DATEADD(YEAR, -1, CAST(GETDATE() AS DATE)) AS last_year_date,
            
            -- Current Period
            C.invoice_count AS current_invoice_count,
            C.total_revenue AS current_revenue,
            C.avg_order_value AS current_avg_order,
            C.active_customers AS current_customers,
            C.stock_movement_count AS current_stock_movements,
            C.stock_movement_value AS current_stock_value,
            
            -- Last Year Same Period
            L.invoice_count AS ly_invoice_count,
            L.total_revenue AS ly_revenue,
            L.avg_order_value AS ly_avg_order,
            L.active_customers AS ly_customers,
            L.stock_movement_count AS ly_stock_movements,
            L.stock_movement_value AS ly_stock_value,
            
            -- Differences
            C.invoice_count - L.invoice_count AS diff_invoice_count,
            C.total_revenue - L.total_revenue AS diff_revenue,
            C.avg_order_value - L.avg_order_value AS diff_avg_order,
            C.active_customers - L.active_customers AS diff_customers,
            
            -- Percentage Changes
            CASE WHEN L.invoice_count = 0 THEN NULL 
                 ELSE ((C.invoice_count - L.invoice_count) * 100.0 / L.invoice_count) END AS pct_change_invoices,
            CASE WHEN L.total_revenue = 0 THEN NULL 
                 ELSE ((C.total_revenue - L.total_revenue) * 100.0 / L.total_revenue) END AS pct_change_revenue,
            CASE WHEN L.avg_order_value = 0 THEN NULL 
                 ELSE ((C.avg_order_value - L.avg_order_value) * 100.0 / L.avg_order_value) END AS pct_change_avg_order,
            CASE WHEN L.active_customers = 0 THEN NULL 
                 ELSE ((C.active_customers - L.active_customers) * 100.0 / L.active_customers) END AS pct_change_customers
        FROM CurrentDay C
        CROSS JOIN LastYearSameDay L
        """
        
        try:
            results = db_manager.execute_ms_query(query)
            return results[0] if results else {}
        except Exception as e:
            logger.error(f"YoY Daily Comparison failed: {e}")
            return {}
    
    async def get_yoy_weekly_comparison(self, firma: str = None, period: str = None):
        """
        Year-over-Year Weekly Comparison
        Compares this week vs same week last year
        """
        f = firma or self.firma_no
        p = period or self.period_no
        
        query = f"""
        WITH CurrentWeek AS (
            SELECT 
                COUNT(DISTINCT I.LOGICALREF) AS invoice_count,
                ISNULL(SUM(I.NETTOTAL), 0) AS total_revenue,
                ISNULL(AVG(I.NETTOTAL), 0) AS avg_order_value,
                COUNT(DISTINCT I.CLIENTREF) AS active_customers,
                ISNULL(SUM(K.AMOUNT), 0) AS total_collections,
                COUNT(DISTINCT K.LOGICALREF) AS collection_count
            FROM LG_{f}_{p}_INVOICE I WITH (NOLOCK)
            LEFT JOIN LG_{f}_{p}_KSLINES K WITH (NOLOCK) 
                ON K.DATE_ BETWEEN DATEADD(DAY, 1-DATEPART(WEEKDAY, GETDATE()), CAST(GETDATE() AS DATE))
                               AND CAST(GETDATE() AS DATE)
            WHERE I.DATE_ BETWEEN DATEADD(DAY, 1-DATEPART(WEEKDAY, GETDATE()), CAST(GETDATE() AS DATE))
                              AND CAST(GETDATE() AS DATE)
        ),
        LastYearSameWeek AS (
            SELECT 
                COUNT(DISTINCT I.LOGICALREF) AS invoice_count,
                ISNULL(SUM(I.NETTOTAL), 0) AS total_revenue,
                ISNULL(AVG(I.NETTOTAL), 0) AS avg_order_value,
                COUNT(DISTINCT I.CLIENTREF) AS active_customers,
                ISNULL(SUM(K.AMOUNT), 0) AS total_collections,
                COUNT(DISTINCT K.LOGICALREF) AS collection_count
            FROM LG_{f}_{p}_INVOICE I WITH (NOLOCK)
            LEFT JOIN LG_{f}_{p}_KSLINES K WITH (NOLOCK) 
                ON K.DATE_ BETWEEN DATEADD(YEAR, -1, DATEADD(DAY, 1-DATEPART(WEEKDAY, GETDATE()), CAST(GETDATE() AS DATE)))
                               AND DATEADD(YEAR, -1, CAST(GETDATE() AS DATE))
            WHERE I.DATE_ BETWEEN DATEADD(YEAR, -1, DATEADD(DAY, 1-DATEPART(WEEKDAY, GETDATE()), CAST(GETDATE() AS DATE)))
                              AND DATEADD(YEAR, -1, CAST(GETDATE() AS DATE))
        )
        SELECT 
            'WEEKLY' AS period_type,
            DATEADD(DAY, 1-DATEPART(WEEKDAY, GETDATE()), CAST(GETDATE() AS DATE)) AS current_week_start,
            CAST(GETDATE() AS DATE) AS current_week_end,
            DATEADD(YEAR, -1, DATEADD(DAY, 1-DATEPART(WEEKDAY, GETDATE()), CAST(GETDATE() AS DATE))) AS ly_week_start,
            DATEADD(YEAR, -1, CAST(GETDATE() AS DATE)) AS ly_week_end,
            
            -- Current Period
            C.invoice_count AS current_invoice_count,
            C.total_revenue AS current_revenue,
            C.avg_order_value AS current_avg_order,
            C.active_customers AS current_customers,
            C.total_collections AS current_collections,
            C.collection_count AS current_collection_count,
            
            -- Last Year Same Period
            L.invoice_count AS ly_invoice_count,
            L.total_revenue AS ly_revenue,
            L.avg_order_value AS ly_avg_order,
            L.active_customers AS ly_customers,
            L.total_collections AS ly_collections,
            L.collection_count AS ly_collection_count,
            
            -- Differences
            C.invoice_count - L.invoice_count AS diff_invoice_count,
            C.total_revenue - L.total_revenue AS diff_revenue,
            C.total_collections - L.total_collections AS diff_collections,
            
            -- Percentage Changes
            CASE WHEN L.invoice_count = 0 THEN NULL 
                 ELSE ((C.invoice_count - L.invoice_count) * 100.0 / L.invoice_count) END AS pct_change_invoices,
            CASE WHEN L.total_revenue = 0 THEN NULL 
                 ELSE ((C.total_revenue - L.total_revenue) * 100.0 / L.total_revenue) END AS pct_change_revenue,
            CASE WHEN L.total_collections = 0 THEN NULL 
                 ELSE ((C.total_collections - L.total_collections) * 100.0 / L.total_collections) END AS pct_change_collections
        FROM CurrentWeek C
        CROSS JOIN LastYearSameWeek L
        """
        
        try:
            results = db_manager.execute_ms_query(query)
            return results[0] if results else {}
        except Exception as e:
            logger.error(f"YoY Weekly Comparison failed: {e}")
            return {}
    
    async def get_yoy_monthly_comparison(self, firma: str = None, period: str = None):
        """
        Year-over-Year Monthly Comparison
        Compares this month vs same month last year
        """
        f = firma or self.firma_no
        p = period or self.period_no
        
        query = f"""
        WITH CurrentMonth AS (
            SELECT 
                COUNT(DISTINCT I.LOGICALREF) AS invoice_count,
                ISNULL(SUM(I.NETTOTAL), 0) AS total_revenue,
                ISNULL(AVG(I.NETTOTAL), 0) AS avg_order_value,
                COUNT(DISTINCT I.CLIENTREF) AS active_customers,
                COUNT(DISTINCT CASE WHEN I.DATE_ >= DATEADD(MONTH, -1, GETDATE()) THEN I.CLIENTREF END) AS new_customers,
                ISNULL(SUM(K.AMOUNT), 0) AS total_collections,
                COUNT(DISTINCT K.LOGICALREF) AS collection_count,
                COUNT(DISTINCT ST.LOGICALREF) AS stock_movement_count,
                ISNULL(SUM(ST.AMOUNT * ST.PRICE), 0) AS stock_movement_value
            FROM LG_{f}_{p}_INVOICE I WITH (NOLOCK)
            LEFT JOIN LG_{f}_{p}_KSLINES K WITH (NOLOCK) 
                ON YEAR(K.DATE_) = YEAR(GETDATE()) AND MONTH(K.DATE_) = MONTH(GETDATE())
            LEFT JOIN LG_{f}_{p}_STLINE ST WITH (NOLOCK)
                ON YEAR(ST.DATE_) = YEAR(GETDATE()) AND MONTH(ST.DATE_) = MONTH(GETDATE())
            WHERE YEAR(I.DATE_) = YEAR(GETDATE()) AND MONTH(I.DATE_) = MONTH(GETDATE())
        ),
        LastYearSameMonth AS (
            SELECT 
                COUNT(DISTINCT I.LOGICALREF) AS invoice_count,
                ISNULL(SUM(I.NETTOTAL), 0) AS total_revenue,
                ISNULL(AVG(I.NETTOTAL), 0) AS avg_order_value,
                COUNT(DISTINCT I.CLIENTREF) AS active_customers,
                COUNT(DISTINCT CASE WHEN I.DATE_ >= DATEADD(MONTH, -1, DATEADD(YEAR, -1, GETDATE())) THEN I.CLIENTREF END) AS new_customers,
                ISNULL(SUM(K.AMOUNT), 0) AS total_collections,
                COUNT(DISTINCT K.LOGICALREF) AS collection_count,
                COUNT(DISTINCT ST.LOGICALREF) AS stock_movement_count,
                ISNULL(SUM(ST.AMOUNT * ST.PRICE), 0) AS stock_movement_value
            FROM LG_{f}_{p}_INVOICE I WITH (NOLOCK)
            LEFT JOIN LG_{f}_{p}_KSLINES K WITH (NOLOCK) 
                ON YEAR(K.DATE_) = YEAR(DATEADD(YEAR, -1, GETDATE())) 
                AND MONTH(K.DATE_) = MONTH(GETDATE())
            LEFT JOIN LG_{f}_{p}_STLINE ST WITH (NOLOCK)
                ON YEAR(ST.DATE_) = YEAR(DATEADD(YEAR, -1, GETDATE())) 
                AND MONTH(ST.DATE_) = MONTH(GETDATE())
            WHERE YEAR(I.DATE_) = YEAR(DATEADD(YEAR, -1, GETDATE())) 
              AND MONTH(I.DATE_) = MONTH(GETDATE())
        )
        SELECT 
            'MONTHLY' AS period_type,
            DATEFROMPARTS(YEAR(GETDATE()), MONTH(GETDATE()), 1) AS current_month_start,
            EOMONTH(GETDATE()) AS current_month_end,
            DATEFROMPARTS(YEAR(DATEADD(YEAR, -1, GETDATE())), MONTH(GETDATE()), 1) AS ly_month_start,
            EOMONTH(DATEADD(YEAR, -1, GETDATE())) AS ly_month_end,
            
            -- Current Period
            C.invoice_count AS current_invoice_count,
            C.total_revenue AS current_revenue,
            C.avg_order_value AS current_avg_order,
            C.active_customers AS current_customers,
            C.new_customers AS current_new_customers,
            C.total_collections AS current_collections,
            C.collection_count AS current_collection_count,
            C.stock_movement_count AS current_stock_movements,
            C.stock_movement_value AS current_stock_value,
            
            -- Last Year Same Period
            L.invoice_count AS ly_invoice_count,
            L.total_revenue AS ly_revenue,
            L.avg_order_value AS ly_avg_order,
            L.active_customers AS ly_customers,
            L.new_customers AS ly_new_customers,
            L.total_collections AS ly_collections,
            L.collection_count AS ly_collection_count,
            L.stock_movement_count AS ly_stock_movements,
            L.stock_movement_value AS ly_stock_value,
            
            -- Differences
            C.invoice_count - L.invoice_count AS diff_invoice_count,
            C.total_revenue - L.total_revenue AS diff_revenue,
            C.total_collections - L.total_collections AS diff_collections,
            C.stock_movement_value - L.stock_movement_value AS diff_stock_value,
            
            -- Percentage Changes
            CASE WHEN L.invoice_count = 0 THEN NULL 
                 ELSE ((C.invoice_count - L.invoice_count) * 100.0 / L.invoice_count) END AS pct_change_invoices,
            CASE WHEN L.total_revenue = 0 THEN NULL 
                 ELSE ((C.total_revenue - L.total_revenue) * 100.0 / L.total_revenue) END AS pct_change_revenue,
            CASE WHEN L.total_collections = 0 THEN NULL 
                 ELSE ((C.total_collections - L.total_collections) * 100.0 / L.total_collections) END AS pct_change_collections,
            CASE WHEN L.stock_movement_value = 0 THEN NULL 
                 ELSE ((C.stock_movement_value - L.stock_movement_value) * 100.0 / L.stock_movement_value) END AS pct_change_stock_value
        FROM CurrentMonth C
        CROSS JOIN LastYearSameMonth L
        """
        
        try:
            results = db_manager.execute_ms_query(query)
            return results[0] if results else {}
        except Exception as e:
            logger.error(f"YoY Monthly Comparison failed: {e}")
            return {}

logo_service = LogoIntegrationService()
