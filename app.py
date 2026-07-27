import urllib.request
import re
from collections import defaultdict
from datetime import datetime, date
import calendar
import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Set calendar to start week on Sunday
calendar.setfirstweekday(calendar.SUNDAY)

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

# Custom Mobile-First CSS
st.markdown("""
    <style>
    /* Adjust top padding so title isn't clipped by Streamlit header */
    .block-container {
        padding-top: 3.5rem !important;
        padding-bottom: 2rem !important;
        padding-left: 0.8rem !important;
        padding-right: 0.8rem !important;
    }
    
    /* Responsive title fitting mobile screen width cleanly */
    .responsive-title {
        font-size: clamp(20px, 6vw, 36px) !important;
        font-weight: 800 !important;
        white-space: nowrap !important;
        margin: 0 !important;
        padding: 0 !important;
        line-height: 1.3 !important;
    }

    /* Dense Dividers & Subheadings */
    hr {
        margin: 0.8rem 0 !important;
    }
    h3 {
        font-size: 1.1rem !important;
        margin-bottom: 0.4rem !important;
        margin-top: 0.2rem !important;
    }

    /* GUARANTEED SINGLE-ROW TOOLBAR FOR MOBILE */
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

    /* Custom Mobile HTML Calendar Table */
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

    /* Yellow Highlight Badge for x2, x3 Multipliers */
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

    /* Counter Control Display Styling */
    .counter-peach-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
    }
    .counter-peach-img {
        font-size: 40px;
        line-height: 1.0;
    }
    .counter-label {
        font-size: 14px;
        color: #a1a1aa;
        font-weight: 500;
        margin-top: 4px;
    }

    /* Round Action Controls (- and +) */
    div[data-testid="stDialog"] button[key="modal_minus_btn"] {
        background-color: #2c2c2e !important;
        color: #ffffff !important;
        border-radius: 50% !important;
        width: 52px !important;
        height: 52px !important;
        font-size: 22px !important;
        border: none !important;
        margin: 0 auto !important;
    }

    div[data-testid="stDialog"] button[key="modal_plus_btn"] {
        background-color: #f59e0b !important;
        color: #000000 !important;
        border-radius: 50% !important;
        width: 52px !important;
        height: 52px !important;
        font-size: 22px !important;
        border: none !important;
        font-weight: bold !important;
        margin: 0 auto !important;
    }

    /* Compact Month Header Styling */
    .month-hdr {
        font-size: 13px !important;
        font-weight: 700 !important;
        color: #f3f4f6 !important;
        margin-bottom: 2px !important;
    }

    /* FORCE 2 COLUMNS ON MOBILE SCREENS FOR TWO-COLUMN SECTIONS */
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
    </style>
""", unsafe_allow_html=True)

ICS_URL = "https://calendar.google.com/calendar/ical/bmadams809%40gmail.com/public/basic.ics"

