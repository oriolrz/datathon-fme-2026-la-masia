"""Recàlcul independent dels KPI (mateixa fórmula que evaluate_results).

El frontend fa exactament aquest càlcul en TypeScript per a qualsevol filtre temporal;
els tests comproven que coincideix amb el simulador oficial.
"""

from __future__ import annotations

import numpy as np


def recompute(load, pv, price, co2, applied, infr, mask=None, alpha=0.7, beta=0.3, penalty=0.002,
              export_price=0.0) -> dict:
    load, pv, price, co2, applied, infr = map(np.asarray, (load, pv, price, co2, applied, infr))
    net = load - pv + applied
    grid = np.maximum(net, 0)
    exp = np.maximum(-net, 0)
    base = np.maximum(load - pv, 0)
    if mask is not None:
        m = np.asarray(mask, bool)
        grid, exp, base, price, co2, infr = grid[m], exp[m], base[m], price[m], co2[m], infr[m]
    cost = float(np.sum(grid * price) - np.sum(exp * export_price))
    em = float(np.sum(grid * co2))
    cb, eb = float(np.sum(base * price)), float(np.sum(base * co2))
    d_co2 = (eb - em) / eb if eb > 0 else 0.0
    d_cost = (cb - cost) / cb if cb > 0 else 0.0
    n_inf = int(np.sum(infr))
    return {"score": round(max(0.0, (alpha * d_co2 + beta * d_cost - penalty * n_inf) * 100), 2),
            "co2_pct": round(d_co2 * 100, 2), "cost_pct": round(d_cost * 100, 2), "infr": n_inf}
