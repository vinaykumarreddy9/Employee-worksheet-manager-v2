# Implementation Plan - Employee Weekly Timesheet Manager

## Phase 1: Environment & Spreadsheet Setup

- [ ] Create Google Cloud Project & Service Account.
- [ ] Create the Google Spreadsheet with 7 mandatory sheets.
- [ ] Set up local project structure (backend, frontend, shared).
- [ ] Install dependencies (FastAPI, Streamlit, gspread, pydantic, etc.).

## Phase 2: Core Data Access Layer (Google Sheets)

- [ ] Implement `SpreadsheetClient` for initialization.
- [ ] Implement CRUD operations for `User Logins`, `Signup Requests`, and `OTP Logs`.
- [ ] Implement CRUD operations for `Pending`, `Approved`, and `Denied` Timesheets.
- [ ] Implement Audit Logging utility.

## Phase 3: Backend API (Auth & Signup)

- [ ] Implement OTP generation and verification logic.
- [ ] Implement Signup Request API.
- [ ] Implement Admin Signup Approval logic.
- [ ] Implement User Session/Auth middleware (FastAPI).

## Phase 4: Frontend (Auth & Signup)

- [ ] Build Streamlit Login flow (Email + OTP).
- [ ] Build Streamlit Signup flow.
- [ ] Build Admin Approval Dashboard component.

## Phase 5: Timesheet Logic (Employee)

- [ ] Implement backend logic for finding/creating current week timesheet.
- [ ] Implement backend logic for saving Drafts and Submitting.
- [ ] Build Streamlit Timesheet Editor (Live totals, Sunday-Saturday).
- [ ] Build History View for employees.

## Phase 6: Admin Review & Audit

- [ ] Implement backend logic for Reviewing (Approve/Deny/Edit).
- [ ] Build Admin Timesheet Review Board.
- [ ] Build Audit Log Viewer.

## Phase 7: Automation & Polish

- [ ] Implement APScheduler for Sunday 4 AM auto-submit.
- [ ] Add detailed error handling and loading states.
- [ ] Final security audit and validation check.
