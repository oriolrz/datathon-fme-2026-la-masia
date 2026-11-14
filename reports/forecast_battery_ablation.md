# Forecast i puntuació de bateria: ablació diagnòstica

Cesc · issue #3 · `feat/cesc-forecast` · 14/11/2026. Experiment local de validació, sense canviar la política oficial ni el codi d'Oriol/Dani.

## Inspecció: la política existent no consumeix forecast

`prototypes/upc/agent_v0_24h.py` només llegeix SOC, preus i CO₂. No llegeix demanda, solar, telemetria ni cap sortida de `forecast_net_load`. Connectar A/B/C/D sense adaptar la regla no pot canviar-ne cap acció. Els scores previs d'aquest prototip no són millores atribuïbles al forecast. Aquest informe distingeix aquesta política de l'adaptador diagnòstic.

El motor oficial decideix primer amb obs i després liquida `load_kw - pv_kw + acció`; no limita la descàrrega per demanda, remunera exportacions a 0 €/kWh i manté el SOC entre files encara que hi hagi salts. Es conserva el preprocessament del tutorial. La guia descriu el comptador al PCC com a importació neta de solar: si aquesta descripció és correcta, definir load_kw=-comptador i restar-hi pv_kw pot produir un doble comptatge PCC/solar. Aquest dubte continua pendent dels mentors; no s'ha alterat el contracte oficial.

## Política experimental única, fixada abans de mesurar

Es conserva capacitat 2000 kWh, potència ±500 kW, eta=sqrt(0,9), threshold=0.2, marge=0.05, pes CO₂ de la heurística=0.5 i clamp amb epsilon=1e−4. El pes heurístic 50/50 es manté igual en totes les alternatives; el score oficial continua sent 70% CO₂ i 30% cost. No s'ha buscat cap altre adaptador ni ajustat llindars segons resultats.

Per a cada horitzó admès, es calcula el mateix valor normalitzat de preu/CO₂ `v[h]` del prototip. Sense forecast s'usa `mean(v)`, exactament com abans. Amb forecast, s'usa `sum(v[h] * max(net_hat[h], 0)) / sum(max(net_hat[h], 0))`; si tots els pesos són zero, es torna a la mitjana uniforme. La resta de les condicions de càrrega/descàrrega no canvia. En descàrrega, el límit addicional és `max(net_hat[0], 0)` kW, abans del mateix clamp físic. Així es consumeixen t i les hores futures del forecast, sense usar labels reals per decidir.

És una heurística diagnòstica de ponderació per demanda, no un MPC ni una política oficial nova. El resultat és condicional a aquesta regla: no mesura la utilitat màxima del forecast per a un optimitzador. Si la demanda prevista és constant (A), la mitjana ponderada equival a la uniforme; només el límit de descàrrega pot tenir efecte addicional.

| Variant | Forecast consumit |
| --- | --- |
| Sense forecast | Pesos uniformes; sense límit addicional per demanda |
| A | Última demanda neta observable, constant; fallback de train al primer pas |
| B | Mediana per hora/dia de setmana entrenada sobre setembre–febrer |
| C | B corregit causalment amb telemetria recent; paràmetres congelats |
| D | A[0] per a t; C[1:24] per a t+1…t+23; sense reentrenament |

## Calendari, causalitat i estat

Només març–maig: **1704 hores**, en blocs de 576, 552 i 576 hores. Els models es carreguen de `src/forecast.py`, amb 2784 hores de train anteriors a març; no s'entrena ni s'ajusta cap model. La reserva es descarta abans de construir targets o diagnòstics i no se'n calcula cap mètrica. La política original ja s'havia ajustat històricament mirant el conjunt complet: aquesta comparació és retrospectiva, no un test intacte.

Totes les simulacions comencen amb SOC=1000 kWh i agents nous. El SOC persisteix entre març, abril i maig, igual que al motor, amb dt=1h per fila i sense simular les setmanes retirades. No hi ha restricció de SOC terminal; es reporta el SOC final per veure si els scores poden estar influïts per inventari residual diferent. Els desglossaments mensuals conserven l'estat acumulat i no són episodis independents.

El primer payload de demanda/solar s'elimina per a totes les variants, evitant que l'excepció t=0 del motor reveli el target actual. Després només es passa la telemetria de la fila anterior. C descarta la correcció obsoleta després dels salts; A i la component A de D poden retenir l'última dada realment observable, amb antiguitat explícita.

**Diferència comuna respecte a obs crues:** els vectors oficials contenen 24 files, que poden pertànyer al mes següent. El benchmark en trunca preu, CO₂ i consum efectiu del forecast al final del bloc cronològic. Hi ha 1635 decisions amb 24 hores consecutives i 69 amb un horitzó més curt: 46 censurades abans dels dos salts interns i 23 al final de la validació. Cap fila de l'altre costat del salt es tracta com t+h. Amb menys de 3 hores, es manté el repòs del prototip. Es puntuen **totes les 1704 accions**, sense eliminar hores després de decidir.

