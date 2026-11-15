"""Entrena A/B/C, valida només març–maig i genera l'informe reproduïble.

python -B analysis/forecast_baselines.py --kit RUTA_ZIP --write-model --report
Sense les dues opcions d'escriptura, comprova paràmetres i recalcula mètriques.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import platform
import pprint
import runpy
import sys
import unittest
from time import perf_counter
from pathlib import Path

import numpy as np
import pandas as pd

from audit_temporal import Kit, COUNTER, HOUR, block_ranges, reproduce_tutorial, table as audit_table


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src/forecast.py"
REPORT = ROOT / "reports/forecast_baselines.md"
TRAIN_START, TRAIN_END = "2025-09-01", "2026-03-01"
VALID_START, VALID_END = "2026-03-01", "2026-06-01"
EXPECTED_TRAIN, EXPECTED_VALID, RESERVE_HOURS = 2784, 1704, 1505
METHODS, LEADS = ("A", "B", "C"), (1, 6, 24)
SCORE_RULE = "MAE mitjà dels 24 horitzons sobre les mateixes finestres completes"


def table(headers, rows):
    return audit_table(headers, [("—" if value is None else value for value in row) for row in rows])


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def load_data(kit):
    data, hashes = {}, {}
    for name in ("contador.csv", "inversor.csv", "precio_pvpc.csv", "co2_red.csv"):
        body = kit.read("data/train/" + name)
        hashes[name] = hashlib.sha256(body).hexdigest()
        df = pd.read_csv(io.BytesIO(body), parse_dates=["Fecha"]).set_index("Fecha")
        # Reserva descartada abans de construir cap target, feature o diagnòstic.
        df = df.loc[df.index < VALID_END].copy()
        require(df.index.is_unique and df.index.is_monotonic_increasing, "Índex no vàlid")
        data[name] = df
    hourly, solar_cols, _, _ = reproduce_tutorial(
        data, kit.read("starter_kit/tutorial.ipynb").decode("utf-8")
    )
    require(len(hourly.loc[hourly.index < TRAIN_END]) == EXPECTED_TRAIN, "Train diferent del congelat")
    require(len(hourly.loc[hourly.index >= VALID_START]) == EXPECTED_VALID, "Validació diferent de la congelada")
    require(hourly.index.max() < pd.Timestamp(VALID_END), "S'ha llegit la reserva com a target")
    counter = data["contador.csv"]
    inverter = data["inversor.csv"]
    lc = counter[COUNTER].resample("1h").count().reindex(hourly.index)
    pc = inverter[solar_cols].notna().all(axis=1).astype(int).resample("1h").sum().reindex(hourly.index)
    # Indicadors exclusivament diagnòstics, mai inputs dels predictors.
    suspect_5min = counter[COUNTER].eq(0) | counter["Contador - CALIDAD COM"].lt(100)
    suspect_5min |= (-counter[COUNTER]).lt(0) | (-counter[COUNTER]).gt(5000)
    quality = pd.DataFrame({
        "suspect": suspect_5min.resample("1h").max().reindex(hourly.index).fillna(False),
        "incomplete": lc.ne(12) | pc.ne(12),
    })
    return hourly, quality, hashes


def fit_parameters(hourly):
    """El tall temporal forma part de l'entrenament, no és responsabilitat del caller."""
    train = hourly.loc[(hourly.index >= TRAIN_START) & (hourly.index < TRAIN_END)]
    require(len(train) == EXPECTED_TRAIN, "No es pot ajustar sobre una partició diferent")
    target = train.load_kw - train.pv_kw
    require(np.isfinite(target).all(), "Target no finit")
    global_median = float(target.median())
    hourly_medians = target.groupby(target.index.hour).median()
    weekly = target.groupby([target.index.dayofweek, target.index.hour]).median()
    counts = target.groupby([target.index.dayofweek, target.index.hour]).size()
    profile = tuple(tuple(round(float(weekly.get((d, h), hourly_medians.get(h, global_median))), 6)
                          for h in range(24)) for d in range(7))
    residuals = np.asarray([target.iloc[i] - profile[t.dayofweek][t.hour]
                            for i, t in enumerate(train.index)])
    # Quantil fixat prèviament, exclusivament sobre residus del train.
    module = runpy.run_path(str(SOURCE))
    quantile = module["RESIDUAL_CLIP_QUANTILE"]
    return {
        "weekly": profile, "global": round(global_median, 6),
        "residual_clip": round(float(np.quantile(np.abs(residuals), quantile)), 6),
        "train_hours": len(train), "train_start": TRAIN_START, "train_end_exclusive": TRAIN_END,
        "train_target_sha256": hashlib.sha256(pd.util.hash_pandas_object(target).values.tobytes()).hexdigest(),
        "cell_count_min": int(counts.min()), "cell_count_max": int(counts.max()),
    }


