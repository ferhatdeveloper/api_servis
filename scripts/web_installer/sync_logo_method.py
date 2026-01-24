    def sync_logo_data_selective(self, pg_config, ms_config, firm_id, salesmen, warehouses):
        """Syncs selected salesmen and warehouses from Logo to PostgreSQL"""
        try:
            import pymssql
            import psycopg2
            from passlib.context import CryptContext
            
            pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
            
            # MSSQL Connection
            ms_conn = pymssql.connect(
                server=ms_config["host"],
                user=ms_config["username"],
                password=ms_config["password"],
                database=ms_config["database"],
                charset='UTF-8'
            )
            ms_cur = ms_conn.cursor(as_dict=True)
            
            # PG Connection
            pg_conn = psycopg2.connect(
                host=pg_config["host"],
                port=pg_config["port"],
                user=pg_config["username"],
                password=pg_config["password"],
                database=pg_config["database"]
            )
            pg_cur = pg_conn.cursor()
            
            # 1. Sync Firm
            ms_cur.execute(f"SELECT NR, NAME FROM L_CAPIFIRM WHERE NR={int(firm_id)}")
            firm = ms_cur.fetchone()
            if not firm:
                return {"success": False, "error": f"Firma {firm_id} bulunamadı"}
            
            pg_cur.execute("""
                INSERT INTO companies (logo_nr, name, is_active)
                VALUES (%s, %s, true)
                ON CONFLICT (logo_nr) DO UPDATE SET name=EXCLUDED.name
                RETURNING id
            """, (firm['NR'], firm['NAME']))
            company_id = pg_cur.fetchone()[0]
            
            # 2. Sync Salesmen
            user_credentials = []
            for salesman in salesmen:
                salesman_id = salesman['id']
                username = salesman['username']
                password = salesman['password']
                
                # Get salesman details from Logo
                ms_cur.execute(f"""
                    SELECT CODE, DEFINITION_, EMAILADDR 
                    FROM LG_{firm_id}_SLSMAN 
                    WHERE CODE='{salesman_id}' AND ACTIVE=0
                """)
                s = ms_cur.fetchone()
                if not s:
                    continue
                
                # Insert into salesmen table
                pg_cur.execute("""
                    INSERT INTO salesmen (company_id, code, name, email)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (company_id, code) DO UPDATE 
                    SET name=EXCLUDED.name, email=EXCLUDED.email
                    RETURNING id
                """, (company_id, s['CODE'], s['DEFINITION_'], s.get('EMAILADDR')))
                salesman_db_id = pg_cur.fetchone()[0]
                
                # Create user account
                hashed_password = pwd_context.hash(password)
                pg_cur.execute("""
                    INSERT INTO users (username, password_hash, full_name, email, role, is_active)
                    VALUES (%s, %s, %s, %s, 'salesman', true)
                    ON CONFLICT (username) DO UPDATE 
                    SET password_hash=EXCLUDED.password_hash
                    RETURNING id
                """, (username, hashed_password, s['DEFINITION_'], s.get('EMAILADDR')))
                
                user_credentials.append({
                    'code': s['CODE'],
                    'name': s['DEFINITION_'],
                    'username': username,
                    'password': password
                })
            
            # 3. Sync Warehouses
            for warehouse_id in warehouses:
                ms_cur.execute(f"""
                    SELECT NR, NAME 
                    FROM L_CAPIWHOUSE 
                    WHERE NR={int(warehouse_id)} AND FIRMNR={int(firm_id)}
                """)
                w = ms_cur.fetchone()
                if not w:
                    continue
                
                pg_cur.execute("""
                    INSERT INTO warehouses (company_id, code, name, logo_ref)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (company_id, code) DO UPDATE 
                    SET name=EXCLUDED.name
                """, (company_id, str(w['NR']).zfill(2), w['NAME'], w['NR']))

            # 4. Sync Customers (Logo CLCARD)
            # Default to fetching top 500 customers if not specified, or all
            ms_cur.execute(f"""
                SELECT CODE, DEFINITION_, TAXOFFICE, TAXNR, ADDR1, ADDR2, CITY, TOWN, TELNRS1, EMAILADDR, LOGICALREF
                FROM LG_{firm_id}_CLCARD
                WHERE ACTIVE=0 AND CARDTYPE<>22
            """)
            logo_customers = ms_cur.fetchall()
            for c in logo_customers:
                full_address = f"{c.get('ADDR1', '')} {c.get('ADDR2', '')}".strip()
                pg_cur.execute("""
                    INSERT INTO customers (
                        company_id, code, name, tax_office, tax_number, 
                        address, city, district, phone, email, logo_ref
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (company_id, code) DO UPDATE SET
                        name=EXCLUDED.name,
                        tax_office=EXCLUDED.tax_office,
                        tax_number=EXCLUDED.tax_number,
                        address=EXCLUDED.address,
                        city=EXCLUDED.city,
                        district=EXCLUDED.district,
                        phone=EXCLUDED.phone,
                        email=EXCLUDED.email,
                        logo_ref=EXCLUDED.logo_ref,
                        updated_at=CURRENT_TIMESTAMP
                """, (
                    company_id, c['CODE'], c['DEFINITION_'], c.get('TAXOFFICE'), c.get('TAXNR'),
                    full_address, c.get('CITY'), c.get('TOWN'), c.get('TELNRS1'), c.get('EMAILADDR'), c['LOGICALREF']
                ))
            
            pg_conn.commit()
            pg_cur.close()
            pg_conn.close()
            ms_cur.close()
            ms_conn.close()
            
            # Generate PDF report
            pdf_url = None
            if user_credentials:
                try:
                    pdf_url = self._generate_credentials_pdf(user_credentials, firm['NAME'])
                except Exception as e:
                    print(f"PDF generation failed: {e}")
            
            return {
                "success": True,
                "message": f"{len(salesmen)} satışçı ve {len(warehouses)} ambar aktarıldı",
                "pdf_url": pdf_url
            }
            
        except Exception as e:
            return {"success": False, "error": self._extract_error(e)}
    
    def _generate_credentials_pdf(self, credentials, firm_name):
        """Generates a PDF report with user credentials"""
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib import colors
            from reportlab.lib.units import cm
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.enums import TA_CENTER
            import datetime
            
            # Create PDF in static folder
            pdf_filename = f"salesman_credentials_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            pdf_path = os.path.join(self.project_dir, "scripts", "web_installer", "static", pdf_filename)
            
            doc = SimpleDocTemplate(pdf_path, pagesize=A4)
            elements = []
            styles = getSampleStyleSheet()
            
            # Title
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=18,
                textColor=colors.HexColor('#1a237e'),
                spaceAfter=30,
                alignment=TA_CENTER
            )
            elements.append(Paragraph(f"EXFIN OPS - Kullanıcı Bilgileri", title_style))
            elements.append(Paragraph(f"Firma: {firm_name}", styles['Normal']))
            elements.append(Spacer(1, 0.5*cm))
            
            # Table
            table_data = [['Kod', 'İsim', 'Kullanıcı Adı', 'Şifre']]
            for cred in credentials:
                table_data.append([
                    cred['code'],
                    cred['name'],
                    cred['username'],
                    cred['password']
                ])
            
            table = Table(table_data, colWidths=[3*cm, 6*cm, 4*cm, 3*cm])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a237e')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            elements.append(table)
            doc.build(elements)
            
            return f"/static/{pdf_filename}"
            
        except Exception as e:
            print(f"PDF generation error: {e}")
            return None
