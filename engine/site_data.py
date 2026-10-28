from collections import defaultdict


def hourly_average(source, dates):
    averages = []
    for hour in range(24):
        means = [
            sum(source[day][hour]) / len(source[day][hour])
            for day in dates
            if source[day].get(hour)
        ]
        averages.append(round(sum(means) / len(means), 3) if means else 0.0)
    return averages


def average_monitoring_export(rows, site_timezone, source_timezone):
    load_by_date = defaultdict(lambda: defaultdict(list))
    solar_by_date = defaultdict(lambda: defaultdict(list))
    for timestamp, load_kw, solar_kw in rows:
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=source_timezone)
        local = timestamp.astimezone(site_timezone)
        load_by_date[local.date()][local.hour].append(load_kw)
        solar_by_date[local.date()][local.hour].append(solar_kw)

    dates = sorted(load_by_date)
    complete_dates = [day for day in dates if len(load_by_date[day]) == 24]
    if not complete_dates:
        raise ValueError("The export needs at least one full day with all 24 hours")

    def solar_total(day):
        return sum(sum(values) / len(values) for values in solar_by_date[day].values())

    low_sun_date = min(complete_dates, key=solar_total)
    low_sun_kw = [
        round(
            sum(solar_by_date[low_sun_date][hour])
            / len(solar_by_date[low_sun_date][hour]),
            3,
        )
        for hour in range(24)
    ]
    return {
        "baseline_demand_kw": hourly_average(load_by_date, dates),
        "solar_profile": {
            "average_kw": hourly_average(solar_by_date, dates),
            "low_sun_kw": low_sun_kw,
        },
        "days_in_export": len(dates),
        "complete_days": len(complete_dates),
        "low_sun_date": low_sun_date,
        "first_date": dates[0],
        "last_date": dates[-1],
    }
