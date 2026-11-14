# Repte candidat — UPC Sostenible x AED: Control de la bateria

**Revisat:** 14/11/2026 · **Estat:** candidat favorit provisional, NO seleccionat per l'equip.  
**Plataforma:** https://repteupc.datathon.cat/  
**Font addicional:** diapositives oficials compartides per l'equip, «Còpia de UPC Sostenible.pdf» (9 pàgines).  
**Nota:** la plataforma s'ha pogut llegir al navegador connectat; el ZIP de 13 MB (Starter Kit) **encara no s'ha analitzat**. Abans de codificar, inspeccionar `environment.py`, `check_submission.py` i les dades.

## Objectiu verificat

Implementar `agent.py` amb classe `BatteryAgent` i mètode `act(obs: dict) -> float`: un valor horari en kW (positiu carrega, negatiu descarrega, zero repòs).

- Bateria: 2.000 kWh, potència de càrrega/descàrrega ±500 kW.
- Eficiència round-trip 90% (per cada sentit, aproximadament `eta = sqrt(0.9)`).
- SOC inicial 50% = 1.000 kWh; es conserva entre dies, no es reinicia diàriament.
- Balanç: `P_xarxa = P_demanda - P_solar + P_bateria`.
- Sense degradació declarada; evitar exportar energia per descàrrega perquè, segons la FAQ, no es remunera ni estalvia CO2.
- L'agent disposa del preu i CO2 actuals i de previsions futures per a 24h; no disposa directament de demanda/solar futures.
- Observacions: `timestamp`, `hour`, `day_of_week`, `soc_kwh`, `soc_pct`, `preu_actual`, `co2_actual`, `preus_properes_24h`, `co2_properes_24h`, `noves_dades_5min` amb `ultim_consum_kw` i `ultima_solar_kw`.

## Puntuació

La plataforma (secció 5) declara:

```
Score = max(0, 0.70 * Delta_CO2_pct + 0.30 * Delta_Cost_pct - 0.20 * infraccions)
```

Les reduccions són respecte al campus **sense bateria**. El leaderboard és orientatiu, i el jurat també pondera la presentació final, les decisions tècniques i l'anàlisi.

**Discrepàncies a confirmar amb organitzadors / codi del simulador:**
1. Penalització: **−0,20** per infracció a la fórmula de la plataforma i secció «Safety Clamp», però **−1,00** a les diapositives (p. 5) i a una FAQ. Prioritat: **zero infraccions**.
2. Exportació: la secció de balanç de la web menciona **0,04 €/kWh** per excedent solar; la FAQ afirma **`export_price = 0.0`**. Prioritat: no descarregar mai per exportar, fins verificar `environment.py`.
3. Durada del test: la web parla de **2.016 hores** en 12 setmanes i del leaderboard de **1.008 hores públiques**; les diapositives parlen d'uns **1.700 h**. Verificar el motor real.
4. Estan disponibles **previsions de preus i CO2** (futur), però no **previsions de càrrega ni solar**. Els registres de telemetria de la «darrera hora» no són una mesura del futur.
5. L'ordre de setmanes de test i els salts entre mesos poden afectar variables retardades; controlar `timestamp`.

## Dades i entorn

