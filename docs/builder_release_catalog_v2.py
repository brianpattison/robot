"""Lightweight shopping catalog shared by the v2 guide and release index.

This module deliberately depends only on tracked JSON and the Python standard
library so the immutable builder-release page can be checked in clean CI.
The full guide still cross-checks the fastener tally against the CAD registry.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLATES = json.loads(
    (ROOT / "cad" / "bambu" / "codex_robot_body_v2_p1s_plates.json").read_text()
)

FASTENER_COUNT = 47
THEME_NAMES = {
    "structure_light": "White",
    "structure_wear": "Black",
    "safety_service": "Red",
    "dark_panel": "Charcoal",
    "top_accent": "Teal",
    "light_diffuser": "Translucent lime",
    "flexible_dark": "Charcoal",
}

_groups: dict[str, dict] = {}
for _plate in PLATES["plates"]:
    _groups.setdefault(_plate["filament_group"], {"plate": _plate, "count": 0})["count"] += 1

SHOP_FILAMENT = []
for _group in _groups.values():
    _plate, _count = _group["plate"], _group["count"]
    _theme_name = THEME_NAMES[_plate["color_profile"]]
    _amount = (
        "one 1 kg spool; confirm the slicer estimate"
        if _count >= 4
        else "one 500 g spool"
        if _plate["material"].startswith("TPU")
        else "a small spool or known-good leftovers"
    )
    _label = (
        f"{_theme_name} PLA"
        if _theme_name.startswith("Translucent") and "PLA" in _plate["material"]
        else f"{_theme_name} {_plate['material']}"
    )
    SHOP_FILAMENT.append(
        (
            _label,
            _amount,
            f"{_plate['recommended_process']['role']} "
            f"({_count} plate{'s' if _count != 1 else ''}).",
        )
    )

SHOP_FASTENERS = [
    (
        "M3 × 8 mm socket head screws",
        "one 100-pack",
        f"The ONLY screw in the robot ({FASTENER_COUNT} used + spares).",
    ),
    (
        "M3 × 5.7 mm brass heat-set inserts (4.6 mm OD)",
        "one 100-pack",
        f"The only insert ({FASTENER_COUNT} used + spares).",
    ),
]

SHOP_ELECTRONICS = [
    ("Raspberry Pi 5 (8 GB)", "1", "The robot’s computer."),
    ("32 GB+ A2 microSD card", "1", "The computer’s memory card — the robot’s programs live here."),
    ("Raspberry Pi Camera Module 3 Wide + long FPC cable", "1", "The robot’s eye."),
    ("Raspberry Pi Pico 2 (no headers, no WiFi)", "1", "The safety helper: reflexes and watchdog."),
    ("Cytron MDDS10 motor driver", "1", "The purple board that powers the wheels."),
    ("Pololu #4867 gearmotor (99:1, 25D, 12 V, encoder)", "2", "The wheel motors."),
    ("Hitec D85MG servo", "2", "The neck motors (look left/right, up/down)."),
    ("Hitec R-ML24 aluminum horn (H24T)", "2", "One per servo; 22 mm single arm with M2 × 0.4 stations at 13 and 16 mm."),
    ("Verified D85MG/R-ML24 component hardware pack", "1 set", "2 spline-center screws, 4 M2 horn-link screws, and both servos’ mounting grommets, eyelets, screws, and nuts. Confirm the delivered pack against the head coupons before use."),
    ("Bioenno BLF-1203AB 12 V 3 Ah LiFePO4 battery", "1", "The robot’s power pack."),
    ("Bioenno BPC-1502DC charger", "1", "The matching charger. Only ever use this one."),
    ("Switchcraft EN2P3M20 inlet + EN2C3F20G2 plug", "1 pair", "The keyed charging plug on the back."),
    ("Pololu D24V90F5 regulator (5 V)", "1", "Makes clean 5 V for the Pi."),
    ("Pololu D36V50F6 regulator (6 V)", "1", "Makes 6 V for the neck servos."),
    ("Panasonic CB1A-R-M-12V relay", "1", "The motor power switch the red button controls."),
    ("Blue Sea Systems 5045 fuse block", "1", "Splits power safely into four fused branches."),
    ("ATO fuse assortment (values not released)", "1 kit", "Prototype starting values require measured load, conductor, inrush, selective-clearing, and thermal tests before use."),
    ("IDEC XW1E-BV402M-R emergency stop", "1", "THE BIG RED BUTTON."),
    ("E-Switch PVB3F230SS311 mute switch", "1", "The microphone privacy switch (glows red when muted)."),
    ("Omron D2HW-C202MR bumper switches", "6", "Feelers inside the bumpers."),
    ("VL53L1X time-of-flight boards (Adafruit 3967)", "4", "Distance eyes: two in front, one each side."),
    ("Adafruit 5975 NeoPixel breakouts + JST-SH cables", "4", "The glowing eyes and status lights."),
    ("ReSpeaker USB mic array", "1", "The robot’s ears."),
    ("Enclosed 3 W 4 ohm speakers + 2× Adafruit MAX98357A amps", "1 set", "The robot’s voice."),
    ("Prototype wire, terminal, and connector kit", "not released", "The production terminal schedule, measured lengths, and crimp tooling are still open; do not improvise a powered harness from this preview."),
]
