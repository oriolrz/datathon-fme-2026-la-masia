"""Clamp exclusiu Hard: defaults 6.000 kWh/1.500 kW; Standard queda intacte."""

from math import isfinite, sqrt

ETA = sqrt(0.9)
EPSILON = 1e-4


def limits(obs):
    try:
        capacity = float(obs.get("cap_max_kwh", 6000.0))
        power = float(obs.get("power_max_kw", 1500.0))
        soc = float(obs["soc_kwh"])
    except (AttributeError, KeyError, TypeError, ValueError, OverflowError):
        return None
    if not all(isfinite(v) for v in (capacity, power, soc)) or capacity <= 0 or power <= 0:
        return None
    if not 0 <= soc <= capacity:
        return None
    return capacity, power, soc


def power_bounds(obs):
    state = limits(obs)
    if state is None:
        return 0.0, 0.0
    capacity, power, soc = state
    charge = max(0.0, min(power, (capacity-soc)/ETA-EPSILON))
    discharge = max(0.0, min(power, soc*ETA-EPSILON))
    return -discharge, charge


def clamp_action(action, obs):
    try:
        value = float(action)
    except (TypeError, ValueError, OverflowError):
        return 0.0
    if not isfinite(value):
        return 0.0
    low, high = power_bounds(obs)
    return float(max(low, min(high, value)))