Aquesta censura usa exclusivament el calendari offline de validació, mai demanda/solar futures. L'obs no proporciona els timestamps futurs necessaris per reconstruir-la de manera general en producció. Per això els scores són del motor oficial amb una interfície temporal censurada comuna, no una reproducció literal del prototip amb vectors crus ni una garantia del servidor. Els 69 horitzons truncats depenen d'informació de calendari offline no disponible a obs: això encara no és una integració validada per a producció. Cal aclarir aquest contracte amb mentors abans d'integrar.

## Resultats mesurats amb el simulador oficial local

| Variant | Score /100 | Δ score vs sense forecast | Reducció CO₂ % | Estalvi cost % | Infraccions | Temps local s |
| --- | --- | --- | --- | --- | --- | --- |
| Sense forecast | 4.90 | +0.00 | 4.16 | 6.63 | 0 | 6.918 |
| A | 4.90 | +0.00 | 4.16 | 6.63 | 0 | 6.642 |
| B | 4.98 | +0.08 | 4.21 | 6.78 | 0 | 5.778 |
| C | 4.95 | +0.05 | 4.20 | 6.72 | 0 | 5.451 |
| D | 4.96 | +0.06 | 4.20 | 6.72 | 0 | 5.595 |

El score és el retorn arrodonit a dos decimals d'`evaluate_results()`: `max(0, 100*(0.7*dCO2 + 0.3*dCost - 0.002*infraccions))`. CO₂ i cost són reduccions percentuals respecte de la mateixa bateria absent, no respecte de la política de referència. Els Δ són diferències de scores ja arrodonits. Temps inclou inicialització, inferència, simulació i comprovacions del bucle local, sense càrrega del CSV ni proves addicionals; no és una mesura del servidor. El cas sense forecast executa també una crida de paritat al prototip a cada pas: les diferències temporals no estimen exclusivament el cost del predictor.

| Variant | Càrrega | Descàrrega | Repòs | Accions diferents del ref. | Límit de demanda actiu | SOC final kWh | Exportació kWh |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Sense forecast | 296 | 238 | 1170 | 0 | 0 | 1999.999905 | 0.000000 |
| A | 296 | 238 | 1170 | 0 | 0 | 1999.999905 | 0.000000 |
| B | 302 | 244 | 1158 | 117 | 0 | 1999.999905 | 0.000000 |
| C | 301 | 243 | 1160 | 117 | 0 | 1999.999905 | 0.000000 |
| D | 301 | 243 | 1160 | 120 | 0 | 1999.999905 | 0.000000 |

Càrrega/descàrrega es defineixen per potència >1e-06 / <−1e-06 kW; la resta és repòs. Amb zero infraccions no hi ha diferència material entre les accions demanades i les aplicades. «Límit de demanda actiu» es compta abans del clamp SOC.

| Mes | Variant | Hores | Score | Reducció CO₂ % | Estalvi cost % | SOC inicial | SOC final |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-03 | Sense forecast | 576 | 4.860000 | 4.100000 | 6.620000 | 1000.000000 | 945.907352 |
| 2026-04 | Sense forecast | 552 | 4.050000 | 3.330000 | 5.720000 | 945.907352 | 1999.999905 |
| 2026-05 | Sense forecast | 576 | 5.690000 | 4.910000 | 7.490000 | 1999.999905 | 1999.999905 |
| 2026-03 | A | 576 | 4.860000 | 4.100000 | 6.620000 | 1000.000000 | 945.907352 |
| 2026-04 | A | 552 | 4.050000 | 3.330000 | 5.720000 | 945.907352 | 1999.999905 |
| 2026-05 | A | 576 | 5.690000 | 4.910000 | 7.490000 | 1999.999905 | 1999.999905 |
| 2026-03 | B | 576 | 4.930000 | 4.190000 | 6.640000 | 1000.000000 | 945.907352 |
| 2026-04 | B | 552 | 4.260000 | 3.470000 | 6.120000 | 945.907352 | 1999.999905 |
| 2026-05 | B | 576 | 5.670000 | 4.860000 | 7.570000 | 1999.999905 | 1999.999905 |
| 2026-03 | C | 576 | 4.880000 | 4.160000 | 6.560000 | 1000.000000 | 945.907352 |
| 2026-04 | C | 552 | 4.250000 | 3.470000 | 6.080000 | 945.907352 | 1999.999905 |
| 2026-05 | C | 576 | 5.650000 | 4.840000 | 7.530000 | 1999.999905 | 1999.999905 |
| 2026-03 | D | 576 | 4.880000 | 4.160000 | 6.560000 | 1000.000000 | 945.907352 |
| 2026-04 | D | 552 | 4.250000 | 3.470000 | 6.080000 | 945.907352 | 1999.999905 |
| 2026-05 | D | 576 | 5.650000 | 4.840000 | 7.540000 | 1999.999905 | 1999.999905 |

## Interpretació i recomanació

Millor score observat: **B**, amb Δ=0.08 punts respecte del cas sense forecast. Aquesta identificació descriu el benchmark; no selecciona una política oficial ni ajusta els predictors. Menor MAE de C no implica automàticament millor score, perquè les decisions són discretes i molts límits de potència/demanda poden estar saturats.

