# Hervé BI ou Quad — `code.py` (CircuitPython)

Ce fichier est le programme principal sur la carte (copié en `code.py` à la racine du volume **CIRCUITPY**). Il lit des **potentiomètres** analogiques et envoie soit des **messages MIDI** (Control Change), soit un **rapport HID Gamepad** (axes des joysticks), selon la position d’un **interrupteur** sur **GP5**.

Le descripteur HID gamepad et l’USB sont définis dans **`boot.py`** (à placer à la racine également). Sans `boot.py` adapté, le mode MIDI peut fonctionner, mais le **gamepad HID** peut être absent ou incorrect.

---

## Cible matérielle et firmware

Le **code** et le **design** (boîtier) ont été pensés pour un **RP2040 Zero (Waveshare)**, avec **CircuitPython 10.x.x** — utilise une build **compatible** avec cette carte (voir le site Adafruit / CircuitPython).

**Potentiomètres :** **2 à 4× 10 kΩ** (montage diviseur de tension vers l’ADC). Pour ajouter des voies, il suffit de **compléter le tuple `POT_GPIO`** dans `code.py` ; le reste (CC MIDI, second stick HID si 4 pots) s’adapte automatiquement.

Sur le **RP2040 Zero Waveshare**, les entrées analogiques sont en pratique repérées **GP26**, **GP27**, **GP28**, **GP29**.

**Exemple fourni dans le dépôt :** les potars **0** et **1** sont **inversés** par rapport aux broches du microcontrôleur (l’ordre dans `POT_GPIO` reflète le boîtier, pas forcément A0/A1 dans l’ordre « naturel »). **Corrige l’ordre des `board.GPxx`** selon **ta** configuration matérielle.

---

## Design (PDF) — découpe Trotec

Couleurs utilisables sur une machine **Trotec** (fichier PDF de découpe / gravure du boîtier) :

| Couleur | Rôle |
|---------|------|
| **Rouge** | Coupe (**cut**) |
| **Vert** | Coupe faible (**30 %**) |
| **Noir** | Gravure |

---

## Modes de fonctionnement

| État logique **GP5** | Comportement |
|----------------------|--------------|
| **LOW** (vers **GND**) | **MIDI** |
| **HIGH** (ligne « lâchée », tirée par le **pull-up** interne) | **HID** |

`use_midi = not mode_switch.value`. **GP5** est en **`Pull.UP`** dans `code.py` : interrupteur **2 broches** uniquement **GP5** + **GND** — **fermé** = MIDI, **ouvert** = HID. Aucun fil **3V3** sur l’interrupteur.

### Câblage **GP4** / **GP5**

Ne pas court-circuiter **GND** et **3V3**.

#### Boot — **`board.GP4`**

Bouton : **GP4** + **GND**.

#### MIDI / HID — **`board.GP5`**

Interrupteur **2 broches** : **GP5** + **GND**. Le firmware met **pull-up** sur **GP5** ; pas besoin de souder **3V3**.

---

## Entrées analogiques : `POT_GPIO`

- Chaque ligne du tuple **`POT_GPIO`** = un **pot logique** `pot[0]`, `pot[1]`, etc., avec la broche **`board.GPxx`** (ou alias ADC) utilisée.
- **`nPot = len(POT_GPIO)`** : le nombre de pots détermine automatiquement le nombre de **CC MIDI** et, en HID, si le **stick droit** est actif (voir ci‑dessous).
- Sur **RP2040**, jusqu’à **4 ADC** (**GP26–GP29**) ; sur le **Zero Waveshare**, repère les broches **GP26 à GP28** sur la doc carte, et **GP29** pour la 4e voie si tu fais un dual stick complet à 4 potars.

Aucune autre partie du script n’a besoin d’être modifiée pour ajouter des pots : il suffit d’**allonger `POT_GPIO`** (et éventuellement décommenter les lignes prévues dans les commentaires de `code.py`).

---

## MIDI — numéros de CC

Par défaut, les **CC MIDI** sont placés sur les **ports 31 et suivants** (numéros de *Control Change* / contrôleurs, via la constante **`addr`** dans `code.py`).

La constante **`addr`** (par défaut **31**) sert de base. La fonction **`_midi_cc_list(addr, nPot)`** construit la liste **`cc_number`** :

- **2 pots** : `pot[0]` → CC **32**, `pot[1]` → CC **31** (ordre historique du projet).
- **Plus de 2 pots** : les suivants reçoivent **33, 34, …** (`addr + 2`, `addr + 3`, …).

Chaque fois qu’une valeur **lissée** change pour un index `p`, le script envoie `ControlChange(cc_number[p], valeur)` sur le canal défini par **`USB_MIDI_channel`**.

### Lissage et détection de changement

