# Primera tramesa web UPC Sostenible — La MasIA

**Data/hora (Europe/Madrid):** 14/11/2026, aprox. 13:26–13:27  
**Verificació:** captures de resultats i pantalla oficial connectada de la plataforma `https://repteupc.datathon.cat/`.  
**Versió de codi:** PR [#6](https://github.com/oriolrz/datathon-fme-2026-la-masia/pull/6), commit `99f3f4358cd85caf136cb0da5df51b2396ef7c21`. L'usuari ha indicat que ha carregat el ZIP d'aquesta versió.  
**SHA-256 del ZIP local segons informe PR:** `24e3376dd27b7ca104bfc69a5a952db8d82794f05111b67bd38122b1e0506cf0`. Cal conservar la prova d'identitat entre el ZIP seleccionat i el resultat web; el servidor no ha retornat un SHA verificable en aquestes captures.

## Resultat oficial / leaderboard públic

- **Puntuació:** 4,03
- **Reducció CO₂:** 3,72% = **2.670,3 kg**
- **Estalvi econòmic:** 4,75% = **5.639,08 €**
- **Infraccions:** **0**
- **Puntuació comprovable:** 0,7×3,72 + 0,3×4,75 = 4,029 ≈ **4,03**
- **Rang observat:** **5è de 5 equips visibles** al leaderboard, amb 6 trameses totals en aquell moment.
- **Líder visible:** 6,43 punts (diversos equips). **No deduir que tots fan servir el mateix algorisme**.
- **Conjunt leaderboard:** **test públic de 1.008 hores**; el bloc de resultats web diu de manera genèrica «12 setmanes de test». No afirmar resultats del 50% privat fins que s'expliquin explícitament.
- **Torn 1 (dissabte fins 21:00): 1/10 lliuraments utilitzats, 9 disponibles**, segons pantalla web. La prova gratuïta de 48h no n'ha consumit cap.
- **Validació tècnica de 48 hores:** superada, zero infraccions, classe BatteryAgent detectada, latència mitjana indicada 0,012 ms/pas. Això és només diagnòstic de compatibilitat.
- **PR #6:** obert i pendent de merge a `main`. Encara que ja hàgim enviat un ZIP a la web, això no fusiona codi a GitHub.

## Comparativa sense confondre datasets

| Execució | Score | CO₂ | Cost | Infraccions | Font |
|---|---:|---:|---:|---:|---|
| Local 5.993 h train | 4,26 | 3,86% | 5,18% | 0 | Simulador local, paràmetres ja explorats |
| Web test públic (leaderboard) | **4,03** | **3,72%** | **4,75%** | 0 | Plataforma oficial, primera tramesa |
| Líder visible, test públic | 6,43 | 5,97% | 7,50% | 0 | Leaderboard públic |

**No** interpretar les dues puntuacions local/web com la mateixa població ni utilitzar el test públic per optimitzacions repetitives.

## Diagnòstic del gràfic de 72 hores

La captura mostra accions sovint de +500 kW i −500 kW, amb el SOC arribant a 0% i 100% en hores consecutives d'alguns dies. **Això és físicament vàlid en aquestes proves (0 infraccions), però suggereix investigar si la política està esgotant massa aviat l'energia i perdent oportunitats futures.** No és prova que un MPC obtingui més score.

## Pròxims passos de l'equip

1. **Oriol**: conservar aquest resultat, revisar PR #6 i no enviar cap altre ZIP sense millora validada; preparar entrega estable i relleu Dani.
2. **Cesc**: definir validació temporal sense fuites i analitzar valor de previsió neta/solar i de reserves SOC.
3. **Dani a les 15:00**: comparar una política MPC/heurística 24h amb el fallback sobre les mateixes dades i sota límit global de 60s.
4. **David**: aprofitar puntuació pública 4,03 i mètriques verificades per al dashboard, amb etiquetes clares; no insinuar que el leaderboard és validació privada.
5. **Tots**: no gastar més trameses només per provar paràmetres. Dry-run de 48h és gratuït; la validació local és la principal font d'experimentació.
6. Abans de qualsevol merge, PR review i tests; conservar la versió de rollback que ja s'ha validat.

**Seguretat:** no publicar el PIN ni els tokens, ni captures que mostrin el formulari d'autenticació. Aquest document no conté credencials.
