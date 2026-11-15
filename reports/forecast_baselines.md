# Baselines causals de demanda neta — issue #3

Cesc · La MasIA · 14/11/2026 · `feat/cesc-forecast`. Target oficial conservat: `load_kw - pv_kw`, sense retocar zeros, clipping ni agregació del tutorial. La qüestió física PCC/solar continua pendent dels mentors; s'avalua el contracte local.

## Protocol congelat abans de comparar

| Partició | Dates (final exclusiu) | Hores | Ús |
| --- | --- | --- | --- |
| Train | 2025-09-01 → 2026-03-01 | 2784 | Únic ajust de perfils, fallback, clip i IQR |
| Validació | 2026-03-01 → 2026-06-01 | 1704 | Comparació de tres candidats prefixats |
| Reserva retrospectiva | 2026-06-01 → 2026-09-01 | 1505 | Exclosa abans de construir targets; sense mètriques ni selecció |

No hi ha aleatorietat ni cal llavor. La selecció usa MAE mitjà dels 24 horitzons sobre les mateixes finestres completes. No s'ha fet cerca d'hiperparàmetres. La reserva ja havia aparegut en l'auditoria i en ajustos previs de polítiques: no es pot anomenar test històricament intacte.

## Contracte temporal i inferència

**Alineament confirmat explícitament per Cesc:** incloure l'hora actual, t…t+23. `forecast_net_load(obs, horizon)[k]` retorna demanda neta en kW a `obs['timestamp'] + k hores`. En les taules, h=1, 6 i 24 són posicions del vector: t, t+5 i t+23. No són desplaçaments de +1, +6 i +24 hores des de la decisió. Amb telemetria recent de t−1 equivalen a 1, 6 i 24 hores des de l'última dada observable; aquesta equivalència no val al primer pas ni després d'un salt. Es conserva l'alineament de l'auditoria i es purguen 23 orígens al final de cada bloc.

Les hores són cronològiques, no posicions de fila. Amb timestamps amb zona, l'avenç és en temps UTC i després es recupera el calendari local. Els CSV oficials són locals sense zona: no es pot reconstruir DST si l'organització no dona offsets. Les transicions no apareixen en els blocs usats. Els vectors oficials de preu/CO₂ també comencen a t, però poden travessar salts: només es poden emparellar per índex amb aquesta sortida si es verifica continuïtat horària. Com que obs no ofereix timestamps futurs per element, no es poden detectar de manera general els salts futurs des de l'agent. Cal aclarir aquest límit amb mentors abans d'integrar-los en un optimitzador.

La primera crida ignora sempre `noves_dades_5min`; en crides posteriors s'atribueix el payload al timestamp de la decisió anterior. A pot retenir una mesura antiga després d'un salt; C descarta la correcció antiga i torna a B. Cap model llegeix demanda actual, meteorologia, qualitat COM o targets futurs del CSV en inferència. B només necessita calendari; A i C necessiten una instància seqüencial amb memòria de les crides anteriors.

## Models fixats

- **A — Persistència:** vector constant amb l'últim `ultim_consum_kw - ultima_solar_kw` finit realment observable. Si no n'hi ha, mediana global del train. Manté valors baixos o zeros observats; una telemetria absent no es converteix en zero.
- **B — Perfil robust:** mediana del target per (dia de setmana, hora), calculada només sobre train. Si falta una cel·la, mediana per hora i després mediana global del train.
- **C — Perfil corregit:** B més la mediana dels residus de fins a les últimes 3 hores observades, amb clip simètric al quantil 95% de |residu| del train. La correcció decau amb semivida fixa de 6 h segons l'edat de la telemetria i l'horitzó. Després d'un salt o sense residus recents vàlids, retorna B. Ni 3, ni 6, ni 95% s'han triat mirant validació.

Mediana global: 1072.166667 kW. Clip del residu: ±335.195833 kW. Mostres per cel·la setmanal: 15–17. Els paràmetres agregats queden incrustats a `src/forecast.py`; no cal cap CSV, model binari ni fitxer auxiliar per fer inferència. No es reentrena automàticament amb validació.

## Finestres avaluades i excloses

