from sqlalchemy import select, update, delete, and_, func
from backend.database.db_config import AsyncSessionLocal
from backend.database import models
from shared.schemas import TimesheetStatus, UserRole
from datetime import datetime
import uuid
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        pass

    # --- User Logins ---
    async def get_user_by_email(self, email: str) -> Optional[dict]:
        async with AsyncSessionLocal() as db:
            try:
                stmt = select(models.User).filter(models.User.email == email)
                result = await db.execute(stmt)
                user = result.scalar_one_or_none()
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
                await db.close()

    async def get_user_by_employee_id(self, employee_id: str) -> Optional[dict]:
        async with AsyncSessionLocal() as db:
            try:
                stmt = select(models.User).filter(models.User.employee_id == employee_id)
                result = await db.execute(stmt)
                user = result.scalar_one_or_none()
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
                await db.close()

    async def add_user(self, email: str, password_hash: str, role: str, full_name: str = "", employee_id: str = "", status: str = "Active"):
        async with AsyncSessionLocal() as db:
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
                await db.commit()
            except Exception as e:
                await db.rollback()
                raise e
            finally:
                await db.close()

    # --- Timesheets ---
    async def get_pending_entries(self, email: str, week_start: str) -> List[dict]:
        from datetime import date
        if isinstance(week_start, str):
            week_start = date.fromisoformat(week_start)
            
        async with AsyncSessionLocal() as db:
            try:
                stmt = select(models.TimesheetEntry).filter(
                    and_(
                        models.TimesheetEntry.email == email,
                        models.TimesheetEntry.week_start_date == week_start
                    )
                )
                result = await db.execute(stmt)
                entries = result.scalars().all()
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
                await db.close()

    async def save_timesheet_entry(self, entry):
        async with AsyncSessionLocal() as db:
            try:
                # Cumulative validation
                daily_stmt = select(func.sum(models.TimesheetEntry.hours)).filter(
                    and_(
                        models.TimesheetEntry.email == entry.email,
                        models.TimesheetEntry.date == entry.date
                    )
                )
                daily_result = await db.execute(daily_stmt)
                daily_total = daily_result.scalar() or 0.0

                weekly_stmt = select(func.sum(models.TimesheetEntry.hours)).filter(
                    and_(
                        models.TimesheetEntry.email == entry.email,
                        models.TimesheetEntry.week_start_date == entry.week_start_date
                    )
                )
                weekly_result = await db.execute(weekly_stmt)
                weekly_total = weekly_result.scalar() or 0.0

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
                await db.commit()
                return True, "Entry logged successfully"
            except Exception as e:
                await db.rollback()
                return False, str(e)
            finally:
                await db.close()

    async def submit_week(self, email: str, week_start: str):
        from datetime import date
        if isinstance(week_start, str):
            week_start = date.fromisoformat(week_start)

        async with AsyncSessionLocal() as db:
            try:
                stmt = select(models.TimesheetEntry).filter(
                    and_(
                        models.TimesheetEntry.email == email,
                        models.TimesheetEntry.week_start_date == week_start,
                        models.TimesheetEntry.status.in_([TimesheetStatus.DRAFT, TimesheetStatus.DENIED])
                    )
                )
                result = await db.execute(stmt)
                entries = result.scalars().all()
                
                if not entries: return False
                
                for e in entries:
                    e.status = TimesheetStatus.SUBMITTED
                    e.updated_at = datetime.utcnow()
                
                await db.commit()
                return True
            except Exception:
                await db.rollback()
                return False
            finally:
                await db.close()

    async def get_all_submissions(self):
        async with AsyncSessionLocal() as db:
            try:
                # Optimized Join to avoid N+1 queries
                stmt = select(
                    models.TimesheetEntry, 
                    models.User.employee_id
                ).outerjoin(
                    models.User, 
                    models.TimesheetEntry.email == models.User.email
                ).filter(
                    models.TimesheetEntry.status == TimesheetStatus.SUBMITTED
                )
                
                result = await db.execute(stmt)
                rows = result.all()
                
                result_list = []
                for entry, emp_id in rows:
                    result_list.append({
                        "entry_id": entry.entry_id,
                        "email": entry.email,
                        "week_start_date": entry.week_start_date.isoformat(),
                        "date": entry.date.isoformat(),
                        "hours": entry.hours,
                        "project_name": entry.project_name,
                        "task_description": entry.task_description,
                        "status": entry.status,
                        "work_type": entry.work_type,
                        "employee_id": emp_id or "Unknown"
                    })
                return result_list
            finally:
                await db.close()

    async def process_timesheet_week(self, email: str, week_start: str, action: str, admin_email: str, reason: str = ""):
        from datetime import date
        if isinstance(week_start, str):
            week_start = date.fromisoformat(week_start)

        async with AsyncSessionLocal() as db:
            try:
                stmt = select(models.TimesheetEntry).filter(
                    and_(
                        models.TimesheetEntry.email == email,
                        models.TimesheetEntry.week_start_date == week_start
                    )
                )
                res = await db.execute(stmt)
                entries = res.scalars().all()
                
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
                
                await db.commit()
                return True, f"Week {action.lower()}d"
            except Exception as e:
                await db.rollback()
                return False, str(e)
            finally:
                await db.close()

    async def update_timesheet_entry(self, entry_id: str, email: str, hours: float, project_name: str, task_description: str, work_type: str):
        async with AsyncSessionLocal() as db:
            try:
                stmt = select(models.TimesheetEntry).filter(models.TimesheetEntry.entry_id == entry_id)
                res = await db.execute(stmt)
                entry = res.scalar_one_or_none()
                if not entry: return False, "Entry not found"
                
                if entry.email != email: return False, "Forbidden"
                
                if entry.status in ["Submitted", "Approved"]:
                    return False, f"Entry is {entry.status} and cannot be modified."
                
                # Cumulative validation for Update
                daily_stmt = select(func.sum(models.TimesheetEntry.hours)).filter(
                    and_(
                        models.TimesheetEntry.email == email,
                        models.TimesheetEntry.date == entry.date,
                        models.TimesheetEntry.entry_id != entry_id
                    )
                )
                daily_res = await db.execute(daily_stmt)
                daily_total = daily_res.scalar() or 0.0

                weekly_stmt = select(func.sum(models.TimesheetEntry.hours)).filter(
                    and_(
                        models.TimesheetEntry.email == email,
                        models.TimesheetEntry.week_start_date == entry.week_start_date,
                        models.TimesheetEntry.entry_id != entry_id
                    )
                )
                weekly_res = await db.execute(weekly_stmt)
                weekly_total = weekly_res.scalar() or 0.0

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
                
                await db.commit()
                return True, "Entry updated successfully"
            except Exception as e:
                await db.rollback()
                return False, str(e)
            finally:
                await db.close()

    async def delete_timesheet_entry(self, entry_id: str, email: str):
        async with AsyncSessionLocal() as db:
            try:
                stmt = select(models.TimesheetEntry).filter(models.TimesheetEntry.entry_id == entry_id)
                res = await db.execute(stmt)
                entry = res.scalar_one_or_none()
                if not entry: return False, "Entry not found"
                
                if entry.email != email: return False, "Forbidden"
                
                if entry.status in ["Submitted", "Approved"]:
                    return False, f"Cannot delete {entry.status} entries."

                await db.delete(entry)
                await db.commit()
                return True, "Entry deleted"
            except Exception as e:
                await db.rollback()
                return False, str(e)
            finally:
                await db.close()
