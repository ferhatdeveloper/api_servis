from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor
from loguru import logger
import os
import json
import subprocess
import sys

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
        """Starts the scheduler and loads jobs"""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Scheduler Started")
            self.refresh_backup_schedule()
            
    def shutdown(self):
        """Stops the scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Scheduler Stopped")

    def run_backup_process(self):
        """Executes the backup script"""
        try:
            logger.info("Executing Scheduled Backup...")
            # Find the script
            base_dir = os.getcwd() # Should be backend root
            script_path = os.path.join(base_dir, "scripts", "backup_db.py")
            
            # Use current python executable
            python_exe = sys.executable
            
            subprocess.run([python_exe, script_path], check=True)
            logger.info("Backup Completed Successfully.")
        except Exception as e:
            logger.error(f"Backup job failed: {e}")

    def refresh_backup_schedule(self):
        """Reads config and updates schedule"""
        try:
            # 1. Clear existing backup jobs
            job_id = "auto_backup_job"
            if self.scheduler.get_job(job_id):
                self.scheduler.remove_job(job_id)
                logger.info("Removed existing backup job.")

            # 2. Read Config
            base_dir = os.getcwd()
            config_path = os.path.join(base_dir, "backup_config.json")
            if not os.path.exists(config_path):
                return

            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            interval = data.get("backup_interval", "off") # off, hourly, daily
            
            if interval == "hourly":
                self.scheduler.add_job(
                    self.run_backup_process,
                    'interval',
                    hours=1,
                    id=job_id,
                    replace_existing=True,
                    name="Hourly Backup"
                )
                logger.info("Scheduled Hourly Backup.")
                
            elif interval == "daily":
                self.scheduler.add_job(
                    self.run_backup_process,
                    'cron',
                    hour=23, # Default to 11 PM
                    minute=0,
                    id=job_id,
                    replace_existing=True,
                    name="Daily Backup (23:00)"
                )
                logger.info("Scheduled Daily Backup at 23:00.")
                
        except Exception as e:
            logger.error(f"Error refreshing schedule: {e}")

scheduler_service = SchedulerService()
