# Pla operatiu — UPC Sostenible + Side Challenge Tukey

**Data:** 14/11/2026  
**Estat:** proposta per a La MasIA; abans de començar el desenvolupament coordinat cal que els quatre accepteu oficialment UPC Sostenible com a repte principal.  
**Fonts verificades:** [plataforma oficial](https://repteupc.datathon.cat/), ZIP oficial descarregat per l'equip (`starter_kit/environment.py`, `check_submission.py`, dades i tutorial), i PDF «SideChallenge_TukeyFME2026.pptx.pdf» (3 pàgines).

## 0. Decisions immediates (reunió de 10–15 minuts)

- [ ] Confirmar **UPC Sostenible** com a repte principal després de comparar els enunciats dels altres dos.
- [ ] Designar un únic integrador i responsable de tramesa al leaderboard.
- [ ] Confirmar el format i el termini del **Premi Tukey** amb l'organització: com es presenta, quan, demo o enllaç, i si es pot compartir un dashboard només local.
- [ ] Preguntar al mentor les contradiccions: penalització 0,20 vs 1,00, excedents 0 vs 0,04 €/kWh i continuïtat temporal del test.
- [ ] Acordar els responsables reals, branques i fitxers; les assignacions següents són **una proposta**.

**Regla de coordinació:** 1 branca + 1 responsable per tasca; només l'integrador fusiona després de revisió. No permetre que dos agents de codi modifiquin simultàniament la mateixa carpeta i branca.

## 1. Entrega i restriccions — font de veritat

- `agent.py` exposa `class BatteryAgent`, `__init__` i `act(obs: dict) -> float`.
- Signes: (P>0) càrrega, (P<0) descàrrega; límits ±500 kW, energia entre 0 i 2.000 kWh.
- Bateria al 50% al principi; eficiència de cicle del 90%. `soc` no es reinicia en canvis de dia.
- Objectiu: **70% reducció percentual de CO₂, 30% estalvi percentual de cost** comparat amb no tenir bateria.
- Observacions: `timestamp`, `hour`, `day_of_week`, `soc_kwh`, `soc_pct`, `preu_actual`, `co2_actual`, `preus_properes_24h`, `co2_properes_24h`, `noves_dades_5min` amb consum/solar de l'hora anterior.
- En cada hora es decideix amb la informació **ja observada**: ni demanda real del futur, ni CO₂/consum del test ocult.
- El simulador local retorna `max(0, 100*(0.7*dCO2 + 0.3*dCost - 0.002*infraccions))`; **0,20 punts per infracció** al codi. Altres documents diuen 1,00: evitar-les completament.
- El simulador local fa `export_price = 0.0`: no és beneficiós descarregar per exportar.
- Web: **10 trameses oficials per equip/dia**, dry-run de **48 hores gratuït i il·limitat**, test privat/públic 50/50, límit del procés **60 s**, màxim **25 MB**.
- Llibreries autoritzades: Python estàndard, NumPy, pandas, SciPy, sklearn, joblib, XGBoost i LightGBM. El servidor bloqueja APIs de xarxa, `os`, `sys`, subprocessos i execució dinàmica.
- No incloure el PIN de tramesa ni secrets a Git, prompts ni capturas.
- Si s'entrenen models: un `submission.zip` amb `agent.py` i `.pkl` a **l'arrel** del ZIP. Rutes relatives a `__file__`.

**Observació important:** el fitxer local `environment.py` fa que les 24 previsions siguin les properes 24 **files** de dades. Si l'índex té salts de setmanes, poden travessar-los. Verificar si el servidor funciona exactament així i evitar suposar continuïtat temporal per als lags.

## 2. Pla tècnic per maximitzar resultats (en aquest ordre)

### Fase A — Fonaments fiables
1. Clonar el ZIP al directori de treball local; **no** publicar datasets reals ni credencials.
2. Unificar comptador (inversió del signe), tres inversors, PVPC i CO₂ a **1 hora**. Confirmar nombre de files, zona horària, duplicats, valors faltants i salts.
3. Reproduir la referència oficial + `agent=0` i el prototip de política de llindars que ja hem validat localment.
4. Crear proves automàtiques de totes les combinacions extremes de SOC 0/2000, potències ±500, valors faltants, salts temporals i vector de futur curt.
5. **Safety clamp obligatori** amb `eta=sqrt(0.9)` i marge mínim:
   - `max_charge = max(0, min(500, (2000 - soc)/eta - eps))`
   - `max_discharge = max(0, min(500, soc*eta - eps))`
6. Criteris de sortida: passa el validador local, zero infraccions, score reproduïble, runtime mesurat i PR revisat.

### Fase B — Política heurística que puntua
1. Utilitzar vectors 24h que contenen **preu i CO₂ futurs reals segons la simulació**.
2. Construir un valor combinat normalitzat per les bases respectives de CO₂ i cost. **No confondre** pesos interns de política amb el 70/30 del Score oficial.
3. Condició d'arbitratge: comparar horaris favorables vs desfavorables, tenint en compte el 10% de pèrdua d'energia del cicle.
4. Afegir una reserva/tancament de SOC per no quedar buit abans d'un pic de CO₂.
5. Avaluar per mesos, setmanes, franges horàries i percentils; enregistrar experiments amb commit, paràmetres i mètriques.
6. **No consumir trameses oficials** sense la comparació interna i el vistiplau del responsable.

### Fase C — MPC (optimització rolling horizon)
1. Provar primer un programa lineal petit per a **24 hores**, maximitzant l'estalvi ponderat previst, amb variables de càrrega/descàrrega i SOC, eficiència i límits.
2. La ponderació marginal teòrica, si no hi ha exportació ni preus negatius, és proporcional a `0.7 * co2_t / CO2_baseline_total + 0.3 * price_t / cost_baseline_total`. Cal comprovar l'escala al simulador.
3. Estimar la demanda neta futura per no planificar descàrregues per sobre del consum (exportació sense ingressos). Primer baseline estacional i després ML només si millora.
4. Utilitzar `scipy.optimize.linprog(method="highs")` **només si s'accepta i el benchmark global passa els 60 s**. Si és massa lent, limitar reoptimitzacions o optar per heurística.
5. Penalitzar o valorar el SOC final de l'horitzó per evitar que un MPC curt buidi la bateria artificialment.
6. Fer **ablation**: heurística vs MPC sense ML vs MPC amb pronòstic de demanda/solar.

### Fase D — Generalització i robustesa
1. Separar blocs sencers de temps dins el train per validar, no fer `train_test_split` aleatori d'hores.
2. No tornar a triar paràmetres pel millor resultat del leaderboard públic; el 50% privat és invisible.
3. Comprovar què passa si falten observacions de novembre, entre setmanes amb salts, amb efecte de SOC persistent, i quan hi ha tarifes o CO₂ extremadament baixos.
4. Comparar score, estalvi de CO₂, estalvi €, infraccions, latència i estabilitat per mes.
5. Conservar una versió **estable i validada** que es pugui entregar si qualsevol experiment avançat falla.

## 3. Rols i branques proposats

| Responsable | Àrea | Branca | Fitxers propis suggerits | Condició d'acabat |
|---|---|---|---|---|
| **Oriol** | Integració, validador, Safety Clamp, trameses | `feat/oriol-integration` | `src/safety.py`, `tests/`, `agent.py` (només integrador) | Zero infraccions i validació web |
| **Cesc** | EDA, predicció demanda/solar i dades | `feat/cesc-forecast` | `src/forecast.py`, `analysis/`, `reports/forecast*` | Forecast temporal comparat amb estacional |
| **Dani** | Optimització heurística / MPC | `feat/dani-optimizer` | `src/policy.py`, `src/mpc.py` | Millora documentada del score/latència |
| **David** | Premi Tukey, dashboard i narrativa de demo | `feat/david-tukey` | `dashboard/`, `reports/`, `presentation/` | Dashboard útil, coherent i executable |

**Interfícies acordades abans de programar**:
- Integrador manté `agent.py` i exporta `BatteryAgent.act(obs)->float`.
- Predicció ofereix `forecast_net_load(obs, horizon=24) -> list[float]` sense fugues temporals.
- Optimitzador ofereix `choose_action(obs, load_forecast=None) -> float`.
- Simulador/exportador de resultats escriu **agregats verificables** a `reports/metrics.json` i sèries per al dashboard; no arxius de dades brutes a repositori.
- Dashboard **no modifica** la política; només consumeix resultats validats i etiqueta clarament `train / holdout / públic`.

La proposta es pot canviar amb acord dels quatre; no hi ha responsabilitats assignades automàticament.

## 4. Side Challenge Tukey — premi de visualització

**PDF oficial, pàgines 2–3:** crear un dashboard vinculat al repte principal; **eina lliure** (Power BI, Shiny, Tableau, web...). Se selecciona **un finalista per cadascun dels tres reptes** i el premi global és per a un dels tres.

**Criteris oficials**: 1) utilitat per prendre decisions, 2) adequació dels gràfics, 3) coherència dels indicadors/resultats.

