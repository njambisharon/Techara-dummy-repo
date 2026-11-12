from zoneinfo import ZoneInfo

SITE_TIMEZONE = ZoneInfo("Africa/Lusaka")

SUGGESTED_SETTINGS = {
    "reserve_factor": 0.2,
    "safety_margin": 0.1,
    "unserved_energy_tolerance_kwh": 0.5,
    "night_start_hour": 18,
    "night_end_hour": 6,
    "min_observed_days": 1,
}
