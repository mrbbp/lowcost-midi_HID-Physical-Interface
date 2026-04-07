#
#   MIDI : CC dérivés de addr et du nombre de pots (voir _midi_cc_list) — pot0→32, pot1→31, puis 33…
#
#   GPIO : INPUT + Pull.UP sur ce boîtier (GP4 dans boot.py, GP5 ici).
#   GP5 : LOW → MIDI ; HIGH → HID (Gamepad). use_midi = not mode_switch.value
#   HID : 2 pots dans POT_GPIO = stick gauche (X,Y) ; 4+ pots = gauche (0,1) + droite Z,Rz (2,3).
#   Gamepad HID : rapport 6 octets + Report ID 4 dans boot.py (voir boot.py).
#
import time
import struct
from math import floor
import board
import digitalio
from analogio import AnalogIn
import usb_hid
import usb_midi as usb_midi_mod
import adafruit_midi
from adafruit_midi.control_change import ControlChange
from adafruit_midi.note_off import NoteOff

# gestion de la led
import neopixel
led = neopixel.NeoPixel(board.NEOPIXEL, 1)
led.brightness = 0  # éteind la led

# init du midi
USB_MIDI_channel = 1  # pick your USB MIDI out channel here, 1-16

midi = adafruit_midi.MIDI(
    midi_in=usb_midi_mod.ports[0], in_channel=USB_MIDI_channel - 1,
    midi_out=usb_midi_mod.ports[1], out_channel=USB_MIDI_channel - 1
)

print("--------------------------")
print("|    Hervé BI MIDI v2    |")
print("--------- @mrbbp ---------")
print("|   USB MIDI channel: {}  |".format(USB_MIDI_channel))
print("--------------------------")

# MIDI : base addr — CC par pot : pot0→addr+1, pot1→addr, puis addr+2, addr+3, …
addr = 31

# GP5 : interrupteur MIDI/HID, Pull.UP (identique au choix matériel de boot.py pour GP4).
mode_switch = digitalio.DigitalInOut(board.GP5)
mode_switch.direction = digitalio.Direction.INPUT
mode_switch.pull = digitalio.Pull.DOWN

# HID gamepad : même rapport 6 octets que boot.py.
# Si boot.py n’a pas tourné : 3 HID (usage 6 / 2 / 1), pas de gamepad (usage 5).
_hid_gamepad = None
_hid_list = tuple(usb_hid.devices)
print("--- HID (debug) ---")
print("nombre d’interfaces HID :", len(_hid_list))
for _i, _d in enumerate(_hid_list):
    print(" ", _i, "usage_page", _d.usage_page, "usage", _d.usage)
for _d in _hid_list:
    if _d.usage_page == 1 and _d.usage == 5:
        _hid_gamepad = _d
        break
if _hid_gamepad is None and len(_hid_list) == 1:
    _hid_gamepad = _hid_list[0]
if _hid_gamepad is None:
    print(
        "!!! Pas de gamepad HID : boot.py absent, pas à la racine CIRCUITPY, "
        "ou carte pas reset après copie. Mode MIDI OK ; mode HID ignoré."
    )
else:
    print("HID gamepad OK (send_report)")

def _gamepad_move_joysticks(jx, jy, jz, jr_z):
    if _hid_gamepad is None:
        return
    r = bytearray(6)
    struct.pack_into("<Hbbbb", r, 0, 0, jx, jy, jz, jr_z)
    try:
        _hid_gamepad.send_report(r)
    except OSError:
        _hid_gamepad.send_report(r, 4)


def _midi_cc_list(base, n_pot):
    """Un CC par entrée dans POT_GPIO : [base+1, base], puis base+2, base+3, …"""
    if n_pot <= 0:
        return []
    head = [base + 1, base]
    if n_pot <= 2:
        return head[:n_pot]
    return head + [base + 2 + i for i in range(n_pot - 2)]


def _axis_from_pot(m):
    """0..127 → -127..127 (centré)."""
    return max(-127, min(127, int(round(m * 2 - 127))))


def _hid_axes_from_omesure(o, n_pot, use_right_stick):
    """Stick gauche : jx←o[1], jy←o[0]. Stick droit (si 4 pots) : jz←o[3], jr_z←o[2] (même logique de croisement)."""
    jx = _axis_from_pot(o[1]) if n_pot > 1 else 0
    jy = _axis_from_pot(o[0]) if n_pot > 0 else 0
    if use_right_stick and n_pot >= 4:
        jz = _axis_from_pot(o[3])
        jr_z = _axis_from_pot(o[2])
    else:
        jz = 0
        jr_z = 0
    return jx, jy, jz, jr_z


# message de contrôle : LOW = MIDI, HIGH = HID
if mode_switch.value:
    print("GP5 initial: HIGH (vers +) -> mode HID")
