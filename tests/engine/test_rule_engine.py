from datetime import datetime, timedelta, timezone

from engine.checks import energy_check, power_check, startup_check
from engine.evaluator import (
    decide_outcome,
    find_limiting_check,
    rank_key,
    run_assessment,
    weakest_label,
)
from engine.hours import night_hours, open_hours
from engine.profiles import build_hourly_profile, energy_from_counter
from engine.simulation import battery_limits, simulate

SETTINGS = {
    "reserve_factor": 0.2,
    "safety_margin": 0.1,
    "unserved_energy_tolerance_kwh": 0.5,
    "night_start_hour": 18,
    "night_end_hour": 6,
    "min_observed_days": 3,
}


def solar_day(peak):
    return [peak if 7 <= hour < 17 else 0.0 for hour in range(24)]


def site(**overrides):
    values = {
        "inverter_continuous_kw": 20.0,
        "inverter_surge_kw": 30.0,
        "inverter_surge_duration_s": 5,
        "battery_nominal_kwh": 100.0,
        "soc_min_percent": 20.0,
        "soc_max_percent": 90.0,
        "charge_efficiency": 0.95,
        "discharge_efficiency": 0.95,
        "max_charge_kw": 15.0,
        "max_discharge_kw": 15.0,
        "tariff_per_kwh": 4.5,
        "baseline_demand_kw": [2.0] * 24,
        "solar_profile": {"average_kw": solar_day(12.0), "low_sun_kw": solar_day(6.0)},
        "settings": dict(SETTINGS),
        "data_labels": {
            "baseline": "observed",
            "solar": "observed",
            "battery": "user_entered",
        },
    }
    values.update(overrides)
    return values


def business(
    kw=2.0, peak=None, startup=8.0, duration=3, hours=(8, 17), business_id="b1"
):
    load = [kw if hours[0] <= hour < hours[1] else 0.0 for hour in range(24)]
    return {
        "business_id": business_id,
        "business_name": f"Business {business_id}",
        "average_kw": load,
        "peak_kw": [value if peak is None or value == 0 else peak for value in load],
        "open_hours": set(range(*hours)),
        "days_per_month": 26,
        "startup_power_kw": startup,
        "startup_duration_s": duration,
        "startup_data_label": None if startup is None else "user_entered",
        "data_label": "observed",
    }


def test_power_passes_fails_and_is_unknown():
    assert power_check(site(), [business(peak=5)])["status"] == "pass"
    failed = power_check(site(), [business(peak=19)])
    assert failed["status"] == "fail"
    assert failed["causing_business_ids"] == ["b1"]
    assert (
        power_check(site(inverter_continuous_kw=None), [business()])["status"]
        == "unknown"
    )


def test_power_inside_safety_margin_is_flagged():
    result = power_check(site(), [business(peak=17)])
    assert result["status"] == "pass"
    assert result["within_margin"] is True


def test_startup_checks_surge_and_duration():
    assert startup_check(site(), [business(startup=29)])["status"] == "fail"
    assert startup_check(site(), [business(duration=9)])["status"] == "fail"
    assert startup_check(site(), [business(startup=None)])["status"] == "unknown"
    assert (
        startup_check(site(inverter_surge_kw=None), [business()])["status"] == "unknown"
    )
    assert startup_check(site(), [business()])["status"] == "pass"


def test_energy_compares_night_need_with_leftover_solar():
    assert energy_check(site(), [business(kw=2)], solar_day(12.0))["status"] == "pass"
    assert (
        energy_check(site(), [business(kw=5, hours=(18, 24))], solar_day(6.0))["status"]
        == "fail"
    )


def test_battery_never_leaves_its_limits():
    limits = battery_limits(site())
    run = simulate([5.0] * 24, solar_day(12.0), limits, 50.0, 3)
    assert min(run["stored_kwh"]) >= limits["min_stored"] - 1e-9
    assert max(run["stored_kwh"]) <= limits["max_stored"] + 1e-9