| Variant | Δ score març | Δ score abril | Δ score maig |
| --- | --- | --- | --- |
| A | +0.00 | +0.00 | +0.00 |
| B | +0.07 | +0.21 | -0.02 |
| C | +0.02 | +0.20 | -0.04 |
| D | +0.02 | +0.20 | -0.04 |

A genera exactament les mateixes accions que la referència. La seva ponderació constant no altera la mitjana i el límit de demanda no és restrictiu en aquestes dades; no hi ha guany atribuïble a persistència en aquest adaptador.

El límit de demanda prevista no s'activa en cap variant: els canvis observats de B/C/D provenen de la ponderació temporal. Millorar la predicció de t amb D no resol aquí una restricció d'autoconsum activa i tampoc supera B.

Totes les variants acaben amb el mateix SOC (1999.999905 kWh). Tot i no imposar igualtat terminal, el guany mesurat no s'explica per buidar més la bateria al final. B millora març i abril, però empitjora maig: no hi ha una millora uniforme en els tres blocs.

B estalvia addicionalment 66.9 kg CO₂ i 337.24 € respecte de la política sense forecast en aquestes 1704 hores (diferències de mètriques arrodonides). El guany de score és petit i no s'ha estimat significació estadística.

**Recomanació: té sentit provar el forecast dins d'una branca experimental de l'optimitzador del Dani, mantenint la política sense forecast com a fallback.** El guany d'aquesta heurística no valida el seu MPC ni justifica desplegar-lo: cal repetir una ablació amb l'optimitzador fix, resoldre timestamps futurs i revisar estabilitat mensual, SOC terminal i runtime abans de substituir la referència.

Limitacions: comparació retrospectiva sobre tres blocs, sense independència entre mesos ni intervals de confiança; regla de ponderació diagnòstica que no pretén ser òptima; censura horària offline no disponible directament a obs; SOC terminal no igualat; mètriques oficials arrodonides; supòsits físics del comptador pendents; no s'ha executat dry-run web, leaderboard ni l'optimitzador del Dani. Cap resultat s'atribueix a forecast en la política original que no el consumeix.

## Verificació i reproducció

- 1704 hores de març–maig; cap ajust de models ni consulta de mètriques de juny–agost.
- 1635 horitzons complets i 69 truncats; tots els elements consumits verificats per timestamp.
- Mateix SOC inicial (1000 kWh), especificació física, denominadors i continuïtat entre blocs.
- Accions sense forecast iguals al prototip en cada estat sota el mateix truncament de vectors.
- Accions, SOC i forecasts prefix invariants en alterar demanda/solar de t i del futur.
- Cap infracció física a les cinc simulacions completes.

**28 proves unitàries passades** entre `analysis/test_forecast.py` i `analysis/test_battery_ablation.py`, incloent sensibilitat real de l'adaptador als forecasts, paritat del cas sense forecast, composició D, protecció del primer pas i alineament als salts. Els fixtures no són dades ni resultats oficials.

Entorn: Python 3.12.14, pandas 3.0.1, numpy 2.3.5. Sense aleatorietat ni llavor. Models i política carregats sense reentrenar. Paquet local: `C:\Users\cescc\Downloads\paquet_participants_datathon_upc.zip`.

| Font | SHA-256 |
| --- | --- |
| prototypes\upc\agent_v0_24h.py | de6beac0ff70206a868a276daecb0148bd4a13b566e65661c69b3d35c8101559 |
| src\forecast.py | 3f443d2198bb03075cd6a361364f4468d1e8fb2c48749627e14e2dd3b41c8090 |
| analysis\forecast_battery_ablation.py | 20be07362f96325e9a4a4cb809c13d624a216f8c91f4fd4155b67a79d3510e88 |
| starter_kit/environment.py (ZIP) | 06dcc2ea2ce9ea09ecde97b0437765be5e08553e8e28306b5bf7aaeb39542ae7 |
| contador.csv (CSV font complet) | baba32739604b8088c5b1ae322eecfa9790879754d3535bae3525f07ad9296ea |
| inversor.csv (CSV font complet) | aeb040d267537c6b59176dec48515d352038a104071365abd5604ef1928ea818 |
| precio_pvpc.csv (CSV font complet) | 73b9bff460d084515f8b1836b90e2299e5a09dd3acd1a55d53a2385a31125249 |
| co2_red.csv (CSV font complet) | 8f19863ffb65624a84615cfd8fb5800f4d37ea5ddf59123a6fd829a6e2736d65 |

Ordre executada:

```powershell
& 'C:\Program Files\WindowsApps\OpenAI.CodexPrimaryRuntime.v26-1112-611-0_26.1112.611.0_x64__3k8sg7r9htsxt\dependencies\python\python.exe' -B analysis/forecast_battery_ablation.py --kit 'C:\Users\cescc\Downloads\paquet_participants_datathon_upc.zip' --report
```

Sense `--report`, es recalcula tot i es passen les proves sense escriure fitxers. Només es creen scripts/proves dins d'analysis i aquest informe; els sis fitxers locals anteriors i els fitxers compartits es conserven. Sense commit, push ni merge.
