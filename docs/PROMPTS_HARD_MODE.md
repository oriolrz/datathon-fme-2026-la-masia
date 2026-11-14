# Encàrrecs immediats — UPC Sostenible HARD MODE (14/11/2026)

**Llegir primer [UPC_HARD_MODE_20261114.md](UPC_HARD_MODE_20261114.md).** El comunicat confirma 12× solar, bateria 6 MWh/±1.500 kW, 3 hores conegudes de preu/CO₂, telemetria meteorològica t−1 i un leaderboard independent. **Snippet oficial rebut** i documentat a [UPC_HARD_SNIPPET_OFICIAL.md](UPC_HARD_SNIPPET_OFICIAL.md). Encara cal executar-lo i inspeccionar `obs`; no fer submissions fins validar-lo.

## Oriol — Codex (integració/diagnòstic P0)

```text
Respon en català. Llegeix AGENTS.md, docs/UPC_HARD_MODE_20261114.md, docs/UPC_FASE2_DECISIO_1600.md.
PRIORITAT ABSOLUTA: no tocar ni substituir el ZIP Standard que ha obtingut 6,43, ni el PR #6.
1. Comprova git status; assegura't que els commits locals MPC Standard queden conservats. No facis push/merge sense consentiment.
2. Llegeix `docs/UPC_HARD_SNIPPET_OFICIAL.md`: el snippet Hard ja hi és. Executa'l exactament sobre el preprocessament horari oficial i inspecciona les observacions reals; no assumeixis que la meteorologia t−1 apareix automàticament.
3. Quan estigui disponible, construeix un entorn de simulació Hard independent amb les regles exactes: solar x12, bateria 6000 kWh i ±1500 kW, 3 entrades de preus/CO2, meteorologia t-1 i exportació sense compensació. Comprova si hi ha restriccions addicionals.
4. Porta la baseline Standard al format Hard només com a prova, amb safety clamp i tests de 0/6000 i ±1500, sense extrapolar el score anterior.
5. Dóna al Dani i al Cesc interfícies estables (inputs exactes de obs i mètriques), sense sobreescriure fitxers seus. Treballa en una branca/worktree Hard.
6. No facis trameses web, push o merge sense confirmació.
Retorna les rutes, tests reals i benchmark Hard inicial, distingint-lo de Standard.
```

## Cesc — Codex (solar i demanda: ara sí prioritari)

```text
Respon en català. Llegeix docs/UPC_HARD_MODE_20261114.md i les teves anàlisis de dades.
Hard Mode té 12× més solar, ±1500 kW i pot donar load_kw - pv_kw < 0.
Telemetria meteorològica de t-1: irradiancia_wm2, temp_ambient_c, temp_panel_c, vent_ms.
Prioritat: desenvolupa predictors causals de solar i demanda neta per 3..24h. Separa previsions realment disponibles de valors futurs ocults. Valida per blocs temporals amb gaps, establint baseline de perfil horari/estacional i una alternativa meteorològica només amb inputs disponibles a inferència.
Reporta MAE de solar i demanda neta, detecció de situacions d'excedent i **impacte en score Hard** quan l'integrador tingui simulador oficial.
Conserva la teva branca i els models previs. No modifiquis agent.py ni src/mpc.py. No facis submissions ni merge.
```

## Dani — Claude Code (MPC robust i futur desconegut)

```text
Respon en català. Llegeix CLAUDE.md i docs/UPC_HARD_MODE_20261114.md.
El mode Hard és un problema diferent: 6000 kWh, ±1500 kW, 12× solar, només 3h de preu/CO2 confirmats, i excedents solars sense remuneració. El MPC Standard de 24h amb futur perfecte ja NO és directament viable.
Primer revisa `docs/UPC_HARD_SNIPPET_OFICIAL.md` i el `environment.py` real. Dissenya un MPC causal amb 3h conegudes i horitzó més llarg previst o escenaris, valor terminal SOC, autoconsum d'excedent i límits físics.
Comparar heurística sense forecast, MPC 3h i MPC robust/forecast amb les mateixes dades Hard. No usis preus ni CO2 futurs reals fora de obs. Audita LP per càrrega/descàrrega simultànies i unitats.
No toquis el codi de l'Oriol, del Cesc ni del David. No facis push, merge o submissions.
```

## David — Claude Code (Tukey amb canvi de règim)

```text
Respon en català. Llegeix docs/UPC_HARD_MODE_20261114.md i els criteris oficials Tukey.
El nou mode Hard obre una història molt més rellevant: energia solar 12×, excedents amb valor d'exportació 0, bateria 6 MWh i només 3h de mercat conegudes.
Al dashboard, separa completament Standard i Hard; no inventis scores Hard ni comparis magnituds de períodes o bases diferents.
Prioritza vista d'excedents solars i autoconsum, valor de previsions, trajectòria SOC, cost-vs-CO2 i errors de forecast per franges/meteorologia.
No bloquegis el simulador: comença amb l'estructura i mètriques Standard reals, però etiqueta totes les dades. Quan l'Oriol exporti experiments Hard, afegeix comparacions reals, robustesa i decisions accionables.
Confirma termini, modalitat de lliurament i si Tukey permet els dos modes.
```

## Regla compartida
- **Hard i Standard són dos productes/leaderboards independents**. No substituïu el codi Standard en el seu lloc.
- **El snippet oficial Hard és la font de veritat**, no una reimplementació per intuïció.
- El test privat no està resolt, ni tan sols al mode Standard (aclariment de l'organització).
- 2 intents Hard per finestra de 4 hores; ús només després de test local i dry-run.
