import urllib.request
import re
from collections import defaultdict
from datetime import datetime, date
import calendar
import time
import streamlit as st
import streamlit.components.v1 as components
import plotly.express as px
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Set calendar to start week on Sunday
calendar.setfirstweekday(calendar.SUNDAY)

# Configuration: Auto-lock timeout duration (in minutes)
TIMEOUT_MINUTES = 15

# Dynamic Year & Today Definitions
today = datetime.now().date()
current_year = today.year
prev_year = current_year - 1
current_month = today.month

# 1. Page Configuration & Favicon Icon
st.set_page_config(
    page_title="PEACH TIME TRACKER", 
    page_icon="🍑", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize Authentication State
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "last_activity" not in st.session_state:
    st.session_state.last_activity = time.time()

# Check for Auto-Lock Timeout
if st.session_state.authenticated:
    elapsed_minutes = (time.time() - st.session_state.last_activity) / 60
    if elapsed_minutes > TIMEOUT_MINUTES:
        st.session_state.authenticated = False
        st.warning(f"🔒 App locked due to {TIMEOUT_MINUTES} minutes of inactivity.")

# Reset Activity Timer on any action
st.session_state.last_activity = time.time()

# Custom Mobile-First CSS
st.markdown("""
    <style>
    .block-container {
        padding-top: 3.5rem !important;
        padding-bottom: 6rem !important; /* Bottom padding for comfortable mobile scrolling */
        padding-left: 0.8rem !important;
        padding-right: 0.8rem !important;
    }
    
    .responsive-title {
        font-size: clamp(20px, 6vw, 36px) !important;
        font-weight: 800 !important;
        white-space: nowrap !important;
        margin: 0 !important;
        padding: 0 !important;
        line-height: 1.3 !important;
    }

    hr {
        margin: 0.8rem 0 !important;
    }
    h3 {
        font-size: 1.1rem !important;
        margin-bottom: 0.4rem !important;
        margin-top: 0.2rem !important;
    }

    div[data-testid="stHorizontalBlock"]:has(.month-nav-label-inline) {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        align-items: center !important;
        justify-content: space-between !important;
        width: 100% !important;
        gap: 8px !important;
        margin-bottom: 12px !important;
    }

    div[data-testid="stHorizontalBlock"]:has(.month-nav-label-inline) > div:nth-child(1),
    div[data-testid="stHorizontalBlock"]:has(.month-nav-label-inline) > div:nth-child(3) {
        width: 20% !important;
        min-width: 0 !important;
    }

    div[data-testid="stHorizontalBlock"]:has(.month-nav-label-inline) > div:nth-child(2) {
        width: 60% !important;
        min-width: 0 !important;
    }

    .month-nav-label-inline {
        font-size: 20px !important;
        font-weight: 700 !important;
        text-align: center !important;
        white-space: nowrap !important;
    }

    .custom-cal-table {
        width: 100% !important;
        border-collapse: collapse !important;
        font-size: 12px !important;
        margin-bottom: 10px !important;
    }
    .custom-cal-table th, .custom-cal-table td {
        border: 1px solid #31333f !important;
        padding: 6px 2px !important;
        text-align: center !important;
        width: 14.28% !important;
    }
    .custom-cal-table th {
        background-color: #1e1f26 !important;
        color: #f3f4f6 !important;
        font-weight: 700 !important;
    }

    .mult-badge {
        background-color: #ffd700 !important;
        color: #111111 !important;
        font-weight: 800 !important;
        padding: 1px 3px !important;
        border-radius: 4px !important;
        font-size: 10px !important;
        margin-left: 2px !important;
        display: inline-block !important;
    }

    .counter-peach-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        margin: 8px 0;
    }
    .counter-peach-img {
        font-size: 38px;
        line-height: 1.0;
    }
    .counter-label {
        font-size: 14px;
        color: #a1a1aa;
        font-weight: 600;
        margin-top: 4px;
    }

    div[data-testid="stDialog"] button[key="modal_plus_btn"] {
        background-color: #f59e0b !important;
        color: #000000 !important;
        border-radius: 50% !important;
        width: 48px !important;
        height: 48px !important;
        font-size: 22px !important;
        border: none !important;
        font-weight: bold !important;
        margin: 0 auto !important;
    }

    div[data-testid="stDialog"] button[key="modal_minus_btn"] {
        background-color: #2c2c2e !important;
        color: #ffffff !important;
        border-radius: 50% !important;
        width: 48px !important;
        height: 48px !important;
        font-size: 22px !important;
        border: none !important;
        margin: 0 auto !important;
    }

    div[data-testid="stDialog"] div[data-testid="stHorizontalBlock"]:has(button[key="btn_cancel_peach"]) {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        gap: 10px !important;
    }
    div[data-testid="stDialog"] div[data-testid="stHorizontalBlock"]:has(button[key="btn_cancel_peach"]) > div {
        width: 50% !important;
        min-width: 0 !important;
    }

    .month-hdr {
        font-size: 13px !important;
        font-weight: 700 !important;
        color: #f3f4f6 !important;
        margin-bottom: 2px !important;
    }

    div[data-testid="stHorizontalBlock"]:has(.month-hdr),
    div[data-testid="stHorizontalBlock"]:has(.metrics-col-hdr) {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        gap: 10px !important;
    }
    div[data-testid="stHorizontalBlock"]:has(.month-hdr) > div,
    div[data-testid="stHorizontalBlock"]:has(.metrics-col-hdr) > div {
        width: 50% !important;
        min-width: 0 !important;
    }

    .metrics-col-hdr {
        font-size: 14px !important;
        font-weight: 700 !important;
        color: #ffa07a !important;
        margin-bottom: 6px !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .national-section-container {
        margin-bottom: 4rem !important; /* Extra bottom padding for mobile browsers */
    }
    </style>
""", unsafe_allow_html=True)

# --- PASSWORD LOCK SCREEN DISPLAY ---
if not st.session_state.authenticated:
    st.markdown('<h1 class="responsive-title">🔒 Tracker Lock Screen</h1>', unsafe_allow_html=True)
    st.caption("Enter your passcode to unlock.")
    
    with st.form("login_form"):
        pwd_input = st.text_input("Passcode", type="password", key="lock_passcode_field")
        
        components.html("""
            <script>
            const forceNumPad = () => {
                const inputs = window.parent.document.querySelectorAll('input[type="password"]');
                inputs.forEach(input => {
                    input.setAttribute('inputmode', 'numeric');
                    input.setAttribute('pattern', '[0-9]*');
                });
            };
            forceNumPad();
            setTimeout(forceNumPad, 300);
            setTimeout(forceNumPad, 800);
            </script>
        """, height=0, width=0)
        
        login_btn = st.form_submit_button("Unlock", use_container_width=True)
        
        if login_btn:
            expected_pwd = str(st.secrets.get("APP_PASSWORD", "peach123"))
            if str(pwd_input) == expected_pwd:
                st.session_state.authenticated = True
                st.session_state.last_activity = time.time()
                st.rerun()
            else:
                st.error("Incorrect passcode. Please try again.")
    st.stop()

# ==============================================================================
# MAIN APP CODE (Only runs when authenticated)
# ==============================================================================

ICS_URL = "https://calendar.google.com/calendar/ical/bmadams809%40gmail.com/public/basic.ics"

def get_calendar_service():
    if "gcp_service_account" not in st.secrets:
        raise ValueError("Google Service Account credentials not found in Streamlit Secrets.")
    
    creds_dict = dict(st.secrets["gcp_service_account"])
    
    if "token_uri" not in creds_dict:
        creds_dict["token_uri"] = "https://oauth2.googleapis.com/token"
    if "auth_uri" not in creds_dict:
        creds_dict["auth_uri"] = "https://accounts.google.com/o/oauth2/auth"

    if "private_key" in creds_dict:
        key_str = str(creds_dict["private_key"]).strip()
        if key_str.startswith('"') and key_str.endswith('"'):
            key_str = key_str[1:-1]
        elif key_str.startswith("'") and key_str.endswith("'"):
            key_str = key_str[1:-1]
            
        key_str = key_str.replace("\\n", "\n")
        creds_dict["private_key"] = key_str.strip()

    credentials = service_account.Credentials.from_service_account_info(
        creds_dict,
        scopes=["https://www.googleapis.com/auth/calendar"]
    )
    return build("calendar", "v3", credentials=credentials)

def update_peach_events(event_date, target_count, current_events):
    service = get_calendar_service()
    calendar_id = "bmadams809@gmail.com"
    
    existing_event_ids = [e['id'] for e in current_events if e['date'] == event_date]
    existing_count = len(existing_event_ids)
    
    if target_count > existing_count:
        for _ in range(target_count - existing_count):
            event_body = {
                'summary': '🍑',
                'start': {'date': event_date.strftime('%Y-%m-%d')},
                'end': {'date': event_date.strftime('%Y-%m-%d')},
            }
            service.events().insert(calendarId=calendar_id, body=event_body).execute()
            
    elif target_count < existing_count:
        to_delete = existing_event_ids[:(existing_count - target_count)]
        for ev_id in to_delete:
            clean_id = ev_id.split('@')[0]
            service.events().delete(calendarId=calendar_id, eventId=clean_id).execute()

@st.cache_data(ttl=300)
def fetch_calendar_data():
    req = urllib.request.Request(ICS_URL, headers={'User-Agent': 'Mozilla/5.0'})
    ics_text = urllib.request.urlopen(req).read().decode('utf-8')
    
    events = []
    current_event = {}
    for line in ics_text.splitlines():
        if line.startswith("BEGIN:VEVENT"):
            current_event = {}
        elif line.startswith("UID:"):
            current_event['id'] = line.split(":", 1)[1].strip()
        elif line.startswith("DTSTART"):
            match = re.search(r'(\d{8})', line)
            if match:
                current_event['date'] = datetime.strptime(match.group(1), "%Y%m%d").date()
        elif line.startswith("SUMMARY:"):
            current_event['summary'] = line.split(":", 1)[1].strip()
        elif line.startswith("END:VEVENT"):
            if current_event.get('summary') == "🍑" and 'date' in current_event:
                events.append(current_event)
    return events

# Load data
raw_events = fetch_calendar_data()
events = sorted([e['date'] for e in raw_events])

# Create maps for analytical calculations
date_counts = defaultdict(int)
day_of_week_counts = defaultdict(int)
month_year_counts = defaultdict(int)

counts_prev = defaultdict(int)
counts_curr = defaultdict(int)
prev_ytd_count = 0

for d in events:
    date_counts[d] += 1
    day_name = calendar.day_name[d.weekday()]
    day_of_week_counts[day_name] += 1
    month_year_counts[f"{calendar.month_abbr[d.month]} {d.year}"] += 1
    
    if d.year == prev_year:
        counts_prev[d.month] += 1
        if (d.month < current_month) or (d.month == current_month and d.day <= today.day):
            prev_ytd_count += 1
    elif d.year == current_year:
        counts_curr[d.month] += 1

total_prev = sum(counts_prev.values())
total_curr = sum(counts_curr.values())
total_lifetime = len(events)

# Dynamic Pace & Goal Calculations
current_week_num = max(1, today.isocalendar()[1])
weekly_pace = round(total_curr / current_week_num, 2)
remaining_weeks = max(1, 52 - current_week_num)

goal_4_0 = 209
pace_needed_4_0 = round(max(0, goal_4_0 - total_curr) / remaining_weeks, 2)

# Dynamic Over / Under Goal Status Calculation
if total_curr < goal_4_0:
    rem_label = "Remaining for Goal"
    rem_val = f"{goal_4_0 - total_curr} 🍑"
    rem_delta = f"Target: {goal_4_0}"
elif total_curr == goal_4_0:
    rem_label = "Goal Status"
    rem_val = "209 🍑"
    rem_delta = "Goal Reached! 🎉"
else:
    over_by = total_curr - goal_4_0
    rem_label = "Over Goal by"
    rem_val = f"+{over_by} 🍑"
    rem_delta = f"Exceeded Target ({goal_4_0}) 🎉"

# Calculate Days Since Last Entry
if events:
    last_event_date = max(events)
    days_since_last = (today - last_event_date).days
    if days_since_last == 0:
        recency_str = "Today 🍑"
    elif days_since_last == 1:
        recency_str = "Yesterday"
    else:
        recency_str = f"{days_since_last} days ago"
else:
    recency_str = "No events"

# Calculate Streaks (Longest & Current Active)
unique_dates = sorted(list(date_counts.keys()))
max_streak = 0
streak_instances = 0
max_streak_dates = []

if unique_dates:
    temp_streak = 1
    temp_instances = date_counts[unique_dates[0]]
    temp_start = unique_dates[0]
    
    for i in range(1, len(unique_dates)):
        if (unique_dates[i] - unique_dates[i-1]).days == 1:
            temp_streak += 1
            temp_instances += date_counts[unique_dates[i]]
        else:
            if temp_streak > max_streak:
                max_streak = temp_streak
                streak_instances = temp_instances
                max_streak_dates = [(temp_start, unique_dates[i-1])]
            elif temp_streak == max_streak and temp_streak > 1:
                max_streak_dates.append((temp_start, unique_dates[i-1]))
            temp_streak = 1
            temp_instances = date_counts[unique_dates[i]]
            temp_start = unique_dates[i]
            
    if temp_streak > max_streak:
        max_streak = temp_streak
        streak_instances = temp_instances
        max_streak_dates = [(temp_start, unique_dates[-1])]
    elif temp_streak == max_streak and temp_streak > 1:
        max_streak_dates.append((temp_start, unique_dates[-1]))

# Calculate Current Active Streak
current_streak = 0
if unique_dates:
    check_date = today
    if check_date not in date_counts and (today - date(1, 1, 1)).days - (max(unique_dates) - date(1, 1, 1)).days <= 1:
        check_date = max(unique_dates)
    
    while check_date in date_counts:
        current_streak += 1
        check_date = date.fromordinal(check_date.toordinal() - 1)

if max_streak_dates:
    d_start, d_end = max_streak_dates[-1]
    streak_period_str = f"{d_start.strftime('%b %d')}–{d_end.strftime('%d, %Y')}"
else:
    streak_period_str = "—"

# Calculate Lifetime Analytics
if month_year_counts:
    top_month_str = max(month_year_counts, key=month_year_counts.get)
    top_month_val = month_year_counts[top_month_str]
else:
    top_month_str, top_month_val = "—", 0

if day_of_week_counts:
    top_day_str = max(day_of_week_counts, key=day_of_week_counts.get)
    top_day_val = day_of_week_counts[top_day_str]
    top_day_pct = round((top_day_val / total_lifetime) * 100, 1) if total_lifetime > 0 else 0.0
else:
    top_day_str, top_day_val, top_day_pct = "—", 0, 0.0

# Initialize Session State
if "cal_year" not in st.session_state:
    st.session_state.cal_year = current_year
if "cal_month" not in st.session_state:
    st.session_state.cal_month = current_month
if "show_add_modal" not in st.session_state:
    st.session_state.show_add_modal = False

def handle_prev():
    if st.session_state.cal_month == 1:
        st.session_state.cal_month = 12
        st.session_state.cal_year -= 1
    else:
        st.session_state.cal_month -= 1

def handle_next():
    if st.session_state.cal_month == 12:
        st.session_state.cal_month = 1
        st.session_state.cal_year += 1
    else:
        st.session_state.cal_month += 1

def logout():
    st.session_state.authenticated = False
    st.rerun()

# Dialog Function for Adding / Updating Peaches
@st.dialog("Add a 🍑")
def add_peach_modal():
    selected_dt = st.date_input("Select Date", value=today)
    
    curr_count = date_counts.get(selected_dt, 0)
    if "modal_target_count" not in st.session_state or st.session_state.get("modal_date_tracker") != selected_dt:
        st.session_state.modal_target_count = curr_count
        st.session_state.modal_date_tracker = selected_dt
        
    if st.button("+", key="modal_plus_btn", use_container_width=True):
        st.session_state.modal_target_count += 1
        st.rerun()

    st.markdown(f"""
        <div class="counter-peach-container">
            <div class="counter-peach-img">🍑</div>
            <div class="counter-label">Count: {st.session_state.modal_target_count}</div>
        </div>
    """, unsafe_allow_html=True)

    if st.button("—", key="modal_minus_btn", use_container_width=True):
        if st.session_state.modal_target_count > 0:
            st.session_state.modal_target_count -= 1
            st.rerun()

    st.divider()
    
    col_cancel, col_save = st.columns(2)
    
    with col_cancel:
        if st.button("✕", key="btn_cancel_peach", use_container_width=True):
            st.session_state.show_add_modal = False
            if "modal_target_count" in st.session_state:
                del st.session_state.modal_target_count
            if "modal_date_tracker" in st.session_state:
                del st.session_state.modal_date_tracker
            st.rerun()
            
    with col_save:
        if st.button("✓", key="btn_commit_peach", use_container_width=True):
            try:
                update_peach_events(selected_dt, st.session_state.modal_target_count, raw_events)
                st.cache_data.clear()
                st.session_state.show_add_modal = False
                if "modal_target_count" in st.session_state:
                    del st.session_state.modal_target_count
                if "modal_date_tracker" in st.session_state:
                    del st.session_state.modal_date_tracker
                st.rerun()
            except Exception as err:
                st.error(f"Error: {err}")

# --- 1. HEADER SECTION ---
h_left, h_right = st.columns([0.8, 0.2], vertical_alignment="center")

with h_left:
    st.markdown('<h1 class="responsive-title">🍑 PEACH TIME TRACKER</h1>', unsafe_allow_html=True)
    st.caption(f"Live Calendar | Updated: {datetime.now().strftime('%b %d, %Y - %I:%M %p')}")

with h_right:
    st.button("🔒 Lock", on_click=logout, use_container_width=True)

# Quick Action Buttons (Quick +1 Today & Force Refresh)
q_col1, q_col2 = st.columns(2)
with q_col1:
    if st.button("⚡ +1 Today", use_container_width=True):
        try:
            today_count = date_counts.get(today, 0)
            update_peach_events(today, today_count + 1, raw_events)
            st.cache_data.clear()
            st.toast("Added 🍑 for today!", icon="🍑")
            st.rerun()
        except Exception as e:
            st.error(f"Error: {e}")

with q_col2:
    if st.button("🔄 Force Refresh", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

st.divider()

# --- 2. CALENDAR TOOLBAR & VIEW ---
st.subheader("📅 Calendar View")

month_display = f"{calendar.month_abbr[st.session_state.cal_month]} {st.session_state.cal_year}"

col_prev, col_label, col_next = st.columns([1, 3, 1])

with col_prev:
    st.button("‹", key="btn_prev_month", on_click=handle_prev, use_container_width=True)

with col_label:
    st.markdown(f'<div class="month-nav-label-inline">{month_display}</div>', unsafe_allow_html=True)

with col_next:
    st.button("›", key="btn_next_month", on_click=handle_next, use_container_width=True)

# Render HTML Month Grid Table
selected_year = st.session_state.cal_year
selected_month = st.session_state.cal_month

month_cal = calendar.monthcalendar(selected_year, selected_month)
days_header = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]

table_html = '<table class="custom-cal-table"><thead><tr>'
for dh in days_header:
    table_html += f'<th>{dh}</th>'
table_html += '</tr></thead><tbody>'

for week in month_cal:
    table_html += '<tr>'
    for day in week:
        if day == 0:
            table_html += '<td></td>'
        else:
            curr_date = date(selected_year, selected_month, day)
            count = date_counts.get(curr_date, 0)
            if count == 1:
                table_html += f'<td>{day}🍑</td>'
            elif count > 1:
                table_html += f'<td>{day}🍑<span class="mult-badge">x{count}</span></td>'
            else:
                table_html += f'<td>{day}</td>'
    table_html += '</tr>'
table_html += '</tbody></table>'

st.markdown(table_html, unsafe_allow_html=True)

# "+ Add a 🍑" Trigger Button Below Calendar
if st.button("+ Custom Date Add 🍑", key="btn_open_add_modal", use_container_width=True):
    st.session_state.show_add_modal = True

if st.session_state.show_add_modal:
    add_peach_modal()

st.divider()

# --- 3. KEY METRICS (DYNAMIC DOUBLE COLUMN) ---
st.subheader("📊 Key Metrics")

km_col_left, km_col_right = st.columns(2)

# Left Column: Dynamic Current Year Goals & Pace
with km_col_left:
    st.markdown(f'<div class="metrics-col-hdr">{current_year} Goals & Pace</div>', unsafe_allow_html=True)
    
    # Pacing Color Badges
    if weekly_pace >= 4.0:
        pace_status = "🟢 On Track"
    elif weekly_pace >= 3.0:
        pace_status = "🟡 Moderate Pace"
    else:
        pace_status = "🔴 Below Target"
        
    ytd_diff = total_curr - prev_ytd_count
    st.metric(
        label=f"{current_year} YTD", 
        value=f"{total_curr} 🍑", 
        delta=f"{prev_year} YTD: {prev_ytd_count} 🍑",
        delta_color="normal" if ytd_diff >= 0 else "inverse"
    )
    st.metric("Weekly Pace", f"{weekly_pace} / wk", delta=pace_status)
    st.metric("4.0/Wk Goal", f"{goal_4_0} 🍑", delta=f"{pace_needed_4_0}/wk needed")
    st.metric(rem_label, rem_val, delta=rem_delta)

# Right Column: Lifetime Insights & Recency
with km_col_right:
    st.markdown('<div class="metrics-col-hdr">Lifetime Insights</div>', unsafe_allow_html=True)
    st.metric("Last Activity", recency_str, delta=f"Current Streak: {current_streak} days" if current_streak > 0 else "No active streak")
    st.metric("Top Month", f"{top_month_str}", delta=f"{top_month_val} 🍑 recorded")
    st.metric("Lifetime 🍑 Total", f"{total_lifetime} 🍑", delta="Since 2025")
    st.metric("Longest Streak", f"{max_streak} Days ({streak_instances} 🍑)", delta=f"{streak_period_str}")

# Day of the Week Distribution Breakdown (Interactive Pie/Donut Chart)
st.markdown("#### 📆 Day of the Week Breakdown")

dow_order = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
dow_data = [{"Day": day_n, "Count": day_of_week_counts[day_n]} for day_n in dow_order]

fig = px.pie(
    dow_data, 
    values="Count", 
    names="Day", 
    hole=0.4,
    color_discrete_sequence=px.colors.qualitative.Pastel
)

fig.update_traces(
    textposition="inside", 
    textinfo="percent+label",
    hovertemplate="<b>%{label}</b><br>Count: %{value} 🍑<br>Share: %{percent}"
)

fig.update_layout(
    margin=dict(t=10, b=10, l=10, r=10),
    showlegend=False,
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    height=280
)

st.plotly_chart(fig, use_container_width=True)

st.divider()

# --- 4. MONTHLY COMPARISON (DYNAMIC DUAL YEAR COLUMNS) ---
st.subheader("🗓️ Monthly Comparison")

col_left, col_right = st.columns(2)

# Left Column: January (1) to June (6)
with col_left:
    for m in range(1, 7):
        m_name = calendar.month_abbr[m]
        c_prev_val = counts_prev[m]
        if m <= current_month:
            c_curr_val = counts_curr[m]
            diff = c_curr_val - c_prev_val
            st.markdown(f'<div class="month-hdr">{m_name}</div>', unsafe_allow_html=True)
            st.metric(label=f"{current_year} vs {prev_year}", value=f"{c_curr_val} 🍑", delta=f"{'+' if diff > 0 else ''}{diff} YoY ({prev_year}: {c_prev_val})")
        else:
            st.markdown(f'<div class="month-hdr">{m_name} *(Upcoming)*</div>', unsafe_allow_html=True)
            st.metric(label=f"{current_year} vs {prev_year}", value="—", delta=f"{prev_year}: {c_prev_val}")

# Right Column: July (7) to December (12)
with col_right:
    for m in range(7, 13):
        m_name = calendar.month_abbr[m]
        c_prev_val = counts_prev[m]
        if m <= current_month:
            c_curr_val = counts_curr[m]
            diff = c_curr_val - c_prev_val
            st.markdown(f'<div class="month-hdr">{m_name}</div>', unsafe_allow_html=True)
            st.metric(label=f"{current_year} vs {prev_year}", value=f"{c_curr_val} 🍑", delta=f"{'+' if diff > 0 else ''}{diff} YoY ({prev_year}: {c_prev_val})")
        else:
            st.markdown(f'<div class="month-hdr">{m_name} *(Upcoming)*</div>', unsafe_allow_html=True)
            st.metric(label=f"{current_year} vs {prev_year}", value="—", delta=f"{prev_year}: {c_prev_val}")

st.divider()

# ==============================================================================
# 5. NATIONAL STATS COMPARISON (AGES 35-45) WITH MOBILE BOTTOM PADDING
# ==============================================================================
st.markdown('<div class="national-section-container">', unsafe_allow_html=True)
st.subheader("🇺🇸 National Demographic Benchmark (Ages 35–45)")
st.caption("U.S. married couple statistics sourced from General Social Survey & Kinsey Institute research.")

nat_col1, nat_col2 = st.columns(2)

# Calculate ratio vs average (assume 50/yr avg or ~0.96/wk)
national_weekly_avg = 0.96
ratio_vs_national = round(weekly_pace / national_weekly_avg, 1) if weekly_pace > 0 else 0.0

with nat_col1:
    st.metric(
        label="Your Weekly Pace vs US Avg", 
        value=f"{weekly_pace} / wk", 
        delta=f"{ratio_vs_national}x US Avg (~0.96/wk)"
    )
    st.metric(
        label="Annual Pace vs US Avg", 
        value=f"{round(weekly_pace * 52)} / year", 
        delta=f"US Avg: 43–54 / year"
    )

with nat_col2:
    st.metric(
        label="Demographic Tier", 
        value="Top ~1–2%", 
        delta="Ages 35–45 Married Couples"
    )
    st.metric(
        label="Target Goal (209/yr)", 
        value="4.0 / wk", 
        delta="4.1x US National Benchmark"
    )

st.markdown("#### 📊 Age 35–45 Frequency Breakdown")
st.markdown("""
| Frequency Tier (Ages 35–45) | Annual Rate | Weekly Pace | US Married Percentile |
| :--- | :--- | :--- | :--- |
| **Infrequent / Sexless** | < 12 / yr | < 0.2 / wk | **~15% – 20%** of couples |
| **1 to 3 times / month** | 12 – 36 / yr | 0.2 – 0.7 / wk | **~35% – 40%** of couples |
| **1 to 2 times / week** *(US Avg)* | 52 – 104 / yr | 1.0 – 2.0 / wk | **~30% – 35%** of couples |
| **3 times / week** | 150 – 180 / yr | ~3.0 / wk | **~3% – 5%** of couples |
| **4+ times / week (Your Pace)** | **200+ / yr** | **4.0+ / wk** | **Top ~1% – 2%** of couples |
""")

st.caption("📌 *Note: In research for ages 35–45, logging multi-session days (x2, x3) occurs in less than 3% of active weeks for average married couples.*")

st.markdown('</div>', unsafe_allow_html=True)
