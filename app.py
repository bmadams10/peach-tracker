import urllib.request
import re
from collections import defaultdict
from datetime import datetime, date
import calendar
import streamlit as st

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
    /* Remove excessive top padding on mobile */
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 2rem !important;
        padding-left: 0.8rem !important;
        padding-right: 0.8rem !important;
    }
    
    /* Responsive single-line title that scales to viewport without overflow */
    .responsive-title {
        font-size: clamp(20px, 6.5vw, 38px) !important;
        font-weight: 800 !important;
        white-space: nowrap !important;
        margin: 0 !important;
        padding: 0 !important;
        line-height: 1.2 !important;
    }

    /* Force Calendar Controls into a Single Compact Row */
    .nav-toolbar {
        display: flex !important;
        align-items: center !important;
        gap: 8px !important;
        margin-bottom: 12px !important;
    }
    
    .month-label {
        font-size: 20px !important;
        font-weight: 700 !important;
        margin-left: 8px !important;
        white-space: nowrap !important;
    }

    /* Mobile Calendar Table Styling */
    div[data-testid="stTable"] table {
        font-size: 13px !important;
        width: 100% !important;
    }
    div[data-testid="stTable"] th, div[data-testid="stTable"] td {
        padding: 4px 2px !important;
        text-align: center !important;
    }
    </style>
""", unsafe_allow_html=True)

ICS_URL = "https://calendar.google.com/calendar/ical/bmadams809%40gmail.com/public/basic.ics"

# 2. Fetch & Cache Data (Refreshes automatically every 5 minutes)
@st.cache_data(ttl=300)
def fetch_calendar_data():
    req = urllib.request.Request(ICS_URL, headers={'User-Agent': 'Mozilla/5.0'})
    ics_text = urllib.request.urlopen(req).read().decode('utf-8')
    
    events = []
    current_event = {}
    for line in ics_text.splitlines():
        if line.startswith("BEGIN:VEVENT"):
            current_event = {}
        elif line.startswith("DTSTART"):
            match = re.search(r'(\d{8})', line)
            if match:
                current_event['date'] = datetime.strptime(match.group(1), "%Y%m%d").date()
        elif line.startswith("SUMMARY:"):
            current_event['summary'] = line.split(":", 1)[1].strip()
        elif line.startswith("END:VEVENT"):
            if current_event.get('summary') == "🍑" and 'date' in current_event:
                events.append(current_event['date'])
    return sorted(events)

# Load data
events = fetch_calendar_data()

# Create a map counting 🍑 per date
date_counts = defaultdict(int)
for d in events:
    date_counts[d] += 1

# Process Annual Counts
counts_2025 = defaultdict(int)
counts_2026 = defaultdict(int)

for d in events:
    if d.year == 2025:
        counts_2025[d.month] += 1
    elif d.year == 2026:
        counts_2026[d.month] += 1

total_2025 = sum(counts_2025.values())
total_2026 = sum(counts_2026.values())

# Initialize Calendar Session State Date
if "cal_year" not in st.session_state:
    st.session_state.cal_year = datetime.now().year
if "cal_month" not in st.session_state:
    st.session_state.cal_month = datetime.now().month

# --- 1. HEADER SECTION ---
st.markdown('<h1 class="responsive-title">🍑 PEACH TIME TRACKER</h1>', unsafe_allow_html=True)
st.caption(f"Live Calendar | Updated: {datetime.now().strftime('%b %d, %Y - %I:%M %p')}")

if st.button("🔄 Force Refresh", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

st.divider()

# --- 2. CALENDAR TOOLBAR & VIEW ---
st.subheader("📅 Calendar View")

# Single-row Mobile Navigation Bar
btn_col1, btn_col2, btn_col3, btn_col4 = st.columns([0.25, 0.15, 0.15, 0.45])

with btn_col1:
    if st.button("Today", use_container_width=True):
        st.session_state.cal_year = datetime.now().year
        st.session_state.cal_month = datetime.now().month
        st.rerun()

with btn_col2:
    if st.button("‹", use_container_width=True):
        if st.session_state.cal_month == 1:
            st.session_state.cal_month = 12
            st.session_state.cal_year -= 1
        else:
            st.session_state.cal_month -= 1
        st.rerun()

with btn_col3:
    if st.button("›", use_container_width=True):
        if st.session_state.cal_month == 12:
            st.session_state.cal_month = 1
            st.session_state.cal_year += 1
        else:
            st.session_state.cal_month += 1
        st.rerun()

with btn_col4:
    month_display = f"{calendar.month_abbr[st.session_state.cal_month]} {st.session_state.cal_year}"
    st.markdown(f'<div class="month-label">{month_display}</div>', unsafe_allow_html=True)

# Render Month Grid Table
selected_year = st.session_state.cal_year
selected_month = st.session_state.cal_month

month_cal = calendar.monthcalendar(selected_year, selected_month)
days_header = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

grid_data = []
for week in month_cal:
    week_row = {}
    for i, day in enumerate(week):
        day_name = days_header[i]
        if day == 0:
            week_row[day_name] = ""
        else:
            curr_date = date(selected_year, selected_month, day)
            count = date_counts.get(curr_date, 0)
            if count == 1:
                week_row[day_name] = f"{day}🍑"
            elif count > 1:
                week_row[day_name] = f"{day}🍑x{count}"
            else:
                week_row[day_name] = str(day)
    grid_data.append(week_row)

st.table(grid_data)

st.divider()

# --- 3. KEY METRICS ---
st.subheader("📊 Key Metrics")
m1, m2 = st.columns(2)
m1.metric("2026 YTD", f"{total_2026} 🍑", delta=f"+{total_2026 - 75} vs 2025")
m2.metric("Weekly Pace", f"{round(total_2026 / 30, 2)} / wk")

m3, m4 = st.columns(2)
m3.metric("4.0/Wk Goal", "209 🍑", delta="4.07/wk needed")
m4.metric("Stretch Goal", "223 🍑", delta="4.65/wk needed")

st.divider()

# --- 4. TARGETS PROGRESS BARS ---
st.subheader("🎯 2026 Progress")
st.progress(min(total_2026 / 202, 1.0), text=f"Real Goal: {total_2026} / 202 🍑 ({round((total_2026/202)*100, 1)}%)")
st.progress(min(total_2026 / 209, 1.0), text=f"4.0/Wk Goal: {total_2026} / 209 🍑 ({round((total_2026/209)*100, 1)}%)")
st.progress(min(total_2026 / 223, 1.0), text=f"Stretch Goal: {total_2026} / 223 🍑 ({round((total_2026/223)*100, 1)}%)")

st.divider()

# --- 5. MONTHLY COMPARISON BREAKDOWN ---
st.subheader("🗓️ Monthly Breakdown")
table_data = []

for m in range(1, 13):
    table_data.append({
        "Month": calendar.month_abbr[m],
        "2025 🍑": counts_2025[m],
        "2026 🍑": counts_2026[m] if m <= 7 else "—"
    })

st.dataframe(table_data, use_container_width=True)
