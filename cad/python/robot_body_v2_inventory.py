"""Registered inventory for the v2 printed-only body (Phase 2, D025-D028).

This module is the single source of truth for the v2 layout's envelopes
and the printed-part registry. It is consumed by:

- `packing_study_printed_only.py` — the box-level screen (today);
- `robot_body_v2.py` — the v2 BREP packing model (forthcoming);
- `validate_robot_body_v2.py` — the inventory-driven validator
  (forthcoming), whose contract is that an envelope absent from THIS
  registry is itself a failure.

Every envelope entry records its `basis`: which `Params` fields or
verified helpers it derives from, or that it is still an ESTIMATE. The
estimates are exactly the envelopes the BREP phase must replace with
drawing-backed geometry before the D027 gate can close.

The printed-part registry implements D028: each part declares quantity,
material, print orientation, and a justification for existing as a
separate part (service access, material/color change, orientation
conflict, calibration interface, or wear-part replaceability). Parts
marked `merge_candidate` are owed merges that bring the draft count down
to the hard budget of 40.
"""

from __future__ import annotations

import math
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import robot_body as rb  # noqa: E402

P = rb.Params()

# ---------------------------------------------------------------------------
# Verified datums (review round 3; see the plan's review-outcome section).
# ---------------------------------------------------------------------------
WALL = P.wall
BODY_L, BODY_W = 238.0, 220.0
IX, IY = BODY_L / 2 - WALL, BODY_W / 2 - WALL            # interior walls
ROOF_FLAT_X = BODY_L / 2 - P.body_edge_radius            # rollover-limited roof flat
ROOF_FLAT_Y = BODY_W / 2 - P.body_edge_radius
TRAY_TOP = P.body_bottom                                  # 49 (verified)
MDDS_TOP = (rb.motor_controller_plate_top_z(P) + P.mdds10_standoff_height
            + P.mdds10_above_pcb)                         # 76.275 (verified)
THERM_TOP = MDDS_TOP + P.mdds10_airflow_height            # 86.275
SHELF0, SHELF1 = THERM_TOP, THERM_TOP + 4.0
PI_TOP = SHELF1 + P.pi_clearance_height                   # 118.275
HAT_TOP = PI_TOP + 22.0                                   # 140.275 (96 x 74 x 22 reserve)
CLEAR_MARGIN = 3.0
DROP_V1 = 131.6                                           # pan_servo_fit bbox min Z at H=121 (verified)
DH = math.ceil(HAT_TOP + CLEAR_MARGIN - DROP_V1)          # 12, computed
BODY_H = 121.0 + DH                                       # 133
Z_TOP = P.body_bottom + BODY_H                            # 182
Z_ROOF_IN = Z_TOP - WALL
DROP0 = DROP_V1 + DH                                      # 143.6
DECK0, DECK1 = P.power_deck_z - 2.0, P.power_deck_z + 2.0  # 102..106 (verified)
FRONT_AXLE_X, REAR_AXLE_X = -74.0, 74.0                   # wheels >= 2 mm inside shell
ESTOP = (55.0, 52.0)
ESTOP_R = P.estop_backing_outer_radius
MIC = (60.0, -25.0)
MIC_R = (P.mic_array_diameter + 2 * P.mic_cradle_outer_margin) / 2
ESTOP_BODY_Z0 = Z_ROOF_IN - P.estop_body_depth            # 130.1
ESTOP_TERM_Z0 = ESTOP_BODY_Z0 - P.estop_terminal_service_depth  # 110.1

MIN_MARGIN = 2.0      # minimum clearance between distinct assemblies and to walls


# ---------------------------------------------------------------------------
# Envelope registry.
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Envelope:
    name: str
    kind: str      # "keepout" | "item" | "service"
    group: str
    box: tuple     # (x0, x1, y0, y1, z0, z1)
    basis: str     # Params/helper derivation, or "ESTIMATE: ..."
    mirror_y: bool = False