| Bloc de validació | Inici | Final | Hores | Finestres completes 24 h |
| --- | --- | --- | --- | --- |
| 1 | 2026-03-01 00:00:00 | 2026-03-24 23:00:00 | 576 | 553 |
| 2 | 2026-04-01 00:00:00 | 2026-04-23 23:00:00 | 552 | 529 |
| 3 | 2026-05-01 00:00:00 | 2026-05-24 23:00:00 | 576 | 553 |

1704 orígens candidats, **1635 finestres completes avaluades** i **69 excloses** per travessar el final d'un bloc/partició. Tots els models i els horitzons de la taula principal comparteixen aquests orígens; no se suprimeixen hores sospitoses per millorar les mètriques. El predictor continua rebent les 1704 observacions en ordre, inclosos els orígens exclosos de puntuació.

| h (posició) | Orígens si s'avalua aquest h sol | Exclosos per a aquest h | Orígens a la comparació principal |
| --- | --- | --- | --- |
| 1 | 1704 | 0 | 1635 |
| 6 | 1689 | 15 | 1635 |
| 24 | 1635 | 69 | 1635 |

## MAE i RMSE de validació (kW)

| Model | h (posició) | N | MAE kW | RMSE kW |
| --- | --- | --- | --- | --- |
| A | 1 | 1635 | 32.585339 | 55.305530 |
| A | 6 | 1635 | 137.326670 | 188.273889 |
| A | 24 | 1635 | 157.255211 | 255.342509 |
| B | 1 | 1635 | 106.527971 | 170.259290 |
| B | 6 | 1635 | 106.745097 | 170.305310 |
| B | 24 | 1635 | 100.698568 | 156.412410 |
| C | 1 | 1635 | 54.432408 | 98.509759 |
| C | 6 | 1635 | 99.076518 | 150.836647 |
| C | 24 | 1635 | 96.486273 | 151.295741 |

| Model | Parelles origen/horitzó | MAE de les 24 h | RMSE de les 24 h | Temps de 1704 inferències (s) |
| --- | --- | --- | --- | --- |
| A | 39240 | 162.986449 | 227.805589 | 0.246817 |
| B | 39240 | 104.483218 | 164.770555 | 1.270014 |
| C | 39240 | 95.551298 | 149.675131 | 1.326304 |

Millor MAE per horitzó: h=1: A; h=6: C; h=24: C. C redueix el MAE del vector complet un 8.55% respecte de B i un 41.37% respecte d'A. La recomanació global no implica dominar tots els horitzons ni tots els mesos.

Les mètriques de les 24 h inclouen tots els h=1…24; MAE i RMSE són mitjanes sobre les mateixes parelles origen/horitzó, sense ponderar per energia. Les finestres se superposen: no són mostres independents i no s'ha inferit significació estadística.

| Mes | Model | Finestres | MAE de les 24 h | RMSE de les 24 h |
| --- | --- | --- | --- | --- |
| 2026-03 | A | 553 | 192.062543 | 259.327211 |
| 2026-03 | B | 553 | 59.563416 | 80.055803 |
| 2026-03 | C | 553 | 58.797999 | 78.386362 |
| 2026-04 | A | 529 | 128.053836 | 183.297605 |
| 2026-04 | B | 529 | 156.423721 | 237.495070 |
| 2026-04 | C | 529 | 136.985209 | 213.268556 |
| 2026-05 | A | 553 | 167.326905 | 232.472462 |
| 2026-05 | B | 553 | 99.716716 | 141.084389 |
| 2026-05 | C | 553 | 92.668902 | 128.770089 |

## Casos problemàtics: diagnòstic separat

Validació conté 0 hores sospitoses segons zeros/qualitat COM/límits i 0 hores amb menys de 12 mostres vàlides de comptador o dels tres inversors. N=0 es mostra com a «—»: no hi ha evidència de rendiment en aquest grup. No s'ha obert la reserva per omplir grups absents. A més, es marca el target fora de l'IQR del train: [44.454063, 2119.863229] kW. Aquests indicadors s'utilitzen només per desglossar errors, mai com a features ni com a filtres sobre la puntuació principal. Les cohorts es poden superposar.

