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
