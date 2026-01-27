from fastapi import APIRouter, HTTPException, Body
from datetime import datetime
from backend.services.sheets import SheetManager
from backend.core.security import create_access_token
from shared.schemas import UserStatus

router = APIRouter(prefix="/auth", tags=["Authentication"])
sheet_manager = SheetManager()

@router.post("/register")
async def register(
    email: str = Body(...),
    password: str = Body(...),
    role: str = Body(...),
    full_name: str = Body(...),
    employee_id: str = Body(...)
):
    # Check if user already exists
    if sheet_manager.get_user_by_email(email):
        raise HTTPException(status_code=400, detail="User with this email already exists")
    
    # Check if employee ID exists
    if sheet_manager.get_user_by_employee_id(employee_id):
        raise HTTPException(status_code=400, detail="Employee ID already registered")

    sheet_manager.add_user(
        email=email,
        password_hash=password, # As requested: no hashing
        role=role,
        full_name=full_name,
        employee_id=employee_id,
        status=UserStatus.ACTIVE
    )
    
    return {"message": "User registered successfully"}

@router.post("/login")
async def login(email: str = Body(...), password: str = Body(...)):
    user = sheet_manager.get_user_by_email(email)
    
    # Direct comparison for simplicity as requested
    if not user or user["status"] != UserStatus.ACTIVE or password != user["password_hash"]:
        raise HTTPException(status_code=401, detail="Invalid credentials or inactive account")
    
    token = create_access_token({"sub": user["email"], "role": user["role"]})
    return {"status": "success", "access_token": token, "user": user}
