from fastapi import APIRouter, Depends, HTTPException, status, Query, Request, Response
from loguru import logger
from app.services.system_service import system_service
from app.services.scheduler_service import scheduler_service
from app.services.profiler_service import profiler_service
from app.core.config import settings
from pydantic import BaseModel

router = APIRouter()

class ScheduleRequest(BaseModel):
    db_type: str # pg, mssql
    hour: int
    minute: int

from fastapi import Header

@router.post("/profiler/start")
async def start_profiler():
    """Start SQL Profiling Session"""
    success, msg = profiler_service.start_trace()
    return {"status": "success", "message": msg}

@router.post("/profiler/stop")
async def stop_profiler(x_firma: str = Header("001", alias="x-firma")): # Default 001 if header missing
    """Stop Profiler and Analyze Queries"""
    success, result = await profiler_service.stop_and_analyze(x_firma)
    if not success:
         raise HTTPException(status_code=500, detail=result)
    return {"status": "success", "data": result}


@router.post("/update")
async def update_system():
    """
    Triggers Auto-Update:
    1. Backup Current Version (retained 10 days)
    2. Git Pull Latest Code
    3. Restart Windows Service
    """
    logger.info("System update requested via API")
    if not settings.DEVELOPER_MODE: # Maybe secure this with a token?
         # For now open, but ideally should be protected.
         pass
         
    success, msg = await system_service.perform_update()
    
    if not success:
        raise HTTPException(status_code=500, detail=msg)
        
    return {"status": "success", "message": msg}

@router.post("/backup")
async def trigger_backup():
    """Manual Backup Trigger"""
    success, msg = system_service.backup_current_version()
    if not success:
        raise HTTPException(status_code=500, detail=msg)
    return {"status": "success", "file": msg}

@router.post("/db-backup")
async def trigger_db_backup(type: str = Query("pg", description="pg (PostgreSQL) or mssql (Logo)")):
    """Triggers Database Backup (Zipped)"""
    if type == "mssql":
        success, msg = system_service.backup_database_mssql()
    else:
        success, msg = system_service.backup_database_pg()
        
    if not success:
        raise HTTPException(status_code=500, detail=msg)
    return {"status": "success", "file": msg}

@router.get("/backups")
async def list_backups():
    """List available backups"""
    import glob
    import os
    files = glob.glob(os.path.join(system_service.backup_dir, "*.zip"))
    # Sort by time desc
    files.sort(key=os.path.getmtime, reverse=True)
    return {
        "count": len(files),
        "backups": [os.path.basename(f) for f in files]
    }

    return {
        "count": len(files),
        "backups": [os.path.basename(f) for f in files]
    }

@router.get("/databases")
async def list_databases():
    """List available databases for backup planning"""
    # 1. PG (EXFINOPS) - Always there
    dbs = [{"code": "pg", "name": "EXFINOPS (PostgreSQL)", "host": settings.DB_HOST}]
    
    # 2. Logo - From Config
    logo_config = next((c for c in settings.DB_CONFIGS if c.get("Name") == "LOGO_Database"), None)
    if logo_config:
        dbs.append({
            "code": "mssql", 
            "name": f"LOGO ({logo_config.get('Database')})", 
            "host": logo_config.get("Server")
        })
        
    return dbs

@router.get("/jobs")
async def list_scheduled_jobs():
    """List active backup schedules"""
    return scheduler_service.list_jobs()

@router.post("/jobs")
async def create_schedule(req: ScheduleRequest):
    """Create a daily backup schedule"""
    job_id = scheduler_service.add_backup_job(req.db_type, req.hour, req.minute)
    return {"status": "success", "job_id": job_id, "message": f"Backup scheduled for {req.hour}:{req.minute}"}

@router.delete("/jobs/{job_id}")
async def remove_schedule(job_id: str):
    """Remove a schedule"""
    if scheduler_service.remove_job(job_id):
        return {"status": "success", "message": "Job removed"}
    raise HTTPException(status_code=404, detail="Job not found")

@router.get("/info")
async def system_info():
    """Returns System Version and Status"""
    return {
        "app_name": settings.APP_NAME,
        "version": settings.VERSION,
        "mode": settings.LOGO_INTEGRATION_MODE,
        "backup_path": system_service.backup_dir
    }

class DBConfigRequest(BaseModel):
    db_type: str # mssql, postgres
    host: str
    port: int
    user: str
    password: str
    dbname: str
    name: str = "Database"

@router.post("/configure-db")
async def configure_database(req: DBConfigRequest):
    """
    Updates db_config.json with new credentials.
    """
    import json
    import os
    
    config_path = os.path.join(os.getcwd(), "db_config.json")
    
    # Load existing or create new
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            try:
                configs = json.load(f)
            except:
                configs = [{"Default": "PostgreSQLDatabase"}]
    else:
        configs = [{"Default": "PostgreSQLDatabase"}]
        
    # Construct new config object
    target_type = "MSSQLDatabase" if req.db_type == "mssql" else "PostgreSQLDatabase"
    
    new_entry = {
        "id": "gen_" + str(len(configs)), 
        "type": target_type,
        "Name": "LOGO_Database" if req.db_type == "mssql" else "Main DB",
        "Server": req.host, # Backend uses 'Server' key usually
        "url": req.host,    # Legacy support
        "Port": req.port,
        "Username": req.user,
        "user": req.user,
        "Password": req.password,
        "password": req.password,
        "Database": req.dbname,
        "databaseName": req.dbname
    }
    
    # Remove existing of same type to replace
    configs = [c for c in configs if c.get("type") != target_type and c.get("Type") != target_type]
    configs.append(new_entry)
    
    try:
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(configs, f, indent=4)
        return {"status": "success", "message": "Configuration saved. Please restart the service."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save config: {e}")
@router.get("/postman-collection")
async def download_postman_collection(request: Request):
    """
    **Postman Koleksiyonunu İndir**

    API'nin güncel OpenAPI şemasını (Swagger) JSON formatında indirir.
    Bu dosya Postman'e 'Import' edilerek kullanılabilir.
    """
    import json
    
    openapi_schema = request.app.openapi()
    
    # JSON string oluştur
    content = json.dumps(openapi_schema, ensure_ascii=False, indent=2)
    
    return Response(
        content=content, 
        media_type="application/json", 
        headers={"Content-Disposition": "attachment; filename=exfin_ops_openapi.json"}
    )
