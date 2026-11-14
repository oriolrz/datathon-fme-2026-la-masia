"""Límit teòric: pla òptim amb informació perfecta (consum, solar, preu i CO2 futurs).

No és implementable (coneix el futur), però respon una pregunta de decisió clau:
**quanta puntuació queda per guanyar** amb la bateria i les dades d'aquest període.

Maximitzar 0.7*dCO2 + 0.3*dCost equival a minimitzar sum_t w_t * grid_t amb
    w_t = 0.7 * co2_t / CO2_base + 0.3 * preu_t / Cost_base
perquè els denominadors del score són constants. És un programa lineal exacte
sobre la dinàmica de environment.py (eta_c = eta_d = sqrt(0.9), exportació a 0 €).
"""

from __future__ import annotations

from math import sqrt

import numpy as np
import pandas as pd
from scipy.optimize import linprog
from scipy.sparse import coo_matrix, hstack, identity, vstack


def oracle_plan(hourly: pd.DataFrame, spec: dict, alpha=0.7, beta=0.3, power_margin=1e-3) -> np.ndarray:
    load = hourly["load_kw"].to_numpy()
    pv = hourly["pv_kw"].to_numpy()
    price = hourly["precio_eur_per_kwh"].to_numpy()
    co2 = hourly["co2_kg_per_kwh"].to_numpy()
    n = len(load)
    cap = float(spec["capacity_kwh"]) * float(spec["soc_max"])
    pmax = float(spec["power_kw"]) - power_margin
    eta = sqrt(float(spec["efficiency"]))
    soc0 = float(spec["soc_init"]) * float(spec["capacity_kwh"])

    net = load - pv
    base = np.maximum(net, 0)
    w = alpha * co2 / float(np.sum(base * co2)) + beta * price / float(np.sum(base * price))
    w = w / float(np.mean(w))  # escala ~1: evita problemes de tolerància numèrica a HiGHS

    # Variables: [c (n), d (n), s (n), g (n)]
    I = identity(n, format="coo")
    shift = coo_matrix((np.ones(n - 1), (np.arange(1, n), np.arange(n - 1))), shape=(n, n))
    # s_t - s_{t-1} - eta*c_t + d_t/eta = 0  (s_{-1} = soc0)
    A_eq = hstack([-eta * I, (1 / eta) * I, I - shift, coo_matrix((n, n))])
    b_eq = np.zeros(n)
    b_eq[0] = soc0
    # c_t - d_t - g_t <= -net_t   (g_t >= net_t + p_t)
    A_ub = hstack([I, -I, coo_matrix((n, n)), -I])
    b_ub = -net
    tiny = 1e-7 * float(np.mean(w))  # desempata: evita carregar i descarregar alhora
    cost = np.concatenate([np.full(n, tiny), np.full(n, tiny), np.zeros(n), w])
    bounds = [(0, pmax)] * (2 * n) + [(0, cap)] * n + [(0, None)] * n
    res = linprog(cost, A_ub=A_ub.tocsr(), b_ub=b_ub, A_eq=A_eq.tocsr(), b_eq=b_eq,
                  bounds=bounds, method="highs")
    if res.status != 0:
        raise RuntimeError(f"LP de l'òptim teòric no resolt: {res.message}")
    c, d = res.x[:n], res.x[n:2 * n]
    return c - d
