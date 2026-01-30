import sqlalchemy
from sqlalchemy.orm import Session
from sqlalchemy import and_
from backend.database.db_config import SessionLocal, engine
from backend.database import models
from shared.schemas import TimesheetStatus, UserRole
from datetime import datetime
import uuid
import logging
from typing import List, Optional
from backend.services.mail import MailService

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        pass

    def get_db(self):
        return SessionLocal()

    # --- User Logins ---
    def get_user_by_email(self, email: str) -> Optional[dict]:
        db = self.get_db()
        try:
            user = db.query(models.User).filter(models.User.email == email).first()
            if not user: return None
            return {
                "email": user.email,
                "password_hash": user.password_hash,
                "role": user.role,
                "status": user.status,
                "full_name": user.full_name,
                "employee_id": user.employee_id,
                "created_at": user.created_at.isoformat() if user.created_at else None
            }
        finally:
            db.close()

    def get_user_by_employee_id(self, employee_id: str) -> Optional[dict]:
        db = self.get_db()
        try:
            user = db.query(models.User).filter(models.User.employee_id == employee_id).first()
            if not user: return None
            return {
                "email": user.email,
                "password_hash": user.password_hash,
                "role": user.role,
                "status": user.status,
                "full_name": user.full_name,
                "employee_id": user.employee_id,
                "created_at": user.created_at.isoformat() if user.created_at else None
            }
        finally:
            db.close()

    def add_user(self, email: str, password_hash: str, role: str, full_name: str = "", employee_id: str = "", status: str = "Active"):
        db = self.get_db()
        try:
            new_user = models.User(
                email=email,
                password_hash=password_hash,
                role=role,
                status=status,
                full_name=full_name,
                employee_id=employee_id
            )
            db.add(new_user)
            db.commit()
        finally:
            db.close()

    # --- Timesheets ---
    def get_pending_entries(self, email: str, week_start: str) -> List[dict]:
        db = self.get_db()
        try:
            entries = db.query(models.TimesheetEntry).filter(
                and_(
                    models.TimesheetEntry.email == email,
                    models.TimesheetEntry.week_start_date == week_start
                )
            ).all()
            return [
                {
                    "entry_id": e.entry_id,
                    "email": e.email,
                    "week_start_date": e.week_start_date.isoformat(),
                    "date": e.date.isoformat(),
                    "hours": e.hours,
                    "project_name": e.project_name,
                    "task_description": e.task_description,
                    "status": e.status,
                    "created_at": e.created_at.isoformat(),
                    "updated_at": e.updated_at.isoformat(),
                    "work_type": e.work_type
                } for e in entries
            ]
        finally:
            db.close()

    def save_timesheet_entry(self, entry):
        db = self.get_db()
        try:
            # Cumulative validation
            daily_total = db.query(models.TimesheetEntry).filter(
                and_(
                    models.TimesheetEntry.email == entry.email,
                    models.TimesheetEntry.date == entry.date
                )
            ).with_entities(sqlalchemy.func.sum(models.TimesheetEntry.hours)).scalar() or 0.0

            weekly_total = db.query(models.TimesheetEntry).filter(
                and_(
                    models.TimesheetEntry.email == entry.email,
                    models.TimesheetEntry.week_start_date == entry.week_start_date
                )
            ).with_entities(sqlalchemy.func.sum(models.TimesheetEntry.hours)).scalar() or 0.0

            # 1. Daily Limit Check (8.0 hrs)
            if daily_total + entry.hours > 8.0:
                remaining_day = max(0.0, 8.0 - daily_total)
                return False, f"Daily limit exceeded. You have already logged {daily_total} hrs for today. Remaining: {remaining_day} hrs."

            # 2. Weekly Limit Check (40.0 hrs)
            if weekly_total + entry.hours > 40.0:
                remaining_week = max(0.0, 40.0 - weekly_total)
                return False, f"Weekly limit exceeded. You have already logged {weekly_total} hrs this week. Remaining: {remaining_week} hrs. (Target: 40.0 hrs)"

            new_entry = models.TimesheetEntry(
                entry_id=entry.entry_id,
                email=entry.email,
                week_start_date=entry.week_start_date,
                date=entry.date,
                hours=entry.hours,
                project_name=entry.project_name,
                task_description=entry.task_description,
                status=entry.status,
                work_type=entry.work_type
            )
            db.add(new_entry)
            db.commit()
            return True, "Entry logged successfully"
        except Exception as e:
            db.rollback()
            return False, str(e)
        finally:
            db.close()

    def submit_week(self, email: str, week_start: str):
        db = self.get_db()
        try:
            entries = db.query(models.TimesheetEntry).filter(
                and_(
                    models.TimesheetEntry.email == email,
                    models.TimesheetEntry.week_start_date == week_start,
                    models.TimesheetEntry.status.in_([TimesheetStatus.DRAFT, TimesheetStatus.DENIED])
                )
            ).all()
            
            if not entries: return False
            
            for e in entries:
                e.status = TimesheetStatus.SUBMITTED
                e.updated_at = datetime.utcnow()
            
            db.commit()
            return True
        finally:
            db.close()

    def get_all_submissions(self):
        db = self.get_db()
        try:
            submissions = db.query(models.TimesheetEntry).filter(
                models.TimesheetEntry.status == TimesheetStatus.SUBMITTED
            ).all()
            
            result = []
            for s in submissions:
                user = db.query(models.User).filter(models.User.email == s.email).first()
                emp_id = user.employee_id if user else "Unknown"
                result.append({
                    "entry_id": s.entry_id,
                    "email": s.email,
                    "week_start_date": s.week_start_date.isoformat(),
                    "date": s.date.isoformat(),
                    "hours": s.hours,
                    "project_name": s.project_name,
                    "task_description": s.task_description,
                    "status": s.status,
                    "work_type": s.work_type,
                    "employee_id": emp_id
                })
            return result
        finally:
            db.close()

    def process_timesheet_week(self, email: str, week_start: str, action: str, admin_email: str, reason: str = ""):
        db = self.get_db()
        try:
            entries = db.query(models.TimesheetEntry).filter(
                and_(
                    models.TimesheetEntry.email == email,
                    models.TimesheetEntry.week_start_date == week_start
                )
            ).all()
            
            if not entries: return False, "No entries found for this week"
            
            total_hours = sum(e.hours for e in entries)
            ts_id = str(uuid.uuid4())
            new_status = "Approved" if action == "Approve" else "Denied"

            if action == "Approve":
                approved = models.ApprovedTimesheet(
                    timesheet_id=ts_id,
                    email=email,
                    week_start_date=week_start,
                    total_hours=total_hours,
                    approved_by=admin_email
                )
                db.add(approved)
            else:
                denied = models.DeniedTimesheet(
                    timesheet_id=ts_id,
                    email=email,
                    week_start_date=week_start,
                    rejection_reason=reason,
                    denied_by=admin_email
                )
                db.add(denied)

            for e in entries:
                e.status = new_status
                e.updated_at = datetime.utcnow()
            
            db.commit()
            
            try:
                MailService.send_timesheet_status_notification(email, week_start, action, reason)
            except Exception as mail_err:
                logger.error(f"Failed to send status email: {mail_err}")
                
            return True, f"Week {action.lower()}d"
        except Exception as e:
            db.rollback()
            return False, str(e)
        finally:
            db.close()

    def update_timesheet_entry(self, entry_id: str, email: str, hours: float, project_name: str, task_description: str, work_type: str):
        db = self.get_db()
        try:
            entry = db.query(models.TimesheetEntry).filter(models.TimesheetEntry.entry_id == entry_id).first()
            if not entry: return False, "Entry not found"
            
            if entry.email != email: return False, "Forbidden"
            
            if entry.status in ["Submitted", "Approved"]:
                return False, f"Entry is {entry.status} and cannot be modified."
            
            # Cumulative validation for Update
            daily_total = db.query(models.TimesheetEntry).filter(
                and_(
                    models.TimesheetEntry.email == email,
                    models.TimesheetEntry.date == entry.date,
                    models.TimesheetEntry.entry_id != entry_id
                )
            ).with_entities(sqlalchemy.func.sum(models.TimesheetEntry.hours)).scalar() or 0.0

            weekly_total = db.query(models.TimesheetEntry).filter(
                and_(
                    models.TimesheetEntry.email == email,
                    models.TimesheetEntry.week_start_date == entry.week_start_date,
                    models.TimesheetEntry.entry_id != entry_id
                )
            ).with_entities(sqlalchemy.func.sum(models.TimesheetEntry.hours)).scalar() or 0.0

            if daily_total + hours > 8.0:
                remaining_day = max(0.0, 8.0 - daily_total)
                return False, f"Daily limit exceeded. You have already logged {daily_total} hrs for {entry.date}. Remaining: {remaining_day} hrs."

            if weekly_total + hours > 40.0:
                remaining_week = max(0.0, 40.0 - weekly_total)
                return False, f"Weekly limit exceeded. You have already logged {weekly_total} hrs for this week. Remaining: {remaining_week} hrs."

            entry.hours = hours
            entry.project_name = project_name
            entry.task_description = task_description
            entry.work_type = work_type
            entry.updated_at = datetime.utcnow()
            
            db.commit()
            return True, "Entry updated successfully"
        except Exception as e:
            db.rollback()
            return False, str(e)
        finally:
            db.close()

    def delete_timesheet_entry(self, entry_id: str, email: str):
        db = self.get_db()
        try:
            entry = db.query(models.TimesheetEntry).filter(models.TimesheetEntry.entry_id == entry_id).first()
            if not entry: return False, "Entry not found"
            
            if entry.email != email: return False, "Forbidden"
            
            if entry.status in ["Submitted", "Approved"]:
                return False, f"Cannot delete {entry.status} entries."

            db.delete(entry)
            db.commit()
            return True, "Entry deleted"
        except Exception as e:
            db.rollback()
            return False, str(e)
        finally:
            db.close()
