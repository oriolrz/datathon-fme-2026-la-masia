# UPC Sostenible — inspecció i proves reals amb el Starter Kit

**Data:** 14/11/2026 · **Estat:** anàlisi i prototip local; **el repte encara no està seleccionat oficialment**.

**Font:** paquet oficial `paquet_participants_datathon_upc.zip` proporcionat per l'equip i plataforma https://repteupc.datathon.cat/ .

## Fitxers inspeccionats

`docs/ENUNCIAT.md`, `docs/GUIA_VARIABLES.md`, `starter_kit/environment.py`, `starter_kit/check_submission.py`, `starter_kit/agent.py`, `starter_kit/tutorial.ipynb`, `starter_kit/battery_spec.json`, i els sis CSV oficials.

**No s'han publicat dades brutes, cap PIN ni cap token a GitHub.**

## Tres descobriments confirmats al codi oficial

1. `CampusBatteryEnv.evaluate_results()`: score final sobre 100 = `max(0, 100*(0.7*dCO2 + 0.3*dCost - 0.002*infraccions))`. Per tant **cada infracció resta 0,20 punts** al resultat final, encara que algunes diapositives/FAQ diguin −1.
2. `CampusBatteryEnv(..., export_price=0.0)` per defecte: **no es remuneren exportacions** al simulador local.
3. `check_submission.py`: valida AST, classe i 24 passos sintètics. **No avalua el score anual** ni garanteix que superi el test ocult.
4. `CampusBatteryEnv._get_obs()` ofereix preus/CO2 de les **24 files següents**; a la pràctica quan hi ha salts de calendari, aquestes 24 files no sempre equivalen a 24 hores consecutives. Vigilar-ho en MPC; cal consultar mentors sobre el motor web.
5. La plantilla usa `rendiment_eta=0.9487`, lleugerament superior a `sqrt(0.9)` en descàrrega. Aquesta diferència pot provocar clipping i infraccions. Per evitar-ho, fer servir `eta=sqrt(0.9)` i restar un petit `epsilon` als límits físics.

## Dades locals inspeccionades

Amb el preprocessament de `tutorial.ipynb`:
- `contador.csv` 74.210 files; `inversor.csv` 71.882 files; `precio_pvpc.csv` 6.768 files; `co2_red.csv` 6.768 files.
- **5.993 hores** amb dades de demanda, solar, preus i CO2 simultànies, de setembre 2025 a agost 2026.
- **Novembre 2025 no apareix** a la sèrie consolidada; hi ha salts entre setmanes i algunes discontinuïtats.
- Demanda mitjana ≈1.115 kW; solar mitjana ≈26,5 kW; generació solar màxima agregada ≈144,1 kW en train.
- Menys del **0,52%** de les hores tenen demanda neta inferior a 500 kW; per tant, en aquestes dades la restricció d'autoconsum no acostuma a impedir descàrregues de 500 kW, excepte en hores anòmales. **El test ocult pot ser diferent**.
- Preu PVPC observat: 0,00327–0,39858 €/kWh; CO2: 0,0279–0,2217 kg/kWh.

## Resultats executats localment (només sobre train, no leaderboard)

Totes les files es processen seqüencialment en el mateix `CampusBatteryEnv`.

| Agent | Score local | Estalvi CO2 | Estalvi cost | Infraccions |
|---|---:|---:|---:|---:|
| Reposar sempre (0 kW) | 0,00 | 0,00% | 0,00% | 0 |
| `BatteryAgent` oficial sense corregir | **0,00** | 0,88% | 2,18% | **46** |
| `BatteryAgent` oficial + clamp precís | **1,27** | 0,88% | 2,18% | **0** |
| Política de llindars de valor 24h, 50% CO2/50% preu normalitzat* | **4,26** | 3,86% | 5,18% | **0** |
| Política de llindars de valor 24h, 70% CO2/30% preu normalitzat* | **4,20** | 4,03% | 4,60% | **0** |
| Política per quantils (25%), 50% CO2/50% preu normalitzat* | **4,19** | 3,71% | 5,31% | **0** |

* S'han provat diversos valors de paràmetres sobre les mateixes dades: **4,26 no és un score de generalització**. La ponderació dins la heurística és un hiperparàmetre, no la fórmula oficial (que continua sent 70/30 i normalitza per les bases respectives).

La política de llindars 0,20/0,50 és simple: valora cada hora del pronòstic 24h per CO2 i preu dividits per llurs mitjanes, carrega si l'hora actual és prou favorable i existeix una hora futura prou pitjor per compensar el 10% de pèrdua, descarrega en el cas oposat, i aplica un clamp físic exacte.

El prototip de `agent.py` executat **ha superat** l'escàner de seguretat, el test tècnic de 24 passos i una simulació completa sobre 5.993 hores en **aprox. 0,56 s** en un entorn local. **No s'ha enviat al leaderboard**.

### Estabilitat descriptiva segons subperíodes

| Agent | Setembre–febrer (2.784 h) | Març–agost (3.209 h) |
|---|---:|---:|
| Referència amb clamp | 1,13 | 1,40 |
| Llindars 0,20/0,50 | 3,40 | 5,07 |

Aquests subperíodes **no són holdouts independents** perquè ja s'han consultat les xifres del conjunt complet. Per calibrar la generalització cal fer un protocol de validació temporal estricte abans de triar la versió final.

## Recomanació tècnica immediata

1. **Confirmar la selecció del repte amb l'equip.** UPC Sostenible és el millor encaix tècnic actual; Tinybird segueix sense enunciat confirmat.
2. Si l'escolliu, copiar l'Starter Kit a una **branca específica**, sense dades sensibles al GitHub, i guardar-hi el prototip en revisió (no substituir `main` sense acord).
3. Fer dry-run web de 48h; no consumeix quota. **No trametre al leaderboard** fins que el grup decideixi i l'agent tingui comprovacions de regressió.
4. Millorar amb MPC/optimització 24h, però controlar cost computacional del càlcul repetit fins a 2.016 hores dins el timeout de 60s.
5. Validació temporal de múltiples setmanes/mesos, score + emissions + cost + infraccions + latència, i tests de dades incompletes.
6. Confirmar amb mentors discrepàncies de score, exportació, discontinuïtats i mida/hora límit del test.

**Avís de comparació:** un score local elevat no garanteix ni la mateixa puntuació al test privat ni una posició concreta al rànquing.
