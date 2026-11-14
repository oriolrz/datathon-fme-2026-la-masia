# Hard Mode — candidata causal independent

**Recomanació: provar `hard_candidate_submission.zip` al dry-run gratuït Hard de 48 h.** Candidata seleccionada: `mpc24_annual`. Encara no hi ha resultat Hard del servidor. No s'ha fet cap upload, tramesa, push ni merge.

Branca local: `codex/oriol-hard-mode-20261114`. Tots els canvis d'aquesta missió són dins d'aquest laboratori; `agent.py`, els mòduls dels companys i el PR #6 es conserven. Commits Standard preservats: `dfe0345fa9d6be77187753515bc555bf826853ff` i `1176f719a236124d0d661e5c6ab4a9271beb21c5`. ZIP Standard de 6,43 preservat amb SHA-256 `50b1a794711d2221855147e44c6be8fc33c9221a9b0bbe258f0f84675721752f`, tornat a comprovar al final.

## Contracte real i discrepància del kit

S'ha llegit el tutorial i `../paquet_participants_datathon_upc/starter_kit/environment.py` directament. El preprocessament reutilitza `scripts/evaluate.py`, transcripció dels passos oficials: demanda del comptador amb signe invertit, clip 0–5.000 i mitjana horària; suma dels tres inversors, sense duplicar fases, i mitjana horària; intersecció amb preu i CO₂.

La física és exactament la del kit: capacitat 6.000 kWh, potència ±1.500 kW, SOC inicial 3.000 kWh, `eta=sqrt(0.9)`, pas 1 h, exportació a 0 €/kWh. La solar s'escala ×12 una sola vegada abans de crear l'entorn. L'exportació no genera crèdit de CO₂.

**El snippet literal amb `forecast_horizon=3` continua produint vectors de 24 elements.** Aquest kit ignora el paràmetre, no injecta meteorologia ni els camps `cap_max_kwh`/`power_max_kw`. SHA-256 del motor oficial: `06dcc2ea2ce9ea09ecde97b0437765be5e08553e8e28306b5bf7aaeb39542ae7`.

Per evitar donar informació extra a l'agent, `hard_observation` trunca els dos vectors a 3 i incorpora només els dos límits de bateria publicats. No inventa meteorologia. Per tant, els resultats següents són **física oficial + adaptador explícit de l'observació Hard anunciada**, no una certificació d'un simulador oficial Hard actualitzat. La lectura de la [web oficial](https://repteupc.datathon.cat/) confirma el contracte anunciat: solar ja ×12 a la telemetria t−1 i tres hores de mercat, incloent l'actual.

La primera telemetria del kit revela la fila actual. S'ignora a la primera crida i després de qualsevol salt temporal. Les actualitzacions utilitzen exclusivament la lectura t−1 quan el timestamp avança exactament una hora. El SOC es conserva als salts perquè així ho fa el motor oficial; no s'hi simulen hores absents. Hi ha 12 salts i el més gran és de 889 hores. No hi ha novembre disponible.

## Protocol i resultats executats

Calibratge: 2.784 files, 01/09/2025–21/02/2026, límit exclusiu 01/03. Validació: 1.704 files, 01/03–24/05/2026, límit exclusiu 01/06. Comprovació: 1.505 files, 01/06–16/08/2026 22:00. Cada episodi comença al 50%; el full de 5.993 hores és un episodi continu. Per això els resultats dels blocs no es poden sumar per reconstruir el full.

S'han fixat nou configuracions a `protocol.json`. Calibratge tria una guanyadora per família; validació les ordena; comprovació avalua les mateixes sense ajustar cap paràmetre. Els hashes de sis fitxers congelen fonts, configuracions i entrenament abans de validar. Llavor declarada 20261114; les polítiques i els tres escenaris són deterministes. Cap ajust al leaderboard. **Són particions internes del train ja explorat pel projecte, no un test privat nou.** El calibratge és in-sample per als perfils; no s'usa com a prova de generalització.

