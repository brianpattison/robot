"""Generate the v2 assembly guide: print-first HTML -> PDF, ages 10+.

Authors the complete builder's book as fixed-size HTML pages (11 x 8.5 in
landscape) designed like a professionally produced kit manual, then prints
it to PDF with headless Chrome. Content is generated from the live
artifacts — the printed-part registry, joint/fastener registries, the
Bambu plate manifest, and the coupon manifest — plus the authored step
and wiring copy below, so the book cannot drift from the model.

Pages: cover with a real table of contents, the annotated "meet the
robot" spread, the how-to-read anatomy page, shopping (filament /
fasteners / electronics / tools), printing with Bambu Studio (plates +
coupons + a LEGO-style piece inventory), twenty assembly steps with
progress bars and checks, the electronics orientation page, the wiring
chapter with SVG power and signal maps, the first-checks page, and a
back cover. The design system: Avenir Next type, chapter thumb tabs,
hairline tables, and the cream/teal/lime robot palette.

Run the v2 chain and both render passes first, then:
    .venv-cad/bin/python docs/generate_assembly_guide_v2.py
Outputs:
    output/guide/codex_robot_body_v2_guide.html
    output/pdf/codex_robot_body_v2_assembly_guide.pdf
Verify pages with pypdfium2 (poppler is not installed here).
"""

from __future__ import annotations

import html
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "cad" / "python"))

import robot_body_v2_inventory as inv  # noqa: E402

IMG = ROOT / "docs" / "images"
GUIDE_IMG = IMG / "guide_v2"
PLATES = json.loads((ROOT / "cad" / "bambu" / "codex_robot_body_v2_p1s_plates.json").read_text())
N_PLATES = len(PLATES["plates"])
N_PIECES = sum(pl["part_count"] for pl in PLATES["plates"])
INVENTORY_COUNTS = PLATES.get("inventory_counts", {})
N_FUNCTIONAL = INVENTORY_COUNTS.get("functional_installed", 40)
N_SPARES = INVENTORY_COUNTS.get("spares", 4)
N_OPTIONAL = INVENTORY_COUNTS.get("optional_cosmetics", max(0, N_PIECES - N_FUNCTIONAL - N_SPARES))
COUPONS = json.loads((ROOT / "cad" / "exports" / "v2" / "coupons" /
                      "codex_robot_body_v2_coupons_manifest.json").read_text())
COUPON_NOTES = {
    "coupon_insert_m3": "Melt one insert into each of the three holes. The one that sits flush without squeezing out goo is your printer’s perfect fit.",
    "coupon_joint_flange": "Screw the small plate onto the block with one screw. It should pull down tight with no wobble and no cracking.",
    "coupon_joint_boss": "The partner block for the plate test above.",
    "coupon_dbore_torque": "Push this onto a motor shaft and twist HARD — twice as hard as driving ever will. If it never slips, wheels are safe.",
    "coupon_axle_stub": "Spin the ring on the peg a few hundred times with some pressure. It should stay smooth, not sloppy.",
    "coupon_bushing_ring": "The spinning ring for the peg test above.",
    "coupon_snap_pair": "Click the two pieces together and apart ten times. The little hook must survive and still hold on.",
    "coupon_bayonet_pair": "Twist the ring onto the stub a quarter turn — it should lock with a nice click and not pull straight off.",
    "coupon_switch_pocket": "Seat one bumper switch in the pocket: it must click when pressed and spring back, never jammed.",
    "coupon_tire_fit": "Stretch the mini tire onto the mini wheel. Snug and even = your big tires will fit too.",
    "coupon_pcb_clamp": "Rest the little green safety board on the pegs and screw the bar over it. Held gently, nothing bending.",
    "coupon_pla_insert_shell": "Use your exact body PLA and record the insert temperature. No white stress marks, cracks, sink, tilt, or pull-through.",
    "coupon_pla_shell_wall": "Check the wall, rounded edge, opening, and panel seat after a bump test, warm soak, and full cool-down.",
    "coupon_pla_head_pivot": "Fit the insert and bushing, load it like the finished head, then check for cracks and growing wobble.",
    "coupon_pla_snap_pair": "Print this in every candidate visible PLA. Click it ten times; it must still latch fully with no whitening or crack.",
    "coupon_pla_optical": "Print once per translucent PLA family/color. Compare the three thicknesses for brightness, hot spots, heat, and camera flare.",
    "coupon_lid_boundary_petg": "Print with the white PETG lid profile and mate it to the teal PLA tab. The blind socket must not crack.",
    "coupon_lid_boundary_pla": "Snap into the white PETG coupon ten times, warm it, and check that it still holds without rattling.",
}
COUPON_TITLES = {
    "coupon_insert_m3": "Insert fit",
    "coupon_joint_flange": "Screw joint",
    "coupon_joint_boss": "Screw joint partner",
    "coupon_dbore_torque": "Wheel grip",
    "coupon_axle_stub": "Axle spin",
    "coupon_bushing_ring": "Axle spin ring",
    "coupon_snap_pair": "Snap click",
    "coupon_bayonet_pair": "Bayonet twist",
    "coupon_switch_pocket": "Switch pocket",
    "coupon_tire_fit": "Tire stretch",
    "coupon_pcb_clamp": "Board clamp",
    "coupon_pla_insert_shell": "PLA insert boss",
    "coupon_pla_shell_wall": "PLA shell wall",
    "coupon_pla_head_pivot": "PLA head pivot",
    "coupon_pla_snap_pair": "PLA snap",
    "coupon_pla_optical": "PLA light test",
    "coupon_lid_boundary_petg": "PETG lid socket",
    "coupon_lid_boundary_pla": "PLA skin tab",
}
HTML_OUT = ROOT / "output" / "guide" / "codex_robot_body_v2_guide.html"
PDF_OUT = ROOT / "output" / "pdf" / "codex_robot_body_v2_assembly_guide.pdf"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

SCREWS = {j.name: len(j.positions) for j in inv.JOINTS}

# Per-camera FRONT hint: rear-camera steps see the front on the far side.
FRONT_LABEL = {
    "step_03_motors": "&#8598; FRONT (far side)",
    "step_06_wheels_on": "&#8598; FRONT (far side)",
    "step_15_panels": "&#8601; FRONT",
    "step_04_wheels_bench": None,   # bench shot, no robot orientation
}
# Inset panels overlaid on a step's big picture: render name + caption.
INSETS = {
    "step_13_shell": ("step_13b_shell_inserts", "All 14 insert spots"),
}
EXTRA_PANELS = {
    "step_10_pico": [("step_10b_pico_close", "USB end, SWD end, and clamp landing")],
    "step_12_deck": [
        ("step_12b_regulators", "Underside: distinct 5 V and 6 V regulators"),
        ("step_12c_fuse", "Topside: covered fuse block and wire edge"),
    ],
    "step_14_bumpers": [("step_14b_switch_underside", "Underside: all 6 NC feeler positions")],
    "step_15_panels": [("step_15b_rear_panel", "Separate rear view: charge, blank, mute")],
    "step_16_speakers": [("step_16b_audio_close", "One side enlarged: speaker, clamp, ToF")],
    "step_17_lid": [
        ("step_17b_lid_inserts", "Lid flipped: the 2 mic bosses"),
        ("step_17c_estop_stack", "Full E-stop body, nut, and 2 NC blocks"),
    ],
    "step_18_neck": [
        ("step_18b_neck_cutaway", "Lid hidden: collar, cradle, servo, plate, horn"),
    ],
    "step_19_head": [
        ("step_19b_tilt_stack", "Tilt servo, horn, hard stops, passive bushing"),
        ("step_19c_camera", "Camera board, lens, and ribbon entrance"),
    ],
}
N_SCREWS, N_INSERTS = inv.fastener_tally()

# Friendly names for parts (printed and purchased) used in strips and the
# piece inventory. Keys are registry/thumbnail base names.
PART_NAMES = {
    "tray_v2": "floor tray", "deck_v2": "power deck",
    "controller_tower_v2": "brain tower", "battery_clamp_v2": "battery clamp",
    "speaker_clamp_v2": "speaker clamp", "yoke_v2": "head yoke",
    "mic_cradle_v2": "mic cradle", "head_pan_plate_v2": "pan-servo plate",
    "pico_clamp_v2": "safety-board clamp", "front_pod_left_v2": "front pod (L)",
    "front_pod_right_v2": "front pod (R)", "motor_cap_v2": "motor cap",
    "tof_clamp_v2": "sensor clamp", "tilt_bushing_v2": "tilt bushing",
    "printed_washer_v2": "washer", "front_wheel_v2": "front wheel",
    "rear_wheel_v2": "back wheel", "shell_v2": "body shell",
    "head_shell_v2": "head shell", "bayonet_collar_v2": "neck collar",
    "neck_v2": "neck", "lid_v2": "lid", "head_faceplate_v2": "head face",
    "lid_skin_v2": "optional lid skin",
    "rear_panel_v2": "back panel", "fascia_v2": "face panel",
    "status_diffuser_bar_v2": "status light bar",
    "eye_diffuser_bar_v2": "eye light bar",
    "bumper_front_v2": "front bumper", "bumper_rear_v2": "back bumper",
    "battery_pad_frame_v2": "battery pad", "tire_v2": "tire",
    "px_insert": "brass inserts", "px_screw": "M3 screws",
    "px_motor_L": "gearmotors", "px_mdds10": "motor board",
    "px_pi": "Raspberry Pi", "px_battery": "battery", "px_relay": "relay",
    "px_fuse": "fuse block", "px_reg1": "regulators",
    "px_switch": "feeler switches", "px_tof_L": "distance boards",
    "px_speaker_L": "speakers", "px_estop_cap": "red button",
    "px_mic": "mic array", "px_servo": "D85MG + R-ML24", "px_camera": "camera",
    "px_pico": "Pico 2",
}
STRIP_NAME_OVERRIDES = {
    ("step_05_front_pods", "front_pod_left_v2"): "front pods",
    ("step_14_bumpers", "bumper_front_v2"): "bumpers",
    ("step_03_motors", "motor_cap_v2"): "motor caps",
}

# Chapter system: (tab label, accent color, TOC line). Page numbers are
# computed at assembly time.
CHAPTERS = [
    ("SHOP", "#B8892E", "Shop", "every spool, screw, and circuit board"),
    ("PRINT", "#0B6E84", "Print", "prototype plates, test parts, and a piece check"),
    ("BUILD", "#075365", "Build", "twenty steps from flat tray to finished robot"),
    ("WIRE", "#C4230F", "Wire", "the power and signal maps, checked with a meter"),
    ("PLAY", "#74A22D", "Check &amp; play", "safety tests first, then floor time"),
]

