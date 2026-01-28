import gspread
import os
from oauth2client.service_account import ServiceAccountCredentials
from backend.config import settings
from shared.schemas import (
    UserRole, UserStatus, TimesheetStatus,
    User, TimesheetEntry,
    WeeklyTimesheetSummary
)
from datetime import datetime, date
import json
import uuid
import logging
from typing import List, Optional
from backend.services.mail import MailService

logger = logging.getLogger(__name__)

class SheetManager:
    def __init__(self):
        self.scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]
        self._client = None
        self._spreadsheet = None
        self.SHEETS = {
            "logins": "User Logins",
            "pending": "Pending Timesheets",
            "approved": "Approved Timesheets",
            "denied": "Denied Timesheets"
        }

    @property
    def client(self):
        if self._client is None:
            if settings.GOOGLE_SERVICE_ACCOUNT_JSON:
                try:
                    # Strip any potential wrapping quotes or white space
                    json_str = settings.GOOGLE_SERVICE_ACCOUNT_JSON.strip()
                    if json_str.startswith("'") and json_str.endswith("'"):
                        json_str = json_str[1:-1]
                    
                    creds_dict = json.loads(json_str)
                    self.creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, self.scope)
                except Exception as e:
                    logger.error(f"CRITICAL: Failed to parse GOOGLE_SERVICE_ACCOUNT_JSON. Error: {e}")
                    raise RuntimeError(f"JSON Parsing Error for Service Account: {e}")
            else:
                self.creds = ServiceAccountCredentials.from_json_keyfile_name(
                    os.path.join(os.getcwd(), "credentials.json"), self.scope
                )
            self._client = gspread.authorize(self.creds)
        return self._client

    @property
    def spreadsheet(self):
        if self._spreadsheet is None:
            try:
                self._spreadsheet = self.client.open_by_key(settings.GOOGLE_SHEET_ID)
            except Exception as e:
                # Log or re-raise with context
                raise RuntimeError(f"Failed to connect to Google Sheets: {e}")
        return self._spreadsheet

    def get_worksheet(self, name):
        return self.spreadsheet.worksheet(self.SHEETS[name])

    # --- User Logins ---
    def get_user_by_email(self, email: str) -> Optional[dict]:
        sheet = self.get_worksheet("logins")
        cell = sheet.find(email, in_column=1)
        if not cell:
            return None
        try:
            row_data = sheet.row_values(cell.row)
            return {
                "email": row_data[0],
                "password_hash": row_data[1],
                "role": row_data[2],
                "status": row_data[3],
                "full_name": row_data[4] if len(row_data) > 4 else "",
                "employee_id": row_data[5] if len(row_data) > 5 else "",
                "created_at": row_data[6] if len(row_data) > 6 else None
            }
        except IndexError:
            return None

    def get_user_by_employee_id(self, employee_id: str) -> Optional[dict]:
        sheet = self.get_worksheet("logins")
        try:
            cell = sheet.find(employee_id, in_column=6) # Employee ID is in column 6
            if not cell:
                return None
            row_data = sheet.row_values(cell.row)
            return {
                "email": row_data[0],
                "password_hash": row_data[1],
                "role": row_data[2],
                "status": row_data[3],
                "full_name": row_data[4] if len(row_data) > 4 else "",
                "employee_id": row_data[5] if len(row_data) > 5 else "",
                "created_at": row_data[6] if len(row_data) > 6 else None
            }
        except Exception:
            return None

    def add_user(self, email: str, password_hash: str, role: str, full_name: str = "", employee_id: str = "", status: str = "Active"):
        sheet = self.get_worksheet("logins")
        sheet.append_row([
            email, password_hash, role, status, full_name, employee_id, datetime.now().isoformat()
        ])

    # --- Timesheets ---
    def get_pending_entries(self, email: str, week_start: str) -> List[dict]:
        sheet = self.get_worksheet("pending")
        all_records = sheet.get_all_records()
        return [r for r in all_records if r["email"] == email and r["week_start_date"] == week_start]

    def save_timesheet_entry(self, entry: TimesheetEntry):
        sheet = self.get_worksheet("pending")
        try:
            records = sheet.get_all_records()
            
            # Cumulative validation
            daily_total = 0.0
            weekly_total = 0.0
            
            logger.info(f"Validating entry for {entry.email} on {entry.date} (Week: {entry.week_start_date})")
            
            for r in records:
                if r["email"] == entry.email:
                    # Sum for the same week
                    if r["week_start_date"] == entry.week_start_date.isoformat():
                        try:
                            h = float(r["hours"]) if r["hours"] else 0.0
                            weekly_total += h
                            # Sum for the same day
                            if r["date"] == entry.date.isoformat():
                                daily_total += h
                        except ValueError:
                            continue # Skip malformed rows
            
            logger.info(f"Current Cumulative: Daily={daily_total}, Weekly={weekly_total} | Adding={entry.hours}")
            
            # 1. Daily Limit Check (8.0 hrs)
            if daily_total + entry.hours > 8.0:
                remaining_day = max(0.0, 8.0 - daily_total)
                logger.warning(f"Daily Limit Reached for {entry.email}")
                return False, f"Daily limit exceeded. You have already logged {daily_total} hrs for today. Remaining: {remaining_day} hrs."

            # 2. Weekly Limit Check (40.0 hrs)
            if weekly_total + entry.hours > 40.0:
                remaining_week = max(0.0, 40.0 - weekly_total)
                logger.warning(f"Weekly Limit Reached for {entry.email}")
                return False, f"Weekly limit exceeded. You have already logged {weekly_total} hrs this week. Remaining: {remaining_week} hrs. (Target: 40.0 hrs)"

            row_data = [
                entry.entry_id, entry.email, entry.week_start_date.isoformat(),
                entry.date.isoformat(), entry.hours, 
                entry.project_name, entry.task_description, entry.status, 
                entry.created_at.isoformat(), entry.updated_at.isoformat(),
                entry.work_type
            ]

            # ALWAYS APPEND for event-based logging
            sheet.append_row(row_data)
            
            return True, "Entry logged successfully"
        except Exception as e:
            return False, str(e)

    def submit_week(self, email: str, week_start: str):
        sheet = self.get_worksheet("pending")
        records = sheet.get_all_records()
        updated = False
        for idx, r in enumerate(records):
            # Allow re-submission of both Drafts and Denied entries
            if r["email"] == email and r["week_start_date"] == week_start and r["status"] in [TimesheetStatus.DRAFT, TimesheetStatus.DENIED]:
                sheet.update_cell(idx + 2, 8, TimesheetStatus.SUBMITTED)
                sheet.update_cell(idx + 2, 10, datetime.now().isoformat())
                updated = True
        return updated

    def get_all_submissions(self):
        sheet = self.get_worksheet("pending")
        records = sheet.get_all_records()
        submissions = [r for r in records if r["status"] == TimesheetStatus.SUBMITTED]
        
        # Enrich with employee_id
        try:
            user_sheet = self.get_worksheet("logins")
            users = user_sheet.get_all_records()
            email_to_id = {u['email']: u.get('employee_id', 'Unknown') for u in users}
            for s in submissions:
                s['employee_id'] = email_to_id.get(s['email'], 'Unknown')
        except Exception as e:
            logger.error(f"Error enriching submissions: {e}")
            
        return submissions

    def process_timesheet_week(self, email: str, week_start: str, action: str, admin_email: str, reason: str = ""):
        try:
            pending_sheet = self.get_worksheet("pending")
            records = pending_sheet.get_all_records()
            
            # Find all matching rows
            # Index 0 in records is row 2 in sheet
            row_indices = [idx + 2 for idx, r in enumerate(records) 
                          if r["email"] == email and r["week_start_date"] == week_start]
            
            if not row_indices:
                return False, "No entries found for this week"
            
            week_entries = [r for r in records if r["email"] == email and r["week_start_date"] == week_start]
            total_hours = sum(float(r["hours"]) for r in week_entries)
            ts_id = str(uuid.uuid4())

            if action == "Approve":
                approved_sheet = self.get_worksheet("approved")
                approved_sheet.append_row([
                    ts_id, email, week_start, total_hours, 
                    datetime.now().isoformat(), admin_email
                ])
                new_status = "Approved"
            else:
                denied_sheet = self.get_worksheet("denied")
                denied_sheet.append_row([
                    ts_id, email, week_start, reason, 
                    datetime.now().isoformat(), admin_email
                ])
                new_status = "Denied"

            # Update all matching rows in pending
            for row_num in row_indices:
                pending_sheet.update_cell(row_num, 8, new_status)
            
            # ✉️ Send notification email to employee (non-blocking failure)
            try:
                MailService.send_timesheet_status_notification(email, week_start, action, reason)
            except Exception as mail_err:
                logger.error(f"Failed to send status email: {mail_err}")
            
            return True, f"Week {action.lower()}d"
        except Exception as e:
            logger.error(f"Error processing timesheet week: {e}")
            return False, f"Internal error: {str(e)}"

    # --- Timesheet Management ---
    def update_timesheet_entry(self, entry_id: str, email: str, hours: float, project_name: str, task_description: str, work_type: str):
        sheet = self.get_worksheet("pending")
        try:
            records = sheet.get_all_records()
            cell = sheet.find(entry_id, in_column=1)
            if not cell:
                return False, "Entry not found"
            
            row_idx = cell.row
            old_row_data = sheet.row_values(row_idx)
            
            # Security check: ensure email matches
            if old_row_data[1] != email:
                return False, "Process error: entry does not belong to user"

            target_date = old_row_data[3]
            week_start = old_row_data[2]
            current_status = old_row_data[7] # Column 8

            # Lockdown check (Cannot edit Submitted or Approved entries)
            if current_status in ["Submitted", "Approved"]:
                return False, f"Entry is {current_status} and cannot be modified."
            
            # Cumulative validation for Update
            daily_total = 0.0
            weekly_total = 0.0
            for r in records:
                # Sum hours for the same user and date/week, but exclude the entry we are currently updating
                if r["email"] == email and r["entry_id"] != entry_id:
                    if r["week_start_date"] == week_start:
                        try:
                            h = float(r["hours"]) if r["hours"] else 0.0
                            weekly_total += h
                            if r["date"] == target_date:
                                daily_total += h
                        except ValueError:
                            continue

            # 1. Daily Limit Check (8.0 hrs)
            if daily_total + hours > 8.0:
                remaining_day = max(0.0, 8.0 - daily_total)
                return False, f"Daily limit exceeded. You have already logged {daily_total} hrs for {target_date}. Remaining: {remaining_day} hrs."

            # 2. Weekly Limit Check (40.0 hrs)
            if weekly_total + hours > 40.0:
                remaining_week = max(0.0, 40.0 - weekly_total)
                return False, f"Weekly limit exceeded. You have already logged {weekly_total} hrs for this week. Remaining: {remaining_week} hrs."

            # Update cells
            # columns: entry_id(1), email(2), week_start(3), date(4), hours(5), proj(6), task(7), status(8), created(9), updated(10), work_type(11)
            sheet.update_cell(row_idx, 5, hours)
            sheet.update_cell(row_idx, 6, project_name)
            sheet.update_cell(row_idx, 7, task_description)
            sheet.update_cell(row_idx, 10, datetime.now().isoformat())
            sheet.update_cell(row_idx, 11, work_type)
            
            return True, "Entry updated successfully"
        except Exception as e:
            return False, str(e)

    def delete_timesheet_entry(self, entry_id: str, email: str):
        sheet = self.get_worksheet("pending")
        try:
            cell = sheet.find(entry_id, in_column=1)
            if not cell:
                return False, "Entry not found"
            
            row_idx = cell.row
            row_data = sheet.row_values(row_idx)
            
            if row_data[1] != email:
                return False, "Forbidden"

            current_status = row_data[7]
            if current_status in ["Submitted", "Approved"]:
                return False, f"Cannot delete {current_status} entries."

            sheet.delete_rows(row_idx)
            return True, "Entry deleted"
        except Exception as e:
            return False, str(e)

