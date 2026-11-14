# Relleu per al Dani — 14/11/2026, 15:00

> **Actualització parcial real d'Oriol, 13:03–13:07.** Apartat d'integració completat amb proves locals; dades de Cesc/David i decisions conjuntes encara pendents. Cal revalidar l'estat entre les 14:40 i les 15:00. Les caselles buides i «Pendent» NO són feines fetes.

## Decisió de repte
- [ ] UPC Sostenible confirmat pels tres presents / confirmació pendent del Dani
- Si no: indicar alternativa i motiu:
- Responsable de les submissions oficials:

## Estat de l'algorisme (Oriol)
- Branca / commit revisat: `feat/oriol-integration`, base d'avaluació `1bb02e1fd026f98399aba6da716f1be7cca991aa`; commit/push i PR autoritzats per l'Oriol, merge pendent. La versió publicada s'identifica amb el commit de la branca i el PR cap a `main`. Hashes de codi/ZIP al [registre v1](INTEGRACIO_UPC_V1.md).
- Versió estable de `agent.py`: reserva de llindars 24h + `src/safety.py` amb `sqrt(0.9)` i epsilon `1e-4 kW`. Candidata futura connectable explícitament, independent dels mòduls del Dani/Cesc.
- Test local exactament executat: `python -B -X utf8 -m unittest discover -s tests -v` (amb `.venv/Scripts/python.exe`): **11 tests passats**, inclosos 10.009 estats aleatoris i simulació sintètica de 2.016 passos. `scripts/evaluate.py`, `scripts/package.py` i `scripts/verify_submission.py` correctes.
- Score **train** / **validació temporal** / **leaderboard públic** (separar!): train complet **4,26** (5.993 h); diagnòstics de train amb reinici de SOC **3,32** abans de març / **5,09** des de març. **Validació independent pendent; leaderboard no executat.**
- Estalvi CO₂ (%): **3,86%**, **21.308,5 kg** al train complet.
- Estalvi cost (%): **5,18%**, **48.655,55 €** al train complet.
- Infraccions: **0** a l'agent estable; referència original **46**, referència amb clamp **0** (score **1,27**).
- Runtime complet (s): **3,977685 s** procés aïllat del ZIP amb imports/lectura/preprocessament i 5.993 passos; simulació font **2,137351 s** sense imports/lectura/preprocessament. No és mesura del servidor.
- `check_submission.py`: **Passat** al prototip, referència original i **ZIP final**, en procés aïllat. Paquet de **2.609 bytes**, SHA-256 `24e3376dd27b7ca104bfc69a5a952db8d82794f05111b67bd38122b1e0506cf0`. ZIP i font tenen les mateixes 5.993 consignes.
- Dry-run web 48h: **Pendent; no s'ha carregat cap fitxer al portal.**
- Submissions oficials gastades i disponibles avui: **0 en aquesta sessió**; quota global de l'equip no consultada.
- Bloquejos / regressions: cap bloqueig d'execució local. Publicació de la branca i PR autoritzats; pendent revisió del PR, dry-run web, protocol de validació independent i aclariments del mentor. Els diagnòstics ja explorats no acrediten generalització. Repetició abans de publicar: 11 tests passats, checker del ZIP passat i procés aïllat 4,841240 s amb consignes idèntiques.

## Dades i prediccions (Cesc)
- Fitxers i branques treballats:
- Filtratge i salts temporals detectats:
- Split de validació congelat:
- Baseline de demanda/solar i resultats:
- Exports disponibles per a l'optimitzador:
- Limitacions:

## Premi Tukey (David)
- Branca / commit:
- Dashboard accessible on:
- Gràfics amb dades REALS ja implementats:
- Fonts i períodes de les mètriques:
- Preguntes útils que respon:
- Bloquejos / elements pendents:
- Termini de Tukey confirmat? Sí / No; hora i procediment si es coneix:

## Decisió conjunta a les 15:00
- Tasca concreta del Dani:
- Fitxers que pot modificar (NO `agent.py`):
- Criteri de millora mesurable:
- Proves i benchmark acordats:
- Hora de proper checkpoint:
- Responsables de revisar el PR:
- Dubtes als mentors encara pendents:

## Incidències conegudes
- Penalització: discrepància documental 0,20 vs 1,00 (intentar 0 infraccions).
- Exportació: discrepància documental 0 vs 0,04 €/kWh; simulador local `0.0`.
- Salts temporals entre blocs de dades.
- Temps límit global del servidor: 60s.
- No incloure secrets ni datasets al repositori.

**Última actualització real:** Oriol · Codex, 14/11/2026, revisió prèvia a publicació de les 13:11 Europe/Madrid; base d'avaluació `1bb02e1`, publicació de la branca i PR autoritzats, merge pendent.
