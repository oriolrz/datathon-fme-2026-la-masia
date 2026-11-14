"""Física de battery_spec.json: pas d'1 h, 2 MWh, 500 kW i rendiment 90%."""

from math import isfinite, sqrt

CAPACITY_KWH = 2000.0
MAX_POWER_KW = 500.0
ETA = sqrt(0.9)
EPSILON_KW = 1e-4


def valid_soc(soc_kwh) -> bool:
    try:
        soc = float(soc_kwh)
    except (TypeError, ValueError, OverflowError):
        return False
    return isfinite(soc) and 0.0 <= soc <= CAPACITY_KWH


def power_bounds(soc_kwh) -> tuple:
    """Retorna (mínim, màxim) en kW, amb marge abans de saturar el SOC.

    L'epsilon es resta als límits d'energia convertits a potència. No es
    resta a ±500 kW quan hi ha prou energia/capacitat disponible.
    Un SOC absent, no finit o fora de rang implica repòs.
    """
    if not valid_soc(soc_kwh):
        return 0.0, 0.0
    soc = float(soc_kwh)
    charge = max(0.0, min(MAX_POWER_KW, (CAPACITY_KWH - soc) / ETA - EPSILON_KW))
    discharge = max(0.0, min(MAX_POWER_KW, soc * ETA - EPSILON_KW))
    return -discharge, charge


def clamp_action(action_kw, soc_kwh) -> float:
    """Una única sortida finita i físicament executable; positiu = càrrega."""
    try:
        action = float(action_kw)
    except (TypeError, ValueError, OverflowError):
        return 0.0
    if not isfinite(action):
        return 0.0
    low, high = power_bounds(soc_kwh)
    return float(max(low, min(high, action)))