def environment_class(kit):
    namespace = {"__file__": "starter_kit/environment.py", "__name__": "upc_baseline_audit"}
    exec(compile(kit.read("starter_kit/environment.py"), "environment.py", "exec"), namespace)
    return namespace["CampusBatteryEnv"], json.loads(kit.read("starter_kit/battery_spec.json"))


def replay(frame, kit, parameters, stop=None):
    module = runpy.run_path(str(SOURCE))
    predictors = {m: module["NetLoadForecaster"](m, parameters) for m in METHODS}
    env_class, spec = environment_class(kit)
    env = env_class(frame, spec=spec)
    obs = env.reset()
    n = len(frame) if stop is None else min(stop, len(frame))
    predictions = {m: np.empty((n, 24)) for m in METHODS}
    elapsed = {m: 0.0 for m in METHODS}
    for t in range(n):
        for method, predictor in predictors.items():
            started = perf_counter()
            values = predictor.forecast(obs, 24)
            elapsed[method] += perf_counter() - started
            require(len(values) == 24 and np.isfinite(values).all(), "Sortida no vàlida")
            predictions[method][t] = values
        obs, _ = env.step(0.0)
    return predictions, elapsed


def evaluate(frame, quality, predictions, train):
    target = frame.load_kw - frame.pv_kw
    y = np.full((len(frame), 24), np.nan)
    valid = np.zeros_like(y, dtype=bool)
    suspect = np.zeros_like(y, dtype=bool)
    incomplete = np.zeros_like(y, dtype=bool)
    outlier = np.zeros_like(y, dtype=bool)
    q1, q3 = (train.load_kw - train.pv_kw).quantile([.25, .75])
    lower, upper = q1 - 1.5 * (q3 - q1), q3 + 1.5 * (q3 - q1)
    blocks = block_ranges(frame.index)
    origin_first3 = np.zeros(len(frame), dtype=bool)
    after_gap = np.zeros(len(frame), dtype=bool)
    for start, end, n in blocks:
        pos = frame.index.get_loc(start)
        origin_first3[pos:pos + min(3, n)] = True
        if pos:
            after_gap[pos] = True
        for offset in range(n):
            for h in range(1, 25):
                row = pos + offset
                lead = h - 1  # h és la posició 1..24: t, t+1, ..., t+23.
                # Exigeix tota la finestra cronològica, no només el target final.
                if offset + lead >= n:
                    continue
                ts = start + (offset + lead) * HOUR
                require(frame.index[row] + lead * HOUR == ts, "Finestres desalineades")
                require(ts < pd.Timestamp(VALID_END), "Target fora de validació")
                y[row, h - 1] = target.loc[ts]
                valid[row, h - 1] = True
                suspect[row, h - 1] = bool(quality.loc[ts, "suspect"])
                incomplete[row, h - 1] = bool(quality.loc[ts, "incomplete"])
                outlier[row, h - 1] = target.loc[ts] < lower or target.loc[ts] > upper
    common = valid.all(axis=1)
    require(int(common.sum()) == sum(max(0, n - 23) for _, _, n in blocks), "Purga incorrecta")
    # Confirmació independent per pertinença explícita dels 24 timestamps.
    allowed = set(frame.index)
    enumeration = [all(t + h * HOUR in allowed for h in range(24)) for t in frame.index]
    require(np.array_equal(common, enumeration), "Una finestra travessa una discontinuïtat")
    source_suspect = np.r_[False, quality.suspect.to_numpy(dtype=bool, na_value=False)[:-1]]
    source_incomplete = np.r_[False, quality.incomplete.to_numpy(dtype=bool, na_value=False)[:-1]]
    cold = np.arange(len(frame)) == 0
    broadcast = lambda a: np.broadcast_to(a[:, None], y.shape)
    cohorts = {
        "Totes les finestres completes": np.ones_like(valid),
        "Target sospitós (zeros/qualitat COM/límit físic)": suspect,
        "Target atípic segons IQR del train": outlier,
        "Target amb mostres incompletes": incomplete,
        "Telemetria d'origen sospitosa": broadcast(source_suspect),
        "Telemetria d'origen amb mostres incompletes": broadcast(source_incomplete),
        "Primera decisió de l'episodi": broadcast(cold),
        "Primera decisió després d'un salt": broadcast(after_gap),
        "Primeres 3 decisions de cada bloc": broadcast(origin_first3),
    }
    errors = {m: predictions[m] - y for m in METHODS}
    def metrics(err):
        return (int(err.size), float(np.abs(err).mean()), float(np.sqrt(np.square(err).mean()))) if err.size else (0, None, None)
    rows = []
    for cohort, mask in cohorts.items():
        for method in METHODS:
            for h in LEADS:
                eligible = common & mask[:, h - 1]
                rows.append((cohort, method, h, *metrics(errors[method][eligible, h - 1])))
    scores = {m: metrics(errors[m][common]) for m in METHODS}
    month_rows = []
    for month in sorted(set(frame.index.strftime("%Y-%m"))):
        mask = common & (frame.index.strftime("%Y-%m") == month)
        for method in METHODS:
            month_rows.append((month, method, int(mask.sum()), *metrics(errors[method][mask])[1:]))
    # Recalcul independent de MAE/RMSE per a una cel·la representativa.
    for m in METHODS:
        e = [float(predictions[m][i, 5] - target.loc[frame.index[i] + 5 * HOUR])
             for i in np.flatnonzero(common)]
        row = next(r for r in rows if r[:3] == ("Totes les finestres completes", m, 6))
        require(np.isclose(row[4], sum(abs(v) for v in e) / len(e)), "MAE incorrecte")
        require(np.isclose(row[5], (sum(v * v for v in e) / len(e)) ** .5), "RMSE incorrecte")
    return {
        "rows": rows, "scores": scores, "months": month_rows,
        "common": int(common.sum()), "candidates": len(frame),
        "available": {h: int(valid[:, h - 1].sum()) for h in LEADS},
        "blocks": blocks, "iqr_lower": float(lower), "iqr_upper": float(upper),
        "suspect_hours": int(quality.suspect.sum()), "incomplete_hours": int(quality.incomplete.sum()),
    }