| Cohort sense casos | N per model i horitzó | MAE/RMSE |
| --- | --- | --- |
| Target sospitós (zeros/qualitat COM/límit físic) | 0 | No estimables |
| Target atípic segons IQR del train | 0 | No estimables |
| Target amb mostres incompletes | 0 | No estimables |
| Telemetria d'origen sospitosa | 0 | No estimables |
| Telemetria d'origen amb mostres incompletes | 0 | No estimables |

| Cohort | Model | h | N | MAE kW | RMSE kW |
| --- | --- | --- | --- | --- | --- |
| Primera decisió de l'episodi | A | 1 | 1 | 307.166667 | 307.166667 |
| Primera decisió de l'episodi | A | 6 | 1 | 307.166667 | 307.166667 |
| Primera decisió de l'episodi | A | 24 | 1 | 346.166667 | 346.166667 |
| Primera decisió de l'episodi | B | 1 | 1 | 6.000000 | 6.000000 |
| Primera decisió de l'episodi | B | 6 | 1 | 6.000000 | 6.000000 |
| Primera decisió de l'episodi | B | 24 | 1 | 25.000000 | 25.000000 |
| Primera decisió de l'episodi | C | 1 | 1 | 6.000000 | 6.000000 |
| Primera decisió de l'episodi | C | 6 | 1 | 6.000000 | 6.000000 |
| Primera decisió de l'episodi | C | 24 | 1 | 25.000000 | 25.000000 |
| Primera decisió després d'un salt | A | 1 | 2 | 41.000000 | 42.449971 |
| Primera decisió després d'un salt | A | 6 | 2 | 41.000000 | 42.449971 |
| Primera decisió després d'un salt | A | 24 | 2 | 170.000000 | 205.805734 |
| Primera decisió després d'un salt | B | 1 | 2 | 15.000000 | 15.811388 |
| Primera decisió després d'un salt | B | 6 | 2 | 15.000000 | 15.811388 |
| Primera decisió després d'un salt | B | 24 | 2 | 135.000000 | 164.502280 |
| Primera decisió després d'un salt | C | 1 | 2 | 15.000000 | 15.811388 |
| Primera decisió després d'un salt | C | 6 | 2 | 15.000000 | 15.811388 |
| Primera decisió després d'un salt | C | 24 | 2 | 135.000000 | 164.502280 |
| Primeres 3 decisions de cada bloc | A | 1 | 9 | 43.240741 | 104.326071 |
| Primeres 3 decisions de cada bloc | A | 6 | 9 | 122.096852 | 165.952725 |
| Primeres 3 decisions de cada bloc | A | 24 | 9 | 142.240741 | 188.045314 |
| Primeres 3 decisions de cada bloc | B | 1 | 9 | 12.000000 | 13.366625 |
| Primeres 3 decisions de cada bloc | B | 6 | 9 | 131.993518 | 212.155869 |
| Primeres 3 decisions de cada bloc | B | 24 | 9 | 98.111111 | 134.712451 |
| Primeres 3 decisions de cada bloc | C | 1 | 9 | 4.872810 | 7.808543 |
| Primeres 3 decisions de cada bloc | C | 6 | 9 | 127.993518 | 208.462949 |
| Primeres 3 decisions de cada bloc | C | 24 | 9 | 97.611111 | 134.378689 |

Només hi ha dues primeres decisions després de salts dins de validació; el primer pas de l'episodi es compta a part. Aquests recomptes són massa petits per donar una garantia estadística de robustesa. C coincideix amb B a l'instant del salt per disseny, i només torna a corregir quan arriba telemetria recent atribuïble.

## Verificació de causalitat i proves

- Paràmetres invariants en alterar totes les etiquetes de validació.
- Paràmetres invariants en afegir valors sentinella a la reserva (sense consultar-la).
- Prediccions idèntiques fins a l'origen 300 en alterar demanda/solar de t i del futur.
- MAE/RMSE recalculats independentment; finestres enumerades per timestamp.
- AST de src/forecast.py aprovat pel comprovador oficial local (no és un ZIP ni un dry-run).

