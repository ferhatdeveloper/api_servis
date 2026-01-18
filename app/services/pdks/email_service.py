import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Template
from datetime import datetime

logger = logging.getLogger(__name__)

class EmailService:
    """Sistem üzerinden rapor gönderimi için E-posta servisi"""
    
    PREMIUM_TEMPLATE = """
    <!DOCTYPE html>
    <html lang="tr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>EXFIN Günlük Raporu</title>
        <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; background-color: #f4F7Fa; }
            .container { max-width: 600px; margin: 20px auto; background: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
            .header { background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%); color: #ffffff; padding: 40px 20px; text-align: center; }
            .header h1 { margin: 0; font-size: 24px; letter-spacing: 1px; }
            .content { padding: 30px; }
            .greeting { font-size: 18px; margin-bottom: 20px; color: #1e3a8a; font-weight: 600; }
            .report-card { background: #f8fafc; border-left: 4px solid #3b82f6; padding: 20px; border-radius: 4px; margin-bottom: 25px; }
            .stats { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 25px; }
            .stat-item { background: #ffffff; padding: 15px; border-radius: 8px; border: 1px solid #e2e8f0; text-align: center; }
            .stat-value { font-size: 24px; font-weight: bold; color: #1e3a8a; }
            .stat-label { font-size: 12px; color: #64748b; text-transform: uppercase; }
            .footer { background: #f1f5f9; padding: 20px; text-align: center; font-size: 12px; color: #64748b; }
            .button { display: inline-block; padding: 12px 24px; background-color: #3b82f6; color: #ffffff; text-decoration: none; border-radius: 6px; font-weight: 600; margin-top: 10px; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>EXFIN PDKS</h1>
                <p>Günlük Otomatik Rapor</p>
            </div>
            <div class="content">
                <div class="greeting">Merhaba,</div>
                <p>{{ date }} tarihli günlük personel devam kontrol raporunuz hazırlandı. Sisteme dair özet bilgiler aşağıdadır:</p>
                
                <div class="report-card">
                    <strong>Rapor Detayı:</strong> {{ report_name }}<br>
                    <strong>Oluşturulma:</strong> {{ timestamp }}
                </div>
                
                <div class="stats">
                    <div class="stat-item">
                        <div class="stat-value">{{ total_checkins }}</div>
                        <div class="stat-label">Toplam Giriş</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">{{ total_absent }}</div>
                        <div class="stat-label">Gelmeyenler</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">{{ late_arrivals }}</div>
                        <div class="stat-label">Geç Kalanlar</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">{{ active_leaves }}</div>
                        <div class="stat-label">İzinli Olanlar</div>
                    </div>
                </div>

                <p>Detaylı raporu görüntülemek ve personel hareketlerini incelemek için panele giriş yapabilirsiniz.</p>
                
                <center>
                    <a href="{{ system_url }}" class="button">Sisteme Giriş Yap</a>
                </center>
            </div>
            <div class="footer">
                &copy; {{ current_year }} EXFIN Personel Devam Kontrol Sistemi<br>
                Bu e-posta otomatik olarak oluşturulmuştur, lütfen yanıtlamayınız.
            </div>
        </div>
    </body>
    </html>
    """

    @staticmethod
    def send_report_email(smtp_config: dict, recipients: list, report_data: dict):
        """Rapor e-postasını gönderir"""
        try:
            logger.info("📧 ========== EMAIL SEND ATTEMPT ==========")
            logger.info(f"📧 SMTP Server: {smtp_config.get('server')}")
            logger.info(f"📧 SMTP Port: {smtp_config.get('port')}")
            logger.info(f"📧 Username: {smtp_config.get('user')}")
            logger.info(f"📧 Recipients: {', '.join(recipients)}")
            
            msg = MIMEMultipart()
            msg['From'] = smtp_config.get('user')
            msg['To'] = ", ".join(recipients)
            msg['Subject'] = f"EXFIN Günlük PDKS Raporu - {report_data.get('date')}"

            # Template render
            template = Template(EmailService.PREMIUM_TEMPLATE)
            html_content = template.render(
                **report_data,
                current_year=datetime.now().year,
                timestamp=datetime.now().strftime("%H:%M:%S")
            )

            msg.attach(MIMEText(html_content, 'html'))

            # Port-based SSL/TLS configuration
            server_address = smtp_config.get('server')
            port = smtp_config.get('port')
            username = smtp_config.get('user')
            password = smtp_config.get('password')
            
            if port == 465:
                # Implicit SSL/TLS for port 465
                logger.info("📧 Using implicit SSL/TLS (port 465)")
                with smtplib.SMTP_SSL(server_address, port, timeout=30) as server:
                    logger.info("📧 SSL connection established")
                    server.login(username, password)
                    logger.info("📧 Authentication successful")
                    server.send_message(msg)
                    logger.info("✅ Email sent successfully!")
            else:
                # Explicit STARTTLS for port 587 or other ports
                logger.info(f"📧 Using STARTTLS (port {port})")
                with smtplib.SMTP(server_address, port, timeout=30) as server:
                    logger.info("📧 SMTP connection established")
                    if smtp_config.get('use_tls', True):
                        server.starttls()
                        logger.info("📧 STARTTLS upgrade successful")
                    server.login(username, password)
                    logger.info("📧 Authentication successful")
                    server.send_message(msg)
                    logger.info("✅ Email sent successfully!")
            
            logger.info("📧 ==========================================")
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            logger.error("❌ ========== EMAIL SEND FAILED ==========")
            logger.error(f"❌ Authentication Error: {str(e)}")
            logger.error("💡 TIP: Check username and password")
            logger.error("❌ ==========================================")
            return False
        except smtplib.SMTPConnectError as e:
            logger.error("❌ ========== EMAIL SEND FAILED ==========")
            logger.error(f"❌ Connection Error: {str(e)}")
            logger.error("💡 TIP: Check server address and port, verify firewall settings")
            logger.error("❌ ==========================================")
            return False
        except smtplib.SMTPException as e:
            logger.error("❌ ========== EMAIL SEND FAILED ==========")
            logger.error(f"❌ SMTP Error: {str(e)}")
            logger.error("❌ ==========================================")
            return False
        except Exception as e:
            logger.error("❌ ========== EMAIL SEND FAILED ==========")
            logger.error(f"❌ Error Type: {type(e).__name__}")
            logger.error(f"❌ Error Message: {str(e)}")
            logger.error("❌ ==========================================")
            return False
