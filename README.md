# Hervé BI ou Quad

Petit boîtier USB autour d’un **RP2040 Zero (Waveshare)** sous **CircuitPython 10.x** : il lit **2 à 4 potentiomètres 10 kΩ** et les expose à l’ordinateur soit en **MIDI** (messages de contrôle), soit en **HID gamepad** (axes de joysticks). Un **interrupteur** sur la carte choisit le mode **sans reconfigurer le firmware** : d’un côté tu as un contrôleur MIDI classique, de l’autre une manette reconnue par le système comme un gamepad.

Les sketchs **`code.py`** (boucle principale) et **`boot.py`** (USB + descripteur HID) vont à la racine du volume **CIRCUITPY**. Sans **`boot.py`** adapté, le MIDI peut marcher, mais le **gamepad HID** risque d’être absent ou incorrect.

---

## Ce que le firmware fait (fonctionnalités)

- **Deux modes USB** : **MIDI** (CC sur les mouvements de potars) ou **HID gamepad** (même potars pilotent des axes X/Y et, avec 4 potars, Z/Rz pour un second stick).
- **Bascule MIDI / HID** sur **GP5** : interrupteur **2 broches** vers **GND** uniquement ; le code active un **pull-up** interne — **contact fermé** = MIDI, **ouvert** = HID (pas de fil **3V3** sur l’interrupteur).
- **Numéros de CC MIDI** générés à partir de **`addr`** (défaut 31) : avec 2 pots, **32** puis **31**, puis **33, 34…** si tu ajoutes des voies (`_midi_cc_list`).
- **Lissage** sur plusieurs lectures par pot avant envoi, pour limiter le bruit et le spam MIDI.
- **MIDI entrant** : un **`NoteOff` canal courant, note 64** demande au boîtier de **renvoyer l’état actuel** de tous les pots en CC (pratique pour resynchroniser une appli).
- **LED NeoPixel** : flash court à chaque changement de valeur traité (couleur selon le pot).
- **Bouton / ligne boot** sur **GP4** : lu dans **`boot.py`** au démarrage (options USB commentées dans le fichier).

---

## Côté page web (navigateur)

Le boîtier est pensé pour être **simple à exploiter dans une page web** selon la position de l’interrupteur :

- **Mode MIDI** : utilise l’**[Web MIDI API](https://developer.mozilla.org/en-US/docs/Web/API/Web_MIDI_API)** (`navigator.requestMIDIAccess`). Tu reçois les **Control Change** sur les numéros décrits plus haut ; tu peux envoyer le **`NoteOff` note 64** pour forcer un rafraîchissement des valeurs.
- **Mode HID gamepad** : utilise l’**[Gamepad API](https://developer.mozilla.org/en-US/docs/Web/API/Gamepad_API)** (`navigator.getGamepads()` + événements `gamepadconnected`). Les axes apparaissent comme ceux d’une manette standard ; pas besoin de pilote spécifique côté navigateur.

HTTPS ou `localhost` selon les exigences du navigateur pour Web MIDI ; la Gamepad API fonctionne en général dès que le périphérique est vu comme gamepad.

---

## Branchements (résumé)

| Élément | Connexion |
|---------|-----------|
| **Boot** | **GP4** + **GND** |
| **Interrupteur MIDI / HID** | **GP5** + **GND** (2 broches, **pull-up** firmware) |
| **Potars** | Une entrée du tuple **`POT_GPIO`** = un pot ; broches ADC **GP26–GP29** selon ton montage |

Ne pas court-circuiter **GND** et **3V3**.

**Découpe laser Trotec (PDF boîtier) :** rouge = coupe, vert = coupe faible 30 %, noir = gravure.

---

## Où regarder dans le code

| Fichier / symbole | À quoi ça sert |
|-------------------|----------------|
| **`POT_GPIO`** | Liste des broches ADC = pot 0, 1, … ; **4** lignes → stick droit HID actif. |
| **`addr`**, **`_midi_cc_list`** | Base et liste des numéros de CC. |
| **`USB_MIDI_channel`** | Canal MIDI sortant (1–16). |
| **`mode_switch`**, **`use_midi`** | **GP5**, **`Pull.UP`**, logique `not mode_switch.value`. |
| **`_hid_axes_from_omesure`**, **`_gamepad_move_joysticks`** | Conversion pot → axes gamepad. |
| **`boot.py`** | Descripteur HID gamepad (report ID 4), **GP4** au boot. |

**Si le gamepad n’apparaît pas :** `boot.py` bien à la racine, build CircuitPython compatible avec la carte, redémarrage après copie des fichiers.

---

## English

Same device: **USB box** with **2–4 pots**, **MIDI** or **HID gamepad** selected by a **2-pin switch** on **GP5** (firmware **pull-up** — **closed to GND** = MIDI, **open** = HID). **Waveshare RP2040 Zero**, **CircuitPython 10.x**. **`code.py`** + **`boot.py`** at **CIRCUITPY** root.

**Features:** CC output with smoothing, **NoteOff note 64** requests full pot state over MIDI, **NeoPixel** blink on change, optional **4-pot** mapping to **dual analog sticks** in HID. **GP4** + **GND** boot input in **`boot.py`**.

**Web:** **Web MIDI API** in MIDI mode; **Gamepad API** in HID mode (`getGamepads`), no extra browser driver.

**Wiring:** **GP4–GND** boot; **GP5–GND** switch only; pots in **`POT_GPIO`** on **GP26–GP29**. **Trotec:** red = cut, green = 30 % cut, black = engrave.

**Code map:** **`POT_GPIO`**, **`addr`** / **`_midi_cc_list`**, **`USB_MIDI_channel`**, **`use_midi`** / **GP5**, **`boot.py`** for HID descriptor. If HID missing: **`boot.py`** at root, reboot.
