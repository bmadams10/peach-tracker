import urllib.request
import re
from collections import defaultdict
from datetime import datetime
import streamlit as st

import streamlit as st

# Set page title and top logo / tab favicon
st.set_page_config(
    page_title="🍑 Live TRACKER Dashboard", 
    page_icon="🍑", 
    layout="wide"
)

ICS_URL = "https://calendar.google.com/calendar/ical/bmadams809%40gmail.com/public/basic.ics"

@st.cache_data(ttl=300)  # Refreshes calendar data every 5 minutes
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

# Process Counts
counts_2025 = defaultdict(int)
counts_2026 = defaultdict(int)

for d in events:
    if d.year == 2025:
        counts_2025[d.month] += 1
    elif d.year == 2026:
        counts_2026[d.month] += 1

total_2025 = sum(counts_2025.values())
total_2026 = sum(counts_2026.values())

# --- DASHBOARD HEADER ---
st.title("🍑 Live TRACKER Dashboard")
st.caption(f"Last updated from Google Calendar: {datetime.now().strftime('%B %d, %Y - %I:%M %p')}")

# --- KEY METRICS ROW ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("2026 YTD Total", f"{total_2026} 🍑", delta=f"+{total_2026 - 75} vs 2025 YTD")
col2.metric("Current Weekly Avg", f"{round(total_2026 / 30, 2)} / wk")
col3.metric("2026 Real Goal", "202 🍑", delta="Pace: 3.72/wk needed")
col4.metric("2026 Stretch Goal", "223 🍑", delta="Pace: 4.65/wk needed")

st.divider()

# --- TARGETS PROGRESS BARS ---
st.subheader("🎯 2026 Progress Targets")
st.progress(min(total_2026 / 202, 1.0), text=f"Real Goal: {total_2026} / 202 🍑 ({round((total_2026/202)*100, 1)}%)")
st.progress(min(total_2026 / 209, 1.0), text=f"4.0/Wk Goal: {total_2026} / 209 🍑 ({round((total_2026/209)*100, 1)}%)")
st.progress(min(total_2026 / 223, 1.0), text=f"Stretch Goal: {total_2026} / 223 🍑 ({round((total_2026/223)*100, 1)}%)")

st.divider()

# --- MONTHLY BREAKDOWN TABLE ---
st.subheader("🗓️ Monthly Comparison Breakdown")

months_name = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
table_data = []

for m in range(1, 13):
    table_data.append({
        "Month": months_name[m-1],
        "2025 🍑": counts_2025[m],
        "2026 🍑": counts_2026[m] if m <= 7 else "—"
    })

st.table(table_data)
