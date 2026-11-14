"""Reserva de llindars 24h, amb els paràmetres congelats del prototip.

No estima demanda/solar ni conserva telemetria entre salts temporals.
Només consumeix els vectors coneguts que proporciona l'observació oficial.
"""

from math import isfinite

THRESHOLD = 0.20
MIN_ARBITRAGE_MARGIN = 0.05
WEIGHT_CO2 = 0.50  # Hiperparàmetre preexistent; no és el pes del score oficial.


def choose_action(obs: dict, load_forecast=None) -> float:
    """Consigna desitjada; agent.py aplica sempre el clamp central després."""
    try:
        raw_prices = obs.get("preus_properes_24h", [])
        raw_carbon = obs.get("co2_properes_24h", [])
        if isinstance(raw_prices, (str, bytes)) or isinstance(raw_carbon, (str, bytes)):
            return 0.0
        prices = [float(value) for value in raw_prices[:24]]
        carbon = [float(value) for value in raw_carbon[:24]]
    except (TypeError, ValueError, OverflowError, KeyError):
        return 0.0
    n = min(len(prices), len(carbon))
    if n < 3:
        return 0.0
    prices, carbon = prices[:n], carbon[:n]
    if not all(isfinite(value) for value in prices + carbon):
        return 0.0
    mean_price = sum(prices) / n
    mean_carbon = sum(carbon) / n
    if not (isfinite(mean_price) and isfinite(mean_carbon)):
        return 0.0
    if mean_price <= 1e-9 or mean_carbon <= 1e-9:
        return 0.0
    values = [
        WEIGHT_CO2 * c / (mean_carbon + 1e-9)
        + (1.0 - WEIGHT_CO2) * p / (mean_price + 1e-9)
        for p, c in zip(prices, carbon)
    ]
    current = values[0]
    mean_value = sum(values) / n
    if (current < mean_value - THRESHOLD
            and max(values) > current / 0.90 + MIN_ARBITRAGE_MARGIN):
        return 500.0
    if (current > mean_value + THRESHOLD
            and min(values) < 0.90 * current - MIN_ARBITRAGE_MARGIN):
        return -500.0
    return 0.0
