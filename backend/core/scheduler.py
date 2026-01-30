from apscheduler.schedulers.background import BackgroundScheduler
from backend.services.database import DatabaseManager
from backend.database.db_config import SessionLocal
from backend.database import models
from backend.utils.helpers import get_current_week_start
from shared.schemas import TimesheetStatus
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

def auto_submit_task():
    logger.info("Running weekly auto-submit job...")
    db_manager = DatabaseManager()
    db = SessionLocal()
    try:
        last_week_start = get_current_week_start() - timedelta(days=7)
        entries = db.query(models.TimesheetEntry).filter(
            models.TimesheetEntry.status == TimesheetStatus.DRAFT,
            models.TimesheetEntry.week_start_date == last_week_start
        ).all()
        
        for e in entries:
            e.status = TimesheetStatus.SUBMITTED
            e.updated_at = datetime.utcnow()
            logger.info(f"Auto-submitted entry {e.entry_id} for {e.email}")
        
        db.commit()
        logger.info("Auto-submit job completed.")
    except Exception as e:
        db.rollback()
        logger.error(f"Auto-submit job failed: {e}")
    finally:
        db.close()

def start_scheduler():
    scheduler = BackgroundScheduler()
    # Sunday at 4:00 AM UTC
    scheduler.add_job(auto_submit_task, 'cron', day_of_week='sun', hour=4, minute=0)
    scheduler.start()
    logger.info("Background scheduler started (Sunday 4:00 AM auto-submit).")
