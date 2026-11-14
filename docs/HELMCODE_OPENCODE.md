# OpenCode + HelmCode — La MasIA

**Situació (14/11/2026):** els organitzadors han comunicat un accés gratuït compartit per als participants durant la Datathon, amb una clau facilitada per Discord. **No enganxeu la clau en aquest repositori, en fitxers versionats ni en prompts.**

## Què hem configurat
- Fitxer d'equip `opencode.json` **sense credencials**.
- Proveïdor `helmcode` amb endpoint `https://api.helmcode.com/v1` i models: `glm5.3-flash`, `deepseek-v4-flash`, `qwen3.6` i `gemma4`.
- Instruccions comunes en català amb `AGENTS.md` (OpenCode el llegeix) i documents de `docs/`.
- No s'afegeixen els models comercials addicionals, com `glm5.3` sense Flash, que el proveïdor documenta com a suplement de pagament.

## Instal·lació personal
1. Descarrega/obre OpenCode a la carpeta del projecte clonat (on és `opencode.json`). Si és la versió CLI, executa `opencode`.
2. A OpenCode, introdueix `/connect`, selecciona o escriu el proveïdor **exactament** `helmcode` i enganxa allà la clau obtinguda al Discord oficial. OpenCode la guarda en el seu magatzem local de credencials, no al Git.
3. Executa `/models`; escull `helmcode/glm5.3-flash` per començar, o `helmcode/qwen3.6` per tasques simples i ràpides.
4. Fes una consulta sense escriure fitxers: «Llegeix AGENTS.md i docs/STATUS.md. Resumeix en català les normes i qui és responsable de què. No modifiquis res.»
5. Si falla l'autenticació, comprova que el proveïdor de `/connect` és `helmcode` (minúscules), no `Helmcode`, i revisa la vigència de la clau al canal d'ajuda oficial.

**Alternativa d'entorn:** en comptes de `/connect`, cada persona pot configurar la variable personal `HELMCODE_API_KEY` al seu sistema. No la definiu en cap fitxer de Git ni en exemples públics.

## Versió de configuració
La guia d'HelmCode mostra un format històric d'OpenCode amb `provider`, `npm` i `options`. El fitxer del nostre equip utilitza el **format actual** de la documentació d'OpenCode (`providers`, `package`, `settings.baseURL`). Si teniu una versió antiga, actualitzeu OpenCode i verifiqueu la versió.

## Estratègia dels agents
- Codex i Claude Code continuen sent les eines principals que cada persona ja coneix.
- OpenCode + HelmCode és un **tercer agent alternatiu**, especialment per tasques independents, revisió, SQL, exploració i petits encàrrecs.
- No feu que dos agents treballin simultàniament en el mateix arbre de fitxers/branca.
- L'ús de serveis allotjats al núvol per tractar dades de l'organització depèn dels permisos del repte. No hi envieu datasets restringits sense confirmació.

## Límit de l'accés gratuït
Els límits del servei són per clau, amb un nombre màxim de peticions i concurrència. Si la clau és compartida entre tots els participants, pot haver-hi saturació. **No assumiu que tots els models del catàleg o els models revenguts de pagament estan inclosos en l'accés de la Datathon.**

## Fonts
- HelmCode, configuració OpenCode: https://helmcode.com/docs/opencode
- HelmCode, models i límits: https://helmcode.com/docs/models i https://helmcode.com/docs/rate-limits
- OpenCode, configuració actual: https://opencode.ai/docs/providers/ i https://opencode.ai/docs/config/
- OpenCode, instruccions AGENTS.md: https://opencode.ai/docs/instructions/
