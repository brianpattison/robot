"""Box-level packing screen for the printed-only 238 x 220 body (D027).

STATUS: the D027 packing gate is OPEN. This screen is axis-aligned-box
feasibility evidence only; it cannot pass the gate. The gate requires the
v2 BREP packing model plus an inventory-driven production validator (see
docs/printed-only-simplification-plan.md, revised Phase 2).

Review history (all findings verified against the source before adoption):
- rev 1 reported a false FEASIBLE (hardcoded envelopes; omitted E-stop
  panel/backing, battery-lead corridor, AI-HAT reserve, Pi service, roof
  rollover, keepout-keepout checks; impossible MDDS10 orientation).
- rev 2 (layout v3) was rejected: mute depth is 26 + 16 = 42 mm, the fuse
  block's 22 mm wire service was absent, the MDDS10 10 mm airflow contract
  was violated by 5.8 mm, and the AI-HAT reserve is 96 x 74 x 22.
- rev 3 (layout v4) was rejected on datums and remaining envelopes: the
  tray top is Z=49 (body_bottom), NOT 49+8 — production helpers put the
  MDDS10 thermal ceiling at 86.275 (the old formula also double-counted
  the 1.57 PCB) and the pan-servo bottom at 131.6 (pan_servo_fit bbox),
  so v4's computed 144 mm height was wrong; the D24V90F5's two terminal
  corridors, the D36V50F6's wire corridor, the fuse corridor's full
  32.5 mm height, and the relay's full 52 x 22 bracket + body/terminal
  volume were missing; and the margin policy let allowlisted pairs hide
  true overlaps and ignored wall margins.
- rev 4 (layout v5, this file) uses verified datums (tray top 49; deck
  plate 102..106 = power_deck_z +/- 2; thermal ceiling 86.275; pan-servo
  drop bottom 131.6 at the v1 121 mm height, tracking body height),
  models every corridor above, and enforces: overlap is NEVER waivable
  outside a same-assembly group; sub-2 mm margins fail unless the exact
  box-name pair is an allowlisted support contact; items keep >= 2 mm to
  the interior walls; wheels stay >= 2 mm inside the shell length.

Height derivation (printed at runtime): thermal ceiling 86.275 + 4 shelf
+ 28 Pi clearance + 22 HAT reserve + 3 margin = 143.275 required
pan-servo drop bottom => +12 over the v1-derived 131.6 => 133 mm body
height. Note for Phase 2: stacking the full 28 Pi band under the HAT band
is deliberately conservative; the physical HAT sits ~17 mm above the Pi
PCB, so the real BREP stack with the HAT drawing may recover ~10 mm.

- rev 5 (v5.1): after the round-4 green light, the box-representable
  Phase-2 carry-ins were registered immediately: the Pico moved to the
  floor NE quadrant because its former NW-wing USB corridor intersected
  the front bay (USB service now faces east, SWD is top-access); the
  battery pack sits on modeled 3 mm cradle pads; the relay is split into
  exact bracket / body / terminal-service volumes. Height recovery from
  the real AI-HAT drawing stays a BREP-discovered bonus, never assumed.

Layout v5.1 (closes at box level; Brian approved the appearance direction
2026-07-16 — off-center E-stop, offset mic, slim vent, forward side
speakers, swapped rear connectors, taller body; height revised
144 -> 133 by the datum fix):
- Body 238 x 220 x 133. Front = -X. Axles X = -74/+74 (148 mm wheelbase).
- MDDS10 plate rotated, terminals NORTH; explicit 10 mm thermal volume;
  Pi 5 shelf at the thermal ceiling, ports east; 96 x 74 x 22 AI-HAT
  reserve above; Pico 2 on the floor NE quadrant with east USB corridor
  and top-access SWD service.
- Battery mid-rear on 3 mm pads (pack top 79); lead corridor ends X=113; riser rises
  through a deck notch to the EN2 inlet on the NORTH rear panel; mute
  SOUTH at its full 42 mm depth.
- Deck plate 102..106 at X 24..113.8: fuse block on its south half with
  the full-height wire corridor overhanging the deck edge; E-stop drops
  through the north half at (55, 52), entirely above the deck plane;
  both regulators hang under the deck east/center with their terminal
  and wire corridors modeled (D36 wire faces WEST); harness rails under
  the deck; relay on the floor at X -46..6, Y -90..-68, as separate
  52 x 22 bracket, 26 x 22 body, and terminal-service volumes.
- Roof: E-stop panel off-center rear-right, mic offset south (60, -25),
  vent slimmed to a south strip; speakers on the FORWARD side walls.
"""

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import robot_body as rb  # noqa: E402

P = rb.Params()

