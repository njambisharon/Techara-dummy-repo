from engine.checks import (
    FAIL,
    PASS,
    UNKNOWN,
    battery_check,
    energy_check,
    power_check,
    startup_check,
)
from engine.simulation import battery_limits, simulate

CHECK_ORDER = ("power", "startup", "energy", "battery")
LABEL_RANK = {"observed": 0, "user_entered": 1, "estimated": 2, "simulated": 3}
OUTCOME_RANK = {"feasible": 0, "conditionally_feasible": 1, "not_feasible": 2}


def weakest_label(site, businesses):
    labels = [
        site["data_labels"]["baseline"],
        site["data_labels"]["solar"],
        site["data_labels"]["battery"],
    ]
    for business in businesses:
        labels.append(business["data_label"])
        if business["startup_data_label"]:
            labels.append(business["startup_data_label"])
    return max(labels, key=lambda label: LABEL_RANK[label])


def decide_outcome(results):
    statuses = [results[name]["status"] for name in CHECK_ORDER]
    if FAIL in statuses:
        return "not_feasible"
    if UNKNOWN in statuses or any(
        results[name]["within_margin"] for name in CHECK_ORDER
    ):
        return "conditionally_feasible"
    return "feasible"


def find_limiting_check(results):
    failed = [name for name in CHECK_ORDER if results[name]["status"] == FAIL]
    candidates = failed or [
        name
        for name in CHECK_ORDER
        if results[name]["status"] == PASS and results[name]["margin"] is not None
    ]
    if not candidates:
        return None
    return min(
        candidates,
        key=lambda name: (
            results[name]["margin"] if results[name]["margin"] is not None else 0
        ),
    )


def utilisation(solar_kw, run, days):
    produced = sum(solar_kw) * days
    if produced == 0:
        return None
    return round((produced - run["total_curtailed_kwh"]) / produced, 4)


def run_assessment(
    site, businesses, initial_stored_kwh, solar_day_type, period_days, flags=None
):
    solar_kw = site["solar_profile"][f"{solar_day_type}_kw"]
    limits = battery_limits(site)
    baseline = site["baseline_demand_kw"]
    with_load = [
        baseline[hour] + sum(business["average_kw"][hour] for business in businesses)
        for hour in range(24)
    ]
    without = simulate(baseline, solar_kw, limits, initial_stored_kwh, period_days)
    with_new = simulate(with_load, solar_kw, limits, initial_stored_kwh, period_days)

    results = {
        "power": power_check(site, businesses),
        "startup": startup_check(site, businesses),
        "energy": energy_check(site, businesses, solar_kw),
        "battery": battery_check(
            site, businesses, limits, without, with_new, period_days
        ),
        "flags": flags or [],
    }

    extra_unserved = max(
        with_new["total_unserved_kwh"] - without["total_unserved_kwh"], 0.0
    )
    business_months = [
        {
            "business_id": business["business_id"],
            "daily_energy_kwh": round(sum(business["average_kw"]), 3),
            "monthly_energy_kwh": round(
                sum(business["average_kw"]) * business["days_per_month"], 3
            ),
        }
        for business in businesses
    ]
    planned_monthly = sum(item["monthly_energy_kwh"] for item in business_months)
    planned_daily = sum(item["daily_energy_kwh"] for item in business_months)
    if extra_unserved > 0 and planned_daily > 0:
        delivered_share = (
            max(planned_daily - extra_unserved / period_days, 0.0) / planned_daily
        )
        monthly_energy = planned_monthly * delivered_share
        revenue_basis = "delivered"
    else:
        monthly_energy = planned_monthly
        revenue_basis = "planned"

    return {
        "outcome": decide_outcome(results),
        "check_results": results,
        "limiting_check": find_limiting_check(results),
        "monthly_revenue": round(monthly_energy * site["tariff_per_kwh"], 2),
        "revenue_basis": revenue_basis,
        "lowest_stored_kwh": with_new["lowest_stored_kwh"],
        "data_label": weakest_label(site, businesses),
        "metrics": {
            "extra_unserved_kwh": round(extra_unserved, 3),
            "shortfall_hours": sum(
                1
                for index, value in enumerate(with_new["unserved_kwh"])
                if value > without["unserved_kwh"][index]
            ),
            "surplus_absorbed_kwh": round(
                max(
                    without["total_curtailed_kwh"] - with_new["total_curtailed_kwh"],
                    0.0,
                ),
                3,
            ),
            "utilisation_before": utilisation(solar_kw, without, period_days),
            "utilisation_after": utilisation(solar_kw, with_new, period_days),
            "monthly_energy_kwh": round(monthly_energy, 3),
            "planned_monthly_energy_kwh": round(planned_monthly, 3),
            "businesses": business_months,
        },
        "simulation_trace": {
            "hours": period_days * 24,
            "without_new": {
                key: without[key]
                for key in ("stored_kwh", "unserved_kwh", "curtailed_kwh")
            },
            "with_new": {
                key: with_new[key]
                for key in ("stored_kwh", "unserved_kwh", "curtailed_kwh")
            },
        },
    }


def rank_key(outcome, monthly_revenue, lowest_stored_kwh):
    return (
        OUTCOME_RANK[outcome],
        -float(monthly_revenue or 0),
        -float(lowest_stored_kwh or 0),
    )