else:
    print("GP5 initial: LOW (repos) -> mode MIDI")

# --- Potentiomètres (ADC) : une ligne = un pot logique pot[0], pot[1], … ---
# RP2040 : 4 canaux ADC (ADC0–ADC3) sur GP26–GP29 (souvent A0–A3 en CircuitPython).
# Waveshare RP2040 Zero : 4 broches ADC utilisables — dual stick HID = 4 lignes dans POT_GPIO.
# MIDI : pot[i] → cc_number[i]. HID : pots 0–1 = stick gauche ; 4 entrées → pots 2–3 = Z / Rz.
MIN_POTS_HID_DUAL_STICK = 4  # len(POT_GPIO) >= 4 → jz et jr_z alimentés (sinon 0).
POT_GPIO = (
    board.GP27,  # pot 0 — A1 / GP27 / ADC1
    board.GP26,  # pot 1 — A0 / GP26 / ADC0
    # Stick droit (Z, Rz) : décommenter sur carte 4 ADC (ex. RP2040 Zero Waveshare) :
    # board.GP28,  # pot 2 — A2 / GP28 / ADC2
    # board.GP29,  # pot 3 — A3 / GP29 / ADC3
)
nPot = len(POT_GPIO)
HID_USE_RIGHT_STICK = nPot >= MIN_POTS_HID_DUAL_STICK
cc_number = _midi_cc_list(addr, nPot)
pot = [AnalogIn(pin) for pin in POT_GPIO]

print("CC MIDI (par pot) =", cc_number)
print(
    "HID sticks : gauche (pots 0–1) ; droite Z/Rz activée"
    if HID_USE_RIGHT_STICK
    else "HID sticks : gauche seulement (ajoute {} pot(s) pour Z/Rz)".format(
        max(0, MIN_POTS_HID_DUAL_STICK - nPot)
    )
)

# Câblage : l’ordre dans POT_GPIO aligne physique ↔ logique ; ajuster ici si tu déplaces des fils.

compteur = 0
totalMesures = 0
nMesures = 10

# Initialize cc_value list with current value and offset placeholders
cc_value = [0]*nPot
valeurs = [0]*nMesures

for i in range(nPot):
    cc_value[i] = [0]*nMesures

# midi IN
msg = midi.receive()
oMesure = [0]*nPot
ooMesure = [0]*nPot


# GP5 : front simple (lecture != etat precedent) — le plus fiable pour voir un message serie.
# Si le contact rebondit, tu peux voir 2-3 lignes d un coup ; c est normal.
_sw_prev = not mode_switch.value

# boucle main
while True:
    use_midi = not mode_switch.value
    if use_midi != _sw_prev:
        _sw_prev = use_midi
        if use_midi:
            print("*** SWITCH GP5 -> MIDI (LOW / repos)")
        else:
            print("*** SWITCH GP5 -> HID (HIGH / vers +)")

    msg = midi.receive() if use_midi else None

    for i in range(nPot):
        cc_value[i][compteur % nMesures] = floor(pot[i].value / 65520 * 127)
        # print(math.floor(pot[0].value/65520*127))

    if compteur > nMesures:  # l'array est plein de mesures
        mesure = 0
        for p in range(nPot):
            totalMesures = 0
            for m in cc_value[p]:
                totalMesures += m
            mesure = round(totalMesures/nMesures)
            # print(mesure)
            if mesure != oMesure[p] and mesure != ooMesure[p]:
                ooMesure[p] = oMesure[p]
                oMesure[p] = mesure
                if use_midi:
                    print(cc_number[p], mesure)
                    midi.send(ControlChange(cc_number[p], mesure))
                else:
                    jx, jy, jz, jr_z = _hid_axes_from_omesure(
                        oMesure, nPot, HID_USE_RIGHT_STICK
                    )
                    if HID_USE_RIGHT_STICK:
                        print("HID jx jy jz Rz =", jx, jy, jz, jr_z)
                    else:
                        print("HID jx jy =", jx, jy)
                    _gamepad_move_joysticks(jx, jy, jz, jr_z)
                led.brightness = .3
                if p == 0:
                    led[0] = (255, 0, 0)
                else:
                    led[0] = (0, 0, 255)
                time.sleep(.005)
                led.brightness = 0
    # envoie des valeurs d'init
    if msg is not None:
        #  if a NoteOff message...
        if isinstance(msg, NoteOff):
            if msg.note == 64:  # si reçoit note 64 (renvoit les valeur des potars)
                print("envoie des etat initiaux potars")
                for p in range(nPot):
                    # Form a MIDI CC message and send it:
                    midi.send(ControlChange(cc_number[p], oMesure[p]))

    compteur += 1
    time.sleep(0.02)
    # previent un depassement de taille de compteur
    if compteur > nMesures*100000:
        compteur = 0