**17 proves unitàries passades**, a `analysis/test_forecast.py`: alineament temporal, primera observació, salts, idempotència, reset d'episodi, agents independents, telemetria absent/no finita, longituds i inferència amb accés a fitxers desactivat. Els fixtures de prova no es presenten com a dades ni com a mètriques oficials.

## Recomanació i límits

**Model recomanat segons el criteri prefixat: C.** És el valor de `DEFAULT_METHOD` exportat. Aquesta és una selecció sobre març–maig, no una confirmació independent; no s'ha ajustat cap hiperparàmetre després de veure'n el resultat. Menor error de forecasting no demostra millora del score de bateria: falta comparació amb la mateixa política, SOC, període i pressupost de runtime quan l'integrador ho autoritzi.

Limitacions: perfil sense estacionalitat anual ni festius; correcció recent limitada i potencialment afectada per telemetria errònia sense flags de qualitat disponibles; persistència obsoleta després de buits; cohorts de qualitat buides si no hi ha casos en validació; reserva retrospectiva ja inspeccionada històricament; semàntica PCC/solar pendent; estat seqüencial explícit i vectors oficials sense timestamps futurs. No hi ha MPC ni models LightGBM/XGBoost; no s'ha modificat cap política de bateria.

## Integració sense dades

Preferible, una instància per `BatteryAgent`:

```python
from src.forecast import NetLoadForecaster

# A __init__ (un predictor nou per episodi):
self.forecaster = NetLoadForecaster()
# A cada act(obs), també si no es puntua aquest origen:
future_net_kw = self.forecaster.forecast(obs, horizon=24)
# future_net_kw[0] correspon a t; future_net_kw[23], a t+23.
```

Façana requerida, per a un únic episodi actiu:

```python
from src.forecast import forecast_net_load, reset_forecast

reset_forecast()  # abans de cada simulació
future_net_kw = forecast_net_load(obs, horizon=24)
```

Una observació sense timestamp torna al perfil/fallback i reinicia la memòria temporal. `horizon=0` retorna `[]`; valors negatius, booleans o no enters donen `ValueError`. Per dos agents intercalats, usar instàncies pròpies; no compartir la façana global.

## Reproducció i procedència

Paquet local: `C:\Users\cescc\Downloads\paquet_participants_datathon_upc.zip`. Python 3.12.14, pandas 3.0.1, numpy 2.3.5. Hash del target de train: `983c2625463295130880f2f03118c405fc3389a195c91346c118fe8c1980c8eb`.

| CSV font (hash del fitxer complet; reserva exclosa de càlculs) | SHA-256 |
| --- | --- |
| contador.csv | baba32739604b8088c5b1ae322eecfa9790879754d3535bae3525f07ad9296ea |
| inversor.csv | aeb040d267537c6b59176dec48515d352038a104071365abd5604ef1928ea818 |
| precio_pvpc.csv | 73b9bff460d084515f8b1836b90e2299e5a09dd3acd1a55d53a2385a31125249 |
| co2_red.csv | 8f19863ffb65624a84615cfd8fb5800f4d37ea5ddf59123a6fd829a6e2736d65 |

Ordre executada:

```powershell
& 'C:\Program Files\WindowsApps\OpenAI.CodexPrimaryRuntime.v26-1112-611-0_26.1112.611.0_x64__3k8sg7r9htsxt\dependencies\python\python.exe' -B analysis/forecast_baselines.py --kit 'C:\Users\cescc\Downloads\paquet_participants_datathon_upc.zip' --write-model --report
```

Sense `--write-model` i `--report`, l'ordre verifica els paràmetres incrustats i recalcula els resultats sense escriure fitxers. Proves unitàries:

```powershell
& 'C:\Program Files\WindowsApps\OpenAI.CodexPrimaryRuntime.v26-1112-611-0_26.1112.611.0_x64__3k8sg7r9htsxt\dependencies\python\python.exe' -B -m unittest discover -s analysis -p test_forecast.py -v
```

`git diff --check` verifica espais dels fitxers versionats; el comprovador unitari també revisa la sintaxi i el contracte del predictor nou. Només es creen el mòdul, scripts a analysis i aquest informe. Sense commit, push ni merge.
