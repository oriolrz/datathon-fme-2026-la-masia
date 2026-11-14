# Fase 2 UPC — Oracle, forecast i decisió de la tarda (14/11/2026, 15:58)

**Font:** resum de resultats comunicat per Oriol a partir de l'execució de Codex de la fase 2. **Aquesta documentació NO és una reproducció independent de codi local**, que encara no està pujat a GitHub.  
**Decisió provisional:** mantenir el MPC que ha obtingut **6,43** a la web i no enviar variants no robustes.

## Estat observable a la plataforma (consulta posterior)
- Leaderboard públic: 25 equips, 53 submissions, rècord visible **6,44**.
- La MasIA: **6,43**, 0 infraccions, en la posició 18 del registre visible.
- El leaderboard és sobre **1.008 h de test públic**; no equival al privat.
- La versió anterior de 4,03 està superada per la darrera versió MPC enviada a la plataforma.

## Oracle offline reportat (no desplegable)

| Període | MPC | Oracle perfecte | Diferència |
|---|---:|---:|---:|
| Calibratge (setembre-febrer) | 4,619219919 | 4,619220402 | 0,000000484 |
| Validació (març-maig) | 6,553241792 | 6,558849139 | 0,005607346 |
| Comprovació (juny-agost) | 6,748775928 | 6,817281214 | 0,068505286 |
| Train complet | **5,655071759** | **5,675261712** | **0,020189952** |

El MPC assoleix aproximadament **99,64%** del score de l'oracle sobre TRAIN complet (`5.655071759 / 5.675261712`). **Important:** aquesta no és una demostració de límit absolut ni de score màxim sobre test públic/privat. L'oracle coneix demanda, solar, preus i CO₂ de tot el període, i les bases de normalització exactes; segueix un conjunt concret de restriccions i una exportació amb valor 0 €.

## Ablations i forecast (reportats)

- MPC actual domina alternatives de reserves i de valor marginal als períodes interns.
- Normalització online: guanya 0,00490 en validació però perd 0,00712 en comprovació.
- Terminal suau/valor ombra: millora 0,00030 en validació i empata en comprovació.
- Previsions estacional/persistència/model C no canvien les consignes en els tres períodes, tot i millores de MAE de 506,33 a 53,97 kW en validació: amb demanda neta molt superior a 500 kW, el límit de potència domina.
- Coll d'ampolla restant: algunes hores amb demanda neta <500 kW i exportació no remunerada.

## Verificació reportada per Codex
- 30 tests superats, sense infraccions ni fallades.
- Oracle sense càrrega i descàrrega simultànies; residu de SOC <=2,28e-13 kWh.
- ZIP MPC actual reproduït en local, 5.993 consignes idèntiques, runtime complet 22,05 s.
- ZIP seleccionat: `artifacts/oriol_phase2/selected_current_submission.zip` (ruta **local, no GitHub**) amb SHA-256 `50b1a794711d2221855147e44c6be8fc33c9221a9b0bbe258f0f84675721752f`.
- Commits **locals**, no publicats encara: MPC `dfe0345fa9d6be77187753515bc555bf826853ff`; fase2 `1176f719a236124d0d661e5c6ab4a9271beb21c5`.
- No pressuposar que el codi de fase 2 es pot veure al GitHub fins a push/PR. El PR #6 continua obert i conté la versió ESTABLE ANTERIOR, no aquesta MPC.

## Què cal fer ara (ordre)

1. **Oriol:** congelar el ZIP del MPC amb 6,43 i confirmar que el SHA-256 correspon al binari que s'ha enviat a la plataforma; si no hi ha identificador al servidor, mantenir registre local amb data i nom. No sobreescriure'l. Conservar el ZIP anterior de 4,03 de rollback.
2. **Oriol/Codex:** portar els dos commits de l'experiment a una branca remota pròpia, sense incloure datasets, secrets ni artifacts temporals; obrir PR de la MPC com a candidata estable, revisat amb el Dani. **No fer merge del PR #6 pensant que és el MPC.**
3. **Dani:** auditar de manera independent l'oracle i l'MPC: consistència d'unitats, exportació, normalitzadors, SOC terminal, límits, eventual solució trivial per cap de setmana i causalitat. Si els resultats aguanten, deixar d'optimitzar a cegues.
4. **Cesc:** reportar ablation: forecast no canvia decisions; concloure si aquest resultat és robust a mesos de demanda reduïda, sense dedicar-li més hores de ML sense justificació.
5. **David:** reforçar Tukey amb dos nivells de resultats: comparació del primer agent 4,03 vs MPC 6,43 al test públic, més un apartat oracle vs MPC **etiquetat TRAIN/diagnòstic** i tradeoffs per setmanes; evitar representar scores de diferents datasets al mateix eix com si fossin comparables.
6. Confirmar amb els mentors **com i quan s'entrega Tukey**, hora del pitch i criteris de desempat o ordenació amb puntuacions arrodonides.
7. Guardar temps per preparar demo, presentació i fitxers d'entrega finals abans del tall oficial.

## Criteri per reobrir l'optimització
Només investigar més si:
- el Dani troba un error metodològic important; o
- hi ha una candidata amb millora **robusta, no només una mil·lèsima** en un únic període, 0 infraccions i runtime segur; o
- dades del servidor indiquen comportament diferent al simulador.

**No fer cap nova submissió al leaderboard només per intentar pujar de 6,43 a 6,44.** L'avaluació privada i els criteris de jurat importen.

