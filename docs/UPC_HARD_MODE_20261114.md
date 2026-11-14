# 🚨 UPC Sostenible — HARD MODE (anunciat al Discord 14/11/2026)

**Estat:** **prioritat operativa a partir del comunicat**, però els paràmetres i el codi de Hard Mode **encara no s'han executat/validat localment**. **No** considerar cap resultat Standard com a score Hard.  
**Font primària:** captura del missatge del canal `#upc-sostenible` compartida per l'equip, més avís de Staff Datathon a les 15:04. La pestanya «🔥 Hard Mode» de la web conté un snippet per simular localment, però encara **no l'hem llegit ni copiat**. Cal obtenir-lo abans d'implementar.

## 1. Normes confirmades en el comunicat oficial

| Aspecte | Mode Standard | Mode Hard |
|---|---|---|
| Generació solar | Solar original | **solar × 12** |
| Capacitat de bateria | 2.000 kWh | **6.000 kWh** |
| Potència màxima | ±500 kW | **±1.500 kW** |
| Previsions confirmades de preu/CO₂ a `obs` | 24 hores | **només 3 hores** (`preus_properes_24h`, `co2_properes_24h`, noms conservats però longitud 3) |
| Telemetria t−1 | Últimes dades de consum i solar | S'afegeixen `irradiancia_wm2`, `temp_ambient_c`, `temp_panel_c`, `vent_ms` |
| Exportació xarxa | segons motor local 0 €/kWh | explícitament **0 €/kWh** |
| Leaderboard | estàndard existent | **separat**, amb públic/privat i quotes pròpies |
| Trameses | quota de mode estàndard | **2 addicionals per finestra de 4 hores** (confirmar horari exacte de finestra a la pestanya) |

- **Standard continua sense canvis** i els scores ja obtinguts es mantenen.
- Els organitzadors afirmen que Standard ha assolit la màxima prestació de la bateria en el mode públic, però **Staff Datathon a les 15:04 ha aclarit explícitament que ningú ha arribat al màxim en el rànquing privat**.
- Hi ha un **snippet oficial a la pestanya 🔥 Hard Mode** per reproduir la simulació sobre train. **La web no ha estat accessible des d'aquesta sessió per llegir-ne el contingut**, de manera que no podem confirmar encara si hi canvien eficiència, score, estructura de dades, límit temporal, temps d'execució o camps addicionals.

## 2. Implicacions matemàtiques i de dades

1. **La demanda neta pot ser negativa** en hores de gran producció (`load_kw - pv_kw < 0`). En aquest cas, l'energia injectada val **0 €/kWh**, així que pot ser valuós carregar la bateria amb excedent que d'altra manera es desaprofitaria.
2. Bateria de 6 MWh i límit de 1,5 MW: a potència nominal, l'escala de càrrega útil és de ~4 h abans de considerar eficiència. Les **3 h conegudes de preu i CO₂ són més curtes que l'horitzó energètic rellevant**. Optimitzar només tres hores sense valor terminal pot ser miop.
3. **La previsió de càrrega neta ara sí pot modificar les accions**: (a) demanda <1.500 kW limita descàrrega útil; (b) solar > demanda crea excedents; (c) anticipar pics solars determina quant espai deixar a la bateria.
4. L'ús de meteorologia `t−1` pot millorar el forecast de generació fotovoltaica. **No confondre aquesta telemetria amb meteorologia futura coneguda**.
5. **Preus i emissions dels passos 4..24 deixen de ser observables**: necessiten pronòstics causals o escenaris d'incertesa. No usar les columnes futures dels CSV d'entrenament com a input del desplegament.
6. Els normalitzadors del score i el balanç d'importació/exportació han de correspondre exactament al **nou simulador oficial**, sense extrapolar paràmetres de Standard. La física exacta (SOC, potència, eficiència) ha de venir de la nova especificació.
7. El resultat de l'oracle anterior (99,64% sobre train) **només** és vàlid com a diagnòstic del mode Standard, no implica cap límit per al Hard Mode.

## 3. Accions P0 (abans de programar una política nova)

- [ ] Entrar a `https://repteupc.datathon.cat/` → pestanya **🔥 Hard Mode** i **copiar el snippet oficial íntegre** amb la seva ubicació/rutes, paràmetres i instruccions d'entrega.
- [ ] Anotar data i SHA/versionat d'aquest snippet en `docs/UPC_HARD_MODE_SNIPPET_NOTES.md` o adjuntar el codi al repo només si és permès (sense secrets/dades).
- [ ] Executar sobre el ZIP local el **benchmark Hard Mode** exactament segons el snippet; no adaptar `environment.py` «a ull» sense comparar-lo amb el snippet.
- [ ] Congelar i conservar el ZIP **Standard 6,43**, amb SHA-256 `50b1a794711d2221855147e44c6be8fc33c9221a9b0bbe258f0f84675721752f`, i publicar-ne el codi del commit local encara pendent amb revisió. **No tocar el PR #6 pensant que conté el MPC:** aquell PR és l'agent antic de 4,03.
- [ ] Registrar un **score Hard baseline** i percentatges amb 0 infraccions; abans no existeix una mètrica Hard comparable.
- [ ] Confirmar exactament **score/penalització**, **eficiència**, **temps màxim**, **format de ZIP**, **reset de SOC**, **quota i finestra de 4 hores** a la pestanya i al mentor.

