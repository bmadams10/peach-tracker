# Calculate Streaks (Longest & Current Active based on total 🍑 count)
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

# Calculate Current Active Streak (Total 🍑 accumulated in ongoing consecutive days)
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
    streak_period_str = f"{d_start.strftime('%b %d')}–{d_end.strftime('%d, %Y')}"
else:
    streak_period_str = "—"