# ---------------------------------------------------------------------------
# Authored content
# ---------------------------------------------------------------------------
_groups: dict[str, dict] = {}
for _plate in PLATES["plates"]:
    _groups.setdefault(_plate["filament_group"], {"plate": _plate, "count": 0})["count"] += 1
SHOP_FILAMENT = []
for _group in _groups.values():
    _plate, _count = _group["plate"], _group["count"]
    _theme = inv.DEFAULT_THEME[_plate["color_profile"]]
    _amount = ("one 1 kg spool; confirm the slicer estimate" if _count >= 4 else
               "one 500 g spool" if _plate["material"].startswith("TPU") else
               "a small spool or known-good leftovers")
    _label = (f"{_theme['name']} PLA" if _theme["name"].startswith("Translucent") and "PLA" in _plate["material"]
              else f"{_theme['name']} {_plate['material']}")
    SHOP_FILAMENT.append((
        _label,
        _amount,
        f"{_plate['recommended_process']['role']} ({_count} plate{'s' if _count != 1 else ''}).",
    ))
SHOP_FASTENERS = [
    ("M3 × 8 mm socket head screws", "one 100-pack", f"The ONLY screw in the robot ({N_SCREWS} used + spares)."),
    ("M3 × 5.7 mm brass heat-set inserts (4.6 mm OD)", "one 100-pack", f"The only insert ({N_INSERTS} used + spares)."),
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
    ("Prototype wire, terminal, and connector kit", "not released", "The exact harness schedule and crimp tooling are still open; do not improvise a powered harness from this preview."),
]
SHOP_TOOLS = [
    ("2.5 mm hex key", "Turns every screw in this robot. Seriously, all of them."),
    ("6 V current-limited servo tester", "Centers both D85MG servos at 1500 µs before either horn goes on."),
    ("Soldering iron", "Melts the brass inserts into the plastic. Hot — treat it with respect."),
    ("Small flush cutters / scissors", "Trims zip ties and TPU strings."),
    ("Painter’s tape + marker", "Label wires as you go."),
    ("Multimeter", "Checks every circuit before the battery ever goes in."),
]

PRINT_TIPS = [
    ("Open the prototype project", f"Open <b>codex_robot_body_v2_p1s.3mf</b> in Bambu Studio. Its {N_PLATES} plates are laid out for geometry review on a P1S with a 0.4 mm nozzle and Textured PEI plate; physical release gates remain open."),
    ("Load the exact family + color", "Each plate names one material and one theme color. Never substitute PLA for a white/black/red PETG plate just to preserve the palette."),
    ("No supports", "Every part targets zero supports. If the slicer asks for supports, stop and re-check the source, plate, and declared orientation."),
    ("TPU is slow and squishy", "Print the tire and bumper plates slowly (the profile already does this). Dry TPU prints much better."),
    ("Big flat parts stay put", "The tray, shell, lid, skin, and bumper plates use lots of bed. Clean the plate with dish soap first so they stick."),
]

# Step tuple: (render name, title, screws, strip items, moves, check).
STEPS = [
    ("step_01_tray", "Start with the floor", 0,
     [("tray_v2", 1)],
     ["Clear a big table. Put the tray down flat, wheel cutouts toward you.",
      "Find the two round motor cradles at the back and the tall round towers — that’s the back of the robot."],
     "The tray sits flat and doesn’t rock."),
    ("step_02_inserts", "Melt in the tray’s brass inserts", 0,
     [("px_insert", 20)],
     ["Heat the soldering iron to about 220 °C — insert temperature.",
      "Rest a brass insert in each gold-marked hole, then press it straight down with the hot iron tip until it sits flush. (The gold pegs in the pictures just point at the holes — the real insert always ends up flush inside, nothing sticking out.)",
      "20 go into the tray now — the picture marks every spot. The other 21 come later: 2 in the wheels, 2 in the front pods, 14 in the shell, 2 in the lid, and 1 in the head. The book calls for each batch when it’s time."],
     "Every insert is flush and straight, none tilted."),
    ("step_03_motors", "Drop in the motors", SCREWS["motor_caps"],
     [("px_motor_L", 2), ("motor_cap_v2", 2)],
     ["Lay a motor in each cradle with the metal shaft poking OUT through the hole toward the wheel side.",
      "Point the wires inward, toward the middle of the robot.",
      "Set a printed cap over each motor and screw it down with 2 screws per cap — snug, not gorilla-tight."],
     "Motors don’t wiggle. Shafts spin freely when you twist them."),
    ("step_04_wheels_bench", "Make the wheels", 0,
     [("rear_wheel_v2", 2), ("front_wheel_v2", 2), ("tire_v2", 4), ("px_insert", 2)],
     ["Each BACK wheel has a little screw well in its rim. Drop 1 insert down each well (2 total), then press it to the bottom with the tip of the iron. It seats deep inside the wheel, close to the axle — nothing pokes out.",
      "Stretch a stretchy printed tire over each of the four wheels, like putting a rubber band on a yo-yo.",
      "Every tire has one little round port in its tread. On the BACK wheels, spin the tire until the port sits right over the screw well (the front wheels don’t care).",
      "Work each tire around evenly until it sits flat in the groove all the way around."],
     "No tire bulges, and each BACK tire’s port lines up over its screw well."),
    ("step_05_front_pods", "Bolt on the front pods", SCREWS["front_pods"],
     [("front_pod_left_v2", 2), ("px_insert", 2)],
     ["Melt 1 insert into the end of each pod’s peg (2 total).",
      "The two front pods have round pegs sticking out — those pegs are the front axles.",
      "Screw each pod to the tray through its little foot tabs, 2 screws each, pegs pointing OUT."],
     "Both pegs point straight out to the sides."),
    ("step_06_wheels_on", "Put the wheels on",
     SCREWS["rear_wheel_clamps"] + SCREWS["front_axle_retainers"],
     [("rear_wheel_v2", 2), ("front_wheel_v2", 2), ("printed_washer_v2", 2)],
     ["BACK wheels: the hole has a flat side, and so does the motor shaft. Line the flats up, push the wheel on, then drop the clamp screw down through the tire’s port and tighten until it presses snug on the shaft’s flat.",
      "FRONT wheels: slide onto the pegs — they should spin freely. Put a printed cap washer over the end (it covers the wheel’s middle hole), then a screw into the peg to keep the wheel from sliding off.",
      "Don’t overtighten the front screws: the wheels must still spin.",
      "You printed extra washers — drop the leftovers in your spares box."],
     "Back wheels should NOT spin freely by hand (the motor holds them). Front wheels spin freely."),
    ("step_07_tower", "Build the brain tower", SCREWS["controller_tower_base"],
     [("controller_tower_v2", 1), ("px_mdds10", 1)],
     ["Set the tower over the front of the tray — its screw holes match the four inserts.",
      "Drive 4 screws down through the base tabs.",
      "Rest the purple motor board on the four little posts, its green terminal blocks facing the RIGHT side of the robot."],
     "The board sits level on all four posts, terminals facing right."),
    ("step_08_pi", "Add the computer", 0,
     [("px_pi", 1)],
     ["The Raspberry Pi lies flat on the tower’s top shelf frame.",
      "Its USB ports face the BACK of the robot so the cables can reach.",
      "Don’t screw anything — the shelf pocket holds it, and the head’s cable will come down to it later."],
     "The Pi sits in its pocket, ports facing backward."),
    ("step_09_battery", "Dry-fit the battery, then remove it", SCREWS["battery_clamp"],
     [("battery_pad_frame_v2", 1), ("px_battery", 1), ("battery_clamp_v2", 1)],
     ["Lay the soft TPU pad frame onto the four pads behind the tower.",
      "Set the battery on it, wires pointing at the BACK of the robot.",
      "Bridge the clamp bar across the battery onto the two posts and screw it down with 2 screws — firm, so the battery cannot slide.",
      "This is a DRY FIT only. Remove the screws, clamp, battery, and soft pad; put the battery in a safe box away from the build until the meter-check page calls for it."],
     "The battery fits without wrapper pinch or lead strain, and is now outside the robot."),
    ("step_10_pico", "Add the safety helper", SCREWS["pico_clamp"],
     [("px_pico", 1), ("pico_clamp_v2", 1)],
     ["The tiny green Pico sits on its little posts to the right of the tower, USB service end facing the BACK of the robot.",
      "USB and SWD are service-only. Never cable either one to the Pi inside the robot.",
      "Lay the small clamp bar across it and screw it down with 2 screws, gently — it’s a small board."],
     "The Pico is held snug, its USB end points back, and no USB/SWD cable is installed."),
    ("step_11_relay", "Mount the power relay", 0,
     [("px_relay", 1)],
     ["The relay drops into its floor pocket on the left, behind the tower.",
      "Its metal bracket slots into the printed pocket; the terminals face UP so they’re easy to wire later.",
      "No wires yet — all wiring happens in the wiring chapter at the back of this book."],
     "The relay clicks into its pocket and doesn’t rattle."),
    ("step_12_deck", "Put on the power deck", SCREWS["deck_towers"],
     [("deck_v2", 1), ("px_fuse", 1), ("px_reg1", 2)],
     ["First hang the two small green regulator boards under the deck’s BACK half (they clip under; wires come later).",
      "Lower the deck onto the four towers — the notch at the back-right corner goes around the battery wires.",
      "Drive 4 screws down into the tower tops.",
      "Set the black fuse box into its raised outline on the deck’s LEFT half, wire tail hanging over the left edge."],
     "The deck is level and the fuse box sits inside its printed fence."),
    ("step_13_shell", "Lower the body shell", SCREWS["shell_tray"],
     [("shell_v2", 1), ("px_insert", 14)],
     ["Melt the shell’s 14 inserts first (4 corner lugs, 4 lid-ledge holes, 4 speaker posts, 2 sensor bosses).",
      "Two people make this easy: lower the big shell straight down over EVERYTHING.",
      "The wheel arches go around the wheels; the lip settles onto the tray edge.",
      "Flip-check the underside: drive 4 screws UP through the tray’s corner holes into the shell’s lugs."],
     "No gaps between shell and tray. The robot is now a box with wheels."),
    ("step_14_bumpers", "Feeler switches, then bumpers", 0,
     [("px_switch", 6), ("bumper_front_v2", 2)],
     ["Tip the robot gently onto its side. Click each of the six little feeler switches into its pocket under the tray edge — two front, two back, one each side. Their tiny buttons face OUT.",
      "Their wires tuck up inside for the wiring chapter.",
      "Stand the robot back up. The two soft bumper halves wrap around the bottom, one from the front, one from the back.",
      "They hug the body loosely on purpose — they squish in to press those feeler switches."],
     "Press any bumper edge gently: it moves a tiny bit, you hear a soft click, and it springs back."),
    ("step_15_panels", "Face and back panels (with the front eyes)", 0,
     [("fascia_v2", 1), ("px_tof_L", 2), ("rear_panel_v2", 1)],
     ["First press the two front distance boards into the pockets on the FACE panel’s back — their little lenses peer through the two low holes.",
      "Click the FACE panel into the front opening.",
      "The dark BACK panel clicks into the back opening. Its two round holes are for the charger plug and the mute switch — they bolt in with their own nuts during the wiring chapter."],
     "Both panels sit flush; two tiny lenses look out of the face."),
    ("step_16_speakers", "Speakers and distance eyes",
     SCREWS["speaker_clamps"] + SCREWS["tof_clamps"],
     [("px_speaker_L", 2), ("px_tof_L", 2), ("speaker_clamp_v2", 2), ("tof_clamp_v2", 2)],
     ["Reach in through the open top: rest a speaker on each side shelf, magnet side in, grille facing the wall.",
      "Lay a clamp bar across each speaker’s top and screw into the two posts (2 screws per side) — the inserts went in with the shell step.",
      "Slide a little blue distance board behind each side window, then its clamp bar and 1 screw."],
     "Speakers can’t rattle; the blue boards peek through their side windows."),
    ("step_17_lid", "The lid and the BIG RED BUTTON",
     SCREWS["mic_cradle"],
     [("lid_v2", 1), ("lid_skin_v2", 1), ("px_estop_cap", 1), ("px_mic", 1), ("mic_cradle_v2", 1), ("px_insert", 2)],
     ["Melt the lid’s 2 mic-boss inserts, then drop the red emergency-stop through the lid’s round hole and spin its nut on underneath — the lid IS its mounting panel, and the printed ring under the lid makes it strong.",
      "Set the round microphone under the lid’s slotted area and screw its ring cradle to the two bosses (2 screws).",
      "OPTIONAL: after the E-stop is clamped, press the teal skin’s four integral tabs into the lid’s blind pockets. It stays above the lid and never goes under the E-stop nut, neck, microphone, or corner screws.",
      "Rest the lid in its ledge — DON’T screw it yet. The neck, the head, and all the wiring still need the inside. Its 4 corner screws are the very last thing in this book."],
     "The optional skin sits flat with every slot open; with the PETG lid supported and nut tight, a centered firm press latches the red button; twist to release."),
    ("step_18_neck", "Build the pan journal and neck", SCREWS["pan_servo_plate"],
     [("neck_v2", 1), ("bayonet_collar_v2", 1), ("head_pan_plate_v2", 1), ("px_servo", 1), ("px_insert", 6)],
     ["Melt 2 inserts into the collar’s pan-plate towers and 4 into the neck’s top flange. Keep heat away from the smooth journal and thrust faces.",
      "From above the loose lid, align the collar’s 3 lugs with the keyways, press through, and twist about 20° until all 3 detents sit in the blind underside race.",
      "Flip the supported lid. Set the pan D85MG into the cradle with its shaft UP; the black pan plate captures its flange from below with 2 M3 screws. The case must not be pinched.",
      "Using a current-limited 6 V servo tester, center the servo at 1500 µs. Fit one R-ML24 arm toward FRONT with its verified spline screw; never force the gears by hand.",
      "Feed the camera ribbon through the open +X crescent, lower the neck journal into the collar, and fasten the neck drive pad to both R-ML24 M2 stations with the verified component screws."],
     "The shoulder sits flat on the greased thrust face; the neck turns by hand through ±60°, meets both hard stops beyond that range, has no lift, and never rubs the ribbon."),
    ("step_19_head", "Build the tilt head and camera", SCREWS["yoke_neck"] + SCREWS["head_tilt_pivot"],
     [("head_shell_v2", 1), ("yoke_v2", 1), ("px_camera", 1), ("px_servo", 1), ("tilt_bushing_v2", 1), ("px_insert", 1)],
     ["Melt 1 insert into the yoke’s passive-pivot boss from the OUTSIDE end. Seat the yoke on the neck and install its 4 M3 screws without trapping the center ribbon.",
      "Mount the second D85MG sideways in the active frame with its verified Hitec grommets, eyelets, screws, and nuts. Center it at 1500 µs on the current-limited 6 V tester; fit the R-ML24 arm toward FRONT.",
      "Slide the head shell over the yoke. Through the two +Y service holes, fasten the shell’s drive boss to the horn’s 13 and 16 mm M2 stations. The servo supplies torque; the printed pivots carry the head.",
      "From the -Y outside face, slide the black shoulder bushing through the shell and install 1 M3 screw into the yoke insert. Tighten against the bushing’s 3.2 mm sleeve — never pinch the moving shell.",
      "Dry-seat the Camera Module 3 behind the face opening and feed its FPC down the hollow neck. Permanent camera-board retention and the exact harness remain prototype release gates."],
     "The bushing flange is flush; the shell has no axial pinch, hand-tilts freely through ±20°, and contacts both printed hard stops only beyond the commanded range."),
    ("step_20_face", "Give it a face", 0,
     [("head_faceplate_v2", 1), ("eye_diffuser_bar_v2", 1), ("status_diffuser_bar_v2", 1)],
     ["Clip the lime eye bar behind the face panel’s eye slots (glow boards ride behind it).",
      "Press the face panel into its recess: camera hole over the lens.",
      "The second lime bar clips behind the front body panel’s light slots — each glow board rides in the pocket behind its bar.",
      "Leave the 4 glow boards in their bag for now — they seat in those pockets during the wiring chapter."],
     "Rover Bean is looking at you. Say hi."),
]

