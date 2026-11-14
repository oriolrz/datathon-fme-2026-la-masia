# Fase 2 — marge real del MPC

**Conclusió: conservar el MPC de 6,43 i no gastar una nova tramesa amb aquestes variants.** Cap canvi desplegable aporta una millora prou gran i robusta. Els oracles només diagnostiquen dades locals; no demostren que 6,43 sigui el màxim del test públic o privat.

## Versió congelada i rollback

El laboratori anterior i la candidata estan versionats al commit **`dfe0345fa9d6be77187753515bc555bf826853ff`**, a la branca local `codex/oriol-optimization-20261114`, sense push. Aquesta fase treballa a `codex/oriol-optimization-phase2-20261114`. No s'ha modificat cap fitxer anterior, el PR #6 ni els mòduls dels companys.

ZIP preservat: `artifacts/oriol_optimization/candidate_submission.zip`, **6.194 bytes**, SHA-256 **`50b1a794711d2221855147e44c6be8fc33c9221a9b0bbe258f0f84675721752f`**. Còpia de rollback amb els 12 fitxers font, ZIP i manifest a `artifacts/oriol_optimization/rollback_6_43/50b1a794711d/`. També hi ha una còpia idèntica a `artifacts/oriol_phase2/selected_current_submission.zip`. Per tornar a la millor versió només cal utilitzar aquest ZIP verificat; no cal regenerar-lo ni modificar `agent.py`.

L'usuari ha reportat 6,43 públic, 5,95% CO₂ (4.276,6 kg), 7,54% cost (8.957,61 €), zero infraccions i dry-run 48 h superat (6,499 ms/pas). No s'ha consultat ni tramès res al portal en aquesta fase; el servidor no ha certificat el SHA del ZIP.

## Referències amb informació perfecta

Tots els episodis comencen amb 1.000 kWh. Es conserva el preprocessament i el motor oficial, inclosos els salts i exportació no remunerada. `perfect24` coneix demanda/PV reals de les 24 files següents: **no desplegable**. L'oracle complet coneix tot el període i usa les bases percentuals exactes del mateix període: **no desplegable**. SOC final lliure, com a l'avaluació oficial.

| Període | Hores | MPC actual | Demanda perfecta 24 files | LP futur complet, bases exactes | Marge màxim experimental |
|---|---:|---:|---:|---:|---:|
| Calibratge abans de març | 2.784 | 4,619219919 | 4,619219919 | 4,619220402 | 0,000000484 |
| Validació març–maig | 1.704 | 6,553241792 | 6,553241792 | 6,558849139 | 0,005607346 |
| Comprovació juny–agost | 1.505 | 6,748775928 | 6,816087212 | 6,817281214 | 0,068505286 |
| Train complet, diagnòstic | 5.993 | 5,655071759 | 5,674517484 | 5,675261712 | **0,020189952** |

Els decimals provenen de les sumes de cost/CO₂ sense arrodonir; els scores oficials locals es continuen retornant amb dos decimals. Les cotes numèriques conservadores del LP són 4,619221090 / 6,558849896 / 6,817281886 / 5,675262414. Inclouen un marge pel terme de throughput `1e-8`; l'avaluació és numèrica, no una certificació racional exacta.

Per al train complet, el marge es descompon en:

- **0,019445725 punts**: conèixer demanda/PV reals amb només 24 passos.
- **0,000002334 punts** addicionals: horitzó complet amb els mateixos normalitzadors de calibratge.
- **0,000741894 punts** addicionals: conèixer les bases percentuals exactes del període complet.

Per tant, gairebé tot el marge restant local prové de la poca demanda neta en algunes hores, no d'un terminal de 1.000 kWh o un horitzó massa curt. El model actual ja captura aproximadament el **99,64% del score de l'oracle local complet**. Aquest percentatge no s'atribueix al leaderboard.

## Totes les alternatives en les mateixes finestres

CO₂/cost són percentatges de validació. Temps de procés local complet: imports, inicialització, lectura/preprocessament i simulació; en els casos del Cesc també inclou l'auditoria repetida del model/targets. No són temps del servidor ni costos purs del predictor.

