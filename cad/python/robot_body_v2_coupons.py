"""Calibration coupons for the v2 printed-only hybrid-material body.

Print and pass these BEFORE any large v2 part, per the repo's build
order. Each coupon exercises one contract the v2 design leans on:

1. insert_m3        — three M3 insert bores at nominal and +/-0.1 to pick
                      the printer-specific fit for the single insert SKU.
2. joint_standard   — the D026 standard joint as a two-piece test: a
                      3.2 mm counterbored flange + an insert boss mate;
                      verifies the M3 x 8 clamp stack end to end.
3. dbore_torque     — a stub hub with the 4 mm D-bore and radial clamp
                      boss; mounts on the real #4867 motor for the
                      2x-stall-torque slip/creep test (D025 gate).
4. axle_bushing     — a stub printed axle + a bushing ring: the front
                      wheel bearing interface wear test (D025 gate).
5. snap_pair        — cantilever snap + socket strips for the fascia,
                      rear panel, and vent-style cosmetic joints.
6. bayonet_pair     — a mini bayonet collar + neck stub for the head
                      retention interface.
7. switch_pocket    — a tray-underside slice with one molded switch
                      pocket and plunger window at the 0.4/2.0/2.4 mm
                      bumper interface values (D028 merge risk gate).
8. tire_fit         — a 40%-scale wheel + TPU ring pair for tire
                      stretch/seat calibration.
9. pcb_clamp        — pocket + pegs + clamp bar sized to the Pico 2 (the
                      cheapest real board) proving the capture-don't-
                      screw pattern before the Pi cradle prints.
10. pla_insert      — production shell-style PLA boss and insert bore.
11. pla_shell_wall  — representative shell wall, rollover/opening, and
                      panel-interface edge.
12. pla_head_pivot  — production tilt-pivot wall/boss stack in PLA.
13. pla_snap        — visible-panel, diffuser, and lid-skin snap cycling.
14. pla_optical     — three optical thickness windows; print once per
                      candidate translucent PLA family/color.
15. lid_boundary    — paired white-PETG socket and teal-PLA tab coupons.

Run from the repo root:
    .venv-cad/bin/python cad/python/robot_body_v2_coupons.py
Exports (STL + manifest) land under cad/exports/v2/coupons/.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import robot_body_v2_inventory as inv  # noqa: E402
from build123d import Axis, Box, Cylinder, Pos, Rot, fillet, export_stl  # noqa: E402

P = inv.P
EXPORT_DIR = Path(__file__).resolve().parents[2] / "cad" / "exports" / "v2" / "coupons"
F = inv.FASTENER


def pad(l, w, h):
    b = Box(l, w, h)
    return Pos(0, 0, h / 2) * fillet(b.edges().filter_by(Axis.Z), 3.0)


def insert_m3():
    c = pad(46, 16, 8)
    for i, d in enumerate((F["insert_bore"] - 0.1, F["insert_bore"], F["insert_bore"] + 0.1)):
        c -= Pos(-14 + i * 14, 0, 8 - 3.5) * Cylinder(d / 2, 7)
    return c


def joint_standard_flange():
    c = pad(24, 16, 3.2)
    c -= Pos(0, 0, 1.6) * Cylinder(F["clearance_hole"] / 2, 4)
    return c


def joint_standard_boss():
    c = pad(24, 16, 10)
    c -= Pos(0, 0, 10 - 3.5) * Cylinder(F["insert_bore"] / 2, 7)
    return c


def dbore_torque():
    hub = Pos(0, 0, 9) * Cylinder(14, 18)
    bore = Pos(0, 0, 9) * Cylinder(2.05, 20)
    bore -= Pos(0, 3.55, 9) * Box(6, 4, 22)          # D-flat: torque is geometric
    hub -= bore
    hub += Pos(0, 9, 9) * Box(10, 10, 18)             # radial clamp boss
    hub -= Pos(0, 12, 9) * Rot(90, 0, 0) * Cylinder(F["insert_bore"] / 2, 7)
    return hub


def axle_stub():
    base = pad(30, 30, 6)
    base += Pos(0, 0, 6 + 12) * Cylinder(9.0, 24)     # the front stub axle section
    base -= Pos(0, 0, 6 + 24 - 5.5) * Cylinder(2.3, 6)
    return base


def bushing_ring():
    ring = Pos(0, 0, 6) * Cylinder(9.25 + 3.0, 12)
    ring -= Pos(0, 0, 6) * Cylinder(9.25, 14)          # wheel-bore wear surface
    return ring


def snap_pair():
    male = pad(30, 12, 3)
    male += Pos(0, 0, 3 + 3) * Box(3, 8, 6)
    male += Pos(1.8, 0, 3 + 6.5) * Box(1.5, 8, 1.5)    # snap hook
    female = Pos(0, 24, 0) * (pad(30, 12, 8) - Pos(0, 0, 5.5) * Box(3.6, 8.6, 8))
    return male + female


def bayonet_pair():
    collar = Pos(0, 0, 3) * Cylinder(20, 6) - Pos(0, 0, 3) * Cylinder(15.5, 8)
    for a in (0, 120, 240):
        collar -= Rot(0, 0, a) * Pos(0, 17.5, 4.5) * Box(6, 5, 4)   # bayonet gates
    stub = Pos(48, 0, 4) * (Cylinder(15, 8) - Cylinder(10, 10))
    for a in (0, 120, 240):
        stub += Pos(48, 0, 6.5) * Rot(0, 0, a) * Pos(0, 16.2, 0) * Box(5.4, 3, 3)  # lugs
    return collar + stub


def switch_pocket():
    slab = pad(46, 60, P.tray_thickness)
    slab -= Pos(0, 0, 3.0) * Box(24, 42, 6.0)          # the molded pocket
    slab -= Pos(-17, 0, 3.0) * Box(20, 12, 6.0)        # plunger window
    return slab


def tire_fit():
    core = Pos(0, 0, 5) * Cylinder(21.0 * 0.4 + 8, 10)
    ring = Pos(60, 0, 5) * (Cylinder(P.wheel_radius * 0.4, 10) - Cylinder(20.8 * 0.4 + 8 - 8, 12))
    return core + ring


def pcb_clamp():
    base = pad(70, 40, 8)
    base -= Pos(0, 0, 8 - 1.5) * Box(P.pico2_board_length + 0.6, P.pico2_board_width + 0.6, 3.1)
    for sx in (1, -1):
        for sy in (1, -1):
            base += Pos(sx * P.pico2_mount_spacing_length / 2,
                        sy * P.pico2_mount_spacing_width / 2, 8 + 0.9) * Cylinder(0.95, 1.8)
    for sx in (1, -1):
        base -= Pos(sx * 30, 0, 8 - 3.5) * Cylinder(F["insert_bore"] / 2, 7)
    bar = Pos(0, 60, 1.6) * Box(66, 10, 3.2)
    for sx in (1, -1):
        bar -= Pos(sx * 30, 60, 1.6) * Cylinder(F["clearance_hole"] / 2, 4)
    return base + bar


def pla_insert_shell():
    wall = pad(34, 24, inv.WALL)
    boss = Pos(0, 0, (inv.WALL + 10.0) / 2) * Cylinder(7.0, 10.0 - inv.WALL)
    boss -= Pos(0, 0, 10.0 - 3.5) * Cylinder(F["insert_bore"] / 2, 7)
    return wall + boss


def pla_shell_wall():
    # A 3.2 mm shell strip with a rounded opening edge, a 12 mm exterior
    # rollover sample, and a 1.5 mm flush-panel seat at one end.
    wall = pad(74, 44, inv.WALL)
    wall -= Pos(-12, 0, inv.WALL / 2) * Cylinder(12, inv.WALL + 2)
    rollover = Pos(18, 0, inv.WALL + 5) * Box(20, 30, 10)
    rollover = fillet(rollover.edges().filter_by(Axis.Y), 4.5)
    wall += rollover
    wall -= Pos(33, 0, inv.WALL - 0.7) * Box(12, 28, 1.5)
    return wall


def pla_head_pivot():
    wall = pad(42, 36, 5.0)
    boss = Pos(0, 0, 10.0) * Cylinder(8.0, 15.0)
    boss -= Pos(0, 0, 10.0) * Cylinder(F["insert_bore"] / 2, 17)
    # Bushing-side shoulder wall representative of the passive pivot.
    boss += Pos(0, 0, 17.0) * Cylinder(11.0, 3.0)
    boss -= Pos(0, 0, 17.0) * Cylinder(4.1, 5.0)
    return wall + boss


def pla_optical():
    # Three labeled-by-position windows: 1.2, 1.6, 2.0 mm. The adjacent
    # camera aperture lets the builder inspect flare/hot spots, not just
    # brightness on a workbench.
    base = pad(84, 28, 2.0)
    base -= Pos(0, 0, 1.0) * Cylinder(6.5, 4)
    for x, h in ((-30, 1.2), (0, 1.6), (30, 2.0)):
        base += Pos(x, 0, 2.0 + h / 2) * Box(14, 10, h)
    return base


def lid_boundary_petg():
    c = pad(34, 22, 4.0)
    c -= Pos(0, 0, 3.45) * Box(5.4, 1.55, 1.2)
    c -= Pos(0, 0, 2.65) * Box(5.4, 2.05, 0.6)
    return c


def lid_boundary_pla():
    tab = pad(34, 22, 1.2)
    tab += Pos(0, 0, 0.6 + 0.6) * Box(5.0, 1.25, 1.2)
    tab += Pos(0, 0, 1.95) * Box(5.0, 1.75, 0.3)
    return tab


COUPONS = {
    "coupon_insert_m3": (insert_m3, "PETG", "insert fit: drive one insert per bore, pick the station that seats flush without melt squeeze-out"),
    "coupon_joint_flange": (joint_standard_flange, "PETG", "with coupon_joint_boss: M3x8 through the counterbored flange; verify 3.2 clamp, full seat, no bottoming"),
    "coupon_joint_boss": (joint_standard_boss, "PETG", "mate of coupon_joint_flange"),
    "coupon_dbore_torque": (dbore_torque, "PETG", "mount on the #4867 shaft: hold 2x extrapolated stall (22 kg-cm) without slip or creep, warm and cold (D025 gate)"),
    "coupon_axle_stub": (axle_stub, "PETG", "with coupon_bushing_ring: spin under ~1 kg radial load; measure slop growth over a carpet-equivalent drag distance (D025 gate)"),
    "coupon_bushing_ring": (bushing_ring, "PETG", "wear ring for coupon_axle_stub; grease PETG-safe"),
    "coupon_snap_pair": (snap_pair, "PETG", "10 insert/release cycles; hook must survive and retention must stay positive"),
    "coupon_bayonet_pair": (bayonet_pair, "PETG", "head-retention interface: engage/disengage feel, no ratcheting under axial pull"),
    "coupon_switch_pocket": (switch_pocket, "PETG", "seat one D2HW switch; verify the 0.4 rest gap / 2.0 stroke / 2.4 stop interface before committing the tray print"),
    "coupon_tire_fit": (tire_fit, "TPU+PETG", "print the ring in TPU, the core in PETG; calibrate tire stretch and seat retention at 40% scale"),
    "coupon_pcb_clamp": (pcb_clamp, "PETG", "drop in the Pico 2, verify peg engagement without board stress, clamp bar seats at 3.2 stack"),
    "coupon_pla_insert_shell": (pla_insert_shell, "PLA", "production shell-style boss: record insert temperature, whitening/cracks/sink/tilt, pull-through, and M3x8 engagement for this exact PLA family"),
    "coupon_pla_shell_wall": (pla_shell_wall, "PLA", "representative 3.2 wall, rollover/opening, and panel seat: record dimensions, impact result, warm soak, and post-cool distortion"),
    "coupon_pla_head_pivot": (pla_head_pivot, "PLA", "production-like tilt-pivot boss/wall: install insert and bushing, cycle under representative head load, inspect cracks and slop"),
    "coupon_pla_snap_pair": (snap_pair, "PLA", "print in each candidate visible PLA family; 10 service cycles with full latch engagement and no whitening, fracture, or retention loss"),
    "coupon_pla_optical": (pla_optical, "Translucent PLA", "print once per candidate family/color; record brightness, hot spots, camera flare, clip fit, and LED temperature at 1.2/1.6/2.0 mm"),
    "coupon_lid_boundary_petg": (lid_boundary_petg, "White PETG", "mate with coupon_lid_boundary_pla; verify blind-socket fit, retention, removal, and no socket cracking"),
    "coupon_lid_boundary_pla": (lid_boundary_pla, "Teal PLA", "mate with coupon_lid_boundary_petg; 10 remove/refit cycles, then warm soak and rattle check"),
}

PROCESS_RECORD = {
    "manufacturer": None,
    "product_line": None,
    "material_subtype": None,
    "color": None,
    "nozzle_mm": 0.4,
    "layer_height_mm": 0.2,
    "wall_count": 4,
    "insert_tool_temperature_c": None,
    "measured_results": None,
    "pass_fail": None,
    "tested_by": None,
    "test_date": None,
}


def main():
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    manifest = {}
    for name, (fn, material, note) in COUPONS.items():
        solid = fn()
        bb = solid.bounding_box()
        export_stl(solid, str(EXPORT_DIR / f"{name}.stl"))
        manifest[name] = {
            "material": material,
            "span_mm": [round(bb.size.X, 1), round(bb.size.Y, 1), round(bb.size.Z, 1)],
            "supports": "none",
            "note": note,
            "physical_evidence_status": "open",
            "process_record": dict(PROCESS_RECORD),
        }
        print(f"{name}: {bb.size.X:.0f} x {bb.size.Y:.0f} x {bb.size.Z:.0f}  [{material}]")
    (EXPORT_DIR / "codex_robot_body_v2_coupons_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"{len(COUPONS)} coupons exported to {EXPORT_DIR}")


if __name__ == "__main__":
    main()
