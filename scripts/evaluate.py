"""Backtest reproduïble amb el preprocessament i environment.py oficials.

Les particions són diagnòstics del train ja explorat, mai holdouts independents.
No copia dades oficials al repositori ni modifica el Starter Kit.
"""

import argparse
import hashlib
import importlib.util
import json
import platform
import random
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_hourly_data(official_root):
    """Transcripció de les dues primeres cel·les de dades del tutorial oficial."""
    data_dir = Path(official_root) / "data" / "train"
    meter = pd.read_csv(data_dir / "contador.csv", parse_dates=["Fecha"]).set_index("Fecha")
    inverter = pd.read_csv(data_dir / "inversor.csv", parse_dates=["Fecha"]).set_index("Fecha")
    prices = pd.read_csv(data_dir / "precio_pvpc.csv", parse_dates=["Fecha"]).set_index("Fecha")
    carbon = pd.read_csv(data_dir / "co2_red.csv", parse_dates=["Fecha"]).set_index("Fecha")
    load = (-meter["Contador - POTENCIA ACTIVA EXPORTADA (kW)"]).clip(lower=0, upper=5000)
    pv_columns = [
        [column for column in inverter.columns
         if f"INVERSOR {i}" in column.upper()
         and "POTENCIA ACTIVA" in column.upper() and "FASE" not in column.upper()][0]
        for i in (1, 2, 3)
    ]
    pv = sum(inverter[column].fillna(0) for column in pv_columns).clip(lower=0)
    hourly = pd.DataFrame({
        "load_kw": load.resample("1h").mean().dropna(),
        "pv_kw": pv.resample("1h").mean().dropna(),
        "precio_eur_per_kwh": prices["precio_eur_per_kwh"],
        "co2_kg_per_kwh": carbon["co2_kg_per_kwh"],
    }).dropna()
    if hourly.empty or not hourly.index.is_monotonic_increasing or not hourly.index.is_unique:
        raise ValueError("La unió horària ha de ser no buida, ordenada i sense duplicats")
    if not np.isfinite(hourly.to_numpy()).all():
        raise ValueError("Dades horàries no finites")
    hourly.index.name = "Fecha"
    return hourly


class StandbyAgent:
    def act(self, obs):
        return 0.0


class ClampedReference:
    def __init__(self, reference_class):
        self.reference = reference_class()

    def act(self, obs):
        from src.safety import clamp_action

        return clamp_action(self.reference.act(obs), obs["soc_kwh"])


def simulate(factory, hourly, env_class):
    started = perf_counter()
    agent = factory()
    env = env_class(hourly)
    obs = env.reset()
    agent_seconds = 0.0
    while obs is not None:
        before = perf_counter()
        action = agent.act(obs)
        agent_seconds += perf_counter() - before
        if not isinstance(action, (int, float, np.number)) or not np.isfinite(action):
            raise ValueError(f"Consigna no numèrica/finita al pas {env.t}")
        obs, _ = env.step(action)
    metrics = env.evaluate_results()
    actions = np.asarray(env.actions)
    metrics.update({
        "runtime_seconds": round(perf_counter() - started, 6),
        "agent_seconds": round(agent_seconds, 6),
        "steps": env.t,
        "soc_initial_kwh": env.soc_init,
        "soc_final_kwh": float(env.soc),
        "soc_min_observed_kwh": float(min(env.soc_series)),
        "soc_max_observed_kwh": float(max(env.soc_series)),
        "charge_steps": int(np.sum(actions > 0)),
        "discharge_steps": int(np.sum(actions < 0)),
        "standby_steps": int(np.sum(actions == 0)),
        "policy_failures": getattr(agent, "policy_failures", 0),
        "actions_sha256": hashlib.sha256(np.asarray(env.actions, dtype="<f8").tobytes()).hexdigest(),
    })
    return metrics


