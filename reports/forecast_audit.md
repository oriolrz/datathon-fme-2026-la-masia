# Auditoria de dades temporals oficials UPC Sostenible

Responsable: Cesc · issue [#3](https://github.com/oriolrz/datathon-fme-2026-la-masia/issues/3) · branca `feat/cesc-forecast`. Auditoria del 14/11/2026. Abast autoritzat: `analysis/audit_temporal.py` i aquest informe. La issue es va consultar en només lectura (oberta, 0 comentaris); els documents compartits encara descriuen el repte com a provisional. Aquest treball aplica l'encàrrec explícit d'auditoria de Cesc; no implementa cap model.

## Procedència i reproduïbilitat

Paquet local: `C:\Users\cescc\Downloads\paquet_participants_datathon_upc.zip`. Lectura directa en memòria, sense extracció ni còpia de CSV. La identitat d'origen és la del paquet proporcionat localment; no s'ha verificat cap signatura ni s'ha comparat amb una descàrrega nova del servidor.

SHA-256 del ZIP: `35bd6e26e8d63a4defaeef8287e38c8b9c39463b99867d14fd44b7766bc976e0`.

Entorn: Python 3.12.14, pandas 3.0.1, numpy 2.3.5. Cap aleatorietat ni entrenament: no cal llavor. La base `Europe/Madrid` només s'usa per diagnosticar DST; la reproducció oficial conserva les marques de temps sense zona.

| Membre del paquet | SHA-256 |
| --- | --- |
| data/train/contador.csv | baba32739604b8088c5b1ae322eecfa9790879754d3535bae3525f07ad9296ea |
| data/train/inversor.csv | aeb040d267537c6b59176dec48515d352038a104071365abd5604ef1928ea818 |
| data/train/precio_pvpc.csv | 73b9bff460d084515f8b1836b90e2299e5a09dd3acd1a55d53a2385a31125249 |
| data/train/co2_red.csv | 8f19863ffb65624a84615cfd8fb5800f4d37ea5ddf59123a6fd829a6e2736d65 |
| data/train/meteo.csv | a28a7bffa193077fe1f849a38cd509f74a9a05ae6aa4a6b5ef3cac3ca8f464c2 |
| data/train/entradas_salidas.csv | 012404e373238d6089cc534401cc7a88f100228fd768f2f5d14b722476245ea9 |
| starter_kit/tutorial.ipynb | e51f5ad46b7c645d350b58fc19fd00f0621326f4a91f6339a43c619a7f2ad526 |
| starter_kit/environment.py | 06dcc2ea2ce9ea09ecde97b0437765be5e08553e8e28306b5bf7aaeb39542ae7 |
| docs/GUIA_VARIABLES.md | 2b1546256315edecc95bc46db838caf694c2b7f45006db8cce7a3c08da35b32b |
| starter_kit/battery_spec.json | 2eb79f7c0ebf0c40acf04a10237746e1655aba7be9287a9884f043fcbeae3211 |

Ordre executable que ha generat aquest informe:

```powershell
& 'C:\Program Files\WindowsApps\OpenAI.CodexPrimaryRuntime.v26-1112-611-0_26.1112.611.0_x64__3k8sg7r9htsxt\dependencies\python\python.exe' -B analysis/audit_temporal.py --kit 'C:\Users\cescc\Downloads\paquet_participants_datathon_upc.zip' --expect-hours 5993 --report reports/forecast_audit.md
```

Per tornar a comprovar-ho sense escriure fitxers, executa la mateixa ordre sense `--report reports/forecast_audit.md`. `--expect-hours 5993` fa fallar l'execució si canvia el recompte. El script només admet aquest informe com a destinació d'escriptura.

## Inventari, temps i qualitat de les sis fonts

| CSV | Files | Columnes | Inici | Final | Cel·les nul·les | Columnes tot nul |
| --- | --- | --- | --- | --- | --- | --- |
| contador.csv | 74210 | 29 | 2025-09-01 00:05:00 | 2026-09-01 00:00:00 | 75438 | 1 |
| inversor.csv | 71882 | 176 | 2025-09-01 00:05:00 | 2026-08-16 22:00:00 | 216037 | 0 |
| precio_pvpc.csv | 6768 | 3 | 2025-09-01 00:00:00 | 2026-09-01 23:00:00 | 0 | 0 |
| co2_red.csv | 6768 | 5 | 2025-09-01 00:00:00 | 2026-09-01 23:00:00 | 0 | 0 |
| meteo.csv | 74210 | 20 | 2025-09-01 00:05:00 | 2026-09-01 00:00:00 | 74259 | 1 |
| entradas_salidas.csv | 74210 | 20 | 2025-09-01 00:05:00 | 2026-09-01 00:00:00 | 734261 | 9 |

`Fecha` és la clau temporal, sense offset ni zona a tots sis CSV. La guia declara hora local UTC+1/UTC+2; `Europe/Madrid` és la interpretació de calendari coherent amb aquesta declaració, no una zona codificada a les dades. La guia anomena `entrades_salides.csv` el fitxer que realment es diu `entradas_salidas.csv`. Els nuls totals inclouen metadades i canals no utilitzats; no equivalen a nuls de demanda.

| CSV | Pas nominal (min) | Passos regulars | Salts | Instants absents en el rang | Timestamps duplicats | Files duplicades | Retrocessos | Fora de graella |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| contador.csv | 5 | 74195 | 14 | 30910 | 0 | 0 | 0 | 0 |
| inversor.csv | 5 | 71868 | 13 | 28894 | 0 | 0 | 0 | 0 |
| precio_pvpc.csv | 60 | 6755 | 12 | 2016 | 0 | 0 | 0 | 0 |
| co2_red.csv | 60 | 6755 | 12 | 2016 | 0 | 0 | 0 | 0 |
| meteo.csv | 5 | 74195 | 14 | 30910 | 0 | 0 | 0 | 0 |
| entradas_salidas.csv | 5 | 74195 | 14 | 30910 | 0 | 0 | 0 | 0 |

Els instants absents es compten entre el primer i l'últim timestamp de cada font, en hora local sense zona; inclouen setmanes retirades, manca de novembre i avaries. No són tots errors de sensors.

| CSV | Marques ambigües de tardor | Marques inexistents de primavera |
| --- | --- | --- |
| contador.csv | 0 | 0 |
| inversor.csv | 0 | 0 |
| precio_pvpc.csv | 0 | 0 |
| co2_red.csv | 0 | 0 |
| meteo.csv | 0 | 0 |
| entradas_salidas.csv | 0 | 0 |

Les hores de canvi d'horari de 26/10/2025 i 29/03/2026 cauen en setmanes absents del paquet: no es pot verificar com les fonts originals resolien l'hora repetida o inexistent. L'absència de duplicats no demostra que la sèrie sigui UTC ni que resolgui DST. Abans d'una conversió a UTC, cal obtenir la zona i el conveni d'ambigüitat de l'organització; no localitzar amb `ambiguous='infer'` a cegues ni inventar offsets.

## Variables, signe i agregació solar

| Família | Unitats / significat | Disponible en obs |
| --- | --- | --- |
| Comptador: potència activa; reactiva; tensió; corrent; factor de potència | kW; kVAr; V; A; adimensional | Només la potència activa transformada i agregada, amb retard |
| Energies importada/exportada i reactives | kWh / kVArh; guia: acumuladors | No |
| Tres inversors: potència AC total, per fase, aparent/reactiva, DC i MPPT | kW / kVA / kVAr; V; A; Hz | Només suma AC agregada, amb retard |
| Temperatures / aïllament / consignes / hores / diagnòstic dels inversors | °C / Ohm / % / h / estats | No |
| Meteorologia: irradiància, temperatures, vent, hores sol pic | W/m²; °C; m/s; h | No, ni actual ni futura |
| Entrades/sortides i metadades de comunicació | Estats binaris i diagnòstic | No |
| PVPC i equivalent MWh | €/kWh i €/MWh | Només €/kWh actual i llista coneguda |
| CO₂, percentatge emissor i potències de generació | kg CO₂/kWh; %; MW | Només intensitat actual i llista coneguda |

Comptador cru: 74010 valors negatius, 197 zeros, 0 positius i 3 nuls; rang [-2696.000, 0.000] kW. La inversió de signe dona importació positiva. El clip [0, 5000] del tutorial afecta 0 valors no nuls.

Columnes solars realment seleccionades: `Inversor 1 - POTENCIA ACTIVA (kW)`, `Inversor 2 - POTENCIA ACTIVA (kW)`, `Inversor 3 - POTENCIA ACTIVA (kW)`. Se sumen els totals AC dels tres equips; afegir-hi les columnes per fase duplicaria potència. El tutorial substitueix cada nul de cada inversor per zero **abans** de sumar i després retalla només el total per sota de zero.

Fragilitat de la selecció del tutorial: el filtre de text també coincideix amb `SETPOINT RELATIVO POTENCIA ACTIVA (%)`; escull `[0]`, que en aquest CSV és el total AC en kW. El script comprova explícitament aquest primer candidat; reordenar columnes podria canviar el resultat oficial sense un error visible. No s'ha alterat el tutorial.

| Total AC | Nuls | Negatius | Mín. kW | Màx. kW | Error mitjà vs suma fases kW | Error màxim kW |
| --- | --- | --- | --- | --- | --- | --- |
| Inversor 1 - POTENCIA ACTIVA (kW) | 3 | 0 | 0.000000 | 50.060000 | 0.003579 | 1.940000 |
| Inversor 2 - POTENCIA ACTIVA (kW) | 3 | 0 | 0.000000 | 50.070000 | 0.003632 | 1.850000 |
| Inversor 3 - POTENCIA ACTIVA (kW) | 3 | 0 | 0.000000 | 50.060000 | 0.003658 | 2.130000 |

Files amb algun inversor nul: 3; amb tots tres nuls: 3. Les petites diferències entre totals AC i fases no proven una suma equivocada: poden incloure arrodoniments i manca de simultaneïtat; no es corregeixen sense evidència física.

El `fillna(0)` introdueix una hora solar aparentment vàlida sense comptador vàlid: 2025-11-01 00:00:00. En aquesta hora només hi ha telemetria nul·la dels tres inversors. La intersecció final la descarta gràcies al nul del comptador; no s'ha comptat com una hora útil.

La guia descriu `Contador - ENERGIA ACTIVA IMPORTADA (kWh)` com a acumulador, però hi ha 22147 decrements entre mostres consecutives separades 5 minuts. No és un acumulador monòton usable sense aclarir resets/semàntica; no s'ha emprat per validar energia integrada ni signe físic.

**Possible doble comptatge físic:** la guia situa el comptador al PCC i descriu els negatius com a importació neta de solar; el tutorial anomena `load_kw=-comptador` i el motor després calcula `load_kw-pv_kw+acció`. Això podria restar dues vegades la generació. No ho resol el signe observat. S'ha reproduït exactament el contracte del simulador, sense canviar-lo; cal confirmar amb mentors si `load_kw` representa demanda bruta o importació al PCC.

## Reproducció exacta del tutorial i hores útils

S'ha replicat la cel·la 4 (`resample('1h').mean()`, signe, clips, zero dels inversors i intersecció final amb `.dropna()`) i s'ha executat separadament aquesta mateixa cel·la oficial en memòria. `pd.testing.assert_frame_equal` confirma igualtat de tota la taula. No s'han executat les cel·les de models, guardat de fitxers ni empaquetament.

| Etapa | Hores no nul·les |
| --- | --- |
| Comptador agregat | 6187 |
| Solar agregada | 5994 |
| PVPC | 6768 |
| CO₂ | 6768 |
| Intersecció final tutorial | 5993 |
| Diferència respecte de 5993 | 0 |

| Disponibilitat a la unió (1=present) | Hores |
| --- | --- |
| load=1 pv=1 price=1 co2=1 | 5993 |
| load=0 pv=1 price=1 co2=1 | 1 |
| load=0 pv=0 price=1 co2=1 | 580 |
| load=1 pv=0 price=1 co2=1 | 194 |

Rang final: 2025-09-01 00:00:00 → 2026-08-16 22:00:00. La graella local completa del rang tindria 8399 hores. «Útils» significa aquí acceptades pel tutorial; no garanteix 12 mostres vàlides a cada hora.

| Mes | Hores |
| --- | --- |
| 2025-09 | 552 |
| 2025-10 | 576 |
| 2025-12 | 576 |
| 2026-01 | 576 |
| 2026-02 | 504 |
| 2026-03 | 576 |
| 2026-04 | 552 |
| 2026-05 | 576 |
| 2026-06 | 550 |
| 2026-07 | 576 |
| 2026-08 | 379 |

Novembre de 2025 no apareix a la taula final. L'inversor acaba el 16/08/2026 a les 22:00, tot i que les altres fonts arriben al setembre. Les absències mensuals de la unió no s'han omplert ni s'han tractat com a temps físic transcorregut d'una hora.

| Mostres vàlides en una hora | Hores comptador | Hores amb 3 inversors vàlids |
| --- | --- | --- |
| 1 | 1 | 2 |
| 4 | 1 | 1 |
| 7 | 1 | 1 |
| 11 | 2 | 2 |
| 12 | 5988 | 5987 |

Hores amb 12 mostres vàlides de comptador i dels tres inversors: 5987; hores parcials en alguna de les dues fonts: 6. La cohort estricta és un diagnòstic de sensibilitat; no substitueix el preprocessament oficial.

| Hora parcial | Mostres comptador | Mostres amb 3 inversors vàlids |
| --- | --- | --- |
| 2025-09-01 00:00:00 | 11 | 11 |
| 2026-06-17 14:00:00 | 11 | 11 |
| 2026-06-17 17:00:00 | 7 | 7 |
| 2026-08-04 07:00:00 | 1 | 1 |
| 2026-08-04 12:00:00 | 4 | 4 |
| 2026-08-16 22:00:00 | 12 | 1 |

`resample('1h')` usa intervals [h, h+1) amb etiqueta a l'esquerra: la mostra de 01:00 pertany a l'hora 01, no a l'hora 00. Els sensors comencen a 00:05; cal confirmar si les marques són instantànies o de final d'interval abans de reinterpretar energia. Les mitjanes són aritmètiques de potència (kW), no sumes de kW; a dt=1h tenen equivalència numèrica en kWh per al motor. Amb mostres parcials es pressuposa representativitat de la resta de l'hora.

## Discontinuïtats i risc d'alineació

| Última hora abans | Primera hora després | Salt (h) | Hores absents |
| --- | --- | --- | --- |
| 2025-09-23 23:00:00 | 2025-10-01 00:00:00 | 169.000000 | 168 |
| 2025-10-24 23:00:00 | 2025-12-01 00:00:00 | 889.000000 | 888 |
| 2025-12-24 23:00:00 | 2026-01-01 00:00:00 | 169.000000 | 168 |
| 2026-01-24 23:00:00 | 2026-02-01 00:00:00 | 169.000000 | 168 |
| 2026-02-21 23:00:00 | 2026-03-01 00:00:00 | 169.000000 | 168 |
| 2026-03-24 23:00:00 | 2026-04-01 00:00:00 | 169.000000 | 168 |
| 2026-04-23 23:00:00 | 2026-05-01 00:00:00 | 169.000000 | 168 |
| 2026-05-24 23:00:00 | 2026-06-01 00:00:00 | 169.000000 | 168 |
| 2026-06-17 14:00:00 | 2026-06-17 17:00:00 | 3.000000 | 2 |
| 2026-06-23 23:00:00 | 2026-07-01 00:00:00 | 169.000000 | 168 |
| 2026-07-24 23:00:00 | 2026-08-01 00:00:00 | 169.000000 | 168 |
| 2026-08-04 07:00:00 | 2026-08-04 12:00:00 | 5.000000 | 4 |

12 salts i 13 blocs contigus en hora local. Total d'hores absents internes: 2406. Un salt de 169 h deixa 168 hores absents; el de 889 h en deixa 888. El simulador conserva el SOC i només aplica dt=1h a cada fila, també a través dels salts; no simula consum, pèrdues ni accions durant les hores absents.

| Bloc | Inici | Final | Hores |
| --- | --- | --- | --- |
| 1 | 2025-09-01 00:00:00 | 2025-09-23 23:00:00 | 552 |
| 2 | 2025-10-01 00:00:00 | 2025-10-24 23:00:00 | 576 |
| 3 | 2025-12-01 00:00:00 | 2025-12-24 23:00:00 | 576 |
| 4 | 2026-01-01 00:00:00 | 2026-01-24 23:00:00 | 576 |
| 5 | 2026-02-01 00:00:00 | 2026-02-21 23:00:00 | 504 |
| 6 | 2026-03-01 00:00:00 | 2026-03-24 23:00:00 | 576 |
| 7 | 2026-04-01 00:00:00 | 2026-04-23 23:00:00 | 552 |
| 8 | 2026-05-01 00:00:00 | 2026-05-24 23:00:00 | 576 |
| 9 | 2026-06-01 00:00:00 | 2026-06-17 14:00:00 | 399 |
| 10 | 2026-06-17 17:00:00 | 2026-06-23 23:00:00 | 151 |
| 11 | 2026-07-01 00:00:00 | 2026-07-24 23:00:00 | 576 |
| 12 | 2026-08-01 00:00:00 | 2026-08-04 07:00:00 | 80 |
| 13 | 2026-08-04 12:00:00 | 2026-08-16 22:00:00 | 299 |

## Rangs, nuls i senyals atípics

| Variable | Nuls | Mín. | Mitjana | Mediana | p99 | Màx. | Fora IQR 1,5 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| load_kw | 0 | 0.000000 | 1122.591372 | 1069.000000 | 2175.446667 | 2503.083333 | 106 |
| pv_kw | 0 | 0.000000 | 26.502328 | 0.765833 | 130.584267 | 144.064167 | 329 |
| precio_eur_per_kwh | 0 | 0.003270 | 0.138001 | 0.132530 | 0.304772 | 0.398580 | 106 |
| co2_kg_per_kwh | 0 | 0.027879 | 0.084672 | 0.072775 | 0.198391 | 0.221743 | 70 |
| net_load_kw | 0 | 0.000000 | 1096.089044 | 1067.500000 | 2074.941600 | 2404.461667 | 91 |

Els llindars IQR són descriptius calculats sobre tota l'auditoria: no són paràmetres de neteja, ni criteris ajustats per entrenar. En solar, una distribució amb moltes nits a zero pot marcar hores diürnes normals. No s'ha eliminat cap outlier ni s'ha interpolat cap dada.

| Meteorologia crua | Nuls | Mín. | Màx. | Zeros | Negatius | Fora IQR 1,5 |
| --- | --- | --- | --- | --- | --- | --- |
| Atersa - TEMPERATURA AMBIENTE (SENSOR 1) (ºC) | 3 | 0.000000 | 56.600000 | 2 | 0 | 104 |
| Atersa - TEMPERATURA PANEL (SENSOR 1) (ºC) | 3 | -1.600000 | 73.100000 | 6 | 31 | 1090 |
| Atersa - VELOCIDAD VIENTO (SENSOR 1) (m/s) | 3 | 0.000000 | 0.000000 | 74207 | 0 | 0 |
| Atersa - IRRADIANCIA (W/m2) | 3 | 0.000000 | 1326.000000 | 36321 | 0 | 6086 |
| Atersa - IRRADIANCIA 1 (W/m2) | 3 | 0.000000 | 1326.000000 | 36722 | 0 | 6080 |
| Atersa - IRRADIANCIA 2 (W/m2) | 3 | 0.000000 | 1322.000000 | 36320 | 0 | 6047 |
| Atersa - HORAS SOL PICO (h) | 2 | -1367.730000 | 0.110000 | 43041 | 2 | 2781 |

El canal de vent és constant a zero en totes les mostres no nul·les: no aporta variació i no se'n pot inferir absència real de vent. Les hores de sol pic tenen valors negatius incompatibles amb la descripció d'energia acumulada normalitzada; la temperatura ambient màxima requereix contrast amb la qualitat/ubicació del sensor. La temperatura de panell negativa o alta i irradiàncies elevades no es declaren errònies només pel rang. Aquestes variables s'auditen, però no s'introdueixen com a features: no les exposa obs.

Demanda horària igual a zero: 15 h; demanda neta negativa: 0 h; demanda neta inferior a 500 kW: 31 h (0.5173%). Zeros i demanda neta negativa poden alterar energia de referència i decisions de descàrrega; no es descarten sense aclarir si són fallades de telemetria o valors reals.

Comptador amb qualitat COM <100: 223 mostres; zeros de potència coincidents amb qualitat <100: 197. Aquesta coincidència és un indici d'incidència de comunicació, no una prova universal. Les marques de qualitat s'han mantingut fora de qualsevol feature perquè no arriben a `obs`.

Discrepància documental resolta: mitjana de demanda crua a 5 min = 1115.039700 kW; mitjana horària consolidada = 1122.591372 kW. Les xifres aproximades 1115 i 1123 dels informes previs corresponen a poblacions i ponderacions diferents; no hi ha discrepància en el recompte de 5993 h.

Coherència de preus: màxim error absolut entre €/MWh / 1000 i €/kWh = 9.97465998687e-17 €/kWh. Les sis fonts no contenen infinits en cap columna numèrica (comprovació explícita).

## Què coneix realment BatteryAgent.act(obs)

| Clau | Unitat / contingut | Disponibilitat comprovada |
| --- | --- | --- |
| timestamp, hour, day_of_week | Hora local sense zona; hora 0–23; dilluns=0 | Fila actual; calendari derivable, inclòs mes; no timestamps futurs |
| soc_kwh, soc_pct, soc_percent | kWh; fracció 0–1; percentatge 0–100 | Estat actual de la bateria |
| preu_actual, co2_actual | €/kWh; kg CO₂/kWh | Fila actual |
| preus_properes_24h, co2_properes_24h | Llistes de longitud 1–24, mateixes unitats | iloc[t:t+24]: inclouen t i arriben com a màxim a t+23 files; sense timestamps per element |
| noves_dades_5min.ultim_consum_kw | kW de demanda mitjana horària | Fila anterior si t>0; fila actual si t=0 |
| noves_dades_5min.ultima_solar_kw | kW de solar mitjana horària | Fila anterior si t>0; fila actual si t=0 |

Comprovació dinàmica del motor oficial en 5993 passos reals, sempre amb acció 0 kW: balanç de xarxa exactament igual a max(load−pv, 0), SOC constant a 1000 kWh, 0 infraccions i score 0.00. Aquesta prova valida el contracte i el balanç; no és un benchmark de cap política candidata.

Hi ha 276 decisions amb un salt dins la llista futura i 12 decisions on la fila anterior no és l'hora anterior. Les últimes 23 decisions tenen llistes de menys de 24 elements. Així, aquestes llistes no representen sempre 24 hores consecutives. L'agent pot detectar que el seu retard és obsolet comparant el timestamp actual amb l'anterior que ha guardat; no pot recuperar els timestamps futurs absents a partir d'obs.

**Excepció del primer pas:** `t=0` exposa el valor real de demanda i solar de la mateixa hora que el motor està a punt de simular. És el contracte local observat, no una disponibilitat causal generalitzable a totes les hores. Per avaluar forecasting, ometre aquesta telemetria al primer origen (o marcar explícitament la inicialització) i comprovar amb mentors si el servidor replica l'excepció.

No estan disponibles demanda/solar actuals quan t>0, demanda/solar futures, mostres de 5 min, meteorologia actual o futura, relés, fases, energies, qualitat COM, consum de les hores retirades ni components del mix de generació. Les previsions perfectes de preu i CO₂ sí que estan expressament autoritzades per aquest motor; no permeten afegir-hi altres futurs. La sola presència d'una columna al CSV no autoritza usar-la com a feature en temps de decisió.

## Proposta de validació temporal causal

Proposta determinista per a H=24 valors: l'hora actual t i les 23 següents, predits a la decisió t amb telemetria de demanda/solar només fins a t−1, coherent amb els vectors de preu/CO₂ d'obs dins d'un bloc contigu. Definida per dates de calendari abans d'ajustar cap forecast. El límit dret és exclusiu:

| Partició | Inici inclòs | Final exclòs | Hores | Blocs contigus | Orígens amb 24 objectius contigus interns |
| --- | --- | --- | --- | --- | --- |
| Entrenament | 2025-09-01 | 2026-03-01 | 2784 | 5 | 2669 |
| Validació de desenvolupament | 2026-03-01 | 2026-06-01 | 1704 | 3 | 1635 |
| Reserva retrospectiva | 2026-06-01 | 2026-09-01 | 1505 | 5 | 1390 |

1. Entrenar només amb dates d'entrenament; ajustar imputació causal, escalat, selecció de variables i qualsevol llindar exclusivament dins el train de cada fold. Sense barreja aleatòria de files.
2. Per entrenar exemples multi-horitzó, un origen t només és admissible si totes les etiquetes t…t+23 existeixen al mateix bloc i partició; comprovar timestamps, no només posicions. Purgar els últims H−1 orígens de cada bloc. Això evita finestres que travessin splits o salts; si canvia H o l'alineament dels objectius, recalcular la purga.
3. Construir lags per unió amb timestamp exacte (t−1h, t−24h, t−168h); un `.shift(24)` sobre files és incorrecte al costat d'un buit. No interpolar amb valors posteriors, no usar rolling centrat ni `bfill`, i no passar a través de setmanes retirades.
4. Reproduir l'ordre d'obs: a la decisió t>0 només entren a l'estat de demanda/solar els valors que el motor revela de la fila anterior; les observacions d'etiquetes futures només es revelen quan toca. La història de validació ja observada es pot actualitzar causalment en línia; els pesos i hiperparàmetres es mantenen congelats durant cada avaluació. Els perfils estacionals de validació no es recalculen amb tot el bloc.
5. Per ajustar opcions dins del train, usar folds expansius amb validació desembre, gener i febrer, entrenant sempre en mesos estrictament anteriors i aplicant la mateixa purga. Novembre absent no s'interpola. Una configuració final es congela abans d'obrir la reserva.
6. Avaluar cada partició amb agent nou, SOC inicial oficial 1000 kWh i sense mirar més enllà del final de la partició; dins d'aquesta, conservar el SOC entre blocs tal com fa el motor. Si es reporta una prova independent per bloc, reinicialitzar-la explícitament i no barrejar aquests scores amb els d'una simulació contínua. Caldrà comprovar el contracte d'estat inicial de la telemetria al primer pas.
7. Reportar error de forecasting per horitzó i bloc amb nombre d'exemples; i, quan s'integri una política, score, costos, CO₂, infraccions, SOC final i runtime sobre el mateix protocol. Calcular el score global amb les sumes dels denominadors oficials, no la mitjana dels scores mensuals.

**Límit d'independència:** els informes compartits indiquen que la política anterior es va triar mirant totes les 5993 h i ja en publiquen resultats mensuals. Cap subconjunt d'aquest paquet es pot presentar com a holdout històricament intacte de l'equip. Aquest split evita fugues de features, etiquetes i preprocessament en nous forecasts si s'aplica el protocol; la reserva continua sent retrospectiva. Només dades realment noves o el test ocult poden donar una confirmació independent. L'auditoria tampoc acredita el preprocessament del servidor.

## Comprovacions executades, límits i següent tasca

Passades: lectura dels sis CSV; esquema i hashes; timestamps vàlids, únics i ordenats; graella nominal; duplicats de fila; nuls de totes les columnes; absència d'infinits numèrics; diagnòstic DST; signe/clips; selecció dels tres inversors i contrast amb fases; igualtat exacta amb la cel·la oficial de preprocessament; cobertura intrahorària; rangs i IQR; blocs; splits; totes les observacions i balanç sense acció del motor oficial. Les anomalies de dades es documenten: no es tracten com un error del script.

Pendents que afecten interpretació: demanda bruta vs comptador net al PCC; semàntica de les marques temporals i acumuladors; qualitat dels zeros; contracte del servidor per a telemetria inicial, DST i previsions que travessen buits. No s'ha executat cap model, validador de submissió, dry-run web ni tramesa; no s'ha fet commit, push ni merge.

Següent tasca recomanada: acordar aquest split i el contracte causal amb l'integrador, resoldre amb mentors el balanç PCC/solar i la telemetria inicial, i després definir una baseline estacional de demanda neta que consumeixi exactament obs. Implementar-la requerirà un nou abast autoritzat; aquí només hi ha auditoria.

## Annex: diccionari complet de columnes i nuls

Noms i recomptes agregats, sense valors de sensors, identificadors de dispositius ni files brutes. Les unitats de les columnes s'infereixen del nom i de la guia; «sense unitat / metadada» no implica una magnitud física coneguda. Els sufixos `.1` procedeixen del CSV llegit amb pandas.

<details>
<summary>contador.csv</summary>

| Columna | Tipus llegit | Unitat / classe | Nuls |
| --- | --- | --- | --- |
| Fecha | datetime sense zona | hora local, sense offset | 0 |
| Medida | int64 | sense unitat / metadada | 0 |
| Contador - MARCA | float64 | sense unitat / metadada | 3 |
| Contador - MODELO | float64 | sense unitat / metadada | 3 |
| Contador - ESTADO COM | float64 | sense unitat / metadada | 3 |
| Contador - CALIDAD COM | float64 | escala 0–100 segons guia | 3 |
| Contador - NUMERO DE PREGUNTAS | float64 | sense unitat / metadada | 2 |
| Contador - NUMERO DE FALLOS | float64 | sense unitat / metadada | 2 |
| Contador - FECHA ULTIMA LECTURA | float64 | marca temporal auxiliar | 3 |
| Contador - DURACION ULTIMO MUESTREO (s) | float64 | s | 3 |
| Contador - FECHA | float64 | marca temporal auxiliar | 3 |
| Contador - DIRECCIÓN DE ENLACE | float64 | sense unitat / metadada | 3 |
| Contador - ENERGIA ACTIVA EXPORTADA (kWh) | float64 | kWh | 195 |
| Contador - ENERGIA ACTIVA IMPORTADA (kWh) | float64 | kWh | 195 |
| Contador - ENERGIA REACTIVA Q1 (kVArh) | float64 | kVArh | 195 |
| Contador - ENERGIA REACTIVA Q2 (kVArh) | float64 | kVArh | 195 |
| Contador - ENERGIA REACTIVA Q3 (kVArh) | float64 | kVArh | 195 |
| Contador - ENERGIA REACTIVA Q4 (kVArh) | float64 | kVArh | 195 |
| Contador - POTENCIA ACTIVA EXPORTADA (kW) | float64 | kW | 3 |
| Dispositivo 1 - POTENCIA REACTIVA (kVAr) | float64 | kVAr | 3 |
| Contador - TENSIÓN AC FASE 1-N (V) | float64 | V | 3 |
| Contador - TENSIÓN AC FASE 2-N (V) | float64 | V | 3 |
| Contador - TENSIÓN AC FASE 3-N (V) | float64 | V | 3 |
| Contador - CORRIENTE AC FASE 1 (A) | float64 | A | 3 |
| Contador - CORRIENTE AC FASE 2 (A) | float64 | A | 3 |
| Contador - CORRIENTE AC FASE 3 (A) | float64 | A | 3 |
| Dispositivo 1 - FACTOR DE POTENCIA | float64 | sense unitat / metadada | 3 |
| Meter 1 - ULTIMA FECHA CURVA DE CARGA | float64 | marca temporal auxiliar | 74210 |
| Contador - FECHA CURVA CARGA ACTUAL | float64 | marca temporal auxiliar | 3 |

</details>

<details>
<summary>inversor.csv</summary>

| Columna | Tipus llegit | Unitat / classe | Nuls |
| --- | --- | --- | --- |
| Fecha | datetime sense zona | hora local, sense offset | 0 |
| Medida | int64 | sense unitat / metadada | 0 |
| Inversor 1 - MARCA | float64 | sense unitat / metadada | 3 |
| Inversor 1 - MODELO | float64 | sense unitat / metadada | 3 |
| Inversor 1 - ESTADO COM | float64 | sense unitat / metadada | 3 |
| Inversor 1 - CALIDAD COM | float64 | escala 0–100 segons guia | 3 |
| Inversor 1 - NUMERO DE PREGUNTAS | float64 | sense unitat / metadada | 4 |
| Inversor 1 - NUMERO DE FALLOS | float64 | sense unitat / metadada | 67899 |
| Inversor 1 - FECHA ULTIMA LECTURA | float64 | marca temporal auxiliar | 3 |
| Inversor 1 - DURACION ULTIMO MUESTREO (s) | float64 | s | 3 |
| Inversor 1 - ENERGIA ACTIVA (kWh) | float64 | kWh | 3399 |
| Inversor 1 - POTENCIA ACTIVA (kW) | float64 | kW | 3 |
| Inversor 1 - POTENCIA ACTIVA FASE 1 (kW) | float64 | kW | 3 |
| Inversor 1 - POTENCIA ACTIVA FASE 2 (kW) | float64 | kW | 3 |
| Inversor 1 - POTENCIA ACTIVA FASE 3 (kW) | float64 | kW | 3 |
| Inversor 1 - POTENCIA REACTIVA (kVAr) | float64 | kVAr | 3 |
| Inversor 1 - POTENCIA REACTIVA FASE 1 (kVAr) | float64 | kVAr | 3 |
| Inversor 1 - POTENCIA REACTIVA FASE 2 (kVAr) | float64 | kVAr | 3 |
| Inversor 1 - POTENCIA REACTIVA FASE 3 (kVAr) | float64 | kVAr | 3 |
| Inversor 1 - POTENCIA APARENTE (kVA) | float64 | kVA | 3 |
| Inversor 1 - POTENCIA APARENTE FASE 1 (kVA) | float64 | kVA | 3 |
| Inversor 1 - POTENCIA APARENTE FASE 2 (kVA) | float64 | kVA | 3 |
| Inversor 1 - POTENCIA APARENTE FASE 3 (kVA) | float64 | kVA | 3 |
| Inversor 1 - TENSIÓN AC FASE 1-N (V) | float64 | V | 3 |
| Inversor 1 - TENSIÓN AC FASE 2-N (V) | float64 | V | 3 |
| Inversor 1 - TENSIÓN AC FASE 3-N (V) | float64 | V | 3 |
| Inversor 1 - CORRIENTE AC (A) | float64 | A | 3 |
| Inversor 1 - CORRIENTE AC FASE 1 (A) | float64 | A | 3 |
| Inversor 1 - CORRIENTE AC FASE 2 (A) | float64 | A | 3 |
| Inversor 1 - CORRIENTE AC FASE 3 (A) | float64 | A | 3 |
| Inversor 1 - FRECUENCIA (Hz) | float64 | Hz | 3 |
| Inversor 1 - TENSIÓN DC (V) | float64 | V | 3 |
| Inversor 1 - CORRIENTE DC (A) | float64 | A | 3 |
| Inversor 1 - POTENCIA DC (kW) | float64 | kW | 3 |
| Inversor 1 - TENSIÓN DC IN 01 (V) | float64 | V | 3 |
| Inversor 1 - CORRIENTE DC IN 01 (A) | float64 | A | 3 |
| Inversor 1 - POTENCIA DC IN 01 (kW) | float64 | kW | 3 |
| Inversor 1 - TENSIÓN DC IN 02 (V) | float64 | V | 3 |
| Inversor 1 - CORRIENTE DC IN 02 (A) | float64 | A | 3 |
| Inversor 1 - POTENCIA DC IN 02 (kW) | float64 | kW | 3 |
| Inversor 1 - TENSIÓN DC IN 03 (V) | float64 | V | 3 |
| Inversor 1 - CORRIENTE DC IN 03 (A) | float64 | A | 3 |
| Inversor 1 - POTENCIA DC IN 03 (kW) | float64 | kW | 3 |
| Inversor 1 - TENSIÓN DC IN 04 (V) | float64 | V | 3 |
| Inversor 1 - CORRIENTE DC IN 04 (A) | float64 | A | 3 |
| Inversor 1 - POTENCIA DC IN 04 (kW) | float64 | kW | 3 |
| Dispositivo 1 - TENSIÓN DC IN 05 (V) | float64 | V | 3 |
| Dispositivo 1 - CORRIENTE DC IN 05 (A) | float64 | A | 3 |
| Dispositivo 1 - POTENCIA DC IN 05 (kW) | float64 | kW | 3 |
| Dispositivo 1 - TENSIÓN DC IN 06 (V) | float64 | V | 3 |
| Dispositivo 1 - CORRIENTE DC IN 06 (A) | float64 | A | 3 |
| Dispositivo 1 - POTENCIA DC IN 06 (kW) | float64 | kW | 3 |
| Inversor 1 - HORAS DE FUNCIONAMIENTO (h) | float64 | h | 196 |
| Inversor 1 - TEMPERATURA INT (degC) | float64 | degC | 3 |
| Inversor 1 - RESISTENCIA AISLAMIENTO (Ohm) | float64 | Ohm | 3 |
| Inversor 1 - SETPOINT RELATIVO POTENCIA ACTIVA (%) | float64 | % | 3 |
| Inversor 1 - SETPOINT RELATIVO POTENCIA REACTIVA (%) | float64 | % | 3 |
| Inversor 1 - SMA NUMERO DE SERIE | float64 | sense unitat / metadada | 3 |
| Inversor 1 - SMA ESTADO | float64 | sense unitat / metadada | 3 |
| Inversor 1 - SMA CONDICION | float64 | sense unitat / metadada | 3 |
| Inversor 2 - MARCA | float64 | sense unitat / metadada | 3 |
| Inversor 2 - MODELO | float64 | sense unitat / metadada | 3 |
| Inversor 2 - ESTADO COM | float64 | sense unitat / metadada | 3 |
| Inversor 2 - CALIDAD COM | float64 | escala 0–100 segons guia | 3 |
| Inversor 2 - NUMERO DE PREGUNTAS | float64 | sense unitat / metadada | 4 |
| Inversor 2 - NUMERO DE FALLOS | float64 | sense unitat / metadada | 69108 |
| Inversor 2 - FECHA ULTIMA LECTURA | float64 | marca temporal auxiliar | 3 |
| Inversor 2 - DURACION ULTIMO MUESTREO (s) | float64 | s | 3 |
| Inversor 2 - ENERGIA ACTIVA (kWh) | float64 | kWh | 4422 |
| Inversor 2 - POTENCIA ACTIVA (kW) | float64 | kW | 3 |
| Inversor 2 - POTENCIA ACTIVA FASE 1 (kW) | float64 | kW | 3 |
| Inversor 2 - POTENCIA ACTIVA FASE 2 (kW) | float64 | kW | 3 |
| Inversor 2 - POTENCIA ACTIVA FASE 3 (kW) | float64 | kW | 3 |
| Inversor 2 - POTENCIA REACTIVA (kVAr) | float64 | kVAr | 3 |
| Inversor 2 - POTENCIA REACTIVA FASE 1 (kVAr) | float64 | kVAr | 3 |
| Inversor 2 - POTENCIA REACTIVA FASE 2 (kVAr) | float64 | kVAr | 3 |
| Inversor 2 - POTENCIA REACTIVA FASE 3 (kVAr) | float64 | kVAr | 3 |
| Inversor 2 - POTENCIA APARENTE (kVA) | float64 | kVA | 3 |
| Inversor 2 - POTENCIA APARENTE FASE 1 (kVA) | float64 | kVA | 3 |
| Inversor 2 - POTENCIA APARENTE FASE 2 (kVA) | float64 | kVA | 3 |
| Inversor 2 - POTENCIA APARENTE FASE 3 (kVA) | float64 | kVA | 3 |
| Inversor 2 - TENSIÓN AC FASE 1-N (V) | float64 | V | 3 |
| Inversor 2 - TENSIÓN AC FASE 2-N (V) | float64 | V | 3 |
| Inversor 2 - TENSIÓN AC FASE 3-N (V) | float64 | V | 3 |
| Inversor 2 - CORRIENTE AC (A) | float64 | A | 3 |
| Inversor 2 - CORRIENTE AC FASE 1 (A) | float64 | A | 3 |
| Inversor 2 - CORRIENTE AC FASE 2 (A) | float64 | A | 3 |
| Inversor 2 - CORRIENTE AC FASE 3 (A) | float64 | A | 3 |
| Inversor 2 - FRECUENCIA (Hz) | float64 | Hz | 3 |
| Inversor 2 - TENSIÓN DC (V) | float64 | V | 3 |
| Inversor 2 - CORRIENTE DC (A) | float64 | A | 3 |
| Inversor 2 - POTENCIA DC (kW) | float64 | kW | 3 |
| Inversor 2 - TENSIÓN DC IN 01 (V) | float64 | V | 3 |
| Inversor 2 - CORRIENTE DC IN 01 (A) | float64 | A | 3 |
| Inversor 2 - POTENCIA DC IN 01 (kW) | float64 | kW | 3 |
| Inversor 2 - TENSIÓN DC IN 02 (V) | float64 | V | 3 |
| Inversor 2 - CORRIENTE DC IN 02 (A) | float64 | A | 3 |
| Inversor 2 - POTENCIA DC IN 02 (kW) | float64 | kW | 3 |
| Inversor 2 - TENSIÓN DC IN 03 (V) | float64 | V | 3 |
| Inversor 2 - CORRIENTE DC IN 03 (A) | float64 | A | 3 |
| Inversor 2 - POTENCIA DC IN 03 (kW) | float64 | kW | 3 |
| Inversor 2 - TENSIÓN DC IN 04 (V) | float64 | V | 3 |
| Inversor 2 - CORRIENTE DC IN 04 (A) | float64 | A | 3 |
| Inversor 2 - POTENCIA DC IN 04 (kW) | float64 | kW | 3 |
| Dispositivo 2 - TENSIÓN DC IN 05 (V) | float64 | V | 3 |
| Dispositivo 2 - CORRIENTE DC IN 05 (A) | float64 | A | 3 |
| Dispositivo 2 - POTENCIA DC IN 05 (kW) | float64 | kW | 3 |
| Dispositivo 2 - TENSIÓN DC IN 06 (V) | float64 | V | 3 |
| Dispositivo 2 - CORRIENTE DC IN 06 (A) | float64 | A | 3 |
| Dispositivo 2 - POTENCIA DC IN 06 (kW) | float64 | kW | 3 |
| Inversor 2 - HORAS DE FUNCIONAMIENTO (h) | float64 | h | 196 |
| Inversor 2 - TEMPERATURA INT (degC) | float64 | degC | 3 |
| Inversor 2 - RESISTENCIA AISLAMIENTO (Ohm) | float64 | Ohm | 3 |
| Inversor 2 - SETPOINT RELATIVO POTENCIA ACTIVA (%) | float64 | % | 3 |
| Inversor 2 - SETPOINT RELATIVO POTENCIA REACTIVA (%) | float64 | % | 3 |
| Inversor 2 - SMA NUMERO DE SERIE | float64 | sense unitat / metadada | 3 |
| Inversor 2 - SMA ESTADO | float64 | sense unitat / metadada | 3 |
| Inversor 2 - SMA CONDICION | float64 | sense unitat / metadada | 3 |
| Inversor 3 - MARCA | float64 | sense unitat / metadada | 3 |
| Inversor 3 - MODELO | float64 | sense unitat / metadada | 3 |
| Inversor 3 - ESTADO COM | float64 | sense unitat / metadada | 3 |
| Inversor 3 - CALIDAD COM | float64 | escala 0–100 segons guia | 3 |
| Inversor 3 - NUMERO DE PREGUNTAS | float64 | sense unitat / metadada | 4 |
| Inversor 3 - NUMERO DE FALLOS | float64 | sense unitat / metadada | 66963 |
| Inversor 3 - FECHA ULTIMA LECTURA | float64 | marca temporal auxiliar | 3 |
| Inversor 3 - DURACION ULTIMO MUESTREO (s) | float64 | s | 3 |
| Inversor 3 - ENERGIA ACTIVA (kWh) | float64 | kWh | 3159 |
| Inversor 3 - POTENCIA ACTIVA (kW) | float64 | kW | 3 |
| Inversor 3 - POTENCIA ACTIVA FASE 1 (kW) | float64 | kW | 3 |
| Inversor 3 - POTENCIA ACTIVA FASE 2 (kW) | float64 | kW | 3 |
| Inversor 3 - POTENCIA ACTIVA FASE 3 (kW) | float64 | kW | 3 |
| Inversor 3 - POTENCIA REACTIVA (kVAr) | float64 | kVAr | 3 |
| Inversor 3 - POTENCIA REACTIVA FASE 1 (kVAr) | float64 | kVAr | 3 |
| Inversor 3 - POTENCIA REACTIVA FASE 2 (kVAr) | float64 | kVAr | 3 |
| Inversor 3 - POTENCIA REACTIVA FASE 3 (kVAr) | float64 | kVAr | 3 |
| Inversor 3 - POTENCIA APARENTE (kVA) | float64 | kVA | 3 |
| Inversor 3 - POTENCIA APARENTE FASE 1 (kVA) | float64 | kVA | 3 |
| Inversor 3 - POTENCIA APARENTE FASE 2 (kVA) | float64 | kVA | 3 |
| Inversor 3 - POTENCIA APARENTE FASE 3 (kVA) | float64 | kVA | 3 |
| Inversor 3 - TENSIÓN AC FASE 1-N (V) | float64 | V | 3 |
| Inversor 3 - TENSIÓN AC FASE 2-N (V) | float64 | V | 3 |
| Inversor 3 - TENSIÓN AC FASE 3-N (V) | float64 | V | 3 |
| Inversor 3 - CORRIENTE AC (A) | float64 | A | 3 |
| Inversor 3 - CORRIENTE AC FASE 1 (A) | float64 | A | 3 |
| Inversor 3 - CORRIENTE AC FASE 2 (A) | float64 | A | 3 |
| Inversor 3 - CORRIENTE AC FASE 3 (A) | float64 | A | 3 |
| Inversor 3 - FRECUENCIA (Hz) | float64 | Hz | 3 |
| Inversor 3 - TENSIÓN DC (V) | float64 | V | 3 |
| Inversor 3 - CORRIENTE DC (A) | float64 | A | 3 |
| Inversor 3 - POTENCIA DC (kW) | float64 | kW | 3 |
| Inversor 3 - TENSIÓN DC IN 01 (V) | float64 | V | 3 |
| Inversor 3 - CORRIENTE DC IN 01 (A) | float64 | A | 3 |
| Inversor 3 - POTENCIA DC IN 01 (kW) | float64 | kW | 3 |
| Inversor 3 - TENSIÓN DC IN 02 (V) | float64 | V | 3 |
| Inversor 3 - CORRIENTE DC IN 02 (A) | float64 | A | 3 |
| Inversor 3 - POTENCIA DC IN 02 (kW) | float64 | kW | 3 |
| Inversor 3 - TENSIÓN DC IN 03 (V) | float64 | V | 3 |
| Inversor 3 - CORRIENTE DC IN 03 (A) | float64 | A | 3 |
| Inversor 3 - POTENCIA DC IN 03 (kW) | float64 | kW | 3 |
| Inversor 3 - TENSIÓN DC IN 04 (V) | float64 | V | 3 |
| Inversor 3 - CORRIENTE DC IN 04 (A) | float64 | A | 3 |
| Inversor 3 - POTENCIA DC IN 04 (kW) | float64 | kW | 3 |
| Dispositivo 3 - TENSIÓN DC IN 05 (V) | float64 | V | 3 |
| Dispositivo 3 - CORRIENTE DC IN 05 (A) | float64 | A | 3 |
| Dispositivo 3 - POTENCIA DC IN 05 (kW) | float64 | kW | 3 |
| Dispositivo 3 - TENSIÓN DC IN 06 (V) | float64 | V | 3 |
| Dispositivo 3 - CORRIENTE DC IN 06 (A) | float64 | A | 3 |
| Dispositivo 3 - POTENCIA DC IN 06 (kW) | float64 | kW | 3 |
| Inversor 3 - HORAS DE FUNCIONAMIENTO (h) | float64 | h | 197 |
| Inversor 3 - TEMPERATURA INT (degC) | float64 | degC | 3 |
| Inversor 3 - RESISTENCIA AISLAMIENTO (Ohm) | float64 | Ohm | 3 |
| Inversor 3 - SETPOINT RELATIVO POTENCIA ACTIVA (%) | float64 | % | 3 |
| Inversor 3 - SETPOINT RELATIVO POTENCIA REACTIVA (%) | float64 | % | 3 |
| Inversor 3 - SMA NUMERO DE SERIE | float64 | sense unitat / metadada | 3 |
| Inversor 3 - SMA ESTADO | float64 | sense unitat / metadada | 3 |
| Inversor 3 - SMA CONDICION | float64 | sense unitat / metadada | 3 |

</details>

<details>
<summary>precio_pvpc.csv</summary>

| Columna | Tipus llegit | Unitat / classe | Nuls |
| --- | --- | --- | --- |
| Fecha | datetime sense zona | hora local, sense offset | 0 |
| precio_eur_per_kwh | float64 | €/kWh | 0 |
| precio_eur_per_mwh | float64 | €/MWh | 0 |

</details>

<details>
<summary>co2_red.csv</summary>

| Columna | Tipus llegit | Unitat / classe | Nuls |
| --- | --- | --- | --- |
| Fecha | datetime sense zona | hora local, sense offset | 0 |
| co2_kg_per_kwh | float64 | kg CO₂/kWh | 0 |
| porcentaje_con_emisiones | float64 | % | 0 |
| gen_con_emisiones_mw | float64 | MW | 0 |
| gen_sin_emisiones_mw | float64 | MW | 0 |

</details>

<details>
<summary>meteo.csv</summary>

| Columna | Tipus llegit | Unitat / classe | Nuls |
| --- | --- | --- | --- |
| Fecha | datetime sense zona | hora local, sense offset | 0 |
| Medida | int64 | sense unitat / metadada | 0 |
| Atersa - MARCA | float64 | sense unitat / metadada | 3 |
| Atersa - MODELO | float64 | sense unitat / metadada | 3 |
| Atersa - ESTADO COM | float64 | sense unitat / metadada | 3 |
| Atersa - CALIDAD COM | float64 | escala 0–100 segons guia | 3 |
| Atersa - NUMERO DE PREGUNTAS | float64 | sense unitat / metadada | 2 |
| Atersa - NUMERO DE FALLOS | float64 | sense unitat / metadada | 74210 |
| Atersa - FECHA ULTIMA LECTURA | float64 | marca temporal auxiliar | 3 |
| Atersa - DURACION ULTIMO MUESTREO (s) | float64 | s | 3 |
| Atersa - TEMPERATURA AMBIENTE (SENSOR 1) (ºC) | float64 | ºC | 3 |
| Atersa - TEMPERATURA PANEL (SENSOR 1) (ºC) | float64 | ºC | 3 |
| Atersa - VELOCIDAD VIENTO (SENSOR 1) (m/s) | float64 | m/s | 3 |
| Atersa - NÚMERO DE SERIE | float64 | sense unitat / metadada | 3 |
| Atersa - IRRADIANCIA (W/m2) | float64 | W/m2 | 3 |
| Atersa - IRRADIANCIA 1 (W/m2) | float64 | W/m2 | 3 |
| Atersa - IRRADIANCIA 2 (W/m2) | float64 | W/m2 | 3 |
| Atersa - ATERSAMET ERROR IRRADIANCIA | float64 | sense unitat / metadada | 3 |
| Atersa - ATERSAMET ALARMA | float64 | sense unitat / metadada | 3 |
| Atersa - HORAS SOL PICO (h) | float64 | h | 2 |

</details>

<details>
<summary>entradas_salidas.csv</summary>

| Columna | Tipus llegit | Unitat / classe | Nuls |
| --- | --- | --- | --- |
| Fecha | datetime sense zona | hora local, sense offset | 0 |
| Medida | int64 | sense unitat / metadada | 0 |
| IoLogik 1214 - MARCA | float64 | sense unitat / metadada | 3 |
| IoLogik 1214 - MODELO | float64 | sense unitat / metadada | 3 |
| IoLogik 1214 - ESTADO COM | float64 | sense unitat / metadada | 3 |
| IoLogik 1214 - CALIDAD COM | float64 | escala 0–100 segons guia | 3 |
| IoLogik 1214 - NUMERO DE PREGUNTAS | float64 | sense unitat / metadada | 2 |
| IoLogik 1214 - NUMERO DE FALLOS | float64 | sense unitat / metadada | 66348 |
| IoLogik 1214 - FECHA ULTIMA LECTURA | float64 | marca temporal auxiliar | 3 |
| IoLogik 1214 - DURACION ULTIMO MUESTREO (s) | float64 | s | 3 |
| IoLogik 1214 - SALIDA RELE 0 | float64 | estat binari segons guia | 3 |
| IoLogik 1214 - MARCA.1 | float64 | sense unitat / metadada | 74210 |
| IoLogik 1214 - MODELO.1 | float64 | sense unitat / metadada | 74210 |
| IoLogik 1214 - ESTADO COM.1 | float64 | sense unitat / metadada | 74210 |
| IoLogik 1214 - CALIDAD COM.1 | float64 | escala 0–100 segons guia | 74210 |
| IoLogik 1214 - NUMERO DE PREGUNTAS.1 | float64 | sense unitat / metadada | 74210 |
| IoLogik 1214 - NUMERO DE FALLOS.1 | float64 | sense unitat / metadada | 74210 |
| IoLogik 1214 - FECHA ULTIMA LECTURA.1 | float64 | marca temporal auxiliar | 74210 |
| IoLogik 1214 - DURACION ULTIMO MUESTREO (s).1 | float64 | sense unitat / metadada | 74210 |
| IoLogik 1214 - SALIDA RELE 0.1 | float64 | estat binari segons guia | 74210 |

</details>