CO₂/cost i runtime de la taula corresponen a **validació**. Runtime = procés complet d'aquell bloc, incloent imports, preprocessament, inicialització, simulació i escriptura de traces; no només una decisió. Totes les files tenen també zero fallades i zero infraccions en calibratge i comprovació.

| Política | Score calibratge | Score validació | Score comprovació | CO₂ % | Cost % | Infraccions | Runtime val. s |
|---|---:|---:|---:|---:|---:|---:|---:|
| A · port ingenu 3 h | 2,06 | 0,00 | 11,14 | −2,66 | 6,10 | 0 | 6,46 |
| B · heurística solar | 5,67 | 11,77 | 10,08 | 10,66 | 14,35 | 0 | 3,30 |
| C · MPC 3 h + valor terminal | 10,29 | 18,27 | 17,31 | 16,11 | 23,30 | 0 | 6,57 |
| **D · MPC 24 h causal anual** | **12,65** | **21,19** | **21,04** | **19,19** | **25,85** | **0** | **7,52** |
| E · MPC de 3 escenaris | 12,35 | 21,02 | 21,58 | 19,69 | 24,11 | 0 | 7,03 |

E guanya en comprovació, però D ja havia estat seleccionada amb validació. No s'ha canviat la decisió a posteriori. Aquesta diferència suggereix incertesa estacional i justifica conservar E com a alternativa experimental, no afirmar superioritat universal de D.

Scores mensuals de D dins dels episodis separats: març 19,69; abril 20,74; maig 23,12; juny 17,74; juliol 16,27; agost 36,63. Tots amb zero infraccions; agost és parcial. Els mesos del full continu difereixen perquè el SOC heretat és diferent.

Resultat full real de la baseline A: **4,14**, CO₂ 2,66%, cost 7,60%, zero infraccions i fallades, procés complet 15,06 s. Resultat del **ZIP D aïllat**, 5.993 passos: **16,86**, CO₂ **15,51%** (72.600,0 kg), cost **20,00%** (153.279,95 €), zero infraccions/fallades; procés complet **16,46 s**, simulació 14,46 s. No són scores de leaderboard. El hash de totes les accions és idèntic entre font i ZIP: `a88ce6b3de14ea719e360ec343576b757607cc83b235ec17f56f4c2ba46b4081`.

Abans del checkpoint s'ha corregit l'escriptura de JSON a LF explícit per evitar que Git canviés els bytes congelats a Windows. S'han repetit les 19 execucions del protocol: mateixos hashes d'accions, scores exactes i selecció que abans del canvi de format. No s'han canviat models ni hiperparàmetres després de veure comprovació. Els temps de la taula i el ZIP són els de la repetició final.

## Energia i oportunitats perdudes

La solar ×12 produeix 1.905.941,39 kWh; crea **541 hores** amb demanda neta negativa i **194.132,22 kWh** d'excedent base. El pic fotovoltaic és 1.728,77 kW. Això invalida el supòsit Standard que la descàrrega sempre redueix importació útil.

| Full de 5.993 hores | Port ingenu A | Candidata D |
|---|---:|---:|
| Excedent carregat a bateria, kWh AC | 64.924,54 | **171.304,10** |
| Exportació total sense remuneració, kWh | 769.498,35 | **94.827,00** |
| Descàrrega de bateria que acaba exportada, kWh | 640.290,67 | **71.998,87** |
| PV aprofitada al campus o carregada, kWh AC | 1.776.733,71 | **1.883.113,26** |
| Hores de SOC aproximadament buit | 0 | 1.049 |
| Hores de SOC aproximadament ple | 442 | 1.055 |

D captura el **88,24%** de l'excedent base; resten errors de demanda/solar que causen exportació de bateria. No tot l'excedent capturat es converteix en servei útil: hi ha pèrdues i possibles exportacions posteriors. PV aprofitada = `min(PV,load) + min(max(action,0),max(PV-load,0))`; no es calcula com PV menys exportació total perquè aquesta també pot incloure bateria. Buit/ple es defineixen com SOC posterior al pas <0,01 kWh / >5.999,99 kWh. SOC final D: 2.048,77 kWh.

