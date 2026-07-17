"""Generate the v2 assembly guide: print-first HTML -> PDF, ages 10+.

Authors the complete builder's book as fixed-size HTML pages (11 x 8.5 in
landscape) styled like an advanced LEGO product manual, then prints it to
PDF with headless Chrome. Content is generated from the live artifacts —
the printed-part registry, joint/fastener registries, the Bambu plate
manifest, and the coupon manifest — plus the authored step and wiring
copy below, so the book cannot drift from the model.

Chapters: cover, how-to-read, shopping (filament / fasteners /
electronics / tools), printing with Bambu Studio (plates + coupons),
grown-up inserts, twenty assembly steps with checks, the electronics
orientation page, the grown-up wiring chapter with SVG power and signal
maps, and the finish/test page.

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
COUPONS = json.loads((ROOT / "cad" / "exports" / "v2" / "coupons" /
                      "codex_robot_body_v2_coupons_manifest.json").read_text())
COUPON_KID_NOTES = {
    "coupon_insert_m3": "Grown-up melts one insert into each of the three holes. The one that sits flush without squeezing out goo is your printer's perfect fit.",
    "coupon_joint_flange": "Screw the small plate onto the block with one screw. It should pull down tight with no wobble and no cracking.",
    "coupon_joint_boss": "The partner block for the plate test above.",
    "coupon_dbore_torque": "Grown-up pushes this onto a motor shaft and twists HARD, twice as hard as driving ever will. If it never slips, wheels are safe.",
    "coupon_axle_stub": "Spin the ring on the peg a few hundred times with some pressure. It should stay smooth, not sloppy.",
    "coupon_bushing_ring": "The spinning ring for the peg test above.",
    "coupon_snap_pair": "Click the two pieces together and apart ten times. The little hook must survive and still hold on.",
    "coupon_bayonet_pair": "Twist the ring onto the stub a quarter turn - it should lock with a nice click and not pull straight off.",
    "coupon_switch_pocket": "Grown-up seats one bumper switch in the pocket: it must click when pressed and spring back, never jammed.",
    "coupon_tire_fit": "Stretch the mini tire onto the mini wheel. Snug and even = your big tires will fit too.",
    "coupon_pcb_clamp": "Rest the little green safety board on the pegs and screw the bar over it. Held gently, nothing bending.",
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
N_SCREWS, N_INSERTS = inv.fastener_tally()

# ---------------------------------------------------------------------------
# Authored content
# ---------------------------------------------------------------------------
SHOP_FILAMENT = [
    ("Cream PETG", "1x 1 kg spool (uses ~600 g)", "The body, tray, head, and most parts."),
    ("Teal PETG", "1x small spool or 250 g (uses ~80 g)", "The top lid."),
    ("Charcoal / black PETG", "leftovers are fine (~20 g)", "Face panel, back panel, head face."),
    ("Translucent lime PETG", "smallest spool available (uses ~5 g)", "The glowing eye and light bars."),
    ("Charcoal TPU 95A", "1x 500 g spool (uses ~280 g)", "Soft tires, bumpers, battery pad."),
]
SHOP_FASTENERS = [
    ("M3 x 8 mm socket head screws", "1x 100-pack", f"The ONLY screw in the robot ({N_SCREWS} used + spares)."),
    ("M3 x 5.7 mm brass heat-set inserts (4.6 mm OD)", "1x 100-pack", f"The only insert ({N_INSERTS} used + spares)."),
]
SHOP_ELECTRONICS = [
    ("Raspberry Pi 5 (8 GB)", "1", "The robot's computer."),
    ("32 GB+ A2 microSD card", "1", "The computer's memory card - the robot's programs live here."),
    ("Raspberry Pi Camera Module 3 Wide + long FPC cable", "1", "The robot's eye."),
    ("Raspberry Pi Pico 2 (no headers, no WiFi)", "1", "The safety helper: reflexes and watchdog."),
    ("Cytron MDDS10 motor driver", "1", "The purple board that powers the wheels."),
    ("Pololu #4867 gearmotor (99:1, 25D, 12 V, encoder)", "2", "The wheel motors."),
    ("Hitec D85MG servo", "2", "The neck motors (look left/right, up/down)."),
    ("Bioenno BLF-1203AB 12 V 3 Ah LiFePO4 battery", "1", "The robot's power pack."),
    ("Bioenno BPC-1502DC charger", "1", "The matching charger. Only ever use this one."),
    ("Switchcraft EN2P3M20 inlet + EN2C3F20G2 plug", "1 pair", "The keyed charging plug on the back."),
    ("Pololu D24V90F5 regulator (5 V)", "1", "Makes clean 5 V for the Pi."),
    ("Pololu D36V50F6 regulator (6 V)", "1", "Makes 6 V for the neck servos."),
    ("Panasonic CB1A-R-M-12V relay", "1", "The motor power switch the red button controls."),
    ("Blue Sea Systems 5045 fuse block", "1", "Splits power safely into four fused branches."),
    ("ATO fuses: 2 A, 3 A, 5 A, 7.5 A assortment", "1 kit", "Branches start at 2-3 A (5 A max); feeder 7.5 A; motor branch 5 A. Grown-up confirms with the meter."),
    ("IDEC XW1E-BV402M-R emergency stop", "1", "THE BIG RED BUTTON."),
    ("E-Switch PVB3F230SS311 mute switch", "1", "The microphone privacy switch (glows red when muted)."),
    ("Omron D2HW-C202MR bumper switches", "6", "Feelers inside the bumpers."),
    ("VL53L1X time-of-flight boards (Adafruit 3967)", "4", "Distance eyes: two in front, one each side."),
    ("Adafruit 5975 NeoPixel breakouts + JST-SH cables", "4", "The glowing eyes and status lights."),
    ("ReSpeaker USB mic array", "1", "The robot's ears."),
    ("Enclosed 3 W 4 ohm speakers + 2x Adafruit MAX98357A amps", "1 set", "The robot's voice."),
    ("18 AWG (power) + 22 AWG (signal) silicone wire, JST/spade connectors, ferrules, zip ties, heat-shrink", "1 kit", "Grown-up wiring supplies."),
]
SHOP_TOOLS = [
    ("2.5 mm hex key", "Turns every screw in this robot. Seriously, all of them."),
    ("Soldering iron (grown-up)", "Melts the brass inserts into the plastic."),
    ("Small flush cutters / scissors", "Trims zip ties and TPU strings."),
    ("Painter's tape + marker", "Label wires as you go."),
    ("Multimeter (grown-up)", "Checks every circuit before the battery ever goes in."),
]

PRINT_TIPS = [
    ("Open the project", f"Open <b>codex_robot_body_v2_p1s.3mf</b> in Bambu Studio. All {N_PLATES} plates are already laid out for the P1S with a 0.4 mm nozzle and Textured PEI plate."),
    ("Load the right color", "Each plate's name says the filament to load (cream, teal, charcoal, lime, or TPU). Print plates one at a time and change filament between groups."),
    ("No supports. Ever.", "Every part is designed to print with zero supports. If the slicer asks for supports, something is wrong - don't add them, re-check the plate."),
    ("TPU is slow and squishy", "Print the tire and bumper plates slowly (the profile already does this). Dry TPU prints much better."),
    ("Big flat parts stay put", "The tray, shell, and bumper plates fill the whole bed. Clean the plate with dish soap first so they stick."),
]

STEPS = [
    ("step_01_tray", "Start with the floor", False, 0,
     [("tray_v2", 1)],
     ["Clear a big table. Put the tray down flat, wheel cutouts toward you.",
      "Find the two round motor cradles at the back and the tall round towers - that's the back of the robot."],
     "The tray sits flat and doesn't rock."),
    ("step_02_inserts", "Melt in the tray's brass inserts", True, 0,
     [("px_insert", 20)],
     ["GROWN-UP: set the soldering iron to about 220 C.",
      "Rest a brass insert in each gold-marked hole, then press it straight down with the hot iron tip until it sits flush.",
      "20 go into the tray now - the picture marks every spot. The other 21 come later: 2 in the wheels, 2 in the front pods, 14 in the shell, 2 in the lid, and 1 in the head. This book asks the grown-up back each time."],
     "Every insert is flush and straight, none tilted."),
    ("step_03_motors", "Drop in the motors", False, SCREWS["motor_caps"],
     [("px_motor_L", 2), ("motor_cap_v2", 2)],
     ["Lay a motor in each cradle with the metal shaft poking OUT through the hole toward the wheel side.",
      "Point the wires inward, toward the middle of the robot.",
      "Set a printed cap over each motor and screw it down with 2 screws per cap - snug, not gorilla-tight."],
     "Motors don't wiggle. Shafts spin freely when you twist them."),
    ("step_04_wheels_bench", "Make the wheels", False, 0,
     [("rear_wheel_v2", 2), ("front_wheel_v2", 2), ("tire_v2", 4), ("px_insert", 2)],
     ["GROWN-UP: melt 1 insert into the little bump on each BACK wheel's rim (2 total).",
      "Stretch a stretchy printed tire over each of the four wheels, like putting a rubber band on a yo-yo.",
      "Work it around evenly until it sits flat in the groove all the way around."],
     "No tire bulges. All four look the same."),
    ("step_05_front_pods", "Bolt on the front pods", False, SCREWS["front_pods"],
     [("front_pod_left_v2", 2), ("px_insert", 2)],
     ["GROWN-UP: melt 1 insert into the end of each pod's peg (2 total).",
      "The two front pods have round pegs sticking out - those pegs are the front axles.",
      "Screw each pod to the tray through its little foot tabs, 2 screws each, pegs pointing OUT."],
     "Both pegs point straight out to the sides."),
    ("step_06_wheels_on", "Put the wheels on", False,
     SCREWS["rear_wheel_clamps"] + SCREWS["front_axle_retainers"],
     [("rear_wheel_v2", 2), ("front_wheel_v2", 2), ("printed_washer_v2", 2)],
     ["BACK wheels: the hole has a flat side, and so does the motor shaft. Line the flats up, push the wheel on, then tighten the one clamp screw on the wheel's rim.",
      "FRONT wheels: slide onto the pegs - they should spin freely. Put a printed washer on, then a screw into the end of the peg to keep the wheel from sliding off.",
      "Don't overtighten the front screws: the wheels must still spin.",
      "You printed extra washers - drop the leftovers in your spares box."],
     "Back wheels should NOT spin freely by hand (the motor holds them). Front wheels spin freely."),
    ("step_07_tower", "Build the brain tower (the controller tower)", False, SCREWS["controller_tower_base"],
     [("controller_tower_v2", 1), ("px_mdds10", 1)],
     ["Set the tower over the front-left of the tray - its screw holes match the four inserts.",
      "Drive 4 screws down through the base tabs.",
      "Rest the purple motor board on the four little posts, its green terminal blocks facing the LEFT side of the robot."],
     "The board sits level on all four posts, terminals facing left."),
    ("step_08_pi", "Add the computer", False, 0,
     [("px_pi", 1)],
     ["The Raspberry Pi lies flat on the tower's top shelf frame.",
      "Its USB ports face the BACK of the robot so the cables can reach.",
      "Don't screw anything - the shelf pocket holds it, and the head's cable will come down to it later."],
     "The Pi sits in its pocket, ports facing backward."),
    ("step_09_battery", "Strap in the battery", False, SCREWS["battery_clamp"],
     [("battery_pad_frame_v2", 1), ("px_battery", 1), ("battery_clamp_v2", 1)],
     ["Lay the soft TPU pad frame onto the four pads behind the tower.",
      "Set the battery on it, wires pointing at the BACK of the robot.",
      "Bridge the clamp bar across the battery onto the two posts and screw it down with 2 screws - firm, so the battery cannot slide."],
     "Grab the battery and try to wiggle it. It shouldn't move."),
    ("step_10_pico", "Add the safety helper", False, SCREWS["pico_clamp"],
     [("px_pico", 1), ("pico_clamp_v2", 1)],
     ["The tiny green Pico sits on its little posts to the right of the tower, USB plug facing RIGHT.",
      "Lay the small clamp bar across it and screw it down with 2 screws, gently - it's a small board."],
     "The Pico is held snug and its USB port is reachable."),
    ("step_11_relay", "Mount the power relay", True, 0,
     [("px_relay", 1)],
     ["GROWN-UP: the relay drops into its floor pocket on the left, behind the tower.",
      "Its metal bracket slots into the printed pocket; the terminals face UP so you can wire them later.",
      "No wires yet - all wiring happens in the wiring chapter at the back of this book."],
     "The relay clicks into its pocket and doesn't rattle."),
    ("step_12_deck", "Put on the power deck", False, SCREWS["deck_towers"],
     [("deck_v2", 1), ("px_fuse", 1), ("px_reg1", 2)],
     ["First hang the two small green regulator boards under the deck's RIGHT end (they clip under; wires come later).",
      "Lower the deck onto the four towers - the notch at the back-right corner goes around the battery wires.",
      "Drive 4 screws down into the tower tops.",
      "Set the black fuse box into its raised outline on the deck's right half, wire end hanging over the edge."],
     "The deck is level and the fuse box sits inside its printed fence."),
    ("step_13_shell", "Lower the body shell", True, SCREWS["shell_tray"],
     [("shell_v2", 1), ("px_insert", 14)],
     ["GROWN-UP FIRST: melt the shell's 14 inserts (4 corner lugs, 4 lid-ledge holes, 4 speaker posts, 2 sensor bosses).",
      "Two people make this easy: lower the big shell straight down over EVERYTHING.",
      "The wheel arches go around the wheels; the lip settles onto the tray edge.",
      "Flip-check the underside: drive 4 screws UP through the tray's corner holes into the shell's lugs."],
     "No gaps between shell and tray. The robot is now a box with wheels."),
    ("step_14_bumpers", "Feeler switches, then bumpers", False, 0,
     [("px_switch", 6), ("bumper_front_v2", 2)],
     ["Tip the robot gently onto its side. Click each of the six little feeler switches into its pocket under the tray edge - two front, two back, one each side. Their tiny buttons face OUT.",
      "Their wires tuck up inside for the wiring chapter.",
      "Stand the robot back up. The two soft bumper halves wrap around the bottom, one from the front, one from the back.",
      "They hug the body loosely on purpose - they squish in to press those feeler switches."],
     "Press any bumper edge gently: it moves a tiny bit, you hear a soft click, and it springs back."),
    ("step_15_panels", "Face and back panels (with the front eyes)", False, 0,
     [("fascia_v2", 1), ("px_tof_L", 2), ("rear_panel_v2", 1)],
     ["First press the two front distance boards into the pockets on the FACE panel's back - their little lenses peer through the two low holes.",
      "Click the FACE panel into the front opening.",
      "The dark BACK panel clicks into the back opening. Its two round holes are for the charger plug and the mute switch - the grown-up bolts those in with their own nuts during the wiring chapter."],
     "Both panels sit flush; two tiny lenses look out of the face."),
    ("step_16_speakers", "Speakers and distance eyes", False,
     SCREWS["speaker_clamps"] + SCREWS["tof_clamps"],
     [("px_speaker_L", 2), ("px_tof_L", 2), ("speaker_clamp_v2", 2), ("tof_clamp_v2", 2)],
     ["Reach in through the open top: rest a speaker on each side shelf, magnet side in, grille facing the wall.",
      "Lay a clamp bar across each speaker's top and screw into the two posts (2 screws per side) - the inserts went in with the shell step.",
      "Slide a little blue distance board behind each side window, then its clamp bar and 1 screw."],
     "Speakers can't rattle; the blue boards peek through their side windows."),
    ("step_17_lid", "The lid and the BIG RED BUTTON", True,
     SCREWS["mic_cradle"],
     [("lid_v2", 1), ("px_estop_cap", 1), ("px_mic", 1), ("mic_cradle_v2", 1), ("px_insert", 2)],
     ["GROWN-UP: melt the lid's 2 mic-boss inserts, then drop the red emergency-stop through the lid's round hole and spin its nut on underneath - the lid IS its mounting panel, and the printed ring under the lid makes it strong.",
      "Set the round microphone under the lid's slotted area and screw its ring cradle to the two bosses (2 screws).",
      "Rest the lid in its ledge - DON'T screw it yet. The neck, the head, and all the grown-up wiring still need the inside. Its 4 corner screws are the very last thing in this book."],
     "Slap test: the red button clicks down hard and twists to release."),
    ("step_18_neck", "Grow the neck", False, 0,
     [("neck_v2", 1), ("bayonet_collar_v2", 1), ("px_servo", 1)],
     ["Feed the neck tube down through the lid's front hole.",
      "From inside, twist the bayonet collar onto the neck's bottom - a quarter turn locks it, like a camera lens.",
      "The neck servo sits in the collar's cradle underneath (its wire joins the wiring chapter)."],
     "The neck turns smoothly by hand and cannot pull up and out."),
    ("step_19_head", "Build the head", False, 1,
     [("head_shell_v2", 1), ("yoke_v2", 1), ("head_pan_plate_v2", 1), ("px_camera", 1), ("px_servo", 1), ("tilt_bushing_v2", 1), ("px_insert", 1)],
     ["Grown-up melts the last insert (the tilt-pivot side), then: screw the yoke's ring onto the top of the neck.",
      "Slide the camera into the pocket behind the face opening, lens forward; its flat ribbon cable runs down through the hollow neck to the Pi.",
      "Lower the head shell over the yoke: one side takes the tilt servo, the other side gets the little bushing and 1 pivot screw.",
      "Close the underside with the pan plate."],
     "The head nods up-down and the neck turns left-right, smoothly."),
    ("step_20_face", "Give it a face", False, 0,
     [("head_faceplate_v2", 1), ("eye_diffuser_bar_v2", 1), ("status_diffuser_bar_v2", 1)],
     ["Clip the lime eye bar behind the face panel's eye slots (glow boards ride behind it).",
      "Press the face panel into its recess: camera hole over the lens.",
      "The second lime bar clips behind the front body panel's light slots - each glow board rides in the pocket behind its bar.",
      "Leave the 4 glow boards in their bag for now - the grown-up seats them in those pockets during the wiring chapter."],
     "Rover Bean is looking at you. Say hi."),
]

WIRE_RULES = [
    "This whole chapter is grown-up work. The builder can watch and hand you zip ties.",
    "The battery stays OUT of the robot until every wire is checked against these maps.",
    "Use wire colors: RED = battery 12 V, YELLOW = switched motor 12 V, BLUE = 5 V, GREEN = 6 V, BLACK = ground, WHITE = signals.",
    "Crimp or solder every joint; no bare twists. Label both ends of every wire with tape.",
    "Fuses go in LAST, after a meter check - the sizes are on the shopping page (2-3 A branches, 5 A motor, 7.5 A feeder).",
    "The robot must FAIL STOPPED: if any of this feels wrong, it stays off.",
]
POWER_MAP = [
    ("Battery +12 V", "feeder fuse (near battery)", "Blue Sea fuse block IN"),
    ("Fuse branch 1", "D24V90F5 regulator", "5 V to the Raspberry Pi"),
    ("Fuse branch 2", "D36V50F6 regulator", "6 V to both neck servos"),
    ("Fuse branch 3", "mute switch common", "mic USB power OR red mute ring"),
    ("Fuse branch 4", "5 V accessories", "NeoPixel eyes + status lights"),
    ("Battery +12 V", "motor fuse -> relay contacts", "MDDS10 motor board power"),
    ("Relay coil 12 V", "through BOTH red-button NC contacts", "coil ground via Pico enable"),
    ("Charger EN2 pins 1+2", "direct to battery charge lead", "pin 3 = charger-present to Pico"),
]
SIGNAL_MAP = [
    ("Raspberry Pi", "MDDS10", "serial motor commands (through the Pico's watchful eye)"),
    ("Raspberry Pi", "Pico 2", "USB: heartbeat + status; Pico can always stop motors"),
    ("Motor encoders (6 wires each)", "Pico 2", "wheel speed feedback"),
    ("Bumper switches x6", "Pico 2", "any press = stop, instantly, no software needed"),
    ("ToF boards x4", "Raspberry Pi", "I2C daisy chain (STEMMA cables)"),
    ("NeoPixels x4", "Raspberry Pi", "one data line, chained eye->eye->status->status"),
    ("Camera", "Raspberry Pi", "flat FPC ribbon down the hollow neck"),
    ("Servos x2", "Raspberry Pi", "PWM signal wires (power from the 6 V rail)"),
    ("Mic array", "Raspberry Pi", "USB (its 5 V passes through the mute switch)"),
    ("Pi I2S pins", "MAX98357A amps", "digital sound out; the amps zip-tie beside each speaker (a future version adds printed pockets)"),
]


# ---------------------------------------------------------------------------
# HTML
# ---------------------------------------------------------------------------
def esc(s):
    return html.escape(str(s), quote=False)


def img_uri(path: Path) -> str:
    return path.resolve().as_uri()


CSS = """
* { margin: 0; padding: 0; box-sizing: border-box; }
:root {
  --cream:#F6F0E2; --paper:#FBF7EC; --teal:#0B6E84; --teal-dk:#07515f;
  --dark:#1F2023; --red:#C4230F; --gold:#C79A3B; --chip:#EAE2CE; --lime:#B9E44A;
}
@page { size: 11in 8.5in; margin: 0; }
body { font-family: "Helvetica Neue", Helvetica, Arial, sans-serif; color: var(--dark); }
section.page { width: 11in; height: 8.5in; page-break-after: always; position: relative;
  overflow: hidden; background: var(--paper); padding: .45in .55in; display: flex; flex-direction: column; }