WALL = P.wall
BODY_L, BODY_W = 238.0, 220.0
IX, IY = BODY_L / 2 - WALL, BODY_W / 2 - WALL          # 115.8 / 106.8
RFX = BODY_L / 2 - P.body_edge_radius                  # 107.0 roof flat
RFY = BODY_W / 2 - P.body_edge_radius                  # 98.0
TRAY_TOP = P.body_bottom                               # 49 (verified: plate bottom 54 = 49 + 5 lift)

# Verified production datums.
MDDS_TOP = (rb.motor_controller_plate_top_z(P) + P.mdds10_standoff_height
            + P.mdds10_above_pcb)                      # 76.275 (above_pcb is from the mount plane)
THERM_TOP = MDDS_TOP + P.mdds10_airflow_height         # 86.275
SHELF0, SHELF1 = THERM_TOP, THERM_TOP + 4.0            # 86.275..90.275
PI_TOP = SHELF1 + P.pi_clearance_height                # 118.275
HAT_TOP = PI_TOP + 22.0                                # 140.275 (96 x 74 x 22 reserve)
MARGIN = 3.0
DROP_V1 = 131.6                                        # pan_servo_fit bbox min Z at v1's 121 height
DH = math.ceil(HAT_TOP + MARGIN - DROP_V1)             # 12 (computed, not chosen)
BODY_H = 121.0 + DH                                    # 133
Z_TOP = P.body_bottom + BODY_H                         # 182
Z_ROOF_IN = Z_TOP - WALL
DROP0 = DROP_V1 + DH                                   # 143.6
DECK0, DECK1 = P.power_deck_z - 2.0, P.power_deck_z + 2.0   # 102..106 (verified)

FAX, RAX = -74.0, 74.0
EST = (55.0, 52.0)
ER = P.estop_backing_outer_radius
MIC = (60.0, -25.0)
MR = (P.mic_array_diameter + 2 * P.mic_cradle_outer_margin) / 2
EB0 = Z_ROOF_IN - P.estop_body_depth                   # 130.1
ET0 = EB0 - P.estop_terminal_service_depth             # 110.1

boxes = []


def add(name, kind, group, x0, x1, y0, y1, z0, z1, mirror=False):
    """group: boxes of one physical assembly may interpenetrate by design."""
    g = group or name
    boxes.append((name, kind, g, x0, x1, y0, y1, z0, z1))
    if mirror:
        boxes.append((name + "~m", kind, g + "~m", x0, x1, -y1, -y0, z0, z1))


# ---- structure and purchased-part keepouts ----
add("front_bay", "keepout", "shellF", -IX, -104, -IY, IY, TRAY_TOP, Z_TOP)
add("rear_en2_N", "keepout", None, IX - 28, IX, 23, 47, 115, 145)
add("rear_mute_S", "keepout", None,
    IX - (P.mute_switch_body_depth + P.mute_switch_terminal_service_depth), IX,
    -47, -23, 115, 145)
add("front_arch", "keepout", "shellF", FAX - 43, FAX + 43, 96, IY, TRAY_TOP, 109, mirror=True)
add("rear_arch", "keepout", "shellR", RAX - 43, IX, 96, IY, TRAY_TOP, 109, mirror=True)
add("front_pod", "keepout", "shellF", FAX - 22, FAX + 22, 86, IY, TRAY_TOP, 95, mirror=True)
add("motor", "keepout", "shellR", RAX - 12.5, RAX + 12.5,
    P.motor_face_y - P.motor_body_length, IY, 53.5, 78.5, mirror=True)
add("neck_drop", "keepout", "head", P.neck_x - 26, P.neck_x + 26, -26, 26, DROP0, Z_TOP)
add("head_roof", "keepout", "head", P.head_center_x - 46, P.head_center_x + 46, -70, 70, Z_TOP - 10, Z_TOP)
add("neck_collar", "keepout", "head", P.neck_x - 30, P.neck_x + 30, -30, 30, Z_TOP - 8, Z_TOP)
add("estop_panel", "keepout", "estop", EST[0] - ER, EST[0] + ER, EST[1] - ER, EST[1] + ER, Z_TOP - 20, Z_TOP)
add("estop_body", "keepout", "estop", EST[0] - 20, EST[0] + 20, EST[1] - 20, EST[1] + 20, EB0, Z_TOP)
add("estop_term", "keepout", "estop", EST[0] - 20, EST[0] + 20, EST[1] - 20, EST[1] + 20, ET0, EB0)
add("mic", "keepout", None, MIC[0] - MR, MIC[0] + MR, MIC[1] - MR, MIC[1] + MR, Z_TOP - 20, Z_TOP)
add("vent", "keepout", None, 30, 90, -96, -65, Z_TOP - 10, Z_TOP)
add("speaker", "keepout", None, -48, 22, 76, 106, 115, 145, mirror=True)
add("mdds10_thermal", "keepout", "mddsT", -101, -34, -50.5, 50.5, MDDS_TOP, THERM_TOP)