### Concepte recomanat: «La MasIA · Battery Decision Lab»

Fes que el jurat pugui respondre, interactuant amb el dashboard:
1. **Quan i per què carrega o descarrega?** Perfil horari SOC, consigna, preu i CO₂ (eixos ben etiquetats).
2. **Quant millora realment?** Targetes de Score, % emissions, % cost i nombre d'infraccions; comparar vs `standby` i vs baseline oficial corregida.
3. **En quin moment funciona pitjor?** Distribució per mes/setmana i boxplots de l'impacte (Tukey), amb outliers i interpretació.
4. **Quin trade-off hi ha?** Gràfic de dispersió Cost% vs CO₂%, un punt per política amb color i identificador de model; marcar frontera de Pareto si té sentit.
5. **És robust?** Comparativa d'avaluació temporal per mesos, no només un score total; filtres per dia, hora, política i període.
6. **Quina decisió recomanem?** Conclusió curta generada a partir de mètriques calculades realment, no de text decoratiu.

### Implementació
- Recomanat: **Streamlit + Plotly** (ràpid per al David amb Claude Code), o una app HTML/JS auto-contenida si cal mostrar-la sense dependències de servidor. L'eina del Tukey no té les restriccions d'execució d'`agent.py`: és un projecte **separat**.
- Gràfics: línies de SOC, barres de càrrega/descàrrega, dispersió CO₂ vs cost, boxplot de millores setmanals; no sobrecarregar amb 12 gràfics poc útils.
- Usar dades resumides de resultats de simulacions reproduïbles; no publicar telemetries crues de la UPC sense confirmar-ne llicència/permís.
- Fer coincidir tots els KPI amb el càlcul de `environment.py` i explicar base, units i finestra temporal.
- Preparar captura i vídeo de reserva + guia curta per executar-lo.

