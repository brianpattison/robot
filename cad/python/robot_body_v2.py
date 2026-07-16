"""v2 BREP packing-model skeleton for the printed-only body (Phase 2).

Builds the primary printed solids of the D027 footprint — one-piece tray,
shell, and lid at 238 x 220 x 133, the two TPU bumper C-halves, and the
two front pods with integral printed stub axles — directly from the
registered inventory (`robot_body_v2_inventory.py`). The inventory-driven
validator checks these for interference against every registered
envelope, bed fit, and the D028 printability audits.

Current model scope:
- Tray: rounded plan, wheel-well notches, envelope-cleared deck towers,
  up-opening motor-saddle troughs, battery cradle (pads, side rails,
  low end stops clear of the lead corridor), Pico seat bosses, and six
  bumper-switch pockets molded into the underside (D028 merge: the six
  v1 switch plates are gone).
- Shell: offset-shelled 3.2 mm walls with the 12 mm top rollover, lid
  recess + opening with a seating ledge, tire-following CIRCULAR wheel
  arches (the round crown prints as a short bridge and matches the
  concept, replacing the earlier oversized peaked cuts), and mullioned
  fascia/rear openings — every sub-span <= 30 mm bridges cleanly and the
  mullions hide behind the fascia and rear panels.
- Lid: seats in the recess; E-stop bore, mic slot field, vent slots.
- Bumper C-halves (TPU): open-bottom U cross-section (D028 rule 8, no
  bridged cavities), wheel cutouts with concealed low inboard bridges
  keeping each half one piece; printed upside-down.
- Front pods: body + integral stub axle with an axle-end insert bore;
  printed INBOARD-face-down so the axle rises axis-vertical (the
  audit caught the outboard-face-down idea standing on the axle tip).

Still owed: insert bosses and the fastener system (Phase 3), speaker and
ToF pockets, head parts, rear/fascia panels, controller tower, wheels.

Run from the repo root:
    .venv-cad/bin/python cad/python/robot_body_v2.py
Exports land under cad/exports/v2/ (gitignored).
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import robot_body_v2_inventory as inv  # noqa: E402
from build123d import (  # noqa: E402
    Axis, Box, Cylinder, Pos, Rot,
    fillet, offset, Kind,
    export_step, export_stl,
)

P = inv.P
EXPORT_DIR = Path(__file__).resolve().parents[2] / "cad" / "exports" / "v2"

CORNER_R = P.body_corner_radius            # 25
ROLLOVER_R = P.body_edge_radius            # 12
WALL = inv.WALL                            # 3.2
TRAY_Z0 = inv.TRAY_TOP - P.tray_thickness  # 41
LID_RECESS = 4.0
LID_LEDGE = 6.0
LID_CLEAR = 0.25
ARCH_R = P.wheel_radius + 4.0              # 47: tire-following arch opening
ARCH_BAND = (94.0, 112.0)                  # Y band the arch clears (to just past the wall)
BUMPER_H = P.bumper_height                 # 28
BUMPER_Z0 = 29.0
BUMPER_WALL = 2.5


def rounded_slab(length, width, height, radius, z0):
    """Vertical-edge-filleted box with its base at z0."""
    b = Box(length, width, height)
    b = fillet(b.edges().filter_by(Axis.Z), radius)
    return Pos(0, 0, z0 + height / 2) * b


def build_tray():
    tray = rounded_slab(inv.BODY_L, inv.BODY_W, P.tray_thickness, CORNER_R, TRAY_Z0)
    # Wheel-well notches.
    for ax in (inv.FRONT_AXLE_X, inv.REAR_AXLE_X):
        for sy in (1, -1):
            tray -= Pos(ax, sy * (inv.IY + WALL), inv.TRAY_TOP) * Box(94, 34, 40)
    # Deck towers at envelope-cleared positions (see the validator history).
    for tx, ty in ((30.0, -61.0), (86.0, -61.0), (95.0, 61.0), (107.0, 55.0)):
        tray += Pos(tx, ty, (inv.TRAY_TOP + inv.DECK0) / 2) * Cylinder(6.0, inv.DECK0 - inv.TRAY_TOP)
        tray -= Pos(tx, ty, inv.DECK0 - 3.5) * Cylinder(2.3, 7)   # deck-joint insert bores
    # Motor saddles: up-opening troughs (support-free by construction).
    trough_r = P.motor_body_diameter / 2 + 0.2
    for sy in (1, -1):
        saddle = Pos(inv.REAR_AXLE_X, sy * 83.0, (inv.TRAY_TOP + 79.0) / 2) * Box(28, 26, 79.0 - inv.TRAY_TOP)
        saddle -= Pos(inv.REAR_AXLE_X, sy * 83.0, P.wheel_center_z) * Rot(90, 0, 0) * Cylinder(trough_r, 40)
        saddle -= Pos(inv.REAR_AXLE_X, sy * (inv.IY + WALL), inv.TRAY_TOP) * Box(94, 34, 90)
        for jx in (63, 85):
            saddle -= Pos(jx, sy * 83, 79.0 - 3.5) * Cylinder(2.3, 7)   # cap-joint inserts
        tray += saddle
    # Battery cradle: four 3 mm pads under the pack, side rails, and low end
    # stops. The pack envelope (52..79) rides the pads; rails stay outside
    # the registered pack envelope, and the rear stop stays below the lead
    # corridor (Z >= 65).
    for px in (-14.5, 75.5):
        for py in (-25.0, 25.0):
            tray += Pos(px, py, (inv.TRAY_TOP + 51.0) / 2) * Box(14, 14, 51.0 - inv.TRAY_TOP)
    for sy in (1, -1):
        tray += Pos(17.0, sy * 41.5, (inv.TRAY_TOP + 63.0) / 2) * Box(78, 5, 63.0 - inv.TRAY_TOP)
        # Battery-clamp posts on the rail tops, insert bores opening up.
        tray += Pos(17.0, sy * 42.5, (63.0 + 80.0) / 2) * Cylinder(3.4, 17)
        tray -= Pos(17.0, sy * 42.5, 80.0 - 3.5) * Cylinder(2.3, 7)
    tray += Pos(-27.5, 0, (inv.TRAY_TOP + 70.0) / 2) * Box(3, 64, 70.0 - inv.TRAY_TOP)
    tray += Pos(87.5, 0, (inv.TRAY_TOP + 63.0) / 2) * Box(3, 64, 63.0 - inv.TRAY_TOP)
    # Pico seat bosses (board bottom at Z 53; locating pegs are a later
    # detail with an allowed-intrusion entry).
    for bx in (-21.0, 27.0):
        for by in (54.5, 72.5):
            tray += Pos(bx, by, (inv.TRAY_TOP + 53.0) / 2) * Cylinder(3.5, 53.0 - inv.TRAY_TOP)
    # Shell-joint clearance holes: M3 up through the tray into the shell
    # corner lugs; the underside counterbore leaves a 3.2 mm clamp stack.
    for jx, jy in ((105, 96), (105, -96), (-105, 96), (-105, -96)):
        tray -= Pos(jx, jy, inv.TRAY_TOP - 4) * Cylinder(1.7, 10)
        tray -= Pos(jx, jy, TRAY_Z0 + 2.4) * Cylinder(3.25, 4.8)
    # Pico clamp bosses north/south of the board seat.
    for jy in (43.0, 84.0):
        tray += Pos(3.0, jy, (inv.TRAY_TOP + 67.0) / 2) * Cylinder(4.0, 67.0 - inv.TRAY_TOP)
        tray -= Pos(3.0, jy, 67.0 - 3.5) * Cylinder(2.3, 7)
    # Controller-tower base and front-pod flange insert bores.
    for jx, jy in ((-101, 59), (-101, -59), (-33, 59), (-33, -59),
                   (-86, 85), (-62, 85), (-86, -85), (-62, -85)):
        tray -= Pos(jx, jy, inv.TRAY_TOP - 3.5) * Cylinder(2.3, 7)
    # Six bumper-switch pockets molded into the tray underside (D028 merge),
    # each with an outward plunger window toward the bumper.
    for cx, cy, along_x in ((-101.0, 56.0, False), (-101.0, -56.0, False),
                            (101.0, 56.0, False), (101.0, -56.0, False),
                            (0.0, 99.0, True), (0.0, -99.0, True)):
        px, py = (42.0, 24.0) if along_x else (24.0, 42.0)
        tray -= Pos(cx, cy, TRAY_Z0 + 3.0) * Box(px, py, 6.0)
        if along_x:
            sy = 1 if cy > 0 else -1
            tray -= Pos(cx, (cy + sy * inv.BODY_W / 2) / 2, TRAY_Z0 + 3.0) * Box(12, 14, 6.0)
        else:
            sx = 1 if cx > 0 else -1
            tray -= Pos((cx + sx * inv.BODY_L / 2) / 2, cy, TRAY_Z0 + 3.0) * Box(20, 12, 6.0)
    return tray


def build_shell():
    outer = rounded_slab(inv.BODY_L, inv.BODY_W, inv.BODY_H, CORNER_R, inv.TRAY_TOP)
    outer = fillet(outer.edges().group_by(Axis.Z)[-1], ROLLOVER_R)
    bottom = outer.faces().sort_by(Axis.Z)[0]
    shell = offset(outer, -WALL, openings=bottom, kind=Kind.INTERSECTION)

    # Lid recess and through-opening with a seating ledge.
    lid_l, lid_w = 216.0, 196.0
    shell -= rounded_slab(lid_l, lid_w, LID_RECESS + 1.0, 18.0, inv.Z_TOP - LID_RECESS)
    shell -= rounded_slab(lid_l - 2 * LID_LEDGE, lid_w - 2 * LID_LEDGE, 20.0, 14.0, inv.Z_TOP - 16.0)

    # Tire-following circular wheel arches: the round crown prints as a
    # short bridge and matches the concept's arch look.
    band_c = (ARCH_BAND[0] + ARCH_BAND[1]) / 2
    band_w = ARCH_BAND[1] - ARCH_BAND[0]
    for ax in (inv.FRONT_AXLE_X, inv.REAR_AXLE_X):
        for sy in (1, -1):
            arch = Pos(ax, sy * band_c, P.wheel_center_z) * Rot(90, 0, 0) * Cylinder(ARCH_R, band_w)
            arch += Pos(ax, sy * band_c, (inv.TRAY_TOP - 10 + P.wheel_center_z) / 2) * Box(
                2 * ARCH_R, band_w, P.wheel_center_z - inv.TRAY_TOP + 10)
            shell -= arch

    # Corner lugs for the tray joint: bosses fused into the interior corner
    # arcs, blind insert bores opening downward (screws drive up from the
    # tray underside, v1-style).
    for jx, jy in ((105, 96), (105, -96), (-105, 96), (-105, -96)):
        shell += Pos(jx, jy, (inv.TRAY_TOP + 68.0) / 2) * Cylinder(7.0, 68.0 - inv.TRAY_TOP)
        shell -= Pos(jx, jy, inv.TRAY_TOP + 3.4) * Cylinder(2.3, 7)
    # Lid-joint insert bores in the seating ledge (screws drive down
    # through the lid corners).
    for jx, jy in ((100, 90), (100, -90), (-100, 90), (-100, -90)):
        shell -= Pos(jx, jy, inv.Z_TOP - 16.0 + 8.0) * Cylinder(2.3, 8.1)

    # Speaker ledges on the forward side walls: a shelf below each speaker
    # envelope (Z 115..145) with a 45-degree gusset underneath (D028 rule 4).
    for sy in (1, -1):
        wall_in = sy * (inv.BODY_W / 2 - WALL)
        ledge_y = sy * (inv.BODY_W / 2 - WALL - 4)
        shell += Pos(-13, (wall_in + ledge_y) / 2, 112.5) * Box(64, 8, 5)
        gusset = Pos(-13, (wall_in + ledge_y) / 2, 106.0) * Box(64, 8, 8)
        gusset -= Pos(-13, ledge_y - sy * 1.0, 103.0) * Rot(45 * sy, 0, 0) * Box(70, 16, 16)
        shell += gusset
    # Speaker clamp columns flanking each speaker pocket, insert bores up.
    for sy in (1, -1):
        for jx in (-52.0, 26.0):
            col_y = sy * (inv.BODY_W / 2 - WALL - 4)
            shell += Pos(jx, col_y, (110.0 + 148.0) / 2) * Cylinder(4.0, 38)
            shell -= Pos(jx, col_y, 148.0 - 3.5) * Cylinder(2.3, 7)
    # Side ToF windows at the v1 station (X=-20) with interior pocket
    # ledges and a clamp boss beside each window.
    for sy in (1, -1):
        shell -= Pos(-20, sy * (inv.BODY_W / 2 - 1.5), 96.0) * Box(12, 8, 8)
        shell += Pos(-20, sy * (inv.BODY_W / 2 - WALL - 3), 89.5) * Box(24, 6, 5)
        shell += Pos(-32, sy * (inv.BODY_W / 2 - WALL - 4), (87.0 + 100.0) / 2) * Cylinder(4.0, 13)
        shell -= Pos(-32, sy * (inv.BODY_W / 2 - WALL - 4), 100.0 - 3.5) * Cylinder(2.3, 7)

    # Fascia opening: two 27 mm sub-openings with a hidden 4 mm mullion
    # (every bridge span <= 30; the fascia panel covers the mullions).
    for sy in (1, -1):
        shell -= Pos(-(inv.BODY_L / 2 - 3.5), sy * 15.5, 110.0) * Box(8, 27, 30)
    # Rear panel opening: three 28 mm sub-openings with hidden mullions.
    for cy in (-32.0, 0.0, 32.0):
        shell -= Pos(inv.BODY_L / 2 - 3.5, cy, 132.0) * Box(8, 28, 40)
    # Flush seating recesses for the snap-in fascia and rear panels.
    shell -= Pos(-(inv.BODY_L / 2 - 0.7), 0, 110.0) * Box(1.5, 76, 40)
    shell -= Pos(inv.BODY_L / 2 - 0.7, 0, 132.0) * Box(1.5, 104, 50)
    return shell


def build_lid():
    lid = rounded_slab(216.0 - LID_CLEAR * 2, 196.0 - LID_CLEAR * 2, LID_RECESS, 18.0,
                       inv.Z_TOP - LID_RECESS)
    lid -= Pos(inv.ESTOP[0], inv.ESTOP[1], inv.Z_TOP - LID_RECESS / 2) * Cylinder(
        P.estop_panel_hole / 2, LID_RECESS + 2)
    lid -= Pos(P.neck_x, 0, inv.Z_TOP - LID_RECESS / 2) * Cylinder(26.5, LID_RECESS + 2)
    for i in range(9):
        lid -= Pos(inv.MIC[0], inv.MIC[1] - 30 + i * 7.5, inv.Z_TOP - LID_RECESS / 2) * Box(36, 3, LID_RECESS + 2)
    for i in range(5):
        lid -= Pos(60, -92 + i * 6.0, inv.Z_TOP - LID_RECESS / 2) * Box(50, 3, LID_RECESS + 2)
    # Lid-joint clearance holes with top counterbores (3.2 mm clamp stack).
    for jx, jy in ((100, 90), (100, -90), (-100, 90), (-100, -90)):
        lid -= Pos(jx, jy, inv.Z_TOP - LID_RECESS / 2) * Cylinder(1.7, LID_RECESS + 2)
        lid -= Pos(jx, jy, inv.Z_TOP - 0.4) * Cylinder(3.25, 0.9)
    # Integrated E-stop backing collar (merge of the v1 separate collar):
    # a reinforcing ring under the panel bore for the purchased nut clamp.
    ring = Pos(inv.ESTOP[0], inv.ESTOP[1], inv.Z_TOP - LID_RECESS - 3.0) * Cylinder(33.0, 6)
    ring -= Pos(inv.ESTOP[0], inv.ESTOP[1], inv.Z_TOP - LID_RECESS - 3.0) * Cylinder(15.0, 8)
    lid += ring
    # Mic-cradle bosses under the lid, flanking the slot field.
    for jx, jy in ((30, -25), (90, -25)):
        lid += Pos(jx, jy, inv.Z_TOP - LID_RECESS - 3.0) * Cylinder(4.5, 6)
        lid -= Pos(jx, jy, inv.Z_TOP - LID_RECESS - 6.0 + 3.5) * Cylinder(2.3, 7)
    return lid


def _bumper_ring():
    outer_l = inv.BODY_L + 2 * (P.bumper_body_clearance + 8.0)   # 256
    outer_w = inv.BODY_W + 2 * (P.bumper_body_clearance + 8.0)   # 238
    inner_l = inv.BODY_L + 2 * P.bumper_body_clearance           # 240
    inner_w = inv.BODY_W + 2 * P.bumper_body_clearance           # 222
    ring = rounded_slab(outer_l, outer_w, BUMPER_H, P.bumper_outer_corner_radius, BUMPER_Z0)
    ring -= rounded_slab(inner_l, inner_w, BUMPER_H + 4, P.bumper_outer_corner_radius - 8, BUMPER_Z0 - 2)
    # Open-bottom U cross-section: hollow between the walls, roof kept
    # (D028 rule 8: no bridged cavities in TPU).
    cavity = rounded_slab(outer_l - 2 * BUMPER_WALL, outer_w - 2 * BUMPER_WALL, BUMPER_H,
                          P.bumper_outer_corner_radius - BUMPER_WALL, BUMPER_Z0 - 2.5)
    cavity -= rounded_slab(inner_l + 2 * BUMPER_WALL, inner_w + 2 * BUMPER_WALL, BUMPER_H + 8,
                           P.bumper_outer_corner_radius - 8 + BUMPER_WALL, BUMPER_Z0 - 4)
    ring -= cavity
    # Wheel cutouts with concealed low inboard bridges (keeps each C-half
    # one piece; the bridge hides below the tray).
    for ax in (inv.FRONT_AXLE_X, inv.REAR_AXLE_X):
        for sy in (1, -1):
            ring -= Pos(ax, sy * 114.5, 50.0) * Box(94, 11, 17)
            ring -= Pos(ax, sy * 116.5, BUMPER_Z0 + BUMPER_H / 2) * Box(94, 7, BUMPER_H + 4)
    return ring


def build_bumper_half(front: bool):
    ring = _bumper_ring()
    keep = Pos(-inv.BODY_L / 2 - 20 if front else inv.BODY_L / 2 + 20, 0, BUMPER_Z0 + BUMPER_H / 2) * Box(
        inv.BODY_L + 40, inv.BODY_W + 60, BUMPER_H + 6)
    return ring & keep


def build_front_pod(left: bool):
    sy = -1 if left else 1
    body = Pos(inv.FRONT_AXLE_X, sy * 96.0, (inv.TRAY_TOP + 92.0) / 2) * Box(40, 18, 92.0 - inv.TRAY_TOP)
    axle = Pos(inv.FRONT_AXLE_X, sy * 118.0, P.wheel_center_z) * Rot(90, 0, 0) * Cylinder(9.0, 26)
    pod = body + axle
    # Inboard base flange with the tray-joint holes (3.2 clamp stack).
    flange = Pos(inv.FRONT_AXLE_X, sy * 85.0, inv.TRAY_TOP + 1.6) * Box(40, 6, 3.2)
    for jx in (-86, -62):
        flange -= Pos(jx, sy * 85.0, inv.TRAY_TOP + 1.6) * Cylinder(1.7, 5)
    pod += flange
    # Axle-end insert bore for the retaining screw (prints axis-vertical in
    # the pod's inboard-face-down orientation).
    pod -= Pos(inv.FRONT_AXLE_X, sy * 126.0, P.wheel_center_z) * Rot(90, 0, 0) * Cylinder(2.3, 12)
    return pod


def build_fascia():
    plate = Pos(-(inv.BODY_L / 2 - 0.75), 0, 110.0) * Box(1.5, 75.4, 39.4)
    # Front ToF apertures (boards pocket behind; Y +/-16.5 per v1 stations).
    for sy in (1, -1):
        plate -= Pos(-(inv.BODY_L / 2 - 0.75), sy * 16.5, 106.0) * Box(3, 7, 5)
    # Status diffuser slots (lime bars mount behind).
    for sy in (1, -1):
        plate -= Pos(-(inv.BODY_L / 2 - 0.75), sy * 30.0, 116.0) * Box(3, 10, 5)
    return plate


def build_rear_panel():
    plate = Pos(inv.BODY_L / 2 - 0.75, 0, 132.0) * Box(1.5, 103.4, 49.4)
    plate -= Pos(inv.BODY_L / 2 - 0.75, 35.0, 130.0) * Cylinder(
        P.charge_jack_cutout_diameter / 2, 4, rotation=(0, 90, 0))
    plate -= Pos(inv.BODY_L / 2 - 0.75, -35.0, 130.0) * Cylinder(
        P.mute_switch_cutout_diameter / 2, 4, rotation=(0, 90, 0))
    return plate


def build_controller_tower():
    # One printed module: MDDS10 base + board standoffs + the Pi shelf
    # frame at the thermal ceiling (D028 merge of plate + shelf). The v1
    # 5 mm spacer lift becomes a molded plinth with three cable/air
    # channels, so the base prints bed-down with only short bridges
    # instead of a floating plate underside.
    tower = Pos(-67, 0, (inv.TRAY_TOP + 58.0) / 2) * Box(74, 124, 58.0 - inv.TRAY_TOP)
    for cy in (-40.0, 0.0, 40.0):
        tower -= Pos(-67, cy, (inv.TRAY_TOP + 54.0) / 2) * Box(80, 22, 54.0 - inv.TRAY_TOP)
    # Base joint: through-holes + counterbores leave a 3.2 clamp stack.
    for jx, jy in ((-101, 59), (-101, -59), (-33, 59), (-33, -59)):
        tower -= Pos(jx, jy, 53.5) * Cylinder(1.7, 10)
        tower -= Pos(jx, jy, 58.0 - 2.9) * Cylinder(3.25, 5.9)
    # Board standoffs (MDDS10 95.25 x 60.96 pattern, rotated: Y-long).
    for bx in (-97.5, -36.5):
        for by in (-47.6, 47.6):
            tower += Pos(bx, by, 61.0) * Cylinder(3.2, 6)
    # Shelf columns outside the thermal volume (|Y| > 50.5). The east pair
    # threads the gap between the battery pack (Y <= 38.1) and the Pico
    # (Y >= 47) / SWD box, so they are slimmer.
    for cx, cy, cr in ((-96, -57, 5.0), (-96, 57, 5.0), (-12, -44, 4.0), (-12, 44, 3.0)):
        tower += Pos(cx, cy, (58.0 + inv.SHELF0) / 2) * Cylinder(cr, inv.SHELF0 - 58.0)
    # Pi shelf as a frame + crossbars, not a solid plate: every elevated
    # ceiling is a narrow strip that bridges (D028), and the windows feed
    # the MDDS10 airflow below.
    frame = Pos(-53, 0, inv.SHELF0 + 2.0) * Box(96, 126, 4)
    for wx, wy in ((-77, -34.5), (-77, 0.0), (-77, 34.5), (-29, -34.5), (-29, 0.0), (-29, 34.5)):
        frame -= Pos(wx, wy, inv.SHELF0 + 2.0) * Box(36, 23, 6)
    tower += frame
    return tower


def build_rear_wheel():
    wheel = Pos(inv.REAR_AXLE_X, 118, P.wheel_center_z) * Rot(90, 0, 0) * Cylinder(21.0, 24)
    # 4 mm D-bore hub: bore minus the D-flat keeps torque geometric.
    bore = Pos(inv.REAR_AXLE_X, 118, P.wheel_center_z) * Rot(90, 0, 0) * Cylinder(2.05, 26)
    bore -= Pos(inv.REAR_AXLE_X, 118, P.wheel_center_z + 3.5) * Box(6, 28, 4)
    wheel -= bore
    # Radial clamp-screw bore into an insert boss (axial retention only).
    wheel -= Pos(inv.REAR_AXLE_X, 118, P.wheel_center_z + 12) * Cylinder(2.3, 20)
    return wheel


def build_front_wheel():
    wheel = Pos(inv.FRONT_AXLE_X, 118, P.wheel_center_z) * Rot(90, 0, 0) * Cylinder(21.0, 24)
    wheel -= Pos(inv.FRONT_AXLE_X, 118, P.wheel_center_z) * Rot(90, 0, 0) * Cylinder(9.25, 26)
    return wheel


def build_tire():
    tire = Pos(0, 0, 0) * Rot(90, 0, 0) * Cylinder(P.wheel_radius, P.wheel_thickness)
    tire -= Rot(90, 0, 0) * Cylinder(20.8, P.wheel_thickness + 2)
    return tire


HEAD_DZ = inv.DH                      # the head rises with the body height
HEAD_C = (P.head_center_x, 0.0, 242.0 + HEAD_DZ)
NECK_Z0, NECK_Z1 = 167.5 + HEAD_DZ, 211.5 + HEAD_DZ


def build_head_shell():
    # OCC's shelling silently no-ops on this triple-filleted capsule, so the
    # cavity is built explicitly. The head prints open-face-down, so the
    # cavity's REAR is heavily domed: the interior then builds as converging
    # perimeters instead of presenting a large flat ceiling, with only a
    # small allowlisted crown region left to droop invisibly inside.
    z0 = HEAD_C[2] - P.head_height / 2
    cap = rounded_slab(P.head_depth, P.head_width, P.head_height, 28.0, z0)
    cap = fillet(cap.edges().group_by(Axis.Z)[-1], 15.0)
    cap = fillet(cap.edges().group_by(Axis.Z)[0], 10.0)
    # Cavity: a shortened rounded box plus a large-radius cylindrical rear
    # cap (crown reaching the original cavity rear), so the interior closes
    # by converging perimeters when printed face-down.
    cav_d, cav_w, cav_h = P.head_depth - 5 - 14, P.head_width - 5, P.head_height - 5
    cavity = rounded_slab(cav_d, cav_w, cav_h, 25.5, z0 + 2.5)
    cavity = Pos(-7.0, 0, 0) * cavity                      # main box spans X -33.5..19.5
    cavity = fillet(cavity.edges().group_by(Axis.Z)[-1], 12.5)
    cavity = fillet(cavity.edges().group_by(Axis.Z)[0], 7.5)
    rear_x, junc_x, half_w = 33.5, 19.5, cav_w / 2
    cap_r = ((rear_x - junc_x) ** 2 + half_w ** 2) / (2 * (rear_x - junc_x))
    rear_cap = Pos(rear_x - cap_r, 0, z0 + 2.5 + cav_h / 2) * Cylinder(cap_r, cav_h - 10)
    rear_cap &= Pos(rear_x - 20, 0, z0 + 2.5 + cav_h / 2) * Box(40, cav_w, cav_h - 10)
    cavity += rear_cap
    shell = cap - cavity
    shell = Pos(HEAD_C[0], 0, 0) * shell
    # Front opening for the faceplate assembly.
    shell -= Pos(HEAD_C[0] - P.head_depth / 2 + 3, 0, HEAD_C[2]) * Box(8, 120, 56)
    # Underside pan-plate opening.
    shell -= Pos(HEAD_C[0], 0, z0 + 1.5) * Box(44, 76, 8)
    return shell


def build_head_faceplate():
    x0 = HEAD_C[0] - P.head_depth / 2
    plate = Pos(x0 + 1.5, 0, HEAD_C[2]) * Box(3, P.head_faceplate_width, P.head_faceplate_height)
    plate -= Pos(x0 + 1.5, 0, HEAD_C[2]) * Cylinder(P.head_camera_aperture_radius, 5, rotation=(0, 90, 0))
    for sy in (1, -1):
        plate -= Pos(x0 + 1.5, sy * 40.0, HEAD_C[2]) * Box(4, 9, 14)
    return plate


def build_neck():
    neck = Pos(P.neck_x, 0, (NECK_Z0 + NECK_Z1) / 2) * Cylinder(20.0, NECK_Z1 - NECK_Z0)
    neck -= Pos(P.neck_x, 0, (NECK_Z0 + NECK_Z1) / 2) * Cylinder(14.0, NECK_Z1 - NECK_Z0 + 4)
    return neck


def build_bayonet_collar():
    ring = Pos(P.neck_x, 0, NECK_Z0 + 6.0) * Cylinder(26.0, 6)
    ring -= Pos(P.neck_x, 0, NECK_Z0 + 6.0) * Cylinder(20.5, 10)
    return ring


def build_head_pan_plate():
    z0 = HEAD_C[2] - P.head_height / 2
    return Pos(HEAD_C[0], 0, z0 + 2.5) * Box(42, 74, 3)


def build_deck():
    # Removable power/service deck: the three registered plate segments
    # (riser notch and trimmed NW as gaps), harness ribs flanking the two
    # wire channels (D028 merge: the v1 rails are deck geometry), a fuse
    # pocket lip, and counterbored tower-joint holes. Prints top-face-down
    # so every rib and lip builds upward.
    deck = Pos((24 + 113.8) / 2, (-67 + 23) / 2, (inv.DECK0 + inv.DECK1) / 2) * Box(89.8, 90, 4)
    deck += Pos((56 + 98) / 2, 35, (inv.DECK0 + inv.DECK1) / 2) * Box(42, 24, 4)
    deck += Pos((56 + 113.8) / 2, 57, (inv.DECK0 + inv.DECK1) / 2) * Box(57.8, 20, 4)
    # Harness ribs just outside the registered channel volumes.
    for y in (-62.0, -44.0):
        deck += Pos(58.0, y + 1.0 if y < -50 else y - 1.0, (96 + inv.DECK0) / 2) * Box(40, 2, inv.DECK0 - 96)
    for y in (39.0 + 1.0, 57.0 - 1.0):
        deck += Pos(56.5, y, (96 + inv.DECK0) / 2) * Box(61, 2, inv.DECK0 - 96)
    # Fuse block pocket lip (west/east/north; the south edge is the wire
    # overhang) — the block drops in and the lip locates its base.
    deck += Pos(22.0, -20.75, inv.DECK1 + 1.5) * Box(4, 92.5, 3)
    deck += Pos(69.8, -20.75, inv.DECK1 + 1.5) * Box(4, 92.5, 3)
    deck += Pos(45.9, 27.5, inv.DECK1 + 1.5) * Box(51.8, 4, 3)
    # Tower joint holes: through 3.4 with a 0.8 top counterbore -> 3.2 stack.
    for jx, jy in ((30, -61), (86, -61), (95, 61), (107, 55)):
        deck -= Pos(jx, jy, (inv.DECK0 + inv.DECK1) / 2) * Cylinder(1.7, 6)
        deck -= Pos(jx, jy, inv.DECK1 - 0.35) * Cylinder(3.25, 0.9)
    return deck


def build_motor_cap():
    # Clamp cap bridging the saddle: flat plate with a shallow gripping arc,
    # printed arc-up (upside down) so it stays support-free.
    cap = Pos(inv.REAR_AXLE_X, 83.0, 81.4) * Box(28, 26, 6)
    cap -= Pos(inv.REAR_AXLE_X, 83.0, P.wheel_center_z) * Rot(90, 0, 0) * Cylinder(12.7, 40)
    for jx in (63, 85):
        cap -= Pos(jx, 83.0, 81.4) * Cylinder(1.7, 8)
        cap -= Pos(jx, 83.0, 83.4) * Cylinder(3.25, 2.2)
    return cap


def build_battery_clamp():
    # 3.2 mm bar spanning the pack between the rail posts: the bar itself is
    # the D026 clamp stack, so no counterbores are needed.
    bar = Pos(17.0, 0, 81.6) * Box(16, 99, 3.2)
    for sy in (1, -1):
        bar -= Pos(17.0, sy * 42.5, 81.6) * Cylinder(1.7, 5)
    return bar


def build_mic_cradle():
    ring = Pos(60, -25, 173.6) * Cylinder(38.0, 3.2) - Pos(60, -25, 173.6) * Cylinder(33.0, 5)
    for jx, jy in ((30, -25), (90, -25)):
        ear = Pos(jx, jy, 173.6) * Cylinder(6.0, 3.2)
        ear -= Pos(jx, jy, 173.6) * Cylinder(1.7, 5)
        ring += ear
        ring += Pos((jx + 60) / 2, jy, 173.6) * Box(18, 8, 3.2)
    return ring


def build_speaker_clamp():
    bar = Pos(-13, 100, 149.6) * Box(86, 8, 3.2)
    for jx in (-52.0, 26.0):
        bar -= Pos(jx, 100, 149.6) * Cylinder(1.7, 5)
    return bar


def build_tof_clamp():
    bar = Pos(-26, inv.BODY_W / 2 - WALL - 4, 101.6) * Box(20, 8, 3.2)
    bar -= Pos(-32, inv.BODY_W / 2 - WALL - 4, 101.6) * Cylinder(1.7, 5)
    return bar


def build_pico_clamp():
    bar = Pos(3, 63.5, 68.6) * Box(10, 49, 3.2)
    for jy in (43.0, 84.0):
        bar -= Pos(3, jy, 68.6) * Cylinder(1.7, 5)
    return bar


def build_battery_pad_frame():
    frame = Pos(30.5, 0, 51.5) * Box(96, 56, 1.0)
    frame -= Pos(30.5, 0, 51.5) * Box(60, 24, 2)
    return frame


def build_yoke():
    base = Pos(P.neck_x, 0, NECK_Z1 + 2.0) * Cylinder(21.5, 4)
    base -= Pos(P.neck_x, 0, NECK_Z1 + 2.0) * Cylinder(9.0, 6)
    yoke = base
    for sy in (1, -1):
        arm = Pos(-10, sy * 38, (NECK_Z1 + 4 + 250.0) / 2) * Box(10, 6, 250.0 - NECK_Z1 - 4)
        arm += Pos(P.neck_x + 4, sy * 38, NECK_Z1 + 6.0) * Box(24, 6, 8)
        arm -= Pos(-10, sy * 38, 245.0 + inv.DH) * Rot(90, 0, 0) * Cylinder(1.7, 10)
        yoke += arm
    return yoke


def build_tilt_bushing():
    b = Pos(0, 0, 1.5) * Cylinder(4.0, 3.0)
    b += Pos(0, 0, 3.3) * Cylinder(4.6, 0.6)
    b -= Pos(0, 0, 2) * Cylinder(1.75, 6)
    return b


def build_eye_diffuser_bar():
    bar = Pos(0, 0, 1.5) * Box(30, 18, 3)
    for sy in (1, -1):
        bar += Pos(0, sy * 5, 3.8) * Box(9, 5, 1.6)
    return bar


def build_status_diffuser_bar():
    bar = Pos(0, 0, 1.0) * Box(76, 12, 2)
    for sx in (1, -1):
        bar += Pos(sx * 30, 0, 2.6) * Box(10, 4, 1.2)
    return bar


def build_printed_washer():
    return Pos(0, 0, 0.8) * Cylinder(4.0, 1.6) - Pos(0, 0, 0.8) * Cylinder(1.75, 3)


def primary_solids():
    return {
        "tray_v2": build_tray(),
        "shell_v2": build_shell(),
        "lid_v2": build_lid(),
        "bumper_front_v2": build_bumper_half(front=True),
        "bumper_rear_v2": build_bumper_half(front=False),
        "front_pod_left_v2": build_front_pod(left=True),
        "front_pod_right_v2": build_front_pod(left=False),
        "fascia_v2": build_fascia(),
        "rear_panel_v2": build_rear_panel(),
        "controller_tower_v2": build_controller_tower(),
        "rear_wheel_v2": build_rear_wheel(),
        "front_wheel_v2": build_front_wheel(),
        "tire_v2": build_tire(),
        "head_shell_v2": build_head_shell(),
        "head_faceplate_v2": build_head_faceplate(),
        "neck_v2": build_neck(),
        "bayonet_collar_v2": build_bayonet_collar(),
        "head_pan_plate_v2": build_head_pan_plate(),
        "motor_cap_v2": build_motor_cap(),
        "battery_clamp_v2": build_battery_clamp(),
        "deck_v2": build_deck(),
        "mic_cradle_v2": build_mic_cradle(),
        "speaker_clamp_v2": build_speaker_clamp(),
        "tof_clamp_v2": build_tof_clamp(),
        "pico_clamp_v2": build_pico_clamp(),
        "battery_pad_frame_v2": build_battery_pad_frame(),
        "yoke_v2": build_yoke(),
        "tilt_bushing_v2": build_tilt_bushing(),
        "eye_diffuser_bar_v2": build_eye_diffuser_bar(),
        "status_diffuser_bar_v2": build_status_diffuser_bar(),
        "printed_washer_v2": build_printed_washer(),
    }


# Declared print orientation per part: UP is the model-space direction that
# points away from the bed in the print pose (D028 audits run against it).
PRINT_UP = {
    "tray_v2": (0, 0, 1),            # flat, bottom down
    "shell_v2": (0, 0, 1),           # upright, open bottom down
    "lid_v2": (0, 0, -1),            # top face down
    "bumper_front_v2": (0, 0, -1),   # upside down: U opens up on the bed
    "bumper_rear_v2": (0, 0, -1),
    "front_pod_left_v2": (0, -1, 0),   # inboard face down, axle rises vertically
    "front_pod_right_v2": (0, 1, 0),
    "fascia_v2": (-1, 0, 0),           # cosmetic face down
    "rear_panel_v2": (1, 0, 0),        # cosmetic face down
    "controller_tower_v2": (0, 0, 1),  # flat, legs up? no: plate down, columns up
    "rear_wheel_v2": (0, -1, 0),       # axis vertical
    "front_wheel_v2": (0, -1, 0),      # axis vertical
    "tire_v2": (0, -1, 0),             # flat ring
    "head_shell_v2": (1, 0, 0),        # open face down, dome rearward-up
    "head_faceplate_v2": (-1, 0, 0),   # cosmetic face down
    "neck_v2": (0, 0, -1),             # flange down
    "bayonet_collar_v2": (0, 0, 1),    # flat
    "head_pan_plate_v2": (0, 0, 1),    # flat
    "motor_cap_v2": (0, 0, -1),        # upside down: gripping arc opens up
    "battery_clamp_v2": (0, 0, 1),     # flat bar
    "deck_v2": (0, 0, -1),             # top face down: ribs and lips build up
    "mic_cradle_v2": (0, 0, 1), "speaker_clamp_v2": (0, 0, 1),
    "tof_clamp_v2": (0, 0, 1), "pico_clamp_v2": (0, 0, 1),
    "battery_pad_frame_v2": (0, 0, 1), "yoke_v2": (0, 0, 1),
    "tilt_bushing_v2": (0, 0, 1), "eye_diffuser_bar_v2": (0, 0, 1),
    "status_diffuser_bar_v2": (0, 0, 1), "printed_washer_v2": (0, 0, 1),
}
# Allowlisted overhang REGIONS per part (model-space boxes): declared
# printable features that exceed the generic 50-degree rule — the shell's
# dome-like top rollover, and the four arched wheel openings whose round
# crowns print as short arc bridges across the 18 mm wall band.
_ARCH_CROWNS = [
    (ax - ARCH_R - 2, ax + ARCH_R + 2, min(sy * 92.0, sy * 114.0),
     max(sy * 92.0, sy * 114.0), 96.0, 115.0)
    for ax in (inv.FRONT_AXLE_X, inv.REAR_AXLE_X) for sy in (1, -1)
]
OVERHANG_ALLOW_REGIONS = {
    "shell_v2": [(-inv.BODY_L, inv.BODY_L, -inv.BODY_W, inv.BODY_W,
                  inv.Z_TOP - ROLLOVER_R - 2.0, inv.Z_TOP + 1.0)] + _ARCH_CROWNS,
    # Head prints open-face-down (+X up): the rear dome (outside) and the
    # domed cavity crown (inside) are the allowlisted convex regions, like
    # the body shell's rollover.
    "head_shell_v2": [(HEAD_C[0] + P.head_depth / 2 - 18.0, HEAD_C[0] + P.head_depth / 2 + 2.0,
                       -P.head_width, P.head_width, 150.0, 320.0)],
}


def main():
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    for name, solid in primary_solids().items():
        bb = solid.bounding_box()
        print(f"{name}: bbox {bb.size.X:.1f} x {bb.size.Y:.1f} x {bb.size.Z:.1f}, "
              f"volume {solid.volume / 1000:.0f} cm3, solids {len(solid.solids())}")
        export_stl(solid, str(EXPORT_DIR / f"{name}.stl"))
        export_step(solid, str(EXPORT_DIR / f"{name}.step"))
    print(f"exported to {EXPORT_DIR}")


if __name__ == "__main__":
    main()
