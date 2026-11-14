"""Candidates causals independents; només obs i paràmetres de calibratge.

No s'importen policy/mpc/forecast dels companys. Cap observació futura de
demanda o solar s'utilitza. El LP prediu demanda neta constant de 500 kW:
en règim de demanda >=500, el balanç marginal és exacte sense preveure-la.
"""

from math import isfinite

import numpy as np

from src.fallback import choose_action as fallback_action
from src.safety import CAPACITY_KWH, ETA, clamp_action, valid_soc


def values_from_obs(obs, parameters):
    try:
        prices = np.asarray(obs.get("preus_properes_24h", []), dtype=float)[:24]
        carbon = np.asarray(obs.get("co2_properes_24h", []), dtype=float)[:24]
        n = min(len(prices), len(carbon))
        if n == 0 or not np.isfinite(prices[:n]).all() or not np.isfinite(carbon[:n]).all():
            return None
        values = 0.7 * carbon[:n] / parameters["mean_carbon"] + 0.3 * prices[:n] / parameters["mean_price"]
        if "preu_actual" in obs and "co2_actual" in obs:
            values[0] = (0.7 * float(obs["co2_actual"]) / parameters["mean_carbon"]
                         + 0.3 * float(obs["preu_actual"]) / parameters["mean_price"])
        if not np.isfinite(values).all() or np.any(values <= 0):
            return None  # Fora del domini convex provat: reserva segura.
        return values
    except (TypeError, ValueError, IndexError, ZeroDivisionError):
        return None


class MarginalPolicy:
    def __init__(self, parameters, margin=0.20, **options):
        self.parameters = parameters
        self.margin = margin
        self.failures = 0

    def desired(self, obs, values):
        if len(values) < 3:
            return 0.0
        current, mean = values[0], float(np.mean(values))
        if current < mean - self.margin and max(values) * 0.9 > current + 0.05:
            return 500.0
        if current > mean + self.margin and min(values) < current * 0.9 - 0.05:
            return -500.0
        return 0.0

    def act(self, obs):
        if not isinstance(obs, dict) or not valid_soc(obs.get("soc_kwh")):
            return 0.0
        values = values_from_obs(obs, self.parameters)
        if values is None:
            self.failures += 1
            return clamp_action(fallback_action(obs), obs["soc_kwh"])
        return clamp_action(self.desired(obs, values), obs["soc_kwh"])


class ReservePolicy(MarginalPolicy):
    """Reserva per pics millors abans de la propera recàrrega rendible.

    Descarrega només el SOC sobrant després de reservar 500/eta kWh per
    cada hora de més valor abans d'una vall de recàrrega. En carregar,
    espera una vall millor si abans no hi ha cap descàrrega rendible.
    """

    def desired(self, obs, values):
        if len(values) < 2:
            return 0.0
        current = values[0]
        soc = float(obs["soc_kwh"])
        mean = float(np.mean(values))
        if current > mean + self.margin and min(values[1:]) < current * 0.9:
            cheaper = np.flatnonzero(values[1:] < current * 0.9 - self.margin)
            stop = int(cheaper[0] + 1) if len(cheaper) else len(values)
            better_slots = int(np.sum(values[1:stop] > current + self.margin))
            reserve = min(CAPACITY_KWH, better_slots * 500.0 / ETA)
            return -min(500.0, max(0.0, soc - reserve) * ETA)
        if current < mean - self.margin and max(values[1:]) * 0.9 > current:
            cheaper = np.flatnonzero(values[1:] < current - self.margin)
            stop = int(cheaper[0] + 1) if len(cheaper) else len(values)
            sales = int(np.sum(values[1:stop] * 0.9 > current + self.margin))
            target = min(CAPACITY_KWH, sales * 500.0 / ETA)
            return min(500.0, max(0.0, target - soc) / ETA)
        return 0.0


