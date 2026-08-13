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

FASTENER_COUNT = 51
THEME_NAMES = {
    "structure_light": "White",
    "structure_wear": "Black",
    "safety_service": "Red",
    "dark_panel": "Charcoal",
    "top_accent": "Teal",
    "light_diffuser": "Translucent lime",
    "flexible_dark": "Charcoal",
}

FILAMENT_GROUPS: dict[str, dict] = {}
for _plate in PLATES["plates"]:
    FILAMENT_GROUPS.setdefault(
        _plate["filament_group"], {"plate": _plate, "count": 0}
    )["count"] += 1

SHOP_FILAMENT = []
for _group in FILAMENT_GROUPS.values():
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

SHOP_FILAMENT.append(
    (
        "Candidate body-color PLA (optional)",
        "one spool per color you audition",
        "Proof try-out only: the shell/head color you hope to qualify. "
        "Those parts print white PETG until a candidate passes its recorded checks.",
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

# Commissioning-grade bench equipment. The 27-step plan specifies acceptance
# thresholds down to millivolts and milliseconds; this table names the
# instruments those thresholds assume so no builder has to reverse-engineer
# the equipment list from the acceptance math. Quantity-one US retail rule
# applies as everywhere else.
SHOP_BENCH_GEAR = [
    ("Current-limited DC bench supply (0–15 V, ≥3 A, settable current limit)",
     "1",
     "Regulator bring-up (C006), the fixture's 0.20 A negative-control stage, the "
     "low-battery sweep (C017), and the 6 V servo bench (C022). A settable limit is "
     "the requirement; programmable sweep is a convenience."),
    ("Multimeter with continuity beeper, mV resolution, and 0.01 A DC current",
     "1",
     "Every continuity check in the harness traveler, the ≤100 mV mute/backfeed "
     "readings (C018), and the per-motor / pack current ceilings (C024)."),
    ("Contactless IR thermometer (or thermocouple meter)",
     "1",
     "Terminal, conductor, servo, motor, driver, and pack temperature evidence "
     "(C019, C022, C024, C025)."),
    ("Raspberry Pi Debug Probe (SC0889)",
     "1",
     "Already in the fixture BOM: the Pi debug-console attestation cable, the "
     "Pico service corridor, and the one-time independent cross-check of the "
     "firmware's self-reported stop-latency telemetry."),
]

SHOP_ELECTRONICS = [
    ("Raspberry Pi 5 (8 GB)", "1", "The robot’s computer."),
    ("32 GB+ A2 microSD card", "1", "The computer’s memory card — the robot’s programs live here."),
    ("Raspberry Pi Camera Module 3 Wide + Pi 5 camera cable (22-pin, 300 mm)", "1", "The robot’s eye. The Pi 5 uses the small 22-pin camera connector — the 15-pin cable in the camera box fits older Pis, not this one."),
    ("Raspberry Pi Pico 2 (no headers, no WiFi)", "1", "The safety helper: reflexes and watchdog."),
    ("Cytron MDDS10 motor driver", "1", "The purple board that powers the wheels."),
    ("Pololu #4867 gearmotor (99:1, 25D, 12 V, encoder)", "2", "The wheel motors."),
    ("Hitec D85MG servo", "2", "The neck motors (look left/right, up/down). The single arm, spline screw, grommets, and eyelets in each servo's own bag are the drive parts — the old metal-horn and hardware-pack rows are retired (D048), so there is nothing extra to buy. Confirm the delivered arm against the horn-capture proof before the head steps."),
    ("Bioenno BLF-1203AB 12 V 3 Ah LiFePO4 battery", "1", "The robot’s power pack."),
    ("Bioenno BPC-1502DC charger", "1", "The matching charger. Only ever use this one."),
    ("Switchcraft EN2P3M20 inlet + EN2C3F20G2 plug", "1 pair", "The keyed charging plug on the back."),
    ("Pololu D24V90F5 regulator (5 V)", "1", "Safe to buy — the settled pick, and since D053 it feeds the head servos too (the separate 6 V rail is retired; its deck bay stays as a reserved spare). What stays BLOCKED is wiring it: the novice-safe locking Pi input, backfeed protection, downstream fusing, boot/load margin, thermal proof, and the shared-rail servo-transient bench test are open; never feed the GPIO header from this preview."),
    ("Panasonic CB1A-R-M-12V relay", "1", "The motor power switch the red button controls."),
    ("Production relay driver", "not released", "BLOCKED, but the candidate is selected (D054): the fixture's Adafruit 5648 MOSFET driver, promoted from negative-control duty. Exit: positive-control conditioning, fit, and EE review — one bench session with a part already in the fixture box."),
    ("Pico-local physical reset", "not released", "BLOCKED, but the candidate is selected (D055): a seventh Omron D2HW — the same switch the bumpers already trust — recessed behind a printed guard in the rear service corridor. Exit: conditioning circuit + CAD pocket."),
    ("Blue Sea Systems 5045 fuse block", "1", "Splits power safely into fused branches. D058 proposes replacing it with two sealed inline ATO holders now that the 6 V branch is retired — hold this purchase if you want to wait for that decision."),
    ("ATO/ATC fuse assortment box", "1", "Buy the cheap assortment; INSTALL NOTHING. Every value stays a release gate until measured load, conductor, inrush, time-current, selective-clearing, and thermal evidence is reviewed — owning fuses is harmless, installing unproven values is not."),
    ("IDEC XW1E-BV402M-R emergency stop", "1", "THE BIG RED BUTTON."),
    ("E-Switch PVB3F230SS311 mute switch", "1", "The microphone privacy switch (glows red when muted)."),
    ("Omron D2HW-C202MR bumper switches", "6", "Feelers inside the bumpers."),
    ("VL53L1X time-of-flight boards (Adafruit 3967)", "2 (+2 optional)", "Distance eyes. Two in front are the baseline; the side pair is optional garnish (D057) — the bumpers are the safety floor and the camera is the perception plan. The side windows and clamps stay in the prints either way."),
    ("Adafruit 5975 NeoPixel breakouts + JST-SH cables", "4", "The glowing eyes and status lights."),
    ("USB microphone (any small one to start; ReSpeaker array as the upgrade)", "1", "The robot's ears. Any plain USB mic clears bring-up (D060); the ReSpeaker array slot remains for when the voice software earns it — its exact revision plus the true VBUS-cut/no-backfeed mute interface remain BLOCKED either way."),
    ("Enclosed 3 W 4 ohm speakers + 2× Adafruit MAX98357A amps", "1 set", "The robot’s voice."),
    ("Harness bench stock (WAGO 221-412/415 lever nuts, label tape, wire in the traveler's published gauges)", "1 set", "Safe to buy under the D047 termination policy — lever nuts are already trusted fixture hardware. Owning stock is not wiring: the battery stays out and nothing gets crimped until the release below."),
    ("Production terminals + measured cut list", "not released", "The exact terminal schedule, measured lengths, and the one named crimper are still open; do not improvise a powered harness from this preview."),
]
