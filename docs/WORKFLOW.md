# Flux de treball — GitHub, Claude Code i Codex

## Avui: preparar sense desenvolupar el repte

1. Afegiu els quatre col·laboradors i confirmeu que han acceptat la invitació.
2. Cada persona ha de poder clonar el repositori, crear una branca, pujar un canvi de documentació innocu i obrir un pull request.
3. Comproveu Git, VS Code, Python, Codex o Claude Code i l'autenticació.
4. No implementeu codi específic del repte abans del seu inici oficial.
5. Llegiu els fitxers d'instruccions i la [guia d'accessos](ACCESSOS.md).

## Durant la Datathon

1. Escolliu un dels reptes oficials i ompliu `docs/BRIEF.md`.
2. Definiu la baseline, els contractes de mòduls i qui és responsable de cada fitxer.
3. Creeu issues concretes amb persona, abast, fitxers, resultats esperats i proves.
4. Creeu branques independents des de `main`: `feature/cesc-eda`, `feature/dani-baseline`, etc.
5. Cada agent rep **una tasca acotada** per sessió.
6. Executeu les proves, apunteu resultats reals i prepareu un commit.
7. Publiqueu la branca amb `git push` (amb l'aprovació del responsable) i obriu un PR.
8. Una altra persona revisa; després feu el merge i comproveu la integració a `main`.
9. Actualitzeu `docs/STATUS.md`, `docs/DECISIONS.md` i `docs/EXPERIMENTS.md`.
10. Feu una prova de punta a punta aproximadament cada 2–3 hores.

## Comandes bàsiques

```bash
git switch main
git pull --ff-only
git switch -c feature/nom-tasca
# Feu només la feina acordada
git status
git add ruta/dels/fitxers
git commit -m "feat: descripció breu"
git push -u origin feature/nom-tasca
# Obriu un pull request a GitHub i reviseu abans de fusionar
```

No feu `git reset --hard` sense revisar conseqüències, ni force-push, ni edicions simultànies a la mateixa branca.

## Prompt compartit per donar feina a un agent

```text
Respon en català.

Llegeix AGENTS.md (Codex) o CLAUDE.md (Claude Code) i també
docs/TEAM_RULES.md, docs/BRIEF.md, docs/STATUS.md,
docs/DECISIONS.md, docs/ACCESSOS.md i docs/WORKFLOW.md.

Issue i responsable: [ISSUE / PERSONA]
Branca: [BRANCA]
Fitxers que em corresponen: [RUTES EXACTES]
Contracte d'entrada/sortida: [SI APLICA]
Definició d'acabat: [PROVES / RESULTATS COMPROVABLES]

Primer comprova la branca, git status i la documentació.
Proposa un pla mínim i treballa només dins d'aquest abast.
Fes proves i indica les ordres i els resultats reals.
No sobreescriguis la feina aliena, no fusionis ni facis force-push,
no inventis mètriques, no publiquis dades restringides ni secrets.
Demana acord abans de publicar canvis a GitHub.
Acaba amb un resum llest per al pull request.
```

## Checkpoints

- Reunió breu després de triar repte i arquitectura.
- Revisió i integració del producte cada 2–3 hores.
- Congelar funcionalitats amb marge suficient per comprovar entrega i assajar.