def leakage_checks(hourly, validation, kit, parameters, predictions):
    poisoned = hourly.copy()
    poisoned.loc[poisoned.index >= TRAIN_END, ["load_kw", "pv_kw"]] = (1e12, 2e12)
    require(fit_parameters(poisoned) == parameters, "L'ajust depèn de validació")
    # Reserva fictícia només per provar la barrera temporal; no és dada ni mètrica oficial.
    extra = pd.DataFrame({"load_kw": [1e15], "pv_kw": [-1e15]}, index=pd.DatetimeIndex([VALID_END], name="Fecha"))
    require(fit_parameters(pd.concat([hourly, extra])) == parameters, "L'ajust depèn de reserva")
    cut = min(300, len(validation) - 1)
    future_poisoned = validation.copy()
    future_poisoned.iloc[cut:, future_poisoned.columns.get_indexer(["load_kw", "pv_kw"])] = (1e9, 2e9)
    changed, _ = replay(future_poisoned, kit, parameters, stop=cut + 1)
    for m in METHODS:
        np.testing.assert_array_equal(predictions[m][:cut + 1], changed[m])
    validator = {"__file__": "starter_kit/check_submission.py", "__name__": "upc_ast_audit"}
    exec(compile(kit.read("starter_kit/check_submission.py"), "check_submission.py", "exec"), validator)
    require(validator["check_ast"](SOURCE) is None, "El predictor no passa l'AST local oficial")
    return [
        "Paràmetres invariants en alterar totes les etiquetes de validació.",
        "Paràmetres invariants en afegir valors sentinella a la reserva (sense consultar-la).",
        f"Prediccions idèntiques fins a l'origen {cut} en alterar demanda/solar de t i del futur.",
        "MAE/RMSE recalculats independentment; finestres enumerades per timestamp.",
        "AST de src/forecast.py aprovat pel comprovador oficial local (no és un ZIP ni un dry-run).",
    ]


