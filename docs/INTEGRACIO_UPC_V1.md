# BatteryAgent v1 — evidència local d'integració

**14/11/2026 · Oriol · issue #2 · branca `feat/oriol-integration`.** Encàrrec d'integració autoritzat per l'Oriol. Les mesures es van fer sobre `1bb02e1fd026f98399aba6da716f1be7cca991aa` amb arbre modificat; els hashes identifiquen el codi exacte. L'Oriol ha autoritzat crear el commit, publicar exclusivament aquesta branca i obrir un PR cap a `main`, sense fusionar-lo. El commit de la branca i el PR identifiquen la versió publicada; això no acredita la ratificació del repte pels quatre ni una integració a `main`.

## Què funciona

- `agent.py: BatteryAgent.act(obs) -> float`, amb reserva de llindars 24h equivalent al prototip en les dades vàlides.
- Clamp únic a `src/safety.py`: `eta=sqrt(0.9)`, epsilon de `1e-4 kW`, capacitat de 2.000 kWh i potència màxima de ±500 kW per passos d'1 h. SOC invàlid o absent i consignes no finites impliquen repòs.
- Previsions de longitud 0–24, camps malformats i salts temporals tractats sense excepcions en els casos provats. La reserva no conserva telemetria i no usa consum/solar futurs.
- Simulació amb `environment.py` oficial sense modificar-lo; dades fora del repositori a `../paquet_participants_datathon_upc`.
- Empaquetament determinista de les dependències locals importades, checker oficial del ZIP i backtest del ZIP en un procés aïllat.

## Entorn i reproducció

Python **3.11.9**, NumPy **2.4.1**, pandas **2.3.3**. Dependències exactes a `requirements-validation.txt`; `pip check` correcte. El lliurable usa només la biblioteca estàndard, sense requerir aquests paquets per executar l'agent.

Els àlies `py`/`python` de WindowsApps fallen en aquest entorn. S'ha creat `.venv` amb l'intèrpret real, sense modificar el Python global:

```powershell
& C:/Users/oriol/AppData/Local/Python/pythoncore-3.11-64/python.exe -m venv .venv
& ./.venv/Scripts/python.exe -m pip install -r requirements-validation.txt
& ./.venv/Scripts/python.exe -m pip check
```

En un altre ordinador es pot crear la mateixa `.venv` amb qualsevol Python 3.11 disponible. Des de l'arrel del repositori, les ordres de validació executades són:

```powershell
& ./.venv/Scripts/python.exe -X utf8 ../paquet_participants_datathon_upc/starter_kit/check_submission.py prototypes/upc/agent_v0_24h.py
& ./.venv/Scripts/python.exe -X utf8 ../paquet_participants_datathon_upc/starter_kit/check_submission.py ../paquet_participants_datathon_upc/starter_kit/agent.py
& ./.venv/Scripts/python.exe -B -X utf8 -m unittest discover -s tests -v
& ./.venv/Scripts/python.exe -B -X utf8 -u scripts/evaluate.py
& ./.venv/Scripts/python.exe -B -X utf8 scripts/package.py
& ./.venv/Scripts/python.exe -B -X utf8 scripts/verify_submission.py
```

Els scripts accepten `--official-root` si el paquet és en una altra ruta. Els tests accepten la variable `UPC_OFFICIAL_ROOT`; si falta el kit fallen explícitament. `agent.py` importa mòduls locals: **cal lliurar el ZIP complet**, perquè el checker d'un `.py` individual només copia aquell fitxer al directori temporal.

## Resultats reals del train complet

Run `20261114T120340Z` (13:03:40 Europe/Madrid), llavor `20261114`. Preprocessament transcrit del tutorial oficial: mitjanes horàries de consum i solar, clips i unió amb preu/CO₂, sense interpolar les hores absents. **5.993 files**, del **01/09/2025 00:00** al **16/08/2026 22:00**. Hi ha **12 salts** diferents d'una hora, el màxim de **889 hores**.

| Política | Score | CO₂ estalviat | Cost estalviat | Infraccions | Simulació local (s) |
|---|---:|---:|---:|---:|---:|
| Repòs | 0,00 | 0,00% | 0,00% | 0 | 2,122 |
| Referència oficial original | 0,00 | 0,88% | 2,18% | 46 | 2,154 |
| Referència oficial + clamp exacte | 1,27 | 0,88% | 2,18% | 0 | 1,978 |
| Prototip 24h preexistent | 4,26 | 3,86% | 5,18% | 0 | 2,209 |
| BatteryAgent amb reserva | **4,26** | **3,86%** | **5,18%** | **0** | **2,137** |

