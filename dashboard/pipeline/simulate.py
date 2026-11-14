"""Executa un agent amb el CampusBatteryEnv OFICIAL i en desa la traça hora a hora."""

from __future__ import annotations

import importlib.util
from math import sqrt
from pathlib import Path
from time import perf_counter

import numpy as np
import pandas as pd


def load_env_class(kit: Path):
    spec = importlib.util.spec_from_file_location("upc_environment", Path(kit) / "starter_kit" / "environment.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.CampusBatteryEnv


def run(agent, hourly: pd.DataFrame, env_class, spec: dict) -> dict:
    env = env_class(hourly, spec=spec)
    obs = env.reset()
    done = False
    t0 = perf_counter()
    while not done:
        action = agent.act(obs)
        obs, done = env.step(action)
    runtime = perf_counter() - t0

    eta = sqrt(float(spec["efficiency"]))
    soc = np.asarray(env.soc_series, dtype=float)
    prev = np.r_[env.soc_init, soc[:-1]]
    dsoc = soc - prev
    applied = np.where(dsoc > 0, dsoc / eta, dsoc * eta)  # kW realment aplicats
    return {
        "requested": np.asarray(env.actions, dtype=float),
        "applied": applied,
        "soc": soc,
        "grid": np.asarray(env.grid, dtype=float),
        "export": np.asarray(env.exports, dtype=float),
        "infr": np.asarray(env.infraccions_per_step, dtype=int),
        "official": env.evaluate_results(),
        "runtime_s": runtime,
    }
