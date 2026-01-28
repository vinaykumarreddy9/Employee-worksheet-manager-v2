import sys
import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# Ensure the root directory is in the path so we can import 'backend'
sys.path.append(os.getcwd())

from backend.config import settings

def setup_spreadsheet():
    try:
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]
        
        # Robust Credential Loading (Support JSON string or File)
        if settings.GOOGLE_SERVICE_ACCOUNT_JSON:
            try:
                json_str = settings.GOOGLE_SERVICE_ACCOUNT_JSON.strip()
                if json_str.startswith("'") and json_str.endswith("'"):
                    json_str = json_str[1:-1]
                creds_dict = json.loads(json_str)
                creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
            except Exception as e:
                print(f"Error parsing GOOGLE_SERVICE_ACCOUNT_JSON: {e}")
                sys.exit(1)
        else:
            creds_file = os.path.join(os.getcwd(), "credentials.json")
            if not os.path.exists(creds_file):
                print(f"Error: Neither GOOGLE_SERVICE_ACCOUNT_JSON env var nor {creds_file} found.")
                sys.exit(1)
            creds = ServiceAccountCredentials.from_json_keyfile_name(creds_file, scope)

        client = gspread.authorize(creds)
        
        try:
            spreadsheet = client.open_by_key(settings.GOOGLE_SHEET_ID)
        except Exception as e:
            print(f"Error: Could not open spreadsheet with ID '{settings.GOOGLE_SHEET_ID}'.")
            print(f"Details: {e}")
            print("Make sure you have shared the spreadsheet with the service account email.")
            return

        sheets_to_create = {
            "User Logins": ["email", "password_hash", "role", "status", "full_name", "employee_id", "created_at"],
            "Pending Timesheets": [
                "entry_id", "email", "week_start_date", "date", "hours", 
                "project_name", "task_description", "status", "created_at", "updated_at", "work_type"
            ],
            "Approved Timesheets": [
                "timesheet_id", "email", "week_start_date", "total_hours", 
                "approval_timestamp", "approved_by"
            ],
            "Denied Timesheets": [
                "timesheet_id", "email", "week_start_date", "rejection_reason", 
                "denied_at", "denied_by"
            ]
        }

        existing_sheets = [s.title for s in spreadsheet.worksheets()]
        
        for sheet_name, headers in sheets_to_create.items():
            if sheet_name not in existing_sheets:
                print(f"Creating sheet: {sheet_name}")
                worksheet = spreadsheet.add_worksheet(title=sheet_name, rows="100", cols=len(headers) + 2)
                worksheet.append_row(headers)
            else:
                print(f"Syncing headers for: {sheet_name}")
                worksheet = spreadsheet.worksheet(sheet_name)
                worksheet.resize(cols=len(headers))
                worksheet.update('A1', [headers])
                
        # --- Add Default Admin User if it doesn't exist ---
        login_sheet = spreadsheet.worksheet("User Logins")
        users = login_sheet.get_all_records()
        admin_exists = any(u.get('email') == "admin@company.com" for u in users)
        
        if not admin_exists:
            print("Seeding default Admin user...")
            admin_data = [
                "admin@company.com", 
                "admin123", # Plain text as per project requirements
                "Admin",
                "Active",
                "System Administrator",
                "ADMIN-01",
                datetime.now().isoformat()
            ]
            login_sheet.append_row(admin_data)
            print("Default credentials: admin@company.com / admin123")
        else:
            print("Admin user already exists.")
        
        print("\nSpreadsheet Setup completed successfully!")
        
    except Exception as e:
        print(f"An error occurred during setup: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    if not settings.GOOGLE_SHEET_ID:
        print("Error: GOOGLE_SHEET_ID not set")
        sys.exit(1)
    setup_spreadsheet()
