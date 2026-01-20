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
        db_path = os.path.join(os.getcwd(), "exfin.db")
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
                
            interval = data.get("backup_interval", "off") # off, hourly, daily, weekly
            
            if interval == "hourly":
                h_val = 1
                try:
                    h_val = int(data.get("backup_hours", "1"))
                except: h_val = 1
                
                self.scheduler.add_job(
                    self.run_backup_process,
                    'interval',
                    hours=h_val,
                    id=job_id,
                    replace_existing=True,
                    name=f"Hourly Backup (Every {h_val} hours)"
                )
                logger.info(f"Scheduled Hourly Backup (Every {h_val} hours).")
                
            elif interval == "daily":
                # Parse time
                t_str = data.get("backup_time", "23:00")
                try:
                    hour, minute = map(int, t_str.split(':'))
                except:
                    hour, minute = 23, 0

                self.scheduler.add_job(
                    self.run_backup_process,
                    'cron',
                    hour=hour,
                    minute=minute,
                    id=job_id,
                    replace_existing=True,
                    name=f"Daily Backup ({t_str})"
                )
                logger.info(f"Scheduled Daily Backup at {t_str}.")

            elif interval == "weekly":
                # Parse time
                t_str = data.get("backup_time", "23:00")
                try:
                    hour, minute = map(int, t_str.split(':'))
                except:
                    hour, minute = 23, 0
                
                # Parse days
                days = data.get("backup_days", [])
                if not days:
                    days_str = "*" # Every day if empty (fallback)
                else:
                    days_str = ",".join(days)

                self.scheduler.add_job(
                    self.run_backup_process,
                    'cron',
                    hour=hour,
                    minute=minute,
                    day_of_week=days_str,
                    id=job_id,
                    replace_existing=True,
                    name=f"Weekly Backup ({t_str} on {days_str})"
                )
                logger.info(f"Scheduled Weekly Backup at {t_str} on {days_str}.")
                
        except Exception as e:
            logger.error(f"Error refreshing schedule: {e}")

scheduler_service = SchedulerService()
