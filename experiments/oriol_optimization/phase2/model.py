"""Ablacions causals independents del MPC congelat i adaptador de forecast."""

from datetime import datetime, timedelta

import numpy as np

from experiments.oriol_optimization.policies import MPCPolicy, solve_plan, values_from_obs
from src.fallback import choose_action as fallback_action
from src.safety import ETA, clamp_action, valid_soc


def timestamp_of(obs):
    ts = obs.get("timestamp")
    return ts.to_pydatetime() if hasattr(ts, "to_pydatetime") else datetime.fromisoformat(str(ts))


class ForecastAdapter:
    """Interfície futura: callback(obs,horizon=n)->n consums nets.

    No importa ni modifica src/forecast.py. Un callback extern només es
    podrà activar després d'auditar-ne la causalitat i els fitxers locals.
    """

    def __init__(self, profile, mode="seasonal", callback=None):
        self.profile, self.mode, self.callback = profile, mode, callback
        self.previous = None
        self.failures = 0

    def predict(self, obs, horizon):
        now = timestamp_of(obs)
        times = [now + timedelta(hours=i) for i in range(horizon)]
        seasonal = np.asarray([self.profile[t.weekday()][t.hour] for t in times], dtype=float)
        contiguous = self.previous is not None and (now - self.previous).total_seconds() == 3600
        self.previous = now
        if self.callback is not None:
            try:
                result = np.asarray(self.callback(obs, horizon=horizon), dtype=float)
                if result.shape != (horizon,) or not np.isfinite(result).all():
                    raise ValueError("Format de forecast invàlid")
                return result
            except (ValueError, TypeError, RuntimeError):
                self.failures += 1
                return seasonal
        if self.mode == "persistence" and contiguous:
            telemetry = obs.get("noves_dades_5min", {})
            try:
                last = float(telemetry["ultim_consum_kw"]) - float(telemetry["ultima_solar_kw"])
                if np.isfinite(last):
                    return np.full(horizon, max(0.0, last))
            except (KeyError, TypeError, ValueError):
                pass
        if self.mode == "constant":
            return np.full(horizon, 500.0)
        return seasonal


class AdvancedMPC:
    def __init__(self, configuration, training, forecast_callback=None):
        self.configuration = configuration
        normalizer = "unweighted" if configuration["normalization"] == "unweighted" else "weighted"
        self.parameters = training[normalizer].copy()
        self.forecaster = ForecastAdapter(training["profile"], configuration["forecast"], forecast_callback)
        self.previous = None
        # Prior d'una setmana, après uniquement en calibratge.
        self.energy = training["mean_net"] * 168.0
        self.carbon = self.energy * self.parameters["mean_carbon"]
        self.cost = self.energy * self.parameters["mean_price"]
        self.failures = 0
        self.lp_calls = 0
        self.last_forecast = None

    def act(self, obs):
        if not isinstance(obs, dict) or not valid_soc(obs.get("soc_kwh")):
            return 0.0
        now = timestamp_of(obs)
        if self.configuration["normalization"] == "online" and self.previous is not None:
            previous_ts, price, carbon = self.previous
            if (now - previous_ts).total_seconds() == 3600:
                telemetry = obs.get("noves_dades_5min", {})
                try:
                    net = max(0.0, float(telemetry["ultim_consum_kw"]) - float(telemetry["ultima_solar_kw"]))
                    if np.isfinite(net):
                        self.energy += net
                        self.carbon += net * carbon
                        self.cost += net * price
                        self.parameters = {"mean_carbon": self.carbon / self.energy, "mean_price": self.cost / self.energy}
                except (KeyError, ValueError, TypeError):
                    pass
        self.previous = now, float(obs.get("preu_actual", 0)), float(obs.get("co2_actual", 0))
        values = values_from_obs(obs, self.parameters)
        if values is None:
            self.failures += 1
            return clamp_action(fallback_action(obs), obs["soc_kwh"])
        available = len(values)
        n = min(available, self.configuration["horizon"])
        self.last_forecast = self.forecaster.predict(obs, n)
        # Preveure més de 500 kW no canvia el valor marginal de l'acció.
        net = np.clip(self.last_forecast, -500.0, 500.0)
        values = values[:n]
        actual_end = available < 24 and n == available
        terminal = self.configuration["terminal"]
        target, shadow = None, 0.0
        if not actual_end:
            if terminal == "fixed":
                target = 1000.0
            elif terminal == "dynamic":
                late_value = float(np.mean(values[-min(6, n):]))
                target = 2000.0 * (1 - float(np.mean(values <= late_value)))
            elif terminal == "shadow":
                shadow = ETA * float(np.mean(values))
        try:
            self.lp_calls += 1
            if terminal == "soft" and not actual_end:
                action = soft_terminal_plan(values, float(obs["soc_kwh"]), net)
            else:
                actions, _ = solve_plan(values, float(obs["soc_kwh"]), net, terminal_value=shadow, terminal_target=target)
                action = float(actions[0])
            return clamp_action(action, obs["soc_kwh"])
        except (RuntimeError, ValueError):
            self.failures += 1
            return clamp_action(fallback_action(obs), obs["soc_kwh"])


def soft_terminal_plan(values, soc, net):
    """Penalització lambda*abs(SOC_final-1000), sense obligar SOC final."""
    from scipy.optimize import linprog

    n = len(values)
    objective = np.zeros(4*n + 2)
    objective[:2*n] = 1e-8
    objective[3*n:4*n] = values
    objective[-2:] = .5 * ETA * float(np.mean(values))
    equality = np.zeros((n + 1, 4*n + 2))
    rhs = np.zeros(n + 1)
    rhs[0], rhs[-1] = soc, 1000.0
    for i in range(n):
        equality[i, i], equality[i, n+i], equality[i, 2*n+i] = -ETA, 1/ETA, 1
        if i:
            equality[i, 2*n+i-1] = -1
    equality[-1, 3*n-1], equality[-1, -2], equality[-1, -1] = 1, -1, 1
    inequality = np.zeros((n, 4*n + 2))
    for i in range(n):
        inequality[i, i], inequality[i, n+i], inequality[i, 3*n+i] = 1, -1, -1
    bounds = [(0,500)]*(2*n) + [(0,2000)]*n + [(0,None)]*(n+2)
    result = linprog(objective, A_eq=equality, b_eq=rhs, A_ub=inequality, b_ub=-net,
                     bounds=bounds, method="highs", options={"time_limit": .5})
    if not result.success or not np.isfinite(result.x).all():
        raise RuntimeError("LP suau no resolt")
    if np.any(np.minimum(result.x[:n], result.x[n:2*n]) > 1e-5):
        raise RuntimeError("Càrrega/descàrrega simultànies")
    return float(result.x[0] - result.x[n])