Les traces locals `artifacts/oriol_hard_mode/trace_*.csv` contenen timestamp, SOC, acció, importació i exportació. No entren al ZIP ni es versionen. Les mètriques agregades, hashes de dades i mesos sí queden a `results.json`.

## Estratègia matemàtica i forecast

Per a cada hora, `n_hat=load_hat-pv_hat`, `P=c-d` i `G=max(n_hat+c-d,0)`. El LP minimitza

`sum_t G_t*(0.7*carbon_t/mu_carbon + 0.3*price_t/mu_price) + 1e-8*sum_t(c_t+d_t)`

subjecte a `E_next=E+sqrt(0.9)*c-d/sqrt(0.9)`, `0<=E<=capacity`, `0<=c,d<=power`. D fixa SOC terminal al 50% amb 3 valors de mercat disponibles, i allibera el terminal quan el vector s'escurça al final real de l'episodi. `mu_carbon` i `mu_price` són mitjanes ponderades per importació **només del calibratge**, aproximacions de les bases percentuals futures desconegudes. No s'usen normalitzadors del període que s'està avaluant.

El model no recompensa exportar; `G>=0` representa correctament l'excedent gratuït. El petit cost de throughput elimina cicles degenerats; es rebutja qualsevol solució amb càrrega i descàrrega simultànies. HiGHS s'executa a cada pas de D, amb límit de 0,5 s per LP i fallback solar si falla. El clamp final usa exactament `sqrt(0.9)` i `eps=1e-4` i respecta els límits dinàmics d'obs; defaults Hard 6.000/1.500 exclusius d'aquest laboratori.

A assumeix demanda constant 1.500 kW i reserva terminal 50% en un horitzó de només 3 hores. B prioritza excedent, buida espai abans de solar prevista i arbitra amb reserva senzilla. C resol únicament les 3 hores conegudes amb valor terminal `0.9*eta*mean(value_hat[3:])`, predit causalment. E combina escenaris equiprobables `(load×1.10, PV×0.65)`, central i `(load×0.90, PV×1.35)`; comparteix **les dues primeres decisions** entre escenaris i replanifica cada dues hores. No és una garantia worst-case ni un arbre estocàstic complet.

Respecte al MPC Standard, D necessita preveure demanda/PV, mantenir espai per captar excedent i predir mercat desconegut. Les hores 0,1,2 de preu/CO₂ es copien de l'observació; les hores 3..23 són perfils setmanals de calibratge amb correcció dels tres valors coneguts, que decau en 6 hores. La demanda usa perfil setmanal i residual t−1 suavitzat/limitat. La PV anual ajusta per hora `a+b*sin(2*pi*doy/365.25)+c*cos(...)`, amb ridge, i correcció de ràtio PV t−1 que decau. Cap CSV, xarxa ni entrenament s'executa dins de l'agent.

En calibratge, el MPC 24 h amb perfil fix dona 10,34; afegir correcció causal dona 12,61; el model solar anual dona 12,65. És una ablation **de calibratge**. La millora 21,19−18,27 en validació compara horitzó i terminal diferents, i no s'atribueix íntegrament al forecast.

Diagnòstic posterior a la selecció, sense modificar paràmetres:

| MAE de previsió de t, kW | Perfil fix val. | Adaptatiu val. | Anual val. | Anual comprov. |
|---|---:|---:|---:|---:|
| Demanda | 82,43 | 38,51 | 38,51 | 97,79 |
| Solar Hard ja ×12 | 204,12 | 101,56 | 71,35 | 78,09 |

El MAE del mercat desconegut a hores cronològiques 3..23 de l'anual és 0,02923 €/kWh i 0,02040 kg/kWh en validació, i 0,04485 / 0,03365 en comprovació. Els targets entren només al diagnòstic d'errors després de produir el forecast; no retornen a l'agent. `forecast_diagnostics.json` registra les quantitats i RMSE. La meteorologia anunciada no s'ha pogut avaluar perquè no existeix a obs del kit.

