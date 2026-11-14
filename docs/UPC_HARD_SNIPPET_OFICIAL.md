# Snippet oficial compartit — UPC Sostenible Hard Mode

**Data:** 14/11/2026. **Font:** text copiat per l'equip de la pestanya 🔥 Hard Mode de la plataforma oficial.  
**Estat:** snippet **rebut**; **no executat ni contrastat amb el servidor** en aquest document.  
**Regles generals:** vegeu [UPC_HARD_MODE_20261114.md](UPC_HARD_MODE_20261114.md).

## 1. Safety clamp publicat

El codi difós pels organitzadors és equivalent al següent (formatat per llegibilitat):

```python
cap_max = float(obs.get("cap_max_kwh", 6000.0))
p_max = float(obs.get("power_max_kw", 1500.0))
soc_kwh = float(obs["soc_kwh"])
eta = 0.90 ** 0.5
eps = 1e-4

max_carrega = max(0.0, min(p_max, (cap_max - soc_kwh) / eta - eps))
max_descarrega = max(0.0, min(p_max, soc_kwh * eta - eps))
consigna_segura = float(max(-max_descarrega, min(max_carrega, consigna_desitjada)))
return consigna_segura
```

**AVÍS IMPORTANT:** El títol oficial diu «compatible tant amb Standard com amb Hard», però els **valors per defecte** són **6.000/1.500**, és a dir, Hard. Si l'observació Standard no inclou els camps `cap_max_kwh` i `power_max_kw`, aquest codi no garanteix els límits de Standard (2.000/500). Cal usar configuració inequívoca per mode, o confirmar que ambdós camps són presents a `obs`, i fer proves separades. **No substituir directament el clamp Standard existent.**

## 2. Simulació Hard Mode local — text oficial formatat

```python
from starter_kit.environment import CampusBatteryEnv

# df_campus_hourly s'obté prèviament amb el preprocessament horari oficial.
df_hard = df_campus_hourly.copy()
df_hard["pv_kw"] = df_hard["pv_kw"] * 12.0

spec_hard = {
    "capacity_kwh": 6000.0,
    "power_kw": 1500.0,
    "efficiency": 0.90,
    "soc_init": 0.50,
    "soc_min": 0.0,
    "soc_max": 1.0,
    "dt_hours": 1.0,
    "forecast_horizon": 3
}
env_hard = CampusBatteryEnv(df_hard, spec=spec_hard)
```

**Aclariments d'execució:**
- El fragment no crea `df_campus_hourly`. Cal carregar i netejar les dades com al `starter_kit/tutorial.ipynb`.
- La solar s'escala **una sola vegada** sobre la còpia `df_hard`; no sobre `df_campus_hourly` ni sobre un `df_hard` ja escalat.
- L'agent ha de funcionar amb llistes de mercat de longitud **3**. No fer l'error d'assumir 24 valors o completar les hores 4..24 amb els valors reals del dataframe del test.
- L'anunci de Discord diu que `obs["noves_dades_5min"]` inclourà meteorologia t−1. **El snippet per si sol no mostra com el simulador local injecta aquestes variables**: inspeccionar `environment.py`, el dataframe i el resultat real de `env_hard.reset()` / `step()` abans de donar per fet que són presents.
- Les observacions de capacitat i potència només queden confirmades per inspecció d'`obs`; la presència dels camps esmentats al clamp no implica que l'entorn els emeti.
- Sense una execució comparable a `CampusBatteryEnv` del mode Hard i sense dry-run, **cap puntuació Hard és encara verificable**.

## 3. Contracte i nous tests

- Bateria 6.000 kWh; potència ±1.500 kW; eficiència round-trip 90%; SOC inicial 50%.
- Solar `pv_kw` multiplicada per 12.
- Preus i CO₂ futurs confirmats: `forecast_horizon = 3` (confirmar si les llistes inclouen l'hora actual, segons `environment.py`).
- Provar el clamp per SOC 0, 3.000 i 6.000 kWh; truncaments; energia exportada i demand neta negativa.
- No barrejar el ZIP Standard guanyador de 6,43, les submissions ni les mètriques amb Hard.

## 4. Accions immediates

1. **Oriol:** executar aquest snippet exactament sobre el dataset horari oficial en una **branca separada Hard**. Extreure un exemple real d'observació, obtenir score inicial, infraccions, latència; congelar una baseline.
2. **Cesc:** predictors causals de generació PV (×12) i demanda neta; la meteorologia t−1 només si apareix de debò a `obs`.
3. **Dani:** dissenyar MPC robust 3 h confirmades + horitzó posterior amb prediccions/escenaris; no usar `obs` de Standard de 24 h.
4. **David:** visualitzar excedents i costos realment evitats al Hard; distingir Standard vs Hard i data train vs web.
