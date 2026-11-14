# Auditoria exhaustiva del planning — UPC Sostenible + Premi Tukey

**Data:** 14 de novembre de 2026. **Estat:** auditat; proposta, no selecció oficial confirmada.  
**Abast:** compatibilitat de `BatteryAgent`, simulació, dades, metodologia, optimització, temps d'execució, empaquetament, GitHub, agents d'IA, Side Challenge Tukey i entrega.

**Fonts verificades:**
- Plataforma oficial: https://repteupc.datathon.cat/ , incloses bases, FAQ, normativa, validador i lliurament.
- ZIP oficial `paquet_participants_datathon_upc.zip`: `docs/ENUNCIAT.md`, `docs/GUIA_VARIABLES.md`, `starter_kit/environment.py`, `starter_kit/check_submission.py`, `starter_kit/agent.py`, `starter_kit/tutorial.ipynb`, `starter_kit/battery_spec.json` i dades reals d'entrenament.
- Side Challenge Tukey, diapositives oficials de 3 pàgines i missatge #tukey-commission del 14/11.
- Documents anteriors del repo: `docs/PLA_UPC_TUKEY.md` i `docs/UPC_STARTER_TESTS.md`.

## 1. Veredicte executiu

**És viable competir fort amb UPC Sostenible i presentar Tukey en paral·lel, condicionat a confirmar el repte amb els quatre.** No és viable fer simultàniament un gran model ML, un MPC complex, una interfície de producció, múltiples cadenes d'agents i experiments poc controlats. El recurs escàs és el temps abans de l'entrega.

**Ordre de prioritat:** (P0) agent correcte + cap infracció + entregable + tests; (P1) heurística 24h robusta i validació temporal; (P2) MPC lleuger i forecasting només si milloren; (P3) Dashboard Tukey amb mètriques reals i conclusió útil; (P4) polir presentació. Tukey pot començar quan existeixen resultats de la baseline, sense esperar el millor agent.

## 2. Contracte oficial: requisits i riscos

