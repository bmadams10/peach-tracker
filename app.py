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
    page_title="PeachTime", 
    page_icon="🍑", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom Mobile-First CSS
st.markdown("""
    <style>
    /* Dark Theme Setup */
    .stApp {
        background-color: #0d0d0d !important;
    }

    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 2rem !important;
        padding-left: 0.8rem !important;
        padding-right: 0.8rem !important;
    }

    /* PeachTime Native Header Title */
    .app-title-container {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 1rem;
    }
    .responsive-title {
        font-size: 22px !important;
        font-weight: 700 !important;
        color: #d1d1d1 !important;
        margin: 0 !important;
    }

    /* Single-Row Navigation Toolbar */
    div[data-testid="stHorizontalBlock"]:has(.month-nav-label-inline) {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        align-items: center !important;
        justify-content: space-between !important;
        width: 100% !important;
        margin-bottom: 16px !important;
    }

    .month-nav-label-inline {
        font-size: 17px !important;
        font-weight: 500 !important;
        color: #8e8e93 !important;
        text-align: center !important;
    }

    /* Borderless Grid Setup */
    div[data-testid="stHorizontalBlock"]:has(.weekday-hdr),
    div[data-testid="stHorizontalBlock"]:has(.cal-date-btn) {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        gap: 0px !important;
    }

    div[data-testid="stHorizontalBlock"]:has(.weekday-hdr) > div,
    div[data-testid="stHorizontalBlock"]:has(.cal-date-btn) > div {
        width: 14.28% !important;
        min-width: 0 !important;
    }

    .weekday-hdr {
        text-align: center;
        font-weight: 500;
        font-size: 13px;
        color: #48484a;
        padding-bottom: 8px;
    }

    /* Clean Transparent Date Buttons */
    .cal-date-btn button {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        color: #d1d1d6 !important;
        font-size: 15px !important;
        font-weight: 400 !important;
        height: 50px !important;
        width: 100% !important;
        padding: 0 !important;
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        justify-content: center !important;
        line-height: 1.1 !important;
    }

    /* Today Active Circular Badge */
    .cal-date-btn-today button {
        background-color: #3a4b6e !important;
        color: #ffffff !important;
        border-radius: 50% !important;
        width: 36px !important;
        height: 36px !important;
        margin: 0 auto !important;
    }

    /* Pop-Up Modal Styling matching screenshot */
    div[data-testid="stModal"] > div {
        background-color: #121212 !important;
        border-radius: 24px 24px 0 0 !important;
        border: none !important;
        color: #ffffff !important;
        padding: 20px !important;
    }

    .modal-title-custom {
        text-align: center;
        font-size: 18px;
        font-weight: 700;
        color: #ffffff;
        margin-bottom: 20px;
    }

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
        font-size: 13px;
        color: #8e8e93;
        font-weight: 500;
        margin-top: 4px;
    }

    /* Round Action Controls (- and +) */
    div[data-testid="stDialog"] button[key="modal_minus_btn"] {
        background-color: #2c2c2e !important;
        color: #8e8e93 !important;
        border-radius: 50% !important;
        width: 56px !important;
        height: 56px !important;
        font-size: 24px !important;
        border: none !important;
        margin: 0 auto !important;
    }

    div[data-testid="stDialog"] button[key="modal_plus_btn"] {
        background-color: #f59e0b !important;
        color: #000000 !important;
        border-radius: 50% !important;
        width: 56px !important;
        height: 56px !important;
        font-size: 24px !important;
        border: none !important;
        font-weight: bold !important;
        margin: 0 auto !important;
    }

    .modal-subtext {
        text-align: center;
        font-size: 10px;
        color: #48484a;
        margin-top: 25px;
    }

    .metrics-col-hdr {
        font-size: 14px !important;
        font-weight: 700 !important;
        color: #ffa07a !important;
        margin-bottom: 6px !important;
        text-transform: uppercase;
    }

    .month-hdr {
        font-size: 13px !important;
        font-weight: 700 !important;
        color: #f3f4f6 !important;
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

# Active Selected Date for Edit Modal
if "active_date" not in st.session_state:
    st.session_state.active_date = None

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

# --- 1. HEADER SECTION ---
st.markdown("""
    <div class="app-title-container">
        <div class="responsive-title">PeachTime</div>
    </div>
""", unsafe_allow_html=True)

# --- 2. CALENDAR TOOLBAR & BORDERLESS GRID ---
month_display = f"{calendar.month_name[st.session_state.cal_month]} {st.session_state.cal_year}"

col_prev, col_label, col_next = st.columns([1, 4, 1])

with col_prev:
    st.button("‹", key="btn_prev_month", on_click=handle_prev, use_container_width=True)

with col_label:
    st.markdown(f'<div class="month-nav-label-inline">{month_display}</div>', unsafe_allow_html=True)

with col_next:
    st.button("›", key="btn_next_month", on_click=handle_next, use_container_width=True)

# Render Weekday Headers
days_header = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
hdr_cols = st.columns(7)
for idx, dh in enumerate(days_header):
    hdr_cols[idx].markdown(f'<div class="weekday-hdr">{dh}</div>', unsafe_allow_html=True)

# Render Borderless Calendar Grid
selected_year = st.session_state.cal_year
selected_month = st.session_state.cal_month
month_cal = calendar.monthcalendar(selected_year, selected_month)

for week in month_cal:
    week_cols = st.columns(7)
    for i, day in enumerate(week):
        with week_cols[i]:
            if day == 0:
                st.write("")
            else:
                curr_date = date(selected_year, selected_month, day)
                count = date_counts.get(curr_date, 0)
                
                # Format Peach Subtext
                peach_str = "🍑" * min(count, 2) if count > 0 else ""
                btn_label = f"{day}\n{peach_str}" if peach_str else f"{day}"
                
                # CSS Class Selector
                css_class = "cal-date-btn"
                if curr_date == today:
                    css_class += " cal-date-btn-today"
                
                st.markdown(f'<div class="{css_class}">', unsafe_allow_html=True)
                if st.button(btn_label, key=f"day_{curr_date}", use_container_width=True):
                    st.session_state.active_date = curr_date
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

# --- 3. EXACT MODAL OVERLAY (MATCHING SCREENSHOT) ---
if st.session_state.active_date is not None:
    target_dt = st.session_state.active_date
    current_cnt = date_counts.get(target_dt, 0)
    
    @st.dialog(" ")
    def edit_modal():
        st.markdown(f'<div class="modal-title-custom">{target_dt.strftime("%B %d, %Y")}</div>', unsafe_allow_html=True)
        
        c_minus, c_display, c_plus = st.columns([1, 1.5, 1], vertical_alignment="center")
        
        with c_minus:
            if st.button("—", key="modal_minus_btn", use_container_width=True):
                if current_cnt > 0:
                    try:
                        update_peach_events(target_dt, current_cnt - 1, raw_events)
                        st.cache_data.clear()
                        st.session_state.active_date = None
                        st.rerun()
                    except Exception as err:
                        st.error(f"Error: {err}")
                        
        with c_display:
            st.markdown(f"""
                <div class="counter-peach-container">
                    <div class="counter-peach-img">🍑</div>
                    <div class="counter-label">Count: {current_cnt}</div>
                </div>
            """, unsafe_allow_html=True)
            
        with c_plus:
            if st.button("+", key="modal_plus_btn", use_container_width=True):
                try:
                    update_peach_events(target_dt, current_cnt + 1, raw_events)
                    st.cache_data.clear()
                    st.session_state.active_date = None
                    st.rerun()
                except Exception as err:
                    st.error(f"Error: {err}")
                    
        st.markdown('<div class="modal-subtext">Updates synced to Google Calendar</div>', unsafe_allow_html=True)
        
    edit_modal()

st.divider()

# --- 4. KEY METRICS (DYNAMIC DOUBLE COLUMN) ---
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

# --- 5. MONTHLY COMPARISON (DYNAMIC DUAL YEAR COLUMNS) ---
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