WIRE_RULES = [
    "Wiring is the careful part. Read this whole chapter once, start to finish, before cutting a single wire.",
    "The battery stays OUT of the robot until every wire is checked against these maps.",
    "Use wire colors: RED = battery 12 V, YELLOW = switched motor 12 V, BLUE = 5 V, GREEN = 6 V, BLACK = ground, WHITE = signals.",
    "Crimp or solder every joint; no bare twists. Label both ends of every wire with tape.",
    "Fuse values are PROTOTYPE STARTING VALUES — NOT RELEASED. A meter alone cannot select them; measured loads, conductor ampacity, inrush, selective-clearing, and thermal tests must close first.",
    "The robot must FAIL STOPPED: if any of this feels wrong, it stays off.",
]
POWER_MAP = [
    ("Battery +12 V", "feeder fuse (near battery)", "Blue Sea fuse block IN"),
    ("Fuse branch 1", "D24V90F5 regulator", "5 V to the Raspberry Pi"),
    ("Fuse branch 2", "D36V50F6 regulator", "6 V to both neck servos"),
    ("Fuse branch 3", "mute switch common", "mic USB power OR red mute ring"),
    ("Fuse branch 4", "5 V accessories", "NeoPixel eyes + status lights"),
    ("Battery +12 V", "motor fuse → relay contacts", "MDDS10 motor board power"),
    ("Relay coil 12 V", "through BOTH red-button NC contacts", "coil ground via Pico enable"),
    ("Charger EN2 pins 1+2", "direct to battery charge lead", "pin 3 = charger-present to Pico"),
]
SIGNAL_MAP = [
    ("Raspberry Pi / robotd", "Pico 2", "framed UART commands + heartbeat; no flash or config-write path"),
    ("Pico 2", "MDDS10", "clamped velocity outputs after leases, watchdog, and latch checks"),
    ("Motor encoders (6 wires each)", "Pico 2", "wheel speed feedback"),
    ("Bumper switches ×6", "Pico 2", "any open NC loop = latched stop in independent safety firmware"),
    ("ToF boards ×4", "Raspberry Pi", "I2C daisy chain (STEMMA cables)"),
    ("NeoPixels ×4", "Raspberry Pi", "one data line, chained eye→eye→status→status"),
    ("Camera", "Raspberry Pi", "flat FPC ribbon down the hollow neck"),
    ("Servos ×2", "Raspberry Pi", "PWM signal wires (power from the 6 V rail)"),
    ("Mic array", "Raspberry Pi", "USB (its 5 V passes through the mute switch)"),
    ("Pi I2S pins", "MAX98357A amps", "digital sound out; board mounts, channel straps, terminals, and strain relief not released"),
]

# "Meet Rover Bean" callouts: (x%, y%, legend). Percentages are positions
# on the uncropped 4:3 render.
MEET_FRONT = [
    (38.5, 13, "The head — camera in the middle, glowing eyes beside it. It nods and turns to look at you."),
    (55, 44, "The white PETG lid carries the red button and head. The teal PLA skin above it is optional decoration."),
    (27, 66, "Face panel — two distance eyes low, glowing status bars above."),
    (23, 83, "Soft bumper — a squishy ring that feels walls and tells the robot to stop."),
    (83, 72, "Four wheels with grippy printed tires. The back pair are the motor wheels."),
]
MEET_REAR = [
    (28, 32, "Cooling vents — warm air from the computer leaves here."),
    (51.5, 39, "The BIG RED BUTTON. Push = everything stops; twist to release."),
    (27, 57, "The charging plug and the mic mute switch bolt into these two holes."),
    (70, 77, "Motor wheels. Each one has its own motor and its own speed sensor."),
]


# ---------------------------------------------------------------------------
# HTML
# ---------------------------------------------------------------------------
def esc(s):
    return html.escape(str(s), quote=False)


def img_uri(path: Path) -> str:
    return path.resolve().as_uri()


def friendly(base: str) -> str:
    return PART_NAMES.get(base, base.replace("_v2", "").replace("_", " "))


