"""La MasIA: primera política de bateria, sense dependències externes.

Candidata de treball: comparar les pròximes 24 h de preu/CO2, protegint el SOC.
Validar amb el simulador i la web oficial abans de trametre al leaderboard.
"""
from math import sqrt


class BatteryAgent:
    def __init__(self):
        self.capacity_kwh = 2000.0
        self.max_power_kw = 500.0
        self.eta = sqrt(0.90)
        self.threshold = 0.20
        self.min_arbitrage_margin = 0.05
        self.weight_co2 = 0.50  # Empíric; no confondre amb 70% de la funció oficial.

    def act(self, obs: dict) -> float:
        soc = float(obs["soc_kwh"])
        prices = [float(x) for x in obs["preus_properes_24h"]]
        carbon = [float(x) for x in obs["co2_properes_24h"]]
        n = min(len(prices), len(carbon))

        desired = 0.0
        if n >= 3:
            prices = prices[:n]
            carbon = carbon[:n]
            mean_price = sum(prices) / n
            mean_carbon = sum(carbon) / n
            values = [
                self.weight_co2 * c / (mean_carbon + 1e-9)
                + (1.0 - self.weight_co2) * p / (mean_price + 1e-9)
                for p, c in zip(prices, carbon)
            ]
            current = values[0]
            mean_value = sum(values) / n
            if (current < mean_value - self.threshold
                    and max(values) > current / 0.90 + self.min_arbitrage_margin):
                desired = self.max_power_kw
            elif (current > mean_value + self.threshold
                    and min(values) < 0.90 * current - self.min_arbitrage_margin):
                desired = -self.max_power_kw

        # Física exacta del motor oficial. Marge de seguretat anticlipping.
        epsilon = 1e-4
        max_charge = max(0.0, min(self.max_power_kw,
                                  (self.capacity_kwh - soc) / self.eta - epsilon))
        max_discharge = max(0.0, min(self.max_power_kw,
                                     soc * self.eta - epsilon))
        return float(max(-max_discharge, min(max_charge, desired)))