def main():
    sys.path.insert(0, str(ROOT))
    from agent import BatteryAgent

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--official-root", type=Path, default=ROOT.parent / "paquet_participants_datathon_upc")
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts" / "evaluation")
    parser.add_argument("--split-date", default="2026-03-01")
    parser.add_argument("--seed", type=int, default=20261114)
    parser.add_argument("--candidate-policy", type=Path, help="Mòdul local amb choose_action(obs,load_forecast=None)")
    args = parser.parse_args()
    total_started = perf_counter()
    random.seed(args.seed)
    np.random.seed(args.seed)
    official = args.official_root.resolve()
    env_module = load_module(official / "starter_kit/environment.py", "upc_environment")
    reference = load_module(official / "starter_kit/agent.py", "upc_reference").BatteryAgent
    prototype = load_module(ROOT / "prototypes/upc/agent_v0_24h.py", "upc_prototype").BatteryAgent
    hourly = load_hourly_data(official)
    split = pd.Timestamp(args.split_date)
    periods = {
        "train_full": hourly,
        "train_early_diagnostic": hourly.loc[hourly.index < split],
        "train_late_diagnostic": hourly.loc[hourly.index >= split],
    }
    if any(frame.empty for frame in periods.values()):
        raise ValueError("La data de tall ha de deixar dos blocs no buits")
    factories = {
        "standby": StandbyAgent,
        "official_reference": reference,
        "official_reference_clamped": lambda: ClampedReference(reference),
        "prototype_24h": prototype,
        "battery_agent_fallback": BatteryAgent,
    }
    if args.candidate_policy:
        candidate = load_module(args.candidate_policy.resolve(), "candidate_policy").choose_action
        factories["candidate_policy"] = lambda: BatteryAgent(policy=candidate)
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    dirty = bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip())
    source_files = ["agent.py", "src/__init__.py", "src/safety.py", "src/fallback.py", "scripts/evaluate.py",
                    "scripts/package.py", "scripts/verify_submission.py", "tests/test_battery_agent.py",
                    "tests/test_package.py", "prototypes/upc/agent_v0_24h.py", "requirements-validation.txt"]
    fingerprints = {name: sha256(ROOT / name) for name in source_files}
    if args.candidate_policy:
        fingerprints["candidate_policy"] = sha256(args.candidate_policy)
    inputs = {f"data/train/{name}.csv": sha256(official / f"data/train/{name}.csv")
              for name in ("contador", "inversor", "precio_pvpc", "co2_red")}
    for name in ("environment.py", "agent.py", "battery_spec.json", "tutorial.ipynb", "check_submission.py"):
        inputs[f"starter_kit/{name}"] = sha256(official / "starter_kit" / name)
    report = {
        "schema_version": 1,
        "run_id": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
        "commit": commit, "working_tree_dirty": dirty,
        "source_sha256": fingerprints, "official_sha256": inputs,
        "seed": args.seed,
        "data_role": "train_explored_not_independent_validation",
        "split_date": args.split_date,
        "protocol": "Cada període reinicia agent i SOC a 1000 kWh; vectors limitats al període. "
                    "Els salts interns conserven SOC; no s'interpolen hores absents. "
                    "Blocs diagnòstics del train ja explorat, sense ajustar paràmetres.",
        "python": platform.python_version(), "platform": platform.platform(),
        "numpy": np.__version__, "pandas": pd.__version__,
        "export_price_eur_per_kwh": 0.0, "penalty_points_per_violation": 0.20,
        "runtime_scope": "Instanciació agent + entorn + passos + evaluate_results; sense lectura/preprocessament/imports.",
        "rows": [],
    }
    for period, frame in periods.items():
        gaps = frame.index.to_series().diff().dropna()
        for name, factory in factories.items():
            metrics = simulate(factory, frame, env_module.CampusBatteryEnv)
            row = {
                "period": period, "policy": name,
                "start": str(frame.index[0]), "end": str(frame.index[-1]),
                "gap_count": int((gaps != pd.Timedelta(hours=1)).sum()),
                "max_gap_hours": float(gaps.max() / pd.Timedelta(hours=1)),
                **metrics,
            }
            report["rows"].append(row)
            print(f"{period:24s} {name:28s} score={row['score']:.2f} "
                  f"CO2={row['co2_estalviat_pct']:.2f}% cost={row['cost_estalviat_pct']:.2f}% "
                  f"infraccions={row['infraccions']} temps={row['runtime_seconds']:.3f}s")
    report["total_command_seconds_before_write"] = round(perf_counter() - total_started, 6)
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "metrics.json").write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    pd.DataFrame(report["rows"]).to_csv(args.output / "metrics.csv", index=False)
    # El fitxer de retorn s'escriu abans de rebutjar una candidata insegura/lenta.
    stable = [row for row in report["rows"] if row["policy"] in ("battery_agent_fallback", "candidate_policy")]
    if any(row["infraccions"] or row["policy_failures"] or row["runtime_seconds"] >= 60 for row in stable):
        raise SystemExit("ERROR: agent/candidata amb infraccions, errors de política o runtime >=60s")


if __name__ == "__main__":
    main()