CSS = """
* { margin: 0; padding: 0; box-sizing: border-box; }
:root {
  --paper:#FBF7EC; --cream:#F3ECDA; --teal:#0B6E84; --teal-dk:#075365;
  --ink:#22231F; --ink2:#6E6553; --red:#C4230F; --gold:#B8892E;
  --lime:#B9E44A; --line:rgba(34,35,31,.16); --line-soft:rgba(34,35,31,.09);
}
@page { size: 11in 8.5in; margin: 0; }
body { font-family: "Avenir Next", "Helvetica Neue", Helvetica, sans-serif; color: var(--ink); }
section.page { width: 11in; height: 8.5in; page-break-after: always; position: relative;
  overflow: hidden; background: var(--paper); padding: .5in .6in; display: flex; flex-direction: column; }
h1 { font-size: 64px; font-weight: 800; color: var(--teal); letter-spacing: -1.5px; line-height: .93; }
h2 { font-size: 29px; font-weight: 600; color: var(--ink); letter-spacing: -.3px; margin-bottom: .16in; }
h3 { font-size: 15px; font-weight: 600; color: var(--teal-dk); margin: .14in 0 .05in; }
p, li { font-size: 12.5px; line-height: 1.5; }
.eyebrow { font-size: 10px; font-weight: 700; letter-spacing: .18em; color: var(--ink2);
  text-transform: uppercase; margin-bottom: .07in; display: flex; align-items: center; gap: .08in; }
.eyebrow i { width: .09in; height: .09in; border-radius: 2px; display: inline-block; }
.tab { position: absolute; right: 0; width: .3in; padding: .14in 0; border-radius: .09in 0 0 .09in;
  color: #fff; font-size: 8.5px; font-weight: 700; letter-spacing: .2em; writing-mode: vertical-rl;
  text-align: center; z-index: 5; }
table { border-collapse: collapse; width: 100%; font-size: 11.5px; }
th { text-align: left; font-size: 9px; letter-spacing: .12em; text-transform: uppercase;
  color: var(--teal-dk); border-bottom: 2px solid var(--teal); padding: .03in .07in .045in; }
td { padding: .052in .07in; border-bottom: 1px solid var(--line-soft); vertical-align: top; }
td b { font-weight: 600; }
.mono { font-family: Menlo, monospace; font-size: 8px; color: var(--ink2); }
.statchip { display: inline-block; border: 1.5px solid var(--ink); border-radius: .16in;
  padding: .045in .13in; font-size: 11px; font-weight: 700; letter-spacing: .03em; }
.stephead { display: flex; align-items: center; gap: .17in; }
.stepnum { width: .58in; height: .58in; border-radius: .13in; background: var(--teal); color: #fff;
  display: flex; align-items: center; justify-content: center; font-size: 29px; font-weight: 800; flex: none; }
.stephead h2 { margin: 0; font-size: 25px; }
.prog { margin-left: auto; text-align: right; }
.prog span { font-size: 8.5px; font-weight: 700; letter-spacing: .14em; color: var(--ink2); }
.prog .bar { display: flex; gap: 2.5px; margin-top: .045in; }
.prog .bar i { display: block; width: .1in; height: .075in; border-radius: 2px; background: #E7DFC8; }
.prog .bar i.on { background: var(--teal); }
.strip { background: var(--cream); border: 1px solid var(--line-soft); border-radius: .12in;
  display: flex; align-items: center; flex-wrap: wrap; gap: .1in; padding: .09in .14in;
  margin: .13in 0; min-height: 1.08in; }
.gather { writing-mode: vertical-rl; transform: rotate(180deg); font-size: 8px; font-weight: 700;
  letter-spacing: .22em; color: var(--ink2); margin-right: .04in; }
.strip .cell { background: #fff; border: 1px solid var(--line-soft); border-radius: .1in;
  padding: .045in .09in; display: flex; align-items: center; gap: .07in; }
.strip .cell img { width: .78in; height: .78in; object-fit: contain; }
.strip .cell b { font-size: 15px; font-weight: 700; display: block; line-height: 1.1; }
.strip .cell small { font-size: 8px; display: block; color: var(--ink2); font-weight: 600; }
.strip.dense { gap: .055in; }
.strip.dense .cell { padding: .03in .05in; gap: .04in; }
.strip.dense .cell img { width: .5in; height: .5in; }
.strip.dense .cell b { font-size: 11px; }
.strip.dense .cell small { font-size: 6.5px; }
.stepbody { display: flex; gap: .28in; flex: 1; min-height: 0; }
.stepbody .imgwrap { width: 6.15in; height: 4.85in; border-radius: .14in; overflow: hidden;
  position: relative; flex: none; border: 1px solid var(--line-soft); }
.stepbody .imgwrap img.main { width: 107%; height: 107%; object-fit: cover; object-position: 50% 55%; margin: -2.5% 0 0 -3.5%; }
.frontchip { position: absolute; left: .12in; bottom: .12in; background: rgba(34,35,31,.85); color: #fff;
  font-weight: 700; font-size: 10.5px; letter-spacing: .04em; padding: .04in .1in; border-radius: .1in; }
.instr { flex: 1; display: flex; flex-direction: column; }
.instr ol { margin-left: .22in; }
.instr li { font-size: 13.5px; margin-bottom: .1in; line-height: 1.42; }
.check { margin-top: auto; background: var(--lime); border-radius: .11in; padding: .1in .13in;
  font-weight: 600; font-size: 12.5px; display: flex; gap: .1in; align-items: flex-start; line-height: 1.35; }
.check .box { flex: none; width: .16in; height: .16in; background: #fff; border: 2px solid var(--ink);
  border-radius: 3px; margin-top: 1px; }
.check b { color: var(--teal-dk); letter-spacing: .08em; font-size: 10.5px; margin-right: .04in; }
.cols { display: flex; gap: .35in; }
.cols > div { flex: 1; }
.footer { position: absolute; bottom: .24in; left: .6in; right: .6in; display: flex;
  justify-content: space-between; font-size: 7.5px; font-weight: 600; letter-spacing: .14em;
  color: #A2967C; text-transform: uppercase; }
.rule { background: #fff; border: 1px solid var(--line-soft); border-left: 4px solid var(--red);
  border-radius: .07in; padding: .07in .13in; margin-bottom: .08in; font-size: 12.5px; }
.hero { position: absolute; right: 0; top: 0; width: 6in; height: 8.5in; object-fit: cover; object-position: 62% 22%; }
.invgrid { display: grid; grid-template-columns: repeat(8, 1fr); gap: .08in; }
.invcell { background: #fff; border: 1px solid var(--line-soft); border-radius: .1in;
  padding: .05in .03in .045in; text-align: center; position: relative; }
.invcell img { width: .84in; height: .68in; object-fit: contain; }
.invcell .nm { font-size: 8px; font-weight: 600; line-height: 1.15; min-height: .19in; }
.invcell .ct { font-size: 11px; font-weight: 800; margin-top: .01in; }
.invcell .swatch { position: absolute; top: .05in; right: .05in; width: .1in; height: .1in;
  border-radius: 50%; border: 1px solid rgba(0,0,0,.25); }
table.roomy td { padding: .075in .07in; }
.callout { position: absolute; width: .26in; height: .26in; border-radius: 50%; background: var(--teal);
  color: #fff; font-size: 13px; font-weight: 800; display: flex; align-items: center;
  justify-content: center; border: 2.5px solid #fff; box-shadow: 0 1px 5px rgba(0,0,0,.3);
  transform: translate(-50%, -50%); }
.legend { margin-top: .09in; }
.legend div { display: flex; gap: .08in; font-size: 11px; line-height: 1.4; margin-bottom: .055in; }
.legend b.n { flex: none; width: .17in; height: .17in; border-radius: 50%; background: var(--teal);
  color: #fff; font-size: 9.5px; display: flex; align-items: center; justify-content: center; margin-top: 1px; }
.toc { margin-top: .3in; width: 3.9in; }
.toc .row { display: flex; align-items: baseline; gap: .09in; margin-bottom: .085in; }
.toc .n { font-size: 13px; font-weight: 800; width: .17in; }
.toc .t { font-size: 13.5px; font-weight: 600; }
.toc .d { font-size: 10px; color: var(--ink2); }
.toc .lead { flex: 1; border-bottom: 1.5px dotted #C4B896; transform: translateY(-3px); }
.toc .pg { font-size: 11px; font-weight: 700; color: var(--ink2); }
svg text { font-family: "Avenir Next", Helvetica, sans-serif; }
"""


def page(body, chapter=None, footer=True, num=None, total=None):
    tab = ""
    if chapter is not None:
        label, color, _, _ = CHAPTERS[chapter]
        top = 0.9 + chapter * 0.82
        tab = f'<div class="tab" style="background:{color}; top:{top}in;">{label}</div>'
    ft = ""
    if footer:
        ft = (f'<div class="footer"><span>Codex Rover Bean &middot; Builder’s Book</span>'
              f'<span>{"" if num is None else f"Page {num} of {total}"}</span></div>')
    return f'<section class="page">{tab}{body}{ft}</section>'


def eyebrow(chapter=None, text=None):
    if chapter is not None:
        label, color, name, _ = CHAPTERS[chapter]
        txt = f"Chapter {chapter + 1} &middot; {name}"
        dot = f'<i style="background:{color}"></i>'
    else:
        txt, dot = text, '<i style="background:var(--teal)"></i>'
    return f'<div class="eyebrow">{dot}{txt}</div>'


def progress(i, n=len(STEPS)):
    cells = "".join('<i class="on"></i>' if k <= i else "<i></i>" for k in range(1, n + 1))
    return f'<div class="prog"><span>STEP {i} OF {n}</span><div class="bar">{cells}</div></div>'


def strip_cells(step_key, items, screws):
    cells = ""
    for t, n in items:
        name = STRIP_NAME_OVERRIDES.get((step_key, t), friendly(t))
        cells += (f'<div class="cell"><img src="{img_uri(GUIDE_IMG / ("thumb_" + t + ".png"))}">'
                  f'<div><b>&times;{n}</b><small>{esc(name)}</small></div></div>')
    if screws:
        cells += (f'<div class="cell"><img src="{img_uri(GUIDE_IMG / "thumb_px_screw.png")}">'
                  f'<div><b>&times;{screws}</b><small>M3 screw{"s" if screws != 1 else ""}</small></div></div>')
    return cells


