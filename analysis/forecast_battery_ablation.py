"""Ablació diagnòstica de forecast amb una política de llindars fixa.

python -B analysis/forecast_battery_ablation.py --kit RUTA_ZIP --report
No entrena models, no modifica polítiques oficials ni llegeix targets de reserva.
Sense --report imprimeix resultats i passa proves sense escriure fitxers.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import platform
import runpy
import sys
from time import perf_counter
import unittest

import numpy as np
import pandas as pd

from audit_temporal import Kit, HOUR
from forecast_baselines import load_data, environment_class, table, require


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports/forecast_battery_ablation.md"
PROTOTYPE = ROOT / "prototypes/upc/agent_v0_24h.py"
FORECAST_PATH = ROOT / "src/forecast.py"
ReferenceAgent = runpy.run_path(str(PROTOTYPE))["BatteryAgent"]
FORECAST = runpy.run_path(str(FORECAST_PATH))
Forecaster = FORECAST["NetLoadForecaster"]
VARIANTS = ("Sense forecast", "A", "B", "C", "D")
ACTION_EPS = 1e-6


def chronological_lengths(index):
    """Calendari offline del benchmark, sense mirar valors de demanda/solar.

    L'obs oficial no dona timestamps futurs. Aquesta censura comuna de vectors
    és una diferència explícita respecte a executar el prototip sobre obs crues.
    """
    remaining = np.ones(len(index), dtype=int)
    for t in range(len(index) - 2, -1, -1):
        if index[t + 1] - index[t] == HOUR:
            remaining[t] = min(24, remaining[t + 1] + 1)
    return remaining


def safe_observation(obs, length, first=False):
    safe = dict(obs)
    safe["preus_properes_24h"] = list(obs["preus_properes_24h"][:length])
    safe["co2_properes_24h"] = list(obs["co2_properes_24h"][:length])
    if first:
        safe["noves_dades_5min"] = {}
    return safe


class ForecastSource:
    """Una memòria nova per variant i episodi; D només combina sortides."""

    def __init__(self, variant):
        require(variant in VARIANTS, "Variant desconeguda")
        self.variant = variant
        self.models = {m: Forecaster(m) for m in (("A", "C") if variant == "D"
                                                else (() if variant == "Sense forecast" else (variant,)))}

    def predict(self, obs):
        if not self.models:
            return None
        predictions = {m: model.forecast(obs, 24) for m, model in self.models.items()}
        result = ([predictions["A"][0]] + predictions["C"][1:]
                  if self.variant == "D" else predictions[self.variant])
        require(len(result) == 24 and np.isfinite(result).all(), "Forecast no finit o mal dimensionat")
        return result


class DiagnosticThresholdPolicy:
    """Adaptador EXPERIMENTAL, no política oficial ni MPC.

    Mateixos llindars, pesos, marges i clamp que el prototip. Únics punts
    dependents del forecast: mitjana de valor ponderada per importació prevista
    i límit de descàrrega segons el net previst de t. Sense forecast: mitjana
    uniforme i cap límit per demanda, exactament com el prototip.
    No s'hi ha ajustat cap paràmetre sobre aquesta validació.
    """

    def __init__(self):
        self.reference = ReferenceAgent()
        self.cap_bound = False

    def act(self, obs, forecast=None):
        r = self.reference
        prices = [float(v) for v in obs["preus_properes_24h"]]
        carbon = [float(v) for v in obs["co2_properes_24h"]]
        n = min(len(prices), len(carbon))
        if forecast is not None:
            require(len(forecast) >= n and np.isfinite(forecast).all(), "Forecast incomplet")
        desired = 0.0
        self.cap_bound = False
        if n >= 3:
            prices, carbon = prices[:n], carbon[:n]
            mean_price, mean_carbon = sum(prices) / n, sum(carbon) / n
            values = [r.weight_co2 * c / (mean_carbon + 1e-9)
                      + (1 - r.weight_co2) * p / (mean_price + 1e-9)
                      for p, c in zip(prices, carbon)]
            mean_value = sum(values) / n
            if forecast is not None:
                weights = [max(0.0, float(v)) for v in forecast[:n]]
                if sum(weights) > 0:
                    mean_value = sum(v * w for v, w in zip(values, weights)) / sum(weights)
            current = values[0]
            if (current < mean_value - r.threshold
                    and max(values) > current / 0.90 + r.min_arbitrage_margin):
                desired = r.max_power_kw
            elif (current > mean_value + r.threshold
                    and min(values) < 0.90 * current - r.min_arbitrage_margin):
                desired = -r.max_power_kw
            if desired < 0 and forecast is not None:
                limited = -min(-desired, max(0.0, float(forecast[0])))
                self.cap_bound = limited > desired
                desired = limited
        soc = float(obs["soc_kwh"])
        epsilon = 1e-4
        max_charge = max(0.0, min(r.max_power_kw, (r.capacity_kwh - soc) / r.eta - epsilon))
        max_discharge = max(0.0, min(r.max_power_kw, soc * r.eta - epsilon))
        action = float(max(-max_discharge, min(max_charge, desired)))
        require(math.isfinite(action), "Acció no finita")
        if forecast is None:
            require(action == r.act(obs), "Sense forecast divergeix del prototip")
        return action


def run_variant(frame, env_class, spec, lengths, variant, stop=None):
    started = perf_counter()
    env = env_class(frame, spec=spec)
    source, policy = ForecastSource(variant), DiagnosticThresholdPolicy()
    obs = env.reset()
    n = len(frame) if stop is None else min(stop, len(frame))
    predictions = None if variant == "Sense forecast" else np.empty((n, 24))
    cap_bound = 0
    for t in range(n):
        require(obs["timestamp"] == frame.index[t], "Timestamp incorrecte")
        length = int(lengths[t])
        # Només calendari: comprova cada fila efectivament emparellada, sense labels.
        for h in range(length):
            require(frame.index[t + h] == frame.index[t] + h * HOUR,
                    "S'està emparellant una previsió a través d'un salt")
        safe = safe_observation(obs, length, first=(t == 0))
        forecast = source.predict(safe)  # Genera 24 h cronològiques; només se'n consumeixen length.
        if predictions is not None:
            predictions[t] = forecast
        action = policy.act(safe, forecast)
        cap_bound += int(policy.cap_bound)
        obs, _ = env.step(action)
    metrics = env.evaluate_results()
    actions = np.asarray(env.actions)
    soc = np.asarray(env.soc_series)
    charge, discharge = actions > ACTION_EPS, actions < -ACTION_EPS
    rest = ~(charge | discharge)
    require(int(charge.sum() + discharge.sum() + rest.sum()) == n, "Comptatge d'accions incorrecte")
    require(np.isfinite(actions).all() and np.isfinite(soc).all(), "Trajectòria no finita")
    require((soc >= env.soc_min - 1e-8).all() and (soc <= env.soc_max + 1e-8).all(), "SOC fora de límits")
    months = []
    for month in sorted(set(frame.index[:n].strftime("%Y-%m"))):
        mask = frame.index[:n].strftime("%Y-%m") == month
        positions = np.flatnonzero(mask)
        measured = env.evaluate_results(mask=mask)
        initial = env.soc_init if positions[0] == 0 else soc[positions[0] - 1]
        months.append({"month": month, "hours": len(positions), "soc_initial": float(initial),
                       "soc_final": float(soc[positions[-1]]), **measured})
    elapsed = perf_counter() - started
    return {
        "variant": variant, "metrics": metrics, "seconds": elapsed,
        "charge": int(charge.sum()), "discharge": int(discharge.sum()), "rest": int(rest.sum()),
        "charge_kwh": float(actions[charge].sum()), "discharge_kwh": float(-actions[discharge].sum()),
        "export_kwh": float(np.asarray(env.exports).sum()), "soc_final": float(env.soc),
        "soc_initial": float(env.soc_init), "cap_bound": cap_bound, "months": months,
        "actions": actions, "soc": soc, "predictions": predictions,
    }


def validate_experiment(frame, env_class, spec, lengths, results):
    require(len(frame) == 1704, "Període de validació incorrecte")
    require(frame.index.min() == pd.Timestamp("2026-03-01"), "Inici incorrecte")
    require(frame.index.max() < pd.Timestamp("2026-06-01"), "La reserva no es pot utilitzar")
    params = FORECAST["TRAINED_PARAMETERS"]
    require(params["train_hours"] == 2784 and params["train_end_exclusive"] == "2026-03-01",
            "No s'estan utilitzant els models congelats")
    require(int((lengths == 24).sum()) == 1635 and int((lengths < 24).sum()) == 69,
            "Blocs o censura temporal diferents dels congelats")
    reference = results["Sense forecast"]
    for variant, result in results.items():
        require(result["soc_initial"] == 1000.0, "SOC inicial desigual")
        require(result["metrics"]["infraccions"] == 0, f"Infraccions a {variant}")
        require(result["metrics"]["cost_baseline_eur"] == reference["metrics"]["cost_baseline_eur"], "Denominador desigual")
        require(result["metrics"]["co2_baseline_kg"] == reference["metrics"]["co2_baseline_kg"], "Denominador desigual")
        result["changed_actions"] = int(np.count_nonzero(np.abs(result["actions"] - reference["actions"]) > ACTION_EPS))
    # Canviar el resultat real de t i de totes les hores futures no pot decidir l'acció de t.
    cut = 64
    poisoned = frame.copy()
    poisoned.iloc[cut:, poisoned.columns.get_indexer(["load_kw", "pv_kw"])] = (1e9, 2e9)
    for variant in VARIANTS:
        altered = run_variant(poisoned, env_class, spec, lengths, variant, stop=cut + 1)
        np.testing.assert_array_equal(results[variant]["actions"][:cut + 1], altered["actions"])
        np.testing.assert_array_equal(results[variant]["soc"][:cut + 1], altered["soc"])
        if variant != "Sense forecast":
            np.testing.assert_array_equal(results[variant]["predictions"][:cut + 1], altered["predictions"])
    return [
        "1704 hores de març–maig; cap ajust de models ni consulta de mètriques de juny–agost.",
        "1635 horitzons complets i 69 truncats; tots els elements consumits verificats per timestamp.",
        "Mateix SOC inicial (1000 kWh), especificació física, denominadors i continuïtat entre blocs.",
        "Accions sense forecast iguals al prototip en cada estat sota el mateix truncament de vectors.",
        "Accions, SOC i forecasts prefix invariants en alterar demanda/solar de t i del futur.",
        "Cap infracció física a les cinc simulacions completes.",
    ]


def make_report(kit, frame, lengths, results, checks, tests_run, hashes, command):
    lines = []
    def add(text):
        lines.extend([text, ""])
    reference = results["Sense forecast"]
    add("# Forecast i puntuació de bateria: ablació diagnòstica")
    add("Cesc · issue #3 · `feat/cesc-forecast` · 14/11/2026. "
        "Experiment local de validació, sense canviar la política oficial ni el codi d'Oriol/Dani.")
    add("## Inspecció: la política existent no consumeix forecast")
    add("`prototypes/upc/agent_v0_24h.py` només llegeix SOC, preus i CO₂. No llegeix demanda, "
        "solar, telemetria ni cap sortida de `forecast_net_load`. Connectar A/B/C/D sense adaptar "
        "la regla no pot canviar-ne cap acció. Els scores previs d'aquest prototip no són millores "
        "atribuïbles al forecast. Aquest informe distingeix aquesta política de l'adaptador diagnòstic.")
    add("El motor oficial decideix primer amb obs i després liquida `load_kw - pv_kw + acció`; "
        "no limita la descàrrega per demanda, remunera exportacions a 0 €/kWh i manté el SOC "
        "entre files encara que hi hagi salts. Es conserva el preprocessament del tutorial. "
        "La guia descriu el comptador al PCC com a importació neta de solar: si aquesta descripció "
        "és correcta, definir load_kw=-comptador i restar-hi pv_kw pot produir un doble comptatge "
        "PCC/solar. Aquest dubte continua pendent dels mentors; no s'ha alterat el contracte oficial.")
    add("## Política experimental única, fixada abans de mesurar")
    r = ReferenceAgent()
    add(f"Es conserva capacitat {r.capacity_kwh:.0f} kWh, potència ±{r.max_power_kw:.0f} kW, "
        f"eta=sqrt(0,9), threshold={r.threshold}, marge={r.min_arbitrage_margin}, "
        f"pes CO₂ de la heurística={r.weight_co2} i clamp amb epsilon=1e−4. "
        "El pes heurístic 50/50 es manté igual en totes les alternatives; el score oficial continua "
        "sent 70% CO₂ i 30% cost. No s'ha buscat cap altre adaptador ni ajustat llindars segons resultats.")
    add("Per a cada horitzó admès, es calcula el mateix valor normalitzat de preu/CO₂ `v[h]` del "
        "prototip. Sense forecast s'usa `mean(v)`, exactament com abans. Amb forecast, s'usa "
        "`sum(v[h] * max(net_hat[h], 0)) / sum(max(net_hat[h], 0))`; si tots els pesos són zero, "
        "es torna a la mitjana uniforme. La resta de les condicions de càrrega/descàrrega no canvia. "
        "En descàrrega, el límit addicional és `max(net_hat[0], 0)` kW, abans del mateix clamp físic. "
        "Així es consumeixen t i les hores futures del forecast, sense usar labels reals per decidir.")
    add("És una heurística diagnòstica de ponderació per demanda, no un MPC ni una política "
        "oficial nova. El resultat és condicional a aquesta regla: no mesura la utilitat màxima "
        "del forecast per a un optimitzador. Si la demanda prevista és constant (A), la mitjana "
        "ponderada equival a la uniforme; només el límit de descàrrega pot tenir efecte addicional.")
    add(table(["Variant", "Forecast consumit"], [
        ("Sense forecast", "Pesos uniformes; sense límit addicional per demanda"),
        ("A", "Última demanda neta observable, constant; fallback de train al primer pas"),
        ("B", "Mediana per hora/dia de setmana entrenada sobre setembre–febrer"),
        ("C", "B corregit causalment amb telemetria recent; paràmetres congelats"),
        ("D", "A[0] per a t; C[1:24] per a t+1…t+23; sense reentrenament"),
    ]))
    add("## Calendari, causalitat i estat")
    add("Només març–maig: **1704 hores**, en blocs de 576, 552 i 576 hores. "
        "Els models es carreguen de `src/forecast.py`, amb 2784 hores de train anteriors a març; "
        "no s'entrena ni s'ajusta cap model. La reserva es descarta abans de construir targets "
        "o diagnòstics i no se'n calcula cap mètrica. La política original ja s'havia ajustat "
        "històricament mirant el conjunt complet: aquesta comparació és retrospectiva, no un test intacte.")
    add("Totes les simulacions comencen amb SOC=1000 kWh i agents nous. El SOC persisteix entre "
        "març, abril i maig, igual que al motor, amb dt=1h per fila i sense simular les setmanes "
        "retirades. No hi ha restricció de SOC terminal; es reporta el SOC final per veure si els "
        "scores poden estar influïts per inventari residual diferent. Els desglossaments mensuals "
        "conserven l'estat acumulat i no són episodis independents.")
    add("El primer payload de demanda/solar s'elimina per a totes les variants, evitant que "
        "l'excepció t=0 del motor reveli el target actual. Després només es passa la telemetria "
        "de la fila anterior. C descarta la correcció obsoleta després dels salts; A i la "
        "component A de D poden retenir l'última dada realment observable, amb antiguitat explícita.")
    add("**Diferència comuna respecte a obs crues:** els vectors oficials contenen 24 files, "
        "que poden pertànyer al mes següent. El benchmark en trunca preu, CO₂ i consum efectiu "
        "del forecast al final del bloc cronològic. Hi ha 1635 decisions amb 24 hores consecutives "
        "i 69 amb un horitzó més curt: 46 censurades abans dels dos salts interns i 23 al final "
        "de la validació. Cap fila de l'altre costat del salt es tracta com t+h. Amb menys de "
        "3 hores, es manté el repòs del prototip. Es puntuen **totes les 1704 accions**, sense "
        "eliminar hores després de decidir.")
    add("Aquesta censura usa exclusivament el calendari offline de validació, mai demanda/solar "
        "futures. L'obs no proporciona els timestamps futurs necessaris per reconstruir-la de "
        "manera general en producció. Per això els scores són del motor oficial amb una interfície "
        "temporal censurada comuna, no una reproducció literal del prototip amb vectors crus ni "
        "una garantia del servidor. Els 69 horitzons truncats depenen d'informació de calendari "
        "offline no disponible a obs: això encara no és una integració validada per a producció. "
        "Cal aclarir aquest contracte amb mentors abans d'integrar.")
    add("## Resultats mesurats amb el simulador oficial local")
    rows = []
    for variant in VARIANTS:
        result = results[variant]
        m = result["metrics"]
        rows.append((variant, f"{m['score']:.2f}", f"{m['score'] - reference['metrics']['score']:+.2f}",
                     f"{m['co2_estalviat_pct']:.2f}", f"{m['cost_estalviat_pct']:.2f}",
                     m["infraccions"], f"{result['seconds']:.3f}"))
    add(table(["Variant", "Score /100", "Δ score vs sense forecast", "Reducció CO₂ %", "Estalvi cost %", "Infraccions", "Temps local s"], rows))
    add("El score és el retorn arrodonit a dos decimals d'`evaluate_results()`: "
        "`max(0, 100*(0.7*dCO2 + 0.3*dCost - 0.002*infraccions))`. "
        "CO₂ i cost són reduccions percentuals respecte de la mateixa bateria absent, no respecte "
        "de la política de referència. Els Δ són diferències de scores ja arrodonits. "
        "Temps inclou inicialització, inferència, simulació i comprovacions del bucle local, "
        "sense càrrega del CSV ni proves addicionals; no és una mesura del servidor. "
        "El cas sense forecast executa també una crida de paritat al prototip a cada pas: "
        "les diferències temporals no estimen exclusivament el cost del predictor.")
    add(table(["Variant", "Càrrega", "Descàrrega", "Repòs", "Accions diferents del ref.", "Límit de demanda actiu", "SOC final kWh", "Exportació kWh"], [
        (v, results[v]["charge"], results[v]["discharge"], results[v]["rest"],
         results[v]["changed_actions"], results[v]["cap_bound"], results[v]["soc_final"], results[v]["export_kwh"])
        for v in VARIANTS
    ]))
    add(f"Càrrega/descàrrega es defineixen per potència >{ACTION_EPS} / <−{ACTION_EPS} kW; "
        "la resta és repòs. Amb zero infraccions no hi ha diferència material entre les accions "
        "demanades i les aplicades. «Límit de demanda actiu» es compta abans del clamp SOC.")
    add(table(["Mes", "Variant", "Hores", "Score", "Reducció CO₂ %", "Estalvi cost %", "SOC inicial", "SOC final"], [
        (month["month"], v, month["hours"], month["score"], month["co2_estalviat_pct"],
         month["cost_estalviat_pct"], month["soc_initial"], month["soc_final"])
        for v in VARIANTS for month in results[v]["months"]
    ]))
    add("## Interpretació i recomanació")
    best = max(VARIANTS, key=lambda v: results[v]["metrics"]["score"])
    delta = results[best]["metrics"]["score"] - reference["metrics"]["score"]
    add(f"Millor score observat: **{best}**, amb Δ={delta:.2f} punts respecte del cas sense forecast. "
        "Aquesta identificació descriu el benchmark; no selecciona una política oficial ni ajusta "
        "els predictors. Menor MAE de C no implica automàticament millor score, perquè les decisions "
        "són discretes i molts límits de potència/demanda poden estar saturats.")
    add(table(["Variant", "Δ score març", "Δ score abril", "Δ score maig"], [
        (v, *(f"{month['score'] - base['score']:+.2f}"
              for month, base in zip(results[v]["months"], reference["months"])))
        for v in VARIANTS if v != "Sense forecast"
    ]))
    if results["A"]["changed_actions"] == 0:
        add("A genera exactament les mateixes accions que la referència. La seva ponderació "
            "constant no altera la mitjana i el límit de demanda no és restrictiu en aquestes dades; "
            "no hi ha guany atribuïble a persistència en aquest adaptador.")
    if all(result["cap_bound"] == 0 for result in results.values()):
        add("El límit de demanda prevista no s'activa en cap variant: els canvis observats de "
            "B/C/D provenen de la ponderació temporal. Millorar la predicció de t amb D no resol "
            "aquí una restricció d'autoconsum activa i tampoc supera B.")
    if all(abs(result["soc_final"] - reference["soc_final"]) < 1e-8 for result in results.values()):
        add(f"Totes les variants acaben amb el mateix SOC ({reference['soc_final']:.6f} kWh). "
            "Tot i no imposar igualtat terminal, el guany mesurat no s'explica per buidar més "
            "la bateria al final. B millora març i abril, però empitjora maig: no hi ha una "
            "millora uniforme en els tres blocs.")
    if best != "Sense forecast":
        extra_co2 = results[best]["metrics"]["co2_estalviat_kg"] - reference["metrics"]["co2_estalviat_kg"]
        extra_cost = results[best]["metrics"]["cost_estalviat_eur"] - reference["metrics"]["cost_estalviat_eur"]
        add(f"{best} estalvia addicionalment {extra_co2:.1f} kg CO₂ i {extra_cost:.2f} € respecte "
            "de la política sense forecast en aquestes 1704 hores (diferències de mètriques arrodonides). "
            "El guany de score és petit i no s'ha estimat significació estadística.")
    if delta <= 0:
        add("**Recomanació: conservar la política sense forecast com a referència operativa.** "
            "Aquest diagnòstic no aporta evidència per integrar A/B/C/D a l'optimitzador del Dani "
            "com a millora ja demostrada. El predictor pot quedar disponible per a una futura "
            "ablació dins del seu optimitzador fix, amb el contracte temporal resolt; no s'hauria "
            "d'incrementar complexitat només perquè el MAE és inferior.")
    else:
        add("**Recomanació: té sentit provar el forecast dins d'una branca experimental de "
            "l'optimitzador del Dani, mantenint la política sense forecast com a fallback.** "
            "El guany d'aquesta heurística no valida el seu MPC ni justifica desplegar-lo: cal "
            "repetir una ablació amb l'optimitzador fix, resoldre timestamps futurs i revisar "
            "estabilitat mensual, SOC terminal i runtime abans de substituir la referència.")
    add("Limitacions: comparació retrospectiva sobre tres blocs, sense independència entre mesos "
        "ni intervals de confiança; regla de ponderació diagnòstica que no pretén ser òptima; "
        "censura horària offline no disponible directament a obs; SOC terminal no igualat; "
        "mètriques oficials arrodonides; supòsits físics del comptador pendents; no s'ha executat "
        "dry-run web, leaderboard ni l'optimitzador del Dani. Cap resultat s'atribueix a forecast "
        "en la política original que no el consumeix.")
    add("## Verificació i reproducció")
    add("\n".join("- " + item for item in checks))
    add(f"**{tests_run} proves unitàries passades** entre `analysis/test_forecast.py` i "
        "`analysis/test_battery_ablation.py`, incloent sensibilitat real de l'adaptador als "
        "forecasts, paritat del cas sense forecast, composició D, protecció del primer pas i "
        "alineament als salts. Els fixtures no són dades ni resultats oficials.")
    add(f"Entorn: Python {platform.python_version()}, pandas {pd.__version__}, numpy {np.__version__}. "
        "Sense aleatorietat ni llavor. Models i política carregats sense reentrenar. "
        f"Paquet local: `{kit.path}`.")
    source_hashes = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                     for p in (PROTOTYPE, FORECAST_PATH, ROOT / "analysis/forecast_battery_ablation.py")}
    source_hashes["starter_kit/environment.py (ZIP)"] = hashlib.sha256(kit.read("starter_kit/environment.py")).hexdigest()
    source_hashes.update({name + " (CSV font complet)": value for name, value in hashes.items()})
    add(table(["Font", "SHA-256"], source_hashes.items()))
    add("Ordre executada:\n\n```powershell\n" + command + "\n```\n\n"
        "Sense `--report`, es recalcula tot i es passen les proves sense escriure fitxers. "
        "Només es creen scripts/proves dins d'analysis i aquest informe; els sis fitxers locals "
        "anteriors i els fitxers compartits es conserven. Sense commit, push ni merge.")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kit", type=Path, required=True)
    parser.add_argument("--report", action="store_true")
    args = parser.parse_args()
    kit = Kit(args.kit)
    try:
        hourly, _, hashes = load_data(kit)
        frame = hourly.loc[(hourly.index >= "2026-03-01") & (hourly.index < "2026-06-01")].copy()
        lengths = chronological_lengths(frame.index)
        env_class, spec = environment_class(kit)
        results = {v: run_variant(frame, env_class, spec, lengths, v) for v in VARIANTS}
        checks = validate_experiment(frame, env_class, spec, lengths, results)
        suites = [unittest.defaultTestLoader.discover(str(ROOT / "analysis"), pattern=pattern)
                  for pattern in ("test_forecast.py", "test_battery_ablation.py")]
        test_result = unittest.TextTestRunner(verbosity=1).run(unittest.TestSuite(suites))
        require(test_result.wasSuccessful(), "Proves fallides")
        command = "& '" + sys.executable.replace("'", "''") + "' -B analysis/forecast_battery_ablation.py --kit '" + str(kit.path).replace("'", "''") + "'"
        if args.report:
            command += " --report"
            REPORT.write_text(make_report(kit, frame, lengths, results, checks, test_result.testsRun, hashes, command),
                              encoding="utf-8", newline="\n")
        summary = {v: {k: value for k, value in result.items() if k not in ("actions", "soc", "predictions", "months")}
                   for v, result in results.items()}
        print(json.dumps({"status": "ok", "hours": len(frame), "full_horizons": int((lengths == 24).sum()),
                          "short_horizons": int((lengths < 24).sum()), "unit_tests_passed": test_result.testsRun,
                          "results": summary, "checks": checks}, ensure_ascii=True))
    finally:
        kit.close()


if __name__ == "__main__":
    main()
