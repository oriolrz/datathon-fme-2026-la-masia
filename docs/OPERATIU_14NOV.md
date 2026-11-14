# Pla operatiu — dissabte 14/11/2026, 12:25 → 15:00 i incorporació del Dani

**Supòsit operatiu:** si el grup confirma UPC Sostenible, ens hi centrem i preparem també la Side Challenge Tukey. Si no, **no començar cap solució del repte** fins escollir-lo. 
**Prioritat:** submissió segura > validació temporal > millores estadístiques > dashboard coherent > estètica.

## Agenda amb punts de control

| Hora (Barcelona) | Oriol | Cesc | David | Resultat esperat |
|---|---|---|---|---|
| **12:25–12:40** | Confirmar repte i pactar propietat de fitxers; clonar/actualitzar | Obre ZIP oficial en local; prepara entorn de dades | Obre repo i instruccions de Claude | 3 entorns connectats; decisions anotades |
| **12:40–13:25** | Recuperar prototip i starter; executar el validador i baseline | Revisar dades, calendari, nuls, salts i agregació horària | Crear estructura de dashboard que consumeixi mètriques reals | Baseline estable + informe EDA + dashboard mínim |
| **13:25–14:10** | Integració i proves de SOC extrem, format ZIP i runtime; si és estable, dry-run de 48h | Especificar holdout temporal i generar mètriques comparables | Primeres 3 visualitzacions útils i etiquetades | Proves reals, primeres comparatives i gràfics |
| **14:10–14:40** | Comprovar que `main` / PR estable; enregistrar resultats | Lliurar resum quantitatiu i eventual predictor baseline | Millorar explicacions orientades a decisions i fixar requisits Tukey | Una versió funcional, sense bloquejos per al Dani |
| **14:40–15:00** | Actualitzar relleu, decisions, GitHub i pròxim checkpoint | Actualitzar resultats, dades, bloquejos, fitxers | Actualitzar dashboard i captures només de dades reals | `docs/RELLEU_1500.md` complet per al Dani |
| **15:00–15:20** | Traspàs curt i definir interfície | Compartir limitacions de demanda/solar | Mostrar el dashboard i necessitats de mètriques | Dani arrenca en branca pròpia sense repetir exploracions |

**Si un punt crític falla:** prioritzar que existeixi un `agent.py` lliurable, no incrementar la complexitat.

## El que NO s'ha de fer abans de les 15:00
- No delegar dependències urgents al Dani, que encara no hi és.
- No deixar que els tres agents editin `agent.py` simultàniament.
- No gastar 10 intents oficials buscant paràmetres; aprofitar simulador local i dry-run gratuït.
- No elaborar un dashboard amb mètriques de mostra presentades com a resultats reals.
- No dedicar hores a models de forecasting sense demostrar que el forecast canvia decisions.
- No pujar el ZIP de dades, el PIN d'equip, API keys ni registres privats al GitHub.
- No confondre resultats del train (4,26) amb el leaderboard/test ocult.
- No executar comandos destructives a Git sense revisar l'estat.

## Contractes de codi per treballar en paral·lel
- `agent.py`: Oriol manté la classe **BatteryAgent** amb `act(obs:dict)->float`. És l'única interfície que necessita el validador.
- `src/policy.py` o `src/mpc.py`: Dani (a partir de les 15:00), `choose_action(obs,load_forecast=None)->float`.
- `src/forecast.py`: Cesc, `forecast_net_load(obs,horizon=24)->list[float]`, només fent servir informació que l'agent coneixia en aquell moment.
- `src/safety.py`: Oriol, límit de potència/SoC amb `eta=sqrt(0.9)` i `eps`.
- `scripts/evaluate.py` i `scripts/package.py`: Oriol, executar l'entorn i empaquetar **tots** els mòduls necessaris a l'arrel del ZIP si el format d'importació ho exigeix.
- `dashboard/`: David, només consumeix resultats calculats i etiquetats amb període/font/codi.

**Avisos tècnics:** `check_submission.py` fa una prova sintètica de 24 passos, **no un backtest complet**; el dry-run de la web prova 48 hores; el leaderboard només 10 enviaments/dia. El nou model no entrarà a `main` si no passa el mateix banc de proves que la baseline estable.

## Què ha de quedar fet a les 15:00
- [ ] Equip ha confirmat o descartat UPC Sostenible.
- [ ] Tres persones tenen el projecte clònic + agent funcionant.
- [ ] Algorisme base reproduït localment amb score i **0 infraccions** (o problema explícit al relleu).
- [ ] Un sol encarregat del botó de tramesa al leaderboard.
- [ ] Validació web: **resultat real o marcat pendent**. Si falla, enganxar error sense secrets.
- [ ] Registre de dades i salts temporals fet pel Cesc.
- [ ] Dashboard mínim del David amb mètriques reals, no simulades (o bloqueig declarat).
- [ ] `docs/RELLEU_1500.md` complet i publicat amb commit identificable.
- [ ] Dani té un primer issue, fitxers assignats i test que ha de superar.
