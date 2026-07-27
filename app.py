import urllib.request
import re
from collections import defaultdict
from datetime import datetime, date
import calendar
import streamlit as st

# Set calendar to start week on Sunday
calendar.setfirstweekday(calendar.SUNDAY)

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

    /* Single-Row Mobile Calendar Toolbar */
    .nav-toolbar-container {
        display: flex !important;
        flex-direction: row !important;
        align-items: center !important;
        justify-content: space-between !important;
        width: 100% !important;
        margin-top: 4px !important;
        margin-bottom: 8px !important;
    }

    .month-nav-label-inline {
        font-size: 20px !important;
        font-weight: 700 !important;
        text-align: center !important;
        flex-grow: 1 !important;
    }

    /* Compact Mobile Calendar Table */
    div[data-testid="stTable"] table {
        font-size: 12px !important;
        width: 100% !important;
        touch-action: pan-y;
    }
    div[data-testid="stTable"] th, div[data-testid="stTable"] td {
        padding: 4px 1px !important;
        text-align: center !important;
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

    <script>
    // Touch Swipe Gesture Listener for Calendar Table
    document.addEventListener('DOMContentLoaded', () => {
        let touchstartX = 0;
        let touchendX = 0;
        const minSwipeDistance = 50;

        function handleGesture() {
            const swipeDistance = touchendX - touchstartX;
            if (Math.abs(swipeDistance) >= minSwipeDistance) {
                if (swipeDistance < 0) {
                    window.location.href = '?action=next';
                } else {
                    window.location.href = '?action=prev';
                }
            }
        }

        const calTable = document.querySelector('div[data-testid="stTable"]');
        if (calTable) {
            calTable.addEventListener('touchstart', e => {
                touchstartX = e.changedTouches[0].screenX;
            }, {passive: true});

            calTable.addEventListener('touchend', e => {
                touchendX = e.changedTouches[0].screenX;
                handleGesture();
            }, {passive: true});
        }
    });
    </script>
""", unsafe_allow_html=True)

ICS_URL = "https://calendar.google.com/calendar/ical/bmadams809%40gmail.com/public/basic.ics"

# 2. Fetch & Cache Data
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

# Create maps for analytical calculations
date_counts = defaultdict(int)
day_of_week_counts = defaultdict(int)
month_year_counts = defaultdict(int)

for d in events:
    date_counts[d] += 1
    day_name = calendar.day_name[d.weekday()]
    day_of_week_counts[day_name] += 1
    month_year_counts[f"{calendar.month_abbr[d.month]} {d.year}"] += 1

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
total_lifetime = len(events)

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

# Initialize Calendar Session State Date
if "cal_year" not in st.session_state:
    st.session_state.cal_year = datetime.now().year
if "cal_month" not in st.session_state:
    st.session_state.cal_month = datetime.now().month

# Handle Action Buttons/Swipes for Next/Prev
query_params = st.query_params
if "action" in query_params:
    act = query_params["action"]
    if act == "prev":
        if st.session_state.cal_month == 1:
            st.session_state.cal_month = 12
            st.session_state.cal_year -= 1
        else:
            st.session_state.cal_month -= 1
    elif act == "next":
        if st.session_state.cal_month == 12:
            st.session_state.cal_month = 1
            st.session_state.cal_year += 1
        else:
            st.session_state.cal_month += 1
    st.query_params.clear()

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

st.markdown(f"""
    <div class="nav-toolbar-container">
        <a href="?action=prev" target="_self" style="text-decoration: none;">
            <button style="width: 44px; height: 34px; font-size: 18px; font-weight: bold; border-radius: 6px; border: 1px solid #444; background: #262730; color: white; cursor: pointer;">‹</button>
        </a>
        <div class="month-nav-label-inline">{month_display}</div>
        <a href="?action=next" target="_self" style="text-decoration: none;">
            <button style="width: 44px; height: 34px; font-size: 18px; font-weight: bold; border-radius: 6px; border: 1px solid #444; background: #262730; color: white; cursor: pointer;">›</button>
        </a>
    </div>
""", unsafe_allow_html=True)

# Render Month Grid Table (Sunday First)
selected_year = st.session_state.cal_year
selected_month = st.session_state.cal_month

month_cal = calendar.monthcalendar(selected_year, selected_month)
days_header = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]

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

# --- 3. KEY METRICS (DOUBLE COLUMN) ---
st.subheader("📊 Key Metrics")

km_col_left, km_col_right = st.columns(2)

# Left Column: Current 2026 Metrics
with km_col_left:
    st.markdown('<div class="metrics-col-hdr">2026 Goals & Pace</div>', unsafe_allow_html=True)
    st.metric("2026 YTD", f"{total_2026} 🍑", delta=f"+{total_2026 - 75} vs 2025")
    st.metric("Weekly Pace", f"{round(total_2026 / 30, 2)} / wk")
    st.metric("4.0/Wk Goal", "209 🍑", delta="4.07/wk needed")
    st.metric("Stretch Goal", "223 🍑", delta="4.65/wk needed")

# Right Column: Lifetime Insights
with km_col_right:
    st.markdown('<div class="metrics-col-hdr">Lifetime Insights</div>', unsafe_allow_html=True)
    st.metric("Top Month", f"{top_month_str}", delta=f"{top_month_val} 🍑 recorded")
    st.metric("Top Day of Week", f"{top_day_str}", delta=f"{top_day_val} total ({top_day_pct}%)")
    st.metric("Lifetime 🍑 Total", f"{total_lifetime} 🍑", delta="All-time overall")
    st.metric("Longest Streak", f"{max_streak} Days ({streak_instances} 🍑)", delta=f"{streak_period_str}")

st.divider()

# --- 4. MONTHLY COMPARISON (FORCED 2 COLUMNS ON MOBILE) ---
st.subheader("🗓️ Monthly Comparison")

current_m = datetime.now().month
col_left, col_right = st.columns(2)

# Left Column: January (1) to June (6)
with col_left:
    for m in range(1, 7):
        m_name = calendar.month_abbr[m]
        c25 = counts_2025[m]
        if m <= current_m:
            c26 = counts_2026[m]
            diff = c26 - c25
            st.markdown(f'<div class="month-hdr">{m_name}</div>', unsafe_allow_html=True)
            st.metric(label="2026 vs 2025", value=f"{c26} 🍑", delta=f"{'+' if diff > 0 else ''}{diff} YoY (2025: {c25})")
        else:
            st.markdown(f'<div class="month-hdr">{m_name} *(Upcoming)*</div>', unsafe_allow_html=True)
            st.metric(label="2026 vs 2025", value="—", delta=f"2025: {c25}")

# Right Column: July (7) to December (12)
with col_right:
    for m in range(7, 13):
        m_name = calendar.month_abbr[m]
        c25 = counts_2025[m]
        if m <= current_m:
            c26 = counts_2026[m]
            diff = c26 - c25
            st.markdown(f'<div class="month-hdr">{m_name}</div>', unsafe_allow_html=True)
            st.metric(label="2026 vs 2025", value=f"{c26} 🍑", delta=f"{'+' if diff > 0 else ''}{diff} YoY (2025: {c25})")
        else:
            st.markdown(f'<div class="month-hdr">{m_name} *(Upcoming)*</div>', unsafe_allow_html=True)
            st.metric(label="2026 vs 2025", value="—", delta=f"2025: {c25}")
