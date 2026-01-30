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

def safe_float(v):
    try:
        return float(v) if v and str(v).strip() else 0.0
    except:
        return 0.0

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
    
    /* Main Background - Adaptive */
    .stApp {
        background-color: var(--background-color);
        background-image: radial-gradient(circle at top right, rgba(56, 189, 248, 0.1), transparent);
        color: var(--text-color);
    }
    
    /* Cards & Glassmorphism */
    .glass-card {
        background: rgba(120, 120, 120, 0.05);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(120, 120, 120, 0.1);
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
    .stTextInput input, .stNumberInput input, .stSelectbox [data-baseweb="select"] {
        background: rgba(120, 120, 120, 0.1) !important;
        border: 1px solid rgba(120, 120, 120, 0.2) !important;
        color: var(--text-color) !important;
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
        background: rgba(120, 120, 120, 0.05);
        border: 1px solid rgba(120, 120, 120, 0.1);
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
        color: var(--text-color);
        opacity: 0.6;
        font-size: 0.8rem;
        display: block;
    }
    .profile-value {
        color: var(--text-color);
        font-size: 0.95rem;
        font-weight: 500;
        word-break: break-all;
    }
    
    /* Sidebar Logo Styling */
    .sidebar-logo-container {
        display: flex;
        justify-content: center;
        margin-top: -20px;
        margin-bottom: 25px;
    }
    .sidebar-logo {
        width: 120px !important;
        height: 120px !important;
        object-fit: cover;
        border-radius: 50% !important;
        border: 4px solid rgba(56, 189, 248, 0.3) !important;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3) !important;
        transition: all 0.3s ease-in-out;
    }
    .sidebar-logo:hover {
        transform: scale(1.05);
        border-color: #38bdf8 !important;
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

    /* --- Hybrid Grid System --- */
    .ts-grid-container {
        width: 100%;
        font-family: 'Inter', sans-serif;
    }
    
    /* Shared widths for both HTML and st.columns to align vertically */
    .col-date    { width: 14%; }
    .col-hours   { width: 9%;  }
    .col-project { width: 44%; }
    .col-type    { width: 18%; }
    .col-action  { width: 15%; }

    /* The HTML Table (Proper structure for Read-Only) */
    .ts-locked-table {
        width: 100%;
        border-collapse: collapse;
        table-layout: fixed;
        background: white;
        border: 2px solid #000000;
    }
    .ts-locked-table th {
        background: rgba(0, 0, 0, 0.05);
        color: #000000;
        font-weight: 700;
        text-transform: uppercase;
        font-size: 0.85rem;
        padding: 14px 10px;
        border: 1px solid #000000;
        text-align: center;
    }
    .ts-locked-table td {
        border: 1px solid #000000;
        padding: 0px 10px;
        height: 52px;
        text-align: center;
        font-size: 0.95rem;
    }
    .ts-locked-table tr:nth-child(even) { background: rgba(0,0,0,0.01); }

    /* Streamlit Row Wrapper (for Interactivity) */
    .ts-edit-row {
        display: flex;
        width: 100%;
        background: white;
        border-left: 2px solid #000000;
        border-right: 2px solid #000000;
        border-bottom: 2px solid #000000;
        margin-top: -1px; /* Stitching rows together */
    }
    .ts-edit-row:hover { background: rgba(56, 189, 248, 0.02); }

    /* Target st.columns inside the row */
    .ts-edit-row [data-testid="column"] {
        border-right: 1px solid #000000;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        padding: 0 !important;
        height: 52px;
    }
    .ts-edit-row [data-testid="column"]:last-child { border-right: none; }

    /* Clean inputs inside the grid */
    .ts-edit-row input, .ts-edit-row [data-baseweb="select"] {
        border: none !important;
        background: transparent !important;
        text-align: center !important;
        box-shadow: none !important;
        height: 48px !important;
        font-size: 0.95rem !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- Constants & State ---
BACKEND_URL = os.getenv("BACKEND_URL", "https://worksheet-manager-backend-v2.onrender.com")

# If BACKEND_URL is provided as a hostname:port (Render internal), add http://
if BACKEND_URL and not BACKEND_URL.startswith("http"):
    BACKEND_URL = f"http://{BACKEND_URL}"

# If on Render, the internal host/port might still fail if not reachable. 
# We'll handle this in the api_call with better error reporting.

if "user" not in st.session_state: st.session_state.user = None
if "step" not in st.session_state: st.session_state.step = "login"
if "temp_email" not in st.session_state: st.session_state.temp_email = ""
if "otp_purpose" not in st.session_state: st.session_state.otp_purpose = ""
if "access_token" not in st.session_state: st.session_state.access_token = None

# --- API Helpers ---
def api_call(method, endpoint, data=None, params=None, retries=5):
    # Ensure no double slashes if BACKEND_URL has a trailing slash
    base_url = BACKEND_URL.rstrip("/")
    final_url = f"{base_url}/{endpoint}"
    res = None
    
    for attempt in range(retries):
        try:
            headers = {}
            if st.session_state.access_token:
                headers["Authorization"] = f"Bearer {st.session_state.access_token}"
                
            if method == "POST":
                res = requests.post(final_url, json=data, headers=headers, timeout=20)
            else:
                res = requests.get(final_url, params=params, headers=headers, timeout=20)
            
            # More flexible JSON check: handle "application/json; charset=utf-8"
            content_type = res.headers.get("Content-Type", "").lower()
            if res.status_code == 200 and "application/json" in content_type:
                return res
            
            # If it's a 200 but not JSON, or a 50x error, it's likely the server waking up
            if (res.status_code == 200 and "application/json" not in content_type) or res.status_code in [502, 503, 504]:
                if attempt < retries - 1:
                    wait_time = 2 + attempt # Increasing wait
                    time.sleep(wait_time)
                    continue
            
            return res # Return what we have for 4xx or persistent errors
            
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            if attempt < retries - 1:
                time.sleep(3)
                continue
            break
        except Exception as e:
            print(f"📡 API Error: {e}")
            break
            
    if res is None:
        st.error(f"📡 **API Connection Error:** Could not reach the backend server.")
        st.info(f"Connecting to: `{final_url}`")
        st.divider()
    return res

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
                    try:
                        data = res.json()
                        st.session_state.user = data["user"]
                        st.session_state.access_token = data["access_token"]
                        st.session_state.step = "dashboard"
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error processing user data: {str(e)}")
                        st.info("The server responded with 200 OK but the data was not in the expected format.")
                else:
                    try:
                        error_msg = res.json().get('detail', 'Authentication failed')
                        st.error(f"❌ {error_msg}")
                    except:
                        st.error(f"❌ Server returned error {res.status_code}. (Non-JSON response)")
                        try:
                            st.code(res.text[:200], language="html")
                        except: pass
        
        st.markdown('<div style="text-align: center; margin-top: 15px; color: #64748b;">Don\'t have an account?</div>', unsafe_allow_html=True)
        if st.button("Create New Account", use_container_width=True):
            st.session_state.step = "register"
            st.rerun()

def register_ui():
    header()
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.subheader("Create Account")
        full_name = st.text_input("Full Name", placeholder="John Doe")
        emp_id = st.text_input("Employee ID", placeholder="EMP-123")
        role = st.selectbox("Role", ["Employee", "Admin"])
        email = st.text_input("Work Email", placeholder="name@company.com")
        password = st.text_input("Password", type="password", placeholder="••••••••")
        
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Sign Up", type="primary", use_container_width=True):
                if not all([full_name, emp_id, email, password]):
                    st.error("Please fill in all fields")
                else:
                    payload = {
                        "full_name": full_name,
                        "employee_id": emp_id,
                        "role": role,
                        "email": email,
                        "password": password
                    }
                    res = api_call("POST", "auth/register", payload)
                    if res and res.status_code == 200:
                        st.success("✅ Registration successful! Please login.")
                        time.sleep(1.5)
                        st.session_state.step = "login"
                        st.rerun()
                    elif res:
                        try:
                            st.error(f"❌ {res.json().get('detail', 'Registration failed')}")
                        except:
                            st.error("❌ Registration failed (Server Error)")
        with c2:
            if st.button("Back to Login", use_container_width=True):
                st.session_state.step = "login"
                st.rerun()

def render_sidebar_profile(user_role="Employee"):
    # Logo - Scaled for better professionalism
    logo_path = os.path.join("frontend", "assets", "logo.png")
    if os.path.exists(logo_path):
        import base64
        with open(logo_path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode()
        
        st.sidebar.markdown(f"""
            <div class="sidebar-logo-container">
                <img src="data:image/png;base64,{encoded}" class="sidebar-logo">
            </div>
        """, unsafe_allow_html=True)
    else:
        # Fallback if image not found
        st.sidebar.markdown("### 🕒 Timesheet Manager")
    
    # Profile Card
    st.sidebar.markdown(f"""
    <div class="profile-card">
        <div class="profile-header">
            <span>{'🛡️' if user_role == 'Admin' else '👤'}</span> {user_role} Profile
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
            <span class="profile-value">{user_role}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

def employee_dashboard():
    if "pending_changes" not in st.session_state: st.session_state.pending_changes = []
    if "is_saving" not in st.session_state: st.session_state.is_saving = False
    if "row_counter" not in st.session_state: st.session_state.row_counter = 0
    
    # Initialize dynamic keys for the current counter
    cnt = st.session_state.row_counter
    if f"new_hrs_{cnt}" not in st.session_state: st.session_state[f"new_hrs_{cnt}"] = "8.0"
    if f"new_proj_{cnt}" not in st.session_state: st.session_state[f"new_proj_{cnt}"] = ""
    if f"new_type_{cnt}" not in st.session_state: st.session_state[f"new_type_{cnt}"] = "Billable"

    # Structured Sidebar Profile
    render_sidebar_profile("Employee")
    
    if st.sidebar.button("Log Out", width="stretch"):
        st.session_state.user = None
        st.session_state.pending_changes = []
        st.session_state.step = "login"
        st.rerun()

    st.title("Employee Dashboard")
    
    # --- Period Selection (Past 4 Weeks) ---
    def on_entry_change(e_id, field):
        if field == "type":
            if st.session_state.get(f"type_{e_id}") == "Holiday":
                st.session_state[f"hrs_{e_id}"] = "8.0"

    def on_new_type_change():
        cnt = st.session_state.row_counter
        if st.session_state.get(f"new_type_{cnt}") == "Holiday":
            st.session_state[f"new_hrs_{cnt}"] = "8.0"

    available_weeks = get_available_weeks()
    week_options = {w.isoformat(): f"Week of {w.strftime('%B %d, %Y')}" for w in available_weeks}
    
    selected_week_str = st.selectbox(
        "Select Period", 
        options=list(week_options.keys()), 
        format_func=lambda x: week_options[x],
        index=0,
        help="Select a Monday-starting week from the past 4 weeks.",
        key="selected_week"
    )
    
    # Clear old row keys when week changes
    if "last_week" not in st.session_state: st.session_state.last_week = selected_week_str
    if st.session_state.last_week != selected_week_str:
        keys_to_clear = [k for k in st.session_state.keys() if k.startswith(("type_", "hrs_", "proj_", "new_"))]
        for k in keys_to_clear: del st.session_state[k]
        st.session_state.pending_changes = []
        st.session_state.row_counter = 0
        st.session_state.last_week = selected_week_str
    
    # Fetch entries for selected week
    res = api_call("GET", "timesheets/current", params={"email": st.session_state.user['email'], "week_start": selected_week_str})
    if res is None or res.status_code != 200:
        if res:
            try:
                msg = res.json().get('detail', 'Unknown error')
                st.error(f"❌ Failed to load timesheet: {msg}")
            except:
                st.error(f"❌ Server error ({res.status_code}) loading timesheet")
        return
    
    try:
        data = res.json()
        entries = data["entries"]
    except Exception as e:
        st.error(f"❌ Error parsing timesheet data")
        return
    week_start_date = datetime.strptime(selected_week_str, "%Y-%m-%d").date()
    # Check if week is locked (Submitted or Approved)
    is_locked = any(e['status'] in ['Submitted', 'Approved'] for e in entries)
    
    # Calculate totals including pending changes
    display_entries = entries + st.session_state.pending_changes
    current_total = sum(safe_float(st.session_state.get(f"hrs_{e['entry_id']}", e['hours'])) for e in display_entries)
    billable_h = sum(safe_float(st.session_state.get(f"hrs_{e['entry_id']}", e['hours'])) for e in display_entries if st.session_state.get(f"type_{e['entry_id']}", e.get('work_type')) == 'Billable')
    holiday_h = sum(safe_float(st.session_state.get(f"hrs_{e['entry_id']}", e['hours'])) for e in display_entries if st.session_state.get(f"type_{e['entry_id']}", e.get('work_type')) == 'Holiday')
    
    # --- Metrics Row ---
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Total Hours", f"{current_total:.1f} hrs", delta=f"{current_total-40:.1f}" if current_total >= 40 else f"{current_total-40:.1f}", delta_color="normal")
    with m2:
        status_color = "🟢" if is_locked else "🟠"
        st.metric("Status", "Locked" if is_locked else "Editable", help="Locked means the week is Submitted or Approved.")
    with m3:
        st.metric("Billable", f"{billable_h:.1f} hrs")
    with m4:
        st.metric("Holiday", f"{holiday_h:.1f} hrs")

    st.markdown("<br>", unsafe_allow_html=True)

    # --- Weekly Activities (Table) ---
    main_col1, main_col2, main_col3 = st.columns([1, 10, 1])
    
    with main_col2:
        # Prepare data
        display_list = entries + st.session_state.pending_changes
        sorted_display = sorted(display_list, key=lambda x: x['date'])

        available_for_new = []
        if not is_locked:
            mon_to_fri_all = [week_start_date + timedelta(days=i) for i in range(5)]
            for d in mon_to_fri_all:
                daily_total = sum(safe_float(st.session_state.get(f"hrs_{e['entry_id']}", e['hours'])) for e in display_list if e['date'] == d.isoformat())
                if daily_total < 8.0: available_for_new.append(d)
        
        # --- RENDER TABLE ---
        if is_locked:
            # Everything as HTML table for perfect stability
            html_rows = []
            for entry in sorted_display:
                date_fmt = datetime.strptime(entry['date'], "%Y-%m-%d").strftime("%a, %b %d")
                html_rows.append(f"<tr><td>{date_fmt}</td><td>{entry['hours']} hrs</td><td>{entry['project_name']}</td><td>{entry.get('work_type', 'Billable')}</td><td>🔒</td></tr>")
            
            st.markdown(f"""
            <table class='ts-locked-table'>
                <thead>
                    <tr>
                        <th class='col-date'>DATE</th><th class='col-hours'>HOURS</th><th class='col-project'>PROJECT DESCRIPTION</th><th class='col-type'>WORK TYPE</th><th class='col-action'>ACTION</th>
                    </tr>
                </thead>
                <tbody>{''.join(html_rows)}</tbody>
            </table>
            """, unsafe_allow_html=True)
        else:
            # Header Only as HTML
            st.markdown("""
            <table class='ts-locked-table' style='border-bottom: none;'>
                <thead>
                    <tr>
                        <th class='col-date'>DATE</th><th class='col-hours'>HOURS</th><th class='col-project'>PROJECT DESCRIPTION</th><th class='col-type'>WORK TYPE</th><th class='col-action'>ACTION</th>
                    </tr>
                </thead>
            </table>
            """, unsafe_allow_html=True)
            
            # Rows using st.columns (Synchronized with CSS)
            col_weights = [1.4, 0.9, 4.4, 1.8, 1.5]
            
            for entry in sorted_display:
                row_id = entry['entry_id']
                # Store state
                if f"type_{row_id}" not in st.session_state: st.session_state[f"type_{row_id}"] = entry.get('work_type', 'Billable')
                if f"hrs_{row_id}" not in st.session_state: st.session_state[f"hrs_{row_id}"] = str(entry['hours'])
                if f"proj_{row_id}" not in st.session_state: st.session_state[f"proj_{row_id}"] = entry['project_name']

                st.markdown("<div class='ts-edit-row'>", unsafe_allow_html=True)
                cols = st.columns(col_weights)
                date_fmt = datetime.strptime(entry['date'], "%Y-%m-%d").strftime("%a, %b %d")
                cols[0].write(date_fmt)
                with cols[1]:
                    is_holiday = st.session_state.get(f"type_{row_id}") == "Holiday"
                    st.text_input("Hrs", key=f"hrs_{row_id}", label_visibility="collapsed", on_change=on_entry_change, args=(row_id, "hrs"), disabled=is_holiday)
                with cols[2]:
                    st.text_input("Proj", key=f"proj_{row_id}", label_visibility="collapsed", on_change=on_entry_change, args=(row_id, "proj"))
                with cols[3]:
                    st.selectbox("Type", options=["Billable", "Holiday"], key=f"type_{row_id}", label_visibility="collapsed", on_change=on_entry_change, args=(row_id, "type"))
                cols[4].write("") 
                st.markdown("</div>", unsafe_allow_html=True)

            # Add New Row
            if available_for_new:
                cnt = st.session_state.row_counter
                st.markdown("<div class='ts-edit-row' style='background: rgba(0,0,0,0.02);'>", unsafe_allow_html=True)
                new_cols = st.columns(col_weights)
                with new_cols[0]:
                    st.selectbox("Date", options=available_for_new, format_func=lambda x: x.strftime("%a, %b %d"), key=f"new_date_{cnt}", label_visibility="collapsed")
                with new_cols[1]:
                    is_new_holiday = st.session_state.get(f"new_type_{cnt}") == "Holiday"
                    st.text_input("NewHrs", key=f"new_hrs_{cnt}", label_visibility="collapsed", disabled=is_new_holiday)
                with new_cols[2]:
                    st.text_input("NewProj", placeholder="Project detail...", key=f"new_proj_{cnt}", label_visibility="collapsed")
                with new_cols[3]:
                    st.selectbox("NewType", options=["Billable", "Holiday"], key=f"new_type_{cnt}", label_visibility="collapsed", on_change=on_new_type_change)
                with new_cols[4]:
                    if st.button("Add", key="add_btn", type="primary", use_container_width=True):
                        # Extract and validate inputs
                        raw_h = st.session_state.get(f"new_hrs_{cnt}", "0").strip()
                        raw_p = st.session_state.get(f"new_proj_{cnt}", "").strip()
                        raw_t = st.session_state.get(f"new_type_{cnt}", "Billable")
                        new_dt = st.session_state.get(f"new_date_{cnt}")

                        if not raw_p and raw_t != "Holiday":
                            st.error("Project description is required for billable work.")
                        elif not raw_h:
                            st.error("Please enter hours worked.")
                        else:
                            try:
                                h_val = float(raw_h)
                                if h_val <= 0:
                                    st.error("Hours must be greater than 0.")
                                    st.stop()
                                
                                # Check daily limit
                                dt_str = new_dt.isoformat()
                                day_total = sum(safe_float(st.session_state.get(f"hrs_{e['entry_id']}", e['hours'])) 
                                               for e in display_list if e['date'] == dt_str)
                                
                                if day_total + h_val > 8.01:
                                    st.error(f"Cannot exceed 8 hours per day. Current total for {new_dt.strftime('%b %d')}: {day_total} hrs.")
                                    st.stop()

                                # Success - Create Draft
                                new_draft = {
                                    "entry_id": f"draft_{uuid.uuid4().hex[:8]}",
                                    "email": st.session_state.user['email'],
                                    "date": dt_str,
                                    "hours": h_val,
                                    "project_name": raw_p,
                                    "task_description": raw_p,
                                    "work_type": raw_t,
                                    "status": "Draft"
                                }
                                st.session_state.pending_changes.append(new_draft)
                                
                                # Increment counter to reset widgets
                                st.session_state.row_counter += 1
                                st.rerun()
                                
                            except ValueError:
                                st.error(f"'{raw_h}' is not a valid number for hours.")
                            except Exception as e:
                                st.error(f"An unexpected error occurred: {str(e)}")
                st.markdown("</div>", unsafe_allow_html=True)

        # Combine official entries with draft changes for display
        display_entries = sorted(entries + st.session_state.pending_changes, key=lambda x: x['date'])
        
        st.markdown("<hr style='margin: 0.5rem 0; opacity: 0.2;'>", unsafe_allow_html=True)

        # --- Finalize & Submit ---
        if not is_locked:
            # --- Validation Logic ---
            validation_errors = []
            daily_totals = {}
            
            # Map all rows (existing + drafts) to their current state values
            for entry in sorted_display:
                e_id = entry['entry_id']
                d_str = entry['date']
                d_fmt = datetime.strptime(d_str, "%Y-%m-%d").strftime("%a, %b %d")
                
                # Get current values from session state
                curr_h = st.session_state.get(f"hrs_{e_id}", str(entry['hours']))
                curr_p = st.session_state.get(f"proj_{e_id}", entry['project_name'])
                curr_t = st.session_state.get(f"type_{e_id}", entry.get('work_type', 'Billable'))
                
                # 1. Project Check
                if not curr_p.strip() and curr_t != "Holiday":
                    validation_errors.append(f"Project Description is missing for {d_fmt}")
                
                # 2. Hours Numeric Check
                try:
                    h_val = float(curr_h)
                    if h_val <= 0:
                        validation_errors.append(f"Hours must be > 0 for {d_fmt}")
                    daily_totals[d_str] = daily_totals.get(d_str, 0.0) + h_val
                except:
                    validation_errors.append(f"Invalid numeric value for hours on {d_fmt}")

            # Check daily limits
            for d_str, total in daily_totals.items():
                if total > 8.01:
                    d_fmt = datetime.strptime(d_str, "%Y-%m-%d").strftime("%a, %b %d")
                    validation_errors.append(f"Total hours for {d_fmt} ({total} hrs) exceeds 8.0 limit")

            if validation_errors:
                for err in validation_errors:
                    st.error(f"⚠️ {err}")

            save_col, submit_col = st.columns(2)
            
            # Save Button
            has_pending = len(st.session_state.pending_changes) > 0
            # Also check if existing entries have different values in session_state than in the database
            modified_existing = []
            for e in entries:
                e_id = e['entry_id']
                row_type = st.session_state.get(f"type_{e_id}", e.get('work_type', 'Billable'))
                
                raw_h = st.session_state.get(f"hrs_{e_id}", str(e['hours']))
                try:
                    row_hrs = float(raw_h)
                except:
                    row_hrs = float(e['hours']) # Fallback for comparison if invalid

                row_proj = st.session_state.get(f"proj_{e_id}", e['project_name'])
                
                if row_type != e.get('work_type') or row_hrs != float(e['hours']) or row_proj != e['project_name']:
                    modified_existing.append({
                        "entry_id": e_id,
                        "email": st.session_state.user['email'],
                        "hours": row_hrs,
                        "project_name": row_proj,
                        "task_description": row_proj,
                        "work_type": row_type
                    })
            
            can_save = (has_pending or modified_existing) and not validation_errors
            
            save_btn_help = "Resolution of all errors is required to save." if validation_errors else "Save all draft changes to the database."
            
            if save_col.button("💾 Save", type="primary", use_container_width=True, disabled=not can_save, help=save_btn_help):
                with st.spinner("Saving..."):
                    success = True
                    # 1. Save modified existing entries
                    for mod in modified_existing:
                        res = api_call("POST", "timesheets/update", mod)
                        if not res or res.status_code != 200: success = False
                    
                    # 2. Save new drafts
                    for draft in st.session_state.pending_changes:
                        payload = {
                            "email": draft['email'],
                            "date_str": draft['date'],
                            "hours": draft['hours'],
                            "project_name": draft['project_name'],
                            "task_description": draft['task_description'],
                            "work_type": draft['work_type']
                        }
                        res = api_call("POST", "timesheets/entry", payload)
                        if not res or res.status_code != 200: success = False
                    
                    if success:
                        st.session_state.pending_changes = []
                        st.success("All changes saved!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Some changes failed to save.")

            # Submit Button (current_total is used for the 40h check)
            can_submit = current_total >= 40.0 and not has_pending and not modified_existing
            if submit_col.button("🚀 Submit", type="primary" if can_submit else "secondary", 
                                 use_container_width=True, disabled=not can_submit,
                                 help="Save all changes first. Requires a total of 40.0 hours to enable."):
                st.session_state.confirm_submit = True

            if st.session_state.get('confirm_submit'):
                st.warning("⚠️ **Confirm Submission:** Once submitted, you cannot edit this week's entries until an admin processes it.")
                c1, c2 = st.columns(2)
                if c1.button("✅ Yes, Submit Now", type="primary", use_container_width=True):
                    res = api_call("POST", "timesheets/submit", {"email": st.session_state.user['email'], "week_start": selected_week_str})
                    if res and res.status_code == 200:
                        st.success("Submitted successfully!")
                        st.session_state.confirm_submit = False
                        st.rerun()
                    elif res:
                        try:
                            st.error(res.json().get('detail', 'Submission failed'))
                        except:
                            st.error(f"Submission failed ({res.status_code})")
                if c2.button("❌ Cancel", use_container_width=True):
                    st.session_state.confirm_submit = False
                    st.rerun()
    

def admin_dashboard():
    # Structured Sidebar Profile
    render_sidebar_profile("Admin")

    if st.sidebar.button("Log Out", width="stretch", type="secondary"):
        st.session_state.user = None
        st.session_state.step = "login"
        st.rerun()

    st.title("Admin Dashboard")
    st.subheader("Timesheet Submissions")
    res = api_call("GET", "admin/submissions")
    if res is not None and res.status_code == 200:
        try:
            subs = res.json()
        except:
            st.error("❌ Failed to parse submissions data")
            return

        if not subs: 
            st.info("No submissions awaiting review.")
        else:
            # Group by email and week_start for aggregate review
            df = pd.DataFrame(subs)
            grouped = df.groupby(['email', 'week_start_date', 'employee_id']).agg({
                'hours': 'sum'
            }).reset_index()
            
            for _, row in grouped.iterrows():
                email = row['email']
                emp_id = row['employee_id']
                w_start = row['week_start_date']
                w_end = (datetime.fromisoformat(w_start) + timedelta(days=6)).date().isoformat()
                with st.expander(f"Employee ID: **{emp_id}** ({w_start} to {w_end})"):
                    week_entries = df[(df['email'] == email) & (df['week_start_date'] == w_start)]
                    
                    # Display entries in a professional table
                    html_rows = []
                    for _, entry in week_entries.iterrows():
                        date_fmt = datetime.fromisoformat(entry['date']).strftime("%a, %b %d") if isinstance(entry['date'], str) else entry['date'].strftime("%a, %b %d")
                        html_rows.append(f"<tr><td>{date_fmt}</td><td>{entry['hours']} hrs</td><td>{entry['project_name']}</td><td>{entry['work_type']}</td></tr>")
                    
                    st.markdown(f"""
                    <table class='ts-locked-table'>
                        <thead>
                            <tr>
                                <th class='col-date'>DATE</th><th class='col-hours'>HOURS</th><th class='col-project'>PROJECT DETAIL</th><th class='col-type'>WORK TYPE</th>
                            </tr>
                        </thead>
                        <tbody>{''.join(html_rows)}</tbody>
                    </table>
                    """, unsafe_allow_html=True)
                    
                    st.markdown(f"<div style='margin-top: 10px; font-weight: 600;'>Total Hours for Week: <span style='color: #38bdf8;'>{row['hours']} hrs</span></div>", unsafe_allow_html=True)
                    st.divider()

                    # Action Buttons
                    b1, b2 = st.columns(2)
                    
                    if b1.button("✅ Approve", key=f"appts_{email}_{w_start}", use_container_width=True):
                        res = api_call("POST", "admin/timesheets/process", {
                            "email": email, "week_start": w_start,
                            "action": "Approve", "admin_email": st.session_state.user['email'], "reason": "Approved"
                        })
                        if res is not None:
                            if res.status_code == 200:
                                st.success("Timesheet Approved!")
                                time.sleep(1)
                                st.rerun()
                            else:
                                try:
                                    error_msg = res.json().get('detail', 'Approval failed')
                                    st.error(f"❌ {error_msg}")
                                except:
                                    st.error(f"❌ Server error ({res.status_code}) during approval.")
                                    with st.expander("Debug Info"):
                                        st.code(res.text[:500])

                    if b2.button("❌ Reject", key=f"rejts_{email}_{w_start}", use_container_width=True, type="secondary"):
                        st.session_state.reject_target = {"email": email, "week_start": w_start}
                        st.rerun()

    # Rejection Modal (Simulated via Session State)
    if "reject_target" in st.session_state:
        target = st.session_state.reject_target
        st.markdown("---")
        st.warning(f"### 🚩 Correction Required\nReturning timesheet for **{target['email']}** for revision (Week: {target['week_start']})")
        reason = st.text_area("Notes for Employee", placeholder="e.g. Please clarify project details for Monday...")
        
        c1, c2 = st.columns(2)
        if c1.button("Send Back", type="primary", use_container_width=True):
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
                        time.sleep(1)
                        st.rerun()
                    else:
                        try:
                            error_msg = res.json().get('detail', 'Rejection failed')
                            st.error(f"❌ {error_msg}")
                        except:
                            st.error(f"❌ Server error ({res.status_code}) during rejection.")
                            with st.expander("Debug Info"):
                                st.code(res.text[:500])
        
        if c2.button("Cancel", use_container_width=True):
            del st.session_state.reject_target
            st.rerun()

# --- Router ---
if st.session_state.step == "login": 
    login_ui()
elif st.session_state.step == "register":
    register_ui()
elif st.session_state.step == "dashboard":
    if st.session_state.user["role"] == "Admin": 
        admin_dashboard()
    else: 
        employee_dashboard()
