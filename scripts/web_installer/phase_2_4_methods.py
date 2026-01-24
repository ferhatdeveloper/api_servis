    def get_logo_preview(self, ms_config, firm_id, data_type):
        """Preview Logo data before sync"""
        try:
            import pymssql
            
            ms_conn = pymssql.connect(
                server=ms_config["host"],
                user=ms_config["username"],
                password=ms_config["password"],
                database=ms_config["database"],
                charset='UTF-8'
            )
            ms_cur = ms_conn.cursor(as_dict=True)
            
            results = []
            
            if data_type == "companies":
                ms_cur.execute("SELECT TOP 50 NR, NAME, TAXNR FROM L_CAPIFIRM ORDER BY NR")
                for row in ms_cur.fetchall():
                    results.append({
                        "nr": row['NR'],
                        "name": row.get('NAME'),
                        "tax_nr": row.get('TAXNR')
                    })
            
            elif data_type == "salesmen":
                ms_cur.execute(f"SELECT TOP 50 CODE, DEFINITION_, EMAILADDR FROM LG_{firm_id}_SLSMAN WHERE ACTIVE=0 ORDER BY CODE")
                for row in ms_cur.fetchall():
                    results.append({
                        "code": row['CODE'],
                        "name": row.get('DEFINITION_'),
                        "email": row.get('EMAILADDR')
                    })
            
            elif data_type == "warehouses":
                ms_cur.execute(f"SELECT TOP 50 NR, NAME FROM L_CAPIWHOUSE WHERE FIRMNR={int(firm_id)} ORDER BY NR")
                for row in ms_cur.fetchall():
                    results.append({
                        "nr": row['NR'],
                        "name": row.get('NAME')
                    })
            
            elif data_type == "customers":
                ms_cur.execute(f"SELECT TOP 50 CODE, DEFINITION_, CITY FROM LG_{firm_id}_CLCARD WHERE ACTIVE=0 AND CARDTYPE<>22 ORDER BY CODE")
                for row in ms_cur.fetchall():
                    results.append({
                        "code": row['CODE'],
                        "name": row.get('DEFINITION_'),
                        "city": row.get('CITY')
                    })
            
            ms_conn.close()
            return {"success": True, "data": results}
            
        except Exception as e:
            return {"success": False, "error": self._extract_error(e)}
    
    def save_backup_config(self, config):
        """Save backup configuration to backup_config.json"""
        try:
            import json
            
            backup_config = {
                "backup_dir": config.get("backup_dir"),
                "backup_interval": config.get("backup_interval", "off"),
                "backup_time": config.get("backup_time", "23:00"),
                "backup_hours": config.get("backup_hours", "1"),
                "backup_days": config.get("backup_days", [])
            }
            
            config_path = os.path.join(self.project_dir, "backup_config.json")
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(backup_config, f, indent=4)
            
            return {"success": True, "message": "Backup configuration saved"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def generate_ssl_certificate(self):
        """Generate self-signed SSL certificate"""
        try:
            # Import the generate_cert script
            cert_script = os.path.join(self.project_dir, "scripts", "generate_cert.py")
            
            if not os.path.exists(cert_script):
                return {"success": False, "error": "generate_cert.py not found"}
            
            # Run the certificate generation
            import sys
            sys.path.insert(0, os.path.join(self.project_dir, "scripts"))
            import generate_cert
            
            cert_file, key_file = generate_cert.generate_self_signed_cert()
            
            # Update .env file
            env_path = os.path.join(self.project_dir, ".env")
            env_content = ""
            
            if os.path.exists(env_path):
                with open(env_path, "r") as f:
                    env_content = f.read()
            
            # Remove old SSL entries if exist
            lines = env_content.split("\n")
            lines = [l for l in lines if not l.startswith("SSL_CERT_FILE=") and not l.startswith("SSL_KEY_FILE=") and not l.startswith("USE_HTTPS=")]
            
            # Add new SSL entries
            lines.append(f"SSL_CERT_FILE={cert_file}")
            lines.append(f"SSL_KEY_FILE={key_file}")
            lines.append("USE_HTTPS=True")
            
            with open(env_path, "w") as f:
                f.write("\n".join(lines))
            
            return {
                "success": True,
                "cert_file": cert_file,
                "key_file": key_file,
                "message": "SSL certificate generated and .env updated"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
