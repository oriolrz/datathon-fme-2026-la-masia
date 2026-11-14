# Battery Decision Lab · La MasIA (Premi Tukey)

Dashboard interactiu de suport a la decisió per al repte **UPC Sostenible**.
Responsable: **David** · branca `feat/david-tukey`.

**Principi:** cap número s'escriu a mà. Tot surt del `CampusBatteryEnv` oficial, i el pipeline s'atura si
el recàlcul dels KPI no coincideix amb `evaluate_results`. El simulador del navegador (laboratori) és un
port exacte a TypeScript, verificat amb `npm run verify-sim` (v1 → 4,256 vs 4,26 oficial, |Δp| < 0,005 kW).

## Execució (Windows, des de l'arrel del repo)

```powershell
pip install -r dashboard\requirements.txt
python -m dashboard.pipeline.build          # simula els agents -> dashboard\web\public\data\*.json (~25 s)
python -m pytest dashboard\tests -q         # tests de coherència amb el simulador oficial

cd dashboard\web
npm install
npm run verify-sim                          # el simulador TS reprodueix l'oficial
npm run dev                                 # http://localhost:5173
npm run build                               # versió estàtica a dashboard\web\dist (per a la demo sense servidor de dev)
```

El paquet oficial es busca a `UPC_KIT_DIR`, a `dashboard/config.local.json` (`{"kit_dir": "..."}`) o a
`~/Documents/DATATHON/paquet_participants_datathon_upc`. Les dades generades **no es pugen a Git**.

## Afegir agents de l'equip

```powershell
python -m dashboard.pipeline.build --git-agent dani_mpc=origin/feat/dani-optimizer
python -m dashboard.pipeline.build --agent prova=ruta\agent.py
```

`--git-agent` extreu `agent.py` + `src/` de la branca sense tocar-la. Per incloure'l sempre,
afegiu-lo a `TEAM_DEFAULTS` a `pipeline/agents.py`. El leaderboard públic es manté a
`web/public/leaderboard.json` (només resultats verificats).

## Vistes (cadascuna respon a una pregunta de decisió)

| Pestanya | Pregunta | Elements clau |
|---|---|---|
| 1. Resum i decisió | Quina política enviem i quant marge queda? | Recomanació automàtica, KPI, % del sostre teòric, composició del score, trade-off CO₂/cost amb línies d'iso-score, score acumulat, posició al leaderboard |
| 2. Operació hora a hora | Quan carrega/descarrega i té sentit? | Senyals, energia, consigna i SOC enllaçats; panell "context de la decisió" en passar el cursor |
| 3. Patrons | Actua a les hores correctes? | Mapes de calor hora×mes, perfil diari, qualitat de l'arbitratge per rang de cost social |
| 4. Robustesa · Tukey | Funciona cada setmana o només de mitjana? | Boxplots amb tanques de Tukey (clic als atípics), duel directe, validació A/B per mesos alterns, taula setmanal |
| 5. Pèrdues i potencial | On es perd energia i punts? | Sankey de fluxos, cicles, pèrdues, energia abocada, bretxa amb l'òptim per hora del dia, distribució del SOC |
| 6. Laboratori what-if | Quina millora val la pena enviar? | Simulació en directe de dues famílies de política, dimensionament de bateria, supòsits del reglament, control antisobreajust, desar la variant com a agent |

Controls globals: agent principal, agent de comparació, període (estació, mes, laborables), penalització
(0,20 codi vs 1,00 enunciat), tema clar/fosc. L'estat queda a l'URL (`#tab=…&a=…&b=…&p=…`).

## Resultats actuals (train, 5.993 h; no és el leaderboard)

| Agent | Score | ΔCO₂ | ΔCost | Infr. |
|---|---:|---:|---:|---:|
| Plantilla oficial | 0,00 | 0,88% | 2,18% | 46 |
| Plantilla + clamp | 1,27 | 0,88% | 2,18% | 0 |
| La MasIA v1 (PR #6) | 4,26 | 3,86% | 5,18% | 0 |
| **Òptim teòric** (LP amb informació perfecta) | **5,68** | 5,27% | 6,62% | 0 |

Lectures per a l'equip:
- La v1 captura un **75%** del sostre teòric del train.
- L'òptim carrega molt més a les **hores solars (12–15 h)**, en què el CO₂ és més baix, i la v1 hi carrega poc. Vegeu "Patrons" i "Pèrdues i potencial".
- Al laboratori, limitar la descàrrega a la demanda dona +0,02 (4,28). Els llindars de la v1 ja són a prop del màxim local (corba de sensibilitat plana entre 0,12 i 0,22).

## Arquitectura

```
dashboard/
├── pipeline/   config · data (taula del tutorial) · agents (registre, --git-agent) · simulate (env oficial)
│               metrics (fórmula evaluate_results) · oracle (LP HiGHS) · build (JSON + verificació)
├── tests/      coherència amb environment.py (ometen la prova si el paquet no hi és)
└── web/        Vite + React + TypeScript + ECharts; src/sim.ts = port verificat del simulador
```
