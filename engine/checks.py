from engine.hours import night_hours

PASS = "pass"
FAIL = "fail"
UNKNOWN = "unknown"


def sum_hours(*series):
    return [sum(values) for values in zip(*series)]


def result(status, within_margin, margin, reason, numbers, causing=None):
    return {
        "status": status,
        "within_margin": within_margin,
        "margin": None if margin is None else round(margin, 4),
        "reason": reason,
        "numbers": numbers,
        "causing_business_ids": causing or [],
    }


def power_check(site, businesses):
    combined = sum_hours(
        site["baseline_demand_kw"], *[business["peak_kw"] for business in businesses]
    )
    worst_hour = max(range(24), key=lambda hour: combined[hour])
    peak = combined[worst_hour]
    limit = site["inverter_continuous_kw"]
    safety_margin = site["settings"]["safety_margin"]
    numbers = {
        "worst_hour": worst_hour,
        "combined_peak_kw": round(peak, 3),
        "inverter_continuous_kw": limit,
        "hourly_combined_peak_kw": [round(value, 3) for value in combined],
    }
    if limit is None:
        return result(
            UNKNOWN,
            False,
            None,
            "Inverter continuous rating is missing, so the power check cannot run.",
            numbers,
        )
    margin = (limit - peak) / limit
    hour_label = f"{worst_hour:02d}:00"
    if peak > limit:
        causing = [
            business["business_id"]
            for business in businesses
            if business["peak_kw"][worst_hour] > 0
        ]
        return result(
            FAIL,
            False,
            margin,
            f"Combined peak of {peak:.2f} kW at {hour_label} is above the {limit:.2f} kW inverter rating.",
            numbers,
            causing,
        )
    within = peak > limit * (1 - safety_margin)
    reason = f"Combined peak of {peak:.2f} kW at {hour_label} fits the {limit:.2f} kW inverter"
    reason += (
        f" but is inside the {safety_margin:.0%} safety margin."
        if within
        else f" with {limit - peak:.2f} kW to spare."
    )
    return result(PASS, within, margin, reason, numbers)


def startup_check(site, businesses):
    surge_limit = site["inverter_surge_kw"]
    surge_duration = site["inverter_surge_duration_s"]
    safety_margin = site["settings"]["safety_margin"]
    baseline = site["baseline_demand_kw"]
    entries = []
    failing = []
    missing = []
    margins = []
    within = False

    for business in businesses:
        if business["startup_power_kw"] is None:
            missing.append(business["business_id"])
            entries.append({"business_id": business["business_id"], "status": UNKNOWN})
            continue
        others = [other for other in businesses if other is not business]
        hours = (
            sorted(business["open_hours"])
            or [hour for hour in range(24) if business["average_kw"][hour] > 0]
            or list(range(24))
        )

        running = {
            hour: baseline[hour] + sum(other["average_kw"][hour] for other in others)
            for hour in hours
        }
        worst_hour = max(hours, key=running.get)
        surge = running[worst_hour] + business["startup_power_kw"]
        entry = {
            "business_id": business["business_id"],
            "worst_hour": worst_hour,
            "surge_kw": round(surge, 3),
            "startup_power_kw": business["startup_power_kw"],
            "startup_duration_s": business["startup_duration_s"],
        }
        if surge_limit is None:
            entry["status"] = UNKNOWN
            entries.append(entry)
            continue
        margins.append((surge_limit - surge) / surge_limit)
        too_long = (
            surge_duration is not None
            and business["startup_duration_s"] is not None
            and business["startup_duration_s"] > surge_duration
        )
        if surge > surge_limit or too_long:
            entry["status"] = FAIL
            entry["too_long"] = too_long
            failing.append(business)
        else:
            entry["status"] = PASS
            within = within or surge > surge_limit * (1 - safety_margin)
        entries.append(entry)

    numbers = {
        "inverter_surge_kw": surge_limit,
        "inverter_surge_duration_s": surge_duration,
        "businesses": entries,
    }
    margin = min(margins) if margins else None
    if failing:
        names = ", ".join(business["business_name"] for business in failing)
        return result(
            FAIL,
            False,
            margin,
            f"Motor startup from {names} would go over the inverter surge rating or last longer than it can hold.",
            numbers,
            [business["business_id"] for business in failing],
        )
    if surge_limit is None:
        return result(
            UNKNOWN,
            False,
            None,
            "Inverter surge rating is missing, so the startup check cannot run.",
            numbers,
        )
    if missing:
        return result(
            UNKNOWN,
            False,
            margin,
            "Startup power is missing for at least one business, so its motor startup cannot be checked.",
            numbers,
            missing,
        )
    reason = f"Every motor startup fits the {surge_limit:.2f} kW surge rating"
    reason += " but at least one is inside the safety margin." if within else "."
    if surge_duration is None:
        reason += " Startup duration was not compared because the inverter surge duration is missing."
    return result(PASS, within, margin, reason, numbers)


