import gspread
from oauth2client.service_account import ServiceAccountCredentials
from backend.config import settings
import sys

def setup_spreadsheet():
    try:
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            settings.GOOGLE_SERVICE_ACCOUNT_FILE, scope
        )
        client = gspread.authorize(creds)
        
        try:
            spreadsheet = client.open_by_key(settings.GOOGLE_SHEET_ID)
        except Exception:
            print(f"Error: Could not open spreadsheet with ID '{settings.GOOGLE_SHEET_ID}'.")
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
                # Ensure the sheet has exactly the number of columns we expect to prune extras
                worksheet.resize(cols=len(headers))
                # Overwrite first row
                worksheet.update('A1', [headers])
                
        print("\nSpreadsheet Setup completed successfully!")
        
    except Exception as e:
        print(f"An error occurred during setup: {str(e)}")

if __name__ == "__main__":
    if not settings.GOOGLE_SHEET_ID:
        print("Error: GOOGLE_SHEET_ID not set in .env")
        sys.exit(1)
    setup_spreadsheet()