| Política | Calibratge | Validació | CO₂ % | Cost % | Infraccions | Procés val. s |
|---|---:|---:|---:|---:|---:|---:|
| MPC actual | 4,619220 | 6,553242 | 5,65 | 8,66 | 0 | 6,40 |
| Demanda perfecta 24h, oracle | 4,619220 | 6,553242 | 5,65 | 8,66 | 0 | 7,15 |
| Estacional, mitjana setmanal | 4,619220 | 6,553242 | 5,65 | 8,66 | 0 | 6,85 |
| Persistència causal | 4,619220 | 6,553242 | 5,65 | 8,66 | 0 | 8,81 |
| Cesc C, només t | 4,619220 | 6,553242 | 5,65 | 8,66 | 0 | 12,51 |
| Cesc C, 24h amb alineament assumit | 4,619220 | 6,553242 | 5,65 | 8,66 | 0 | 12,57 |
| Terminal suau | 4,619220 | 6,553546 | 5,65 | 8,66 | 0 | 7,13 |
| Valor ombra terminal | 4,619220 | 6,553546 | 5,65 | 8,66 | 0 | 9,60 |
| SOC terminal dinàmic | 4,619220 | 6,553349 | 5,65 | 8,66 | 0 | 8,62 |
| Horitzó 12h | 4,614095 | 6,553089 | 5,68 | 8,60 | 0 | 7,75 |
| Horitzó 6h | 4,471786 | 6,384775 | 5,44 | 8,58 | 0 | 7,60 |
| Normalització mitjanes no ponderades | 4,619122 | 6,551456 | 5,63 | 8,69 | 0 | 9,28 |
| Normalització online causal | 4,618620 | 6,558143 | 5,73 | 8,49 | 0 | 8,04 |

Les variants terminals canvien el SOC final planificat: penalització L1 de desviació de 1.000 amb lambda=0,5·eta·mitjana(v), valor ombra eta·mitjana(v), o target segons el rang del valor de les últimes sis hores. Cap paràmetre s'ha cercat al leaderboard. Quan el vector oficial s'escurça fins al final real de l'episodi, es retira la reserva terminal; un horitzó de planificació de 6/12 h no es confon amb el final de l'episodi.

El protocol es va fixar abans de les proves: mínima millora de 0,01 punts, cap mes de validació per sota de l'actual−0,02, zero infraccions/fallades i menys de 45 s locals. Calibratge tria la millor variant per família; validació avalua aquesta selecció congelada. Les variants descartades i la normalització online es van completar després només com a diagnòstic, **sense modificar la selecció**. El millor terminal suau guanya 0,000304 punts en validació i empata exactament en comprovació. La normalització online guanya **0,004901606** en validació però perd **0,007117718** en comprovació (6,741658210 vs 6,748775928). La persistència guanya 0,005539036 en comprovació, amb validació empatada. Cap millora supera el criteri prefixat ni justifica una tramesa.

**Totes són particions internes del train ja explorat pel projecte.** No són nous holdouts independents. No s'ha ajustat cap alternativa després de veure comprovació.

## Forecast del Cesc, causalitat i alineament

Durant l'execució s'ha publicat `src/forecast.py` a `feat/cesc-forecast`, commit **`acc09c06b30d9dcf78f38c88e9c554b2c2f8f57c`**. S'ha llegit amb `git show`, sense checkout ni modificacions, i s'ha conservat un snapshot local ignorat a Git. `cesc_compare.py` usa una instància pròpia de `NetLoadForecaster(method='C')` per episodi.

S'han reproduït amb el nostre calibratge les 168 medianes setmanals, el clip residual i els mateixos targets. El hash inicial diferia perquè el nostre índex és `datetime64[ns]` i el del Cesc `datetime64[us]`: normalitzant a microsegons s'obté exactament `983c2625463295130880f2f03118c405fc3389a195c91346c118fe8c1980c8eb`. Aquesta comprovació addicional no canvia el predictor ni les decisions.

| Previsió de t | MAE validació, 1.704 hores | Score val. | Score comprovació | Malbaratament comprovació |
|---|---:|---:|---:|---:|
| Constant 500 kW | 506,33 kW | 6,553242 | 6,748776 | 1.432,62 kWh |
| Mitjana setmanal pròpia | 98,31 kW | 6,553242 | 6,748776 | 1.432,62 kWh |
| Persistència causal pròpia | 32,07 kW | 6,553242 | 6,754315 | 983,94 kWh |
| Cesc C | 53,97 kW | 6,553242 | 6,748776 | 1.432,62 kWh |
| Demanda perfecta, oracle | 0,00 kW | 6,553242 | 6,816087 | 0,00 kWh |

