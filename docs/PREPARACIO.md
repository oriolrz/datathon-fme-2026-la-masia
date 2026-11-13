# Preparació abans de la Datathon — La MasIA

**Objectiu:** arribar el dissabte 14/11/2026 amb els quatre equips tècnics preparats, sense haver desenvolupat la solució de cap repte.

> Les bases oficials prohibeixen presentar codi de la solució escrit fora de l'esdeveniment. Preparar accessos, instal·lacions, rols i coordinació sí que és una activitat organitzativa. Quan els organitzadors expliquin el repte, confirmeu les regles específiques.

## 1. Verificació individual (10–20 minuts per persona)

- [ ] Inscripció i plaça personal confirmades al dashboard de la Datathon.
- [ ] Invitació al repositori GitHub acceptada amb el propi usuari.
- [ ] Repositori clonat: `git clone https://github.com/oriolrz/datathon-fme-2026-la-masia.git`
- [ ] Carpeta oberta a VS Code.
- [ ] Git i Python disponibles (vegeu ordres més avall).
- [ ] Claude Code (Dani/David) o Codex (Oriol/Cesc) obre una sessió des de la carpeta correcta.
- [ ] L'agent pot llegir `CLAUDE.md` o `AGENTS.md` i els fitxers compartits.
- [ ] El compte té autenticació GitHub funcionant, inclòs `git push` a una branca pròpia.
- [ ] Endoll, carregador, adaptador, bateria i connexió alternativa preparats.
- [ ] Cada persona sap on són `docs/STATUS.md` i `docs/WORKFLOW.md`.

### Ordres de diagnòstic (terminal a VS Code)

```bash
git --version
git status
git branch --show-current
python --version
python -m pip --version
```

**Windows:** si `python` no està disponible, proveu `py -V` i `py -m pip --version`.

Per comprovar l'agent, executeu **una** de les ordres següents si teniu instal·lat el CLI corresponent:

```bash
claude --version
# o bé
codex --version
```

Si utilitzeu només l'extensió de VS Code, verifiqueu que l'extensió es pot iniciar i llegir la carpeta.

### Prova de col·laboració sense codi de repte

1. Amb el repositori net: `git switch main` i `git pull --ff-only`.
2. Creeu una branca amb nom únic: `git switch -c chore/nom-prova-git`.
3. Creeu una nota temporal `prova-nom.txt` amb el vostre editor; **no conté cap solució**.
4. `git add prova-nom.txt` i `git commit -m "test: comprovar accés GitHub"`.
5. `git push -u origin chore/nom-prova-git`.
6. Comproveu al web que podeu obrir un pull request cap a `main`. **No el fusioneu**.
7. Tanqueu el PR de prova, si l'heu obert, i torneu a `main` amb `git switch main`. La branca remota es pot esborrar des del web després de la prova.

Eviteu que dues persones utilitzin el mateix nom de branca. Si la terminal demana credencials, completeu l'inici de sessió de GitHub amb el vostre compte.

## 2. Arribada i horaris útils (web oficial)

- **Dissabte 14/11, 08:30:** check-in al Vèrtex.
- **09:00:** cerimònia inaugural.
- **10:00:** esmorzar i presentació dels reptes.
- **11:30:** excursió/desplaçament a l'FME.
- **12:00:** activitat GitHub 101.
- **Diumenge 15/11, 12:00:** últim avís per a les entregues.
- **14:00:** demos.

Comproveu el dashboard i els avisos dels organitzadors per si els horaris canvien. Web: https://www.datathon.cat/

## 3. Pla dels primers 30 minuts després d'escoltar els reptes

- **0–10 min:** tothom llegeix els tres enunciats i identifica dades, objectius, mètriques i terminis.
- **10–20 min:** puntueu-los amb `docs/TRIATGE_REPTES.md` i escolliu-ne un.
- **20–30 min:** ompliu `docs/BRIEF.md`, definiu una baseline, una demo possible i 4 tasques independents.
- Escolliu un únic responsable d'integració i protegiu una versió funcional a `main`.

## 4. Què NO fem avui

- No es creen models entrenats, pipelines, scrapers, notebooks ni una demo específica dels reptes.
- No es generen dades per simular el repte que encara no coneixem.
- No es pugen dades confidencials de l'organització a GitHub ni a serveis d'IA sense autorització.
- No es donen permisos il·limitats a agents sobre els ordinadors personals.

## 5. Material pràctic

Portàtil i carregador, regleta si teniu, ratolí/adaptadors, dades mòbils com a reserva, targeta o QR d'accés, aigua, menjar lleuger i alguna peça d'abric. Si us quedeu fins tard, planifiqueu descans.