# 2. Google Calendar API Helper Functions
def get_calendar_service():
    if "gcp_service_account" not in st.secrets:
        raise ValueError("Google Service Account credentials not found in Streamlit Secrets.")
    
    creds_info = st.secrets["gcp_service_account"]
    credentials = service_account.Credentials.from_service_account_info(
        creds_info,
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
            service.events().delete(calendarId=calendar_id, eventId=ev_id).execute()

# 3. Fetch & Cache Data
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

stretch_goal = 223
pace_needed_stretch = round(max(0, stretch_goal - total_curr) / remaining_weeks, 2)

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

# Calculate Longest Consecutive Streak
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

if max_streak_dates:
    d_start, d_end = max_streak_dates[-1]
    streak_period_str = f"{d_start.strftime('%b %d')}–{d_end.strftime('%d, %Y')}"
else:
    streak_period_str = "—"

# Initialize Calendar Session State
if "cal_year" not in st.session_state:
    st.session_state.cal_year = current_year
if "cal_month" not in st.session_state:
    st.session_state.cal_month = current_month

# Direct State Mutation Functions
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
@st.dialog("Add a Peach 🍑")
def add_peach_modal():
    selected_dt = st.date_input("Select Date", value=today)
    
    # Get current counts for selected date
    curr_count = date_counts.get(selected_dt, 0)
    
    if "modal_target_count" not in st.session_state or st.session_state.get("modal_date_tracker") != selected_dt:
        st.session_state.modal_target_count = curr_count
        st.session_state.modal_date_tracker = selected_dt
        
    c_minus, c_display, c_plus = st.columns([1, 1.5, 1], vertical_alignment="center")
    
    with c_minus:
        if st.button("—", key="modal_minus_btn", use_container_width=True):
            if st.session_state.modal_target_count > 0:
                st.session_state.modal_target_count -= 1
                st.rerun()
                
    with c_display:
        st.markdown(f"""
            <div class="counter-peach-container">
                <div class="counter-peach-img">🍑</div>
                <div class="counter-label">Count: {st.session_state.modal_target_count}</div>
            </div>
        """, unsafe_allow_html=True)
        
    with c_plus:
        if st.button("+", key="modal_plus_btn", use_container_width=True):
            st.session_state.modal_target_count += 1
            st.rerun()
            
    st.divider()
    
    col_cancel, col_save = st.columns(2)
    
    with col_cancel:
        if st.button("✕ Cancel", key="btn_cancel_peach", use_container_width=True):
            if "modal_target_count" in st.session_state:
                del st.session_state.modal_target_count
            if "modal_date_tracker" in st.session_state:
                del st.session_state.modal_date_tracker
            st.rerun()
            
    with col_save:
        if st.button("✓ Commit", key="btn_commit_peach", use_container_width=True):
            try:
                update_peach_events(selected_dt, st.session_state.modal_target_count, raw_events)
                st.cache_data.clear()
                if "modal_target_count" in st.session_state:
                    del st.session_state.modal_target_count
                if "modal_date_tracker" in st.session_state:
                    del st.session_state.modal_date_tracker
                st.success("Updated!")
                st.rerun()
            except Exception as err:
                st.error(f"Error: {err}")

# --- 1. HEADER SECTION ---
st.markdown('<h1 class="responsive-title">🍑 PEACH TIME TRACKER</h1>', unsafe_allow_html=True)
st.caption(f"Live Calendar | Updated: {datetime.now().strftime('%b %d, %Y - %I:%M %p')}")

if st.button("🔄 Force Refresh", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

st.divider()

# --- 2. CALENDAR TOOLBAR & VIEW ---
st.subheader("📅 Calendar View")

month_display = f"{calendar.month_abbr[st.session_state.cal_month]} {st.session_state.cal_year}"

# Native Streamlit Columns forced to 1-line via CSS
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

# "Add a Peach" Button Below Calendar
if st.button("➕ Add a Peach", key="btn_open_add_modal", use_container_width=True):
    add_peach_modal()

st.divider()

# --- 3. KEY METRICS (DYNAMIC DOUBLE COLUMN) ---
st.subheader("📊 Key Metrics")

km_col_left, km_col_right = st.columns(2)

# Left Column: Dynamic Current Year Goals & Pace
with km_col_left:
    st.markdown(f'<div class="metrics-col-hdr">{current_year} Goals & Pace</div>', unsafe_allow_html=True)
    ytd_diff = total_curr - prev_ytd_count
    st.metric(f"{current_year} YTD", f"{total_curr} 🍑", delta=f"{'+' if ytd_diff > 0 else ''}{ytd_diff} vs {prev_year} YTD")
    st.metric("Weekly Pace", f"{weekly_pace} / wk")
    st.metric("4.0/Wk Goal", f"{goal_4_0} 🍑", delta=f"{pace_needed_4_0}/wk needed")
    st.metric("Stretch Goal", f"{stretch_goal} 🍑", delta=f"{pace_needed_stretch}/wk needed")

# Right Column: Lifetime Insights
with km_col_right:
    st.markdown('<div class="metrics-col-hdr">Lifetime Insights</div>', unsafe_allow_html=True)
    st.metric("Top Month", f"{top_month_str}", delta=f"{top_month_val} 🍑 recorded")
    st.metric("Top Day of Week", f"{top_day_str}", delta=f"{top_day_val} total ({top_day_pct}%)")
    st.metric("Lifetime 🍑 Total", f"{total_lifetime} 🍑", delta="All-time overall")
    st.metric("Longest Streak", f"{max_streak} Days ({streak_instances} 🍑)", delta=f"{streak_period_str}")

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
