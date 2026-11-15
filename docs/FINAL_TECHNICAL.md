# Solució tècnica · La MasIA (UPC Sostenible × AED)

## Repte i objectiu

L'agent decideix una potència de bateria en kW a cada hora. Acció positiva: carrega; negativa: descarrega. Optimitzem la reducció percentual d'emissions de CO₂ (70% del score) i de despesa energètica (30%) respecte de l'escenari sense bateria.

| Mode | Capacitat | Potència | Solar | Preu i CO₂ coneguts |
|---|---:|---:|---:|---:|
| Normal | 2.000 kWh | ±500 kW | Original | 24 hores |
| Hard | 6.000 kWh | ±1.500 kW | ×12 | 3 hores |

Eficiència round-trip: 90%. L'estat de càrrega inicial és el 50%. L'exportació causada per descarregar energia de la bateria no té benefici en l'avaluació oficial. Els límits físics es verifiquen abans de retornar cada acció.

## Aproximació

La nostra línia Hard utilitza *Model Predictive Control* (MPC) amb previsions de demanda, producció solar, preus i intensitat de CO₂. En la v2 de referència, el MPC considera cinc escenaris d'incertesa de la demanda neta. Cada hora resol un pla, aplica la primera acció i torna a planificar en rebre la següent observació.

El controlador utilitza només dades disponibles causalment al pas actual: preu i CO₂ de t a t+2, telemetria passada i models ajustats amb les dades TRAIN autoritzades. No incorpora observacions reals de consum, solar o mercat futures ocultes.

**Nota de versions:** les versions v2, v6 i final no s'han de presentar com si fossin idèntiques. La implementació i els paràmetres concrets de l'agent final són els del ZIP registrat a la plataforma.

## Resultats registrats

- Mode Normal: **6,43 punts públics** segons els enviaments comunicats per l'equip.
- Mode Hard: **23,16 punts públics** per al Dani v2 i **23,32 punts públics** comunicats per a la versió final, amb verificacions de zero infraccions.
- Són puntuacions del *leaderboard públic*: no demostren el rendiment en el rànquing privat.

La puntuació privada i l'ordre definitiu del jurat són desconeguts.

## Avaluació crítica i generalització

Hem reproduït numèricament els paràmetres de la v2 amb el TRAIN oficial (diferències dels coeficients de l'ordre de 10⁻¹³). Hem executat validacions amb blocs temporals exclosos de l'ajust i hem estudiat alternatives: perfils jeràrquics, calibratge d'incertesa out-of-fold, regressió de demanda neta, memòria inicial, adaptadors mensuals i estratègies de risc.

**No tot canvi que millora una finestra generalitza.** Els experiments de calibratge OOF, per exemple, van mostrar variacions +0,03 (octubre), −0,30 (gener), +0,18 (abril) i +0,08 (juliol walk-forward); no s'ha acceptat aquesta modificació com a millora robusta.

S'ha identificat també que el comportament de l'horitzó quan hi ha salts mensuals pot dependre de si el simulador ofereix les tres següents files o només hores consecutives. Un guany local sota un protocol alternatiu no és evidència de guany oficial.

**Limitacions:** les dades TRAIN han estat utilitzades repetidament durant la investigació i part del disseny de l'arquitectura depèn d'aquesta exploració; la validació retrospectiva no substitueix un test privat cec. Per això distingim replays sobre TRAIN, folds reentrenats amb períodes exclosos, i puntuacions oficials públiques.

## Reproductibilitat i seguretat

- Paquet oficial i `starter_kit/environment.py` com a referències de la física.
- Control de potència i SOC a cada pas.
- Zero infraccions en els replays i en la submissió pública comunicada.
- Temps d'execució dins el límit de 60 segons en els benchmarks documentats.
- Cap ús de test ocult ni accés a xarxa durant la inferència del codi auditat.
- Les dades originals no es tornen a publicar sense verificar-ne els permisos.

Font del repte: https://repteupc.datathon.cat/

[Portada del projecte](../README.md) · [Presentació i dashboard](TUKEY_DEMO.md) · [Lliurament](SUBMISSION.md)