def solve_plan(values, soc, net_load, terminal_value=0.0, terminal_target=None):
    """LP: x=(charge, discharge, SOC_next, grid_import), un bloc per variable.

    Min sum(v*grid)+1e-8*throughput-terminal_value*SOC_final.
    grid>=net_load+charge-discharge, grid>=0: exportació sense remuneració.
    Amb v>0, terminal_value>=0 i cost de throughput, la càrrega/descàrrega
    simultània no aporta avantatge; es comprova també després de resoldre.
    """
    from scipy.optimize import linprog
    from scipy.sparse import coo_matrix

    n = len(values)
    objective = np.zeros(4 * n)
    objective[:2 * n] = 1e-8
    objective[3 * n:] = values
    objective[3 * n - 1] = -terminal_value
    rows, cols, data = [], [], []
    for i in range(n):
        for col, value in [(i, -ETA), (n + i, 1.0 / ETA), (2 * n + i, 1.0)]:
            rows.append(i); cols.append(col); data.append(value)
        if i:
            rows.append(i); cols.append(2 * n + i - 1); data.append(-1.0)
    equality = coo_matrix((data, (rows, cols)), shape=(n, 4 * n)).tocsr()
    rhs = np.zeros(n)
    rhs[0] = soc
    rows, cols, data = [], [], []
    for i in range(n):
        for col, value in [(i, 1.0), (n + i, -1.0), (3 * n + i, -1.0)]:
            rows.append(i); cols.append(col); data.append(value)
    inequality = coo_matrix((data, (rows, cols)), shape=(n, 4 * n)).tocsr()
    bounds = [(0.0, 500.0)] * (2 * n) + [(0.0, CAPACITY_KWH)] * n + [(0.0, None)] * n
    if terminal_target is not None:
        bounds[3 * n - 1] = (terminal_target, terminal_target)
    result = linprog(objective, A_ub=inequality, b_ub=-np.asarray(net_load),
                     A_eq=equality, b_eq=rhs, bounds=bounds, method="highs",
                     options={"time_limit": 10.0 if n > 24 else 0.5})
    if not result.success or not np.isfinite(result.x).all():
        raise RuntimeError(f"LP no òptim: {result.status}")
    charge, discharge = result.x[:n], result.x[n:2*n]
    if np.any(np.minimum(charge, discharge) > 1e-5):
        raise RuntimeError("LP amb càrrega/descàrrega simultània")
    return charge - discharge, result


class MPCPolicy(MarginalPolicy):
    def __init__(self, parameters, terminal_factor=0.5, terminal_target=None, replan_every=1, **options):
        super().__init__(parameters)
        self.terminal_factor = terminal_factor
        self.terminal_target = terminal_target
        self.replan_every = replan_every
        self.lp_calls = 0
        self._plan = []
        self._previous_timestamp = None

    def desired(self, obs, values):
        from datetime import datetime

        timestamp = obs.get("timestamp")
        try:
            now = timestamp.to_pydatetime() if hasattr(timestamp, "to_pydatetime") else datetime.fromisoformat(str(timestamp))
            contiguous = self._previous_timestamp is not None and (now - self._previous_timestamp).total_seconds() == 3600
        except (TypeError, ValueError):
            now, contiguous = None, False
        self._previous_timestamp = now
        if not contiguous:
            self._plan = []
        if self._plan:
            return self._plan.pop(0)
        # Una previsió més curta és la cua coneguda del motor oficial.
        # No s'afegeix cap dada futura fora d'aquest vector.
        terminal_value = self.terminal_factor * ETA * float(np.mean(values)) if len(values) == 24 else 0.0
        target = self.terminal_target if len(values) == 24 else None
        try:
            self.lp_calls += 1
            plan, _ = solve_plan(values, float(obs["soc_kwh"]), np.full(len(values), 500.0),
                                 terminal_value=terminal_value, terminal_target=target)
            self._plan = plan[1:self.replan_every].tolist()
            return float(plan[0])
        except (ValueError, RuntimeError):
            self.failures += 1
            return fallback_action(obs)


def make_policy(configuration, parameters):
    kind = configuration["kind"]
    options = {key: value for key, value in configuration.items() if key not in {"id", "family", "kind"}}
    if kind == "stable":
        from agent import BatteryAgent
        return BatteryAgent()
    return {"marginal": MarginalPolicy, "reserve": ReservePolicy, "mpc": MPCPolicy}[kind](parameters, **options)
