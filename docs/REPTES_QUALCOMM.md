# Repte candidat: Qualcomm — Math on the Edge

**Data de revisió:** 14/11/2026  
**Estat:** candidat, **NO escollit**; pendents els enunciats de Tinybird i UPC Sostenible.  
**Font principal:** https://github.com/mpous/datathon-UPC-maths-qualcomm-arduino-unoq  
**Vídeo proporcionat:** https://www.youtube.com/watch?v=l1gk_Qj23cY (sense transcripció verificada en aquesta revisió)

## Enunciat literal resumit

Crear un Math Copilot que **s'executi completament en un Arduino UNO Q de 4 GB** i utilitzi M3Kang per ajudar l'alumnat a raonar matemàticament. Dos camins:
- **TEACH:** experiència educativa que fomenti el raonament (pistes, pràctica adaptativa, anàlisi d'errors, interacció física) sense revelar directament la solució.
- **REASON:** respondre preguntes Cangur de cinc opcions (A-E), mesurades amb un test ocult.

El README també afirma que el jurat provarà `predict.py` de tots els equips, encara que implementin TEACH: cal confirmar el pes real de cada component amb els mentors.

## Requisits i restriccions confirmats al README

- El projecte ha de funcionar **offline**, a la placa i sense cap servei de núvol en temps d'inferència; màxim **60 segons per problema**, respostes deterministes.
- Arduino UNO Q **4 GB**; Linux Qualcomm QRB2210 i microcontrolador STM32; en aquest repte només la matriu LED **8x13** com a sortida de hardware afegida. Sense sensors ni mòduls externs.
- Es proporciona pipeline base amb `predict.py`, `eval.py`, `copilot/`, scripts `board/`, `laptop/prepare_m3kang.py`, exemples web i skills.
- Models de referència: Qwen3.5 0.8B Q8_0 (~835 MB), bge-small-en-v1.5 (~37 MB), llama.cpp. A la placa cal compilar llama.cpp i instal·lar serveis.
- Dades M3Kang: **1.747 problemes originals**, amb traduccions a **108 idiomes** i **8 nivells**. Les opcions A-E acostumen a estar dins les imatges.
- OCR documentat: opcions completes en **1.078/1.747 (62%)** d'una prova en anglès.
- Baseline documentada, **40 problemes en anglès i amb opcions OCR llegides**: **22,5% (9/40)**, temps mitjà **8,7 s**. **No generalitzar aquest 22,5% al test ocult**; el model mostra biaix cap a D/A.
- RAG amb embeddings i SQLite funciona però encareix el prompt. Prefill ~11–12 tokens/s i generació ~5–6 tokens/s.
- **Entregables addicionals:** repositori GitHub públic de codi (sense dades de M3Kang), projecte documentat a Arduino Project Hub, demo en placa i pitch de **3 minuts**, anàlisi d'errors per tema/idioma/dificultat.
- **Dades amb llicència de recerca:** no publicar `train.jsonl`, `val.jsonl`, imatges ni l'índex SQLite derivat amb text.

## Riscos prioritaris per a La MasIA

1. **Disponibilitat i estat físic de la placa:** necessitem saber si la cedeixen, si està preparada i si el model és de 4 GB. Fer el setup de zero consumeix hores; el README estima uns 15+2+5+30+5+10+5+5+5+30+1+10+15 minuts, abans d'idear, implementar i publicar.
2. **Dependències Python del portàtil:** Oriol té Python 3.14.5, però `rapidocr_onnxruntime` (a `laptop/requirements.txt`) indica a PyPI compatibilitat amb Python <3.13. Fer servir un entorn Python **3.11/3.12**, separat de l'entorn global, si escollim Qualcomm. Font: https://pypi.org/project/rapidocr-onnxruntime/
3. **Poca experiència amb hardware:** el més nou no és l'electrònica, sinó SSH, Debian, App Lab, Bridge, serveis, USB/ADB i RAM. Els exemples ja resolen una part important.
4. **M3Kang multilingüe amb duplicats per traducció:** separar train/validation per `id`, no per fila. Evitar filtracions al RAG.
5. **Avaluació i demo:** un model millor en un petit subconjunt pot no generalitzar; és imprescindible mesurar un conjunt fix per categoria i mostrar latència real.

## Opcions competidores (hipòtesis, no decisions)

**A — TEACH: entrenador adaptatiu offline amb pista progressiva i matriu LED (més viable per a la primera demo).**
- Preguntes M3Kang en català; perfil local per temes/nivells; recuperació ràpida d'exercicis similars; pistes curtes; respostes A-E i feedback via matriu 8x13.
- Diferenciació: adaptació real, privadesa, accessibilitat i experiència docent verificable; no dependre de generacions llargues.
- Mesurar latència, adequació de dificultat, cobertura, qualitat de pistes i percentatge de pistes que filtren respostes.

**B — REASON: pipeline d'avaluació optimitzat i multimodal.**
- Prioritzar extracció d'opcions, detecció de categoria i càlcul determinista en Python quan sigui possible.
- Comparar contra baseline en la mateixa validació, per idioma/nivell/problemes amb i sense opcions.
- Evitar OCR al mateix UNO Q si massa lent; revisar el format exacte del test ocult amb els mentors abans d'entrenar.
- Més incertesa en score: el 0.8B és proper a l'atzar en la mostra documentada i el límit de 60s és estricte.

**Opció híbrida:** una bona demo TEACH més millores modestes i mesurades a `predict.py`. És una hipòtesi competitiva a valorar després d'aclarir la rúbrica.

## Preguntes imprescindibles als mentors Qualcomm

1. Doneu **un Arduino UNO Q 4GB físic per equip**? Està actualitzat, amb models/serveis ja instal·lats?
2. Quin és el **pes exacte de TEACH vs REASON**? Si triem TEACH, `predict.py` s'avaluarà igualment al test ocult i amb quin pes?
3. El **test ocult** inclourà opcions en text, imatge/base64, o només el text? Es pot usar precomputació d'OCR feta abans de la demo?
4. La matriu LED és **obligatòria** o només recomanable?
5. Es pot tenir una interfície web en el portàtil **només com a pantalla**, mentre tot el processament es fa a la placa?
6. Quina és l'hora límit i l'ordre d'entrega del **GitHub públic + Arduino Project Hub**?
7. És permès descarregar altres models o paquet extern durant el desenvolupament, si el sistema final funciona offline?

## Recomanació provisional

**Viabilitat tècnica: mitjana condicionada a la placa preparada.** Pot encaixar per l'experiència en Python i IA de l'equip, però té risc de setup/hardware, latència i OCR. **No escollir encara** fins llegir Tinybird i UPC Sostenible i confirmar que l'organització facilita la placa operativa.

Fonts: README i codi del repositori del repte; fitxa M3Kang https://huggingface.co/datasets/qualcomm/M3Kang ; fitxa Arduino UNO Q https://www.qualcomm.com/developer/hardware/arduino-uno-q
