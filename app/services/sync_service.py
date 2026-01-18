import json
from loguru import logger
from ..core.database import db_manager
from ..core.config import settings
from .logo_service import logo_service

class ReportSyncService:
    def __init__(self):
        pass

    async def generate_and_save_snapshot(self, report_code: str, firma: str = None, period: str = None):
        """EXFIN Raporunun bir snapshot'ını alıp PostgreSQL'e kaydeder"""
        f = firma or settings.LOGO_FIRMA_NO
        p = period or settings.LOGO_PERIOD_NO
        tenant_id = f"{f}_{p}"

        logger.info(f"Generating snapshot for {report_code} (Tenant: {tenant_id})")
        
        # 1. Fetch data from Logo (MSSQL)
        data = await logo_service.get_report_data(report_code, firma=f, period=p)
        
        if data is None:
            logger.error(f"Failed to fetch data for report {report_code}")
            return False

        # 2. Save/Update snapshot in PostgreSQL
        query = """
            INSERT INTO report_snapshots (report_code, tenant_id, snapshot_data, version_id)
            VALUES (%s, %s, %s, 1)
            ON CONFLICT (report_code, tenant_id) DO UPDATE
            SET snapshot_data = EXCLUDED.snapshot_data,
                version_id = report_snapshots.version_id + 1,
                updated_at = CURRENT_TIMESTAMP
        """
        success = db_manager.execute_pg_query(query, (report_code, tenant_id, json.dumps(data)), fetch=False)
        
        if success:
            logger.info(f"Snapshot for {report_code} saved successfully.")
        return success

    async def get_latest_snapshot(self, report_code: str, firma: str = None, period: str = None):
        """En son kaydedilen snapshot dökümünü getirir"""
        f = firma or settings.LOGO_FIRMA_NO
        p = period or settings.LOGO_PERIOD_NO
        tenant_id = f"{f}_{p}"

        query = "SELECT snapshot_data, version_id, updated_at FROM report_snapshots WHERE report_code = %s AND tenant_id = %s"
        result = db_manager.execute_pg_query(query, (report_code, tenant_id))
        
        if result and len(result) > 0:
            return result[0]
        return None

sync_service = ReportSyncService()