def build_body_pages():
    """Everything except the cover; returns a list of page dicts."""
    pages = []

    def add(html_body, chapter=None, footer=True, mark=None):
        pages.append({"html": html_body, "chapter": chapter, "footer": footer, "mark": mark})

    # --- Meet the robot -----------------------------------------------------
    def figure(img_name, callouts, caption):
        dots = "".join(f'<div class="callout" style="left:{x}%; top:{y}%;">{k}</div>'
                       for k, (x, y, _) in enumerate(callouts, start=1))
        legend = "".join(f'<div><b class="n">{k}</b><span>{esc(t)}</span></div>'
                         for k, (_, _, t) in enumerate(callouts, start=1))
        return (f'<div style="flex:1;"><div style="position:relative; border-radius:.14in; overflow:hidden;'
                f' border:1px solid var(--line-soft); aspect-ratio:4/3;">'
                f'<img src="{img_uri(IMG / img_name)}" style="width:100%; height:100%; object-fit:cover;">{dots}</div>'
                f'<p style="font-size:9px; font-weight:700; letter-spacing:.12em; color:var(--ink2);'
                f' text-transform:uppercase; margin-top:.05in;">{caption}</p>'
                f'<div class="legend">{legend}</div></div>')

    stats = "".join(
        f'<div style="flex:1; text-align:center;"><div style="font-size:26px; font-weight:800; color:var(--teal);">{v}</div>'
        f'<div style="font-size:9px; font-weight:700; letter-spacing:.12em; color:var(--ink2); text-transform:uppercase;">{k}</div></div>'
        for v, k in [(N_PIECES, "printed incl. spare + optional"), (N_SCREWS, "screws, one size"),
                     (N_PLATES, "printer plates"), ("0", "supports needed")])
    add(f"""
      {eyebrow(text="Meet your robot")}
      <h2>This is Rover Bean</h2>
      <div style="display:flex; gap:.3in;">
        {figure('codex_robot_body_v2_assembled.png', MEET_FRONT, 'From the front')}
        {figure('codex_robot_body_v2_rear.png', MEET_REAR, 'From the back')}
      </div>
      <div style="display:flex; gap:.2in; border-top:1px solid var(--line); padding-top:.14in; margin-top:.22in;">{stats}</div>""",
        mark="meet")

    # --- How the book works -------------------------------------------------
    mini_bar = "".join('<i class="on"></i>' if k <= 7 else "<i></i>" for k in range(1, 21))
    anatomy = f"""
      <div style="background:#fff; border:1px solid var(--line); border-radius:.14in; padding:.16in; width:4.9in;">
        <div class="stephead"><div class="stepnum" style="width:.42in;height:.42in;font-size:20px;">7</div>
          <h2 style="font-size:17px;">Every step looks like this</h2>
          <div class="prog"><span>STEP 7 OF 20</span><div class="bar">{mini_bar}</div></div></div>
        <div class="strip" style="min-height:.72in; margin:.09in 0;"><span class="gather">GATHER</span>
          <div class="cell"><img src="{img_uri(GUIDE_IMG / 'thumb_controller_tower_v2.png')}" style="width:.5in;height:.5in;">
            <div><b style="font-size:12px;">&times;1</b><small>brain tower</small></div></div>
          <div class="cell"><img src="{img_uri(GUIDE_IMG / 'thumb_px_screw.png')}" style="width:.5in;height:.5in;">
            <div><b style="font-size:12px;">&times;4</b><small>M3 screws</small></div></div></div>
        <div style="display:flex; gap:.12in;">
          <div style="width:2.5in; height:1.5in; border-radius:.1in; background:#E8DFC9; position:relative;">
            <div class="frontchip" style="font-size:8px; padding:.03in .07in;">&#8601; FRONT</div>
            <div style="position:absolute; top:38%; left:0; right:0; text-align:center; font-size:9px; font-weight:700; color:var(--ink2); letter-spacing:.1em;">THE BIG PICTURE</div></div>
          <div style="flex:1; display:flex; flex-direction:column;">
            <ol style="margin-left:.16in;"><li style="font-size:9px; margin-bottom:.04in;">Numbered moves&hellip;</li>
              <li style="font-size:9px;">&hellip;if you want words too.</li></ol>
            <div class="check" style="font-size:9px; padding:.06in .08in; gap:.06in;"><span class="box" style="width:.12in;height:.12in;"></span>
              <div><b style="font-size:8px;">CHECK</b> A 10-second test.</div></div></div>
        </div>
      </div>"""
    add(f"""
      {eyebrow(text="How this book works")}
      <h2>Four things to know before you build</h2>
      <div style="display:flex; gap:.32in; flex:1;">
        <div>{anatomy}
          <p style="font-size:11px; color:var(--ink2); margin-top:.1in; width:4.9in;">The tan GATHER strip lists every
          part and screw the step needs — lay them out like a cooking show. The picture shows the robot so far,
          with the new parts floating just off their spot. The FRONT tag always points at the robot’s face.</p>
        </div>
        <div style="flex:1;">
          <h3 style="margin-top:0;">1. The pictures do the talking</h3>
          <p>Match the big picture, then read the numbered lines if you want words too. Do the little green
          CHECK before moving on — if it fails, fix it now, because later steps cover things up.</p>
          <h3>2. One screw. One key.</h3>
          <p>Every screw in this robot is the same M3 × 8 screw, and one 2.5 mm hex key turns them all.
          “Snug” means: stop when it stops, then an eighth of a turn. Plastic hates gorillas.</p>
          <h3>3. Front and back</h3>
          <p>The FRONT is where the face panel and head look. The BACK has the charging plug, the mute switch,
          and the motor wheels. Left and right are the robot’s left and right, not yours.</p>
          <h3>4. Go in order</h3>
          <p>The steps nest like LEGO bags: wheels before shell, shell before lid. The soldering iron and the
          multimeter each come out for their own steps — the book tells you exactly when.</p>
        </div>
      </div>
      <div style="display:flex; align-items:center; gap:.14in; border-top:1px solid var(--line);
           padding-top:.16in; margin-top:.1in;">
        <div style="font-size:9px; font-weight:700; letter-spacing:.14em; color:var(--ink2); width:.9in;">THE ROAD TO A ROBOT</div>
        {"".join(
            f'<div style="flex:1; display:flex; align-items:center; gap:.1in;">'
            f'<div style="flex:1; text-align:center;"><div style="background:{c}; color:#fff; border-radius:.09in;'
            f' padding:.045in 0; font-size:10.5px; font-weight:800; letter-spacing:.1em;">{i + 1} &middot; {lbl}</div>'
            f'<div style="font-size:8.5px; color:var(--ink2); margin-top:.03in; font-weight:600;">{hint}</div></div>'
            + ('<div style="font-size:14px; color:#B4A785;">&#8594;</div>' if i < 4 else "")
            + "</div>"
            for i, ((lbl, c, _, _), hint) in enumerate(zip(CHAPTERS,
                ["buy the box", f"{N_PLATES} plates", f"{len(STEPS)} steps", "maps + meter", "tests, then fun"])))}
      </div>""",
        mark="how")

    # --- Chapter 1: shop -----------------------------------------------------
    fil = "".join(f"<tr><td><b>{esc(a)}</b></td><td>{esc(b)}</td><td>{esc(c)}</td></tr>" for a, b, c in SHOP_FILAMENT)
    fas = "".join(f"<tr><td><b>{esc(a)}</b></td><td>{esc(b)}</td><td>{esc(c)}</td></tr>" for a, b, c in SHOP_FASTENERS)
    tools = "".join(f"<tr><td><b>{esc(a)}</b></td><td>{esc(b)}</td></tr>" for a, b in SHOP_TOOLS)
    add(f"""
      {eyebrow(0)}
      <h2>Go shopping: plastic, screws, tools</h2>
      <div class="cols"><div>
        <h3 style="margin-top:0;">Filament (for the printer)</h3>
        <table><tr><th>Filament</th><th>How much</th><th>What it becomes</th></tr>{fil}</table>
        <h3 style="margin-top:.2in;">The only two fastener packs</h3>
        <table><tr><th>Fastener</th><th>Buy</th><th>Why</th></tr>{fas}</table>
        <div style="margin-top:.22in; background:var(--cream); border-radius:.12in; padding:.11in .14in;">
          <p style="font-size:11.5px;"><b>Get a spares box.</b> A cheap compartment box keeps screws, inserts,
          washers, and every printed spare sorted through the whole build. Future-you says thanks.</p>
        </div>
      </div><div>
        <h3 style="margin-top:0;">Tools</h3>
        <table><tr><th>Tool</th><th>Job</th></tr>{tools}</table>
        <div style="margin-top:.22in; background:#fff; border:1px solid var(--line-soft); border-radius:.12in;
             padding:.12in; display:flex; gap:.22in; align-items:center;">
          <img src="{img_uri(GUIDE_IMG / 'thumb_px_screw.png')}" style="width:1.15in;">
          <img src="{img_uri(GUIDE_IMG / 'thumb_px_insert.png')}" style="width:1.15in;">
          <p style="font-size:11.5px;">This screw and this brass insert are the only fasteners you’ll buy for the
          whole robot. When a step says “2 screws,” it always means these.</p>
        </div>
      </div></div>""",
        chapter=0, mark="ch0")

    # Shopping: electronics (split across two pages so nothing clips).
    half = (len(SHOP_ELECTRONICS) + 1) // 2
    for part_i, chunk in enumerate((SHOP_ELECTRONICS[:half], SHOP_ELECTRONICS[half:]), start=1):
        elec = "".join(f"<tr><td><b>{esc(a)}</b></td><td style='text-align:center'>{esc(b)}</td><td>{esc(c)}</td></tr>"
                       for a, b, c in chunk)
        intro = ("Every named production component must be a normal buy-one-online part in the US. This prototype "
                 "preview does not yet release the harness terminals, wire schedule, crimp tooling, or fuse values."
                 if part_i == 1 else "The rest of the electronics box:")
        add(f"""
          {eyebrow(0)}
          <h2>Go shopping: the electronics box ({part_i} of 2)</h2>
          <p style="margin-bottom:.12in;">{intro}</p>
          <table class="roomy" style="font-size:12px;"><tr><th>Part</th><th>Qty</th><th>What it does</th></tr>{elec}</table>""",
            chapter=0)

    # --- Chapter 2: print ----------------------------------------------------
    tips = "".join(
        f'<div style="display:flex; gap:.12in; margin-bottom:.13in;">'
        f'<div style="flex:none; width:.28in; height:.28in; border-radius:50%; background:var(--teal); color:#fff;'
        f' font-size:14px; font-weight:800; display:flex; align-items:center; justify-content:center;">{k}</div>'
        f'<div><h3 style="margin:0 0 .02in;">{esc(t)}</h3><p style="font-size:11.5px;">{d}</p></div></div>'
        for k, (t, d) in enumerate(PRINT_TIPS, start=1))
    order_data = [("#fff", "TEST PARTS", f"{len(COUPONS)} coupons first")]
    for group in _groups.values():
        plate, count = group["plate"], group["count"]
        theme = inv.DEFAULT_THEME[plate["color_profile"]]
        label = (f"{theme['name']} PLA" if theme["name"].startswith("Translucent") and "PLA" in plate["material"]
                 else f"{theme['name']} {plate['material']}")
        order_data.append((plate["color_hex"], label,
                           f"{count} plate{'s' if count != 1 else ''}"))
    order_chips = "".join(
        f'<div style="text-align:center; background:#fff; border:1px solid var(--line); border-radius:.09in; padding:.05in .04in;">'
        f'<div style="font-size:9px; font-weight:800; letter-spacing:.04em;">'
        f'<span style="display:inline-block; width:.11in; height:.11in; border-radius:50%; background:{c};'
        f' border:1px solid rgba(0,0,0,.2); vertical-align:-1.5px; margin-right:.045in;"></span>{esc(t)}</div>'
        f'<div style="font-size:8px; color:var(--ink2); margin-top:.02in; font-weight:600;">{esc(d)}</div></div>'
        for c, t, d in order_data)
    add(f"""
      {eyebrow(1)}
      <div style="display:inline-block; margin-bottom:.1in; background:var(--red); color:#fff; padding:.07in .12in; font-size:11px; font-weight:800; letter-spacing:.08em;">PROTOTYPE PLATES — PHYSICAL RELEASE GATES OPEN</div>
      <h2>Print it with Bambu Studio</h2>
      <div class="cols">
        <div>{tips}</div>
        <div>
          <img src="{img_uri(IMG / 'codex_robot_body_v2_p1s_plates.png')}"
               style="width:100%; border-radius:.12in; border:1px solid var(--line-soft);">
          <p style="font-size:10px; margin-top:.06in; color:var(--ink2);">All {N_PLATES} prototype plates, exactly as they open in Bambu Studio. Layout is not powered-motion release.</p>
        </div>
      </div>
      <div style="border-top:1px solid var(--line); padding-top:.12in; margin-top:auto;">
        <div style="font-size:9px; font-weight:700; letter-spacing:.14em; color:var(--ink2); margin-bottom:.06in;">PRINTING ORDER</div>
        <div style="display:grid; grid-template-columns:repeat(4,1fr); gap:.06in;">{order_chips}</div>
      </div>""",
        chapter=1, mark="ch1")

    # Plate table: aggregate instances and use the same friendly part names
    # as the piece chart and step strips, so a kid can match them.
    rows = ""
    for p in PLATES["plates"]:
        plate_counts: dict[str, int] = {}
        for pp in p["parts"]:
            base = re.sub(r"_i\d+$", "", pp["name"])
            plate_counts[base] = plate_counts.get(base, 0) + 1
        parts_txt = esc(", ".join(
            friendly(base) if n == 1 else f"{friendly(base)} ×{n}"
            for base, n in plate_counts.items()))
        if "washer" in parts_txt:
            parts_txt += " <i>(the robot uses 2 — the rest are spares)</i>"
        rows += (
            f"<tr><td style='text-align:center'><b>{p['plate_number']}</b></td>"
            f"<td><span style='display:inline-block;width:.13in;height:.13in;border-radius:50%;"
            f"background:{p['color_hex']};border:1px solid rgba(0,0,0,.25); vertical-align:-2px;'></span> "
            f"{esc(p['name'].replace(' - ', ' · '))}</td>"
            f"<td style='text-align:center'>{p['part_count']}</td>"
            f"<td>{parts_txt}</td></tr>")
    add(f"""
      {eyebrow(1)}
      <h2>The {N_PLATES} prototype plates, in printing order</h2>
      <table class="roomy" style="font-size:10.5px;"><tr><th style="width:.35in;">#</th><th style="width:2.4in;">Plate (load this filament)</th><th style="width:.5in;">Parts</th><th>What’s on it</th></tr>{rows}</table>
      <p style="margin-top:.12in; font-size:11px;"><b>Tip:</b> the plates are already grouped by exact material and color.
      Print each group back to back, then label its box before changing filament.</p>""",
        chapter=1)

    # Coupons: keep the original mechanical checks and the new material
    # qualification evidence on separate pages so the recording fields remain
    # readable instead of becoming microscopic ant paperwork.
    standard_coupons = [(k, v) for k, v in COUPONS.items()
                        if "_pla_" not in k and "lid_boundary" not in k]
    material_coupons = [(k, v) for k, v in COUPONS.items()
                        if "_pla_" in k or "lid_boundary" in k]
    for coupon_page, coupon_items in enumerate((standard_coupons, material_coupons), start=1):
        crows = "".join(f"<tr><td><b>{esc(COUPON_TITLES.get(k, k))}</b><br>"
                        f"<span class='mono'>{esc(k)}.stl</span></td>"
                        f"<td>{esc(v['material'])}</td><td>{esc(COUPON_NOTES.get(k, v['note']))}</td></tr>"
                        for k, v in coupon_items)
        intro = ("These checks prove the shared screw, wheel, switch, board, and motion interfaces."
                 if coupon_page == 1 else
                 "These checks are specific to the exact PLA/PETG product lines you load. A pass never transfers to another brand, subtype, or effect filament.")
        record = "" if coupon_page == 1 else """
          <div style="margin-top:.12in; border:2px solid var(--red); border-radius:.1in; padding:.08in .12in; font-size:10px;">
            <b>RECORD BEFORE PASS:</b> manufacturer · product line · subtype · color · nozzle · layer height · wall count ·
            insert-tool temperature (when used) · measurements · pass/fail · tester · date. Blank evidence means the gate is open.
          </div>"""
        add(f"""
          {eyebrow(1)}
          <h2>Print the little test parts first ({coupon_page} of 2)</h2>
          <p style="margin-bottom:.1in;">Generate them with <b>cad/python/robot_body_v2_coupons.py</b>. {intro}</p>
          <table class="roomy" style="font-size:10.5px;"><tr><th>Test part</th><th>Filament</th><th>What it proves</th></tr>{crows}</table>
          {record}""", chapter=1)

    # Piece inventory
    counts: dict[str, int] = {}
    colors: dict[str, str] = {}
    for pl in PLATES["plates"]:
        for pp in pl["parts"]:
            base = re.sub(r"_i\d+$", "", pp["name"])
            counts[base] = counts.get(base, 0) + 1
            colors[base] = pl["color_hex"]
    cells = ""
    for base, n in counts.items():
        note = " <span style='font-weight:600; font-size:8px; color:var(--ink2);'>(4 spares)</span>" \
            if base == "printed_washer_v2" else ""
        cells += (f'<div class="invcell"><span class="swatch" style="background:{colors[base]}"></span>'
                  f'<img src="{img_uri(GUIDE_IMG / ("thumb_" + base + ".png"))}">'
                  f'<div class="nm">{esc(friendly(base))}</div><div class="ct">&times;{n}{note}</div></div>')
    add(f"""
      {eyebrow(1)}
      <h2>When the printer stops: count your pieces</h2>
      <p style="margin-bottom:.12in;">All {N_PIECES} printed pieces: {N_FUNCTIONAL} installed functional parts,
      {N_SPARES} spare washers, and {N_OPTIONAL} optional cosmetic skin. Line yours up before Chapter 3; the dot shows each piece’s current effective color.</p>
      <div class="invgrid">{cells}</div>""",
        chapter=1)

    # --- Chapter 3: build ----------------------------------------------------
    add(f"""
      <img class="hero" src="{img_uri(IMG / 'codex_robot_body_v2_chassis.png')}">
      <div style="width:4.3in; padding-top:1.05in;">
        {eyebrow(2)}
        <h1 style="font-size:52px;">Build it</h1>
        <p style="font-size:14px; margin-top:.2in; width:3.9in;">Twenty steps. Lay out the parts from each step’s
        GATHER strip before you start, match the big picture, then run the green CHECK.</p>
        <p style="font-size:13px; margin-top:.15in; width:3.9in;">The little <b>FRONT</b> tag on every picture points
        at the robot’s face, so left and right never get confusing.</p>
        <p style="font-size:13px; margin-top:.15in; width:3.9in;">One rule: <b>go in order.</b> The steps nest —
        skipping ahead means taking things apart later.</p>
        <div style="display:flex; gap:.3in; margin-top:.32in; width:4in; border-top:1px solid var(--line); padding-top:.18in;">
          {"".join(
              '<div style="flex:1;">' + "".join(
                  f'<div style="display:flex; gap:.07in; margin-bottom:.052in; align-items:baseline;">'
                  f'<span style="font-size:9.5px; font-weight:800; color:var(--teal); width:.16in; text-align:right;">{n}</span>'
                  f'<span style="font-size:9.5px; font-weight:500;">{esc(t)}</span></div>'
                  for n, (_, t, *_) in col) + "</div>"
              for col in (list(enumerate(STEPS, start=1))[:10], list(enumerate(STEPS, start=1))[10:]))}
        </div>
      </div>""",
        chapter=2, footer=False, mark="ch2")

    # Steps
    for i, (img_name, title, screws, items, subs, check) in enumerate(STEPS, start=1):
        label = FRONT_LABEL.get(img_name, "&#8601; FRONT")
        front_chip = f'<div class="frontchip">{label}</div>' if label else ""
        inset = ""
        if img_name in INSETS:
            inset_img, inset_caption = INSETS[img_name]
            inset = (
                f'<div style="position:absolute; top:.1in; right:.1in; width:2.05in; background:#fff;'
                f' border:1px solid var(--line); border-radius:.1in; overflow:hidden;'
                f' box-shadow:0 1px 6px rgba(0,0,0,.2);">'
                f'<img src="{img_uri(GUIDE_IMG / (inset_img + ".png"))}" style="width:100%; display:block;">'
                f'<div style="font-size:8.5px; font-weight:700; letter-spacing:.06em; padding:.035in .06in;'
                f' color:var(--teal-dk); text-transform:uppercase;">{inset_caption}</div></div>')
        if img_name in EXTRA_PANELS:
            panel_count = len(EXTRA_PANELS[img_name])
            panel_h = 2.15 if panel_count > 1 else 2.55
            chunks = []
            for panel_i, (panel_img, panel_caption) in enumerate(EXTRA_PANELS[img_name]):
                top = 0.10 + panel_i * (panel_h + 0.12)
                chunks.append(
                    f'<div style="position:absolute; top:{top:.2f}in; right:.1in; width:2.25in; background:#fff;'
                    f' border:1px solid var(--line); border-radius:.1in; overflow:hidden;'
                    f' box-shadow:0 1px 6px rgba(0,0,0,.2);">'
                    f'<img src="{img_uri(GUIDE_IMG / (panel_img + ".png"))}" '
                    f'style="width:100%; height:{panel_h - .38:.2f}in; object-fit:cover; display:block;">'
                    f'<div style="font-size:8px; font-weight:700; line-height:1.15; padding:.045in .06in;'
                    f' color:var(--teal-dk); text-transform:uppercase;">{panel_caption}</div></div>')
            inset = "".join(chunks)
        cells = strip_cells(img_name, items, screws)
        strip_cls = "strip dense" if len(items) + (1 if screws else 0) >= 6 else "strip"
        lis = "".join(f"<li>{esc(s)}</li>" for s in subs)
        add(f"""
          <div class="stephead"><div class="stepnum">{i}</div><h2>{esc(title)}</h2>{progress(i)}</div>
          <div class="{strip_cls}"><span class="gather">GATHER</span>{cells}</div>
          <div class="stepbody">
            <div class="imgwrap"><img class="main" src="{img_uri(GUIDE_IMG / (img_name + '.png'))}">
              {front_chip}{inset}</div>
            <div class="instr"><ol>{lis}</ol>
              <div class="check"><span class="box"></span><div><b>CHECK</b>{esc(check)}</div></div></div>
          </div>""",
            chapter=2)

    # --- Chapter 4: wire -----------------------------------------------------
    add(f"""
      {eyebrow(3)}
      <h2>Where every electronic part lives</h2>
      <div class="cols">
        <div><img src="{img_uri(IMG / 'codex_robot_body_v2_populated_cutaway.png')}"
             style="width:100%; border-radius:.12in; border:1px solid var(--line-soft);"></div>
        <div>
          <table style="font-size:10.5px;">
            <tr><th>Part</th><th>Home</th><th>Faces</th></tr>
            <tr><td><b>MDDS10 motor board</b></td><td>tower posts, front-center</td><td>terminals RIGHT</td></tr>
            <tr><td><b>Raspberry Pi 5</b></td><td>tower top shelf</td><td>USB ports BACK</td></tr>
            <tr><td><b>Pico 2</b></td><td>floor, right of tower</td><td>USB/SWD service ends accessible; never cabled to Pi</td></tr>
            <tr><td><b>Battery</b></td><td>middle-back floor</td><td>wires BACK</td></tr>
            <tr><td><b>Relay</b></td><td>floor pocket, left</td><td>terminals UP</td></tr>
            <tr><td><b>Fuse block</b></td><td>deck, left half</td><td>wire exit LEFT edge</td></tr>
            <tr><td><b>Regulators (5 V + 6 V)</b></td><td>hang UNDER deck, back half</td><td>6 V wire exit FRONT</td></tr>
            <tr><td><b>Big red button</b></td><td>through the lid</td><td>UP; test with a centered firm press</td></tr>
            <tr><td><b>Mic array</b></td><td>under the lid slots</td><td>UP</td></tr>
            <tr><td><b>Speakers</b></td><td>side shelves</td><td>grilles OUT</td></tr>
            <tr><td><b>ToF distance boards</b></td><td>2 behind face, 2 side windows</td><td>lenses OUT</td></tr>
            <tr><td><b>Bumper feeler switches ×6</b></td><td>pockets under the tray edge</td><td>buttons OUT</td></tr>
            <tr><td><b>Charger inlet + mute</b></td><td>back panel holes</td><td>BACK</td></tr>
            <tr><td><b>Camera</b></td><td>head, pocket behind the face opening</td><td>lens FRONT</td></tr>
            <tr><td><b>Pan + tilt servos</b></td><td>pan inside the neck, tilt in the head’s side</td><td>pan shaft UP, tilt shaft SIDEWAYS</td></tr>
            <tr><td><b>Glow boards ×4</b></td><td>pockets behind the eye + status bars</td><td>lights OUT</td></tr>
          </table>
          <p style="font-size:10px; margin-top:.08in; color:var(--red);"><b>PROTOTYPE HOLD:</b> This populated cutaway
          proves placement only. MAX98357A mounts, NeoPixel installation, and the exact harness schedule are not released yet.</p>
        </div>
      </div>""",
        chapter=3, mark="ch3")

    # Wiring rules + power map
    rules = "".join(f'<div class="rule">{esc(r)}</div>' for r in WIRE_RULES)
    prow = "".join(f"<tr><td>{esc(a)}</td><td>{esc(b)}</td><td>{esc(c)}</td></tr>" for a, b, c in POWER_MAP)
    add(f"""
      {eyebrow(3)}
      <h2>The wiring rules</h2>
      {rules}
      <h3 style="margin-top:.15in;">The power map (every 12 V wire)</h3>
      <table class="roomy" style="font-size:11.5px;"><tr><th>From</th><th>Through</th><th>To</th></tr>{prow}</table>""",
        chapter=3)

    # SVG power diagram
    add(f"""
      {eyebrow(3)}
      <h2>Power, as a picture</h2>
      <svg viewBox="0 0 1000 560" style="width:100%; height:6.5in;">
        <defs><marker id="a" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
          <path d="M0,0 L6,3 L0,6 z" fill="#6E6553"/></marker></defs>
        <rect x="20" y="230" width="150" height="90" rx="12" fill="#075365"/>
        <text x="95" y="270" fill="#fff" font-size="20" font-weight="bold" text-anchor="middle">BATTERY</text>
        <text x="95" y="295" fill="#9fd4e2" font-size="14" text-anchor="middle">12 V LiFePO4</text>
        <rect x="240" y="150" width="120" height="60" rx="10" fill="#B8892E"/>
        <text x="300" y="186" font-size="15" font-weight="bold" text-anchor="middle" fill="#fff">FEEDER FUSE</text>
        <rect x="430" y="130" width="170" height="100" rx="10" fill="#22231F"/>
        <text x="515" y="170" fill="#fff" font-size="16" font-weight="bold" text-anchor="middle">FUSE BLOCK</text>
        <text x="515" y="192" fill="#bbb" font-size="12" text-anchor="middle">4 fused branches</text>
        <g>
          <rect x="688" y="40" width="214" height="52" rx="10" fill="#fff" stroke="#d8cfb6"/>
          <rect x="688" y="40" width="8" height="52" rx="4" fill="#2b6cb0"/>
          <text x="800" y="72" fill="#22231F" font-size="14" font-weight="bold" text-anchor="middle">5 V REG → RASPBERRY PI</text>
          <rect x="688" y="110" width="214" height="52" rx="10" fill="#fff" stroke="#d8cfb6"/>
          <rect x="688" y="110" width="8" height="52" rx="4" fill="#2f855a"/>
          <text x="800" y="142" fill="#22231F" font-size="14" font-weight="bold" text-anchor="middle">6 V REG → NECK SERVOS</text>
          <rect x="688" y="180" width="214" height="52" rx="10" fill="#fff" stroke="#d8cfb6"/>
          <rect x="688" y="180" width="8" height="52" rx="4" fill="#2b6cb0"/>
          <text x="800" y="205" fill="#22231F" font-size="13" font-weight="bold" text-anchor="middle">MUTE SWITCH → MIC</text>
          <text x="800" y="222" fill="#C4230F" font-size="11" text-anchor="middle">or red mute ring</text>
          <rect x="688" y="250" width="214" height="52" rx="10" fill="#fff" stroke="#d8cfb6"/>
          <rect x="688" y="250" width="8" height="52" rx="4" fill="#2b6cb0"/>
          <text x="800" y="282" fill="#22231F" font-size="14" font-weight="bold" text-anchor="middle">GLOW LIGHTS (5 V)</text>
        </g>
        <rect x="240" y="360" width="120" height="60" rx="10" fill="#B8892E"/>
        <text x="300" y="396" font-size="15" font-weight="bold" text-anchor="middle" fill="#fff">MOTOR FUSE</text>
        <rect x="430" y="350" width="150" height="80" rx="10" fill="#22231F"/>
        <text x="505" y="382" fill="#fff" font-size="16" font-weight="bold" text-anchor="middle">RELAY</text>
        <text x="505" y="404" fill="#f0a89d" font-size="11" text-anchor="middle">coil runs through the</text>
        <text x="505" y="418" fill="#f0a89d" font-size="11" text-anchor="middle">RED BUTTON + Pico OK</text>
        <rect x="660" y="350" width="150" height="80" rx="10" fill="#5e2b7a"/>
        <text x="735" y="384" fill="#fff" font-size="15" font-weight="bold" text-anchor="middle">MDDS10</text>
        <text x="735" y="406" fill="#dcf" font-size="12" text-anchor="middle">motor board</text>
        <rect x="860" y="340" width="110" height="44" rx="10" fill="#fff" stroke="#d8cfb6"/>
        <text x="915" y="367" fill="#22231F" font-size="13" font-weight="bold" text-anchor="middle">MOTOR L</text>
        <rect x="860" y="396" width="110" height="44" rx="10" fill="#fff" stroke="#d8cfb6"/>
        <text x="915" y="423" fill="#22231F" font-size="13" font-weight="bold" text-anchor="middle">MOTOR R</text>
        <rect x="20" y="440" width="220" height="70" rx="12" fill="#0B6E84"/>
        <text x="130" y="470" fill="#fff" font-size="14" font-weight="bold" text-anchor="middle">CHARGER PLUG (EN2)</text>
        <text x="130" y="492" fill="#c9ecf5" font-size="11" text-anchor="middle">pins 1+2 → battery charge lead</text>
        <path d="M170,260 C210,260 210,180 240,180" stroke="#C4230F" stroke-width="5" fill="none" marker-end="url(#a)"/>
        <path d="M360,180 L430,180" stroke="#C4230F" stroke-width="5" fill="none" marker-end="url(#a)"/>
        <path d="M600,155 C650,155 650,66 688,66" stroke="#2b6cb0" stroke-width="4" fill="none" marker-end="url(#a)"/>
        <path d="M600,175 C650,175 650,136 688,136" stroke="#2f855a" stroke-width="4" fill="none" marker-end="url(#a)"/>
        <path d="M600,195 C650,195 650,206 688,206" stroke="#2b6cb0" stroke-width="4" fill="none" marker-end="url(#a)"/>
        <path d="M600,215 C650,215 650,276 688,276" stroke="#2b6cb0" stroke-width="4" fill="none" marker-end="url(#a)"/>
        <path d="M170,300 C210,300 210,390 240,390" stroke="#C4230F" stroke-width="5" fill="none" marker-end="url(#a)"/>
        <path d="M360,390 L430,390" stroke="#DFA400" stroke-width="5" fill="none" marker-end="url(#a)"/>
        <path d="M580,390 L660,390" stroke="#DFA400" stroke-width="5" fill="none" marker-end="url(#a)"/>
        <path d="M810,368 L860,362" stroke="#DFA400" stroke-width="4" fill="none" marker-end="url(#a)"/>
        <path d="M810,412 L860,418" stroke="#DFA400" stroke-width="4" fill="none" marker-end="url(#a)"/>
        <path d="M130,440 C130,380 95,360 95,320" stroke="#075365" stroke-width="4" fill="none" marker-end="url(#a)"/>
        <text x="300" y="135" font-size="12" fill="#6E6553" text-anchor="middle" font-weight="bold">RED = always-hot 12 V</text>
        <text x="468" y="342" font-size="12" fill="#6E6553" font-weight="bold">YELLOW = motor 12 V, dead unless the relay says so</text>
      </svg>""",
        chapter=3)

    # Signal map
    srow = "".join(f"<tr><td>{esc(a)}</td><td>{esc(b)}</td><td>{esc(c)}</td></tr>" for a, b, c in SIGNAL_MAP)
    add(f"""
      {eyebrow(3)}
      <h2>The signal map (thin wires)</h2>
      <div style="padding:.1in .14in; margin-bottom:.12in; border:2px solid var(--red); color:var(--red); font-size:11px; font-weight:700;">
        PICO USB/SWD ARE SERVICE-ONLY. DO NOT CONNECT THEM TO THE PI INSIDE THE ROBOT.
      </div>
      <table style="font-size:11px;"><tr><th>From</th><th>To</th><th>What travels</th></tr>{srow}</table>
      <div class="cols" style="margin-top:.15in;">
        <div>
          <h3 style="margin-top:0;">Cable neatness</h3>
          <p style="font-size:11.5px;">Quiet wires (signals, audio, sensors) ride the LEFT channel under the deck.
          Power wires ride the RIGHT channel. The camera ribbon goes up the little tunnel beside the neck servo,
          through the hollow neck, into the head. Zip-tie at every printed tie point; no wire may touch a wheel or the fan.</p>
        </div>
        <div>
          <h3 style="margin-top:0;">Before the battery goes in: the meter checklist</h3>
          <p style="font-size:11.5px;">No shorts first: beep-test + to − at the fuse block (no fuses in yet). Then:</p>
          <ol style="font-size:11.5px; margin-left:.25in;">
          <li>Red button held down = relay coil circuit reads OPEN.</li>
          <li>Regulator outputs read 5.0–5.2 V and 6.0 V on the bench before their loads connect.</li>
          <li>Do not choose or install fuses until the measured-load, conductor, inrush, selective-clearing, and thermal evidence is released.</li>
          <li>Charger plug in = motors will not run.</li>
          <li>For the first powered test, close the lid with its 4 corner screws. Reopen only while shut down with the motor branch physically isolated.</li></ol>
        </div>
      </div>""",
        chapter=3)

    # --- Chapter 5: check & play ---------------------------------------------
    add(f"""
      <img class="hero" src="{img_uri(IMG / 'codex_robot_body_v2_assembled.png')}">
      <div style="width:4.4in; padding-top:.6in;">
        {eyebrow(4)}
        <div style="display:inline-block; background:var(--red); color:white; padding:.06in .12in; font-size:11px; font-weight:800; letter-spacing:.08em;">PROTOTYPE PREVIEW — NO POWERED MOTION</div>
        <h2 style="font-size:36px; letter-spacing:-.8px; margin-top:.12in;">The body preview is assembled</h2>
        <p style="font-size:13px; margin-top:.08in; width:3.9in;">The Pi installer, Pico firmware release, executable harness schedule,
        head mechanism, and signed commissioning procedure are not shipped yet. Do not energize the motor branch from this book.</p>
        <h3 style="margin-top:.2in;">Commissioning gate</h3>
        <p style="font-size:11.5px; width:3.9in;">A released checklist must cover both E-stop NC channels and physical reset;
        all six NC bumper zones plus a broken wire; watchdog and setpoint-lease expiry; velocity/acceleration clamps;
        charger inhibit; low-battery cutoff; hardware mic mute with no backfeed; regulator polarity and voltage;
        branch-by-branch power-up; stop latency; motor direction; and a wheels-off-ground run before any floor test.</p>
        <p style="font-size:11.5px; margin-top:.1in; width:3.9in;">Until those artifacts and physical results exist,
        Rover Bean’s number one rule is wonderfully easy: <b>admire, measure, and keep the battery out.</b></p>
      </div>""",
        chapter=4, footer=False, mark="ch4")

    # --- Back cover ----------------------------------------------------------
    features = "".join(
        f'<div style="display:flex; gap:.14in; margin-bottom:.17in; align-items:flex-start;">'
        f'<div style="flex:none; width:.34in; height:.34in; border-radius:.09in; background:rgba(255,255,255,.12);'
        f' display:flex; align-items:center; justify-content:center;">{icon}</div>'
        f'<div><div style="font-size:12.5px; font-weight:700; letter-spacing:.06em; color:#fff;">{t}</div>'
        f'<div style="font-size:11px; color:#B7D6DE; line-height:1.4;">{d}</div></div></div>'
        for icon, t, d in [
            ('<svg width="18" height="18" viewBox="0 0 18 18"><circle cx="9" cy="9" r="6.5" fill="none" stroke="#B9E44A" stroke-width="1.8"/><path d="M9 5.2 12.3 7.1 12.3 10.9 9 12.8 5.7 10.9 5.7 7.1 Z" fill="none" stroke="#B9E44A" stroke-width="1.4"/></svg>',
             "ONE SCREW, ONE KEY",
             f"Every one of the {N_SCREWS} screws is the same M3 × 8, and one 2.5 mm hex key turns them all."),
            ('<svg width="18" height="18" viewBox="0 0 18 18"><path d="M2.5 13.5 H15.5 M2.5 10 H15.5 M2.5 6.5 H15.5" stroke="#B9E44A" stroke-width="1.8" stroke-linecap="round"/><path d="M9 4.5 V1.5 M7.2 3 L9 1.2 L10.8 3" stroke="#B9E44A" stroke-width="1.5" fill="none" stroke-linecap="round"/></svg>',
             "ZERO SUPPORTS",
             f"{N_FUNCTIONAL} functional + {N_SPARES} spare + {N_OPTIONAL} optional pieces target {N_PLATES} prototype plates. Physical gates remain open."),
            ('<svg width="18" height="18" viewBox="0 0 18 18"><path d="M5.6 2.2 H12.4 L15.8 5.6 V12.4 L12.4 15.8 H5.6 L2.2 12.4 V5.6 Z" fill="none" stroke="#B9E44A" stroke-width="1.8" stroke-linejoin="round"/></svg>',
             "FAILS STOPPED",
             "The E-stop is physical; bumper latches and the watchdog live in independent safety firmware, with no Pi software required."),
        ])
    add(f"""
      <div style="position:absolute; inset:0; background:var(--teal-dk); padding:.65in .75in; display:flex; flex-direction:column;">
        <div style="font-size:11px; font-weight:700; letter-spacing:.24em; color:#7FB6C4;">CODEX ROVER BEAN</div>
        <div style="position:absolute; left:.75in; top:.92in; background:#C4230F; color:#fff; padding:.07in .12in; font-size:10px; font-weight:800; letter-spacing:.08em;">PROTOTYPE PREVIEW — NO POWERED MOTION</div>
        <div style="display:flex; gap:.55in; flex:1; align-items:center;">
          <div style="width:4.1in;">
            <div style="font-size:33px; font-weight:800; color:#fff; line-height:1.12; letter-spacing:-.5px; margin-bottom:.32in;">
              Print coupons.<br>Dry-build the chassis.<br>Measure everything.</div>
            {features}
          </div>
          <div style="flex:1;">
            <div style="border-radius:.16in; overflow:hidden; border:1px solid rgba(255,255,255,.18);">
              <img src="{img_uri(IMG / 'codex_robot_body_v2_populated_cutaway.png')}" style="width:100%; display:block;"></div>
            <p style="font-size:10px; color:#7FB6C4; margin-top:.08in; text-align:center; letter-spacing:.08em;">
              INSIDE: RASPBERRY PI 5 BRAIN &middot; SAFETY CO-PILOT &middot; FAIL-STOPPED POWER</p>
          </div>
        </div>
        <div style="display:flex; justify-content:space-between; font-size:9.5px; font-weight:600;
             letter-spacing:.14em; color:#7FB6C4;">
          <span>BODY V2 &middot; PRINTED-ONLY STRUCTURE</span>
          <span>github.com/brianpattison/robot</span>
        </div>
      </div>""",
        footer=False, mark="back")

    return pages


