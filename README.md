# La MasIA — Datathon FME 2026

## 🚨 Novetat: Hard Mode UPC

[Regles i pla urgent](docs/UPC_HARD_MODE_20261114.md) · [Encàrrecs per als quatre agents](docs/PROMPTS_HARD_MODE.md). **12× solar, bateria 6 MWh i ±1.500 kW, previsions confirmades només de 3 hores i leaderboard separat.** El mode Standard 6,43 segueix intacte; el privat no està maximitzat. Falta el snippet oficial de la pestanya Hard abans d'implementar.


**Resultat web confirmat 14/11 (primer enviament): [4,03 punts, −3,72% CO₂, −4,75% cost, 0 infraccions](docs/UPC_PRIMER_RESULTAT_WEB.md).** A la plataforma constava 1/10 intents gastats del primer torn. Diferencieu aquesta puntuació pública de 4,26 sobre train. PR #6 pendent de merge.


## ⚡ Situació operativa d'avui (14/11)

**[COMENÇA AQUÍ — context únic per als agents](docs/START_HERE.md)** · [Runbook 12:25–15:00](docs/OPERATIU_14NOV.md) · [Dani entra a les 15:00](docs/HANDOFF_DANI_1500.md) · [Relleu que s'ha d'actualitzar](docs/RELLEU_1500.md).

**Branques creades:** `feat/oriol-integration`, `feat/cesc-forecast`, `feat/david-tukey`, `feat/dani-optimizer`. **Issues:** [coordinació #1](../../issues/1), [Oriol #2](../../issues/2), [Cesc #3](../../issues/3), [David #4](../../issues/4), [Dani #5](../../issues/5). Les assignacions són provisionals fins a l'acord de l'equip.

**Codi experimental compartit:** [prototip 24h UPC](prototypes/upc/agent_v0_24h.py), no és la submissió final ni una puntuació del leaderboard.


**Equip:** Oriol, Cesc, Dani i David  
**Dates:** 14–15 de novembre de 2026  
**Idioma de treball:** català (excepte noms d'eines, codi i identificadors)

> Aquesta estructura és **preparació organitzativa**. El desenvolupament de la solució específica del repte comença durant la competició, seguint les bases i indicacions dels organitzadors.

## Comencem

1. Tots quatre heu d'acceptar la invitació al repositori privat i clonar-lo.
2. Obriu aquesta carpeta amb VS Code i inicieu Claude Code o Codex dins del projecte.
3. Codex llegirà `AGENTS.md`; Claude Code llegirà `CLAUDE.md`. Tots dos consultaran els mateixos documents compartits.
4. **Abans de la competició:** completeu la [checklist de preparació](docs/PREPARACIO.md). Després, consulteu les [normes comunes](docs/TEAM_RULES.md), els [accessos i permisos](docs/ACCESSOS.md) i el [flux amb Git](docs/WORKFLOW.md).
5. Quan comenci la competició, llegiu els reptes, utilitzeu la [matriu per escollir el repte](docs/TRIATGE_REPTES.md) i completeu el [brief oficial](docs/BRIEF.md).
6. Cada tasca ha de tenir responsable, branca i criteris de finalització. Integreu els canvis amb pull requests i reviseu que `main` funciona.
7. Registreu els resultats reals a [experiments](docs/EXPERIMENTS.md) i les decisions a [decisions](docs/DECISIONS.md).

## Fitxers principals

| Fitxer | Per a què serveix |
|---|---|
| `AGENTS.md` | Instruccions específiques per a Codex i OpenCode |
| `CLAUDE.md` | Instruccions específiques per a Claude Code |
| `.claude/settings.json` | Permisos locals compartits de Claude Code: `acceptEdits` |
| `docs/PREPARACIO.md` | Checklist, comprovacions d'eines i horaris d'arribada |
| `docs/TRIATGE_REPTES.md` | Guia per comparar els tres reptes en començar |
| `docs/TEAM_RULES.md` | Normes i criteris compartits per als quatre i les IA |
| `docs/ACCESSOS.md` | Configuració dels permisos i diferència entre editar i publicar |
| `docs/BRIEF.md` | Enunciat, objectius, dades i criteris del repte |
| `docs/STATUS.md` | Estat, responsabilitats, branques i bloquejos |
| `docs/DECISIONS.md` | Decisions tècniques i justificacions |
| `docs/EXPERIMENTS.md` | Experiments, mètriques i reproduïbilitat |
| `docs/WORKFLOW.md` | Guia de branques, pull requests i encàrrecs als agents |
| `docs/DELIVERY.md` | Comprovacions abans de presentar i entregar |
| `.github/pull_request_template.md` | Plantilla per revisar els canvis |

## OpenCode gratuït (HelmCode)

Aquest equip també pot utilitzar OpenCode amb HelmCode. Vegeu la [guia d'instal·lació i autenticació](docs/HELMCODE_OPENCODE.md) i el fitxer `opencode.json`, que no conté cap clau.

Per revisar el candidat Tinybird/RawTree, consulteu [REPTES_TINYBIRD.md](docs/REPTES_TINYBIRD.md), pendent de rebre l'enunciat complet.

## Pla de competició (pendent de decisió de l'equip)

**Comenceu per la [nova auditoria de viabilitat i riscos](docs/AUDITORIA_PLANNING_UPC_TUKEY.md) abans d'executar els prompts dels agents.**

- [Guia operativa UPC Sostenible + Premi Tukey](docs/PLA_UPC_TUKEY.md)
- [Prompts preparats per a Oriol, Cesc, Dani, David i una auditoria OpenCode](docs/PROMPTS_EQUIP_UPC.md)
- [Anàlisi i proves del Starter Kit](docs/UPC_STARTER_TESTS.md)

Aquests documents són **propostes**: no determinen el repte ni assignen rols fins que els quatre ho acordeu.

## Com funciona la coordinació entre IA?

Les converses privades de Claude i ChatGPT **no se sincronitzen**. La informació que han de compartir s'escriu als fitxers del repositori i es publica amb Git. Cadascú ha de fer `git pull --ff-only` a `main` abans de començar una nova tasca.

**Important:** que un agent pugui editar fitxers no significa que tingui autorització per publicar automàticament a GitHub, ni per saltar-se les normes del repte.

Bases: https://www.datathon.cat/condicions