def export_parameters(parameters, selected):
    source = SOURCE.read_text(encoding="utf-8")
    begin = "# BEGIN TRAINED PARAMETERS — regenerat només amb setembre–febrer."
    end = "# END TRAINED PARAMETERS"
    require(source.count(begin) == source.count(end) == 1, "Marcadors d'exportació no vàlids")
    before, rest = source.split(begin)
    _, after = rest.split(end)
    fitted = "TRAINED_PARAMETERS = " + pprint.pformat(parameters, width=110, sort_dicts=False)
    SOURCE.write_text(before + begin + "\n" + fitted + f'\nDEFAULT_METHOD = "{selected}"\n' + end + after,
                      encoding="utf-8", newline="\n")


def make_report(kit, parameters, results, elapsed, checks, selected, hashes, command, tests_run):
    lines = []
    def add(text):
        lines.extend([text, ""])
    add("# Baselines causals de demanda neta — issue #3")
    add("Cesc · La MasIA · 14/11/2026 · `feat/cesc-forecast`. "
        "Target oficial conservat: `load_kw - pv_kw`, sense retocar zeros, clipping ni agregació del tutorial. "
        "La qüestió física PCC/solar continua pendent dels mentors; s'avalua el contracte local.")
    add("## Protocol congelat abans de comparar")
    add(table(["Partició", "Dates (final exclusiu)", "Hores", "Ús"], [
        ("Train", "2025-09-01 → 2026-03-01", EXPECTED_TRAIN, "Únic ajust de perfils, fallback, clip i IQR"),
        ("Validació", "2026-03-01 → 2026-06-01", EXPECTED_VALID, "Comparació de tres candidats prefixats"),
        ("Reserva retrospectiva", "2026-06-01 → 2026-09-01", RESERVE_HOURS, "Exclosa abans de construir targets; sense mètriques ni selecció"),
    ]))
    add("No hi ha aleatorietat ni cal llavor. La selecció usa " + SCORE_RULE + ". "
        "No s'ha fet cerca d'hiperparàmetres. La reserva ja havia aparegut en l'auditoria i en "
        "ajustos previs de polítiques: no es pot anomenar test històricament intacte.")
    add("## Contracte temporal i inferència")
    add("**Alineament confirmat explícitament per Cesc:** incloure l'hora actual, t…t+23. "
        "`forecast_net_load(obs, horizon)[k]` retorna demanda neta en kW a "
        "`obs['timestamp'] + k hores`. En les taules, h=1, 6 i 24 són posicions del vector: "
        "t, t+5 i t+23. No són desplaçaments de +1, +6 i +24 hores des de la decisió. "
        "Amb telemetria recent de t−1 equivalen a 1, 6 i 24 hores des de l'última dada observable; "
        "aquesta equivalència no val al primer pas ni després d'un salt. "
        "Es conserva l'alineament de l'auditoria i es purguen 23 orígens al final de cada bloc.")
    add("Les hores són cronològiques, no posicions de fila. Amb timestamps amb zona, l'avenç és "
        "en temps UTC i després es recupera el calendari local. Els CSV oficials són locals sense zona: "
        "no es pot reconstruir DST si l'organització no dona offsets. Les transicions no apareixen "
        "en els blocs usats. Els vectors oficials de preu/CO₂ també comencen a t, però poden travessar "
        "salts: només es poden emparellar per índex amb aquesta sortida si es verifica continuïtat horària. "
        "Com que obs no ofereix timestamps futurs per element, no es poden detectar de manera general "
        "els salts futurs des de l'agent. Cal aclarir aquest límit amb mentors abans d'integrar-los en un optimitzador.")
    add("La primera crida ignora sempre `noves_dades_5min`; en crides posteriors s'atribueix el payload "
        "al timestamp de la decisió anterior. A pot retenir una mesura antiga després d'un salt; C "
        "descarta la correcció antiga i torna a B. Cap model llegeix demanda actual, meteorologia, "
        "qualitat COM o targets futurs del CSV en inferència. B només necessita calendari; A i C "
        "necessiten una instància seqüencial amb memòria de les crides anteriors.")
    add("## Models fixats")
    add("- **A — Persistència:** vector constant amb l'últim `ultim_consum_kw - ultima_solar_kw` "
        "finit realment observable. Si no n'hi ha, mediana global del train. Manté valors baixos "
        "o zeros observats; una telemetria absent no es converteix en zero.\n"
        "- **B — Perfil robust:** mediana del target per (dia de setmana, hora), calculada només "
        "sobre train. Si falta una cel·la, mediana per hora i després mediana global del train.\n"
        "- **C — Perfil corregit:** B més la mediana dels residus de fins a les últimes 3 hores "
        "observades, amb clip simètric al quantil 95% de |residu| del train. La correcció decau "
        "amb semivida fixa de 6 h segons l'edat de la telemetria i l'horitzó. Després d'un salt "
        "o sense residus recents vàlids, retorna B. Ni 3, ni 6, ni 95% s'han triat mirant validació.")
    add(f"Mediana global: {parameters['global']:.6f} kW. Clip del residu: ±{parameters['residual_clip']:.6f} kW. "
        f"Mostres per cel·la setmanal: {parameters['cell_count_min']}–{parameters['cell_count_max']}. "
        "Els paràmetres agregats queden incrustats a `src/forecast.py`; no cal cap CSV, model binari ni "
        "fitxer auxiliar per fer inferència. No es reentrena automàticament amb validació.")
    add("## Finestres avaluades i excloses")
    add(table(["Bloc de validació", "Inici", "Final", "Hores", "Finestres completes 24 h"], [
        (i, a, b, n, max(0, n - 23)) for i, (a, b, n) in enumerate(results["blocks"], 1)
    ]))
    add(f"{results['candidates']} orígens candidats, **{results['common']} finestres completes avaluades** "
        f"i **{results['candidates'] - results['common']} excloses** per travessar el final d'un bloc/partició. "
        "Tots els models i els horitzons de la taula principal comparteixen aquests orígens; "
        "no se suprimeixen hores sospitoses per millorar les mètriques. El predictor continua rebent "
        "les 1704 observacions en ordre, inclosos els orígens exclosos de puntuació.")
    add(table(["h (posició)", "Orígens si s'avalua aquest h sol", "Exclosos per a aquest h", "Orígens a la comparació principal"], [
        (h, results["available"][h], results["candidates"] - results["available"][h], results["common"]) for h in LEADS
    ]))
    add("## MAE i RMSE de validació (kW)")
    main_rows = [r[1:] for r in results["rows"] if r[0] == "Totes les finestres completes"]
    add(table(["Model", "h (posició)", "N", "MAE kW", "RMSE kW"], main_rows))
    add(table(["Model", "Parelles origen/horitzó", "MAE de les 24 h", "RMSE de les 24 h", "Temps de 1704 inferències (s)"], [
        (m, *results["scores"][m], elapsed[m]) for m in METHODS
    ]))
    winners = []
    for h in LEADS:
        candidates = [r for r in main_rows if r[1] == h]
        winners.append(f"h={h}: {min(candidates, key=lambda r: r[3])[0]}")
    add("Millor MAE per horitzó: " + "; ".join(winners) + ". "
        f"C redueix el MAE del vector complet un {100 * (1 - results['scores']['C'][1] / results['scores']['B'][1]):.2f}% "
        f"respecte de B i un {100 * (1 - results['scores']['C'][1] / results['scores']['A'][1]):.2f}% respecte d'A. "
        "La recomanació global no implica dominar tots els horitzons ni tots els mesos.")
    add("Les mètriques de les 24 h inclouen tots els h=1…24; MAE i RMSE són mitjanes sobre "
        "les mateixes parelles origen/horitzó, sense ponderar per energia. Les finestres se superposen: "
        "no són mostres independents i no s'ha inferit significació estadística.")
    add(table(["Mes", "Model", "Finestres", "MAE de les 24 h", "RMSE de les 24 h"], results["months"]))
    add("## Casos problemàtics: diagnòstic separat")
    add(f"Validació conté {results['suspect_hours']} hores sospitoses segons zeros/qualitat COM/límits "
        f"i {results['incomplete_hours']} hores amb menys de 12 mostres vàlides de comptador o dels "
        "tres inversors. N=0 es mostra com a «—»: no hi ha evidència de rendiment en aquest grup. "
        "No s'ha obert la reserva per omplir grups absents. A més, es marca el target fora de l'IQR "
        f"del train: [{results['iqr_lower']:.6f}, {results['iqr_upper']:.6f}] kW. "
        "Aquests indicadors s'utilitzen només per desglossar errors, mai com a features ni com a "
        "filtres sobre la puntuació principal. Les cohorts es poden superposar.")
    diagnostic = [r for r in results["rows"] if r[0] != "Totes les finestres completes"]
    empty_cohorts = list(dict.fromkeys(r[0] for r in diagnostic if r[3] == 0))
    add(table(["Cohort sense casos", "N per model i horitzó", "MAE/RMSE"], [
        (name, 0, "No estimables") for name in empty_cohorts
    ]))
    add(table(["Cohort", "Model", "h", "N", "MAE kW", "RMSE kW"], [r for r in diagnostic if r[3] > 0]))
    add("Només hi ha dues primeres decisions després de salts dins de validació; "
        "el primer pas de l'episodi es compta a part. Aquests recomptes són massa petits "
        "per donar una garantia estadística de robustesa. C coincideix amb B a l'instant del salt "
        "per disseny, i només torna a corregir quan arriba telemetria recent atribuïble.")
    add("## Verificació de causalitat i proves")
    add("\n".join("- " + c for c in checks))
    add(f"**{tests_run} proves unitàries passades**, a `analysis/test_forecast.py`: alineament temporal, "
        "primera observació, salts, idempotència, reset d'episodi, agents independents, "
        "telemetria absent/no finita, longituds i inferència amb accés a fitxers desactivat. "
        "Els fixtures de prova no es presenten com a dades ni com a mètriques oficials.")
    add("## Recomanació i límits")
    add(f"**Model recomanat segons el criteri prefixat: {selected}.** És el valor de `DEFAULT_METHOD` "
        "exportat. Aquesta és una selecció sobre març–maig, no una confirmació independent; "
        "no s'ha ajustat cap hiperparàmetre després de veure'n el resultat. Menor error de "
        "forecasting no demostra millora del score de bateria: falta comparació amb la mateixa "
        "política, SOC, període i pressupost de runtime quan l'integrador ho autoritzi.")
    add("Limitacions: perfil sense estacionalitat anual ni festius; correcció recent limitada i "
        "potencialment afectada per telemetria errònia sense flags de qualitat disponibles; persistència "
        "obsoleta després de buits; cohorts de qualitat buides si no hi ha casos en validació; "
        "reserva retrospectiva ja inspeccionada històricament; semàntica PCC/solar pendent; "
        "estat seqüencial explícit i vectors oficials sense timestamps futurs. No hi ha MPC ni models "
        "LightGBM/XGBoost; no s'ha modificat cap política de bateria.")
    add("## Integració sense dades")
    add("Preferible, una instància per `BatteryAgent`:\n\n```python\n"
        "from src.forecast import NetLoadForecaster\n\n"
        "# A __init__ (un predictor nou per episodi):\n"
        "self.forecaster = NetLoadForecaster()\n"
        "# A cada act(obs), també si no es puntua aquest origen:\n"
        "future_net_kw = self.forecaster.forecast(obs, horizon=24)\n"
        "# future_net_kw[0] correspon a t; future_net_kw[23], a t+23.\n```")
    add("Façana requerida, per a un únic episodi actiu:\n\n```python\n"
        "from src.forecast import forecast_net_load, reset_forecast\n\n"
        "reset_forecast()  # abans de cada simulació\n"
        "future_net_kw = forecast_net_load(obs, horizon=24)\n```\n\n"
        "Una observació sense timestamp torna al perfil/fallback i reinicia la memòria temporal. "
        "`horizon=0` retorna `[]`; valors negatius, booleans o no enters donen `ValueError`. "
        "Per dos agents intercalats, usar instàncies pròpies; no compartir la façana global.")
    add("## Reproducció i procedència")
    add(f"Paquet local: `{kit.path}`. Python {platform.python_version()}, pandas {pd.__version__}, "
        f"numpy {np.__version__}. Hash del target de train: `{parameters['train_target_sha256']}`.")
    add(table(["CSV font (hash del fitxer complet; reserva exclosa de càlculs)", "SHA-256"], hashes.items()))
    add("Ordre executada:\n\n```powershell\n" + command + "\n```")
    add("Sense `--write-model` i `--report`, l'ordre verifica els paràmetres incrustats i recalcula "
        "els resultats sense escriure fitxers. Proves unitàries:\n\n```powershell\n"
        "& '" + sys.executable.replace("'", "''") + "' -B -m unittest discover -s analysis -p test_forecast.py -v\n```\n\n"
        "`git diff --check` verifica espais dels fitxers versionats; el comprovador unitari també "
        "revisa la sintaxi i el contracte del predictor nou. Només es creen el mòdul, scripts a "
        "analysis i aquest informe. Sense commit, push ni merge.")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kit", type=Path, required=True)
    parser.add_argument("--write-model", action="store_true", help="Actualitza només els paràmetres a src/forecast.py")
    parser.add_argument("--report", action="store_true", help="Escriu reports/forecast_baselines.md")
    args = parser.parse_args()
    kit = Kit(args.kit)
    try:
        hourly, quality, hashes = load_data(kit)
        parameters = fit_parameters(hourly)
        train = hourly.loc[hourly.index < TRAIN_END]
        validation = hourly.loc[(hourly.index >= VALID_START) & (hourly.index < VALID_END)]
        predictions, elapsed = replay(validation, kit, parameters)
        results = evaluate(validation, quality.loc[validation.index], predictions, train)
        checks = leakage_checks(hourly, validation, kit, parameters, predictions)
        selected = min(METHODS, key=lambda m: (results["scores"][m][1], m))
        if args.write_model:
            export_parameters(parameters, selected)
        embedded = runpy.run_path(str(SOURCE))
        require(embedded["TRAINED_PARAMETERS"] == parameters, "Paràmetres incrustats diferents: --write-model")
        require(embedded["DEFAULT_METHOD"] == selected, "Model per defecte diferent del criteri de selecció")
        suite = unittest.defaultTestLoader.discover(str(ROOT / "analysis"), pattern="test_forecast.py")
        tests_result = unittest.TextTestRunner(verbosity=1).run(suite)
        require(tests_result.wasSuccessful(), "Han fallat proves de contracte/causalitat")
        command = "& '" + sys.executable.replace("'", "''") + "' -B analysis/forecast_baselines.py --kit '" + str(kit.path).replace("'", "''") + "'"
        command += " --write-model" if args.write_model else ""
        command += " --report" if args.report else ""
        if args.report:
            REPORT.write_text(make_report(kit, parameters, results, elapsed, checks, selected, hashes, command, tests_result.testsRun),
                              encoding="utf-8", newline="\n")
        print(json.dumps({"status": "ok", "selected": selected, "train_hours": len(train),
                          "validation_hours": len(validation), "windows": results["common"],
                          "excluded": len(validation) - results["common"],
                          "scores_24h": results["scores"],
                          "metrics": [r[1:] for r in results["rows"] if r[0] == "Totes les finestres completes"],
                          "suspect_hours": results["suspect_hours"], "incomplete_hours": results["incomplete_hours"],
                          "unit_tests_passed": tests_result.testsRun,
                          "seconds": elapsed, "checks": checks}, ensure_ascii=True))
    finally:
        kit.close()


if __name__ == "__main__":
    main()