def build_cover(chapter_pages):
    toc_rows = ""
    for idx, (label, color, name, desc) in enumerate(CHAPTERS):
        toc_rows += (f'<div class="row"><span class="n" style="color:{color}">{idx + 1}</span>'
                     f'<span class="t">{name}</span><span class="d">{desc}</span>'
                     f'<span class="lead"></span><span class="pg">{chapter_pages[idx]}</span></div>')
    chips = "".join(f'<span class="statchip">{c}</span>' for c in
                    ("AGES 10+", f"{N_FUNCTIONAL} FUNCTIONAL + {N_SPARES} SPARE + {N_OPTIONAL} OPTIONAL",
                     f"{N_PLATES} PLATES", "ONE HEX KEY"))
    return f"""
      <img class="hero" src="{img_uri(IMG / 'codex_robot_body_v2_assembled.png')}">
      <div style="width:4.4in; padding-top:.55in;">
        <div class="eyebrow" style="color:var(--gold);"><i style="background:var(--gold)"></i>A prototype print-and-build preview</div>
        <div style="display:inline-block; margin:.08in 0 .04in; background:var(--red); color:#fff; padding:.07in .12in; font-size:11px; font-weight:800; letter-spacing:.08em;">DO NOT USE FOR POWERED MOTION</div>
        <h1 style="font-size:55px;">CODEX<br>ROVER BEAN</h1>
        <p style="font-size:19px; font-weight:600; margin-top:.16in;">The Robot Body Builder’s Book</p>
        <p style="font-size:13px; margin-top:.08in; color:var(--ink2);">Review the geometry, print coupons, and dry-build the released chassis steps.<br>
        Software, firmware, the production harness, head physical qualification, and commissioning remain open.</p>
        <div style="display:flex; gap:.09in; margin-top:.22in; flex-wrap:wrap;">{chips}</div>
        <div class="toc">{toc_rows}</div>
        <p style="font-size:9.5px; font-weight:600; letter-spacing:.14em; color:#A2967C; margin-top:.28in;">
          BODY V2 &middot; ZERO SUPPORTS &middot; {N_SCREWS} SCREWS, ONE SIZE</p>
      </div>"""