def test_outcome_rules():
    passing = {"status": "pass", "within_margin": False, "margin": 0.5}
    tight = {"status": "pass", "within_margin": True, "margin": 0.05}
    failing = {"status": "fail", "within_margin": False, "margin": -0.2}
    unknown = {"status": "unknown", "within_margin": False, "margin": None}
    checks = ("power", "startup", "energy", "battery")
    assert decide_outcome(dict.fromkeys(checks, passing)) == "feasible"
    assert (
        decide_outcome({**dict.fromkeys(checks, passing), "startup": unknown})
        == "conditionally_feasible"
    )
    assert (
        decide_outcome({**dict.fromkeys(checks, passing), "energy": tight})
        == "conditionally_feasible"
    )
    assert (
        decide_outcome({**dict.fromkeys(checks, passing), "battery": failing})
        == "not_feasible"
    )
    assert (
        find_limiting_check({**dict.fromkeys(checks, passing), "energy": tight})
        == "energy"
    )


def test_weakest_label_wins():
    assert weakest_label(site(), [business()]) == "user_entered"
    estimated = business()
    estimated["startup_data_label"] = "estimated"
    assert weakest_label(site(), [estimated]) == "estimated"


def test_small_daytime_load_is_feasible():
    result = run_assessment(
        site(), [business(kw=2, peak=3, startup=8)], 60.0, "average", 2
    )
    assert result["outcome"] == "feasible"
    assert result["revenue_basis"] == "planned"
    assert result["monthly_revenue"] == round(18 * 26 * 4.5, 2)
    assert len(result["simulation_trace"]["with_new"]["stored_kwh"]) == 48


def test_big_night_load_is_not_feasible():
    result = run_assessment(
        site(),
        [business(kw=12, peak=12, startup=None, hours=(18, 24))],
        30.0,
        "low_sun",
        3,
    )
    assert result["outcome"] == "not_feasible"
    assert result["check_results"]["battery"]["status"] == "fail"
    assert result["revenue_basis"] == "delivered"


def test_ranking_order():
    keys = [
        rank_key("not_feasible", 900, 50),
        rank_key("feasible", 100, 10),
        rank_key("feasible", 300, 5),
        rank_key("conditionally_feasible", 1000, 80),
    ]
    assert min(keys) == rank_key("feasible", 300, 5)
    assert max(keys) == rank_key("not_feasible", 900, 50)


def test_hours_helpers_handle_overnight():
    assert open_hours({"friday": {"open": 22, "close": 2}}) == {22, 23, 0, 1}
    assert night_hours(18, 6) == set(range(18, 24)) | set(range(6))


def test_counter_reset_uses_new_value():
    assert energy_from_counter([1.0, 1.5, 2.0, 0.2, 0.5]) == 1.5


def test_profile_ignores_closed_days():
    lusaka = timezone(timedelta(hours=2))
    monday = datetime(2026, 10, 19, 9, tzinfo=lusaka)
    sunday = datetime(2026, 10, 18, 9, tzinfo=lusaka)
    profile = build_hourly_profile(
        [(monday, 2000.0, 1.0), (sunday, 9000.0, 2.0)],
        {"monday": {"open": 8, "close": 17}},
        lusaka,
    )
    assert profile["average_kw"][9] == 2.0
    assert profile["observed_days"] == 2


def test_profile_converts_utc_readings_to_lusaka_hour():
    from datetime import datetime, timezone
    from zoneinfo import ZoneInfo

    lusaka = ZoneInfo("Africa/Lusaka")

    # 07:00 UTC is 09:00 in Lusaka.
    measured_at = datetime(2026, 10, 19, 7, 0, tzinfo=timezone.utc)

    profile = build_hourly_profile(
        [(measured_at, 2000.0, 1.0)],
        {"monday": {"open": 8, "close": 17}},
        lusaka,
    )

    assert profile["average_kw"][9] == 2.0
    assert profile["peak_kw"][9] == 2.0
    assert profile["average_kw"][7] == 0.0
    assert profile["observed_days"] == 1
