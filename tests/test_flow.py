import pytest
import httpx
import uuid
import time
from datetime import date, timedelta, datetime
from backend.services.sheets import SheetManager
from backend.utils.helpers import get_available_weeks

# Configuration
test_email = f"e2e_{uuid.uuid4().hex[:6]}@example.com"
test_password = "TestPassword123"

@pytest.mark.asyncio
async def test_full_system_flow():
    sheet_manager = SheetManager()
    base_url = "http://localhost:8000"
    
    # 1. Manual Setup: Inject User (Since signup is removed)
    print(f"\n[1/7] Injecting test user: {test_email}")
    sheet_manager.add_user(
        email=test_email,
        password_hash=test_password, # Now plain text as per requirements
        role="Employee",
        full_name="E2E Test User",
        employee_id=f"T-{uuid.uuid4().hex[:4]}",
        status="Active"
    )

    async with httpx.AsyncClient(base_url=base_url, timeout=60.0) as ac:
        # 2. Login
        print("[2/7] Logging in (Plain Text Auth)...")
        resp = await ac.post("/auth/login", json={"email": test_email, "password": test_password})
        assert resp.status_code == 200, f"Login failed: {resp.text}"
        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("Login Successful.")

        # 3. Create First Entry
        available_weeks = get_available_weeks()
        target_week = available_weeks[0] # Last week
        target_date = target_week + timedelta(days=0) # Monday
        
        print(f"[3/7] Creating Regular Entry for {target_date}...")
        resp = await ac.post("/timesheets/entry", json={
            "email": test_email,
            "date_str": target_date.isoformat(),
            "hours": 5.0,
            "project_name": "E2E Project",
            "task_description": "Initial Task",
            "work_type": "Billable"
        }, headers=headers)
        assert resp.status_code == 200, f"Entry creation failed: {resp.text}"

        # 4. Test 8-Hour Validation (Backend check)
        print("[4/7] Testing 8-Hour Daily Limit (Attempting to add 4h more to same day)...")
        resp = await ac.post("/timesheets/entry", json={
            "email": test_email,
            "date_str": target_date.isoformat(),
            "hours": 4.0, # 5 + 4 = 9 (Should fail)
            "project_name": "Overtime",
            "task_description": "Should fail",
            "work_type": "Billable"
        }, headers=headers)
        assert resp.status_code == 400
        assert "Daily limit exceeded" in resp.json()["detail"]
        print("Daily Limit Blocked successfully.")

        # 5. Test Inline Update
        print("[5/7] Testing Inline Update...")
        # Get existing entry
        resp = await ac.get("/timesheets/current", params={"email": test_email, "week_start": target_week.isoformat()}, headers=headers)
        entries = resp.json()["entries"]
        entry_id = entries[0]["entry_id"]
        
        resp = await ac.post("/timesheets/update", json={
            "entry_id": entry_id,
            "email": test_email,
            "hours": 8.0, # Change 5 to 8
            "project_name": "Modified Project",
            "task_description": "Updated Task",
            "work_type": "Billable"
        }, headers=headers)
        assert resp.status_code == 200
        print("Inline Update Successful.")

        # 5b. Test Delete
        print("[5b/7] Testing Delete...")
        # Add a temporary entry to delete
        temp_date = target_week + timedelta(days=1)
        resp = await ac.post("/timesheets/entry", json={
            "email": test_email,
            "date_str": temp_date.isoformat(),
            "hours": 1.0,
            "project_name": "Delete Me",
            "task_description": "Garbage",
            "work_type": "Billable"
        }, headers=headers)
        temp_id = sheet_manager.get_pending_entries(test_email, target_week.isoformat())[-1]["entry_id"]
        
        resp = await ac.post("/timesheets/delete", json={
            "entry_id": temp_id,
            "email": test_email
        }, headers=headers)
        assert resp.status_code == 200
        print("Delete Successful.")

        # 6. Fill Week to 40 Hours and Submit
        print("[6/7] Filling week to 40 hours for submission...")
        # Currently at 8h for Monday. Need 32h more.
        for i in range(1, 5): # Tue, Wed, Thu, Fri
            fill_date = target_week + timedelta(days=i)
            await ac.post("/timesheets/entry", json={
                "email": test_email,
                "date_str": fill_date.isoformat(),
                "hours": 8.0,
                "project_name": "Filling",
                "task_description": "Work",
                "work_type": "Billable"
            }, headers=headers)
        
        print("Submitting full week...")
        resp = await ac.post("/timesheets/submit", json={
            "email": test_email,
            "week_start": target_week.isoformat()
        }, headers=headers)
        assert resp.status_code == 200
        print("Submission Successful.")

        # 7. Verify Lockdown state
        print("[7/7] Verifying Lockdown (Attempting update after submission)...")
        resp = await ac.post("/timesheets/update", json={
            "entry_id": entry_id,
            "email": test_email,
            "hours": 1.0, 
            "project_name": "Tamper",
            "task_description": "Fraud",
            "work_type": "Billable"
        }, headers=headers)
        assert resp.status_code == 400
        assert "cannot be modified" in resp.json()["detail"]
        print("Backend Lockdown Verified.")
        
        print("\n✅ E2E SYSTEM FLOW VERIFIED FOR: " + test_email)

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_full_system_flow())
