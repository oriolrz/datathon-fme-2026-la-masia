# 👋 Dani — Incorporació a les 15:00 (Datathon FME 2026)

**Aquest document està escrit a les 12:25; és el pla d'incorporació, no un informe de feina acabada.** Per conèixer què s'ha executat de debò fins a les 15:00, llegeix primer [RELLEU_1500.md](RELLEU_1500.md), actualitzat pels tres companys quan acabi el bloc.

## 1. Què ha passat mentre no hi eres?
- Els tres presents fins a les 15:00 són **Oriol, Cesc i David**.
- El projecte principal proposat és **UPC Sostenible**, un agent que gestiona una bateria del Campus Nord; només s'activa aquest pla si l'equip el confirma.
- Side quest **Tukey**: dashboard sobre el repte principal. El David n'és el responsable provisional.
- Oriol: `agent.py`, integració, safety clamp, tests i trameses.
- Cesc: dades, qualitat, validació temporal i predicció si aporta millora.
- Dani (tu): **optimització i polítiques avançades**, en una branca pròpia. **No has de refer la feina d'EDA, baseline ni dashboard.**
- Resultats locals previs a les 12:25: baseline segura 1,27 punts; prototip heurístic 4,26 punts/0 infraccions **en train**; cap puntuació oficial de leaderboard confirmada.
- Prototip compartit: `prototypes/upc/agent_v0_24h.py` (referència, no la submissió definitiva).

## 2. Context mínim del repte (2 minuts)
- `BatteryAgent.act(obs) -> float`: positiu carrega, negatiu descarrega, zero standby.
- SOC `[0,2000]` kWh; potència `[-500,500]` kW; round-trip `0.9`; inicial 1000 kWh.
- Maximitzar `Score=70%*reducció_CO2 +30%*estalvi_cost - penalitzacions`.
- `obs`: SOC actual, hora/dia, preu i CO₂ actuals, vectors 24h de preu i CO₂, consum/solar **anteriors**, no futurs.
- Avaluador web sense xarxa ni subprocessos; `numpy/scipy/sklearn/xgboost/lightgbm` i biblioteques autoritzades; **60 segons per simulació sencera**.
- `check_submission.py` és només una prova de format/safety de 24 passos. Les millores s'avaluen amb `environment.py` + validació temporal.
- Les sèries de dades tenen salts entre setmanes; **no inferir que la fila anterior és una hora immediatament anterior**.
- No gastar submissions oficials sense acord d'Oriol.

## 3. On has de llegir el context (ordre recomanat, 8–12 minuts)
1. `CLAUDE.md` i `docs/START_HERE.md` (idioma català i normes).
2. `docs/RELLEU_1500.md` (**estat verificat en arribar**).
3. `docs/STATUS.md` i `docs/AUDITORIA_PLANNING_UPC_TUKEY.md` (restriccions).
4. `docs/UPC_STARTER_TESTS.md` i `docs/EXPERIMENTS.md` (resultats preexistents).
5. `prototypes/upc/agent_v0_24h.py` (algorisme original per superar).
6. Després, si necessites detalls: `docs/PLA_UPC_TUKEY.md` i `docs/PROMPTS_EQUIP_UPC.md`.

## 4. Setup i primera tasca amb Claude Code
Al terminal, des del directori local del projecte:
```bash
git status
git switch main
git pull --ff-only
git switch -c feat/dani-optimizer
```

**Si la branca ja existeix**, fes `git switch feat/dani-optimizer` i actualitza la branca segons l'estat de Git; no executis el `-c` a cegues.

Arrenca Claude Code dins de la carpeta del repositori (o la seva extensió). Fes-lo començar en mode lectura, amb aquest prompt:

```text
Respon en català. Abans d'editar res, llegeix CLAUDE.md, docs/START_HERE.md,
docs/RELLEU_1500.md, docs/AUDITORIA_PLANNING_UPC_TUKEY.md,
docs/UPC_STARTER_TESTS.md i prototypes/upc/agent_v0_24h.py.

Comprova branca, git status, interfície BatteryAgent i quines tasques ja han fet
Oriol, Cesc i David. No repeteixis aquesta feina. La meva responsabilitat és
NOMÉS src/policy.py, src/mpc.py i tests/test_optimizer.py.

Proposa un MVP d'optimització a 24h que superi la heurística inicial
sense fuites temporals, infraccions físiques ni superar 60s de simulació completa.
Primer ensenya el pla, dependències i interfícies; després implementa la
tasca acotada. No toquis agent.py, dashboard ni docs/STATUS.md.
No facis merge, force-push o trameses web.
```

## 5. Primera entrega esperada (pròxim checkpoint)
- `choose_action(obs,load_forecast=None)->float` importable des de `src/policy.py`.
- Política de millora o LP de 24h; explicar supòsits i restriccions.
- Comparativa reproduïble amb `agent_v0_24h.py` en **les mateixes setmanes**: score, CO₂, cost, infraccions, runtime.
- Si el MPC és lent o no millora el resultat independent, documentar-ho i mantenir la baseline.
- Commit i PR propis, lliurats a Oriol; **no tocar `agent.py` final**.
- Notes i números al relleu/issue mitjançant PR, sense falses dades.

## 6. Preguntes que hauràs de fer a l'Oriol en arribar
1. Hem ratificat definitivament UPC Sostenible?
2. Quin és el score/revisió estable de l'agent **a les 15:00** i on és el seu commit?
3. Quin contracte m'ha donat el Cesc per a la demanda neta futura?
4. Hi ha algun error actual de validador/dry-run que faci canviar les prioritats?
5. Quina hora és la següent integració i quan congelen les entregues?

**Principi:** comença des de l'últim estat de GitHub, no des de converses de Claude o missatges antics.
