from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor
from loguru import logger
import os
from datetime import datetime
from .system_service import system_service

class SchedulerService:
    def __init__(self):
        # Persistence: Use local SQLite for jobs
        db_path = os.path.join(os.getcwd(), "scheduler.db")
        jobstores = {
            'default': SQLAlchemyJobStore(url=f'sqlite:///{db_path}')
        }
        executors = {
            'default': ThreadPoolExecutor(20)
        }
        job_defaults = {
            'coalesce': False,
            'max_instances': 1
        }
        
        self.scheduler = BackgroundScheduler(jobstores=jobstores, executors=executors, job_defaults=job_defaults)
        
    def start(self):
        """Starts the scheduler"""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Backup Scheduler Started")
            
    def shutdown(self):
        """Stops the scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Backup Scheduler Stopped")

    def list_jobs(self):
        """Returns list of active jobs"""
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger)
            })
        return jobs

    def add_backup_job(self, db_type: str, hour: int, minute: int):
        """Adds a daily backup job"""
        job_id = f"backup_{db_type}_{hour:02d}{minute:02d}"
        
        # Determine target function
        func = system_service.backup_database_pg if db_type == 'pg' else system_service.backup_database_mssql
        name = f"Daily Backup ({db_type.upper()})"
        
        # Replace existing if any
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)
            
        self.scheduler.add_job(
            func,
            'cron',
            hour=hour,
            minute=minute,
            id=job_id,
            name=name,
            replace_existing=True
        )
        logger.info(f"Scheduled job added: {job_id} at {hour}:{minute}")
        return job_id

    def remove_job(self, job_id: str):
        """Removes a job by ID"""
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)
            logger.info(f"Job removed: {job_id}")
            return True
        return False

scheduler_service = SchedulerService()
