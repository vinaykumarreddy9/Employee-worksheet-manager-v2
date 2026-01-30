from fastapi import APIRouter, HTTPException, Body
from datetime import datetime
from backend.services.database import DatabaseManager
from backend.core.security import create_access_token
from shared.schemas import UserStatus

router = APIRouter(prefix="/auth", tags=["Authentication"])
db_manager = DatabaseManager()

@router.post("/register")
async def register(
    email: str = Body(...),
    password: str = Body(...),
    role: str = Body(...),
    full_name: str = Body(...),
    employee_id: str = Body(...)
):
    # Check if user already exists
    if db_manager.get_user_by_email(email):
        raise HTTPException(status_code=400, detail="User with this email already exists")
    
    # Check if employee ID exists
    if db_manager.get_user_by_employee_id(employee_id):
        raise HTTPException(status_code=400, detail="Employee ID already registered")

    db_manager.add_user(
        email=email,
        password_hash=password, # As requested: no hashing
        role=role,
        full_name=full_name,
        employee_id=employee_id,
        status=UserStatus.ACTIVE
    )
    
    return {"message": "User registered successfully"}

import logging

logger = logging.getLogger(__name__)

@router.post("/login")
async def login(email: str = Body(...), password: str = Body(...)):
    logger.info(f"Login attempt for: {email}")
    try:
        user = db_manager.get_user_by_email(email)
        
        if not user:
            logger.warning(f"Login failed: User {email} not found")
            raise HTTPException(status_code=401, detail="Invalid credentials")
            
        if user.get("status") != UserStatus.ACTIVE:
            logger.warning(f"Login failed: User {email} is inactive")
            raise HTTPException(status_code=401, detail="Account is inactive")

        # Direct comparison for simplicity (no hashing as per current requirement)
        stored_password = str(user.get("password_hash", ""))
        if str(password) != stored_password:
            logger.warning(f"Login failed: Password mismatch for {email}")
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        logger.info(f"Password verified for {email}. Creating token...")
        
        try:
            token = create_access_token({"sub": user["email"], "role": user["role"]})
            logger.info(f"Token created successfully for {email}")
            return {"status": "success", "access_token": token, "user": user}
        except Exception as jwt_err:
            logger.error(f"JWT Creation Error for {email}: {jwt_err}")
            raise HTTPException(status_code=500, detail="Error generating sequence token")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"UNEXPECTED LOGIN ERROR for {email}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