h1 { font-size: 58px; color: var(--teal); letter-spacing: -1px; line-height: .95; }
h2 { font-size: 30px; color: var(--teal); margin-bottom: .18in; }
h3 { font-size: 16px; color: var(--teal-dk); margin: .12in 0 .06in; }
p, li, td, th { font-size: 12.5px; line-height: 1.45; }
.badges { display: flex; gap: .12in; margin: .18in 0; }
.badge { background: var(--teal); color: #fff; font-weight: 700; font-size: 12px;
  padding: .06in .14in; border-radius: .17in; }
.badge.red { background: var(--red); }
.badge.gold { background: var(--gold); }
.grownup { position: absolute; top: .42in; right: .55in; background: var(--red); color: #fff;
  font-weight: 800; font-size: 13px; padding: .07in .16in; border-radius: .17in; }
table { border-collapse: collapse; width: 100%; }
th { text-align: left; color: #fff; background: var(--teal); padding: .05in .09in; font-size: 12px; }
td { padding: .045in .09in; border-bottom: 1px solid #d8cfba; vertical-align: top; }
tr:nth-child(even) td { background: #f2ecdc; }
.stepnum { width: .62in; height: .62in; border-radius: 50%; background: var(--teal); color: #fff;
  display: flex; align-items: center; justify-content: center; font-size: 30px; font-weight: 800; }
.stepnum.red { background: var(--red); }
.stephead { display: flex; align-items: center; gap: .18in; }
.stephead h2 { margin: 0; font-size: 26px; color: var(--dark); }
.strip { background: var(--chip); border-radius: .12in; display: flex; align-items: center;
  flex-wrap: wrap; gap: .22in; padding: .08in .18in; margin: .12in 0; min-height: 1.05in; }
.strip .cell { display: flex; align-items: center; gap: .05in; }
.strip img { width: .9in; height: .9in; object-fit: contain; }
.strip b { font-size: 15px; }
.strip small { font-size: 9px; display:block; color:#555; }
.strip.dense { gap: .1in; padding: .08in .12in; }
.strip.dense img { width: .62in; height: .62in; }
.strip.dense b { font-size: 12px; }
.strip.dense small { font-size: 8px; }
.stepbody { display: flex; gap: .3in; flex: 1; min-height: 0; }
.stepbody .imgwrap { width: 6.1in; height: 4.9in; border-radius: .14in; overflow: hidden; position: relative; flex: none; }
.stepbody .imgwrap img { width: 118%; height: 118%; object-fit: cover; object-position: 50% 55%; margin: -4.5% 0 0 -9%; }
.frontchip { position: absolute; left: .12in; bottom: .12in; background: rgba(31,32,35,.82); color: #fff;
  font-weight: 800; font-size: 11px; padding: .04in .1in; border-radius: .1in; }
.instr { flex: 1; display: flex; flex-direction: column; }
.instr ol { margin-left: .22in; }
.instr li { font-size: 13.5px; margin-bottom: .1in; }
.check { margin-top: auto; background: var(--lime); border-radius: .1in; padding: .09in .14in;
  font-weight: 700; font-size: 12.5px; }
.check::before { content: "CHECK  "; color: var(--teal-dk); }
.cols { display: flex; gap: .35in; }
.cols > div { flex: 1; }
.footer { position: absolute; bottom: .22in; left: .55in; right: .55in; display: flex;
  justify-content: space-between; font-size: 9px; color: #7a7261; }
.rule { border-left: 4px solid var(--red); padding: .04in .12in; margin-bottom: .09in; font-size: 12px; }
.hero { position: absolute; right: 0; top: 0; width: 6in; height: 7.95in; object-fit: cover; object-position: 62% 22%; }
.gridwrap { display: grid; grid-template-columns: repeat(8, 1fr); gap: .08in; }
.gcell { text-align: center; }
.gcell img { width: 1.05in; height: .95in; object-fit: contain; }
.gcell div { font-size: 9.5px; font-weight: 700; }
svg text { font-family: Helvetica, Arial, sans-serif; }
"""


def page(body, footer_left="CODEX ROVER BEAN - Builder's Book", num=None, total=None, grownup=False):
    gu = '<div class="grownup">GROWN-UP STEP</div>' if grownup else ""
    ft = f'<div class="footer"><span>{footer_left}</span><span>{"" if num is None else f"page {num} / {total}"}</span></div>'
    return f'<section class="page">{gu}{body}{ft}</section>'


def build_pages():
    pages = []

    # Cover
    pages.append(f"""
      <img class="hero" src="{img_uri(IMG / 'codex_robot_body_v2_assembled.png')}">
      <div style="width:4.4in; padding-top:.7in;">
        <h1>CODEX<br>ROVER BEAN</h1>
        <p style="font-size:19px; font-weight:700; margin-top:.15in;">The Robot Body Builder's Book</p>
        <p style="font-size:13.5px; margin-top:.1in;">Print it. Screw it together. Meet your robot.<br>
        Everything you need is in this book and one Bambu Studio file.</p>
        <div class="badges" style="flex-wrap:wrap;">
          <span class="badge">AGES 10+</span><span class="badge">{sum(pl["part_count"] for pl in PLATES["plates"])} PIECES TO PRINT</span>
          <span class="badge">{len(PLATES["plates"])} PLATES</span><span class="badge">1 HEX KEY</span>
          <span class="badge red">GROWN-UP NEEDED: SOLDERING &amp; WIRING</span>
        </div>
        <p style="font-size:11px; margin-top:.28in; color:#6d6552;">Chapters: 1 Shop &nbsp;-&nbsp; 2 Print &nbsp;-&nbsp; 3 Build &nbsp;-&nbsp; 4 Wire (grown-up) &nbsp;-&nbsp; 5 Check &amp; play</p>
      </div>""")

    # How to read
    pages.append(f"""
      <h2>How this book works</h2>
      <div class="cols">
        <div>
          <h3>The pictures do the talking</h3>
          <p>Every build step shows the robot so far. On most pictures the NEW parts float just off their spot
          (early steps show them already home). The little dark tag with the arrow points toward the robot's FACE.
          Match the picture, then read the numbered lines if you want words too.</p>
          <h3>The parts strip</h3>
          <p>The tan strip at the top of each step shows exactly which parts and how many screws you need
          <b>before you start</b>. Lay them out like a cooking show.</p>
          <h3>The green CHECK bar</h3>
          <p>Do the little test at the bottom of each step before moving on. If the check fails, fix it now -
          later steps cover things up.</p>
        </div>
        <div>
          <h3>Red circles mean grown-up</h3>
          <p>Steps with a <span style="color:var(--red); font-weight:800;">red number</span> use the soldering
          iron or touch wires. A grown-up does those; you can watch and help.</p>
          <h3>One screw. One key.</h3>
          <p>Every screw in this robot is the same M3 x 8 screw, and one 2.5 mm hex key turns them all.
          "Snug" means: stop when it stops, then an eighth of a turn. Plastic hates gorillas.</p>
          <h3>Front and back</h3>
          <p>The FRONT is where the face panel and head look. The BACK has the charging plug, the mute switch,
          and the motor wheels. Left and right are the robot's left and right, not yours.</p>
        </div>
      </div>""")

    # Shopping 1: filament + fasteners + tools
    fil = "".join(f"<tr><td><b>{esc(a)}</b></td><td>{esc(b)}</td><td>{esc(c)}</td></tr>" for a, b, c in SHOP_FILAMENT)
    fas = "".join(f"<tr><td><b>{esc(a)}</b></td><td>{esc(b)}</td><td>{esc(c)}</td></tr>" for a, b, c in SHOP_FASTENERS)
    tools = "".join(f"<tr><td><b>{esc(a)}</b></td><td>{esc(b)}</td></tr>" for a, b in SHOP_TOOLS)
    pages.append(f"""
      <h2>Chapter 1 - Go shopping: plastic, screws, tools</h2>
      <div class="cols"><div>
        <h3>Filament (for the printer)</h3>
        <table><tr><th>Filament</th><th>How much</th><th>What it becomes</th></tr>{fil}</table>
        <h3 style="margin-top:.18in;">The only two fastener packs</h3>
        <table><tr><th>Fastener</th><th>Buy</th><th>Why</th></tr>{fas}</table>
      </div><div>
        <h3>Tools</h3>
        <table><tr><th>Tool</th><th>Job</th></tr>{tools}</table>
        <div style="margin-top:.2in; display:flex; gap:.3in; align-items:center;">
          <img src="{img_uri(GUIDE_IMG / 'thumb_px_screw.png')}" style="width:1.3in;">
          <img src="{img_uri(GUIDE_IMG / 'thumb_px_insert.png')}" style="width:1.3in;">
          <p style="font-size:12px;">This screw and this brass insert are the only fasteners you'll buy for the
          whole robot. When a step says "2 screws," it always means these.</p>
        </div>
      </div></div>""")

    # Shopping 2: electronics (split across two pages so nothing clips).
    half = (len(SHOP_ELECTRONICS) + 1) // 2
    for part_i, chunk in enumerate((SHOP_ELECTRONICS[:half], SHOP_ELECTRONICS[half:]), start=1):
        elec = "".join(f"<tr><td><b>{esc(a)}</b></td><td style='text-align:center'>{esc(b)}</td><td>{esc(c)}</td></tr>"
                       for a, b, c in chunk)
        intro = ("Every item is a normal buy-one online part in the US. A grown-up orders these. "
                 "Fuse sizes and wire gauges are right here in the list; the wiring chapter shows where each goes."
                 if part_i == 1 else "The rest of the electronics box:")
        pages.append(f"""
          <h2>Chapter 1 - Go shopping: the electronics box ({part_i} of 2)</h2>
          <p style="margin-bottom:.1in;">{intro}</p>
          <table style="font-size:11.5px;"><tr><th>Part</th><th>Qty</th><th>What it does</th></tr>{elec}</table>""")

    # Print chapter: how to print
    tips = "".join(f"<h3>{esc(t)}</h3><p>{d}</p>" for t, d in PRINT_TIPS)
    pages.append(f"""
      <h2>Chapter 2 - Print it with Bambu Studio</h2>
      <div class="cols">
        <div>{tips}</div>
        <div>
          <img src="{img_uri(IMG / 'codex_robot_body_v2_p1s_plates.png')}"
               style="width:100%; border-radius:.12in;">
          <p style="font-size:10.5px; margin-top:.06in;">All {N_PLATES} plates, exactly as they open in Bambu Studio.</p>
        </div>
      </div>""")

    # Plate table
    rows = ""
    for p in PLATES["plates"]:
        parts_txt = esc(", ".join(pp["name"].replace("_v2", "").replace("_i", " #")
                                  .replace("_", " ").replace("fascia", "face panel")
                                  for pp in p["parts"]))
        if "printed washer" in parts_txt:
            parts_txt += " <i>(the robot uses 2 washers - the rest are spares)</i>"
        rows += (
            f"<tr><td style='text-align:center'><b>{p['plate_number']}</b></td>"
            f"<td><span style='display:inline-block;width:.14in;height:.14in;border-radius:50%;"
            f"background:{p['color_hex']};border:1px solid #999;'></span> {esc(p['name'])}</td>"
            f"<td style='text-align:center'>{p['part_count']}</td>"
            f"<td>{parts_txt}</td></tr>")
    pages.append(f"""
      <h2>Chapter 2 - The {N_PLATES} plates, in printing order</h2>
      <table style="font-size:10.5px;"><tr><th>#</th><th>Plate (load this filament)</th><th>Parts</th><th>What's on it</th></tr>{rows}</table>
      <p style="margin-top:.1in; font-size:11px;"><b>Tip:</b> print plates 1-5 (cream) back to back, then change color once per group. Keep every part in a labeled box - the next chapter uses them in order.</p>""")

    # Coupons
    crows = "".join(f"<tr><td><b>{esc(k.replace('coupon_', '').replace('_', ' '))}</b></td>"
                    f"<td>{esc(v['material'])}</td><td>{esc(COUPON_KID_NOTES.get(k, v['note']))}</td></tr>"
                    for k, v in COUPONS.items())
    pages.append(f"""
      <h2>Chapter 2 - Print the little test parts FIRST</h2>
      <p style="margin-bottom:.08in;">Before the big plates, ask your grown-up to print the little TEST PARTS
      that come with the project (the <b>coupons</b> folder next to the Bambu file). They make sure your printer's
      holes, snaps, and fits are dialed in - like tasting the batter before baking the whole cake. Each one has a
      simple pass test:</p>
      <table style="font-size:10.5px;"><tr><th>Test part</th><th>Filament</th><th>What it proves</th></tr>{crows}</table>""")

    # Chapter 3 divider.
    pages.append(f"""
      <img class="hero" src="{img_uri(IMG / 'codex_robot_body_v2_chassis.png')}">
      <div style="width:4.3in; padding-top:1.1in;">
        <h1 style="font-size:44px;">Chapter 3<br>Build it</h1>
        <p style="font-size:14px; margin-top:.2in;">Twenty steps. Lay out the parts from each step's tan strip
        before you start, match the big picture, then run the green CHECK.</p>
        <p style="font-size:13px; margin-top:.15in;">The little <b>FRONT</b> tag on every picture points at the
        robot's face, so left and right never get confusing.</p>
        <p style="font-size:13px; margin-top:.15in; color:var(--red); font-weight:700;">Red-number steps need a grown-up.</p>
      </div>""")

    # Steps
    for i, (img_name, title, grownup, screws, items, subs, check) in enumerate(STEPS, start=1):
        label = FRONT_LABEL.get(img_name, "&#8601; FRONT")
        front_chip = f'<div class="frontchip">{label}</div>' if label else ""
        cells = "".join(
            f'<div class="cell"><img src="{img_uri(GUIDE_IMG / ("thumb_" + t + ".png"))}"><b>x{n}</b></div>'
            for t, n in items)
        if screws:
            cells += (f'<div class="cell"><img src="{img_uri(GUIDE_IMG / "thumb_px_screw.png")}">'
                      f'<b>x{screws}<small>M3 screw{"s" if screws != 1 else ""}</small></b></div>')
        strip_cls = "strip dense" if len(items) + (1 if screws else 0) >= 7 else "strip"
        lis = "".join(f"<li>{esc(s)}</li>" for s in subs)
        pages.append(f"""
          <div class="stephead"><div class="stepnum{' red' if grownup else ''}">{i}</div><h2>{esc(title)}</h2></div>
          <div class="{strip_cls}">{cells}</div>
          <div class="stepbody">
            <div class="imgwrap"><img src="{img_uri(GUIDE_IMG / (img_name + '.png'))}">
              {front_chip}</div>
            <div class="instr"><ol>{lis}</ol><div class="check">{esc(check)}</div></div>
          </div>""")
        if grownup:
            pages[-1] = pages[-1]  # grown-up flag handled by page()

    # Electronics orientation page
    pages.append(f"""
      <h2>Chapter 4 - Where every electronic part lives</h2>
      <div class="cols">
        <div><img src="{img_uri(IMG / 'codex_robot_body_v2_chassis.png')}" style="width:100%; border-radius:.12in;"></div>
        <div>
          <table style="font-size:11px;">
            <tr><th>Part</th><th>Home</th><th>Faces</th></tr>
            <tr><td><b>MDDS10 motor board</b></td><td>tower posts, front-left</td><td>terminals LEFT</td></tr>
            <tr><td><b>Raspberry Pi 5</b></td><td>tower top shelf</td><td>USB ports BACK</td></tr>
            <tr><td><b>Pico 2</b></td><td>floor, right of tower</td><td>USB RIGHT, pins UP</td></tr>
            <tr><td><b>Battery</b></td><td>middle-back floor</td><td>wires BACK</td></tr>
            <tr><td><b>Relay</b></td><td>floor pocket, left</td><td>terminals UP</td></tr>
            <tr><td><b>Fuse block</b></td><td>deck, right half</td><td>wire exit RIGHT edge</td></tr>
            <tr><td><b>Regulators (5 V + 6 V)</b></td><td>hang UNDER deck, right end</td><td>6 V wire exit LEFT</td></tr>
            <tr><td><b>Big red button</b></td><td>through the lid</td><td>UP (slap it!)</td></tr>
            <tr><td><b>Mic array</b></td><td>under the lid slots</td><td>UP</td></tr>
            <tr><td><b>Speakers</b></td><td>side shelves</td><td>grilles OUT</td></tr>
            <tr><td><b>ToF distance boards</b></td><td>2 behind face, 2 side windows</td><td>lenses OUT</td></tr>
            <tr><td><b>Bumper feeler switches x6</b></td><td>pockets under the tray edge</td><td>buttons OUT</td></tr>
            <tr><td><b>Charger inlet + mute</b></td><td>back panel holes</td><td>BACK</td></tr>
            <tr><td><b>Camera</b></td><td>head, pocket behind the face opening</td><td>lens FRONT</td></tr>
            <tr><td><b>Pan + tilt servos</b></td><td>pan inside the neck, tilt in the head's side</td><td>pan shaft UP, tilt shaft SIDEWAYS</td></tr>
            <tr><td><b>Glow boards x4</b></td><td>pockets behind the eye + status bars</td><td>lights OUT</td></tr>
          </table>
          <p style="font-size:10.5px; margin-top:.08in;">The two speaker amp boards (MAX98357A) zip-tie beside
          their speakers - a future version of the body adds printed pockets for them.</p>
        </div>
      </div>""")

    # Wiring rules + power map
    rules = "".join(f'<div class="rule">{esc(r)}</div>' for r in WIRE_RULES)
    prow = "".join(f"<tr><td>{esc(a)}</td><td>{esc(b)}</td><td>{esc(c)}</td></tr>" for a, b, c in POWER_MAP)
    pages.append(f"""
      <h2 style="color:var(--red);">Chapter 4 - Grown-up wiring rules</h2>
      {rules}
      <h3 style="margin-top:.14in;">The power map (every 12 V wire)</h3>
      <table style="font-size:11px;"><tr><th>From</th><th>Through</th><th>To</th></tr>{prow}</table>""")

    # SVG power diagram
    pages.append(f"""
      <h2 style="color:var(--red);">Chapter 4 - Power, as a picture</h2>
      <svg viewBox="0 0 1000 560" style="width:100%; height:6.6in;">
        <defs><marker id="a" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
          <path d="M0,0 L6,3 L0,6 z" fill="#555"/></marker></defs>
        <rect x="20" y="230" width="150" height="90" rx="10" fill="#26438f"/>
        <text x="95" y="270" fill="#fff" font-size="20" font-weight="bold" text-anchor="middle">BATTERY</text>
        <text x="95" y="295" fill="#cfe" font-size="14" text-anchor="middle">12 V LiFePO4</text>
        <rect x="240" y="150" width="120" height="60" rx="8" fill="#C79A3B"/>
        <text x="300" y="186" font-size="15" font-weight="bold" text-anchor="middle" fill="#fff">FEEDER FUSE</text>
        <rect x="430" y="130" width="170" height="100" rx="8" fill="#1F2023"/>
        <text x="515" y="170" fill="#fff" font-size="16" font-weight="bold" text-anchor="middle">FUSE BLOCK</text>
        <text x="515" y="192" fill="#ccc" font-size="12" text-anchor="middle">4 fused branches</text>
        <rect x="700" y="40" width="180" height="52" rx="8" fill="#1b7a3d"/>
        <text x="790" y="72" fill="#fff" font-size="14" font-weight="bold" text-anchor="middle">5 V reg -> RASPBERRY PI</text>
        <rect x="700" y="110" width="180" height="52" rx="8" fill="#1b7a3d"/>
        <text x="790" y="142" fill="#fff" font-size="14" font-weight="bold" text-anchor="middle">6 V reg -> NECK SERVOS</text>
        <rect x="700" y="180" width="180" height="52" rx="8" fill="#444"/>
        <text x="790" y="205" fill="#fff" font-size="13" font-weight="bold" text-anchor="middle">MUTE SWITCH -> MIC</text>
        <text x="790" y="222" fill="#f88" font-size="11" text-anchor="middle">or red mute ring</text>
        <rect x="700" y="250" width="180" height="52" rx="8" fill="#5c7a1b"/>
        <text x="790" y="282" fill="#fff" font-size="14" font-weight="bold" text-anchor="middle">GLOW LIGHTS (5 V)</text>
        <rect x="240" y="360" width="120" height="60" rx="8" fill="#C79A3B"/>
        <text x="300" y="396" font-size="15" font-weight="bold" text-anchor="middle" fill="#fff">MOTOR FUSE</text>
        <rect x="430" y="350" width="150" height="80" rx="8" fill="#333"/>
        <text x="505" y="384" fill="#fff" font-size="16" font-weight="bold" text-anchor="middle">RELAY</text>
        <text x="505" y="406" fill="#fbb" font-size="11" text-anchor="middle">coil runs through the</text>
        <text x="505" y="420" fill="#fbb" font-size="11" text-anchor="middle">RED BUTTON + Pico OK</text>
        <rect x="660" y="350" width="150" height="80" rx="8" fill="#5e2b7a"/>
        <text x="735" y="384" fill="#fff" font-size="15" font-weight="bold" text-anchor="middle">MDDS10</text>
        <text x="735" y="406" fill="#dcf" font-size="12" text-anchor="middle">motor board</text>
        <rect x="860" y="340" width="110" height="44" rx="8" fill="#555"/>
        <text x="915" y="367" fill="#fff" font-size="13" font-weight="bold" text-anchor="middle">MOTOR L</text>
        <rect x="860" y="396" width="110" height="44" rx="8" fill="#555"/>
        <text x="915" y="423" fill="#fff" font-size="13" font-weight="bold" text-anchor="middle">MOTOR R</text>
        <rect x="20" y="440" width="220" height="70" rx="10" fill="#0B6E84"/>
        <text x="130" y="470" fill="#fff" font-size="14" font-weight="bold" text-anchor="middle">CHARGER PLUG (EN2)</text>
        <text x="130" y="492" fill="#cef" font-size="11" text-anchor="middle">pins 1+2 -> battery charge lead</text>
        <path d="M170,260 C210,260 210,180 240,180" stroke="#c00" stroke-width="5" fill="none" marker-end="url(#a)"/>
        <path d="M360,180 L430,180" stroke="#c00" stroke-width="5" fill="none" marker-end="url(#a)"/>
        <path d="M600,155 C650,155 650,66 700,66" stroke="#26f" stroke-width="4" fill="none" marker-end="url(#a)"/>
        <path d="M600,175 C650,175 650,136 700,136" stroke="#2a5" stroke-width="4" fill="none" marker-end="url(#a)"/>
        <path d="M600,195 C650,195 650,206 700,206" stroke="#26f" stroke-width="4" fill="none" marker-end="url(#a)"/>
        <path d="M600,215 C650,215 650,276 700,276" stroke="#26f" stroke-width="4" fill="none" marker-end="url(#a)"/>
        <path d="M170,300 C210,300 210,390 240,390" stroke="#c00" stroke-width="5" fill="none" marker-end="url(#a)"/>
        <path d="M360,390 L430,390" stroke="#dd0" stroke-width="5" fill="none" marker-end="url(#a)"/>
        <path d="M580,390 L660,390" stroke="#dd0" stroke-width="5" fill="none" marker-end="url(#a)"/>
        <path d="M810,368 L860,362" stroke="#dd0" stroke-width="4" fill="none" marker-end="url(#a)"/>
        <path d="M810,412 L860,418" stroke="#dd0" stroke-width="4" fill="none" marker-end="url(#a)"/>
        <path d="M130,440 C130,380 95,360 95,320" stroke="#26438f" stroke-width="4" fill="none" marker-end="url(#a)"/>
        <text x="300" y="140" font-size="12" fill="#555" text-anchor="middle">RED = always-hot 12 V</text>
        <text x="470" y="345" font-size="12" fill="#555">YELLOW = motor 12 V, dead unless relay says so</text>
      </svg>""")

    # Signal map
    srow = "".join(f"<tr><td>{esc(a)}</td><td>{esc(b)}</td><td>{esc(c)}</td></tr>" for a, b, c in SIGNAL_MAP)
    pages.append(f"""
      <h2 style="color:var(--red);">Chapter 4 - The signal map (thin wires)</h2>
      <table style="font-size:11.5px;"><tr><th>From</th><th>To</th><th>What travels</th></tr>{srow}</table>
      <h3 style="margin-top:.14in;">Cable neatness</h3>
      <p style="font-size:12px;">Quiet wires (signals, audio, sensors) ride the LEFT channel under the deck.
      Power wires ride the RIGHT channel. The camera ribbon goes up the little tunnel beside the neck servo,
      through the hollow neck, into the head. Zip-tie at every printed tie point; no wire may touch a wheel or the fan.</p>
      <h3>Before the battery goes in - the grown-up meter checklist</h3>
      <p style="font-size:12px;">No shorts first: beep-test + to - at the fuse block (no fuses in yet). Then:
      </p><ol style="font-size:12px; margin-left:.25in;">
      <li>Red button held down = relay coil circuit reads OPEN.</li>
      <li>Regulator outputs read 5.0-5.2 V and 6.0 V on the bench before their loads connect.</li>
      <li>Fuses go in smallest-first, one branch at a time (the sizes are on the shopping page).</li>
      <li>Charger plug in = motors will not run.</li>
      <li>Only then: drive the lid's 4 corner screws - the last 4 of the robot's 41. NOW it's closed for good.</li></ol>""")

    # Finish page
    pages.append(f"""
      <img class="hero" src="{img_uri(IMG / 'codex_robot_body_v2_assembled.png')}">
      <div style="width:4.4in; padding-top:.6in;">
        <h2 style="font-size:38px;">You built a robot!</h2>
        <p style="font-size:14px; margin-top:.1in;">High five, builder. Rover Bean's body is done.</p>
        <h3 style="margin-top:.25in;">Chapter 5 - Before it ever moves (grown-ups)</h3>
        <p style="font-size:12px;">Slap the red button while the wheels spin on blocks - everything must stop instantly.
        Press each bumper - stop. Unplug the Pi's heartbeat - stop. Plug in the charger - it refuses to drive.
        Only after every one of these passes does Rover Bean get floor time, supervised, at walking pace.</p>
        <h3 style="margin-top:.18in;">Load the brain (grown-up)</h3>
        <p style="font-size:12px;">Flash <b>Raspberry Pi OS</b> onto the microSD with Raspberry Pi Imager, then
        follow the README at <b>github.com/brianpattison/robot</b> to install the robot's programs on the Pi and
        the safety code on the Pico. The tests above only work once the brain is loaded.</p>
        <p style="font-size:12px; margin-top:.12in;">The robot's number one rule, forever:
        <b>when anything is wrong, it stops.</b></p>
        <p style="font-size:11px; margin-top:.3in; color:#6d6552;">Codex Rover Bean v2 - printed-only body -
        one screw, one key, zero supports.</p>
      </div>""")

    return pages


def check_images(pages):
    import re
    missing = []
    for pg in pages:
        for m in re.finditer(r'src="file://([^"]+)"', pg):
            from urllib.parse import unquote
            if not Path(unquote(m.group(1))).exists():
                missing.append(unquote(m.group(1)))
    if missing:
        raise SystemExit("MISSING GUIDE IMAGES:\n" + "\n".join(missing))


def main():
    HTML_OUT.parent.mkdir(parents=True, exist_ok=True)
    PDF_OUT.parent.mkdir(parents=True, exist_ok=True)
    pages = build_pages()
    check_images(pages)
    total = len(pages)
    grown_pages = {i for i, p in enumerate(pages, start=1) if 'stepnum red' in p or 'GROWN-UP' in p[:400]}
    body = "".join(
        page(p, num=i, total=total, grownup=(i in grown_pages))
        for i, p in enumerate(pages, start=1))
    HTML_OUT.write_text(f"<!doctype html><html><head><meta charset='utf-8'>"
                        f"<style>{CSS}</style></head><body>{body}</body></html>", encoding="utf-8")
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
