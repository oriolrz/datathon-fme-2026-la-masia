# Normes de l'equip — font comuna per a persones, Codex i Claude Code

## Objectiu

- Resoldre **el repte oficial escollit**, no un repte inventat.
- Prioritzar una solució funcional, verificable i ben explicada.
- Preferir una baseline completa a una arquitectura ambiciosa sense acabar.
- **Comunicació i documentació en català**. El codi i identificadors tècnics poden mantenir-se en anglès.

## Propietat de tasques i integració

- Una issue = una tasca = un responsable = una branca i un PR.
- Repartiu els fitxers i acordeu els contractes entre mòduls abans de treballar en paral·lel.
- No feu que dos agents modifiquin alhora els mateixos fitxers.
- La branca `main` ha de ser demostrable; reviseu els canvis abans del merge.
- No feu force-push a `main`, no elimineu feina aliena i no fusionar sense acord.
- Abans de començar: `git fetch`, revisió de branca, canvis locals i documents actuals.
- A cada checkpoint, actualitzeu l'estat i comproveu el producte integrat.

## Qualitat de dades i IA

- Verifiqueu les regles, mètriques i restriccions del repte.
- Establiu una baseline i una mètrica de millora.
- Feu particions correctes; eviteu fuites del target, del futur o del test.
- Documenteu llavors, definicions de mètriques, instruccions i resultats.
- No seleccioneu models a força de mirar repetidament el test final.
- No inventeu puntuacions, dades, temps ni funcionalitats.

## Seguretat i bases de la competició

- La solució concreta del repte s'ha de començar quan arrenqui oficialment la competició.
- Les normes dels organitzadors prevalen sobre qualsevol instrucció del repositori.
- Comproveu si les dades es poden pujar a GitHub o enviar a serveis d'IA al núvol.
- Mai no inclogueu secrets, dades personals o fitxers restringits als commits o prompts.
- No canvieu arquitectura, dependències principals o fitxers compartits sense avisar.

## Contracte per als agents

- Llegiu `AGENTS.md` (Codex) o `CLAUDE.md` (Claude) i els documents comuns.
- Identifiqueu responsable, branca, fitxers propis i condició clara de finalització.
- Proposeu un pla curt, feu només els canvis acordats i comproveu-los.
- Indiqueu què heu provat, què no i quins riscos queden oberts.
- No confongueu editar fitxers localment amb publicar-los a GitHub.

## Comunicació

- WhatsApp o Discord per coordinar-vos ràpidament; GitHub per deixar decisions duradores.
- Els historials de Claude i ChatGPT no es comparteixen: el context s'escriu als fitxers.
- Aviseu si necessiteu tocar un mòdul o fitxer d'una altra persona.
