from collections import defaultdict

from engine.hours import is_open_on


def energy_from_counter(counter_values):
    total = 0.0
    previous = None
    for value in counter_values:
        if previous is not None:
            difference = value - previous
            total += value if difference < 0 else difference
        previous = value
    return round(total, 4)


def build_hourly_profile(readings, operating_hours, timezone):
    if not readings:
        return {
            "average_kw": [0.0] * 24,
            "peak_kw": [0.0] * 24,
            "observed_days": 0,
            "open_days_used": 0,
            "reading_count": 0,
            "first_measured_at": None,
            "last_measured_at": None,
            "measured_energy_kwh": 0.0,
            "daily_energy_kwh": 0.0,
        }

    ordered = sorted(readings, key=lambda item: item[0])
    by_date = defaultdict(lambda: defaultdict(list))
    for measured_at, power_w, _ in ordered:
        local = measured_at.astimezone(timezone)
        by_date[local.date()][local.hour].append(power_w)

    all_dates = sorted(by_date)
    open_dates = [
        day for day in all_dates if is_open_on(operating_hours, day.weekday())
    ]
    used_dates = open_dates or all_dates

    average_kw = []
    peak_kw = []
    for hour in range(24):
        hour_means = []
        hour_peak = 0.0
        for day in used_dates:
            values = by_date[day].get(hour)
            if values:
                hour_means.append(sum(values) / len(values))
                hour_peak = max(hour_peak, max(values))
        average = sum(hour_means) / len(hour_means) if hour_means else 0.0
        average_kw.append(round(average / 1000, 4))
        peak_kw.append(round(hour_peak / 1000, 4))

    return {
        "average_kw": average_kw,
        "peak_kw": peak_kw,
        "observed_days": len(all_dates),
        "open_days_used": len(used_dates),
        "reading_count": len(ordered),
        "first_measured_at": ordered[0][0],
        "last_measured_at": ordered[-1][0],
        "measured_energy_kwh": energy_from_counter([item[2] for item in ordered]),
        "daily_energy_kwh": round(sum(average_kw), 4),
    }
