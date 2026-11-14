# Candidata MPC d'Oriol — experiment congelat

Branca local `codex/oriol-optimization-20261114`, base estable `99f3f43`. Només es creen fitxers en aquesta carpeta; PR #6, agent estable i mòduls dels companys intactes. Cap push, merge ni submissió. S'ha llegit també `docs/UPC_PRIMER_RESULTAT_WEB.md` amb `git show origin/main:docs/UPC_PRIMER_RESULTAT_WEB.md`; aquell resultat públic és 4,03, diferent d'aquests experiments locals.

## Resultat i selecció

**Recomanació: revisar i integrar la candidata MPC congelada**, conservant la reserva estable. No hi ha cap score oficial d'aquesta candidata. El 6,55 intern no demostra superar el 6,43 públic d'altres equips: són poblacions diferents.

| Família, millor configuració de calibratge | Score calibratge | Score validació | CO₂ % validació | Cost % validació | Infraccions | Procés validació |
|---|---:|---:|---:|---:|---:|---:|
| A: estable 24h | 3,32 | 4,90 | 4,15 | 6,65 | 0 | 2,63 s |
| B: valor marginal, marge 0,10 | 3,31 | 4,86 | 4,31 | 6,15 | 0 | 2,59 s |
| C: reserva dinàmica, marge 0,05 | 4,06 | 5,87 | 5,03 | 7,83 | 0 | 2,48 s |
| D: MPC 24h, SOC terminal 1.000 kWh | **4,62** | **6,55** | **5,65** | **8,66** | **0** | **7,46 s** |

Després de seleccionar amb validació, **comprovació final juny–agost: MPC 6,75 vs estable 5,18**, CO₂ 6,97% vs 5,14%, cost 6,23% vs 5,28%, 0 infraccions i procés MPC 6,32 s. Els mesos de comprovació donen MPC/estable: juny 5,82/4,39; juliol 5,28/4,42; agost parcial 11,47/8,11.

Diagnòstic posterior sobre totes les 5.993 hores: **5,66 vs 4,26**, CO₂ 5,22% vs 3,86%, cost 6,67% vs 5,18%, 0 infraccions. El ZIP de la candidata ha reproduït exactament les 5.993 consignes en procés aïllat: **20,611170 s** amb extracció/imports/preprocessament/inicialització/simulació. El servidor encara no s'ha mesurat.

## Matemàtica i límits d'informació

Per pas d'1 h, demanda neta n=L−PV, acció P i importació G(P)=max(n+P,0). El score oficial és `100*(0.7*(1−sum(G*c)/C0)+0.3*(1−sum(G*p)/K0))−0.20*I`, truncat a zero. C0 i K0 són les emissions i el cost del campus sense bateria. Per tant, sense infraccions, equival a minimitzar `sum(G*w)`, amb `w=0.7*c/C0+0.3*p/K0`.

Definint E0 com la importació total base, `mu_c=C0/E0`, `mu_p=K0/E0`, s'obté el valor escalat `v=0.7*c/mu_c+0.3*p/mu_p`; el factor positiu E0 no canvia l'òptim. **Les bases del test són desconegudes**: es fixen només amb calibratge `mu_c=0.08930741373496812 kg/kWh` i `mu_p=0.14347114750579337 €/kWh`, ponderades per energia importada. La normalització és exacta en calibratge i una aproximació fora seu. Cap normalitzador usa març–agost ni el leaderboard.

Amb eta=sqrt(0.9), carregar c kWh AC proporciona eta*c kWh emmagatzemats i una descàrrega posterior de 0.9*c kWh AC. Un cicle que substitueixi importacions és beneficiós si **0.9*v_venda > v_compra**, equivalent a comparar eta*v_venda amb v_compra/eta per kWh emmagatzemat. La càrrega amb excedent solar és gratuïta fins a esgotar-lo; descarregar més que la demanda neta no aporta valor perquè l'exportació no es remunera. El clamp estable aplica eta exacte i epsilon 1e-4 kW.

LP de fins a 24 passos: variables de càrrega c, descàrrega d, SOC e i importació g; `e_next=e+eta*c−d/eta`, `0<=e<=2000`, `0<=c,d<=500`, `g>=n+c−d`, `g>=0`. Objectiu `sum(v*g)+1e-8*sum(c+d)`, amb SOC terminal 1.000 kWh. Amb valors positius no interessa carregar i descarregar simultàniament; també es rebutja qualsevol solució que ho faci. Només s'aplica la primera acció, després es reoptimitza. La cua de vectors de menys de 24 files indica el final al motor oficial i no imposa reserva terminal. També s'han comparat valors terminals lineals 0/0,5/1: tots els MPC han donat 4,62 en calibratge; cap millora significativa del tractament terminal en aquell bloc.

Les previsions contenen l'hora actual i fins a 24 **files**, inclosos salts de calendari. El SOC persisteix com al simulador. No s'utilitza consum/solar futurs ni telemetria vella. El LP assumeix demanda neta de 500 kW: quan la real és >=500, el seu valor marginal és exacte sense predir demanda. Tot el calibratge compleix aquest règim (mínim 500,49 kW). En validació hi ha 14 hores per sota de 500 kW (mínim 459,225), sense exportació per descàrrega observada; en comprovació n'hi ha 17 (mínim zero). Amb demanda inferior pot malbaratar descàrrega; és una limitació explícita.

S'utilitza [scipy.optimize.linprog amb HiGHS](https://docs.scipy.org/doc/scipy/reference/optimize.linprog-highs.html). Cap API ni xarxa en inferència. Si el problema no es resol, es fa servir la reserva i es registra una fallada; totes les candidates acceptades han tingut **0 fallades**. El domini provat del LP té valors marginals positius; observacions incompletes/no finites o valors no positius deriven a la reserva, sense garantia de rendiment en aquell règim.

