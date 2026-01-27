# Employee Weekly Timesheet Manager

A professional, streamlined timesheet management system built with Python, FastAPI, Streamlit, and Google Spreadsheets. Optimized for speed, reliability, and ease of use.

## Key Features

- **Simplified Authentication**: Direct login with plain-text password comparison (configurable for production) and JWT session security.
- **Live Grid Editing**: A seamless, "Google Sheets-like" interface for employees to log hours. Changes are auto-synced to the backend.
- **Automated Validation**: Strict enforcement of daily (max 8h) and weekly (max 40h) limits.
- **Correction Workflow**: Admins can "Send Back" timesheets for corrections, unlocking them for employee editing and resubmission.
- **Admin Dashboard**: Centralized review interface for approving or returning timesheets.
- **Google Sheets Integration**: All data is persisted in a Google Spreadsheet for easy auditing and reporting.
- **Production Ready**: Fully configured for deployment on **Render** using Blueprints.

## Tech Stack

- **Frontend**: Streamlit (Premium Glassmorphism Theme)
- **Backend**: FastAPI
- **Data Store**: Google Spreadsheets (using `gspread`)
- **Automation**: APScheduler (Sunday 4:00 AM Auto-submission)
- **E2E Testing**: Pytest + HTTPX

## Deployment on Render

This project is ready for deployment on [Render](https://render.com/) using the provided `render.yaml`.

### 1. Preparation

1. Create a Google Service Account and download the JSON credentials.
2. Create a Google Spreadsheet and share it with the service account email.
3. Convert your Service Account JSON into a single-line string.

### 2. Launch

1. Connect your GitHub repository to Render.
2. Render will automatically detect the `render.yaml` and create two services:
   - `timesheet-backend` (FastAPI)
   - `timesheet-frontend` (Streamlit)
3. Configure the following **Environment Variables** in the Render Dashboard:
   - `GOOGLE_SHEET_ID`: Your Spreadsheet ID.
   - `GOOGLE_SERVICE_ACCOUNT_JSON`: The contents of your service account JSON file.
   - `SMTP_USER` & `SMTP_PASSWORD`: For email notifications.
   - `SYSTEM_EMAIL`: Sender email address.

## Local Setup

### 1. Environment Setup

1. Clone the repo and install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Create a `.env` file based on `.env.example`.

### 2. Initialize Spreadsheet

```bash
$env:PYTHONPATH="."
python backend/setup_sheets.py
```

### 3. Run Locally

You can use the provided `run.bat` (Windows) or start manually:

```bash
# Backend
uvicorn backend.main:app --reload

# Frontend
streamlit run frontend/app.py
```

## Security & Validation

- **JWT Protection**: All API endpoints (except login) require a valid JWT token.
- **Lockdown Mechanism**: Entries are locked immediately upon submission.
- **Daily/Weekly Limits**: Prevents logging more than 8h/day or 40h/week.