- Les échantillons ADC sont convertis en **0–127** (échelle approximative via `65520`).
- **`nMesures` (10)** : moyenne glissante sur les **10** dernières lectures par pot pour limiter le bruit.
- Un envoi n’a lieu que si la moyenne diffère de l’avant‑dernière **et** de la dernière valeur retenue (filtre anti‑répétition / rebond logique).

### MIDI entrant — réinitialisation des pots

Si un message **`NoteOff`** arrive avec **`note == 64`**, le firmware renvoie l’état courant de chaque pot en **CC** (`oMesure[p]`), utile pour resynchroniser un hôte.

---

## HID — gamepad

- Le rapport suit **`boot.py`** : **6 octets**, **Report ID 4**, axes **X, Y, Z, Rz** sur **−127…127** (voir `_gamepad_move_joysticks`).
- **`_axis_from_pot`** : passage **0–127** → **−127…127** (centré).

### Affectation des axes

- **Stick gauche** (toujours si au moins **2** pots) : **`jy`** ← mesure du pot **0**, **`jx`** ← mesure du pot **1** (croisement volontaire par rapport aux indices, cohérent avec le câblage du boîtier).
- **Stick droit** : si **`len(POT_GPIO) >= 4`** (`MIN_POTS_HID_DUAL_STICK`), alors **`jr_z`** ← pot **2**, **`jz`** ← pot **3** (même logique de paire croisée que pour la gauche). Sinon **`jz`** et **`jr_z`** restent à **0**.

Au démarrage, le port série indique si le mode **dual stick** HID est actif ou combien de pots manquent pour l’activer.

---

## LED NeoPixel

Lors d’un changement de valeur traité (MIDI ou HID), la LED clignote brièvement : **rouge** si le pot concerné est l’index **0**, **bleu** sinon.

---

## Paramètres utiles à ajuster

| Paramètre | Rôle |
|-----------|------|
| `USB_MIDI_channel` | Canal MIDI sortant (1–16). |
| `addr` | Base des numéros de CC. |
| `POT_GPIO` | Broches ADC et ordre logique des pots. |
| `nMesures` | Nombre d’échantillons pour la moyenne (lissage). |
| `time.sleep(0.02)` dans la boucle | Cadence de lecture (~50 Hz). |

---

## Fichiers liés

- **`boot.py`** : identification USB optionnelle, activation du **device HID Gamepad** seul, et (côté matériel) **GP4** pour des options de stockage/USB (voir commentaires dans `boot.py`).
- **`code.py`** : tout le comportement temps réel décrit ci‑dessus ; **GP5** = choix MIDI / HID.

---

## Dépannage rapide

- **Pas de gamepad HID** au démarrage : message d’erreur sur le série — vérifier **`boot.py`** à la racine, **CircuitPython 10.x** (ou version testée avec la carte), redémarrage après copie.
- **Valeurs MIDI instables** : augmenter **`nMesures`** ou le délai dans la boucle.
- **Axes HID inversés ou permutés** : ajuster l’ordre des broches dans **`POT_GPIO`** ou, en dernier recours, la logique dans **`_hid_axes_from_omesure`**.

---

## English

### Hervé BI / Quad — `code.py` (CircuitPython)

This file is the main firmware on the board (copy it as `code.py` at the root of the **CIRCUITPY** volume). It reads **analog potentiometers** and sends either **MIDI messages** (Control Change) or an **HID Gamepad report** (joystick axes), depending on a **switch** wired to **GP5**.

The HID gamepad descriptor and USB setup live in **`boot.py`** (also at the root). Without a matching `boot.py`, **MIDI mode** may still work, but the **HID gamepad** may be missing or wrong.

#### Target hardware & firmware

The **firmware** and **enclosure design** target a **Waveshare RP2040 Zero** running **CircuitPython 10.x.x** — use a **board-compatible** build (see Adafruit / CircuitPython downloads).

**Potentiometers:** **2 to 4× 10 kΩ** (voltage divider into the ADC). Add channels by **extending the `POT_GPIO` tuple** in `code.py`; MIDI CC mapping and the HID right stick (when using four pots) follow automatically.

On the **Waveshare RP2040 Zero**, analog inputs are labelled **GP26**, **GP27**, **GP28** on the board docs; the RP2040’s **4th** ADC input is **GP29** — use it when wiring a **fourth** pot.

**Example in this repo:** pots **0** and **1** are **swapped** vs the MCU pin order (the tuple order matches the mechanical layout, not necessarily “A0 then A1”). **Adjust the `board.GPxx` order** to match **your** wiring.

#### Design (PDF) — Trotec laser

Layer colours for **Trotec** cutters (PDF for enclosure cut / engrave):

| Colour | Role |
|--------|------|
| **Red** | Cut |
| **Green** | Light cut (**30 %**) |
| **Black** | Engraving |

Add the path or filename of the project PDF here if you distribute the files.

#### Operating modes

