# FME Tukey · Dashboard de decisions energètiques

## Objectiu

No n'hi ha prou amb mostrar números: el dashboard ha d'ajudar una persona responsable del campus a entendre per què l'agent carrega o descarrega i què comporta la decisió en emissions, cost i seguretat.

## Dos modes, una mateixa història

**Normal**: 2 MWh de bateria, ±500 kW, 24 h de mercat conegudes. És el primer problema resolt i és un bon punt de referència.

**Hard**: 6 MWh, ±1.500 kW, solar ×12 i només 3 h de mercat conegudes. Afegeix incertesa sobre la solar, la demanda i el futur del mercat. És el mode que decideix el premi principal segons la comunicació més recent de l'organització.

## Demo suggerida (90–120 segons)

1. **Context**: mostrar les corbes de demanda, producció solar, preu i CO₂ d'un dia real del TRAIN.
2. **Decisió**: seleccionar una hora i explicar l'acció (+ carrega / − descarrega), el SOC, les restriccions i la previsió disponible.
3. **Impacte**: comparar imports de xarxa, kg de CO₂ i euros amb la baseline sense bateria; distingir estalvis del període, no només una hora.
4. **Comparativa**: canviar Normal ↔ Hard amb el selector; explicar què canvia en la física i en la informació disponible, no comparar directament scores de modes diferents.
5. **Pensament crític**: mostrar que el model té incertesa i que les previsions no són les observacions futures reals.

## Requisits de qualitat abans de presentar

- Cada gràfic porta unitats: kW, kWh, kg CO₂, euros, €/kWh.
- No barrejar "resultat web públic", "simulació TRAIN" i "exemple il·lustratiu".
- No inventar una traça del Mode Normal: cal l'agent Normal original per reproduir-ne les accions.
- En comparar modes, usar dates i dades d'origen coherents i documentar la solar ×12.
- Evitar afirmar que el dashboard fa prediccions privades amb dades que no pot veure.
- Preparar còpia offline, captures i una navegació de demostració que funcioni sense xarxa.
- El jurat ha de trobar el codi del dashboard o un enllaç de demo al repositori abans de presentar.

## Coordinació

El desenvolupament principal del dashboard es fa a [`feat/david-tukey`](https://github.com/oriolrz/datathon-fme-2026-la-masia/tree/feat/david-tukey), amb aportacions d'optimització del Dani. Cal integrar o enllaçar-ne la versió final des de `main`; no s'han d'atribuir funcionalitats no verificades.

## Guió final

> "Hem resolt el repte amb un agent que replanifica cada hora i hem creat una interfície perquè el gestor energètic pugui entendre i contrastar les seves decisions. Distingim el que es coneix del que es prediu, i el que s'ha validat del que encara és incert."

[Portada](../README.md) · [Solució tècnica](FINAL_TECHNICAL.md)