## ZIP, proves i límits

ZIP local: `artifacts/oriol_hard_mode/hard_candidate_submission.zip`, **11.712 bytes**, SHA-256 **`00c48bfc277f3eb6c7b1719c9d6cc82fdadfe3ed173ae24fc642c1620ff56210`**.

Conté 8 entrades: `agent.py`, `candidate_config.json`, `training.json`, dos `__init__.py` i `safety.py`, `forecast.py`, `policies.py` del paquet Hard. S'han recorregut els imports estàtics per assegurar totes les dependències locals. Només requereix numpy/scipy i biblioteca estàndard en inferència. No conté dades horàries, models dels companys, entorns, claus, traces ni eines de subprocessos. Python local 3.11.9; numpy 2.4.1; pandas 2.3.3 per simulació; scipy 1.17.0.

Proves executades: **19 Hard + 11 estables, totes superades**. Inclouen SOC extrems i 1.000 estats aleatoris, límits dinàmics, sortides finites, cicle solar físic independent, gaps, longituds 0..3, mercat ocult contaminat, ignorar telemetria inicial, correcció PV sense doble escala, hooks externs amb fallback i bytes LF dels JSON. El ZIP passa l'AST i els 24 passos del **checker oficial local genèric**, i el harness Hard complet aïllat. Tots els mòduls locals es resolen dins de l'extracció del ZIP; accions reproduïdes exactament. El checker genèric no certifica les 48 hores del servidor Hard.

