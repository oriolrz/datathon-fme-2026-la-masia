"""Límit clairvoyant de calibratge; NO és una política causal ni lliurable."""

import json
import sys
from pathlib import Path
from time import perf_counter

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))

import numpy as np

from policies import solve_plan
from run import OUT, context, read, write


def main():
    protocol, official, hourly, parameters = context()
    hourly = hourly.loc[hourly.index < protocol["calibration_end_exclusive"]]
    net = (hourly.load_kw - hourly.pv_kw).to_numpy()
    price, carbon = hourly.precio_eur_per_kwh.to_numpy(), hourly.co2_kg_per_kwh.to_numpy()
    base = np.maximum(net, 0)
    values = .7 * carbon / parameters["mean_carbon"] + .3 * price / parameters["mean_price"]
    before = perf_counter()
    actions, result = solve_plan(values, 1000.0, net)
    grid = result.x[3 * len(hourly):]
    score = 100 * (.7 * (1 - (grid @ carbon) / (base @ carbon)) + .3 * (1 - (grid @ price) / (base @ price)))
    report = {
        "label": "clairvoyant_calibration_LP_not_deployable",
        "information": "Totes les hores futures de demanda, PV, preu i CO2 del calibratge; SOC final lliure.",
        "steps": len(hourly), "score_upper_bound_relaxation": float(score),
        "solver_seconds": perf_counter() - before,
        "explanation": "Relaxació sense epsilon amb informació futura completa; no és evidència de generalització. Cost throughput 1e-8 negligible.",
    }
    write(OUT / "oracle_calibration.json", report)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
