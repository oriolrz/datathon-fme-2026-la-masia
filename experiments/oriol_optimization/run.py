"""Laboratori per fases: calibrate -> validate -> confirm -> stress.

Cada política/període s'executa en un procés nou; la durada externa inclou
imports, inicialització, lectura, preprocessament i simulació oficial.
"""

import argparse
import hashlib
import importlib.util
import json
import platform
import subprocess
import sys
from pathlib import Path
from time import perf_counter

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / "artifacts/oriol_optimization"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write(path, value):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def context():
    import numpy as np
    import scipy
    from scripts.evaluate import load_hourly_data

    protocol = read(HERE / "protocol.json")
    official = ROOT.parent / "paquet_participants_datathon_upc"
    hourly = load_hourly_data(official)
    calibration = hourly.loc[hourly.index < protocol["calibration_end_exclusive"]]
    grid = (calibration.load_kw - calibration.pv_kw).clip(lower=0)
    parameters = {
        "mean_carbon": float((grid * calibration.co2_kg_per_kwh).sum() / grid.sum()),
        "mean_price": float((grid * calibration.precio_eur_per_kwh).sum() / grid.sum()),
    }
    return protocol, official, hourly, parameters


def worker(args):
    import numpy as np
    import pandas as pd
    import scipy
    from policies import make_policy, values_from_obs
    from scripts.evaluate import load_module

    protocol, official, hourly, parameters = context()
    split1, split2 = protocol["calibration_end_exclusive"], protocol["validation_end_exclusive"]
    if args.period == "calibration":
        hourly = hourly.loc[hourly.index < split1]
    elif args.period == "validation":
        hourly = hourly.loc[(hourly.index >= split1) & (hourly.index < split2)]
    elif args.period == "confirmation":
        hourly = hourly.loc[hourly.index >= split2]
    elif args.period != "full_diagnostic":
        raise ValueError(args.period)
    hourly = hourly.copy()
    hourly["load_kw"] *= args.load_multiplier
    configuration = next(item for item in protocol["grid"] if item["id"] == args.policy)
    np.random.seed(protocol["seed"])
    env_class = load_module(official / "starter_kit/environment.py", "official_environment").CampusBatteryEnv
    before = perf_counter()
    policy = make_policy(configuration, parameters)
    env = env_class(hourly)
    obs = env.reset()
    diagnostics = {key: 0 for key in ["empty_high_value", "full_low_value", "discharge_before_better_peak",
                                     "charge_without_profitable_24h_sale", "discharge_above_true_net", "partial_power"]}
    potential_exports = 0.0
    while obs is not None:
        values = values_from_obs(obs, parameters)
        action = policy.act(obs)
        if not isinstance(action, (float, int, np.number)) or not np.isfinite(action):
            raise RuntimeError(f"Consigna invàlida: {env.t}")
        true_net = max(0.0, float(hourly.load_kw.iloc[env.t] - hourly.pv_kw.iloc[env.t]))
        potential_exports += max(0.0, -action - true_net)
        diagnostics["discharge_above_true_net"] += int(action < -true_net - 1e-5)
        diagnostics["partial_power"] += int(1e-6 < abs(action) < 499.999)
        if values is not None and len(values) > 1:
            current, mean = values[0], float(np.mean(values))
            diagnostics["empty_high_value"] += int(obs["soc_kwh"] < 0.01 and current > mean + 0.2)
            diagnostics["full_low_value"] += int(obs["soc_kwh"] > 1999.99 and current < mean - 0.2)
            diagnostics["discharge_before_better_peak"] += int(action < -1 and max(values[1:]) * 0.9 > current + 0.05)
            diagnostics["charge_without_profitable_24h_sale"] += int(action > 1 and max(values[1:]) * 0.9 <= current)
        obs, _ = env.step(action)
    result = env.evaluate_results()
    result.update({
        "policy": args.policy, "family": configuration["family"], "configuration": configuration,
        "period": args.period, "load_multiplier": args.load_multiplier,
        "steps": len(hourly), "start": str(hourly.index[0]), "end": str(hourly.index[-1]),
        "simulation_seconds": perf_counter() - before,
        "soc_final_kwh": float(env.soc), "soc_min_kwh": float(min(env.soc_series)), "soc_max_kwh": float(max(env.soc_series)),
        "failures": getattr(policy, "failures", 0), "lp_calls": getattr(policy, "lp_calls", 0),
        "parameters": parameters, "diagnostics": diagnostics, "discharge_export_waste_kwh": potential_exports,
        "actions_sha256": hashlib.sha256(np.asarray(env.actions, dtype="<f8").tobytes()).hexdigest(),
        "monthly": {str(month): env.evaluate_results(mask=hourly.index.to_period("M") == month)
                    for month in hourly.index.to_period("M").unique()},
        "python": platform.python_version(), "numpy": np.__version__, "pandas": pd.__version__, "scipy": scipy.__version__,
    })
    print(json.dumps(result, allow_nan=False))