E = Envelope
ENVELOPES = [
    # -- structure and purchased-part keepouts --
    E("front_bay", "keepout", "shellF", (-IX, -104, -IY, IY, TRAY_TOP, Z_TOP),
      "modeled: fascia panel recess + front ToF pocket depth (robot_body_v2)"),
    E("rear_en2_N", "keepout", "rear_en2_N", (IX - 28, IX, 23, 47, 115, 145),
      "charge_jack_overall_depth 20.07 + wire bend; rear panel + connector holes modeled"),
    E("rear_mute_S", "keepout", "rear_mute_S",
      (IX - (P.mute_switch_body_depth + P.mute_switch_terminal_service_depth), IX, -47, -23, 115, 145),
      "mute_switch_body_depth 26 + mute_switch_terminal_service_depth 16"),
    E("front_arch", "keepout", "shellF", (FRONT_AXLE_X - 43, FRONT_AXLE_X + 43, 96, IY, TRAY_TOP, 109),
      "modeled: circular arch opening r47 following the tire; wall band Y 94..112", mirror_y=True),
    E("rear_arch", "keepout", "shellR", (REAR_AXLE_X - 43, IX, 96, IY, TRAY_TOP, 109),
      "modeled: circular arch opening r47 following the tire (rear)", mirror_y=True),
    E("front_pod", "keepout", "shellF", (FRONT_AXLE_X - 22, FRONT_AXLE_X + 22, 86, IY, TRAY_TOP, 95),
      "modeled: pod skeleton with integral printed stub axle (robot_body_v2)", mirror_y=True),
    E("motor", "keepout", "shellR",
      (REAR_AXLE_X - 12.5, REAR_AXLE_X + 12.5, P.motor_face_y - P.motor_body_length, IY, 53.5, 78.5),
      "motor_body_diameter 25 / motor_body_length 68.45 / motor_face_y 110 at axle Z 66", mirror_y=True),
    E("neck_drop", "keepout", "head", (P.neck_x - 26, P.neck_x + 26, -26, 26, DROP0, Z_TOP),
      "pan_servo_fit bbox min Z 131.6 at H=121, tracking body height; XY ESTIMATE"),
    E("head_roof", "keepout", "head",
      (P.head_center_x - 46, P.head_center_x + 46, -70, 70, Z_TOP - 10, Z_TOP),
      "ESTIMATE: head shadow proxy over the roof"),
    E("neck_collar", "keepout", "head", (P.neck_x - 30, P.neck_x + 30, -30, 30, Z_TOP - 8, Z_TOP),
      "neck_collar_outer_diameter 60"),
    E("estop_panel", "keepout", "estop",
      (ESTOP[0] - ESTOP_R, ESTOP[0] + ESTOP_R, ESTOP[1] - ESTOP_R, ESTOP[1] + ESTOP_R, Z_TOP - 20, Z_TOP),
      "estop_backing_outer_radius 33"),
    E("estop_body", "keepout", "estop",
      (ESTOP[0] - 20, ESTOP[0] + 20, ESTOP[1] - 20, ESTOP[1] + 20, ESTOP_BODY_Z0, Z_TOP),
      "estop_body_pass_diameter 40 / estop_body_depth 48.7"),
    E("estop_term", "keepout", "estop",
      (ESTOP[0] - 20, ESTOP[0] + 20, ESTOP[1] - 20, ESTOP[1] + 20, ESTOP_TERM_Z0, ESTOP_BODY_Z0),
      "estop_terminal_service_depth 20"),
    E("mic", "keepout", "mic",
      (MIC[0] - MIC_R, MIC[0] + MIC_R, MIC[1] - MIC_R, MIC[1] + MIC_R, Z_TOP - 20, Z_TOP),
      "mic_array_diameter 70 + mic_cradle_outer_margin 3"),
    E("vent", "keepout", "vent", (30, 90, -96, -65, Z_TOP - 10, Z_TOP),
      "design: slim south vent strip (D027 delta)"),
    E("speaker", "keepout", "speaker", (-48, 22, 76, 106, 115, 145),
      "speaker 70x30x17 + clearance; shell ledges/gussets modeled (robot_body_v2)", mirror_y=True),
    E("mdds10_thermal", "keepout", "mddsT", (-101, -34, -50.5, 50.5, MDDS_TOP, THERM_TOP),
      "mdds10_airflow_height 10 over the board extent"),

    # -- placed items and their service volumes --
    E("mdds10", "item", "mdds", (-101, -34, -50.5, 50.5, 64, MDDS_TOP),
      "MDDS10 board 66.8x101 + components, PCB bottom at Z 64 on the tower "
      "standoffs (motor_controller_plate_top_z chain); plate, standoffs, and "
      "shelf are controller_tower printed geometry"),
    E("mdds10_svc", "service", "mdds", (-89, -45, 62, 84, TRAY_TOP + 3, MDDS_TOP),
      "mdds10_terminal_service 24x44, terminals facing NORTH (rotated board short edge)"),
    E("pi_shelf", "item", "pi", (-101, -5, -34, 34, SHELF1, PI_TOP),
      "pi_clearance 96x68x28 seated on the controller_tower shelf plate "
      "(the plate itself is printed geometry at the thermal ceiling)"),
    E("pi_port_svc", "service", "pi", (-5, 19, -30, 30, SHELF1, PI_TOP),
      "ESTIMATE: 24 mm east cable service at the port edge"),
    E("ai_hat2", "item", "pi", (-101, -5, -37, 37, PI_TOP, HAT_TOP),
      "cad-mechanical-plan.md: AI HAT+ 2 clearance 96 x 74 x 22; stacked above the Pi band (conservative)"),
    E("pico_floor", "item", "pico", (-28, 34, 47, 80, 53, 67),
      "pico2_clearance 62x33x14 seated on 4 mm tray bosses (bosses are tray geometry)"),
    E("pico_usb_svc", "service", "pico", (34, 54, 58.5, 68.5, 53, 67),
      "pico2_usb_notch 20x10, facing EAST"),
    E("pico_swd_svc", "service", "pico", (-26, -6, 52, 75, 63, 80),
      "ESTIMATE: top-access SWD service volume"),
    E("battery_pack", "item", "bat", (-25.3, 85.3, -38.1, 38.1, 52, 79),
      "BLF-1203AB 110x75x27 rotated + 0.6 side clearance, on 3 mm tray pads; "
      "cradle rails/stops are tray geometry, not envelope"),
    E("bat_leads", "service", "bat", (85, 113, -27, 27, 65, 79),
      "battery_lead_service 28x54x14 at the pack rear"),
    E("riser", "service", "bat", (100, 113, 25, 45, 65, 115),
      "round-4 carry-in: lead riser through the deck notch to the EN2"),
    E("deck_mid", "item", "deck", (24, 113.8, -67, 23, DECK0, DECK1),
      "deck plate at power_deck_z +/- 2 (verified); riser notch splits the segments"),
    E("deck_n2", "item", "deck", (56, 98, 23, 47, DECK0, DECK1),
      "deck segment west of the riser notch; NW trimmed (floor below is battery+Pico, nothing to carry)"),
    E("deck_n1", "item", "deck", (56, 113.8, 47, 67, DECK0, DECK1), "deck north segment, NW trimmed"),
    E("fuse5045", "item", "fuse",
      (24, 24 + P.power_distribution_width, -67, -67 + P.power_distribution_length,
       DECK1, DECK1 + P.power_distribution_height),
      "Blue Sea 5045 92.5x43.8x32.5 (power_distribution_*), lengthwise on the deck south half"),
    E("fuse_wire_svc", "service", "fuse",
      (24, 24 + P.power_distribution_width, -67 - P.power_distribution_wire_service_length, -67,
       DECK1, DECK1 + P.power_distribution_height),
      "power_distribution_wire_service_length 22 at FULL block height (round-3 fix)"),
    E("relay_bracket", "item", "relay",
      (-46, -46 + P.motor_cutoff_bracket_length, -90, -90 + P.motor_cutoff_bracket_width, TRAY_TOP, 51),
      "motor_cutoff_bracket 52x22 on the floor (round-4 carry-in: exact volumes)"),
    E("relay_body", "item", "relay",
      (-36, -36 + P.motor_cutoff_body_length, -90, -90 + P.motor_cutoff_body_width, 51,
       51 + P.motor_cutoff_body_height),
      "motor_cutoff_body 26x22x25"),
    E("relay_term_svc", "service", "relay",
      (-36, -36 + P.motor_cutoff_body_length, -90, -90 + P.motor_cutoff_body_width, 76,
       76 + P.motor_cutoff_terminal_service_height),
      "motor_cutoff_terminal_service_height 16"),
    E("regD24_under", "item", "regD24",
      (92, 92 + P.pi_regulator_width, -50, -50 + P.pi_regulator_length, 94, DECK0),
      "D24V90F5 40.6x20.3 rotated, hung under the deck"),
    E("regD24_term_S", "service", "regD24", (94, 110, -60, -50, 90, DECK0),
      "pi_regulator_terminal_service 10x16x12, south end"),
    E("regD24_term_N", "service", "regD24", (94, 110, -9.4, 0.6, 90, DECK0),
      "pi_regulator_terminal_service 10x16x12, north end (round-3 fix)"),
    E("regD36_under", "item", "regD36",
      (60, 60 + P.servo_regulator_length, -6, -6 + P.servo_regulator_width, 92.5, DECK0),
      "D36V50F6 25.4 sq, hung under the deck"),
    E("regD36_wire_W", "service", "regD36",
      (60 - P.servo_regulator_wire_service_length, 60, -2, 20, 90, DECK0),
      "servo_regulator_wire_service 14x22x12 facing WEST (round-3 fix: east exits the body)"),
    E("rail_L", "item", "rail_L", (38, 78, -60, -46, 96, DECK0),
      "signal/audio harness channel under the deck (v2: deck rib per D028); shortened clear of the SW and SE deck towers"),
    E("rail_R", "item", "rail_R", (26, 96, 41, 55, 96, DECK0),
      "switched-power harness channel under the deck (v2: deck rib per D028)"),
]

