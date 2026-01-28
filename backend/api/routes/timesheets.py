from typing import Optional
from backend.utils.helpers import get_current_week_start
from backend.api.deps import get_current_user
from fastapi import APIRouter, HTTPException, Body, Depends
from shared.schemas import TimesheetStatus, TimesheetEntry
from datetime import datetime, timedelta
from backend.services.sheets import SheetManager
import uuid

router = APIRouter(prefix="/timesheets", tags=["Timesheets"])
sheet_manager = SheetManager()

@router.get("/current")
async def get_current_timesheet(email: str, week_start: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    if email != current_user["sub"]:
        raise HTTPException(status_code=403, detail="Forbidden: You can only view your own timesheet")
    
    if not week_start:
        w_start = get_current_week_start()
    else:
        w_start = datetime.strptime(week_start, "%Y-%m-%d").date()
        
    entries = sheet_manager.get_pending_entries(email, w_start.isoformat())
    return {"week_start": w_start.isoformat(), "entries": entries}

@router.post("/entry")
async def save_entry(
    email: str = Body(...),
    date_str: str = Body(...),
    hours: float = Body(...),
    project_name: str = Body(...),
    task_description: str = Body(...),
    work_type: str = Body("Billable"),
    current_user: dict = Depends(get_current_user)
):
    if email != current_user["sub"]:
        raise HTTPException(status_code=403, detail="Forbidden")
    from backend.config import settings
    entry_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    week_start = entry_date - timedelta(days=entry_date.weekday())
    
    if not (week_start <= entry_date <= week_start + timedelta(days=6)):
        raise HTTPException(status_code=400, detail="Date outside current week")
    
    if hours < 0 or hours > settings.MAX_DAILY_HOURS:
        raise HTTPException(status_code=400, detail=f"Invalid hours (0-{settings.MAX_DAILY_HOURS})")
    
    entry = TimesheetEntry(
        entry_id=str(uuid.uuid4()),
        email=email,
        week_start_date=week_start,
        date=entry_date,
        hours=hours,
        project_name=project_name,
        task_description=task_description,
        work_type=work_type,
        status=TimesheetStatus.DRAFT,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    success, message = sheet_manager.save_timesheet_entry(entry)
    if not success:
        raise HTTPException(status_code=400, detail=message)
    return {"message": message}

@router.post("/update")
async def update_entry(
    entry_id: str = Body(...),
    email: str = Body(...),
    hours: float = Body(...),
    project_name: str = Body(...),
    task_description: str = Body(...),
    work_type: str = Body(...),
    current_user: dict = Depends(get_current_user)
):
    if email != current_user["sub"]:
        raise HTTPException(status_code=403, detail="Forbidden")
    
    success, message = sheet_manager.update_timesheet_entry(entry_id, email, hours, project_name, task_description, work_type)
    if not success:
        raise HTTPException(status_code=400, detail=message)
    return {"message": message}

@router.post("/submit")
async def submit_timesheet(email: str = Body(...), week_start: str = Body(...), current_user: dict = Depends(get_current_user)):
    if email != current_user["sub"]:
        raise HTTPException(status_code=403, detail="Forbidden")
    success = sheet_manager.submit_week(email, week_start)
    if not success:
        raise HTTPException(status_code=400, detail="No draft entries found to submit")
    return {"message": "Week submitted successfully"}

@router.post("/delete")
async def delete_entry(
    entry_id: str = Body(..., embed=True),
    email: str = Body(..., embed=True),
    current_user: dict = Depends(get_current_user)
):
    if email != current_user["sub"]:
        raise HTTPException(status_code=403, detail="Forbidden")
    
    success, message = sheet_manager.delete_timesheet_entry(entry_id, email)
    if not success:
        raise HTTPException(status_code=400, detail=message)
    return {"message": message}
