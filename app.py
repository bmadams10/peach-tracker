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
    layout="wide"
)

# Custom CSS for single-line title & navigation button styling
st.markdown("""
    <style>
    .responsive-title {
        font-size: min(4.5vw, 42px);
        font-weight: 800;
        white-space: nowrap;
        margin: 0;
        padding: 0;
        line-height: 1.2;
    }
    .month-label {
        font-size: 24px;
        font-weight: 600;
        margin-left: 10px;
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
col_title, col_btn = st.columns([0.8, 0.2])
with col_title:
    st.markdown('<h1 class="responsive-title">🍑 PEACH TIME TRACKER</h1>', unsafe_allow_html=True)
    st.caption(f"Connected Live to Google Calendar | Last Checked: {datetime.now().strftime('%B %d, %Y - %I:%M %p')}")
with col_btn:
    st.write("")
    if st.button("🔄 Force Refresh"):
        st.cache_data.clear()
        st.rerun()

st.divider()

# --- 2. CALENDAR TOOLBAR & VIEW ---
st.subheader("📅 Interactive 🍑 Calendar View")

# Custom Navigation Bar: [Today] [<] [>] Month Year
c_today, c_prev, c_next, c_label, _ = st.columns([0.1, 0.05, 0.05, 0.4, 0.4])

with c_today:
    if st.button("Today"):
        st.session_state.cal_year = datetime.now().year
        st.session_state.cal_month = datetime.now().month
        st.rerun()

with c_prev:
    if st.button("‹"):
        if st.session_state.cal_month == 1:
            st.session_state.cal_month = 12
            st.session_state.cal_year -= 1
        else:
            st.session_state.cal_month -= 1
        st.rerun()

with c_next:
    if st.button("›"):
        if st.session_state.cal_month == 12:
            st.session_state.cal_month = 1
            st.session_state.cal_year += 1
        else:
            st.session_state.cal_month += 1
        st.rerun()

with c_label:
    month_display = f"{calendar.month_name[st.session_state.cal_month]} {st.session_state.cal_year}"
    st.markdown(f'<span class="month-label">{month_display}</span>', unsafe_allow_html=True)

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
                week_row[day_name] = f"{day} 🍑"
            elif count > 1:
                week_row[day_name] = f"{day} 🍑x{count}"
            else:
                week_row[day_name] = str(day)
    grid_data.append(week_row)

st.table(grid_data)

st.divider()

# --- 3. KEY METRICS ROW ---
m1, m2, m3, m4 = st.columns(4)
m1.metric("2026 YTD Total", f"{total_2026} 🍑", delta=f"+{total_2026 - 75} vs 2025 YTD")
m2.metric("Current Weekly Pace", f"{round(total_2026 / 30, 2)} / wk")
m3.metric("4.0/Wk Target Goal", "209 🍑", delta="Pace: 4.07/wk needed")
m4.metric("Stretch Goal (+25%)", "223 🍑", delta="Pace: 4.65/wk needed")

st.divider()

# --- 4. TARGETS PROGRESS BARS ---
st.subheader("🎯 2026 Target Tracking")
st.progress(min(total_2026 / 202, 1.0), text=f"Real Goal (202 Total): {total_2026} / 202 🍑 ({round((total_2026/202)*100, 1)}%)")
st.progress(min(total_2026 / 209, 1.0), text=f"4.0/Wk Milestone (209 Total): {total_2026} / 209 🍑 ({round((total_2026/209)*100, 1)}%)")
st.progress(min(total_2026 / 223, 1.0), text=f"Stretch Goal (223 Total): {total_2026} / 223 🍑 ({round((total_2026/223)*100, 1)}%)")

st.divider()

# --- 5. MONTHLY COMPARISON BREAKDOWN ---
st.subheader("🗓️ Monthly Comparison Breakdown")
table_data = []

for m in range(1, 13):
    table_data.append({
        "Month": calendar.month_name[m],
        "2025 🍑": counts_2025[m],
        "2026 🍑": counts_2026[m] if m <= 7 else "—"
    })

st.dataframe(table_data, use_container_width=True)import urllib.request
import re
from collections import defaultdict
from datetime import datetime, date
import calendar
import streamlit as st

# 1. Page Configuration & Favicon Icon
st.set_page_config(
    page_title="PEACH TIME TRACKER", 
    page_icon="🍑", 
    layout="wide"
)

# Custom CSS: Single-line responsive header & Disable typing in Selectboxes
st.markdown("""
    <style>
    /* Responsive single-line title that fills screen width */
    .responsive-title {
        font-size: min(4.5vw, 42px);
        font-weight: 800;
        white-space: nowrap;
        margin: 0;
        padding: 0;
        line-height: 1.2;
    }
    /* Disable text editing/typing in Streamlit selectboxes while keeping click-to-select */
    div[data-baseweb="select"] input {
        caret-color: transparent !important;
        cursor: pointer !important;
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

# --- 1. HEADER SECTION ---
col_title, col_btn = st.columns([0.8, 0.2])
with col_title:
    st.markdown('<h1 class="responsive-title">🍑 PEACH TIME TRACKER</h1>', unsafe_allow_html=True)
    st.caption(f"Connected Live to Google Calendar | Last Checked: {datetime.now().strftime('%B %d, %Y - %I:%M %p')}")
with col_btn:
    st.write("")
    if st.button("🔄 Force Refresh"):
        st.cache_data.clear()
        st.rerun()

st.divider()

# --- 2. CALENDAR VIEW (AFTER HEADER) ---
st.subheader("📅 Interactive 🍑 Calendar View")

cal_col1, cal_col2 = st.columns([0.5, 0.5])
with cal_col1:
    selected_year = st.selectbox("Select Year", [2026, 2025], index=0)
with cal_col2:
    current_month_index = datetime.now().month - 1 if selected_year == datetime.now().year else 0
    selected_month_name = st.selectbox(
        "Select Month", 
        list(calendar.month_name)[1:], 
        index=current_month_index
    )

selected_month = list(calendar.month_name).index(selected_month_name)

# Render Month Grid Table
month_cal = calendar.monthcalendar(selected_year, selected_month)
days_header = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

# Format days with 🍑 emoji
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
                week_row[day_name] = f"{day} 🍑"
            elif count > 1:
                week_row[day_name] = f"{day} 🍑x{count}"
            else:
                week_row[day_name] = str(day)
    grid_data.append(week_row)

st.table(grid_data)

st.divider()

# --- 3. KEY METRICS ROW ---
m1, m2, m3, m4 = st.columns(4)
m1.metric("2026 YTD Total", f"{total_2026} 🍑", delta=f"+{total_2026 - 75} vs 2025 YTD")
m2.metric("Current Weekly Pace", f"{round(total_2026 / 30, 2)} / wk")
m3.metric("4.0/Wk Target Goal", "209 🍑", delta="Pace: 4.07/wk needed")
m4.metric("Stretch Goal (+25%)", "223 🍑", delta="Pace: 4.65/wk needed")

st.divider()

# --- 4. TARGETS PROGRESS BARS ---
st.subheader("🎯 2026 Target Tracking")
st.progress(min(total_2026 / 202, 1.0), text=f"Real Goal (202 Total): {total_2026} / 202 🍑 ({round((total_2026/202)*100, 1)}%)")
st.progress(min(total_2026 / 209, 1.0), text=f"4.0/Wk Milestone (209 Total): {total_2026} / 209 🍑 ({round((total_2026/209)*100, 1)}%)")
st.progress(min(total_2026 / 223, 1.0), text=f"Stretch Goal (223 Total): {total_2026} / 223 🍑 ({round((total_2026/223)*100, 1)}%)")

st.divider()

# --- 5. MONTHLY COMPARISON BREAKDOWN ---
st.subheader("🗓️ Monthly Comparison Breakdown")
table_data = []

for m in range(1, 13):
    table_data.append({
        "Month": calendar.month_name[m],
        "2025 🍑": counts_2025[m],
        "2026 🍑": counts_2026[m] if m <= 7 else "—"
    })

st.dataframe(table_data, use_container_width=True)
