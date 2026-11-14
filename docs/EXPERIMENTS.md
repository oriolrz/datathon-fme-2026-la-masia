# Registre d'experiments

Anoteu **resultats mesurats**, mai millores imaginades. Les comparacions han de fer servir la mateixa mètrica i un protocol d'avaluació equivalent.

| ID | Responsable | Commit SHA | Partició / llavor | Mètode | Mètrica principal | Altres mètriques | Temps | Observacions |
|---|---|---|---|---|---|---|---|---|
| — | — | — | — | Encara no iniciat | — | — | — | — |

## Evidència necessària

- Definició exacta de train/validation/test i ordre temporal quan correspongui
- Llavor, paràmetres, dependències i instruccions per reproduir l'experiment
- Comparativa baseline/model nou sobre la mateixa partició
- Si la xifra és d'entrenament, validació o test final
- Comprovacions d'overfitting, data leakage i supòsits erronis
- Enllaç al PR, fitxer de resultats o informe

## Integració Oriol v1 — execució local 14/11/2026 a les 13:03

Run `20261114T120340Z`, base `1bb02e1fd026f98399aba6da716f1be7cca991aa` amb arbre modificat; hashes exactes a `artifacts/evaluation/metrics.json`. **Mesurat abans del commit; codi identificat pels hashes.** Llavor `20261114`, Python 3.11.9, preprocessament del tutorial oficial, 5.993 hores de **train ja explorat**, sense retocar paràmetres. [Protocol, ordres i limitacions](INTEGRACIO_UPC_V1.md).

| Política | Score train | CO₂ | Cost | Infraccions | Simulació local |
|---|---:|---:|---:|---:|---:|
| Referència original | 0,00 | 0,88% | 2,18% | 46 | 2,154 s |
| Referència + clamp exacte | 1,27 | 0,88% | 2,18% | 0 | 1,978 s |
| Prototip preexistent | 4,26 | 3,86% | 5,18% | 0 | 2,209 s |
| BatteryAgent reserva | 4,26 | 3,86% | 5,18% | 0 | 2,137 s |

ZIP final validat amb checker oficial i procés aïllat: mateixes 5.993 consignes i mètriques, **3,977685 s** incloent extracció/imports/preprocessament/simulació. 11 tests correctes. Diagnòstics amb reinici de SOC/horitzó per bloc: 2.784 h abans de març **3,32**; 3.209 h des de març **5,09**. **No són holdouts independents** i no són directament comparables amb màscares d'un recorregut complet. Dry-run web i leaderboard pendents; 0 submissions en aquesta sessió.

## Proves exploratòries 14/11/2026 (fora de Git; encara NO són el model final)

**Origen:** Starter Kit oficial, preprocessament del tutorial; **5.993 hores de train**. Els valors van ser reproduïts localment i hi ha un informe ampli a [UPC_STARTER_TESTS.md](UPC_STARTER_TESTS.md) i [AUDITORIA_PLANNING_UPC_TUKEY.md](AUDITORIA_PLANNING_UPC_TUKEY.md).

| ID | Política | Fitxers de prova locals | Score | CO₂ estalvi | Cost estalvi | Infraccions | Advertiment |
|---|---|---|---:|---:|---:|---:|---|
| explor-00 | Bateria inactiva | environment.py | 0,00 | 0,00% | 0,00% | 0 | Referència neutra |
| explor-01 | Agent oficial original | starter_kit/agent.py | 0,00 | 0,88% | 2,18% | 46 | Clipping de precisió |
| explor-02 | Agent oficial amb clamp | Wrapper temporal local | 1,27 | 0,88% | 2,18% | 0 | Baseline segura |
| explor-03 | Prototip llindars 24h | Prototip local de La MasIA | 4,26 | 3,86% | 5,18% | 0 | **Seleccionat entre alternatives sobre el mateix train; NO és holdout** |

No s'ha pujat encara el codi del prototip a aquest repositori: no es pot reproduir només amb un `git clone`. **No etiqueteu aquests valors com a leaderboard o mètrica de generalització.** Registrar nous experiments amb commits de codi, split temporal independent, temps i accions per cada hora.

**Proves no comparables al score:** ZIP auxiliar amb import de `src/policy.py` validat localment (24 passos); 10.009 casos de límits SOC passats; 150 problemes sintètics LP de 24h (1,5 ms/LP a la màquina de proves). Aquestes proves no demostren performance del MPC complet ni del servidor.
