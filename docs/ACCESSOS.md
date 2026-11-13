# Accessos i permisos — Claude Code, Codex i GitHub

## Les tres capes que cal distingir

1. **Permís al GitHub:** els col·laboradors que hagin acceptat la invitació a aquest repositori privat personal poden llegir-lo i publicar-hi canvis. Han d'iniciar sessió al seu propi compte i autoritzar les eines que utilitzin.
2. **Permís d'edició local:** Claude Code i Codex poden modificar fitxers de la carpeta de treball segons el seu mode de permisos. Això no implica publicar-los automàticament a GitHub.
3. **Integració de l'equip:** els canvis es converteixen en commits, es publiquen amb `git push` i s'integren a `main` després de revisar un pull request.

## Claude Code (Dani i David)

Hem afegit `.claude/settings.json` amb `permissions.defaultMode = "acceptEdits"`. Quan Claude Code detecti la configuració compartida, **pot editar fitxers locals dins del projecte sense haver d'aprovar cada edició ordinària**. Altres ordres poden seguir demanant permís; això és normal.

Per canviar el mode durant una sessió, feu servir `/permissions`, les opcions del VS Code o `Shift+Tab` a la terminal, segons la versió.

- `acceptEdits`: mode compartit recomanat per desenvolupar ràpid.
- `auto`: si la versió i el compte l'ofereixen, utilitza comprovacions de seguretat en segon pla per reduir confirmacions.
- `bypassPermissions` / `--dangerously-skip-permissions`: salta proteccions. **No el recomanem a l'ordinador personal**; només en contenidors o entorns realment aïllats.

Si l'organització o una configuració personal té prioritat, pot prevaler sobre el fitxer del repositori. Comproveu els permisos reals dins l'aplicació.

## Codex (Oriol i Cesc)

El mode habitual `workspace-write` permet editar fitxers dins de la carpeta del projecte sense autoritzar cada modificació local. Si cal, configureu els permisos amb `/permissions` o el selector del VS Code.

Per a més autonomia sense obrir tot l'ordinador, utilitzeu `Approve for me` quan estigui disponible; fa una revisió automàtica de les sol·licituds elegibles.

No és necessari activar `danger-full-access` ni `--yolo` per col·laborar amb GitHub. Els modes perillosos poden afectar fitxers fora del projecte.

## Publicar al GitHub sense trepitjar-vos

- Cada persona treballa en una **branca pròpia**: `feature/oriol-...`, `feature/cesc-...`, `feature/dani-...` o `feature/david-...`.
- L'agent pot preparar commits i un pull request **quan el responsable autoritzi aquella operació**.
- Amb `git push -u origin nom-de-la-branca`, la feina és visible a GitHub; la resta no necessita esperar a fusionar-la per revisar-la.
- Per passar els canvis a `main`, reviseu-los i feu el merge del PR. Eviteu quatre agents fent push directe al mateix `main`.
- Quan es fusiona, la resta fa `git switch main` i `git pull --ff-only` abans de crear noves branques.

**No hi ha sincronització en temps real entre les converses de les IA.** GitHub és el punt comú i cal desar-hi les decisions rellevants.

Documentació oficial:
- https://code.claude.com/docs/en/permissions
- https://code.claude.com/docs/en/settings
- https://learn.chatgpt.com/docs/agent-approvals-security
- https://docs.github.com/en/repositories/creating-and-managing-repositories/access-to-repositories
