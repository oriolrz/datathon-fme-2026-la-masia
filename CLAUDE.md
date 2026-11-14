# La MasIA — Instruccions per a Claude Code

Treballes dins d'un repositori compartit de quatre persones a la Datathon FME 2026. **Respon, redacta documentació i coordina't en català.** Mantén en anglès els noms de biblioteques, la sintaxi del codi i els identificadors existents.

## Context del dia (prioritat màxima)

Llegeix **`docs/START_HERE.md`** abans de començar. Durant el 14/11/2026, consulta també **`docs/OPERATIU_14NOV.md`** i **`docs/RELLEU_1500.md`**. El Dani arriba a les **15:00**; no li deleguis tasques bloquejants abans d'aquella hora. Les tasques i branques creades a GitHub són propostes fins que l'equip confirmi formalment el repte i els rols. No sobreescriguis les tasques d'una altra persona.

**IMPORTANT:** les quatre branques remotes ja existeixen. Per començar utilitza `git fetch origin` i `git switch --track origin/feat/nom-persona-tasca` si encara no tens branca local. Si ja existeix, utilitza `git switch nom-persona-tasca` (sense `-c`).

## Context obligatori abans d'actuar

1. `docs/TEAM_RULES.md`
2. `docs/BRIEF.md`
3. `docs/STATUS.md`
4. `docs/DECISIONS.md`
5. `docs/WORKFLOW.md`
6. `docs/ACCESSOS.md`

## Normes d'actuació

- Primer comprova `git status`, la branca actual i si hi ha fitxers modificats localment. No sobreescriguis la feina dels companys.
- Confirma qui és el responsable, quina tasca o issue s'ha assignat, quins fitxers pots tocar i què es considera acabat.
- Abans de l'inici oficial de la competició, no escriguis la solució específica del repte.
- Treballa a la teva branca i dins l'abast acordat. Avisa abans de tocar fitxers compartits.
- Fes canvis petits, verificables i reproduïbles. Protegeix l'estabilitat de `main`.
- El projecte configura `acceptEdits` per acceptar edicions locals habituals. **Això no és permís per fer push, merge, force-push o accions destructives sense acord explícit.**
- No inventis mètriques ni resultats. Registra l'split de dades, la llavor, les mètriques i l'evidència real.
- Respecta les normes de les dades i l'ús d'IA. No publiquis contrasenyes, tokens, dades privades ni dades restringides.
- En acabar, resumeix els fitxers modificats, les proves executades (i resultats reals), els límits, els bloquejos i el pas següent.
- No afirmis que GitHub està actualitzat fins a comprovar que els canvis hi han arribat.

**Font de veritat:** els fitxers compartits del repositori, no els historials de conversa de Claude o ChatGPT.