Temps de la taula: instanciació de l'agent i de l'entorn, tots els passos i `evaluate_results`, sense imports/lectura/preprocessament. Varia amb la càrrega de l'ordinador. El procés aïllat del ZIP, incloent extracció, imports, lectura, preprocessament i simulació, ha trigat **3,977685 s**; la simulació dins d'aquell procés ha trigat **1,492401 s**. No és una mesura del servidor web.

La reserva estalvia **21.308,5 kg de CO₂** i **48.655,55 €** sobre les bases oficials de **551.822,5 kg** i **939.634,22 €**. SOC inicial **1.000 kWh**, final **1.999,999905 kWh**; **1.688** passos de càrrega, **940** de descàrrega i **3.365** de repòs. No s'ha imposat neutralitat del SOC final, seguint el simulador oficial.

### Diagnòstics temporals, sense ajustar paràmetres

Tall fixat a `2026-03-01`. Cada bloc reinicia agent i SOC a 1.000 kWh i limita les previsions al seu període. Els salts interns conserven el SOC, com al motor oficial.

| Reserva | Hores | Score | CO₂ | Cost | Infraccions |
|---|---:|---:|---:|---:|---:|
| Setembre–febrer | 2.784 | 3,32 | 2,92% | 4,26% | 0 |
| Març–agost parcial | 3.209 | 5,09 | 4,73% | 5,93% | 0 |

**Aquests blocs ja formaven part del train explorat anteriorment. No són un holdout independent ni una estimació de generalització.** Les xifres poden diferir del desglossament històric que conservava SOC o horitzons del recorregut complet. No s'han canviat hiperparàmetres ni seleccionat polítiques amb aquests diagnòstics. No hi ha score de leaderboard ni test ocult.

## Proves i paquet final

**11 tests superats** (`unittest`, 1,142 s de suite): SOC extrems i veïns de coma flotant, límits físics calculats independentment, sortides finites, 10.009 estats aleatoris reproduïbles amb equivalència exacta al prototip, previsions incompletes, salts de timestamp, recuperació de candidates que fallen, física contra l'entorn oficial, 2.016 passos sintètics sota 60 s, dependències transitives i importació del ZIP sense `site-packages`.

El checker oficial ha aprovat el prototip, la referència original i **el ZIP final** (AST/imports/classe/24 passos). La referència supera el checker tot i les 46 infraccions del backtest: el checker no comprova tota la física del recorregut real.

Lliurable local: `artifacts/submission.zip`, **2.609 bytes**. Contingut exacte:

```text
agent.py
src/__init__.py
src/fallback.py
src/safety.py
```

SHA-256 del ZIP: `24e3376dd27b7ca104bfc69a5a952db8d82794f05111b67bd38122b1e0506cf0`.

El backtest aïllat del ZIP té **les mateixes mètriques i totes les mateixes 5.993 consignes** que el codi font. SHA-256 de les accions en float64 little endian: `dc16ad64022b7a9cd599759fede7ec1fc9d233eb0588484938612affb6aeb34a`.

Evidència local, tota sota `artifacts/` ignorat a Git:

- `evaluation/metrics.json` i `metrics.csv`: resultats de les cinc polítiques i tres períodes, versions, llavor, commit base, arbre modificat i hashes de codi/material oficial.
- `validation/prototype_checker.txt`, `reference_checker.txt`, `tests.txt` i `evaluate.txt`: sortides reals de les ordres.
- `submission.manifest.json` i `submission.checker.txt`: hashes, mida, fitxers i resultat del checker final.
- `validation/zip_simulation.json`: equivalència de la traça, mètriques, runtime complet del procés i hashes dels inputs.

Revisió prèvia a publicació: `git diff --check` correcte; els 18 fitxers revisats només contenen codi, proves, dependències i documentació. Cap dataset, credencial, PIN, entorn virtual, temporal o artefacte entre els fitxers versionats o candidats. Repetició dels **11 tests correcta** (0,994 s), checker del ZIP correcte i simulació aïllada correcta: **4,841240 s** totals, mateixes 5.993 consignes i mètriques, 0 infraccions. Evidència addicional: `validation/tests_pre_push.txt`, `zip_checker_pre_push.txt`, `zip_simulation_pre_push.json` i `pre_push_audit.json`, tots locals i ignorats a Git. El ZIP conserva el mateix SHA-256.

No s'han copiat datasets al repositori, ni inclòs dades, credencials o entorns al ZIP. Aquest informe només recull mètriques agregades; les traces horàries de consum/solar no s'exporten.

## Contracte amb el Dani i el Cesc

La versió estable no depèn de l'existència de `src/policy.py`, `src/mpc.py` o `src/forecast.py`. Per comparar la futura política:

