"""Auditoria local del paquet UPC, sense models ni exportació de dades brutes.

Ús: python -B analysis/audit_temporal.py --kit RUTA_ZIP --report reports/forecast_audit.md
Sense --report només imprimeix un resum JSON; llegeix el ZIP sense extreure'l.
Dependències: Python >= 3.10, pandas >= 2.0, numpy i la base de zones horàries tzdata.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd


COUNTER = "Contador - POTENCIA ACTIVA EXPORTADA (kW)"
PRICE = "precio_eur_per_kwh"
CO2 = "co2_kg_per_kwh"
HOUR = pd.Timedelta(hours=1)
REPO = Path(__file__).resolve().parents[1]
FILES = (
    "contador.csv", "inversor.csv", "precio_pvpc.csv", "co2_red.csv",
    "meteo.csv", "entradas_salidas.csv",
)


class Kit:
    """Accés de només lectura a un ZIP o al seu directori ja extret."""

    def __init__(self, path: Path):
        self.path = path.resolve(strict=True)
        self.archive = zipfile.ZipFile(self.path) if self.path.is_file() else None

    def read(self, name: str) -> bytes:
        if self.archive is not None:
            return self.archive.read(name)
        return (self.path / name).read_bytes()

    def close(self):
        if self.archive is not None:
            self.archive.close()


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def check(condition, message):
    if not condition:
        raise ValueError(message)


def fmt(value):
    if isinstance(value, (int, np.integer)):
        return str(value)
    if isinstance(value, (float, np.floating)):
        return f"{value:.6f}" if np.isfinite(value) else "—"
    return str(value).replace("|", "\\|").replace("\n", " ")


def table(headers, rows):
    return "\n".join([
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
        *("| " + " | ".join(fmt(v) for v in row) + " |" for row in rows),
    ])


def temporal_stats(df, minutes):
    ts = df.index
    step = pd.Timedelta(minutes=minutes)
    delta = ts.to_series().diff()
    expected = pd.date_range(ts.min(), ts.max(), freq=step)
    missing = expected.difference(ts)
    # No assignem silenciosament un offset a marques de temps locals ambigües.
    ambiguous = ts.tz_localize(
        "Europe/Madrid", ambiguous="NaT", nonexistent="shift_forward"
    ).isna().sum()
    nonexistent = ts.tz_localize(
        "Europe/Madrid", ambiguous=True, nonexistent="NaT"
    ).isna().sum()
    return {
        "rows": len(df), "columns": len(df.columns) + 1,
        "start": ts.min(), "end": ts.max(),
        "null_cells": int(df.isna().sum().sum()),
        "all_null_columns": int(df.isna().all().sum()),
        "duplicate_times": int(ts.duplicated().sum()),
        "duplicate_rows": int(df.copy().reset_index().duplicated().sum()),
        "backward_steps": int((delta < pd.Timedelta(0)).sum()),
        "off_grid": int(((ts.as_unit("ns").asi8 - expected[0].value) % step.value != 0).sum()),
        "regular_steps": int(delta.eq(step).sum()),
        "gaps": int(delta.gt(step).sum()), "missing_slots": len(missing),
        "dst_ambiguous": int(ambiguous), "dst_nonexistent": int(nonexistent),
    }


def block_ranges(index):
    if len(index) == 0:
        return []
    starts = np.r_[0, np.flatnonzero(np.diff(index.as_unit("ns").asi8) != HOUR.value) + 1]
    ends = np.r_[starts[1:], len(index)]
    return [(index[a], index[b - 1], int(b - a)) for a, b in zip(starts, ends)]


def unit(column):
    overrides = {
        "Fecha": "hora local, sense offset", "precio_eur_per_kwh": "€/kWh",
        "precio_eur_per_mwh": "€/MWh", "co2_kg_per_kwh": "kg CO₂/kWh",
        "porcentaje_con_emisiones": "%", "gen_con_emisiones_mw": "MW",
        "gen_sin_emisiones_mw": "MW",
    }
    if column in overrides:
        return overrides[column]
    if "FECHA" in column.upper():
        return "marca temporal auxiliar"
    if "(" in column and column.endswith(")"):
        return column.rsplit("(", 1)[1][:-1]
    if "SALIDA RELE" in column:
        return "estat binari segons guia"
    if "CALIDAD COM" in column:
        return "escala 0–100 segons guia"
    return "sense unitat / metadada"


def reproduce_tutorial(data, source):
    """Replica la cel·la 4 i la contrasta executant NOMÉS aquesta cel·la."""
    contador = data["contador.csv"]
    inversor = data["inversor.csv"]
    columns = []
    for i in (1, 2, 3):
        candidates = [
            c for c in inversor
            if f"INVERSOR {i}" in c.upper()
            and "POTENCIA ACTIVA" in c.upper() and "FASE" not in c.upper()
        ]
        # La cerca oficial també coincideix amb el setpoint percentual: pren el primer.
        check(candidates and candidates[0] == f"Inversor {i} - POTENCIA ACTIVA (kW)",
              f"El primer candidat del tutorial no és el total AC de l'inversor {i}")
        columns.append(candidates[0])
    load = (-contador[COUNTER]).clip(lower=0, upper=5000)
    solar = inversor[columns].fillna(0).sum(axis=1).clip(lower=0)
    hourly_load = load.resample("1h").mean().dropna()
    hourly_solar = solar.resample("1h").mean().dropna()
    hourly = pd.DataFrame({
        "load_kw": hourly_load, "pv_kw": hourly_solar,
        PRICE: data["precio_pvpc.csv"][PRICE], CO2: data["co2_red.csv"][CO2],
    }).dropna()
    notebook = json.loads(source)
    code = "".join(notebook["cells"][4]["source"])
    # Llista tancada: la cel·la inspeccionada només transforma aquests DataFrames.
    # No executem cap altra cel·la: ni entrenament, ni figures, ni empaquetament.
    expected_tokens = ("load_5min =", "pv_total_5min =", "df_campus_hourly =")
    check(all(token in code for token in expected_tokens), "Ha canviat el tutorial")
    import ast
    tree = ast.parse(code)
    check(not any(isinstance(node, (ast.Import, ast.ImportFrom)) for node in ast.walk(tree)),
          "La cel·la de preprocessament conté imports no previstos")
    check(not any(isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                  and node.func.id in {"open", "exec", "eval", "compile", "__import__"}
                  for node in ast.walk(tree)), "La cel·la conté execució no prevista")
    namespace = {"pd": pd, "print": lambda *args, **kwargs: None}
    for key, filename in (("df_contador", "contador.csv"), ("df_inversor", "inversor.csv"),
                          ("df_pvpc", "precio_pvpc.csv"), ("df_co2", "co2_red.csv")):
        namespace[key] = data[filename].copy().reset_index()
    exec(compile(tree, "tutorial.ipynb:cell4", "exec"), namespace)
    pd.testing.assert_frame_equal(hourly, namespace["df_campus_hourly"], check_exact=True)
    check(hourly.index.is_unique and hourly.index.is_monotonic_increasing,
          "Índex horari duplicat o desordenat")
    check(np.isfinite(hourly.to_numpy()).all(), "Valors horaris no finits")
    return hourly, columns, hourly_load, hourly_solar


def simulator_checks(kit, hourly):
    """Contrasta totes les observacions oficials amb les dades reals, acció zero."""
    source = kit.read("starter_kit/environment.py").decode("utf-8")
    namespace = {"__file__": "starter_kit/environment.py", "__name__": "upc_audit"}
    exec(compile(source, "starter_kit/environment.py", "exec"), namespace)
    spec = json.loads(kit.read("starter_kit/battery_spec.json"))
    check(float(spec.get("dt_hours", 1)) == 1, "El simulador ja no usa dt=1h")
    env = namespace["CampusBatteryEnv"](hourly, spec=spec)
    horizon_crossings = 0
    stale_lags = 0
    keys = None
    obs = env.reset()
    expected_keys = {
        "timestamp", "hour", "day_of_week", "soc_kwh", "soc_pct", "soc_percent",
        "preu_actual", "co2_actual", "preus_properes_24h", "co2_properes_24h", "noves_dades_5min",
    }
    for t in range(len(hourly)):
        keys = list(obs)
        check(set(obs) == expected_keys, "Han canviat les claus observables del motor")
        check(obs["timestamp"] == hourly.index[t], "Timestamp d'obs incorrecte")
        check(obs["hour"] == hourly.index[t].hour and
              obs["day_of_week"] == hourly.index[t].dayofweek, "Calendari incorrecte")
        check(obs["soc_kwh"] == env.soc_init and obs["soc_pct"] == env.soc_init / env.cap
              and obs["soc_percent"] == env.soc_init / env.cap * 100, "SOC observable incorrecte")
        check(obs["preus_properes_24h"] == hourly[PRICE].iloc[t:t + 24].tolist(),
              "Previsió de preu diferent del tall de files")
        check(obs["co2_properes_24h"] == hourly[CO2].iloc[t:t + 24].tolist(),
              "Previsió de CO₂ diferent del tall de files")
        check(obs["preu_actual"] == hourly[PRICE].iloc[t] and
              obs["co2_actual"] == hourly[CO2].iloc[t], "Valors actuals incorrectes")
        lag = max(0, t - 1)
        check(obs["noves_dades_5min"] == {
            "ultim_consum_kw": float(hourly["load_kw"].iloc[lag]),
            "ultima_solar_kw": float(hourly["pv_kw"].iloc[lag]),
        }, "Telemetria diferent de la fila anterior")
        if t and hourly.index[t] - hourly.index[t - 1] != HOUR:
            stale_lags += 1
        future = hourly.index[t:t + 24]
        if len(future) > 1 and (np.diff(future.as_unit("ns").asi8) != HOUR.value).any():
            horizon_crossings += 1
        next_obs, done = env.step(0.0)
        check(done == (t == len(hourly) - 1), "Final d'episodi incorrecte")
        check((next_obs is None) == done, "Observació final incorrecta")
        obs = next_obs
    expected_grid = np.maximum(hourly.load_kw - hourly.pv_kw, 0).to_numpy()
    np.testing.assert_allclose(env.grid, expected_grid, rtol=0, atol=1e-10)
    np.testing.assert_allclose(env.soc_series, env.soc_init, rtol=0, atol=1e-10)
    metrics = env.evaluate_results()
    check(metrics["infraccions"] == 0 and metrics["score"] == 0,
          "L'acció zero no reprodueix el balanç sense bateria")
    return {
        "keys": keys, "observations_checked": len(hourly),
        "horizon_crossings": horizon_crossings, "stale_lags": stale_lags,
        "short_horizons": min(23, len(hourly)), "metrics": metrics,
        "soc_initial_kwh": env.soc_init,
    }


def split_stats(hourly):
    periods = [
        ("Entrenament", "2025-09-01", "2026-03-01"),
        ("Validació de desenvolupament", "2026-03-01", "2026-06-01"),
        ("Reserva retrospectiva", "2026-06-01", "2026-09-01"),
    ]
    result = []
    for name, start, end in periods:
        subset = hourly.loc[(hourly.index >= start) & (hourly.index < end)]
        blocks = block_ranges(subset.index)
        # Decisió t amb telemetria fins a t-1: objectius t..t+23, com els vectors d'obs.
        origins = sum(max(0, n - 23) for _, _, n in blocks)
        result.append((name, start, end, len(subset), len(blocks), origins))
    check(sum(row[3] for row in result) == len(hourly), "Split incomplet")
    return result


def make_report(kit, payloads, data, stats, hourly, solar_cols, load_h, pv_h, sim, command):
    lines = []
    def add(text=""):
        lines.extend([text, ""])

    add("# Auditoria de dades temporals oficials UPC Sostenible")
    add("Responsable: Cesc · issue [#3](https://github.com/oriolrz/datathon-fme-2026-la-masia/issues/3) · "
        "branca `feat/cesc-forecast`. Auditoria del 14/11/2026. "
        "Abast autoritzat: `analysis/audit_temporal.py` i aquest informe. "
        "La issue es va consultar en només lectura (oberta, 0 comentaris); "
        "els documents compartits encara descriuen el repte com a provisional. "
        "Aquest treball aplica l'encàrrec explícit d'auditoria de Cesc; no implementa cap model.")
    add("## Procedència i reproduïbilitat")
    add(f"Paquet local: `{kit.path}`. Lectura directa en memòria, sense extracció ni còpia de CSV. "
        "La identitat d'origen és la del paquet proporcionat localment; no s'ha verificat cap signatura "
        "ni s'ha comparat amb una descàrrega nova del servidor.")
    if kit.archive is not None:
        add(f"SHA-256 del ZIP: `{digest(kit.path.read_bytes())}`.")
    add(f"Entorn: Python {platform.python_version()}, pandas {pd.__version__}, numpy {np.__version__}. "
        "Cap aleatorietat ni entrenament: no cal llavor. La base `Europe/Madrid` només s'usa per "
        "diagnosticar DST; la reproducció oficial conserva les marques de temps sense zona.")
    add(table(["Membre del paquet", "SHA-256"], [(name, digest(body)) for name, body in payloads.items()]))
    add("Ordre executable que ha generat aquest informe:\n\n```powershell\n" + command + "\n```")
    add("Per tornar a comprovar-ho sense escriure fitxers, executa la mateixa ordre sense `--report reports/forecast_audit.md`. "
        "`--expect-hours 5993` fa fallar l'execució si canvia el recompte. "
        "El script només admet aquest informe com a destinació d'escriptura.")

    add("## Inventari, temps i qualitat de les sis fonts")
    add(table(["CSV", "Files", "Columnes", "Inici", "Final", "Cel·les nul·les", "Columnes tot nul"], [
        (name, s["rows"], s["columns"], s["start"], s["end"], s["null_cells"], s["all_null_columns"])
        for name, s in stats.items()
    ]))
    add("`Fecha` és la clau temporal, sense offset ni zona a tots sis CSV. "
        "La guia declara hora local UTC+1/UTC+2; `Europe/Madrid` és la interpretació de calendari coherent "
        "amb aquesta declaració, no una zona codificada a les dades. "
        "La guia anomena `entrades_salides.csv` el fitxer que realment es diu `entradas_salidas.csv`. "
        "Els nuls totals inclouen metadades i canals no utilitzats; no equivalen a nuls de demanda.")
    add(table(["CSV", "Pas nominal (min)", "Passos regulars", "Salts", "Instants absents en el rang", "Timestamps duplicats", "Files duplicades", "Retrocessos", "Fora de graella"], [
        (name, 60 if name in ("precio_pvpc.csv", "co2_red.csv") else 5,
         s["regular_steps"], s["gaps"], s["missing_slots"], s["duplicate_times"],
         s["duplicate_rows"], s["backward_steps"], s["off_grid"])
        for name, s in stats.items()
    ]))
    add("Els instants absents es compten entre el primer i l'últim timestamp de cada font, en hora local "
        "sense zona; inclouen setmanes retirades, manca de novembre i avaries. No són tots errors de sensors.")
    add(table(["CSV", "Marques ambigües de tardor", "Marques inexistents de primavera"], [
        (name, s["dst_ambiguous"], s["dst_nonexistent"]) for name, s in stats.items()
    ]))
    add("Les hores de canvi d'horari de 26/10/2025 i 29/03/2026 cauen en setmanes absents "
        "del paquet: no es pot verificar com les fonts originals resolien l'hora repetida o inexistent. "
        "L'absència de duplicats no demostra que la sèrie sigui UTC ni que resolgui DST. "
        "Abans d'una conversió a UTC, cal obtenir la zona i el conveni d'ambigüitat de l'organització; "
        "no localitzar amb `ambiguous='infer'` a cegues ni inventar offsets.")

    add("## Variables, signe i agregació solar")
    add(table(["Família", "Unitats / significat", "Disponible en obs"], [
        ("Comptador: potència activa; reactiva; tensió; corrent; factor de potència",
         "kW; kVAr; V; A; adimensional", "Només la potència activa transformada i agregada, amb retard"),
        ("Energies importada/exportada i reactives", "kWh / kVArh; guia: acumuladors", "No"),
        ("Tres inversors: potència AC total, per fase, aparent/reactiva, DC i MPPT",
         "kW / kVA / kVAr; V; A; Hz", "Només suma AC agregada, amb retard"),
        ("Temperatures / aïllament / consignes / hores / diagnòstic dels inversors",
         "°C / Ohm / % / h / estats", "No"),
        ("Meteorologia: irradiància, temperatures, vent, hores sol pic",
         "W/m²; °C; m/s; h", "No, ni actual ni futura"),
        ("Entrades/sortides i metadades de comunicació", "Estats binaris i diagnòstic", "No"),
        ("PVPC i equivalent MWh", "€/kWh i €/MWh", "Només €/kWh actual i llista coneguda"),
        ("CO₂, percentatge emissor i potències de generació", "kg CO₂/kWh; %; MW",
         "Només intensitat actual i llista coneguda"),
    ]))
    counter = data["contador.csv"][COUNTER]
    inv = data["inversor.csv"][solar_cols]
    add(f"Comptador cru: {(counter < 0).sum()} valors negatius, {(counter == 0).sum()} zeros, "
        f"{(counter > 0).sum()} positius i {counter.isna().sum()} nuls; "
        f"rang [{counter.min():.3f}, {counter.max():.3f}] kW. "
        f"La inversió de signe dona importació positiva. El clip [0, 5000] del tutorial "
        f"afecta {(((-counter) < 0) | ((-counter) > 5000)).sum()} valors no nuls.")
    add("Columnes solars realment seleccionades: " + ", ".join(f"`{c}`" for c in solar_cols) + ". "
        "Se sumen els totals AC dels tres equips; afegir-hi les columnes per fase duplicaria potència. "
        "El tutorial substitueix cada nul de cada inversor per zero **abans** de sumar i després retalla "
        "només el total per sota de zero.")
    add("Fragilitat de la selecció del tutorial: el filtre de text també coincideix amb "
        "`SETPOINT RELATIVO POTENCIA ACTIVA (%)`; escull `[0]`, que en aquest CSV és el total AC en kW. "
        "El script comprova explícitament aquest primer candidat; reordenar columnes podria canviar "
        "el resultat oficial sense un error visible. No s'ha alterat el tutorial.")
    phase_rows = []
    for n, col in enumerate(solar_cols, 1):
        phases = data["inversor.csv"][[f"Inversor {n} - POTENCIA ACTIVA FASE {p} (kW)" for p in (1, 2, 3)]]
        error = (inv[col] - phases.sum(axis=1, min_count=3)).abs()
        phase_rows.append((col, inv[col].isna().sum(), (inv[col] < 0).sum(), inv[col].min(),
                           inv[col].max(), error.mean(), error.max()))
    add(table(["Total AC", "Nuls", "Negatius", "Mín. kW", "Màx. kW", "Error mitjà vs suma fases kW", "Error màxim kW"], phase_rows))
    add(f"Files amb algun inversor nul: {inv.isna().any(axis=1).sum()}; "
        f"amb tots tres nuls: {inv.isna().all(axis=1).sum()}. "
        "Les petites diferències entre totals AC i fases no proven una suma equivocada: poden incloure "
        "arrodoniments i manca de simultaneïtat; no es corregeixen sense evidència física.")
    solar_only = pv_h.index.difference(load_h.index)
    add("El `fillna(0)` introdueix una hora solar aparentment vàlida sense comptador vàlid: "
        + ", ".join(str(ts) for ts in solar_only) + ". "
        "En aquesta hora només hi ha telemetria nul·la dels tres inversors. "
        "La intersecció final la descarta gràcies al nul del comptador; no s'ha comptat com una hora útil.")
    energy_col = "Contador - ENERGIA ACTIVA IMPORTADA (kWh)"
    energy = data["contador.csv"][energy_col]
    regular = data["contador.csv"].index.to_series().diff().eq(pd.Timedelta(minutes=5))
    decreases = (energy.diff().lt(0) & regular).sum()
    add(f"La guia descriu `{energy_col}` com a acumulador, però hi ha {decreases} "
        "decrements entre mostres consecutives separades 5 minuts. No és un acumulador monòton usable "
        "sense aclarir resets/semàntica; no s'ha emprat per validar energia integrada ni signe físic.")
    add("**Possible doble comptatge físic:** la guia situa el comptador al PCC i descriu els negatius "
        "com a importació neta de solar; el tutorial anomena `load_kw=-comptador` i el motor després "
        "calcula `load_kw-pv_kw+acció`. Això podria restar dues vegades la generació. "
        "No ho resol el signe observat. S'ha reproduït exactament el contracte del simulador, "
        "sense canviar-lo; cal confirmar amb mentors si `load_kw` representa demanda bruta o importació al PCC.")

    add("## Reproducció exacta del tutorial i hores útils")
    add("S'ha replicat la cel·la 4 (`resample('1h').mean()`, signe, clips, zero dels inversors i "
        "intersecció final amb `.dropna()`) i s'ha executat separadament aquesta mateixa cel·la oficial "
        "en memòria. `pd.testing.assert_frame_equal` confirma igualtat de tota la taula. "
        "No s'han executat les cel·les de models, guardat de fitxers ni empaquetament.")
    add(table(["Etapa", "Hores no nul·les"], [
        ("Comptador agregat", len(load_h)), ("Solar agregada", len(pv_h)),
        ("PVPC", data["precio_pvpc.csv"][PRICE].notna().sum()),
        ("CO₂", data["co2_red.csv"][CO2].notna().sum()),
        ("Intersecció final tutorial", len(hourly)),
        ("Diferència respecte de 5993", len(hourly) - 5993),
    ]))
    union = load_h.index.union(pv_h.index).union(data["precio_pvpc.csv"].index).union(data["co2_red.csv"].index)
    presence = pd.DataFrame({
        "load": load_h.reindex(union).notna(), "pv": pv_h.reindex(union).notna(),
        "price": data["precio_pvpc.csv"][PRICE].reindex(union).notna(),
        "co2": data["co2_red.csv"][CO2].reindex(union).notna(),
    })
    add(table(["Disponibilitat a la unió (1=present)", "Hores"], [
        (" ".join(f"{k}={int(v)}" for k, v in zip(presence.columns, flags)), n)
        for flags, n in presence.value_counts(sort=False).items()
    ]))
    add(f"Rang final: {hourly.index.min()} → {hourly.index.max()}. "
        f"La graella local completa del rang tindria {len(pd.date_range(hourly.index.min(), hourly.index.max(), freq='1h'))} hores. "
        "«Útils» significa aquí acceptades pel tutorial; no garanteix 12 mostres vàlides a cada hora.")
    add(table(["Mes", "Hores"], [(str(month), n) for month, n in hourly.groupby(hourly.index.to_period("M")).size().items()]))
    add("Novembre de 2025 no apareix a la taula final. L'inversor acaba el 16/08/2026 a les 22:00, "
        "tot i que les altres fonts arriben al setembre. Les absències mensuals de la unió "
        "no s'han omplert ni s'han tractat com a temps físic transcorregut d'una hora.")

    load_count = data["contador.csv"][COUNTER].resample("1h").count().reindex(hourly.index)
    inv_count = inv.notna().all(axis=1).astype(int).resample("1h").sum().reindex(hourly.index)
    complete = load_count.eq(12) & inv_count.eq(12)
    partial = hourly.index[~complete]
    add(table(["Mostres vàlides en una hora", "Hores comptador", "Hores amb 3 inversors vàlids"], [
        (n, load_count.eq(n).sum(), inv_count.eq(n).sum())
        for n in sorted(set(load_count.tolist()) | set(inv_count.tolist()))
    ]))
    add(f"Hores amb 12 mostres vàlides de comptador i dels tres inversors: {complete.sum()}; "
        f"hores parcials en alguna de les dues fonts: {(~complete).sum()}. "
        "La cohort estricta és un diagnòstic de sensibilitat; no substitueix el preprocessament oficial.")
    add(table(["Hora parcial", "Mostres comptador", "Mostres amb 3 inversors vàlids"], [
        (ts, load_count.loc[ts], inv_count.loc[ts]) for ts in partial
    ]))
    add("`resample('1h')` usa intervals [h, h+1) amb etiqueta a l'esquerra: "
        "la mostra de 01:00 pertany a l'hora 01, no a l'hora 00. Els sensors comencen a 00:05; "
        "cal confirmar si les marques són instantànies o de final d'interval abans de reinterpretar energia. "
        "Les mitjanes són aritmètiques de potència (kW), no sumes de kW; a dt=1h tenen equivalència "
        "numèrica en kWh per al motor. Amb mostres parcials es pressuposa representativitat de la resta de l'hora.")

    add("## Discontinuïtats i risc d'alineació")
    gaps = []
    for t in range(1, len(hourly)):
        delta = hourly.index[t] - hourly.index[t - 1]
        if delta != HOUR:
            gaps.append((hourly.index[t - 1], hourly.index[t], delta / HOUR, int(delta / HOUR) - 1))
    add(table(["Última hora abans", "Primera hora després", "Salt (h)", "Hores absents"], gaps))
    blocks = block_ranges(hourly.index)
    add(f"{len(gaps)} salts i {len(blocks)} blocs contigus en hora local. "
        f"Total d'hores absents internes: {sum(row[3] for row in gaps)}. "
        "Un salt de 169 h deixa 168 hores absents; el de 889 h en deixa 888. "
        "El simulador conserva el SOC i només aplica dt=1h a cada fila, també a través dels salts; "
        "no simula consum, pèrdues ni accions durant les hores absents.")
    add(table(["Bloc", "Inici", "Final", "Hores"], [(i, a, b, n) for i, (a, b, n) in enumerate(blocks, 1)]))

    add("## Rangs, nuls i senyals atípics")
    quantities = hourly.assign(net_load_kw=hourly.load_kw - hourly.pv_kw)
    rows = []
    for col in quantities:
        s = quantities[col]
        q1, q3 = s.quantile([0.25, 0.75])
        iqr = q3 - q1
        rows.append((col, s.isna().sum(), s.min(), s.mean(), s.median(), s.quantile(.99),
                     s.max(), ((s < q1 - 1.5 * iqr) | (s > q3 + 1.5 * iqr)).sum()))
    add(table(["Variable", "Nuls", "Mín.", "Mitjana", "Mediana", "p99", "Màx.", "Fora IQR 1,5"], rows))
    add("Els llindars IQR són descriptius calculats sobre tota l'auditoria: "
        "no són paràmetres de neteja, ni criteris ajustats per entrenar. En solar, "
        "una distribució amb moltes nits a zero pot marcar hores diürnes normals. "
        "No s'ha eliminat cap outlier ni s'ha interpolat cap dada.")
    meteo = data["meteo.csv"]
    meteo_cols = [c for c in meteo if any(key in c for key in (
        "TEMPERATURA", "VELOCIDAD", "IRRADIANCIA (", "IRRADIANCIA 1",
        "IRRADIANCIA 2", "HORAS SOL PICO",
    ))]
    meteo_rows = []
    for col in meteo_cols:
        s = meteo[col]
        q1, q3 = s.quantile([.25, .75])
        iqr = q3 - q1
        meteo_rows.append((col, s.isna().sum(), s.min(), s.max(), s.eq(0).sum(),
                           s.lt(0).sum(), ((s < q1 - 1.5 * iqr) | (s > q3 + 1.5 * iqr)).sum()))
    add(table(["Meteorologia crua", "Nuls", "Mín.", "Màx.", "Zeros", "Negatius", "Fora IQR 1,5"], meteo_rows))
    add("El canal de vent és constant a zero en totes les mostres no nul·les: no aporta variació "
        "i no se'n pot inferir absència real de vent. Les hores de sol pic tenen valors negatius "
        "incompatibles amb la descripció d'energia acumulada normalitzada; la temperatura ambient "
        "màxima requereix contrast amb la qualitat/ubicació del sensor. La temperatura de panell "
        "negativa o alta i irradiàncies elevades no es declaren errònies només pel rang. "
        "Aquestes variables s'auditen, però no s'introdueixen com a features: no les exposa obs.")
    add(f"Demanda horària igual a zero: {hourly.load_kw.eq(0).sum()} h; "
        f"demanda neta negativa: {quantities.net_load_kw.lt(0).sum()} h; "
        f"demanda neta inferior a 500 kW: {quantities.net_load_kw.lt(500).sum()} h "
        f"({100 * quantities.net_load_kw.lt(500).mean():.4f}%). "
        "Zeros i demanda neta negativa poden alterar energia de referència i decisions de descàrrega; "
        "no es descarten sense aclarir si són fallades de telemetria o valors reals.")
    quality = data["contador.csv"]["Contador - CALIDAD COM"]
    low_quality = quality.lt(100)
    add(f"Comptador amb qualitat COM <100: {low_quality.sum()} mostres; "
        f"zeros de potència coincidents amb qualitat <100: {(counter.eq(0) & low_quality).sum()}. "
        "Aquesta coincidència és un indici d'incidència de comunicació, no una prova universal. "
        "Les marques de qualitat s'han mantingut fora de qualsevol feature perquè no arriben a `obs`.")
    raw_load_mean = (-counter).mean()
    add(f"Discrepància documental resolta: mitjana de demanda crua a 5 min = {raw_load_mean:.6f} kW; "
        f"mitjana horària consolidada = {hourly.load_kw.mean():.6f} kW. "
        "Les xifres aproximades 1115 i 1123 dels informes previs corresponen a poblacions i "
        "ponderacions diferents; no hi ha discrepància en el recompte de 5993 h.")
    price_ratio_error = (data["precio_pvpc.csv"].precio_eur_per_mwh / 1000 - data["precio_pvpc.csv"][PRICE]).abs().max()
    add(f"Coherència de preus: màxim error absolut entre €/MWh / 1000 i €/kWh = {price_ratio_error:.12g} €/kWh. "
        "Les sis fonts no contenen infinits en cap columna numèrica (comprovació explícita).")

    add("## Què coneix realment BatteryAgent.act(obs)")
    add(table(["Clau", "Unitat / contingut", "Disponibilitat comprovada"], [
        ("timestamp, hour, day_of_week", "Hora local sense zona; hora 0–23; dilluns=0",
         "Fila actual; calendari derivable, inclòs mes; no timestamps futurs"),
        ("soc_kwh, soc_pct, soc_percent", "kWh; fracció 0–1; percentatge 0–100", "Estat actual de la bateria"),
        ("preu_actual, co2_actual", "€/kWh; kg CO₂/kWh", "Fila actual"),
        ("preus_properes_24h, co2_properes_24h", "Llistes de longitud 1–24, mateixes unitats",
         "iloc[t:t+24]: inclouen t i arriben com a màxim a t+23 files; sense timestamps per element"),
        ("noves_dades_5min.ultim_consum_kw", "kW de demanda mitjana horària",
         "Fila anterior si t>0; fila actual si t=0"),
        ("noves_dades_5min.ultima_solar_kw", "kW de solar mitjana horària",
         "Fila anterior si t>0; fila actual si t=0"),
    ]))
    add(f"Comprovació dinàmica del motor oficial en {sim['observations_checked']} passos reals, "
        f"sempre amb acció 0 kW: balanç de xarxa exactament igual a max(load−pv, 0), "
        f"SOC constant a {sim['soc_initial_kwh']:.0f} kWh, "
        f"{sim['metrics']['infraccions']} infraccions i score {sim['metrics']['score']:.2f}. "
        "Aquesta prova valida el contracte i el balanç; no és un benchmark de cap política candidata.")
    add(f"Hi ha {sim['horizon_crossings']} decisions amb un salt dins la llista futura i "
        f"{sim['stale_lags']} decisions on la fila anterior no és l'hora anterior. "
        f"Les últimes {sim['short_horizons']} decisions tenen llistes de menys de 24 elements. "
        "Així, aquestes llistes no representen sempre 24 hores consecutives. "
        "L'agent pot detectar que el seu retard és obsolet comparant el timestamp actual amb l'anterior "
        "que ha guardat; no pot recuperar els timestamps futurs absents a partir d'obs.")
    add("**Excepció del primer pas:** `t=0` exposa el valor real de demanda i solar de la mateixa "
        "hora que el motor està a punt de simular. És el contracte local observat, no una "
        "disponibilitat causal generalitzable a totes les hores. Per avaluar forecasting, "
        "ometre aquesta telemetria al primer origen (o marcar explícitament la inicialització) "
        "i comprovar amb mentors si el servidor replica l'excepció.")
    add("No estan disponibles demanda/solar actuals quan t>0, demanda/solar futures, mostres de 5 min, "
        "meteorologia actual o futura, relés, fases, energies, qualitat COM, consum de les hores retirades "
        "ni components del mix de generació. Les previsions perfectes de preu i CO₂ sí que estan "
        "expressament autoritzades per aquest motor; no permeten afegir-hi altres futurs. "
        "La sola presència d'una columna al CSV no autoritza usar-la com a feature en temps de decisió.")

    add("## Proposta de validació temporal causal")
    add("Proposta determinista per a H=24 valors: l'hora actual t i les 23 següents, "
        "predits a la decisió t amb telemetria de demanda/solar només fins a t−1, "
        "coherent amb els vectors de preu/CO₂ d'obs dins d'un bloc contigu. "
        "Definida per dates de calendari abans d'ajustar cap forecast. El límit dret és exclusiu:")
    splits = split_stats(hourly)
    add(table(["Partició", "Inici inclòs", "Final exclòs", "Hores", "Blocs contigus", "Orígens amb 24 objectius contigus interns"], splits))
    add("1. Entrenar només amb dates d'entrenament; ajustar imputació causal, escalat, selecció de "
        "variables i qualsevol llindar exclusivament dins el train de cada fold. Sense barreja aleatòria de files.\n"
        "2. Per entrenar exemples multi-horitzó, un origen t només és admissible si totes les etiquetes "
        "t…t+23 existeixen al mateix bloc i partició; comprovar timestamps, no només posicions. "
        "Purgar els últims H−1 orígens de cada bloc. Això evita finestres que travessin splits o salts; "
        "si canvia H o l'alineament dels objectius, recalcular la purga.\n"
        "3. Construir lags per unió amb timestamp exacte (t−1h, t−24h, t−168h); un `.shift(24)` "
        "sobre files és incorrecte al costat d'un buit. No interpolar amb valors posteriors, "
        "no usar rolling centrat ni `bfill`, i no passar a través de setmanes retirades.\n"
        "4. Reproduir l'ordre d'obs: a la decisió t>0 només entren a l'estat de demanda/solar els "
        "valors que el motor revela de la fila anterior; les observacions d'etiquetes futures només "
        "es revelen quan toca. La història de validació ja observada es pot actualitzar causalment "
        "en línia; els pesos i hiperparàmetres es mantenen congelats durant cada avaluació. "
        "Els perfils estacionals de validació no es recalculen amb tot el bloc.\n"
        "5. Per ajustar opcions dins del train, usar folds expansius amb validació desembre, gener "
        "i febrer, entrenant sempre en mesos estrictament anteriors i aplicant la mateixa purga. "
        "Novembre absent no s'interpola. Una configuració final es congela abans d'obrir la reserva.\n"
        "6. Avaluar cada partició amb agent nou, SOC inicial oficial 1000 kWh i sense mirar més "
        "enllà del final de la partició; dins d'aquesta, conservar el SOC entre blocs tal com fa el motor. "
        "Si es reporta una prova independent per bloc, reinicialitzar-la explícitament i no barrejar "
        "aquests scores amb els d'una simulació contínua. Caldrà comprovar el contracte d'estat inicial "
        "de la telemetria al primer pas.\n"
        "7. Reportar error de forecasting per horitzó i bloc amb nombre d'exemples; i, quan s'integri "
        "una política, score, costos, CO₂, infraccions, SOC final i runtime sobre el mateix protocol. "
        "Calcular el score global amb les sumes dels denominadors oficials, no la mitjana dels scores mensuals.")
    add("**Límit d'independència:** els informes compartits indiquen que la política anterior es va "
        "triar mirant totes les 5993 h i ja en publiquen resultats mensuals. Cap subconjunt d'aquest "
        "paquet es pot presentar com a holdout històricament intacte de l'equip. Aquest split evita "
        "fugues de features, etiquetes i preprocessament en nous forecasts si s'aplica el protocol; "
        "la reserva continua sent retrospectiva. Només dades realment noves o el test ocult poden "
        "donar una confirmació independent. L'auditoria tampoc acredita el preprocessament del servidor.")

    add("## Comprovacions executades, límits i següent tasca")
    add("Passades: lectura dels sis CSV; esquema i hashes; timestamps vàlids, únics i ordenats; "
        "graella nominal; duplicats de fila; nuls de totes les columnes; absència d'infinits numèrics; "
        "diagnòstic DST; signe/clips; selecció dels tres inversors i contrast amb fases; "
        "igualtat exacta amb la cel·la oficial de preprocessament; cobertura intrahorària; "
        "rangs i IQR; blocs; splits; totes les observacions i balanç sense acció del motor oficial. "
        "Les anomalies de dades es documenten: no es tracten com un error del script.")
    add("Pendents que afecten interpretació: demanda bruta vs comptador net al PCC; semàntica de "
        "les marques temporals i acumuladors; qualitat dels zeros; contracte del servidor per a "
        "telemetria inicial, DST i previsions que travessen buits. No s'ha executat cap model, "
        "validador de submissió, dry-run web ni tramesa; no s'ha fet commit, push ni merge.")
    add("Següent tasca recomanada: acordar aquest split i el contracte causal amb l'integrador, "
        "resoldre amb mentors el balanç PCC/solar i la telemetria inicial, i després definir una "
        "baseline estacional de demanda neta que consumeixi exactament obs. Implementar-la requerirà "
        "un nou abast autoritzat; aquí només hi ha auditoria.")

    add("## Annex: diccionari complet de columnes i nuls")
    add("Noms i recomptes agregats, sense valors de sensors, identificadors de dispositius ni files brutes. "
        "Les unitats de les columnes s'infereixen del nom i de la guia; «sense unitat / metadada» "
        "no implica una magnitud física coneguda. Els sufixos `.1` procedeixen del CSV llegit amb pandas.")
    for name, df in data.items():
        add(f"<details>\n<summary>{name}</summary>\n\n" + table(
            ["Columna", "Tipus llegit", "Unitat / classe", "Nuls"],
            [("Fecha", "datetime sense zona", unit("Fecha"), 0)] +
            [(col, str(df[col].dtype), unit(col), int(df[col].isna().sum())) for col in df],
        ) + "\n\n</details>")
    return "\n".join(lines), splits


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kit", type=Path, required=True, help="ZIP oficial o directori extret")
    parser.add_argument("--report", type=Path, help="Única sortida admesa: reports/forecast_audit.md")
    parser.add_argument("--expect-hours", type=int, help="Recompte esperat; discrepància = error")
    args = parser.parse_args()
    if args.report is not None:
        check(args.report.resolve() == (REPO / "reports/forecast_audit.md").resolve(),
              "La sortida ha de ser reports/forecast_audit.md dins d'aquest repositori")
    kit = Kit(args.kit)
    try:
        import io
        names = [f"data/train/{name}" for name in FILES] + [
            "starter_kit/tutorial.ipynb", "starter_kit/environment.py",
            "docs/GUIA_VARIABLES.md", "starter_kit/battery_spec.json",
        ]
        payloads = {name: kit.read(name) for name in names}
        data, stats = {}, {}
        for name in FILES:
            df = pd.read_csv(io.BytesIO(payloads[f"data/train/{name}"]))
            df["Fecha"] = pd.to_datetime(df["Fecha"], errors="raise")
            check(df["Fecha"].notna().all(), f"Timestamp nul a {name}")
            df = df.set_index("Fecha")
            check(df.index.tz is None, f"La font {name} ara incorpora zona: revisar preprocessament")
            check(df.index.is_unique and df.index.is_monotonic_increasing,
                  f"Timestamps duplicats o desordenats a {name}; no s'arreglen silenciosament")
            check(not np.isinf(df.select_dtypes(include="number").to_numpy(dtype=float)).any(),
                  f"Infinits numèrics a {name}")
            data[name] = df
            stats[name] = temporal_stats(df, 60 if name in ("precio_pvpc.csv", "co2_red.csv") else 5)
        hourly, columns, load_h, pv_h = reproduce_tutorial(
            data, payloads["starter_kit/tutorial.ipynb"].decode("utf-8")
        )
        if args.expect_hours is not None:
            check(len(hourly) == args.expect_hours,
                  f"Hores obtingudes {len(hourly)}, esperades {args.expect_hours}")
        sim = simulator_checks(kit, hourly)
        # Una ordre PowerShell literal, sense dependència de PATH ni instal·lacions noves.
        def quote(value):
            return "'" + str(value).replace("'", "''") + "'"
        command = "& " + quote(sys.executable) + " -B analysis/audit_temporal.py --kit " + quote(kit.path)
        if args.expect_hours is not None:
            command += f" --expect-hours {args.expect_hours}"
        if args.report is not None:
            command += " --report reports/forecast_audit.md"
        report, splits = make_report(
            kit, payloads, data, stats, hourly, columns, load_h, pv_h, sim, command
        )
        if args.report is not None:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(report, encoding="utf-8", newline="\n")
        print(json.dumps({
            "status": "ok", "hours": len(hourly), "difference_vs_5993": len(hourly) - 5993,
            "start": str(hourly.index.min()), "end": str(hourly.index.max()),
            "contiguous_blocks": len(block_ranges(hourly.index)),
            "load_mean_kw": float(hourly.load_kw.mean()), "pv_mean_kw": float(hourly.pv_kw.mean()),
            "simulator": sim, "splits": splits,
            "report": str(args.report) if args.report is not None else None,
        }, ensure_ascii=True))
    finally:
        kit.close()


if __name__ == "__main__":
    main()