# ---- placed items ----
add("mdds10", "item", "mdds", -104, -30, -62, 62, TRAY_TOP, MDDS_TOP)
add("mdds10_svc", "service", "mdds", -89, -45, 62, 84, TRAY_TOP + 3, MDDS_TOP)
add("pi_shelf", "item", "pi", -101, -5, -34, 34, SHELF0, PI_TOP)
add("pi_port_svc", "service", "pi", -5, 19, -30, 30, SHELF1, PI_TOP)
add("ai_hat2", "item", "pi", -101, -5, -37, 37, PI_TOP, HAT_TOP)
add("pico_floor", "item", "pico", -28, 34, 47, 80, TRAY_TOP, 63)
add("pico_usb_svc", "service", "pico", 34, 54, 58.5, 68.5, TRAY_TOP, 63)
add("pico_swd_svc", "service", "pico", -26, -6, 52, 75, 63, 80)
add("bat_main", "item", "bat", -28, 59.5, -44, 44, TRAY_TOP, 79)   # pack on 3 mm pads
add("bat_rear", "item", "bat", 59.5, 89, -39.5, 39.5, TRAY_TOP, 79)
add("bat_leads", "service", "bat", 85, 113, -27, 27, 65, 79)
add("riser", "service", "bat", 100, 113, 25, 45, 65, 115)
add("deck_mid", "item", "deck", 24, 113.8, -67, 23, DECK0, DECK1)
add("deck_n2", "item", "deck", 24, 98, 23, 47, DECK0, DECK1)
add("deck_n1", "item", "deck", 24, 113.8, 47, 67, DECK0, DECK1)
add("fuse5045", "item", "fuse", 24, 24 + P.power_distribution_width,
    -67, -67 + P.power_distribution_length, DECK1, DECK1 + P.power_distribution_height)
add("fuse_wire_svc", "service", "fuse", 24, 24 + P.power_distribution_width,
    -67 - P.power_distribution_wire_service_length, -67, DECK1, DECK1 + P.power_distribution_height)
add("relay_bracket", "item", "relay", -46, -46 + P.motor_cutoff_bracket_length,
    -90, -90 + P.motor_cutoff_bracket_width, TRAY_TOP, 51)
add("relay_body", "item", "relay", -36, -36 + P.motor_cutoff_body_length,
    -90, -90 + P.motor_cutoff_body_width, 51, 51 + P.motor_cutoff_body_height)
add("relay_term_svc", "service", "relay", -36, -36 + P.motor_cutoff_body_length,
    -90, -90 + P.motor_cutoff_body_width, 76, 76 + P.motor_cutoff_terminal_service_height)
add("regD24_under", "item", "regD24", 92, 92 + P.pi_regulator_width,
    -50, -50 + P.pi_regulator_length, 94, DECK0)
add("regD24_term_S", "service", "regD24", 94, 110, -60, -50, 90, DECK0)
add("regD24_term_N", "service", "regD24", 94, 110, -9.4, 0.6, 90, DECK0)
add("regD36_under", "item", "regD36", 60, 60 + P.servo_regulator_length,
    -6, -6 + P.servo_regulator_width, 92.5, DECK0)
add("regD36_wire_W", "service", "regD36", 60 - P.servo_regulator_wire_service_length, 60,
    -2, 20, 90, DECK0)
add("rail_L", "item", None, 26, 90, -60, -46, 96, DECK0)
add("rail_R", "item", None, 26, 96, 41, 55, 96, DECK0)

# Margin-waiver allowlist: EXACT box-name pairs for intended support or
# abutment contacts. Overlap is never waived by this list.
ALLOWED_TOUCH = {
    frozenset(("fuse5045", "deck_mid")), frozenset(("fuse5045", "deck_n2")),
    frozenset(("fuse_wire_svc", "deck_mid")),
    frozenset(("regD24_under", "deck_mid")), frozenset(("regD24_term_S", "deck_mid")),
    frozenset(("regD24_term_N", "deck_mid")), frozenset(("regD36_under", "deck_mid")),
    frozenset(("regD36_wire_W", "deck_mid")),
    frozenset(("rail_L", "deck_mid")), frozenset(("rail_R", "deck_mid")),
    frozenset(("rail_R", "deck_n2")), frozenset(("rail_R", "deck_n1")),
    frozenset(("riser", "rear_en2_N")), frozenset(("riser", "deck_mid")),
    frozenset(("riser", "deck_n1")), frozenset(("riser", "deck_n2")),
    frozenset(("mdds10", "front_bay")), frozenset(("mdds10_svc", "front_bay")),
    frozenset(("mdds10_thermal", "mdds10")), frozenset(("mdds10_thermal", "pi_shelf")),
}