```python
from agent import BatteryAgent
from src.policy import choose_action

agent = BatteryAgent(policy=choose_action)
# choose_action(obs, load_forecast=None) -> float
```

El wrapper aplica sempre el clamp després de la candidata. Si aquesta llança una excepció o retorna un valor no finit/no convertible, usa la reserva i incrementa `policy_failures`. `scripts/evaluate.py` rebutja candidates amb errors recuperats, infraccions o runtime de 60 s o més; una recuperació segura no compta com a candidata vàlida.

Hi ha l'opció `--candidate-policy src/policy.py` per a mòduls candidats amb imports absoluts. Per usar imports relatius o un forecast causal cal integrar explícitament el mòdul al wrapper quan estigui revisat. L'agent estable passa `load_forecast=None`; no s'ha integrat cap predictor. L'aparició d'un fitxer del Dani no canvia automàticament la reserva.

Abans d'activar una candidata al lliurable, cal comparar-la en el banc acordat, canviar explícitament el default d'`agent.py`, regenerar el ZIP i repetir checker i simulació aïllada. `scripts/package.py` segueix els imports locals i rebutja dependències absents; models/configuracions futurs necessitaran un manifest d'actius explícit.

## Límits i pas següent

- **Dry-run web de 48 h pendent**; no s'ha carregat cap fitxer al portal ni fet cap submissió oficial. La quota global de l'equip no s'ha consultat; en aquesta sessió s'han gastat **0** intents.
- El runtime local té marge sota 60 s, però no acredita el CPU/RAM ni el comportament del servidor.
- Pendent una validació temporal acordada amb el Cesc per comparar futures polítiques sense reutilitzar dades de selecció.
- Continuen pendents les contradiccions oficials: penalització 0,20/1,00, remuneració d'excedents i vectors de previsions que travessen buits. S'ha seguit `environment.py`: exportació 0 €/kWh i penalització 0,20; la reserva no té infraccions.
- La reserva pot descarregar en hores amb poc consum net: no coneix demanda/solar futures. El límit físic està verificat, l'òptim econòmic no està garantit.
- Publicació de la branca i PR autoritzats per l'Oriol. **Revisió i merge a `main` pendents; cap submissió oficial.**

Següent pas: revisió del PR i execució manual de la Validació Ràpida web. Els fitxers del Dani, Cesc i David no s'han modificat.

## Validació Ràpida web de 48 hores

Passos contrastats amb la interfície i la FAQ de [la plataforma oficial](https://repteupc.datathon.cat/) el 14/11/2026. **Només s'ha inspeccionat la web; no s'hi ha carregat ni executat el ZIP.**

1. Fes servir el ZIP actual `artifacts/submission.zip` (2.609 bytes), sense tornar-lo a comprimir. Si el vols comprovar amb PowerShell: `Get-FileHash -Algorithm SHA256 .\artifacts\submission.zip`. Ha de coincidir amb `24e3376dd27b7ca104bfc69a5a952db8d82794f05111b67bd38122b1e0506cf0`.
2. Obre `https://repteupc.datathon.cat/` i selecciona la pestanya **Lliurament de Solucions**.
3. Al **Formulari de Tramesa**, posa `La MasIA` al camp **Nom de l'Equip:**. La pantalla també mostra **PIN de Seguretat de l'Equip (mínim 4 caràcters):** i **Noms i Cognoms dels Integrants (obligatori en el 1r lliurament):**. Si la validació els requereix, completa'ls directament a la web amb les dades acordades; no comparteixis el PIN en registres ni captures.
4. A **Arxiu de la solució:**, prem **Upload** i selecciona el ZIP actual de la carpeta `artifacts`. Comprova que el nom carregat sigui `submission.zip`.
5. Prem exclusivament **🧪 Validació Ràpida (Sense gastar quota)**. La FAQ confirma que executa **48 hores**, és **gratuïta i il·limitada** i prova imports, format i càrrega de models.
6. Espera el resultat i registra el missatge real, la data/hora, el SHA del commit i el SHA del ZIP. Si falla, guarda el text d'error sense PIN ni altres secrets. El resultat de format/execució de 48 h no és una puntuació de leaderboard.
7. Acaba aquí. **No premis 🚀 Trametre al Leaderboard**: aquest és el botó que consumeix un intent oficial.

**Actualització respecte a la documentació inicial:** la web ara indica 10 intents de leaderboard **per franja**, fins a 30 en total: dissabte fins a les 21 h, dissabte de 21 h fins a diumenge a les 08 h, i diumenge des de les 08 h fins al tancament. La Validació Ràpida continua sense consumir quota. No s'ha consultat la quota utilitzada de l'equip.