## 4. Arquitectura proposada (hipòtesi tècnica, a validar)

```text
obs Hard Mode (SOC, temps, preu/CO2 conegut 3 h, telemetria t−1)
                |
   +------------+-------------+
   |                          |
Forecast solar+demanda    Forecast preu+CO₂
 Cesc (causal)            Oriol/Dani (causal)
   +------------+-------------+
                |
   MPC robust/receding horizon 12–24 h
      3 h observades + futur incert
                |
        Safety clamp Hard
   SOC [0,6000], P ±1500 (confirmar eficiència)
                |
       BatteryAgent.act(obs)
```

- **Baseline #0:** agent Standard congelat i només adaptat als límits Hard, per mesurar si perd valor amb el nou entorn.
- **Baseline #1:** política de càrrega amb excedent fotovoltaic i descàrrega només si cobreix demanda real, amb reserves SOC.
- **Candidat #2:** MPC amb 3 h certes, la resta prevista causalment; interval/escenaris per incertesa i valor terminal.
- **Candidat #3:** comparar previsió de demanda/solar per Cesc amb heurístiques simples; provar ablation «sense forecast», «solar», «demanda», «preus/CO₂».
- Evitar que el LP faci càrrega i descàrrega simultànies fictícies; verificar exportació zero i unitats de cada variable.
- El firmware/sandbox de Hard podria imposar restriccions noves. **No afirmar temps ni compatibilitat fins executar el checker oficial Hard.**

## 5. Repartiment d'equip immediat (proposta)

| Persona | Rol Hard Mode | Resultat concret |
|---|---|---|
| **Oriol — Codex** | Integrador Hard, compatibilitat, simulador oficial i paquets | Baseline Hard reproduïble, ZIP independent, zero infraccions |
| **Cesc — Codex** | Forecast causal de **solar/PV neta** amb irradiància/temperatures/vent t−1, i anàlisi d'excedents | Prediccions 3–24 h comparades en blocs temporals i impacte en score |
| **Dani — Claude Code** | **MPC Hard** de 3 h conegudes i futur pronosticat/incert, reserves i efecte de 6 MWh | Política que millora baseline Hard amb temps segur |
| **David — Claude Code** | **Tukey**: dashboard de decisions sota sol/escenaris Hard, robustesa, CO₂/cost | Visualitzacions amb valors reals Hard, sense barrejar modes |

**Coordinar abans de passar fitxers:** Codex/Claude no comparteixen automàticament la conversa, només Git. No tocar mòduls d'altres persones. Tot experiment Hard en una **branca/directori separats**, sense trencar Standard.

## 6. Proves imprescindibles

- 0/6000 kWh, ±1500 kW, eficiència actualitzada; sense NaN ni accions no finites.
- Solar 0 i solar > demanda; compensació d'excedents; no descarregar a exportacions gratuïtes.
- Longitud exacta **3** de les llistes, amb possibles arrays truncats/absents si el snippet ho permet.
- Telemetria t−1 desfasada en salts entre setmanes; causalitat del forecast i del perfil meteorològic.
- Preu/CO₂ no disponibles més enllà de les 3 h: cap fuga temporal.
- Comparativa identical train/validation/confirmation i dry-run oficial Hard.
- Latència completa i respectar límit del servidor (a confirmar).
- Dashboard Tukey etiqueta inequívocament Standard/Hard i train/test públic.

## 7. Criteris de decisió

**No enviar el primer ZIP Hard fins que:** (1) el motor oficial local executi la baseline, (2) checker/dry-run Hard passin, (3) hi hagi 0 infraccions, (4) millora en validació respecte a la baseline Hard, (5) versionat, SHA i rollback correctes.

Com a màxim 2 submissions per finestra de 4 hores; reservar-les per candidats robustos, i comprovar horari exacte al portal.

## 8. Dubtes a resoldre a la pestanya Hard/mentors

- El mateix 70/30 i penalització? Importació zero-clip? Altres canvis a l'eficiència?
- Les telemetries meteorològiques són mitjanes, instantànies o acumulades? Quina unitat i quin offset?
- Els 3 valors inclouen l'hora actual? Hi ha més camps accessibles que els del Discord?
- L'escala solar es fa directament sobre els inversors train/test i és determinista?
- Test train/hard, concatenació de setmanes, SOC entre blocs, durada/timeout?
- On es registra el Hard, quan es restableix la quota i què queda visible al privat?
- Premi Tukey: es pot usar Hard, Standard o tots dos? Termini i format?
