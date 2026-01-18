from loguru import logger
from ..core.database import db_manager
from datetime import datetime
import re

class ProfilerService:
    def __init__(self):
        self._listening = False
        self._start_time = None
        self._captured_queries = []

    def start_trace(self):
        """
        Marks the start time for the trace.
        """
        self._listening = True
        self._start_time = datetime.now()
        self._captured_queries = []
        logger.info(f"SQL Profiler Started at {self._start_time}")
        return True, "Profiler Started. Perform your operations in Logo now."

    async def stop_and_analyze(self, firma_no: str):
        """
        Stops the trace, queries DMVs for SQLs executed after start_time,
        and attempts to construct a View definition.
        """
        if not self._listening or not self._start_time:
            return False, "Profiler was not running."

        self._listening = False
        stop_time = datetime.now()
        logger.info(f"Profiler Stopped at {stop_time}")

        # 1. Query DMVs for recently executed SQLs
        # We look for queries containing 'LG_' (Logo tables) executed since start_time
        # This is heuristics-based.
        # sys.dm_exec_query_stats tracks cached plans. 
        # last_execution_time is crucial.
        
        # Note: This query requires VIEW SERVER STATE permission usually.
        # If user is db_owner/sysadmin it works.
        
        query = f"""
            SELECT TOP 50
                st.text AS SQL_TEXT,
                qs.last_execution_time,
                qs.execution_count
            FROM sys.dm_exec_query_stats qs
            CROSS APPLY sys.dm_exec_sql_text(qs.sql_handle) st
            WHERE qs.last_execution_time >= '{self._start_time.strftime('%Y-%m-%d %H:%M:%S')}'
            AND st.text LIKE '%LG_{firma_no}%'
            AND st.text NOT LIKE '%sys.dm_%' -- Exclude self
            AND st.text NOT LIKE '%INSERT INTO%' -- Focus on SELECTs usually for reports
            AND st.text NOT LIKE '%UPDATE%'
            ORDER BY qs.last_execution_time DESC
        """
        
        try:
            results = db_manager.execute_ms_query(query)
            if not results:
                return True, {"message": "No relevant queries captured.", "sql": [], "view_suggestion": ""}

            # 2. Analyze & Filter
            unique_sqls = []
            seen = set()
            
            longest_sql = ""
            
            for row in results:
                raw_sql = row['SQL_TEXT'].strip()
                if raw_sql in seen: continue
                seen.add(raw_sql)
                unique_sqls.append(raw_sql)
                
                # Heuristic: The report query is usually the longest/most complex SELECT
                if len(raw_sql) > len(longest_sql):
                    longest_sql = raw_sql

            # 3. Generate View Suggestion
            view_name = f"V_CUSTOM_REPORT_{datetime.now().strftime('%Y%m%d_%H%M')}"
            view_def = f"CREATE OR ALTER VIEW {view_name} AS\n"
            view_def += longest_sql
            
            return True, {
                "message": f"Captured {len(unique_sqls)} queries.",
                "captured_sqls": unique_sqls,
                "view_suggestion": view_def
            }
            
        except Exception as e:
            logger.error(f"Profiler Error: {e}")
            return False, f"Profiler Error: {e}"

profiler_service = ProfilerService()
