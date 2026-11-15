# Lliurament i checklist final — 15/11/2026

## Formulari de presentació a datathon.cat

- Challenge: **UPC Sostenible x AED**.
- **Nom d'equip a avaluar:** el nom EXACTE del registre Hard que realment conté la submissió final. No confondre'l amb el nom del grup de la Datathon ni amb noms provisionals amb sufixos.
- **Presentació:** sí.
- **Side challenge:** marcar **FME Tukey** (si hi participeu). Tinybird només si també hi presenteu un projecte propi que compleixi les seves condicions.
- **Enllaç al repositori públic:** https://github.com/oriolrz/datathon-fme-2026-la-masia
- Prémer **Desa els canvis** i verificar que el formulari conserva les dades.

Laia Álvarez ha aclarit al Discord (15/11 10:40) que **només es revisarà la candidatura d'un nom d'equip indicat** i que el premi UPC Sostenible es decideix pel **Hard Mode i rànquing privat**. Aquesta instrucció més recent preval davant els exemples antics del portal.

## Plataforma d'avaluació d'agents

https://repteupc.datathon.cat/

- La plataforma gestiona les submissões de Normal i Hard independentment.
- Hard final: `hard_final_submission.zip`, fitxers `agent.py`, `hard_v2_model.py`, `params.json` i `dashboard.html`. SHA-256 del ZIP final rebut: `63fc916796cbcc18906972867c854b568a6e1ed40b2dfaafd9dacfdd2a9081a4`.
- Aquest ZIP va superar el checker del paquet oficial en la inspecció local. La puntuació pública de 23,32 és la comunicada per l'equip; confirmar que el ZIP concret s'ha pujat i coincideix amb el registre.
- Mode Normal: la submissió original de 6,43 és independent. Evitar substituir-la amb un prototip.
- Si el Hard final ja està registrat amb el nom correcte, **NO cal repetir l'enviament**.
- Cap punt del leaderboard públic justifica, per si sol, substituir una candidata validada per una altra.

## Publicació de GitHub (obligatori abans de desar)

1. Revisar que no hi ha PIN, tokens, dades restringides o fitxers privats versionats.
2. GitHub → **Settings** → **General** → **Danger Zone** → **Change repository visibility** → **Make public**.
3. Obrir el link en una finestra d'incògnit i confirmar que README, fitxers i branches són visibles.
4. Afegir codi real de la submissió final a `submissions/hard_final/` amb els arxius corresponents, si l'equip autoritza publicar-los, i documentar com reproduir-lo. No substituir amb el prototip de `prototypes/`.
5. Integrar el dashboard final o publicar un enllaç de demo verificat. No publicar dades originals de TRAIN, ZIP de participants o recursos amb drets desconeguts.
6. Actualitzar els enllaços quan el dashboard definitiu estigui a `main`.

## Demo i presentació

Preparar tres minuts tècnics i 90 segons de dashboard. Mostrar: motivació i score 70/30, mecànica Normal/Hard, MPC sota incertesa, resultats públics etiquetats, zero infraccions, validació temporal i limitacions. Backup de demo offline.

**Observació crítica:** actualitzar el README no converteix el repositori en públic ni hi afegeix automàticament els ZIP finals. Aquestes comprovacions s'han de fer manualment abans de l'entrega.

[Portada](../README.md) · [Tukey](TUKEY_DEMO.md) · [Mètode](FINAL_TECHNICAL.md)
