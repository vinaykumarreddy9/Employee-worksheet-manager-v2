from apscheduler.schedulers.background import BackgroundScheduler
from backend.services.sheets import SheetManager
from backend.utils.helpers import get_current_week_start
from shared.schemas import TimesheetStatus
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

def auto_submit_task():
    logger.info("Running weekly auto-submit job...")
    sheet_manager = SheetManager()
    try:
        last_week_start = get_current_week_start() - timedelta(days=7)
        sheet = sheet_manager.get_worksheet("pending")
        records = sheet.get_all_records()
        for idx, r in enumerate(records):
            if r["status"] == TimesheetStatus.DRAFT and r["week_start_date"] == last_week_start.isoformat():
                sheet.update_cell(idx + 2, 8, TimesheetStatus.SUBMITTED)
                sheet.update_cell(idx + 2, 10, datetime.now().isoformat())
                logger.info(f"Auto-submitted entry {r['entry_id']} for {r['email']}")
        logger.info("Auto-submit job completed.")
    except Exception as e:
        logger.error(f"Auto-submit job failed: {e}")

def start_scheduler():
    scheduler = BackgroundScheduler()
    # Sunday at 4:00 AM UTC
    scheduler.add_job(auto_submit_task, 'cron', day_of_week='sun', hour=4, minute=0)
    scheduler.start()
    logger.info("Background scheduler started (Sunday 4:00 AM auto-submit).")