## Protocol i interpretació dels errors

`protocol.json` es va escriure abans dels experiments: calibratge abans de març (2.784 h), validació març–maig (1.704 h), comprovació juny–agost (1.505 h). Mateixa condició inicial de 1.000 kWh per política/període i horitzons limitats al període. Es van triar els paràmetres només en calibratge, després la família en validació, exigint no perdre més de 0,20 punts en cap mes de validació. La selecció es va guardar abans de mirar comprovació/estrès. Els hashes del codi de política/protocol/runner impedeixen canviar-los silenciosament entre fases.

**Validació interna sobre train ja explorat pel projecte, no holdout independent ni prova del test privat.** Els paràmetres han quedat congelats després de la selecció. Les mètriques mensuals són màscares del recorregut amb SOC persistent, no simulacions mensuals reiniciades. Versions: Python 3.11.9, NumPy 2.4.1, pandas 2.3.3, SciPy 1.17.0; llavor 20261114. Cada runtime de procés inclou imports, dades i inicialització; pot variar segons càrrega de CPU.

- La normalització de pesos sola no ajuda: B empitjora 0,04 punts en validació. La millora ve de la planificació conjunta de potència/SOC, no d'afirmar que 70/30 sempre supera 50/50.
- En validació, les hores amb bateria buida i valor actual >mitjana 24h+0,2 baixen de **170 a 54**; les hores plena i valor <mitjana−0,2, de **182 a 35**. Les accions parcials pugen de **111 a 187**. Són diagnòstics descriptius, no atribucions causals de punts.
- La regla «descarregar abans d'un pic millor» també es compleix en decisions òptimes si hi ha oportunitat de recàrrega/capacitat disponible: el comptador puja de 101 a 205 amb MPC. No és, tot sol, una prova d'error. No s'han detectat càrregues sense cap venda rendible en les 24 files següents amb el criteri marginal fixat.
- En comprovació, la descàrrega que excedeix la demanda neta real suma **1.897,37 kWh estable vs 1.432,62 kWh MPC**, en 4 passos de cada política. Això no genera infraccions, però perd valor. No s'ha retocat la candidata amb aquesta informació.
- LP clairvoyant de totes les hores de **calibratge**, amb demanda/futur complet i SOC final lliure: límit superior aproximat **4,6192204**. No és lliurable. MPC hi arriba al nivell de precisió reportat. El possible crèdit diferencial pel SOC terminal, fins i tot valorat al màxim valor horari, és <=**0,136 punts**, davant una millora de 1,30; acabar més buit no explica la major part de la millora.
- Estrès sintètic, només després de congelar selecció: multiplicant la demanda de comprovació per 0,3/0,6/1,4, estable dona **8,25/8,64/3,68** i MPC **11,48/11,18/4,80**, sempre 0 infraccions i 0 fallades. No són dades ni scores oficials.

## Lliurable i reproducció

`candidate_agent.py` i `candidate_config.json` són l'entrada/configuració congelades. `policies.py` conté totes les alternatives; la candidata reutilitza el clamp estable sense editar-lo. `results_summary.json` conserva mètriques agregades, paràmetres, totes les configuracions, hashes de dades oficials i del paquet; cap dataset ni traça horària. Logs, ZIP i sortides detallades són a `artifacts/oriol_optimization/` i `artifacts/validation/`, ignorats a Git.

ZIP candidat local: `artifacts/oriol_optimization/candidate_submission.zip`, **6.194 bytes**, SHA-256 `50b1a794711d2221855147e44c6be8fc33c9221a9b0bbe258f0f84675721752f`. Checker oficial superat; simulació aïllada completa superada amb consignes idèntiques al codi font. **No s'ha substituït el ZIP estable ni fet cap prova web.**

Des de l'arrel, amb el Starter Kit a la carpeta germana indicada:

```powershell
& ./.venv/Scripts/python.exe -m pip install -r requirements-validation.txt -r experiments/oriol_optimization/requirements.txt
& ./.venv/Scripts/python.exe -B -X utf8 -m unittest discover -s experiments/oriol_optimization -p test_*.py -v
& ./.venv/Scripts/python.exe -B -X utf8 -u experiments/oriol_optimization/run.py calibrate
& ./.venv/Scripts/python.exe -B -X utf8 -u experiments/oriol_optimization/run.py validate
& ./.venv/Scripts/python.exe -B -X utf8 -u experiments/oriol_optimization/run.py confirm
& ./.venv/Scripts/python.exe -B -X utf8 -u experiments/oriol_optimization/run.py stress
& ./.venv/Scripts/python.exe -B -X utf8 -u experiments/oriol_optimization/run.py diagnostic
& ./.venv/Scripts/python.exe -B -X utf8 experiments/oriol_optimization/oracle.py
& ./.venv/Scripts/python.exe -B -X utf8 experiments/oriol_optimization/deliver.py
```

El lliurable usa sempre la configuració congelada inclosa. Si una repetició de selecció amb temps diferents resol un empat de configuracions a favor d'una altra, `deliver.py` ho detecta i rebutja empaquetar una versió diferent de la congelada. No es canvia silenciosament la candidata.

Pas següent proposat, subjecte a autorització: revisió amb Dani/Cesc, comprovació de compatibilitat SciPy al dry-run gratuït del ZIP candidat i posterior decisió d'integració. El test privat, les discrepàncies de normes i el runtime del servidor continuen sense verificar.