# Intended support/abutment contacts: EXACT envelope-name pairs. These waive
# only the 2 mm margin; a volumetric overlap is never waived by this list.
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


def boxes():
    """Expand mirrors into the (name, kind, group, x0, x1, y0, y1, z0, z1) tuples."""
    out = []
    for e in ENVELOPES:
        out.append((e.name, e.kind, e.group, *e.box))
        if e.mirror_y:
            x0, x1, y0, y1, z0, z1 = e.box
            out.append((e.name + "~m", e.kind, e.group + "~m", x0, x1, -y1, -y0, z0, z1))
    return out


# ---------------------------------------------------------------------------
# Printed-part registry (D028): draft v2 inventory with owed merges.
# ---------------------------------------------------------------------------
PART_BUDGET = 40

@dataclass(frozen=True)
class PrintedPart:
    name: str
    qty: int
    material: str        # "PETG" | "TPU" | "PETG-lime" | "PETG-dark"
    orientation: str     # declared print orientation (D028 audits run in it)
    justification: str   # why this exists as a separate part
    merge_candidate: str = ""  # non-empty: owed merge target to reach the budget


PP = PrintedPart
PRINTED_PARTS = [
    PP("tray", 1, "PETG", "flat, bottom down",
       "structural floor: motor saddles, switch pockets, battery cradle, pico bosses, deck towers"),
    PP("shell", 1, "PETG", "upright, open bottom down",
       "one-piece exterior; separate from tray for assembly access (arches, speaker pockets, ToF pockets, pod shrouds integrated)"),
    PP("lid", 1, "PETG-dark", "top face down", "roof service access; vent slots print directly"),
    PP("bumper_half", 2, "TPU", "flat, open-bottom U", "compliance + material change + bed length"),
    PP("rear_panel", 1, "PETG", "flat", "connector service and independent reprintability"),
    PP("fascia", 1, "PETG-dark", "flat", "sensor service + color break; front ToF pockets integrated"),
    PP("estop_mount_panel", 1, "PETG", "flat", "IDEC 4 mm clamp-range calibration interface"),
    PP("estop_backing_collar", 1, "PETG", "flat", "safety-critical roof reinforcement",
       merge_candidate="lid-integrated collar boss"),
    PP("deck", 1, "PETG", "flat, ribs up", "removable power/service deck; harness ribs + fuse saddles integrated"),
    PP("controller_tower", 1, "PETG", "flat", "MDDS10 plate + Pi shelf towers as one service module"),
    PP("pico_clamp_bar", 1, "PETG", "flat", "safety-MCU capture on tray bosses"),
    PP("battery_clamp_bar", 1, "PETG", "flat", "battery service (replaces straps, D025)"),
    PP("battery_pad_frame", 1, "TPU", "flat", "material change: compliant pack interface"),
    PP("wheel_core_rear", 2, "PETG", "axis vertical", "wear part; D-bore calibration interface"),
    PP("tire", 4, "TPU", "flat ring", "material change; shared profile front/rear"),
    PP("wheel_front", 2, "PETG", "axis vertical",
       "wear part; bore is the bearing surface (bushing merged into the wheel; worn wheel = reprint)"),
    PP("front_pod", 2, "PETG", "inboard face down (axle rises vertical)",
       "orientation conflict with the flat-printed tray: the stub axle must print axis-vertical"),
    PP("printed_washer_set", 1, "PETG", "flat",
       "plan rule 4: printed washers under screw heads on TPU/soft parts and the axle-end retainers"),
    PP("motor_clamp_cap", 2, "PETG", "flat", "motor service without tray removal"),
    PP("speaker_clamp_bar", 2, "PETG", "flat", "speaker capture in shell side pockets"),
    PP("mic_cradle", 1, "PETG", "flat", "mic array service under the lid slots"),
    PP("tof_side_clamp", 2, "PETG", "flat", "side ToF capture in shell pockets"),
    PP("head_shell", 1, "PETG", "open face down", "one-piece head enclosure (v1 front/rear covers merged)"),
    PP("head_pan_plate", 1, "PETG", "flat", "underside service plate; pan servo mounts here"),
    PP("head_faceplate", 1, "PETG-dark", "flat, face down", "color break + fused camera annulus"),
    PP("camera_carrier", 1, "PETG", "flat", "camera aim/service",
       merge_candidate="head_faceplate pocket + clamp"),
    PP("neck", 1, "PETG", "flange down", "rotating pan structure with cable corridor"),
    PP("bayonet_collar", 1, "PETG", "flat", "pan retention; tool-free head removal"),
    PP("yoke", 1, "PETG", "TBD (BREP)", "tilt structure spanning the neck flange"),
    PP("tilt_adapter", 1, "PETG", "flat", "servo-horn interface on the moving head",
       merge_candidate="yoke-side integration"),
    PP("tilt_bushing", 1, "PETG", "axis vertical", "designated tilt wear part"),
    PP("pan_servo_mount", 1, "PETG", "flat", "pan servo capture",
       merge_candidate="bayonet-collar base"),
    PP("eye_diffuser_bar", 1, "PETG-lime", "flat", "color/optics: both eye diffusers as one bar"),
    PP("eye_clamp_bar", 1, "PETG", "flat", "eye NeoPixel capture",
       merge_candidate="head_faceplate pocket"),
    PP("status_diffuser_bar", 1, "PETG-lime", "flat", "color/optics: both status diffusers as one bar"),
    PP("status_clamp_bar", 1, "PETG", "flat", "status NeoPixel capture",
       merge_candidate="fascia pocket"),
]


def budget_report():
    draft = sum(p.qty for p in PRINTED_PARTS)
    owed = sum(p.qty for p in PRINTED_PARTS if p.merge_candidate)
    return draft, draft - owed, PART_BUDGET


if __name__ == "__main__":
    draft, after, budget = budget_report()
    est = [e.name for e in ENVELOPES if "ESTIMATE" in e.basis]
    print(f"envelopes: {len(ENVELOPES)} registered ({len(boxes())} boxes with mirrors)")
    print(f"ESTIMATE-basis envelopes needing BREP replacement ({len(est)}): {', '.join(est)}")
    print(f"printed parts: draft {draft}, after owed merges {after}, budget {budget}"
          f" -> {'OK' if after <= budget else 'OVER BUDGET'}")
    print(f"body {BODY_L} x {BODY_W} x {BODY_H}; axles {FRONT_AXLE_X}/{REAR_AXLE_X}; deck {DECK0}..{DECK1}")