**Decisió pràctica:** el Premi Tukey mereix un flux propi però no sacrificar el repte principal; iniciar maquetació només després d'obtenir una baseline fiable. El David pot tenir suport del Cesc amb gràfics d'EDA.

## 5. Eines d'IA sense trepitjar-vos

- **Oriol + Cesc:** Codex App en branques diferents.
- **Dani + David:** Claude Code, igualment en branques diferents.
- **OpenCode + HelmCode:** revisor alternatiu o assistent d'alguna tasca independent, mai una cinquena IA editant les mateixes carpetes simultàniament.
- Tot prompt de codi ha d'explicitar **branca, issue, fitxers propis, inputs/outputs, criteris d'èxit i tests**.
- No publicar PIN, tokens ni dades protegides; no incloure crides a APIs d'IA dins l'agent sotmès a l'avaluador.

## 6. Checkpoints recomanats (relatius al moment de decisió)

| Moment | Fita verificable |
|---|---|
| T+0:15 h | Repte confirmat, rols acceptats, branques creades, dades localitzades |
| T+1 h | Starter Kit reproduït, referència i agent estable sense infraccions |
| T+3 h | Heurística millorada, primera validació temporal i primer dry-run web |
| T+5 h | MPC mínim benchmarked i dashboard Tukey estructurat amb dades reals |
| T+8 h | Comparativa de totes les polítiques, error analysis i tria de candidata |
| Abans del límit de tramesa | Freeze, validació de ZIP, submissió oficial i captura del rebut |
| Abans de demos | Dashboard Tukey funcional, història de 3 minuts, prova i backup |

**El temps T és relatiu**: reorganitzar segons l'hora real de l'inici, terminis confirmats i descans. No pressuposeu que la referència de les 12:00 de diumenge és necessàriament el tall exacte de l'API sense confirmar-ho.

## 7. Proves ja realitzades (només entrenament!)

Inspecció del paquet i scripts locals, anotada a [UPC_STARTER_TESTS.md](UPC_STARTER_TESTS.md):
- `BatteryAgent` oficial sense corregir: score **0,00**, 46 infraccions.
- Referència amb clamp físic exacte: score **1,27**, zero infraccions.
- Prototip de llindars 24h: score **4,26**, estalvi CO₂ **3,86%**, cost **5,18%**, zero infraccions sobre **5.993 hores** de train.
- Reconfirmat l'èxit del `check_submission.py` sobre el prototip amb 24 casos: imports, AST, signatura i execució OK.

**No són resultats del test ocult ni del leaderboard**. La configuració 4,26 es va seleccionar entre alternatives provades sobre el mateix train, i cal validar generalització. No anunciar-la com a score oficial.

## 8. Què preguntar als mentors avui

1. Penalització: les diapositives diuen **−1,00**, la web i `environment.py` indiquen **−0,20**. Quina és definitiva?
2. Exportació: FAQ i engine indiquen **0 €**, però un paràgraf de la web diu **0,04 €/kWh**. Quin valor s'utilitza al test?
3. Els vectors de 24h al test ocult poden **saltar setmanes** com al simulador local?
4. El temps límit de 60s és **global de totes les 2.016 hores** i quin hardware del servidor s'utilitza?
5. El portal admet desar com a fitxers auxiliars taules `json` a banda de `.pkl`?
6. Side Challenge Tukey: quin **termini**, procediment de **presentació** i criteri de **lliurament**, i es poden mostrar gràfics amb dades agregades del campus?
7. Es poden compartir traces agregades de les dades reals fora del GitHub privat, per a demo o presentació?

## 9. Regles per decidir si una millora entra a la versió final

**Només fusionar a `main`** si:
- No hi ha infraccions en cap prova de SOC extrem ni a les simulacions completes.
- No hi ha APIs prohibides ni dependències no autoritzades.
- Runtime de tota la simulació amb marge respecte al timeout.
- Supera l'agent estable en validació temporal (o documenta el trade-off si guanya en emissions però perd en cost).
- Inclou proves, paràmetres fixats, mètriques i nota de limitacions.
- La versió de `main` és reproduïble des de zero, sense dades privades al repositori.

**No escolliu models pel nombre de vegades que pugen al leaderboard.** El 50% privat és l'avaluació decisiva per detectar overfitting.