| **GP5** logic level | Behaviour |
|---------------------|-----------|
| **LOW** (tied to **GND**) | **MIDI** |
| **HIGH** (line open, **internal pull-up**) | **HID** |

`use_midi = not mode_switch.value`. **GP5** uses **`Pull.UP`** in `code.py`: **2-pin** switch only **GP5** + **GND** — **closed** = MIDI, **open** = HID. No **3V3** wire on the switch.

##### Wiring **GP4** / **GP5**

Do not short **GND** and **3V3**.

###### Boot — **`board.GP4`**

Button: **GP4** + **GND**.

###### MIDI / HID — **`board.GP5`**

**2-pin** switch: **GP5** + **GND**. Firmware enables **pull-up** on **GP5**; no **3V3** soldered on the switch.

#### Analog inputs: `POT_GPIO`

- Each entry in the **`POT_GPIO`** tuple is a **logical pot** `pot[0]`, `pot[1]`, …, with the **`board.GPxx`** pin (or ADC alias) in use.
- **`nPot = len(POT_GPIO)`**: the pot count automatically sets how many **MIDI CCs** are used and, in HID, whether the **right stick** is active (see below).
- On **RP2040**, up to **four ADC channels** (**GP26–GP29**). On the **Waveshare Zero**, **GP26–GP28** are the usual analogue pins called out on the silkscreen; add **GP29** for a **fourth** pot / full dual-stick HID.

You do not need to edit the rest of the script to add pots: **extend `POT_GPIO`** (and uncomment the optional lines in `code.py` if present).

#### MIDI — CC numbers

By default, **MIDI CCs** use **controller numbers 31 and up** (*Control Change* IDs for the pots, via the **`addr`** constant in `code.py`).

The **`addr`** constant (default **31**) is the base. **`_midi_cc_list(addr, nPot)`** builds the **`cc_number`** list:

- **2 pots**: `pot[0]` → CC **32**, `pot[1]` → CC **31** (project history).
- **More than 2 pots**: further pots get **33, 34, …** (`addr + 2`, `addr + 3`, …).

Whenever the **smoothed** value for index `p` changes, the script sends `ControlChange(cc_number[p], value)` on the channel set by **`USB_MIDI_channel`**.

##### Smoothing and change detection

- ADC samples are scaled to **0–127** (approximate scale via `65520`).
- **`nMesures` (10)**: rolling average over the **last 10** samples per pot to reduce noise.
- A send happens only if the average differs from both the previous **and** the last accepted value (anti-repeat / logical debounce).

##### MIDI in — pot state dump

If a **`NoteOff`** message arrives with **`note == 64`**, the firmware sends each pot’s current value as **CC** (`oMesure[p]`), useful to resync a host.

#### HID — gamepad

- The report matches **`boot.py`**: **6 bytes**, **Report ID 4**, axes **X, Y, Z, Rz** in **−127…127** (see `_gamepad_move_joysticks`).
- **`_axis_from_pot`**: maps **0–127** → **−127…127** (centred).

##### Axis mapping

- **Left stick** (when there are at least **2** pots): **`jy`** ← pot **0**, **`jx`** ← pot **1** (intentional cross-mapping vs indices, matches the enclosure wiring).
- **Right stick**: if **`len(POT_GPIO) >= 4`** (`MIN_POTS_HID_DUAL_STICK`), then **`jr_z`** ← pot **2**, **`jz`** ← pot **3** (same cross-pair rule as the left stick). Otherwise **`jz`** and **`jr_z`** stay **0**.

At startup, the serial port prints whether **dual-stick** HID is active or how many more pots are needed.

#### NeoPixel LED

On each processed value change (MIDI or HID), the LED blinks briefly: **red** if the pot index is **0**, **blue** otherwise.

#### Useful tunables

| Parameter | Role |
|-----------|------|
| `USB_MIDI_channel` | MIDI output channel (1–16). |
| `addr` | Base CC numbers. |
| `POT_GPIO` | ADC pins and logical pot order. |
| `nMesures` | Samples averaged per pot (smoothing). |
| `time.sleep(0.02)` in the loop | Poll rate (~50 Hz). |

#### Related files

- **`boot.py`**: optional USB identification, enables the **HID Gamepad device** only, and (hardware) **GP4** for storage/USB options (see comments in `boot.py`).
- **`code.py`**: all real-time behaviour above; **GP5** selects MIDI vs HID.

#### Quick troubleshooting

- **No HID gamepad** at boot: error on serial — check **`boot.py`** at the root, **CircuitPython 10.x** (or the version you validated with the board), reboot after copy.
- **Unstable MIDI values**: increase **`nMesures`** or the loop delay.
- **HID axes swapped or inverted**: change pin order in **`POT_GPIO`**, or as a last resort adjust **`_hid_axes_from_omesure`**.
