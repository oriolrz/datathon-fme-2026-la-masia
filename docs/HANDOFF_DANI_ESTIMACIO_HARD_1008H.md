# Traspàs al Dani — estimació de score Hard sobre finestres de 1.008 observacions

**Data:** 14/11/2026 · **Objectiu d'aquesta tasca:** fer una estimació **exploratòria** de la variabilitat de la puntuació de l'agent Hard congelat, sense gastar submissions, no construir automàticament un altre model.

## Fonts i què és on
- [PR #8 (draft)](https://github.com/oriolrz/datathon-fme-2026-la-masia/pull/8), commit **`4df0a8aef67ad53f08e91dc5ec78393bf62c0b47`**, branca `codex/oriol-hard-mode-20261114`.
- [Informe de l'agent](https://github.com/oriolrz/datathon-fme-2026-la-masia/blob/4df0a8aef67ad53f08e91dc5ec78393bf62c0b47/experiments/oriol_hard_mode/README.md)
- [Simulador/adaptador](https://github.com/oriolrz/datathon-fme-2026-la-masia/blob/4df0a8aef67ad53f08e91dc5ec78393bf62c0b47/experiments/oriol_hard_mode/lab.py)
- [Polítiques](https://github.com/oriolrz/datathon-fme-2026-la-masia/blob/4df0a8aef67ad53f08e91dc5ec78393bf62c0b47/experiments/oriol_hard_mode/policies.py)
- [Forecast](https://github.com/oriolrz/datathon-fme-2026-la-masia/blob/4df0a8aef67ad53f08e91dc5ec78393bf62c0b47/experiments/oriol_hard_mode/forecast.py)
- [Protocol](https://github.com/oriolrz/datathon-fme-2026-la-masia/blob/4df0a8aef67ad53f08e91dc5ec78393bf62c0b47/experiments/oriol_hard_mode/protocol.json)
- [Paràmetres congelats](https://github.com/oriolrz/datathon-fme-2026-la-masia/blob/4df0a8aef67ad53f08e91dc5ec78393bf62c0b47/experiments/oriol_hard_mode/training.json) i [configuració](https://github.com/oriolrz/datathon-fme-2026-la-masia/blob/4df0a8aef67ad53f08e91dc5ec78393bf62c0b47/experiments/oriol_hard_mode/candidate_config.json).
- [Regles i snippet oficial Hard documentat a main](https://github.com/oriolrz/datathon-fme-2026-la-masia/blob/main/docs/UPC_HARD_SNIPPET_OFICIAL.md). Aquest document pot no ser present a la branca del PR #8, que conté història anterior.
- **Paquet de participants oficial** amb `starter_kit/environment.py` i `data/train/`: és fora de Git, l'ha de descarregar/obtenir el Dani per canals autoritzats. **No pujar-ne els datasets al repositori**.
- ZIP Hard enviable, només en local d'Oriol: `artifacts/oriol_hard_mode/hard_candidate_submission.zip`, SHA-256 `00c48bfc277f3eb6c7b1719c9d6cc82fdadfe3ed173ae24fc642c1620ff56210`. No cal rebre'l per fer l'estudi si es reconstrueix la mateixa configuració; si es comparteix, fer-ho privadament, sense PIN ni dades sensibles.

## Context i resultats que no s'han de confondre

Hard: solar x12, capacitat 6.000 kWh, màxim ±1.500 kW, eficiència .90, SOC inicial .5, només 3 valors de preu/CO₂ (t,t+1,t+2). Excedent no remunerat; la telemetria meteorològica t−1 anunciada no entra al Starter Kit local antic.

Local Hard reportat sobre 5.993 observacions del train (amb **12 salts**): calibratge 12,65; validació 21,19; comprovació 21,04; conjunt complet 16,86; zero infraccions/fallades i 30 tests. El servidor ja ha **superat el dry-run Hard gratuït 48/48, 0 infraccions i 7,097 ms/pas**, però això **no és un score públic**. Darrer líder Hard vist a captura: 23,03 punts, 8 equips/11 trameses en aquell instant; no extrapolar a una classificació actual.

El kit local IGNORA `forecast_horizon=3` i dóna 24 valors. La funció `lab.hard_observation(raw)` els retalla a 3 i afegeix els límits. El motor físic `CampusBatteryEnv` continua essent l'oficial. **No saltar-se l'adaptador** o hi haurà leakage. Les dades tenen 12 discontinuïtats i un salt màxim reportat de 889 hores, i `CampusBatteryEnv` conserva SOC al salt. `lab.py` busca el paquet a `ROOT.parent/'paquet_participants_datathon_upc'`; una altra distribució local requereix configurar explícitament la ruta sense editar el codi congelat.

## Instal·lació recomanada per al Dani

1. Clonar o obrir `oriolrz/datathon-fme-2026-la-masia` localment amb permisos de lectura i fer `git fetch origin`.
2. Crear **worktree/branca pròpia** des del commit congelat Hard, sense tocar `main` ni el PR #8: per exemple `git worktree add -b feat/dani-hard-score-estimation ../datathon-dani-hard origin/codex/oriol-hard-mode-20261114`. Si existeix una branca de mateix nom, escollir-ne una altra sense force/clean.
3. Obtenir el paquet oficial de participants i ubicar-lo com espera el harness o configurar-ne la ruta **només al laboratori propi**, sense canviar els arxius congelats.
4. Crear entorn de Python 3.11 i dependències de `experiments/oriol_hard_mode/requirements.txt`; usar Python real, no àlies WindowsApps.
5. Executar el benchmark de l'agent Hard sense canvis per verificar que el resultat de Dani coincideix (toleràncies i hashes descrits al README); si no coincideix, investigar abans d'extreure conclusions.

## Tasca científica

- Determinar **com és realment una avaluació de 1.008 hores**: són 1.008 *files consecutives* encara que hi hagi gaps, 1.008 hores cronològiques sense gaps, o blocs de setmanes? Si l'especificació no ho defineix, fer **escenaris separats** i etiquetar-los, no fingir que se sap.
- **No** fer bootstrap fila a fila (trenca estacionalitat/SOC/forecast). Evitar recombinar arbitràriament setmanes de forma que inventi històries impossibles. Si es fa resampling per blocs, justificar com s'inicialitza/manté el SOC i com s'actualitzen timestamps.
- Construir proves sobre *TRAIN* amb `CampusBatteryEnv` Hard + adaptador `hard_observation`, el mateix agent/JSON congelats, SOC inicial equivalent i sense recalibrar. En el conjunt hi ha 5.993 files i salts; distingir rolling windows sobre files de finestres cronològiques de 1.008h contínues.
- Començar per finestres de 1.008 observacions que respectin l'ordre original, comprovar si hi ha alternatives contigües reals i fer anàlisi per estacions. No presentar finestres sobreposades com independents.
- Calcular score oficial `evaluate_results` sobre cada finestra (recomputar les seves pròpies bases), CO₂, cost, infraccions, temps, solar, estació i absència de leakage.
- Fer distribució: nombre de finestres, mediana, min, max, P10/P25/P75/P90, diferència per mesos i proporció de finestres >23,03. **No** presentar l'última proporció com probabilitat de guanyar ni els percentils com un interval de confiança del test públic.
- *Control negatiu*: una política standby (0 kW) sobre les mateixes finestres ha de donar score ~0; contrastar MPC amb heurística baseline si n'hi ha de vàlida.
- Analitzar efectes de SOC inicial, gaps, tendència estacionària i diferències entre finestres amb molts/pocs excedents. Indicar si l'avaluació oficial pública sembla provenir d'una distribució diferent; sense inferir el test privat.
- Si es volen fer prediccions més útils que una distribució incondicional, treballar en **escenaris hipotètics transparents** (p.ex. test similar a primavera/estiu/hivern), no inventar la temporada del test.
- Si la simulació no és reproduïble al Dani, aturar estimacions numèriques i explicar el bloqueig amb instruccions concretes. No donar rangs ficticis.

## Lliurables de Dani

1. **Taula per finestra**: identificador, files, dates reals, gaps, estació/composició, SOC inicial/final, score, CO₂, cost, infraccions, temps.
2. **Resum distributiu** amb percentils, mediana i dispersió per règim, i count de finestres realment diferents.
3. **Crítica metodològica**: dades ja explorades, sobreposició, selecció de blocs i diferència amb test públic/privat.
4. Codi reproduïble propi sota `experiments/dani_hard_score_estimation/`, sense alterar els fitxers d'Oriol.
5. Veredicte per l'equip: si la prova aporta una estimació útil o si la variància i el desconeixement de la distribució del test impedeixen donar un rang defensable.
6. PR propi **només si Oriol ho autoritza**; no fer submissions, merge ni push automàtics.

**Norma:** no entrenar, ajustar hiperparàmetres ni modificar `candidate_agent.py` / `training.json` / `candidate_config.json` durant l'experiment. No gastar quota Hard.