| Prioritat | Restricció / fet | Avaluació de viabilitat | Acció |
|---|---|---|---|
| P0 | `BatteryAgent.act(obs)->float`; `agent.py` obligatori | Baixa complexitat | Contract test i validador |
| P0 | SOC de 0 a 2.000 kWh, potència ±500 kW, rendiment 90%, SOC inicial 1.000 kWh | Viable | Safety clamp central |
| P0 | Score 70% CO₂ / 30% cost percentual vs sense bateria | Viable | Comparar en mètrica oficial, no només euros |
| P0 | 10 entregues leaderboard/dia, 50% test públic / 50% privat | Risc alt d'overfit | Reserveu intents, registre i decisió única de submissió |
| P0 | 60 s per **simulació completa** al servidor, ZIP max 25 MB | Risc mitjà amb MPC | Benchmark de tota la simulació amb marge |
| P0 | Sense xarxa/subprocessos/importacions prohibides al `agent.py` | Viable | AST + dry-run del ZIP |
| P0 | Importar mòduls auxiliars exigeix ZIP complet (agent.py a l'arrel) | Viable: verificat amb test local | Empaquetador propi |
| P1 | L'agent veu preu/CO₂ actual i llistes de 24h, NO demanda ni solar futures | Risc metodològic | Forecast causal; cap fuga temporal |
| P1 | El test separa setmanes mensuals i el SOC persisteix entre passos | Viable amb gestió d'estat | Detectar salts de timestamp |
| P1 | El jurat revisa explicació i presentació, no només leaderboard | Fortalesa | Resultats auditables, gràfics i limitacions |
| P2 | Premi Tukey: dashboard vinculat al repte, eina lliure, tres finalistes i un premi | Viable si no frena la missió | David en branca independent |

**Contradiccions del material oficial**:
- Document `ENUNCIAT.md` i diapositives: penalització **−1,00 punt**; el codi local `environment.py` i la fórmula de la web: **−0,20 punt**. Només el servidor final/mentor pot resoldre-ho; mantenir **0 infraccions**.
- A un apartat de la web s'esmenten exportacions a **0,04 €/kWh**, però la FAQ, `ENUNCIAT.md` i `environment.py` indiquen **0,00**. L'agent no ha de descarregar amb l'única finalitat d'exportar.
- La web/ENUNCIAT parlen de **2.016 h de test**, mentre que les diapositives indiquen ~1.700 h. L'avaluador real preval; no fer supòsits de longitud fixa.
- El `README.md` del ZIP enumera `app.py`, `scripts/`, `requirements.txt` i `data/test_hidden/`, però **aquests fitxers/directoris no estan inclosos al ZIP real**. No els considereu recursos disponibles.
- El `check_submission.py` descriu una simulació sintètica de **24 passos**, i el botó web fa **48 hores** de dry-run: NO són comprovacions de puntuació ni del test privat.

## 3. Dades: auditoria real

Els CSVs contenen aproximadament:
- `contador.csv`: 74.210 registres; `inversor.csv`: 71.882; `precio_pvpc.csv` i `co2_red.csv`: 6.768 cadascun.
- Unió horària amb el preprocessament del **tutorial oficial**: **5.993 hores**, de setembre 2025 a agost 2026.
- **Falta novembre 2025** a la unió de dades, i l'agost acaba el dia 16 per a la font solar; hi ha diversos salts de ~169 h entre blocs mensuals, un de **889 h**, i alguns salts menors.
- Càrrega mitjana de ~1.123 kW i PV mitjana de ~26,5 kW. Menys del 0,52% de les hores tenen demanda neta inferior a 500 kW; **no suposeu que el test tingui la mateixa distribució**.
- El simulador usa `iloc[t:t+24]` per als vectors futurs de preu i CO₂, **inclou l'hora actual** i, quan hi ha buits temporals, pot incloure hores de la següent setmana/mes. Això obliga a gestionar l'horitzó amb cura.
- `noves_dades_5min` dona la demanda i solar de la **fila anterior**; en un salt de setmana aquesta dada queda temporalment obsoleta. Usar `timestamp` per no tractar-la com l'hora immediatament precedent.
- Verificar el sentit físic del comptador: el tutorial diu `load_kw=-contador` i després resta solar al balanç. Si el comptador mesurés importació ja neta de solar, hi hauria possible doble comptatge; **seguir el simulador oficial però preguntar als mentors**, sense modificar unilateralment el preprocessing.
- Els valors d'entrenament provenen d'un conjunt de dades reals, segons l'organització; **no consta permís explícit per publicar dades brutes**, així que millor mantenir-les fora de GitHub públic i compartir només resultats autoritzats.

## 4. Auditoria de la baseline i del prototip

Repetides proves locals seqüencials sobre les 5.993 hores d'entrenament amb el `CampusBatteryEnv` oficial:

| Política | Score | CO₂ estalviat | Cost estalviat | Infraccions |
|---|---:|---:|---:|---:|
| Standby | 0,00 | 0,00% | 0,00% | 0 |
| Heurística oficial sense corregir | 0,00 | 0,88% | 2,18% | 46 |
| Heurística oficial amb clamp exacte | 1,27 | 0,88% | 2,18% | 0 |
| Prototip de la MasIA, llindars 24h | **4,26** | **3,86%** | **5,18%** | **0** |

El 4,26 prové d'haver comparat diverses configuracions sobre el mateix **train**; no és un resultat de generalització. En desglossar-lo per mesos, el prototip oscil·la entre **1,99 (desembre 2025)** i **8,11 (agost 2026 parcial)**; supera la referència corregida en tots els mesos disponibles, però això tampoc és un holdout independent.

**Proves extra d'aquesta auditoria:**
- **10.009 estats sintètics/aleatoris** amb SOC extrems i llistes de longitud 1–24: totes les accions del prototip són finites i respecten els límits físics calculats.
- Empaquetament de prova `submission.zip` amb `agent.py` i `src/policy.py`: **aprovat pel validador local de 24 passos**. Això confirma el suport **local** a mòduls auxiliars; provar igualment el **dry-run web** final.
- Benchmark exploratori SciPy `linprog(method="highs")` de 24h, **150 optimitzacions sintètiques** en un ordinador de treball: ~**1,5 ms/LP**, extrapolació optimista ~**3,0 s per 2.016 decisions**. **NO equival** al MPC integrat ni al servidor (falten càrrega del model, forecast, restriccions reals, import i entorn del servidor). Mostra que val la pena provar MPC, **no que estigui validat**.

## 5. Què corregiria al planning inicial

### P0 — Abans de repartir desenvolupament
1. Decidir el repte i el responsable final de trameses. Evitar quatre persones experimentant sobre `agent.py` alhora.
2. Afegir una **branca d'integració** o PRs curts: la branca `main` només conté versions que funcionen.
3. Definir un **format de resultats** (`run_id,policy,commit,period,score,co2_pct,cost_pct,infraccions,seconds,train_or_validation`) i una sola funció d'avaluació.
4. Generar un paquet ZIP complet amb estructura igual a la del desplegament, i passar **el validador sobre el ZIP final**, no només `agent.py`.
5. Conservar un **rollback** segur (baseline lliurable) abans d'iniciar MPC.

### P1 — Validació sense autoengany
1. Separar blocs de validació temporal **abans** d'ajustar una nova política. No fer random split de files.
2. Entrenar/optimitzar només en la resta i reportar mètriques per cada bloc, a més del global ponderat per energia real.
3. Si els mesos són inconnexos, controlar la durada i el SOC inicial: no confondre scores mensuals amb simulacions completament independents si l'estat de bateria es conserva.
4. Evitar mirar una vegada i una altra el leaderboard públic. Amb 50% privat, això pot afavorir polítiques fràgils.
5. Mesurar `score, cost, CO₂, infraccions, temps, SOC final, accions 0 / + / -`.

### P2 — Estratègia de millora
1. Mantenir una política de llindars 24h **com a rival obligatori** del MPC. És molt ràpida i ja és millor que la referència local.
2. Millorar llindars i valorització de CO₂/cost tenint en compte que la puntuació és per percentatges de dues bases diferents, no sumes de magnituds.
3. Provar **MPC LP 24h** amb límits SOC intermedis, control de càrrega/descàrrega i una aproximació conservadora de demanda futura. Important: valor del SOC final de l'horitzó (si no, el sistema pot buidar-se imprudentment).
4. Si el MPC no millora en validació o s'acosta al timeout, **descartar-lo** i continuar amb heurístiques.
5. Primer forecast estacional molt simple (hora/dia/mes + telemetria recent vàlida); després LightGBM només si la millora en mètrica final és significativa. L'entrenament se'n fa **fora del servidor**; els models `.pkl` es carreguen a `__init__`.

### P3 — Premi Tukey
- Dashboard vinculat al repte principal, NO projecte separat sense connexió.
- Les tres preguntes centrals: **Quan convé carregar? Quant estalviem? En quines situacions falla o canvia la decisió?**
- 5 visualitzacions útils: SOC i potència horaris; costos/CO₂ baselines vs candidats; boxplot setmanal o mensual; scatter cost% vs CO₂%; error/robustesa per període.
- Mostrar fonts, unitats, denominadors i etiqueta `train / validació / test públic` als gràfics.
- Eina lliure: Streamlit+Plotly o HTML, **separat de `agent.py`**; no necessita executar-se dins del sandbox del repte principal.
- **Pendent:** termini, modalitat i plataforma de lliurament del Tukey. Missatge de Discord no ho especifica.
- No començar amb un dashboard decoratiu fet amb dades fictícies. Primer connectar-lo al resultat del simulador.

## 6. Repartiment recomanat dels quatre, revisat

| Persona (proposta) | Tasca prioritària | Fitxers de treball | Dependència |
|---|---|---|---|
| **Oriol + Codex** | Integració, `agent.py`, safety clamp, tests, packaging, dry-run i trameses | `agent.py`, `src/safety.py`, `tests/`, `scripts/package.py` | Defineix el contracte amb Dani/Cesc |
| **Cesc + Codex** | Qualitat de dades, anàlisi de valor, forecast causal mínim i validació temporal | `analysis/`, `src/forecast.py`, `reports/` | Disponible sense MPC |
| **Dani + Claude Code** | Heurística+MPC LP amb benchmarks i comparació honesta | `src/policy.py`, `src/mpc.py` | Consumeix `forecast_net_load` si realment aporta |
| **David + Claude Code** | Dashboard Tukey, explicacions i pitch del repte principal | `dashboard/`, `presentation/` | Consumeix `reports/metrics.json` verificat |

**Interfícies:** `BatteryAgent.act(obs)->float`, `choose_action(obs,forecast=None)->float`, `forecast_net_load(obs,horizon=24)->list[float]`. Una sola persona toca `agent.py`; els ajudants es poden versionar per separat però **s'han d'incloure al ZIP**.

**Integració**: cada mòdul en branca/PR, un integrador, cap `git push --force`, res de dades privades ni PIN als commits. OpenCode/HelmCode serveix d'**auditor només lectura** mentre altres agents editen.

## 7. Pla de temps pràctic (fites, no hores de rellotge)

1. **Fita 0: 15 minuts** — decidir repte, confirmar mentors i assignacions, crear branques; una persona controla submissions.
2. **Fita 1: 1 hora** — base segura amb score local, zero infraccions, validador del ZIP i `main` neta.
3. **Fita 2: 2–3 hores** — primer holdout temporal, calibratge metodològic, proves d'accions i primers resultats al dashboard.
4. **Fita 3: 3–5 hores** — MPC candidat i forecast mínim, cada millora com a PR reversible, benchmark sota temps.
5. **Fita 4: abans del congelament** — comparar baselines/MPC, triar una sola versió, dry-run web (48h), entrega oficial amb PIN.
6. **Fita 5: abans de la demo** — Tukey coherent i usable, explicació oral, captura/vídeo alternatiu; res de funcionalitats noves a última hora.

**Horari de l'esdeveniment:** el web general diu «últim avís» diumenge 15 a les 12:00 i demos a les 14:00; **no pressuposeu que les 12:00 són el termini de tancament exacte** fins confirmar-ho amb el portal o mentor. Les diapositives no especifiquen el temps de pitch d'UPC; **no extrapolar els 3 minuts del repte Qualcomm**.

## 8. AIMA / ABIA

Els conceptes de models d'estat, espai d'accions, restriccions i funció objectiu són reutilitzables. L'exercici d'ABIA de centrals elèctriques i clients amb capacitat i pèrdues és especialment proper **conceptualment**.

**No integrar `aima` al fitxer de submissió:** no es troba a la llista de dependències autoritzades i els mètodes de cerca en espais discrets (A*, BFS, Hill Climbing, Simulated Annealing) no ofereixen una via més eficient, fiable i ràpida que un problema lineal de control de bateria amb SOC continu. El coneixement sí; la dependència no.

## 9. Condicions per a una entrega guanyadora però robusta

Abans de fer una submissió:
- [ ] Agent importable i compatible amb l'AST del validador.
- [ ] ZIP amb **totes les dependències locals** importades i cap secret.
- [ ] Cap infracció a casos extrems ni en simulació sencera.
- [ ] Zero dades del futur diferents de les explícites a `obs`.
- [ ] Robustesa en salts temporals i en longituds de previsió incompletes.
- [ ] Score superior a la baseline en períodes temporals no usats per triar paràmetres.
- [ ] Temps complet per sota de 60s amb marge i sense excepcions.
- [ ] Test ràpid web superat i control únic de la quota de 10 submissions.
- [ ] Mètriques i gràfics Tukey coherents amb el simulador, sense inventar xifres.
- [ ] Material de presentació i instruccions de reproducibilitat llestes.

## 10. Preguntes pendents als mentors

1. Confirmeu **−0,20 o −1,00** punts per infracció?
2. Quin és el valor efectiu de **remuneració d'excedents** al test?
3. Els vectors `preus_properes_24h` i `co2_properes_24h` poden travessar els salts mensuals? Es considera legítim?
4. Quin CPU/RAM i **timeout global** té el servidor per a MPC?
5. El test ocult conserva realment totes les hores/setmanes mensuals i dades d'última hora, o hi ha mancances?
6. Com i quan s'entrega la **Side Challenge Tukey**? Demo separada? Accés a internet?
7. Quin és el termini exacte de tramesa d'UPC Sostenible, i quant ha de durar la presentació?
8. Es permet presentar gràfics derivats de la telemetria real si el dashboard es publica fora del recinte?