def check_images(pages_html):
    from urllib.parse import unquote
    missing = []
    for pg in pages_html:
        for m in re.finditer(r'src="file://([^"]+)"', pg):
            if not Path(unquote(m.group(1))).exists():
                missing.append(unquote(m.group(1)))
    if missing:
        raise SystemExit("MISSING GUIDE IMAGES:\n" + "\n".join(missing))


def main():
    HTML_OUT.parent.mkdir(parents=True, exist_ok=True)
    PDF_OUT.parent.mkdir(parents=True, exist_ok=True)
    body_pages = build_body_pages()
    total = len(body_pages) + 1
    # Chapter start page numbers (cover is page 1; body pages start at 2).
    chapter_pages = []
    for idx in range(len(CHAPTERS)):
        first = next(i for i, p in enumerate(body_pages) if p["mark"] == f"ch{idx}")
        chapter_pages.append(first + 2)
    cover = {"html": build_cover(chapter_pages), "chapter": None, "footer": False, "mark": "cover"}
    pages = [cover] + body_pages
    check_images([p["html"] for p in pages])
    body = "".join(
        page(p["html"], chapter=p["chapter"], footer=p["footer"], num=i, total=total)
        for i, p in enumerate(pages, start=1))
    html_doc = ("<!doctype html><html><head><meta charset='utf-8'>"
                "<title>Codex Rover Bean — Builder’s Book</title>"
                f"<style>{CSS}</style></head><body>{body}</body></html>")
    html_doc = "\n".join(line.rstrip() for line in html_doc.splitlines()) + "\n"
    HTML_OUT.write_text(html_doc, encoding="utf-8")
    result = subprocess.run(
        [CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
         "--no-margins", f"--print-to-pdf={PDF_OUT}", HTML_OUT.resolve().as_uri()],
        capture_output=True, text=True, timeout=300)
    if not PDF_OUT.exists():
        raise SystemExit(f"Chrome PDF failed:\n{result.stderr[-2000:]}")
    print(f"wrote {HTML_OUT}")
    print(f"wrote {PDF_OUT} ({total} pages)")


if __name__ == "__main__":
    main()
