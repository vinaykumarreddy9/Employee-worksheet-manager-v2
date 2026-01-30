# Employee Weekly Timesheet Manager

A professional, streamlined timesheet management system built with Python, FastAPI, Streamlit, and PostgreSQL (Neon). Optimized for speed, reliability, and ease of use.

## Key Features

- **Simplified Authentication**: Direct login with plain-text password comparison (configurable for production) and JWT session security.
- **Live Grid Editing**: A seamless, professional interface for employees to log hours. Changes are auto-synced to the backend.
- **Automated Validation**: Strict enforcement of daily (max 8h) and weekly (max 40h) limits.
- **Correction Workflow**: Admins can "Send Back" timesheets for corrections, unlocking them for employee editing and resubmission.
- **Admin Dashboard**: Centralized review interface for approving or returning timesheets.
- **PostgreSQL Persistence**: All data is stored in a Neon PostgreSQL database for reliable, scalable auditing and reporting.
- **Production Ready**: Optimized for deployment on **Render**.

## Tech Stack

- **Frontend**: Streamlit (Premium Glassmorphism Theme)
- **Backend**: FastAPI
- **Data Store**: PostgreSQL (Neon) using SQLAlchemy
- **Automation**: APScheduler (Sunday 4:00 AM Auto-submission)
- **E2E Testing**: Pytest + HTTPX

## Deployment on Render

This project is optimized for individual service deployment on Render.

### 1. Backend Service (FastAPI)

1. **Source**: Connect your GitHub repo.
2. **Environment**: Python 3.
3. **Build Command**: `pip install -r requirements.txt`
4. **Start Command**: `export PYTHONPATH=$PYTHONPATH:. && gunicorn backend.main:app --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT`
5. **Environment Variables**:
   - `DATABASE_URL`: Your Neon connection string.
   - `SECRET_KEY`: A random secret string.
   - `PYTHON_VERSION`: `3.12.0` (Recommended for stability, also supports 3.13)
   - `SMTP_SERVER`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SYSTEM_EMAIL`: For email notifications.

### 2. Frontend Service (Streamlit)

1. **Source**: Connect your GitHub repo.
2. **Build Command**: `pip install -r requirements.txt`
3. **Start Command**: `streamlit run frontend/app.py --server.port $PORT --server.address 0.0.0.0`
4. **Environment Variables**:
   - `BACKEND_URL`: The URL of your deployed Backend service.
   - `PYTHON_VERSION`: `3.12.0`

## Local Setup

### 1. Environment Setup

1. Clone the repo and install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Create a `.env` file containing your `DATABASE_URL`.

### 2. Run Locally

Use the provided `run.bat` (Windows) or start manually:

```bash
# Backend
uvicorn backend.main:app --reload

# Frontend
streamlit run frontend/app.py
```

_Note: The database tables are automatically created on first run._

## Security & Validation

- **JWT Protection**: All API endpoints (except login) require a valid JWT token.
- **Lockdown Mechanism**: Entries are locked immediately upon submission.
- **Daily/Weekly Limits**: Prevents logging more than 8h/day or 40h/week.
