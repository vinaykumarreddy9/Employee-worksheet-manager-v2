from fastapi import APIRouter, HTTPException, Body, Depends
from backend.services.sheets import SheetManager
from backend.api.deps import get_admin_user
from shared.schemas import SignupStatus, TimesheetStatus
from datetime import datetime
import json

router = APIRouter(prefix="/admin", tags=["Admin"])
sheet_manager = SheetManager()

@router.get("/submissions")
async def admin_get_submissions(_: dict = Depends(get_admin_user)):
    return sheet_manager.get_all_submissions()

@router.post("/timesheets/process")
async def admin_process_timesheet(
    email: str = Body(...),
    week_start: str = Body(...),
    action: str = Body(...),
    admin_email: str = Body(...),
    reason: str = Body(""),
    _: dict = Depends(get_admin_user)
):
    success, message = sheet_manager.process_timesheet_week(email, week_start, action, admin_email, reason)
    if not success:
        raise HTTPException(status_code=400, detail=message)
    return {"message": message}
