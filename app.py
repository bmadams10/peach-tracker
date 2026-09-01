import urllib.request
import re
from collections import defaultdict
from datetime import datetime, date
import calendar
import time
from zoneinfo import ZoneInfo
import streamlit as st
import streamlit.components.v1 as components
import plotly.express as px
from google.oauth2 import service_account
from googleapiclient.discovery import build

import auth

# Set calendar to start week on Sunday
calendar.setfirstweekday(calendar.SUNDAY)

# Dynamic Year & Today Definitions (Enforced US Central Timezone)
central_tz = ZoneInfo("America/Chicago")
today = datetime.now(central_tz).date()
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

# Initialize & Enforce Multi-User Authentication
auth.init_auth_state()
auth.check_session_timeout()

# Custom Mobile-First CSS
st.markdown("""
    <style>
    .block-container {
        padding-top: 3.5rem !important;
        padding-bottom: 6rem !important;
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

    div[data-testid="stHorizontalBlock"]:has(.metrics-col-hdr) {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        gap: 10px !important;
    }
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

    /* Custom Lifetime Goal Card & Doubled Progress Bar Styling */
    .lifetime-progress-card {
        background-color: #1e1f26;
        border: 1px solid #31333f;
        border-radius: 10px;
        padding: 14px 16px;
        margin-top: 10px;
        margin-bottom: 8px;
    }
    .lifetime-card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
    }
    .lifetime-title {
        font-size: 14px;
        font-weight: 700;
        color: #f3f4f6;
    }
    .lifetime-sub {
        font-size: 12px;
        color: #ffa07a;
        font-weight: 600;
    }
    .lifetime-progress-container {
        background-color: #2c2c2e;
        border-radius: 12px;
        height: 24px;
        width: 100%;
        position: relative;
        overflow: visible;
    }
    .lifetime-progress-fill {
        background: linear-gradient(90deg, #1d4ed8, #3b82f6);
        height: 100%;
        border-radius: 12px;
        position: relative;
    }
    .lifetime-progress-peach {
        position: absolute;
        right: -10px;
        top: 50%;
        transform: translateY(-50%);
        font-size: 18px;
        line-height: 1;
        z-index: 2;
    }
    .milestone-ticks {
        display: flex;
        justify-content: space-between;
        font-size: 10px;
        color: #a1a1aa;
        margin-top: 8px;
        font-weight: 600;
    }

    .bench-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 10px;
        margin-top: 10px;
        margin-bottom: 16px;
    }
    @media (max-width: 600px) {
        .bench-grid {
            grid-template-columns: 1fr;
        }
    }
    .bench-card {
        background-color: #1e1f26;
        border: 1px solid #31333f;
        border-radius: 8px;
        padding: 12px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .bench-title {
        font-size: 12px;
        color: #a1a1aa;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 4px;
    }
    .bench-val {
        font-size: 22px;
        font-weight: 800;
        color: #f3f4f6;
    }
    .bench-sub {
        font-size: 12px;
        color: #ffa07a;
        margin-top: 4px;
        font-weight: 600;
    }

    .national-section-container {
        margin-bottom: 2rem !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- LOCK SCREEN ENFORCEMENT ---
if not st.session_state.authenticated_user:
    auth.render_login_screen()
    st.stop()

# Refresh Activity Timer on active user interaction
auth.update_activity_timer()
current_user = st.session_state.authenticated_user

# ==============================================================================
# MAIN APP CODE (Only runs when authenticated)
# ==============================================================================

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
        # Clean up quotes if wrapped
        if (key_str.startswith('"') and key_str.endswith('"')) or (key_str.startswith("'") and key_str.endswith("'")):
            key_str = key_str[1:-1]
        
        # Ensure proper PEM newline formatting
        key_str = key_str.replace("\\n", "\n")
        if "BEGIN PRIVATE KEY" in key_str and not key_str.endswith("\n"):
            key_str += "\n"
            
        creds_dict["private_key"] = key_str

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
    service = get_calendar_service()
    calendar_id = "bmadams809@gmail.com"
    
    events = []
    page_token = None
    
    # Query Google Calendar API directly back to 2009-01-01
    while True:
        events_result = service.events().list(
            calendarId=calendar_id,
            timeMin="2009-01-01T00:00:00Z",
            q="🍑",
            singleEvents=True,
            orderBy="startTime",
            pageToken=page_token
        ).execute()
        
        items = events_result.get('items', [])
        for item in items:
            if item.get('summary') == "🍑":
                start_date_str = item['start'].get('date') or item['start'].get('dateTime', '')[:10]
                if start_date_str:
                    event_dt = datetime.strptime(start_date_str, "%Y-%m-%d").date()
                    events.append({
                        'id': item['id'],
                        'date': event_dt,
                        'summary': item.get('summary')
                    })
                    
        page_token = events_result.get('nextPageToken')
        if not page_token:
            break
            
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
    month_year_counts[f"{calendar.month_abbr[d.month]} {d.year}"] += 1
    
    # Day of the Week filter: Only count entries from current_year and prev_year
    if d.year in (current_year, prev_year):
        day_name = calendar.day_name[d.weekday()]
        day_of_week_counts[day_name] += 1
    
    if d.year == prev_year:
        counts_prev[d.month] += 1
        if (d.month < current_month) or (d.month == current_month and d.day <= today.day):
            prev_ytd_count += 1
    elif d.year == current_year:
        counts_curr[d.month] += 1

total_prev = sum(counts_prev.values())
total_curr = sum(counts_curr.values())
total_lifetime = len(events)

# Lifetime Goal Progress Calculations
lifetime_target = 10000
next_milestone = ((total_lifetime // 1000) + 1) * 1000
next_milestone = min(next_milestone, lifetime_target)
lifetime_pct = min(1.0, total_lifetime / lifetime_target)
lifetime_pct_str = f"{round(lifetime_pct * 100, 1)}%"
fill_width_css = f"{round(lifetime_pct * 100, 2)}%"

# Dynamic Pace & Goal Calculations
current_week_num = max(1, today.isocalendar()[1])
weekly_pace = round(total_curr / current_week_num, 2)
remaining_weeks = max(1, 52 - current_week_num)

goal_4_0 = 209

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

# --- MILESTONE CELEBRATIONS ---
if total_curr >= goal_4_0 and "celebrated_goal" not in st.session_state:
    st.balloons()
    st.toast("🎉 AMAZING! You hit your 4.0/wk annual goal of 209 🍑!", icon="🍑")
    st.session_state.celebrated_goal = True

if total_prev > 0 and total_curr > total_prev and "celebrated_prev_year" not in st.session_state:
    st.balloons()
    st.toast(f"🚀 MILESTONE! You officially passed {prev_year}'s total of {total_prev} 🍑!", icon="🔥")
    st.session_state.celebrated_prev_year = True

# --- 1. CONSECUTIVE DAILY STREAK LOGIC ---
unique_dates = sorted(list(date_counts.keys()))
max_streak_peaches = 0
max_streak_days = 0
max_streak_dates = []

if unique_dates:
    temp_days = 1
    temp_peaches = date_counts[unique_dates[0]]
    temp_start = unique_dates[0]
    
    for i in range(1, len(unique_dates)):
        if (unique_dates[i] - unique_dates[i-1]).days == 1:
            temp_days += 1
            temp_peaches += date_counts[unique_dates[i]]
        else:
            if temp_peaches > max_streak_peaches:
                max_streak_peaches = temp_peaches
                max_streak_days = temp_days
                max_streak_dates = [(temp_start, unique_dates[i-1])]
            elif temp_peaches == max_streak_peaches and temp_peaches > 0:
                max_streak_dates.append((temp_start, unique_dates[i-1]))
            
            temp_days = 1
            temp_peaches = date_counts[unique_dates[i]]
            temp_start = unique_dates[i]
            
    if temp_peaches > max_streak_peaches:
        max_streak_peaches = temp_peaches
        max_streak_days = temp_days
        max_streak_dates = [(temp_start, unique_dates[-1])]
    elif temp_peaches == max_streak_peaches and temp_peaches > 0:
        max_streak_dates.append((temp_start, unique_dates[-1]))

# Current Active Consecutive Streak
current_streak_peaches = 0
current_streak_days = 0
if unique_dates:
    check_date = today
    if check_date not in date_counts and (today - max(unique_dates)).days <= 1:
        check_date = max(unique_dates)
    
    while check_date in date_counts:
        current_streak_peaches += date_counts[check_date]
        current_streak_days += 1
        check_date = date.fromordinal(check_date.toordinal() - 1)

if max_streak_dates:
    d_start, d_end = max_streak_dates[-1]
    streak_period_str = f"{d_start.strftime('%b %d')}–{d_end.strftime('%b %d, %Y')}" if d_start != d_end else f"{d_start.strftime('%b %d, %Y')}"
else:
    streak_period_str = "—"

# --- 2. MOST PEACHES IN A WEEK LOGIC (SUNDAY TO SATURDAY) ---
weekly_peach_counts = defaultdict(int)
for event_date, count in date_counts.items():
    days_since_sunday = (event_date.weekday() + 1) % 7
    week_start_sunday = date.fromordinal(event_date.toordinal() - days_since_sunday)
    weekly_peach_counts[week_start_sunday] += count

if weekly_peach_counts:
    top_week_sunday = max(weekly_peach_counts, key=weekly_peach_counts.get)
    max_weekly_peaches = weekly_peach_counts[top_week_sunday]
    top_week_sat = date.fromordinal(top_week_sunday.toordinal() + 6)
    max_weekly_period_str = f"{top_week_sunday.strftime('%b %d')}–{top_week_sat.strftime('%b %d, %Y')}"
else:
    max_weekly_peaches = 0
    max_weekly_period_str = "—"

# Days Ago Last Activity Calculation
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
    st.caption(f"Logged in as **{current_user['name']}** | Updated: {datetime.now(central_tz).strftime('%b %d, %Y - %I:%M %p')}")

with h_right:
    st.button("🔒 Lock", on_click=auth.logout, use_container_width=True)

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

# Left Column: Current Year Goals, Pace & Last Activity
with km_col_left:
    st.markdown(f'<div class="metrics-col-hdr">{current_year} Goals & Pace</div>', unsafe_allow_html=True)
    
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
    st.metric(rem_label, rem_val, delta=rem_delta)
    
    active_streak_delta = f"Streak: {current_streak_peaches} 🍑 ({current_streak_days}d)" if current_streak_peaches > 0 else "No active streak"
    st.metric("Last Activity", recency_str, delta=active_streak_delta)

# Right Column: Lifetime Insights, Peaks & Streaks
with km_col_right:
    st.markdown('<div class="metrics-col-hdr">Lifetime Insights</div>', unsafe_allow_html=True)
    
    st.metric("Lifetime 🍑 Total", f"{total_lifetime:,} 🍑", delta=f"Next Milestone: {next_milestone:,} 🍑")
    st.metric("Top Month", f"{top_month_str}", delta=f"{top_month_val} 🍑 recorded")
    st.metric("Most 🍑 in a Week", f"{max_weekly_peaches} 🍑", delta=f"{max_weekly_period_str}")
    st.metric("Longest Streak", f"{max_streak_peaches} 🍑 ({max_streak_days} Days)", delta=f"{streak_period_str}")

st.divider()

# --- 4. DEDICATED LIFETIME PROGRESS SECTION ---
st.markdown(f"""
    <div class="lifetime-progress-card">
        <div class="lifetime-card-header">
            <span class="lifetime-title">🏆 Lifetime Goal Progress</span>
            <span class="lifetime-sub">{total_lifetime:,} / {lifetime_target:,} 🍑 ({lifetime_pct_str})</span>
        </div>
        <div class="lifetime-progress-container">
            <div class="lifetime-progress-fill" style="width: {fill_width_css};">
                <span class="lifetime-progress-peach">🍑</span>
            </div>
        </div>
        <div class="milestone-ticks">
            <span>0</span>
            <span>1k</span>
            <span>2k</span>
            <span>3k</span>
            <span>4k</span>
            <span>5k</span>
            <span>6k</span>
            <span>7k</span>
            <span>8k</span>
            <span>9k</span>
            <span>10k 🍑</span>
        </div>
    </div>
""", unsafe_allow_html=True)

st.divider()

# --- 5. DAY OF THE WEEK BREAKDOWN ---
st.markdown(f"#### 📆 Day of the Week Breakdown ({prev_year}–{current_year})")

dow_order = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
dow_data = [{"Day": day_n, "Count": day_of_week_counts[day_n]} for day_n in dow_order]

fig_dow = px.pie(
    dow_data, 
    values="Count", 
    names="Day", 
    hole=0.4,
    color_discrete_sequence=px.colors.qualitative.Pastel
)

fig_dow.update_traces(
    textposition="inside", 
    textinfo="percent+label",
    hovertemplate="<b>%{label}</b><br>Count: %{value} 🍑<br>Share: %{percent}"
)

fig_dow.update_layout(
    margin=dict(t=10, b=10, l=10, r=10),
    showlegend=False,
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    height=280
)

st.plotly_chart(fig_dow, use_container_width=True, config={'displayModeBar': False})

st.divider()

# --- 6. MONTHLY COMPARISON (GROUPED DOUBLE BAR CHART) ---
st.subheader(f"🗓️ Monthly Comparison ({prev_year} vs {current_year})")

monthly_chart_data = []
for m in range(1, 13):
    m_name = calendar.month_abbr[m]
    monthly_chart_data.append({"Month": m_name, "Year": str(prev_year), "Count": counts_prev[m]})
    c_val = counts_curr[m] if m <= current_month else 0
    monthly_chart_data.append({"Month": m_name, "Year": str(current_year), "Count": c_val})

fig_monthly = px.bar(
    monthly_chart_data,
    x="Month",
    y="Count",
    color="Year",
    text="Count",
    barmode="group",
    color_discrete_map={
        str(prev_year): "#6366f1",
        str(current_year): "#f59e0b"
    }
)

fig_monthly.update_traces(
    textposition="outside",
    textfont=dict(color="#f3f4f6", size=11),
    hovertemplate="<b>%{x} %{fullData.name}</b><br>Count: %{y} 🍑<extra></extra>"
)

fig_monthly.update_xaxes(fixedrange=True)
fig_monthly.update_yaxes(fixedrange=True)

fig_monthly.update_layout(
    margin=dict(t=30, b=10, l=10, r=10),
    xaxis_title=None,
    yaxis_title=None,
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1,
        title=None
    ),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    height=320,
    bargap=0.2,
    bargroupgap=0.1
)

st.plotly_chart(fig_monthly, use_container_width=True, config={'displayModeBar': False})

st.divider()

# ==============================================================================
# 7. NATIONAL STATS COMPARISON (AGES 35-45) WITH CLEAN MOBILE CARDS
# ==============================================================================
st.markdown('<div class="national-section-container">', unsafe_allow_html=True)
st.subheader("🇺🇸 National Benchmark (Ages 35–45)")
st.caption("U.S. married couple data sourced from General Social Survey & Kinsey Institute statistics.")

national_weekly_avg = 0.96
ratio_vs_national = round(weekly_pace / national_weekly_avg, 1) if weekly_pace > 0 else 0.0
projected_annual = round(weekly_pace * 52)

# Calculate National YTD Average through current week number
national_ytd_avg = round(0.96 * current_week_num)
ytd_ratio_vs_national = round(total_curr / national_ytd_avg, 1) if national_ytd_avg > 0 else 1.0

st.markdown(f"""
    <div class="bench-grid">
        <div class="bench-card">
            <div class="bench-title">Weekly Pace Comparison</div>
            <div class="bench-val">{weekly_pace} / wk</div>
            <div class="bench-sub">{ratio_vs_national}x National Average (~0.96/wk)</div>
        </div>
        <div class="bench-card">
            <div class="bench-title">Annual Rate Comparison</div>
            <div class="bench-val">~{projected_annual} / yr</div>
            <div class="bench-sub">US National Average: 43–54 / yr</div>
        </div>
        <div class="bench-card">
            <div class="bench-title">National Percentile Tier</div>
            <div class="bench-val">Top ~1–2%</div>
            <div class="bench-sub">Among US Married Couples (35–45)</div>
        </div>
        <div class="bench-card">
            <div class="bench-title">Current YTD</div>
            <div class="bench-val">{total_curr} 🍑</div>
            <div class="bench-sub">{ytd_ratio_vs_national}x US YTD Average ({national_ytd_avg})</div>
        </div>
    </div>
""", unsafe_allow_html=True)

st.markdown("#### 📊 Age 35–45 Demographic Breakdown")
st.markdown("""
| Frequency Tier | Annual Rate | Weekly Pace | US Married Percentile |
| :--- | :--- | :--- | :--- |
| **Infrequent / Sexless** | < 12 / yr | < 0.2 / wk | **~15% – 20%** of couples |
| **1 to 3 times / month** | 12 – 36 / yr | 0.2 – 0.7 / wk | **~35% – 40%** of couples |
| **1 to 2 times / week** *(US Avg)* | 52 – 104 / yr | 1.0 – 2.0 / wk | **~30% – 35%** of couples |
| **3 times / week** | 150 – 180 / yr | ~3.0 / wk | **~3% – 5%** of couples |
| **4+ times / week (Your Pace)** | **200+ / yr** | **4.0+ / wk** | **Top ~1% – 2%** of couples |
""")

st.caption("📌 *Note: For couples aged 35–45, logging multi-session days (x2, x3) occurs in under 3% of active weeks for average married households.*")

st.markdown('</div>', unsafe_allow_html=True)

st.divider()

# ==============================================================================
# 8. DYNAMIC PHYSICS BOX (YEAR-TO-DATE 🍑 VISUALIZER)
# ==============================================================================
st.subheader("🫨 Play with your 🍑s")
st.caption(f"Play with all {total_curr} 🍑s in {current_year}. —click or tap inside to stir!")

physics_box_html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{
            margin: 0;
            padding: 0;
            background: transparent;
            overflow: hidden;
            font-family: sans-serif;
        }}
        .physics-container {{
            width: 100%;
            height: 380px;
            background-color: #1e1f26;
            border: 2px solid #31333f;
            border-radius: 12px;
            box-sizing: border-box;
            position: relative;
            overflow: hidden;
            touch-action: none;
        }}
        canvas {{
            display: block;
            width: 100%;
            height: 100%;
        }}
    </style>
</head>
<body>
    <div class="physics-container">
        <canvas id="peachCanvas"></canvas>
    </div>

    <script>
        const canvas = document.getElementById('peachCanvas');
        const ctx = canvas.getContext('2d');

        function resizeCanvas() {{
            canvas.width = canvas.parentElement.clientWidth;
            canvas.height = canvas.parentElement.clientHeight;
        }}
        resizeCanvas();
        window.addEventListener('resize', resizeCanvas);

        const count = {total_curr};
        const peaches = [];
        const radius = 14; 
        const drag = 0.985; // Viscous drag (slows velocity down like in water)

        for (let i = 0; i < count; i++) {{
            peaches.push({{
                x: Math.random() * (canvas.width - radius * 4) + radius * 2,
                y: Math.random() * (canvas.height - radius * 4) + radius * 2,
                vx: (Math.random() - 0.5) * 1.5,
                vy: (Math.random() - 0.5) * 1.5,
                radius: radius
            }});
        }}

        function updatePhysics() {{
            const w = canvas.width;
            const h = canvas.height;

            for (let i = 0; i < peaches.length; i++) {{
                let p = peaches[i];

                // Apply viscous drag & subtle drift (underwater feel)
                p.vx *= drag;
                p.vy *= drag;
                p.vx += (Math.random() - 0.5) * 0.08;
                p.vy += (Math.random() - 0.5) * 0.08;

                p.x += p.vx;
                p.y += p.vy;

                // Wall collisions
                if (p.x - p.radius < 0) {{
                    p.x = p.radius;
                    p.vx *= -0.6;
                }} else if (p.x + p.radius > w) {{
                    p.x = w - p.radius;
                    p.vx *= -0.6;
                }}

                if (p.y - p.radius < 0) {{
                    p.y = p.radius;
                    p.vy *= -0.6;
                }} else if (p.y + p.radius > h) {{
                    p.y = h - p.radius;
                    p.vy *= -0.6;
                }}

                // Particle collisions
                for (let j = i + 1; j < peaches.length; j++) {{
                    let p2 = peaches[j];
                    let dx = p2.x - p.x;
                    let dy = p2.y - p.y;
                    let dist = Math.hypot(dx, dy);
                    let minDist = p.radius + p2.radius;

                    if (dist < minDist && dist > 0) {{
                        let nx = dx / dist;
                        let ny = dy / dist;

                        let overlap = minDist - dist;
                        p.x -= nx * overlap * 0.5;
                        p.y -= ny * overlap * 0.5;
                        p2.x += nx * overlap * 0.5;
                        p2.y += ny * overlap * 0.5;

                        let kx = p.vx - p2.vx;
                        let ky = p.vy - p2.vy;
                        let p_val = (nx * kx + ny * ky) * 0.8;

                        p.vx -= p_val * nx;
                        p.vy -= p_val * ny;
                        p2.vx += p_val * nx;
                        p2.vy += p_val * ny;
                    }}
                }}
            }}
        }}

        function render() {{
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.font = '22px serif';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';

            for (let p of peaches) {{
                ctx.fillText('🍑', p.x, p.y);
            }}
        }}

        function loop() {{
            updatePhysics();
            render();
            requestAnimationFrame(loop);
        }}
        loop();

        // Underwater pulse/shockwave interaction on click or tap
        canvas.addEventListener('pointerdown', (e) => {{
            const rect = canvas.getBoundingClientRect();
            const clickX = e.clientX - rect.left;
            const clickY = e.clientY - rect.top;

            for (let p of peaches) {{
                let dx = p.x - clickX;
                let dy = p.y - clickY;
                let dist = Math.hypot(dx, dy);
                if (dist < 160) {{
                    let force = (160 - dist) / 25;
                    let angle = Math.atan2(dy, dx);
                    p.vx += Math.cos(angle) * force;
                    p.vy += Math.sin(angle) * force;
                }}
            }}
        }});
    </script>
</body>
</html>
"""

components.html(physics_box_html, height=400)
