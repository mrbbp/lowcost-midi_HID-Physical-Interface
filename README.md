# Hervé BI ou Quad — CircuitPython

`code.py` à la racine **CIRCUITPY** : potars → **MIDI** (CC) ou **HID gamepad**, selon **GP5**. **`boot.py`** à la racine aussi : sans lui, pas de gamepad HID correct.

**Carte visée :** RP2040 Zero **Waveshare**, **CircuitPython 10.x**. Potars **10 kΩ**, **2 à 4** voies analogiques (**GP26–GP29**). Liste des broches dans **`POT_GPIO`** (`code.py`).

---

## Branchements

| Élément | Connexion |
|---------|-----------|
| **Bouton boot** | **GP4** + **GND** (`boot.py`) |
| **Interrupteur MIDI / HID** | **GP5** + **GND** seulement (2 broches). **`Pull.UP`** dans `code.py` : **fermé** = MIDI, **ouvert** = HID. Pas de **3V3** sur l’int. |
| **Potars** | Une ligne de **`POT_GPIO`** = un pot ; broches **GP26…GP29** selon ton câblage. |

Ne pas court-circuiter **GND** et **3V3**.

**PDF découpe Trotec :** rouge = coupe, vert = coupe 30 %, noir = gravure.

---

## Lire le code (`code.py`)

| Élément | Rôle |
|---------|------|
| **`POT_GPIO`** | Ordre des broches ADC = pot 0, 1, … Ajouter des lignes = plus de CC + stick droit HID si **4** pots. |
| **`addr`** (défaut **31**) | CC : pot0→**32**, pot1→**31**, puis **33, 34…** (`_midi_cc_list`). |
| **`USB_MIDI_channel`** | Canal MIDI sortant. |
| **`use_midi`** | `not mode_switch.value` — **GP5** en **`Pull.UP`**. |
| **HID** | 2 pots : axes gauche (pot 0 / 1 croisés). 4 pots : + Z/Rz (`_hid_axes_from_omesure`). Descripteur dans **`boot.py`**. |
| **MIDI entrant** | `NoteOff` **note 64** → renvoie les CC des pots. |

**`boot.py`** : HID gamepad seul + lecture **GP4** au démarrage (options USB commentées).

**Problème fréquent :** pas de HID au boot → `boot.py` présent à la racine, CP compatible, reset après copie.

---

## English (short)

Same project: **`code.py`** on **CIRCUITPY** (pots → MIDI or HID), **`boot.py`** required for HID gamepad. **Waveshare RP2040 Zero**, **CircuitPython 10.x**. Pots **10 kΩ**, **GP26–GP29** listed in **`POT_GPIO`**.

**Wiring:** **GP4** + **GND** = boot button. **GP5** + **GND** 2-pin switch only; firmware **`Pull.UP`** on **GP5** — **closed** = MIDI, **open** = HID. No **3V3** on the switch.

**Code:** **`POT_GPIO`** = pin list; **`addr`** = CC base — two pots: **32** then **31**, then **33…**; **`USB_MIDI_channel`**; **`use_midi`** = `not mode_switch.value`. **HID** report from **`boot.py`**. **`NoteOff` note 64** = dump pot CCs.

**Trotec PDF:** red = cut, green = 30 % cut, black = engrave.

If HID missing: put **`boot.py`** at root, matching CP build, reboot.
