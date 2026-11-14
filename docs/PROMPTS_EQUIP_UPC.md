# Encàrrecs preparats per als quatre agents — UPC Sostenible

> **No executeu aquests prompts fins que l'equip hagi escollit oficialment UPC Sostenible i s'hagi acordat un responsable per fitxer.**
>
> Cada persona obre la seva branca local i actualitza `main` abans de començar. Les instruccions de `AGENTS.md`, `CLAUDE.md` i `docs/TEAM_RULES.md` continuen vigents.

## Oriol — Codex: integració, tests i entrega

```text
Respon en català. Llegeix AGENTS.md i docs/PLA_UPC_TUKEY.md.
Tasca: preparar l'estructura integrable del BatteryAgent d'UPC Sostenible
a partir del Starter Kit oficial, sense modificar les branques d'altres persones.

Branca: feat/oriol-integration
Propietat exclusiva: agent.py, src/safety.py, tests/, scripts/validation.py.
No implementis la política avançada del Dani ni el predictor del Cesc;
defineix interfícies importables i defaults segurs.

Criteris: BatteryAgent.act(obs)->float; clamp amb sqrt(0.9) i epsilon;
0 infraccions en extrems de SOC; passar check_submission.py;
una simulació reproduïble amb mètriques i temps; no fer push o merge sense el meu vistiplau.
Primer revisa l'estat Git i proposa un pla de 5 passos.
```

## Cesc — Codex: EDA i predicció sense leakage

```text
Respon en català. Llegeix AGENTS.md i docs/PLA_UPC_TUKEY.md.
Tasca: estudiar les sis sèries de train del Starter Kit i crear un
predictor de demanda neta per a fins a 24 hores.

Branca: feat/cesc-forecast
Propietat exclusiva: analysis/, src/forecast.py, reports/forecast*.
No modifiquis agent.py, src/policy.py ni src/mpc.py.

Criteris: documentar temps/mostres/NA/gaps, sumar els 3 inversors,
invertir correctament el signe de contador, validar en blocs temporals
resguardats, comparar contra perfil horari/estacional, donar
forecast_net_load(obs, horizon=24) i no usar dades futures no observades.
Exporta només mètriques agregades verificables per al dashboard;
no publicar CSV del campus.
```

## Dani — Claude Code: control i optimització

```text
Respon en català. Llegeix CLAUDE.md i docs/PLA_UPC_TUKEY.md.
Tasca: desenvolupar i comparar una política de bateria, primer heurística
i després MPC/LP 24h, amb limitació estricta de temps i memòria.

Branca: feat/dani-optimizer
Propietat exclusiva: src/policy.py, src/mpc.py, tests/test_optimizer.py.
No modifiquis agent.py, dashboard/ ni src/forecast.py.
Interfície: choose_action(obs, load_forecast=None)->float en kW.

Criteris: mateix score del simulador, sense ús de xarxa, zero infraccions
després de safety clamp (la integració el garanteix), cap demanda futura
real fora d'obs, ablations reals contra la baseline i prototip ja provat,
runtime global mesurat amb marge de 60s i regressions automàtiques.
Una solució que no superi la baseline en validació temporal no s'integra.
```

## David — Claude Code: Premi Tukey i pitch

```text
Respon en català. Llegeix CLAUDE.md i docs/PLA_UPC_TUKEY.md,
especialment els criteris oficials del Premi Tukey.
Tasca: dissenyar un dashboard de presa de decisions de bateria anomenat
«La MasIA Battery Decision Lab».

Branca: feat/david-tukey
Propietat exclusiva: dashboard/, presentation/, reports/dashboard*.
No modifiquis agent.py, src/policy.py ni src/forecast.py.
Entrada: fitxers de resultats AGREGATS dels experiments locals.

Criteris: KPI Score/CO2/cost/infraccions, línia temporal SOC i potència,
comparació d'estratègies, boxplots de variabilitat per període, scatter
cost-vs-CO2, filtres, eixos amb unitats i etiquetes train/holdout.
Mostrar conclusions accionables i verificables, no decorar.
Proposar Streamlit+Plotly o HTML estàtic segons la forma de lliurament
que confirmin els mentors. Preparar una demo curta amb pla de reserva.
No incloure dades brutes o informació privada del campus al repositori.
```

## Agent extra — OpenCode amb HelmCode (auditoria independent)

```text
Llegeix AGENTS.md i docs/PLA_UPC_TUKEY.md. Fes NOMÉS una revisió de codi,
sense editar fitxers ni fer commit. Busca riscos de leakage temporal,
violacions de límits del SOC, dependències prohibides, temps d'execució
superior a 60 segons, manca de tractament dels salts entre setmanes,
sobreajust al leaderboard i discrepàncies d'unitats. Classifica els
problemes per gravetat i proposa proves concretes reproduïbles.
```

## Integració

- Una sola persona revisa i fusiona PRs a `main`.
- El David consumeix resultats verificats del simulador, no xifres inventades.
- Els experiments de cada agent s'enregistren a `docs/EXPERIMENTS.md` abans de la decisió final.
- Abans de trametre, recupera `main`, executa el validador del Starter Kit, simula en dades locals, comprova espai/temps/format, usa dry-run web (48h) i només llavors envia al leaderboard.
