def battery_limits(site):
    nominal = site["battery_nominal_kwh"]
    min_stored = nominal * site["soc_min_percent"] / 100
    max_stored = nominal * site["soc_max_percent"] / 100
    return {
        "min_stored": min_stored,
        "max_stored": max_stored,
        "usable": max_stored - min_stored,
        "charge_efficiency": site["charge_efficiency"],
        "discharge_efficiency": site["discharge_efficiency"],
        "max_charge_kw": site["max_charge_kw"],
        "max_discharge_kw": site["max_discharge_kw"],
    }


def simulate(load_kw, solar_kw, limits, initial_stored, days):
    stored = min(max(initial_stored, limits["min_stored"]), limits["max_stored"])
    stored_trace = []
    unserved_trace = []
    curtailed_trace = []
    lowest = stored
    for _ in range(days):
        for hour in range(24):
            net = solar_kw[hour] - load_kw[hour]
            unserved = 0.0
            curtailed = 0.0
            if net >= 0:
                room = (limits["max_stored"] - stored) / limits["charge_efficiency"]
                charge_in = max(min(net, limits["max_charge_kw"], room), 0.0)
                stored += charge_in * limits["charge_efficiency"]
                curtailed = net - charge_in
            else:
                need = -net
                available = (stored - limits["min_stored"]) * limits[
                    "discharge_efficiency"
                ]
                discharge_out = max(
                    min(need, limits["max_discharge_kw"], available), 0.0
                )
                stored -= discharge_out / limits["discharge_efficiency"]
                unserved = need - discharge_out
            lowest = min(lowest, stored)
            stored_trace.append(round(stored, 4))
            unserved_trace.append(round(unserved, 4))
            curtailed_trace.append(round(curtailed, 4))
    return {
        "stored_kwh": stored_trace,
        "unserved_kwh": unserved_trace,
        "curtailed_kwh": curtailed_trace,
        "total_unserved_kwh": round(sum(unserved_trace), 4),
        "total_curtailed_kwh": round(sum(curtailed_trace), 4),
        "lowest_stored_kwh": round(lowest, 4),
    }
