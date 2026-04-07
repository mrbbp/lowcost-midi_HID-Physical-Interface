# GP4 : INPUT + Pull.UP (câblage du boîtier). Bloc USB disque / CDC en bas : actuellement en pass.
# + HID Gamepad (usage 0x05), descripteur aligné sur le guide Adafruit « Custom HID » (Report ID 4).
# GP5 : interrupteur MIDI/HID dans code.py uniquement.
#
# Ordre important : set_usb_identification AVANT usb_hid.enable, sinon l'USB
# est reconfigure et le HID redevient le triplet par defaut (clavier/souris/consumer).

import supervisor
import usb_hid

# Si cette ligne lève (CP < 8, ou bug carte), tout le boot s’arrête : tu retombes
# sur le HID par défaut (3 interfaces) sans message évident sur l’hôte.
try:
    supervisor.set_usb_identification("Herve Bi", "Herve Bi")
except Exception as _e:
    # Décommente pour voir l’erreur sur le port série au boot :
    # print("[boot] set_usb_identification ignoré:", _e)
    pass

# --- Gamepad HID : copie du descripteur Adafruit Learn (Report ID 4 obligatoire pour TinyUSB/CP) ---
# Sans 0x85 + report_ids=(4,), la pile peut garder le triplet HID par défaut ou refuser le device.
_GAMEPAD_REPORT_DESCRIPTOR = bytes(
    (
        0x05,
        0x01,  # Usage Page (Generic Desktop)
        0x09,
        0x05,  # Usage (Game Pad)
        0xA1,
        0x01,  # Collection (Application)
        0x85,
        0x04,  # Report ID (4)
        0x05,
        0x09,  # Usage Page (Button)
        0x19,
        0x01,
        0x29,
        0x10,
        0x15,
        0x00,
        0x25,
        0x01,
        0x75,
        0x01,
        0x95,
        0x10,
        0x81,
        0x02,
        0x05,
        0x01,  # Usage Page (Generic Desktop)
        0x15,
        0x81,  # Logical Minimum (-127)
        0x25,
        0x7F,  # Logical Maximum (127)
        0x09,
        0x30,  # X
        0x09,
        0x31,  # Y
        0x09,
        0x32,  # Z
        0x09,
        0x35,  # Rz
        0x75,
        0x08,
        0x95,
        0x04,
        0x81,
        0x02,
        0xC0,
    )
)

_GAMEPAD = usb_hid.Device(
    report_descriptor=_GAMEPAD_REPORT_DESCRIPTOR,
    usage_page=0x01,
    usage=0x05,
    report_ids=(4,),
    in_report_lengths=(6,),
    out_report_lengths=(0,),
)

usb_hid.enable((_GAMEPAD,))
print("boot.py OK: HID gamepad seul (usage 5)")

import storage
import usb_cdc
import board
import digitalio

button = digitalio.DigitalInOut(board.GP4)
button.direction = digitalio.Direction.INPUT
button.pull = digitalio.Pull.DOWN

if not button.value:
    # storage.disable_usb_drive()
    # usb_midi.disable()
    # usb_cdc.disable()
    pass
