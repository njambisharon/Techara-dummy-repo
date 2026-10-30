def make_site(inverter=None):
    flat = [1.0] * 24
    return {
        "baseline_demand_kw": flat,
        "charge_efficiency": 0.95,
        "discharge_efficiency": 0.95,
        "inverter_continuous_kw": inverter,
        "solar_profile": {"average_kw": flat, "low_sun_kw": flat},
    }
