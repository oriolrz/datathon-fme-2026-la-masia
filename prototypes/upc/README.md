# Prototip UPC de La MasIA — només referència experimental

Fitxer: `agent_v0_24h.py` és una còpia del prototip local generat durant la Datathon el **14 de novembre de 2026**. **No és el fitxer `agent.py` final ni un enviament al leaderboard.**

Resultats sobre **5.993 hores de TRAIN** amb el simulador `CampusBatteryEnv` del Starter Kit oficial:
- Score: **4,26**.
- Reducció CO₂: **3,86%**.
- Estalvi econòmic: **5,18%**.
- Infraccions: **0**.
- Validador tècnic local superat.

**Advertiment metodològic:** els paràmetres d'aquest prototip es van seleccionar comparant diverses versions sobre les mateixes dades. El score no és una validació temporal independent ni una estimació de la classificació pública/privada.

El Dani pot estudiar-ne la lògica per construir una política millor **al seu mòdul**, sense modificar aquest arxiu ni `agent.py` d'Oriol. Qualsevol millora s'ha de validar amb les mateixes mètriques i un holdout temporal separat.

Aquest codi no inclou dades, PINs o credencials. Les dades i el motor de simulació oficials s'han de descarregar per separat des de la plataforma.