def touch_ok(a, b):
    return frozenset((a[0].rstrip("~m"), b[0].rstrip("~m"))) in ALLOWED_TOUCH


def gap(a, b):
    """Largest single-axis separation; negative means volumetric overlap."""
    return max(max(a[3] - b[4], b[3] - a[4]),
               max(a[5] - b[6], b[5] - a[6]),
               max(a[7] - b[8], b[7] - a[8]))


problems, warnings = [], []
for i, a in enumerate(boxes):
    if a[1] in ("item", "service"):
        wall_margin = min(a[3] + IX, IX - a[4], a[5] + IY, IY - a[6])
        if wall_margin < 0:
            problems.append(f"OUT OF INTERIOR: {a[0]}")
        elif wall_margin < 2:
            warnings.append(f"WALL MARGIN {wall_margin:.1f} mm (<2): {a[0]}")
    for b in boxes[i + 1:]:
        if a[2].rstrip("~m") == b[2].rstrip("~m"):
            continue
        g = gap(a, b)
        if g < 0:
            problems.append(f"OVERLAP {-g:.1f} mm: {a[0]} <-> {b[0]}")
        elif g < 2.0 and not touch_ok(a, b):
            warnings.append(f"MARGIN {g:.1f} mm (<2): {a[0]} <-> {b[0]}")

for nm, x0, x1, y0, y1 in [
    ("estop_panel", EST[0] - ER, EST[0] + ER, EST[1] - ER, EST[1] + ER),
    ("mic", MIC[0] - MR, MIC[0] + MR, MIC[1] - MR, MIC[1] + MR),
    ("vent", 30, 90, -96, -65),
]:
    if x0 < -RFX or x1 > RFX or y0 < -RFY or y1 > RFY:
        problems.append(f"OFF ROOF FLAT: {nm} exceeds +/-{RFX:.0f} x +/-{RFY:.0f}")

for nm, ax in [("front", FAX), ("rear", RAX)]:
    if abs(ax) + P.wheel_radius > BODY_L / 2 - 2:
        problems.append(f"WHEEL OUTSIDE BODY: {nm} axle X={ax}")

masses = [("battery", 340, 30), ("head+neck", 350, P.head_center_x), ("pi+hat", 140, -53),
          ("mdds10+plate", 160, -67), ("motors+wheels", 400, RAX), ("front wheels+pods", 150, FAX),
          ("deck+fuse+regs", 300, 66), ("relay", 60, -20), ("printed body", 1000, 0),
          ("bumper+switches", 200, 0), ("speakers+mic", 120, -10), ("estop", 60, EST[0])]
cg_x = sum(m * x for _, m, x in masses) / sum(m for _, m, x in masses)

print(f"body {BODY_L} x {BODY_W} x {BODY_H} (Z_TOP {Z_TOP}); roof flat +/-{RFX:.0f} x +/-{RFY:.0f}")
print(f"height derivation: thermal ceiling {THERM_TOP:.3f} + shelf 4 + Pi {P.pi_clearance_height:.0f}"
      f" + HAT 22 + margin {MARGIN:.0f} = {HAT_TOP + MARGIN:.3f} required drop bottom;"
      f" v1 drop {DROP_V1} => dH +{DH} => H {BODY_H:.0f}")
print(f"axles {FAX}/{RAX} (wheelbase {RAX - FAX:.0f}); rough CG X={cg_x:.0f}")
print("critical margins: "
      f"HAT-to-drop {DROP0 - HAT_TOP:.1f}; estop-terms-to-deck {ET0 - DECK1:.1f}; "
      f"speaker-arch web {115 - 109:.0f}; rear-wheel-to-shell {BODY_L / 2 - (RAX + P.wheel_radius):.0f}; "
      f"lead-corridor-to-wall {IX - 113:.1f}")
print()
if problems or warnings:
    for pr in problems:
        print("  ", pr)
    for w in warnings:
        print("  ", w)
    print(f"\nBOX-LEVEL RESULT: NOT CLOSED ({len(problems)} violations, {len(warnings)} thin margins).")
    sys.exit(1)
print("BOX-LEVEL RESULT: layout v5.1 closes with zero violations and no margin below 2 mm.")
print("D027 gate REMAINS OPEN: box screen only. The gate needs the v2 BREP")
print("packing model + the inventory-driven production validator (plan, Phase 2).")
