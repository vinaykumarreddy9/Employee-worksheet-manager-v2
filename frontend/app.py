import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta, date
import time
import uuid
import sys
import os

# Ensure the project root is in PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.utils.helpers import get_available_weeks

# --- Page Config ---
st.set_page_config(
    page_title="Timesheet Manager App",
    page_icon="🕒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Theme & Design ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    
    /* Main Background */
    .stApp {
        background: radial-gradient(circle at top right, #1e293b, #0f172a);
        color: #f8fafc;
    }
    
    /* Cards & Glassmorphism */
    .glass-card {
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 20px;
    }
    
    /* Metric Styling */
    [data-testid="stMetricValue"] {
        font-size: 2rem;
        font-weight: 600;
        color: #38bdf8;
    }
    
    /* Input Styling */
    .stTextInput input, .stNumberInput input {
        background: rgba(15, 23, 42, 0.6) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        color: white !important;
        border-radius: 8px !important;
    }
    
    /* Button Styling */
    .stButton>button {
        background: linear-gradient(135deg, #38bdf8, #2563eb) !important;
        color: white !important;
        border: none !important;
        padding: 12px 24px !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1) !important;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(56, 189, 248, 0.3) !important;
    }
    
    /* Secondary Button */
    [data-testid="stBaseButton-secondary"] button {
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
    }
    
    /* Success/Info Messages */
    .stAlert {
        border-radius: 12px !important;
        background-color: rgba(16, 185, 129, 0.1) !important;
        border: 1px solid rgba(16, 185, 129, 0.2) !important;
    }
    
    /* Custom Header */
    .app-header {
        display: flex;
        align-items: center;
        gap: 15px;
        margin-bottom: 40px;
    }
    .app-logo { font-size: 2.5rem; }
    .app-title { font-size: 2rem; font-weight: 600; background: linear-gradient(to right, #38bdf8, #818cf8); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    
    /* Sidebar Profile Card */
    .profile-card {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 20px;
    }
    .profile-header {
        color: #38bdf8;
        font-size: 0.9rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .profile-item {
        margin-bottom: 8px;
    }
    .profile-label {
        color: #94a3b8;
        font-size: 0.8rem;
        display: block;
    }
    .profile-value {
        color: #f1f5f9;
        font-size: 0.95rem;
        font-weight: 500;
        word-break: break-all;
    }
    
    /* Stat Card Component */
    .stat-card {
        background: linear-gradient(135deg, rgba(56, 189, 248, 0.1), rgba(37, 99, 235, 0.1));
        border: 1px solid rgba(56, 189, 248, 0.2);
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        transition: all 0.3s ease;
    }
    .stat-card:hover {
        border-color: rgba(56, 189, 248, 0.5);
        transform: translateY(-2px);
    }
    .stat-label {
        color: #94a3b8;
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 8px;
    }
    .stat-value {
        color: #38bdf8;
        font-size: 2.5rem;
        font-weight: 700;
        line-height: 1;
    }
    .stat-unit {
        font-size: 1rem;
        color: #64748b;
        margin-left: 4px;
    }
    </style>
""", unsafe_allow_html=True)

# --- Constants & State ---
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
if BACKEND_URL and not BACKEND_URL.startswith("http"):
    BACKEND_URL = f"http://{BACKEND_URL}"

if "user" not in st.session_state: st.session_state.user = None
if "step" not in st.session_state: st.session_state.step = "login"
if "temp_email" not in st.session_state: st.session_state.temp_email = ""
if "otp_purpose" not in st.session_state: st.session_state.otp_purpose = ""
if "access_token" not in st.session_state: st.session_state.access_token = None

# --- API Helpers ---
def api_call(method, endpoint, data=None, params=None):
    try:
        url = f"{BACKEND_URL}/{endpoint}"
        headers = {}
        if st.session_state.access_token:
            headers["Authorization"] = f"Bearer {st.session_state.access_token}"
            
        if method == "POST":
            res = requests.post(url, json=data, headers=headers)
        else:
            res = requests.get(url, params=params, headers=headers)
        return res
    except Exception as e:
        # Don't show error here, handle it in the UI caller
        print(f"📡 API Connection Error: {e}")
        return None

# --- UI Components ---

def header():
    st.markdown('<div class="app-header"><span class="app-logo">🕒</span><span class="app-title">Timesheet Manager App</span></div>', unsafe_allow_html=True)

def login_ui():
    header()
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        #st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("Login")
        email = st.text_input("Work Email", placeholder="name@company.com")
        password = st.text_input("Password", type="password", placeholder="••••••••")
        
        if st.button("Login", width="stretch"):
            res = api_call("POST", "auth/login", {"email": email, "password": password})
            if res is not None:
                if res.status_code == 200:
                    data = res.json()
                    st.session_state.user = data["user"]
                    st.session_state.access_token = data["access_token"]
                    st.session_state.step = "dashboard"
                    st.rerun()
                else:
                    st.error(f"❌ {res.json().get('detail', 'Authentication failed')}")

def employee_dashboard():
    # Session State for adding/editing
    if "adding_row" not in st.session_state: st.session_state.adding_row = False
    if "editing_id" not in st.session_state: st.session_state.editing_id = None

    # Structured Sidebar Profile
    st.sidebar.markdown(f"""
    <div class="profile-card">
        <div class="profile-header">
            <span>👤</span> User Profile
        </div>
        <div class="profile-item">
            <span class="profile-label">Name</span>
            <span class="profile-value">{st.session_state.user.get('full_name', 'N/A')}</span>
        </div>
        <div class="profile-item">
            <span class="profile-label">Employee ID</span>
            <span class="profile-value">{st.session_state.user.get('employee_id', 'N/A')}</span>
        </div>
        <div class="profile-item">
            <span class="profile-label">Email</span>
            <span class="profile-value">{st.session_state.user['email']}</span>
        </div>
        <div class="profile-item">
            <span class="profile-label">Role</span>
            <span class="profile-value">Employee</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if st.sidebar.button("Log Out", width="stretch"):
        st.session_state.user = None
        st.session_state.step = "login"
        st.rerun()

    st.title("Employee Timesheet Dashboard")
    
    # --- Period Selection (Past 4 Weeks) ---
    available_weeks = get_available_weeks()
    week_options = {w.isoformat(): f"Week of {w.strftime('%B %d, %Y')}" for w in available_weeks}
    
    selected_week_str = st.selectbox(
        "Select Pay Period", 
        options=list(week_options.keys()), 
        format_func=lambda x: week_options[x],
        index=0,
        help="Select a Monday-starting week from the past 4 weeks."
    )
    
    # Fetch entries for selected week
    res = api_call("GET", "timesheets/current", params={"email": st.session_state.user['email'], "week_start": selected_week_str})
    if res is None or res.status_code != 200:
        if res: st.error(f"❌ Failed to load timesheet: {res.json().get('detail', 'Unknown error')}")
        return
    
    data = res.json()
    entries = data["entries"]
    week_start_date = datetime.strptime(selected_week_str, "%Y-%m-%d").date()
    
    # Check if week is locked (Submitted or Approved)
    is_locked = any(e['status'] in ['Submitted', 'Approved'] for e in entries)
    
    # Calculate totals
    total_h = sum(float(e['hours']) for e in entries) if entries else 0.0

    # --- Weekly Summary Table (Live Grid) ---
    st.markdown("### Weekly Activities")
    
    # Table Header
    header_cols = st.columns([1.5, 0.8, 3.2, 1.5, 1])
    headers = ["Date", "Hours", "Project Description", "Work Type", ""]
    for col, h in zip(header_cols, headers):
        col.markdown(f"**{h}**")
    st.divider()

    # Define update callback
    def on_entry_change(e_id, field):
        try:
            # Handle Holiday logic: if type is Holiday, hours=8.0, proj='Holiday'
            work_type = st.session_state.get(f"type_{e_id}", "Regular Work")
            if work_type == "Holiday":
                hours = 8.0
                proj = "Holiday"
            else:
                hours = float(st.session_state.get(f"hrs_{e_id}", 0.0))
                proj = st.session_state.get(f"proj_{e_id}", "")

            res = api_call("POST", "timesheets/update", {
                "entry_id": e_id,
                "email": st.session_state.user['email'],
                "hours": hours,
                "project_name": proj,
                "task_description": proj,
                "work_type": work_type
            })
            if res and res.status_code == 200:
                st.toast(f"Entry updated", icon="✅")
            else:
                st.error(res.json().get('detail', 'Update failed'))
        except Exception as ex:
            st.error(f"Sync error: {ex}")

    # Sort entries by date
    sorted_entries = sorted(entries, key=lambda x: x['date'])

    for entry in sorted_entries:
        row_id = entry['entry_id']
        cols = st.columns([1.5, 0.8, 3.2, 1.5, 1])
        
        if is_locked:
            cols[0].write(datetime.strptime(entry['date'], "%Y-%m-%d").strftime("%a, %b %d"))
            cols[1].write(f"{entry['hours']} hrs")
            cols[2].write(entry['project_name'])
            cols[3].write(entry.get('work_type', 'Regular Work'))
            cols[4].write("🔒")
        else:
            # --- Live Edit Mode ---
            mon_to_fri = [week_start_date + timedelta(days=i) for i in range(5)]
            curr_date = datetime.strptime(entry['date'], "%Y-%m-%d").date()
            
            # Filter dates
            available_dates = []
            for d in mon_to_fri:
                daily_total = sum(float(e['hours']) for e in entries if e['date'] == d.isoformat())
                if d == curr_date or daily_total < 8.0:
                    available_dates.append(d)
            
            # Date Select
            cols[0].selectbox("Date", options=available_dates, format_func=lambda x: x.strftime("%a, %b %d"), 
                             index=available_dates.index(curr_date) if curr_date in available_dates else 0, 
                             key=f"date_{row_id}", label_visibility="collapsed", disabled=True)
            
            # Type Select
            curr_work_type = entry.get('work_type') or 'Regular Work'
            type_options = ["Regular Work", "Holiday"]
            try:
                type_idx = type_options.index(curr_work_type)
            except ValueError:
                type_idx = 0
            
            cols[3].selectbox("Type", options=type_options, index=type_idx, 
                             key=f"type_{row_id}", label_visibility="collapsed", on_change=on_entry_change, args=(row_id, "type"))
            
            is_holiday = st.session_state[f"type_{row_id}"] == "Holiday"
            
            if is_holiday:
                cols[1].markdown("**8.0**")
                cols[2].markdown("*Holiday*")
            else:
                # Calculate remaining hours
                other_logged = sum(float(e['hours']) for e in entries if e['date'] == entry['date'] and e['entry_id'] != row_id)
                remaining_for_row = 8.0 - other_logged
                hour_options = [float(i/2) for i in range(1, 17) if (i/2) <= remaining_for_row]
                
                try:
                    def_idx = hour_options.index(float(entry['hours']))
                except:
                    def_idx = 0
                
                cols[1].selectbox("Hrs", options=hour_options, index=def_idx, key=f"hrs_{row_id}", 
                                 label_visibility="collapsed", on_change=on_entry_change, args=(row_id, "hrs"))
                cols[2].text_input("Project", value=entry['project_name'], key=f"proj_{row_id}", 
                                  label_visibility="collapsed", on_change=on_entry_change, args=(row_id, "proj"))
            

        st.divider()

    # --- New Row Area ---
    if not is_locked:
        mon_to_fri_all = [week_start_date + timedelta(days=i) for i in range(5)]
        available_for_new = []
        for d in mon_to_fri_all:
            daily_total = sum(float(e['hours']) for e in entries if e['date'] == d.isoformat())
            if daily_total < 8.0:
                available_for_new.append(d)

        if available_for_new:
            cols = st.columns([1.5, 0.8, 3.2, 1.5, 1])
            new_date = cols[0].selectbox("Date", options=available_for_new, format_func=lambda x: x.strftime("%a, %b %d"), key="new_date", label_visibility="collapsed")
            new_type = cols[3].selectbox("Type", options=["Regular Work", "Holiday"], key="new_type", label_visibility="collapsed")
            
            if new_type == "Holiday":
                new_hours = 8.0
                new_proj = "Holiday"
                cols[1].markdown("8.0")
                cols[2].markdown("Holiday")
            else:
                today_logged = sum(float(e['hours']) for e in entries if e['date'] == new_date.isoformat())
                rem = 8.0 - today_logged
                h_opts = [float(i/2) for i in range(1, 17) if (i/2) <= rem]
                if h_opts:
                    new_hours = cols[1].selectbox("Hrs", options=h_opts, index=len(h_opts)-1, key="new_hrs", label_visibility="collapsed")
                else:
                    new_hours = 0.0
                    cols[1].error("Full")
                new_proj = cols[2].text_input("Project", placeholder="Task...", key="new_proj", label_visibility="collapsed")
            
            if cols[4].button("➕ New", key="add_btn", type="primary"):
                if not new_proj and new_type != "Holiday":
                    st.error("Project required")
                else:
                    res = api_call("POST", "timesheets/entry", {
                        "email": st.session_state.user['email'],
                        "date_str": new_date.isoformat(),
                        "hours": new_hours,
                        "project_name": new_proj,
                        "task_description": new_proj,
                        "work_type": new_type
                    })
                    if res and res.status_code == 200:
                        st.success("Added!")
                        st.rerun()
                    else:
                        st.error(res.json().get('detail', 'Failed'))

    st.divider()

    # --- Finalize & Submit ---
    if not is_locked:
        if total_h >= 40.0:
            if st.button("🚀 Submit", type="primary", use_container_width=True):
                st.session_state.confirm_submit = True
        else:
            st.button("🚀 Submit", type="secondary", disabled=True, use_container_width=True, help="Record 40.0 hours to enable.")

        if st.session_state.get('confirm_submit'):
            st.warning("⚠️ **Confirm Submission:** Once submitted, you cannot edit this week's entries until an admin processes it.")
            c1, c2 = st.columns(2)
            if c1.button("✅ Yes, Submit Now", type="primary", use_container_width=True):
                res = api_call("POST", "timesheets/submit", {"email": st.session_state.user['email'], "week_start": selected_week_str})
                if res and res.status_code == 200:
                    st.success("Submitted successfully!")
                    st.session_state.confirm_submit = False
                    st.rerun()
                else:
                    st.error(res.json().get('detail', 'Submission failed'))
            if c2.button("❌ Cancel", use_container_width=True):
                st.session_state.confirm_submit = False
                st.rerun()
    

def admin_dashboard():
    # Structured Sidebar Profile
    st.sidebar.markdown(f"""
    <div class="profile-card">
        <div class="profile-header">
            <span>🛡️</span> Administrator
        </div>
        <div class="profile-item">
            <span class="profile-label">Name</span>
            <span class="profile-value">{st.session_state.user.get('full_name', 'Admin')}</span>
        </div>
        <div class="profile-item">
            <span class="profile-label">Employee ID</span>
            <span class="profile-value">{st.session_state.user.get('employee_id', 'ADM001')}</span>
        </div>
        <div class="profile-item">
            <span class="profile-label">Email</span>
            <span class="profile-value">{st.session_state.user['email']}</span>
        </div>
        <div class="profile-item">
            <span class="profile-label">Role</span>
            <span class="profile-value">System Admin</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.sidebar.button("Log Out", width="stretch", type="secondary"):
        st.session_state.user = None
        st.session_state.step = "login"
        st.rerun()

    st.title("Admin Dashboard")
    st.subheader("Timesheet Submissions")
    res = api_call("GET", "admin/submissions")
    if res is not None and res.status_code == 200:
        subs = res.json()
        if not subs: 
            st.info("No submissions awaiting review.")
        else:
            # Group by email and week_start for aggregate review
            df = pd.DataFrame(subs)
            grouped = df.groupby(['email', 'week_start_date']).agg({
                'hours': 'sum'
            }).reset_index()
            
            for _, row in grouped.iterrows():
                email = row['email']
                w_start = row['week_start_date']
                w_end = (datetime.fromisoformat(w_start) + timedelta(days=6)).date().isoformat()
                
                with st.expander(f"Review: **{email}** ({w_start} to {w_end})"):
                    week_entries = df[(df['email'] == email) & (df['week_start_date'] == w_start)]
                    
                    # Display entries in a professional table
                    display_df = week_entries[['date', 'project_name', 'work_type', 'hours']].copy()
                    display_df.columns = ['Date', 'Project Detail', 'Work Type', 'Hours']
                    st.table(display_df)
                    
                    st.markdown(f"**Total Hours for Week:** `{row['hours']} hrs`")
                    st.divider()

                    # Action Buttons
                    b1, b2 = st.columns(2)
                    
                    if b1.button("✅ Approve", key=f"appts_{email}_{w_start}", width="stretch"):
                        res = api_call("POST", "admin/timesheets/process", {
                            "email": email, "week_start": w_start,
                            "action": "Approve", "admin_email": st.session_state.user['email'], "reason": "Approved"
                        })
                        if res is not None:
                            if res.status_code == 200:
                                st.success("Timesheet Approved!")
                                st.rerun()
                            else:
                                st.error(f"❌ {res.json().get('detail', 'Approval failed')}")

                    if b2.button("❌ Reject", key=f"rejts_{email}_{w_start}", width="stretch", type="secondary"):
                        st.session_state.reject_target = {"email": email, "week_start": w_start}
                        st.rerun()

    # Rejection Modal (Simulated via Session State)
    if "reject_target" in st.session_state:
        target = st.session_state.reject_target
        st.markdown("---")
        st.warning(f"### 🚩 Correction Required\nReturning timesheet for **{target['email']}** for revision (Week: {target['week_start']})")
        reason = st.text_area("Notes for Employee", placeholder="e.g. Please clarify project details for Monday...")
        
        c1, c2 = st.columns(2)
        if c1.button("Send Back", type="primary", width="stretch"):
            if not reason:
                st.error("Please provide a reason")
            else:
                res = api_call("POST", "admin/timesheets/process", {
                    "email": target['email'], "week_start": target['week_start'],
                    "action": "Deny", "admin_email": st.session_state.user['email'], "reason": reason
                })
                if res is not None:
                    if res.status_code == 200:
                        del st.session_state.reject_target
                        st.success("Timesheet returned for correction.")
                        st.rerun()
                    else:
                        st.error(f"❌ {res.json().get('detail', 'Rejection failed')}")
        
        if c2.button("Cancel", width="stretch"):
            del st.session_state.reject_target
            st.rerun()

# --- Router ---
if st.session_state.step == "login": 
    login_ui()
elif st.session_state.step == "dashboard":
    if st.session_state.user["role"] == "Admin": 
        admin_dashboard()
    else: 
        employee_dashboard()
