# Estat actual — La MasIA, 14 novembre 2026

**Coordinació 12:25–15:00:** Oriol, Cesc i David presents; Dani s'incorpora cap a les **15:00**. [Punt d'entrada](START_HERE.md), [runbook](OPERATIU_14NOV.md), [onboarding Dani](HANDOFF_DANI_1500.md), [relleu per omplir](RELLEU_1500.md).

**GitHub preparat, no vol dir tasques executades:** issues [#1](https://github.com/oriolrz/datathon-fme-2026-la-masia/issues/1), [#2](https://github.com/oriolrz/datathon-fme-2026-la-masia/issues/2), [#3](https://github.com/oriolrz/datathon-fme-2026-la-masia/issues/3), [#4](https://github.com/oriolrz/datathon-fme-2026-la-masia/issues/4), [#5](https://github.com/oriolrz/datathon-fme-2026-la-masia/issues/5). Branques remotes `feat/oriol-integration`, `feat/cesc-forecast`, `feat/david-tukey`, `feat/dani-optimizer`. Codi de prototip 24h compartit a `prototypes/upc/` com a referència experimental.


**Repte:** ja estan anunciats Qualcomm, UPC Sostenible i Tinybird/RawTree. **No s'ha confirmat encara la decisió oficial dels quatre.**
**Candidat preferent tècnicament:** UPC Sostenible, segons anàlisi i proves locals; no confondre amb una decisió de l'equip.
**Side Challenge:** Tukey (dashboard de suport al repte principal), amb criteris confirmats; termini i forma de lliurament pendents.

## Fonts que han de llegir els agents quan es confirmi UPC
- [Auditoria exhaustiva i correccions prioritàries](AUDITORIA_PLANNING_UPC_TUKEY.md)
- [Pla operatiu provisional](PLA_UPC_TUKEY.md)
- [Prompts per als quatre](PROMPTS_EQUIP_UPC.md)
- [Inspecció i benchmarks locals](UPC_STARTER_TESTS.md)
- [Requisits generals de l'equip](TEAM_RULES.md)

## Proves fetes fora del repositori de codi
- Starter Kit oficial inspeccionat; simulador i validador disponibles localment.
- Simulació en **5.993 hores de train**: agent oficial 0,00 punts / 46 infraccions; referència amb clamp 1,27 / 0; candidat simple 24h 4,26 / 0.
- El candidat 4,26 **s'ha triat entre configuracions ajustades al train**. No és validació independent ni score de leaderboard; no hi ha cap tramesa oficial confirmada.
- Validador local de 24 passos superat pel candidat, **no verificat encara el dry-run web**.
- Prova de mòduls `agent.py` + `src/policy.py` empaquetats en ZIP: validador local superat. Cal repetir-la al servidor web.
- Benchmark sintètic de 150 problemes LP de 24h: ~1,5 ms/LP al maquinari de proves. No equival al runtime real complet.
- Proves de seguretat del candidat en 10.009 SOC/previsions sintètics: totes les accions dins els límits calculats.

## Responsabilitats proposades (pendent d'acceptació)

| Persona | Àrea suggerida | Branca suggerida | Estat |
|---|---|---|---|
| Oriol | Integració, política final, proves i trameses | `feat/oriol-integration` | No assignat oficialment |
| Cesc | Dades, exploració, pronòstic causal | `feat/cesc-forecast` | No assignat oficialment |
| Dani | Heurística i MPC | `feat/dani-optimizer` | No assignat oficialment |
| David | Dashboard Tukey, presentació i resultats | `feat/david-tukey` | No assignat oficialment |

## Bloquejos reals
1. Decisió i repartiment dels quatre.
2. Confirmar amb mentor contradiccions del material: penalització, excedents, vectors de 24h entre salts i termini exacte.
3. Confirmar com/quan entregar Tukey.
4. Mesurar validació temporal sense reutilitzar el train per seleccionar hiperparàmetres.
5. Verificar el ZIP final al dry-run web i complir timeout de 60 s.

**Regla de màxima prioritat:** l'agent `main` ha de passar validador, funcionar offline i no generar infraccions. Cap agent fa push a `main` sense revisió.
