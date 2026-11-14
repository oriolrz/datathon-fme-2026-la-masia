# 🚀 LA MASIA — LLEGEIX AIXÒ PRIMER (14/11/2026)

> **URGENT — HARD MODE ACTIVAT:** [Regles, riscos i estratègia Hard](UPC_HARD_MODE_20261114.md) · [Prompts per als quatre](PROMPTS_HARD_MODE.md). **12× solar, bateria de 6.000 kWh/±1.500 kW i preus/CO₂ només 3h**, amb telemetria meteorològica t−1. Standard 6,43 es conserva. El snippet Hard oficial de la web encara és pendent d'inspeccionar. Prioritzar-lo abans d'adaptar el codi. NO assumir que s'ha arribat al màxim privat.


> **Actualització 15:58 — fase 2:** el MPC ha obtingut **6,43** a l'avaluació web, amb zero infraccions. L'oracle offline en train només supera el MPC per **0,02019** punts en el conjunt complet. El leaderboard mostrat recentment té un màxim de **6,44**, però no és un límit matemàtic. **No gastar més submissions sense millora robusta.** Llegiu [decisió de fase 2](UPC_FASE2_DECISIO_1600.md). Els commits de l'experiment són locals i **no** estan al GitHub; el PR #6 segueix essent l'agent anterior.


> **Font de context compartida de l'equip i dels agents.** Les converses de Codex, Claude i OpenCode **no** se sincronitzen: l'estat real es publica al repositori. Després de cada integració, l'integrador actualitza aquest document i `docs/HANDOFF_DANI_1500.md`.

## Situació a les 12:25 (hora Barcelona)
- Membres presents: **Oriol, Cesc, David**. **Dani arriba cap a les 15:00.**
- **UPC Sostenible** és el candidat prioritari i base d'aquest pla. **La decisió definitiva dels quatre no s'ha confirmat** al xat: ratifiqueu-la abans de desenvolupar.
- Side Challenge: **Tukey**, un dashboard útil per decidir sobre el mateix repte. Premi separat, un finalista per repte; termini/mecanisme pendent.
- Font oficial UPC: https://repteupc.datathon.cat/ ; contracte `BatteryAgent.act(obs:dict)->float`.
- Dades i simulador al ZIP oficial proporcionat per l'organització; **no es troben encara dins el repositori GitHub**. Cada ordinador necessita el seu ZIP autoritzat.
- A GitHub hi ha **anàlisis i documentació**; el prototip local en Python s'ha afegit només com a **referència experimental**, no és el `agent.py` final ni una submissió.
- Proves locals documentades: prototip de llindars 24h **4,26** sobre 5.993 hores d'entrenament (3,86% CO₂, 5,18% cost, 0 infraccions); baseline oficial corregida 1,27. **No és puntuació de leaderboard ni holdout generalitzable.**
- Manca el **dry-run oficial web** i la revisió definitiva del ZIP.
- Restriccions: bateria 2.000 kWh/±500 kW/eficiència 90%, puntuació 70% CO₂ + 30% cost, 10 submissions oficials/dia, dry-run 48h il·limitat, timeout global 60s, fitxer màx. 25 MB, imports de sistema/xarxa prohibits. El safety clamp és crític.
- Discrepàncies documentals: penalització 0,20 vs 1,00; exportació 0 vs 0,04 €/kWh. No dependre'n i preguntar als mentors.

## Documents, per ordre
1. [Runbook operatiu fins a les 15:00 i després](OPERATIU_14NOV.md)
2. [Estat real i bloquejos](STATUS.md)
3. [Auditoria completa](AUDITORIA_PLANNING_UPC_TUKEY.md)
4. [Pla de competició UPC/Tukey](PLA_UPC_TUKEY.md)
5. [Prompts preparats per persona](PROMPTS_EQUIP_UPC.md)
6. [Proves del Starter Kit](UPC_STARTER_TESTS.md)
7. [Experimentació i resultats](EXPERIMENTS.md)
8. [Guia d'incorporació del Dani a les 15:00](HANDOFF_DANI_1500.md)
9. [Plantilla de relleu que s'ha d'omplir](RELLEU_1500.md)

## Repartiment proposat
| Persona | Fins 15:00 | A partir 15:00 | Propietat de codi |
|---|---|---|---|
| Oriol · Codex | Baseline estable, integració, tests, ZIP i dry-run | Integració, comparació de polítiques, trameses | `agent.py`, `src/safety.py`, `tests/`, packaging |
| Cesc · Codex | Preprocessament, QA temporal, perfil estadístic i validació | Forecast causal si millora la puntuació, suport dades del Tukey | `analysis/`, `src/forecast.py`, mètriques d'EDA |
| David · Claude Code | Dashboard Tukey amb dades **reals** de la baseline, sense inventar KPI | Dashboard, documentació, relat i pitch | `dashboard/`, `presentation/` |
| Dani · Claude Code | **Absent, no assignar-li bloquejos** | Heurística avançada/MPC i benchmarks per separat | `src/policy.py`, `src/mpc.py` |

**Important:** aquestes assignacions requereixen el vistiplau del grup. Dani no ha de tocar `agent.py` ni l'estructura del dashboard, excepte acord exprés.

## GitHub: tasques i branques ja preparades

- [#1 Coordinació i decisió de repte](https://github.com/oriolrz/datathon-fme-2026-la-masia/issues/1)
- [#2 Oriol — Integració i validació](https://github.com/oriolrz/datathon-fme-2026-la-masia/issues/2) — `feat/oriol-integration`
- [#3 Cesc — Dades i validació](https://github.com/oriolrz/datathon-fme-2026-la-masia/issues/3) — `feat/cesc-forecast`
- [#4 David — Dashboard Tukey](https://github.com/oriolrz/datathon-fme-2026-la-masia/issues/4) — `feat/david-tukey`
- [#5 Dani — Optimització a partir de les 15:00](https://github.com/oriolrz/datathon-fme-2026-la-masia/issues/5) — `feat/dani-optimizer`

**Branques remotes creades; comanda local:** `git fetch origin` i després `git switch --track origin/feat/<nom>` (si no existeix encara la branca local). **No executeu `git switch -c` amb aquests noms sense comprovar abans el remot.**

## Primeres accions immediates
1. Confirmar UPC Sostenible i propietaris del codi amb l'equip present. Si no es confirma, només coordinació/documentació.
2. Tots: `git switch main && git pull --ff-only` (o comandes per separat a PowerShell), crear branca pròpia i obrir l'agent des de l'arrel correcta.
3. Oriol: posar el **Starter Kit oficial en local** i fer `check_submission.py`; comparar amb el prototip compartit. No pujar dades a Git.
4. Cesc: inspecció de l'agrupació horària i definició de validació per blocs; reportar conclusions.
5. David: dashboard funcional minimalista amb dades d'experiments verificats i vista de decisió, abans de polir disseny.
6. Abans de les 14:45: actualitzar [RELLEU_1500.md](RELLEU_1500.md) amb **fets verificats, commits, score i bloquejos**.
7. 15:00: Dani llegeix [HANDOFF_DANI_1500.md](HANDOFF_DANI_1500.md), prova la seva configuració i agafa la feina d'optimització.

## Norma anti-caos
- No s'inventen mètriques, no es fa `force push`, no es comparteixen PIN/claus/tokens ni dades no autoritzades.
- `main` estable, una branca per persona, una sola persona autoritzada a trametre.
- Si una millora no supera una validació temporal independent o no compleix timeout, es conserva la baseline.
- El primer que ha d'entendre un agent nou és **què està fet, què no, a quina branca ha de treballar, i els fitxers que no ha de tocar**.
