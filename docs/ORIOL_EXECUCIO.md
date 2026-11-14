# Oriol — Execució immediata del rol d'integrador (14/11/2026)

**Punt d'entrada:** [START_HERE](START_HERE.md) · [Runbook d'equip](OPERATIU_14NOV.md) · [Issue #2](https://github.com/oriolrz/datathon-fme-2026-la-masia/issues/2)

> **Aquest és un guió d'accions, no un informe de feines ja fetes.** El repte UPC Sostenible ha d'estar confirmat per l'equip. No tocar els mòduls assignats a Cesc/David/Dani i no gastar intents de leaderboard sense acord.

## Fase 0 — Confirmar i sincronitzar (5–10 min)
- [ ] Els presents confirmen UPC Sostenible com a repte; Oriol és l'integrador i qui tramet.
- [ ] Obre PowerShell dins del repo:
```powershell
git status -sb
git switch main
git pull --ff-only
git fetch origin
git switch --track origin/feat/oriol-integration
git status -sb
```
Si la branca local ja existeix, substitueix l'últim `git switch --track ...` per `git switch feat/oriol-integration`; no descartis canvis no commitats.

## Fase 1 — Materials oficials en local, fora del repositori
- [ ] Descomprimeix **paquet_participants_datathon_upc.zip** en una carpeta **germana** al repositori, per exemple `DATATHON/upc_official/`, que contingui `starter_kit/` i `data/train/`.
- [ ] **No descomprimeixis el ZIP a l'arrel del repositori**: el ZIP inclou una carpeta `docs/` que podria barrejar-se amb les nostres instruccions, i els CSV no s'han d'enviar a GitHub.
- [ ] Mantén les dades en local. Si algun agent necessita l'ubicació, passa només la **ruta** de la carpeta al prompt.
- [ ] Si cal instal·lar paquets per simular, crea un entorn `.venv` dins del repo (ignorat a Git). No canviïs la versió global de Python. Comença amb NumPy, pandas i SciPy; els fitxers del simulador són la font real de dependències.
- [ ] Els altres companys han de tenir accés al ZIP oficial per canals autoritzats o el seu propi download.

## Fase 2 — Verificador oficial (15–20 min)
**Amb `upc_official` com a carpeta germana**, aquestes ordres funcionen des de l'arrel del repo:
```powershell
py ..\upc_official\starter_kit\check_submission.py prototypes\upc\agent_v0_24h.py
py ..\upc_official\starter_kit\check_submission.py ..\upc_official\starter_kit\agent.py
```
- [ ] El prototip experimental i la referència oficial passen AST/imports i 24 passos. Si falla, conserva la sortida textual i corregeix la ruta.
- [ ] Reprodueix la simulació anual amb `starter_kit/environment.py`, a través d'un script de validació teu. Compara sobre el **mateix període** score, reducció CO₂, cost, infraccions i segons totals.
- [ ] El 4,26 és un score anterior **sobre TRAIN**, no leaderboard i **NO garanteix** la teva reproducció local si el preprocessament varia.

## Fase 3 — `agent.py` principal (en branca d'Oriol)
- [ ] Utilitza el prototip com a referència per crear un únic `agent.py` importable.
- [ ] Centralitza el safety clamp amb `eta=sqrt(0.9)`, `eps` i cas de SOC 0/2000.
- [ ] Defineix el contracte perquè Dani només hagi d'oferir `src/policy.py: choose_action(obs,load_forecast=None)->float`. Si el mòdul no existeix, mantén una política de reserva funcional.
- [ ] `src/forecast.py` és del Cesc; `dashboard/` és del David; no els modifiquis.
- [ ] Afegeix tests de SOC, formats, salts temporals i rendiment; cap consulta de xarxa ni imports prohibits a l'agent lliurat.
- [ ] Si hi ha mòduls locals importats, empaqueta `agent.py` **i tots els fitxers necessaris** en un ZIP. No depenguis de carpetes locals que el servidor no tingui.
- [ ] Executa el checker **sobre el ZIP final**, no només sobre l'agent.

## Fase 4 — Web oficial, quan el codi estigui estable
- [ ] A https://repteupc.datathon.cat/ > «Lliurament de Solucions», prova **Validació Ràpida (48 h, gratuïta)**.
- [ ] Si és correcta, registra el resultat exactament al relleu. Si falla, captura el missatge d'error sense PIN o credencials.
- [ ] Només amb acord de l'equip, prem **Trametre al Leaderboard**, que consumeix 1 de 10 intents/dia. Anota score públic i versió/commit, sense confondre-ho amb el privat.
- [ ] No desis ni publiquis el PIN a GitHub o als prompts.

## Fase 5 — Relleu de les 14:40–15:00
- [ ] Actualitza [RELLEU_1500.md](RELLEU_1500.md): branch/commit, què funciona, què no, score per tipus, infraccions, runtime, dry-run, incidents i següent checkpoint.
- [ ] Integra PRs revisats només si `main` continua funcionant. No force-push.
- [ ] Comprova que Dani pot llegir [HANDOFF_DANI_1500.md](HANDOFF_DANI_1500.md), el teu relleu i el prototip, i sap que no ha de tocar `agent.py`.

## Prompt exacte per a Codex (inici)
```text
Respon en català i actua com a enginyer d'integració de La MasIA.

Llegeix AGENTS.md, docs/START_HERE.md,
docs/OPERATIU_14NOV.md, docs/AUDITORIA_PLANNING_UPC_TUKEY.md
i docs/ORIOL_EXECUCIO.md.

Aquesta és la meva tasca de la issue #2. La branca que em correspon
és feat/oriol-integration. Les branques remotes ja existeixen;
comprova git status i no descartis canvis.

Objectiu P0: aconseguir un BatteryAgent reproduïble i lliurable
per UPC Sostenible, zero infraccions i proves oficials superades.
L'Starter Kit està fora del repositori a ../upc_official
(o indica'm la ruta real si encara no hi és).

Revisa prototypes/upc/agent_v0_24h.py com a referència experimental,
sense presentar el seu score de train com una estimació de generalització.
Primer comprova el checker oficial i el simulador; després implementa
només agent.py, src/safety.py, tests/ i scripts/.
Mantén una versió estable encara que els mòduls del Dani/Cesc no existeixin.

No toquis src/policy.py, src/mpc.py, src/forecast.py ni dashboard/.
No facis submissions, merge, force-push ni publiquis secrets/dades.
Fes un primer pla curt i continua amb implementació i proves locals.
Acaba informant les comandes executades, resultats reals, fitxers,
riscos i el següent pas; demana'm confirmació abans de push.
```


