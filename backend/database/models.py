from sqlalchemy import Column, String, Float, DateTime, Date, Enum as SQLEnum, ForeignKey
from .db_config import Base
from shared.schemas import UserRole, UserStatus, TimesheetStatus, WorkType
import datetime

class User(Base):
    __tablename__ = "users"
    email = Column(String, primary_key=True, index=True)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="Employee") # Admin, Employee
    status = Column(String, default="Active") # Active, Inactive
    full_name = Column(String)
    employee_id = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class TimesheetEntry(Base):
    __tablename__ = "timesheet_entries"
    entry_id = Column(String, primary_key=True, index=True)
    email = Column(String, ForeignKey("users.email"), index=True)
    week_start_date = Column(Date, index=True)
    date = Column(Date, index=True)
    hours = Column(Float)
    project_name = Column(String)
    task_description = Column(String)
    work_type = Column(String, default="Billable") # Billable, Holiday
    status = Column(String, default="Draft") # Draft, Submitted, Approved, Denied
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class ApprovedTimesheet(Base):
    __tablename__ = "approved_timesheets"
    timesheet_id = Column(String, primary_key=True)
    email = Column(String, ForeignKey("users.email"))
    week_start_date = Column(Date)
    total_hours = Column(Float)
    approved_at = Column(DateTime, default=datetime.datetime.utcnow)
    approved_by = Column(String)

class DeniedTimesheet(Base):
    __tablename__ = "denied_timesheets"
    timesheet_id = Column(String, primary_key=True)
    email = Column(String, ForeignKey("users.email"))
    week_start_date = Column(Date)
    rejection_reason = Column(String)
    denied_at = Column(DateTime, default=datetime.datetime.utcnow)
    denied_by = Column(String)