def execute(policy, period, multiplier=1.0):
    before = perf_counter()
    result = subprocess.run([sys.executable, "-B", "-X", "utf8", str(Path(__file__).resolve()),
                             "worker", "--policy", policy, "--period", period,
                             "--load-multiplier", str(multiplier)],
                            cwd=ROOT, capture_output=True, text=True, encoding="utf-8", timeout=120)
    if result.returncode:
        raise RuntimeError(result.stdout + result.stderr)
    row = json.loads(result.stdout)
    row["process_seconds"] = round(perf_counter() - before, 6)
    filename = f"{period}_{policy}_load{multiplier:.2f}.json"
    write(OUT / filename, row)
    print(f"{period:14} {policy:22} score={row['score']:.2f} CO2={row['co2_estalviat_pct']:.2f}% "
          f"cost={row['cost_estalviat_pct']:.2f}% infr={row['infraccions']} fail={row['failures']} "
          f"wall={row['process_seconds']:.2f}s", flush=True)
    return row


def safe(row):
    return row["infraccions"] == 0 and row["failures"] == 0 and row["process_seconds"] < 45


def frozen_hashes():
    return {name: digest(HERE / name) for name in ["policies.py", "protocol.json", "run.py", "requirements.txt"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=["worker", "calibrate", "validate", "confirm", "stress", "diagnostic"])
    parser.add_argument("--policy")
    parser.add_argument("--period", default="calibration")
    parser.add_argument("--load-multiplier", type=float, default=1.0)
    args = parser.parse_args()
    if args.phase == "worker":
        worker(args)
        return
    protocol = read(HERE / "protocol.json")
    hashes = frozen_hashes()
    if args.phase == "calibrate":
        rows = [execute(item["id"], "calibration") for item in protocol["grid"]]
        selected = {}
        for family in "ABCD":
            eligible = [row for row in rows if row["family"] == family and safe(row)]
            if eligible:
                selected[family] = max(eligible, key=lambda row: (row["score"], -row["process_seconds"]))["policy"]
        write(OUT / "calibration_selection.json", {"source_sha256": hashes, "rows": rows, "selected": selected})
    elif args.phase == "validate":
        calibration = read(OUT / "calibration_selection.json")
        if calibration["source_sha256"] != hashes:
            raise RuntimeError("El codi ha canviat després de calibrar; cal repetir calibratge")
        rows = [execute(policy, "validation") for policy in calibration["selected"].values()]
        stable = next(row for row in rows if row["policy"] == "stable")
        eligible = [row for row in rows if safe(row) and all(
            metrics["score"] >= stable["monthly"][month]["score"] - 0.20
            for month, metrics in row["monthly"].items())]
        winner = max(eligible, key=lambda row: (row["score"], -row["process_seconds"]))
        write(OUT / "validation_selection.json", {"source_sha256": hashes, "rows": rows, "winner": winner["policy"]})
    else:
        selection = read(OUT / "validation_selection.json")
        if selection["source_sha256"] != hashes:
            raise RuntimeError("El codi ha canviat després de validar; no es pot mirar confirmació amb aquesta versió")
        policies = list(dict.fromkeys(["stable", selection["winner"]]))
        if args.phase == "confirm":
            rows = [execute(policy, "confirmation") for policy in policies]
        elif args.phase == "stress":
            rows = [execute(policy, "confirmation", multiplier) for multiplier in protocol["stress_load_multipliers"] for policy in policies]
        else:
            rows = [execute(policy, "full_diagnostic") for policy in policies]
        write(OUT / f"{args.phase}_results.json", {"source_sha256": hashes, "rows": rows,
                                                  "selection_frozen_before_confirmation": selection["winner"]})


if __name__ == "__main__":
    main()