El forecast C dona **exactament les mateixes consignes** que el MPC actual en els tres períodes, comprovades per SHA-256, tant usant només t com usant les 24 hores. El MAE d'aquí usa tots els orígens de t, no només les 1.635 finestres completes de l'informe del Cesc.

Amb n>=500 kW i bateria limitada a 500, el cost marginal de l'acció no depèn del nivell exacte de n; reduir MAE sobre 500 no millora l'òptim. La versió conservadora de l'adaptador usa només la previsió de t i 500 per a la resta. L'altra versió assumeix hores consecutives: el forecast del Cesc és cronològic però els preus/CO₂ són files i poden travessar salts. **No s'han usat timestamps futurs del CSV per censurar horitzons**, perquè això no és observable a `obs`.

## Auditoria matemàtica, física i temps

Es minimitza `sum(G_t*(0.7*c_t/C0+0.3*p_t/K0))`; `C0,K0` són bases sense bateria. En inferència s'aproximen exclusivament amb mitjanes de calibratge ponderades per energia. La versió online associa la telemetria de l'hora anterior al seu preu/CO₂ anterior i ignora els salts, sense mirar bases futures. L'oracle de bases exactes només existeix al diagnòstic.

`G=max(load−PV+charge−discharge,0)`, `SOC_next=SOC+sqrt(0.9)*charge−discharge/sqrt(0.9)`. Límits 0–2.000 kWh i 0–500 kW per sentit; cada consigna passa pel clamp amb epsilon. En tots els oracles complets: càrrega/descàrrega simultànies **0 kW**, residu màxim del balanç SOC **2,28e-13 kWh**, slack mínim de xarxa >=−2,28e-13 kW i gap primal-dual màxim **8,23e-7** en les unitats de l'objectiu. Les proves inclouen eficiència, excedent PV sense remuneració i absència de cicles ficticis.

**30 tests únics passats**: 11 estables, 8 fase 1 i 11 fase 2/adaptador Cesc. El ZIP congelat torna a superar el checker oficial i reprodueix les mateixes 5.993 consignes en procés aïllat de **22,046266 s**, amb inicialització/imports/lectura/preprocessament, zero infraccions i zero fallades. El SHA és idèntic abans i després. Això deixa marge local respecte dels 60 s; no és una mesura completa del servidor. No s'ha fet cap dry-run nou ni submissió.

## Fitxers i reproducció

`model.py`: alternatives i adaptador genèric; `bench.py`: finestres/oracles/comparació; `protocol.json`: criteri prefixat; `cesc_compare.py`: adaptador del commit del Cesc; dos fitxers de tests; `results_summary.json`: resultats agregats, cotes, configuracions, hashes i rollback. Les dades, ZIP i snapshots són només a `artifacts/`, ignorat a Git. Els tres fitxers de model/protocol/benchmark es conserven amb els mateixos hashes de la congelació prèvia a validació.

Des de l'arrel del repositori amb la mateixa `.venv` de la fase 1:

```powershell
& ./.venv/Scripts/python.exe -B -X utf8 experiments/oriol_optimization/phase2/bench.py bounds
& ./.venv/Scripts/python.exe -B -X utf8 experiments/oriol_optimization/phase2/bench.py calibrate
& ./.venv/Scripts/python.exe -B -X utf8 experiments/oriol_optimization/phase2/bench.py validate
& ./.venv/Scripts/python.exe -B -X utf8 experiments/oriol_optimization/phase2/bench.py confirm
& ./.venv/Scripts/python.exe -B -X utf8 experiments/oriol_optimization/phase2/cesc_compare.py
& ./.venv/Scripts/python.exe -B -X utf8 -m unittest discover -s experiments/oriol_optimization/phase2 -p test_*.py -v
```

Per repetir qualsevol diagnòstic no seleccionat: `bench.py worker --model normalization_online --period confirmation` (o l'identificador/període de les taules). Els resultats detallats executats i els logs són a `artifacts/oriol_phase2/` i `artifacts/validation/phase2_*`. La importació del forecast fixat requereix que l'objecte Git `acc09c0` sigui disponible localment; no hi ha xarxa en inferència.

**Recomanació operativa:** conservar el ZIP verificat de 6,43, compartir aquests resultats amb l'equip quan s'autoritzi publicar-los i no fer una tramesa nova només per canvis de decimals o MAE. Les dades ocultes, la recompensa d'exportació del servidor i les seves bases percentuals continuen fora d'aquest diagnòstic; no es pot proclamar un òptim del leaderboard.