def energy_check(site, businesses, solar_kw):
    load = sum_hours(
        site["baseline_demand_kw"], *[business["average_kw"] for business in businesses]
    )
    round_trip = site["charge_efficiency"] * site["discharge_efficiency"]
    safety_margin = site["settings"]["safety_margin"]
    surplus = [max(solar_kw[hour] - load[hour], 0.0) for hour in range(24)]
    deficit = [max(load[hour] - solar_kw[hour], 0.0) for hour in range(24)]
    deliverable = sum(surplus) * round_trip
    needed = sum(deficit)
    numbers = {
        "daily_demand_kwh": round(sum(load), 3),
        "daily_solar_kwh": round(sum(solar_kw), 3),
        "deficit_kwh": round(needed, 3),
        "deliverable_from_surplus_kwh": round(deliverable, 3),
        "round_trip_efficiency": round(round_trip, 4),
    }
    if needed == 0:
        return result(
            PASS,
            False,
            1.0,
            "Solar covers the whole daily demand in the hours it is produced.",
            numbers,
        )
    margin = (deliverable - needed) / deliverable if deliverable > 0 else -1.0
    if needed > deliverable:
        deficit_hours = {hour for hour in range(24) if deficit[hour] > 0}
        causing = [
            business["business_id"]
            for business in businesses
            if any(business["average_kw"][hour] > 0 for hour in deficit_hours)
        ]
        return result(
            FAIL,
            False,
            margin,
            f"The site needs {needed:.2f} kWh a day outside solar hours but leftover solar can only "
            f"deliver {deliverable:.2f} kWh after battery losses.",
            numbers,
            causing,
        )
    within = needed > deliverable * (1 - safety_margin)
    reason = f"Leftover solar can deliver {deliverable:.2f} kWh against {needed:.2f} kWh needed outside solar hours"
    reason += ", inside the safety margin." if within else "."
    return result(PASS, within, margin, reason, numbers)


def battery_check(site, businesses, limits, without, with_new, period_days):
    settings = site["settings"]
    tolerance = settings["unserved_energy_tolerance_kwh"] * period_days
    extra_unserved = max(
        with_new["total_unserved_kwh"] - without["total_unserved_kwh"], 0.0
    )
    reserve_level = limits["min_stored"] + settings["reserve_factor"] * limits["usable"]
    lowest = with_new["lowest_stored_kwh"]
    nights = night_hours(settings["night_start_hour"], settings["night_end_hour"])
    night_load = sum(
        business["average_kw"][hour] for business in businesses for hour in nights
    )
    business_energy = (
        sum(sum(business["average_kw"]) for business in businesses) * period_days
    )
    numbers = {
        "extra_unserved_kwh": round(extra_unserved, 3),
        "tolerance_kwh": round(tolerance, 3),
        "lowest_stored_kwh": round(lowest, 3),
        "reserve_level_kwh": round(reserve_level, 3),
        "min_stored_kwh": round(limits["min_stored"], 3),
        "max_stored_kwh": round(limits["max_stored"], 3),
        "extra_night_load_kwh_per_day": round(night_load, 3),
    }
    if extra_unserved > tolerance:
        margin = (
            -(extra_unserved - tolerance) / business_energy if business_energy else -1.0
        )
        short_hours = {
            index % 24
            for index, value in enumerate(with_new["unserved_kwh"])
            if value > without["unserved_kwh"][index]
        }
        causing = [
            business["business_id"]
            for business in businesses
            if any(business["average_kw"][hour] > 0 for hour in short_hours)
        ]
        return result(
            FAIL,
            False,
            margin,
            f"The battery runs out and leaves {extra_unserved:.2f} kWh of extra demand unserved over "
            f"{period_days} day(s), above the {tolerance:.2f} kWh tolerance.",
            numbers,
            causing,
        )
    margin = (
        (lowest - limits["min_stored"]) / limits["usable"] if limits["usable"] else 0.0
    )
    within = lowest < reserve_level
    reason = f"The battery never drops below {lowest:.2f} kWh"
    reason += (
        f", which is under the {reserve_level:.2f} kWh reserve."
        if within
        else f" and stays above the {reserve_level:.2f} kWh reserve."
    )
    return result(PASS, within, margin, reason, numbers)