La web presenta el ZIP oficial de **13 MB**, amb:
- Sèries `contador.csv`, `inversor.csv`, `meteo.csv`, `entradas_salidas.csv`, `precio_pvpc.csv`, `co2_red.csv`.
- Unes 6.000 hores de training, primeres ~3 setmanes de cada mes de setembre 2025 a agost 2026; test en últimes setmanes mensuals.
- `starter_kit/tutorial.ipynb`, `starter_kit/agent.py`, `starter_kit/environment.py`, `starter_kit/check_submission.py`, documentació de variables.
- Comptador invertit: consum positiu = negatiu del camp `Contador - POTENCIA ACTIVA EXPORTADA (kW)`.
- Agregar telemetria de 5/15 minuts a 1 hora amb definicions correctes (potència mitjana i unitats).
- Màxim **10 trameses al leaderboard per equip/dia**. El **dry-run web de 48 hores és gratuït i il·limitat** i no consumeix aquests intents.
- Test amb **50% públic / 50% privat**. No sobreajustar al leaderboard públic.
- `agent.py` o `submission.zip` (model `.pkl` + agent, rutes relatives), màxim **25 MB**.
- Timeout de **60 segons per execució**; cal verificar a l'Starter Kit si és temps global de tota la simulació.
- Mòduls autoritzats: numpy, pandas, scipy, sklearn, joblib, xgboost, lightgbm i estàndards indicats. AST denega network/system/dynamic execution. Evitar imports prohibits.
- Nom d'equip, PIN privat i integrants al primer lliurament; **no versionar el PIN**.

## Estratègia proposada (pendent de codi i dades)

1. **Clonar l'Starter Kit i executar baseline**. Confirmar que el simulador local és equivalent al servidor.
2. **Safety clamp obligatori** abans de retornar qualsevol acció:
   `eta = sqrt(.9)`;
   `max_charge = min(500, (2000-soc)/eta - eps)`;
   `max_discharge = min(500, soc*eta - eps)`.
   Retornar dins `[-max_discharge, +max_charge]`; respectar signes i potència. No descarregar per sota de la demanda neta estimada, si no es remunera exportar.
3. **Baseline de decisions**: comparar sempre `0`, heurística oficial, i una regla econòmica+CO2 basada en previsions 24h.
4. **Horitzó mòbil (MPC)**: cada hora, triar `action_t` amb previsió a 24h, restriccions de bateria i cost de xarxa ponderat. **No optimitzar només els preus**, el CO2 té pes 70%.
5. **Forecast de demanda/solar**: començar amb calendaris i lags segurs; provar LightGBM/XGBoost només si la validació temporal supera una baseline simple. Guardar model lleuger.
6. **Mètrica normalitzada**: valorar emissions i cost en percentatge respecte a les respectives bases. En una aproximació lineal i sense exportació, el cost marginal horari és proporcional a `0.7*CO2_t/E0 + 0.3*price_t/C0`, on E0 i C0 són les bases totals del període. **Verificar al simulador com es tracten tarifes negatives i exportació**.
7. **Backtesting temporal**: separar setmanes i mesos, no fer train/test aleatori; analitzar score/CO2/cost/infraccions/SOC i desviació de prevenció de fuga temporal.
8. **Pressupost computacional**: els optimitzadors per hora han de ser prou lleugers perquè tota la simulació entri en el timeout. Mesurar amb el simulador local abans d'enviar.

## Repartiment inicial possible

| Persona | Àrea | Primer lliurable |
|---|---|---|
| Oriol | Integració, simulador, score, safety clamp | Baseline reproduïble i cap infracció |
| Cesc | Exploració estadística i predicció | Forecast de demanda/solar amb mètriques temporals |
| Dani | Optimització / MPC | Política 24h que superi la baseline |
| David | Evaluació, ablations i pitch | Taula de resultats, visualització i relat |

**Important:** rols **no assignats encara**; cal acord de l'equip. De moment no copiar una implementació al `main` sense escollir repte.

## Comparació provisional de viabilitat

- **UPC Sostenible**: millor encaix tècnic amb l'equip (Python, estadística, optimització), sense hardware, avaluador objectiu, dades + starter. **Favorit actual**.
- **Qualcomm**: interessant però dependència crítica de configurar Arduino UNO Q i models, OCR i 60 s per pregunta, demo i Project Hub públic.
- **Tinybird / RawTree**: enunciat no llegit de forma verificable; no fingir comparació final.

## Proper pas

1. Descarregar el ZIP de la plataforma i inspeccionar `environment.py` i `check_submission.py`.
2. Confirmar les discrepàncies preguntant als mentors.
3. Decidir un únic repte; si és UPC Sostenible, completar `docs/BRIEF.md` i crear tasques independents.
