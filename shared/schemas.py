from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime, date
from enum import Enum

class UserRole(str, Enum):
    ADMIN = "Admin"
    EMPLOYEE = "Employee"

class UserStatus(str, Enum):
    ACTIVE = "Active"
    INACTIVE = "Inactive"

class SignupStatus(str, Enum):
    PENDING = "Pending"
    APPROVED = "Approved"
    REJECTED = "Rejected"

class TimesheetStatus(str, Enum):
    DRAFT = "Draft"
    SUBMITTED = "Submitted"
    APPROVED = "Approved"
    DENIED = "Denied"

class WorkType(str, Enum):
    REGULAR = "Billable"
    HOLIDAY = "Holiday"

class User(BaseModel):
    email: EmailStr
    password_hash: str
    role: UserRole
    status: UserStatus
    full_name: str
    employee_id: str
    created_at: datetime

class SignupRequest(BaseModel):
    email: EmailStr
    otp_verified: bool = False
    status: SignupStatus = SignupStatus.PENDING
    rejection_reason: Optional[str] = None
    created_at: datetime

class OTPLog(BaseModel):
    email: EmailStr
    otp_code: str
    purpose: str # Signup, Recovery
    expires_at: datetime
    used: bool = False
    attempts: int = 0
    created_at: datetime

class TimesheetEntry(BaseModel):
    entry_id: str
    email: EmailStr
    week_start_date: date # Sunday
    date: date
    hours: float
    project_name: str
    task_description: str
    work_type: WorkType = WorkType.REGULAR
    status: TimesheetStatus = TimesheetStatus.DRAFT
    created_at: datetime
    updated_at: datetime

class WeeklyTimesheetSummary(BaseModel):
    timesheet_id: str
    email: EmailStr
    week_start_date: date
    total_hours: float
    approval_timestamp: Optional[datetime] = None
    approved_by: Optional[EmailStr] = None

class DeniedTimesheet(BaseModel):
    timesheet_id: str
    email: EmailStr
    week_start_date: date
    rejection_reason: str
    denied_at: datetime
    denied_by: EmailStr

class AuditLog(BaseModel):
    log_id: str
    admin_email: EmailStr
    timestamp: datetime
    action: str
    target_id: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    reason: Optional[str] = None
