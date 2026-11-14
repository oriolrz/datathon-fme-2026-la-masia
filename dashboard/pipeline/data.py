"""Taula horària del campus, transcripció exacta de starter_kit/tutorial.ipynb."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


def load_hourly(kit: Path) -> pd.DataFrame:
    data_dir = Path(kit) / "data" / "train"
    meter = pd.read_csv(data_dir / "contador.csv", parse_dates=["Fecha"]).set_index("Fecha")
    inverter = pd.read_csv(data_dir / "inversor.csv", parse_dates=["Fecha"]).set_index("Fecha")
    prices = pd.read_csv(data_dir / "precio_pvpc.csv", parse_dates=["Fecha"]).set_index("Fecha")
    carbon = pd.read_csv(data_dir / "co2_red.csv", parse_dates=["Fecha"]).set_index("Fecha")

    load = (-meter["Contador - POTENCIA ACTIVA EXPORTADA (kW)"]).clip(lower=0, upper=5000)
    cols = []
    for i in (1, 2, 3):
        cols.append([c for c in inverter.columns
                     if f"INVERSOR {i}" in c.upper() and "POTENCIA ACTIVA" in c.upper()
                     and "FASE" not in c.upper()][0])
    pv = (inverter[cols[0]].fillna(0) + inverter[cols[1]].fillna(0) + inverter[cols[2]].fillna(0)).clip(lower=0)

    hourly = pd.DataFrame({
        "load_kw": load.resample("1h").mean().dropna(),
        "pv_kw": pv.resample("1h").mean().dropna(),
        "precio_eur_per_kwh": prices["precio_eur_per_kwh"],
        "co2_kg_per_kwh": carbon["co2_kg_per_kwh"],
    }).dropna()
    hourly.index.name = "Fecha"
    if hourly.empty or not hourly.index.is_monotonic_increasing or not hourly.index.is_unique:
        raise ValueError("Taula horària buida, desordenada o amb duplicats")
    if not np.isfinite(hourly.to_numpy()).all():
        raise ValueError("Taula horària amb valors no finits")
    return hourly


def contiguous_blocks(index: pd.DatetimeIndex) -> list[dict]:
    """Trams consecutius d'1 h (el simulador els encadena sense reiniciar el SOC)."""
    gaps = np.where(np.diff(index.values).astype("timedelta64[h]").astype(int) != 1)[0]
    starts = np.r_[0, gaps + 1]
    ends = np.r_[gaps, len(index) - 1]
    return [{"i0": int(s), "i1": int(e), "start": index[s].isoformat(), "end": index[e].isoformat(),
             "hours": int(e - s + 1)} for s, e in zip(starts, ends)]
