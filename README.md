# La MasIA — Datathon FME 2026

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
| `AGENTS.md` | Instruccions específiques per a Codex |
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

## Com funciona la coordinació entre IA?

Les converses privades de Claude i ChatGPT **no se sincronitzen**. La informació que han de compartir s'escriu als fitxers del repositori i es publica amb Git. Cadascú ha de fer `git pull --ff-only` a `main` abans de començar una nova tasca.

**Important:** que un agent pugui editar fitxers no significa que tingui autorització per publicar automàticament a GitHub, ni per saltar-se les normes del repte.

Bases: https://www.datathon.cat/condicions