La [web oficial](https://repteupc.datathon.cat/) publica límits generals de **60 s i 25 MB**, i la pestanya Hard no mostra cap excepció específica. El widget mostra un límit genèric superior de pujada; no substitueix el límit publicat del repte. El ZIP i els 16,46 s locals queden per sota dels límits generals, amb criteri local <45 s. **L'acceptació i el temps en servidor Hard continuen pendents del seu dry-run**, especialment per disponibilitat de scipy i velocitat de l'entorn remot.

Riscos: observació meteorològica no reproduïda, extrapolació estacional entrenada només setembre–febrer, deriva de demanda a l'estiu, futurs de mercat imperfectes i salts del dataset. Cap evidència permet extrapolar 21,19 al test ocult. Cal mantenir la baseline i estudiar E en nous blocs acordats abans de canviar la selecció.

## Reproducció des de l'arrel, PowerShell

```powershell
# Python comprovat: no usar els àlies WindowsApps que no funcionen aquí.
& ./.venv/Scripts/python.exe --version
# Si cal un entorn nou: Python 3.11 real, python -m venv .venv;
# després instal·lar les versions de requirements.txt del laboratori.
& ./.venv/Scripts/python.exe -m pip install -r experiments/oriol_hard_mode/requirements.txt
& ./.venv/Scripts/python.exe -B -X utf8 experiments/oriol_hard_mode/lab.py audit
& ./.venv/Scripts/python.exe -B -X utf8 experiments/oriol_hard_mode/lab.py baseline
& ./.venv/Scripts/python.exe -B -X utf8 experiments/oriol_hard_mode/lab.py calibrate
& ./.venv/Scripts/python.exe -B -X utf8 experiments/oriol_hard_mode/lab.py validate
& ./.venv/Scripts/python.exe -B -X utf8 experiments/oriol_hard_mode/lab.py confirm
& ./.venv/Scripts/python.exe -B -X utf8 -m unittest discover -s experiments/oriol_hard_mode -p test_*.py -v
& ./.venv/Scripts/python.exe -B -X utf8 -m unittest discover -s tests -p test_*.py -v
& ./.venv/Scripts/python.exe -B -X utf8 experiments/oriol_hard_mode/diagnostics.py
& ./.venv/Scripts/python.exe -B -X utf8 -c "from experiments.oriol_hard_mode.lab import execute; execute('mpc24_annual','full')"
& ./.venv/Scripts/python.exe -B -X utf8 experiments/oriol_hard_mode/deliver.py build
& ./.venv/Scripts/python.exe -B -X utf8 experiments/oriol_hard_mode/deliver.py benchmark
Get-FileHash artifacts/oriol_hard_mode/hard_candidate_submission.zip -Algorithm SHA256
```

No cal reinstal·lar dependències si ja hi ha l'entorn comprovat. `training.json` està congelat i només conté perfils agregats; `calibrate` el regenera des del train autoritzat. Si canvien fonts/protocol, cal repetir calibratge i validació, i acordar nous blocs si ja s'ha examinat comprovació. El runtime pot variar amb la màquina. Manifest i logs del checker: mateix directori d'artifacts, sufixos `.manifest.json` i `.checker.txt`.

## Integració amb Cesc i Dani

Després de `git fetch origin`, Cesc continua a `acc09c06b30d9dcf78f38c88e9c554b2c2f8f57c`: `NetLoadForecaster` Standard retorna demanda **neta Standard**, no demanda bruta i PV Hard separades. Dani continua a `1bb02e1fd026f98399aba6da716f1be7cca991aa`, sense `src/policy.py`/`src/mpc.py` publicats. No s'ha modificat ni importat cap dels seus fitxers.

Hooks d'integració explícits i opcionals de `HardAgent` i `BatteryAgent`:

```python
forecast_provider(obs, horizon=24) -> {"load_kw": array24, "pv_kw": array24}
policy(obs, forecasts=forecasts) -> float
BatteryAgent(forecast_provider=forecast_provider, policy=policy)
```

Cesc: arrays de kW bruts de demanda i PV **ja Hard ×12**, ordre cronològic `t..t+23h`; només timestamp, mercat conegut i telemetria t−1. No fer ×12 dins del callback. El wrapper valida mida, finitud i signe; manté internament el mercat i els seus tres valors coneguts. Un adaptador d'un forecast net s'haurà de validar com a contracte diferent; no connectar el model Standard directament. La meteorologia futura real no és una entrada disponible.

Dani: acció AC amb signe positiu per carregar, negativa per descarregar; `forecasts` inclou demanda, PV, preu i CO₂, amb `known_market_hours` explícit. Respectar importació truncada a zero, SOC i terminal; el clamp final és obligatori i independent. Un error o sortida no finita de política externa activa reserva solar i incrementa el comptador visible `policy_failures`. Si no hi ha callbacks, funciona l'MPC propi. Per incorporar-los al ZIP cal declarar els nous imports locals, reempaquetar i repetir checker/harness; no copiar carpetes senceres.

## Validació Ràpida Hard de 48 hores, pendent

1. Comprovar el SHA-256 del ZIP Hard anterior, separat del ZIP Standard de 6,43.
2. Obrir [repteupc.datathon.cat](https://repteupc.datathon.cat/) i seleccionar **🔥 Mode Difícil**.
3. A **🧪 Validació Ràpida Mode Difícil (Sense gastar quota)**, seleccionar el ZIP Hard. Executar únicament el control de validació ràpida d'aquesta secció. No entrar a **🔥 Trametre al Rànquing Mode Difícil**.
4. Comprovar que es reconeix `BatteryAgent`, que els 48 passos acaben, les sortides són finites i no hi ha infraccions, errors d'importació o timeout. Registrar el text exacte, runtime, data/hora, mode i SHA local del fitxer pujat. La validació curta no garanteix el runtime de tot el test ocult.
5. Si falla, conservar el missatge i corregir/revalidar localment. No transformar la prova en una tramesa al leaderboard. Qualsevol tramesa oficial requereix consentiment de l'Oriol i l'acord d'equip.

S'han observat aquests noms i la indicació de validació sense quota a la web; no s'ha premut cap control de pujada ni execució. No es publiquen PIN ni credencials.
