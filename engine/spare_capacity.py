from engine.simulation import battery_limits, simulate


def spare_capacity(site):
    baseline = site["baseline_demand_kw"]
    limits = battery_limits(site)
    round_trip = site["charge_efficiency"] * site["discharge_efficiency"]
    inverter = site["inverter_continuous_kw"]
    days = {}
    for day_type in ("average", "low_sun"):
        solar = site["solar_profile"][f"{day_type}_kw"]
        surplus = [max(solar[hour] - baseline[hour], 0.0) for hour in range(24)]
        deficit = [max(baseline[hour] - solar[hour], 0.0) for hour in range(24)]
        run = simulate(baseline, solar, limits, limits["max_stored"], 3)
        last_day = slice(48, 72)
        days[day_type] = {
            "hourly_solar_surplus_kw": [round(value, 3) for value in surplus],
            "daily_spare_energy_kwh": round(
                sum(surplus) * round_trip - sum(deficit), 3
            ),
            "daily_curtailed_kwh": round(sum(run["curtailed_kwh"][last_day]), 3),
            "daily_unserved_kwh": round(sum(run["unserved_kwh"][last_day]), 3),
            "lowest_stored_kwh": round(min(run["stored_kwh"][last_day]), 3),
        }
    return {
        "hourly_inverter_headroom_kw": (
            None
            if inverter is None
            else [round(inverter - baseline[hour], 3) for hour in range(24)]
        ),
        "usable_battery_kwh": round(limits["usable"], 3),
        "min_stored_kwh": round(limits["min_stored"], 3),
        "max_stored_kwh": round(limits["max_stored"], 3),
        "days": days,
    }
