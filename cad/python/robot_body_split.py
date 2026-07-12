"""Printer-aware split variants for the build123d robot body.

The default variant targets the Bambu Lab P1S's nominal 256 mm square bed with
an 8 mm safety margin. Large body parts are clipped into the same inventory
used by the main assembly and remain compatible with a 220 mm bed when that
size is selected explicitly. Small printed bridge plates are exported for
screw-together seams. The bridges are not safety-critical load paths; the real
battery, motor, axle, and E-stop loads still require hardware-backed retention.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from build123d import Align, Box, Compound, Cylinder, Location, export_step, export_stl

try:
    from robot_body import (
        EXPORT_DIR,
        Params,
        audio_mounts,
        base_tray,
        battery_cradle,
        bumper_carrier,
        bumper_center_z,
        bumper_inner_length,
        bumper_inner_width,
        bumper_switch_mounts,
        electronics_mounts,
        estop_backing_plate,
        front_idler_pods,
        motor_pods,
        power_harness_rails,
        lid_and_top_details,
        body_shell,
        cylinder_x,
        cylinder_y,
        cylinder_z,
        side_fairings,
        rounded_box,
        tof_sensor_pods,
    )
except ModuleNotFoundError:
    from cad.python.robot_body import (
        EXPORT_DIR,
        Params,
        audio_mounts,
        base_tray,
        battery_cradle,
        bumper_carrier,
        bumper_center_z,
        bumper_inner_length,
        bumper_inner_width,
        bumper_switch_mounts,
        electronics_mounts,
        estop_backing_plate,
        front_idler_pods,
        motor_pods,
        power_harness_rails,
        lid_and_top_details,
        body_shell,
        cylinder_x,
        cylinder_y,
        cylinder_z,
        side_fairings,
        rounded_box,
        tof_sensor_pods,
    )


def clip(shape, x0, x1, y0, y1, z0, z1):
    cutter = Box(
        x1 - x0,
        y1 - y0,
        z1 - z0,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    ).moved(Location(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)))
    return shape & cutter


def bridge_box(length, width, height, xyz, holes=(), hole_radius=2.3):
    shape = Box(
        length,
        width,
        height,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    ).moved(Location(xyz))
    for dx, dy in holes:
        hole = Cylinder(
            hole_radius,
            height + 6,
            align=(Align.CENTER, Align.CENTER, Align.CENTER),
        ).moved(Location((xyz[0] + dx, xyz[1] + dy, xyz[2])))
        shape = shape - hole
    return shape


def plate_xz(length, depth, height, xyz, holes=(), hole_radius=2.3):
    """Vertical seam plate normal to Y with holes specified as X/Z offsets."""
    shape = rounded_box(length, depth, height, 2.0, xyz)
    for dx, dz in holes:
        shape = shape - cylinder_y(
            hole_radius,
            depth + 6.0,
            (xyz[0] + dx, xyz[1], xyz[2] + dz),
        )
    return shape


def plate_yz(depth, width, height, xyz, holes=(), hole_radius=2.3):
    """Vertical seam plate normal to X with holes specified as Y/Z offsets."""
    shape = rounded_box(depth, width, height, 2.0, xyz)
    for dy, dz in holes:
        shape = shape - cylinder_x(
            hole_radius,
            depth + 6.0,
            (xyz[0], xyz[1] + dy, xyz[2] + dz),
        )
    return shape


def split_quadrants(shape, x_bounds, y_bounds, z_bounds, prefix):
    out = {}
    x_labels = (("front", x_bounds[0], x_bounds[1]), ("rear", x_bounds[1], x_bounds[2]))
    y_labels = (("left", y_bounds[0], y_bounds[1]), ("right", y_bounds[1], y_bounds[2]))
    for x_name, x0, x1 in x_labels:
        for y_name, y0, y1 in y_labels:
            out[f"{prefix}_{x_name}_{y_name}"] = clip(
                shape,
                x0,
                x1,
                y0,
                y1,
                z_bounds[0],
                z_bounds[1],
            )
    return out


def alignment_pilot_interfaces(p: Params):
    """Hidden plate pilots and the split pieces receiving their recesses."""
    shell_plate_z = p.body_bottom + 18.0
    shell_side_inner = p.body_width / 2.0 - p.wall
    shell_end_inner = p.body_length / 2.0 - p.wall
    bumper_side_plate_z = bumper_center_z(p) + 4.0
    bumper_end_plate_z = bumper_center_z(p) - 3.0
    bumper_side_inner = bumper_inner_width(p) / 2.0
    bumper_end_inner = bumper_inner_length(p) / 2.0
    tray_bottom = p.body_bottom - p.tray_thickness

    return (
        {
            "group": "body",
            "plate": "body_seam_plate_side_left",
            "axis": "y",
            "face": -shell_side_inner,
            "outward_sign": -1,
            "points": ((0.0, shell_plate_z - 7.0), (0.0, shell_plate_z + 7.0)),
            "targets": ("body_shell_q_front_left", "body_shell_q_rear_left"),
        },
        {
            "group": "body",
            "plate": "body_seam_plate_side_right",
            "axis": "y",
            "face": shell_side_inner,
            "outward_sign": 1,
            "points": ((0.0, shell_plate_z - 7.0), (0.0, shell_plate_z + 7.0)),
            "targets": ("body_shell_q_front_right", "body_shell_q_rear_right"),
        },
        {
            "group": "body",
            "plate": "body_seam_plate_end_front",
            "axis": "x",
            "face": -shell_end_inner,
            "outward_sign": -1,
            "points": ((0.0, shell_plate_z - 7.0), (0.0, shell_plate_z + 7.0)),
            "targets": ("body_shell_q_front_left", "body_shell_q_front_right"),
        },
        {
            "group": "body",
            "plate": "body_seam_plate_end_rear",
            "axis": "x",
            "face": shell_end_inner,
            "outward_sign": 1,
            "points": ((0.0, shell_plate_z - 7.0), (0.0, shell_plate_z + 7.0)),
            "targets": ("body_shell_q_rear_left", "body_shell_q_rear_right"),
        },
        {
            "group": "base",
            "plate": "base_seam_plate",
            "axis": "z",
            "face": tray_bottom,
            "outward_sign": 1,
            "points": ((0.0, -50.0), (0.0, 50.0)),
            "targets": ("base_tray_half_front", "base_tray_half_rear"),
        },
        {
            "group": "bumper",
            "plate": "bumper_seam_plate_side_left",
            "axis": "y",
            "face": -bumper_side_inner,
            "outward_sign": -1,
            "points": ((0.0, bumper_side_plate_z - 4.0), (0.0, bumper_side_plate_z + 4.0)),
            "targets": ("bumper_q_front_left", "bumper_q_rear_left"),
        },
        {
            "group": "bumper",
            "plate": "bumper_seam_plate_side_right",
            "axis": "y",
            "face": bumper_side_inner,
            "outward_sign": 1,
            "points": ((0.0, bumper_side_plate_z - 4.0), (0.0, bumper_side_plate_z + 4.0)),
            "targets": ("bumper_q_front_right", "bumper_q_rear_right"),
        },
        {
            "group": "bumper",
            "plate": "bumper_seam_plate_end_front",
            "axis": "x",
            "face": -bumper_end_inner,
            "outward_sign": -1,
            "points": ((0.0, bumper_end_plate_z - 4.0), (0.0, bumper_end_plate_z + 4.0)),
            "targets": ("bumper_q_front_left", "bumper_q_front_right"),
        },
        {
            "group": "bumper",
            "plate": "bumper_seam_plate_end_rear",
            "axis": "x",
            "face": bumper_end_inner,
            "outward_sign": 1,
            "points": ((0.0, bumper_end_plate_z - 4.0), (0.0, bumper_end_plate_z + 4.0)),
            "targets": ("bumper_q_rear_left", "bumper_q_rear_right"),
        },
    )


def alignment_pilot_shape(p: Params, interface, point, recess: bool = False):
    radius = p.split_pilot_radius + (p.split_pilot_radial_clearance if recess else 0.0)
    length = p.split_pilot_length + (p.split_pilot_axial_clearance if recess else 0.0)
    center_axis = interface["face"] + interface["outward_sign"] * (
        length / 2.0 - p.split_pilot_overlap
    )
    if interface["axis"] == "x":
        return cylinder_x(radius, length, (center_axis, point[0], point[1]))
    if interface["axis"] == "y":
        return cylinder_y(radius, length, (point[0], center_axis, point[1]))
    return cylinder_z(radius, length, (point[0], point[1], center_axis))


def add_alignment_pilots(p: Params, plate_name: str, plate):
    for interface in alignment_pilot_interfaces(p):
        if interface["plate"] != plate_name:
            continue
        for point in interface["points"]:
            plate = plate + alignment_pilot_shape(p, interface, point)
    return plate


def cut_alignment_recesses(p: Params, group: str, shape):
    for interface in alignment_pilot_interfaces(p):
        if interface["group"] != group:
            continue
        for point in interface["points"]:
            shape = shape - alignment_pilot_shape(p, interface, point, recess=True)
    return shape


def split_parts(p: Params):
    parts = {}
    body = body_shell(p)

    # Four low internal plates span the vertical shell seams. The plates carry
    # heat-set inserts; matching clearance holes are drilled only in the split
    # shell variant, keeping the one-piece shell visually clean.
    shell_plate_z = p.body_bottom + 18.0
    shell_holes = ((-18.0, -7.0), (-18.0, 7.0), (18.0, -7.0), (18.0, 7.0))
    shell_side_inner = p.body_width / 2.0 - p.wall
    for side, sign in (("left", -1), ("right", 1)):
        plate_y = sign * (shell_side_inner - 3.5)
        wall_y = sign * (p.body_width / 2.0 - 1.0)
        for dx, dz in shell_holes:
            body = body - cylinder_y(
                p.m3_clearance_hole / 2.0,
                16.0,
                (dx, wall_y, shell_plate_z + dz),
            )
        plate_name = f"body_seam_plate_side_{side}"
        plate = plate_xz(
            56.0,
            7.0,
            30.0,
            (0.0, plate_y, shell_plate_z),
            holes=shell_holes,
            hole_radius=p.insert_hole_m3 / 2.0,
        )
        parts[plate_name] = add_alignment_pilots(p, plate_name, plate)

    shell_end_inner = p.body_length / 2.0 - p.wall
    for end, sign in (("front", -1), ("rear", 1)):
        plate_x = sign * (shell_end_inner - 3.5)
        wall_x = sign * (p.body_length / 2.0 - 1.0)
        for dy, dz in shell_holes:
            body = body - cylinder_x(
                p.m3_clearance_hole / 2.0,
                16.0,
                (wall_x, dy, shell_plate_z + dz),
            )
        plate_name = f"body_seam_plate_end_{end}"
        plate = plate_yz(
            7.0,
            56.0,
            30.0,
            (plate_x, 0.0, shell_plate_z),
            holes=shell_holes,
            hole_radius=p.insert_hole_m3 / 2.0,
        )
        parts[plate_name] = add_alignment_pilots(p, plate_name, plate)

    body = cut_alignment_recesses(p, "body", body)
    body_z = (p.body_bottom - 1, p.body_bottom + p.body_height + 2)
    parts.update(
        split_quadrants(
            body,
            (-p.body_length / 2, 0, p.body_length / 2),
            (-p.body_width / 2, 0, p.body_width / 2),
            body_z,
            "body_shell_q",
        )
    )
    parts["battery_cradle"] = battery_cradle(p)
    parts.update(motor_pods(p))
    parts.update(front_idler_pods(p))
    parts.update(audio_mounts(p))
    parts.update(tof_sensor_pods(p))
    parts.update(electronics_mounts(p))
    parts.update(power_harness_rails(p))
    parts.update(bumper_switch_mounts(p))
    parts["estop_backing_plate"] = estop_backing_plate(p)

    tray = base_tray(p)
    base_seam_holes = tuple(
        (x, y)
        for x in (-14.0, 14.0)
        for y in (-70.0, -25.0, 25.0, 70.0)
    )
    for x, y in base_seam_holes:
        tray = tray - cylinder_z(
            p.insert_hole_m3 / 2.0,
            16.0,
            (x, y, p.body_bottom - p.tray_thickness / 2.0),
        )
    tray = cut_alignment_recesses(p, "base", tray)
    tray_z = (p.body_bottom - p.tray_thickness - 2, p.body_bottom + 8)
    tray_x = (p.body_length - 8) / 2.0
    tray_y = (p.body_width - 8) / 2.0
    parts["base_tray_half_front"] = clip(
        tray,
        -tray_x,
        0.0,
        -tray_y,
        tray_y,
        *tray_z,
    )
    parts["base_tray_half_rear"] = clip(
        tray,
        0.0,
        tray_x,
        -tray_y,
        tray_y,
        *tray_z,
    )
    base_plate = bridge_box(
        42.0,
        168.0,
        4.0,
        (0.0, 0.0, p.body_bottom - p.tray_thickness - 2.0),
        holes=base_seam_holes,
        hole_radius=p.m3_clearance_hole / 2.0,
    )
    parts["base_seam_plate"] = add_alignment_pilots(
        p,
        "base_seam_plate",
        base_plate,
    )

    bumper = bumper_carrier(p)
    bumper_side_plate_z = bumper_center_z(p) + 4.0
    bumper_end_plate_z = bumper_center_z(p) - 3.0
    bumper_side_inner = bumper_inner_width(p) / 2.0
    for side, sign in (("left", -1), ("right", 1)):
        plate_y = sign * (bumper_side_inner - 3.5)
        wall_y = sign * (p.bumper_width / 2.0 - 8.5)
        for x in (-18.0, 18.0):
            bumper = bumper - cylinder_y(
                p.m3_clearance_hole / 2.0,
                30.0,
                (x, wall_y, bumper_side_plate_z),
            )
        plate_name = f"bumper_seam_plate_side_{side}"
        plate = plate_xz(
            56.0,
            7.0,
            14.0,
            (0.0, plate_y, bumper_side_plate_z),
            holes=((-18.0, 0.0), (18.0, 0.0)),
            hole_radius=p.insert_hole_m3 / 2.0,
        )
        parts[plate_name] = add_alignment_pilots(p, plate_name, plate)

    bumper_end_inner = bumper_inner_length(p) / 2.0
    for end, sign in (("front", -1), ("rear", 1)):
        plate_x = sign * (bumper_end_inner - 3.5)
        wall_x = sign * (p.bumper_length / 2.0 - 8.5)
        for y in (-18.0, 18.0):
            bumper = bumper - cylinder_x(
                p.m3_clearance_hole / 2.0,
                30.0,
                (wall_x, y, bumper_end_plate_z),
            )
        plate_name = f"bumper_seam_plate_end_{end}"
        plate = plate_yz(
            7.0,
            56.0,
            14.0,
            (plate_x, 0.0, bumper_end_plate_z),
            holes=((-18.0, 0.0), (18.0, 0.0)),
            hole_radius=p.insert_hole_m3 / 2.0,
        )
        parts[plate_name] = add_alignment_pilots(p, plate_name, plate)

    bumper = cut_alignment_recesses(p, "bumper", bumper)
    bumper_z = (
        bumper_center_z(p) - p.bumper_height / 2.0 - 4.0,
        bumper_center_z(p) + p.bumper_height / 2.0 + 4.0,
    )
    parts.update(
        split_quadrants(
            bumper,
            (-p.bumper_length / 2, 0, p.bumper_length / 2),
            (-p.bumper_width / 2, 0, p.bumper_width / 2),
            bumper_z,
            "bumper_q",
        )
    )

    for side, fairing in side_fairings(p).items():
        parts[f"{side}_front"] = clip(
            fairing,
            -p.body_length / 2,
            0,
            -p.body_width / 2 - 8,
            p.body_width / 2 + 8,
            50,
            140,
        )
        parts[f"{side}_rear"] = clip(
            fairing,
            0,
            p.body_length / 2,
            -p.body_width / 2 - 8,
            p.body_width / 2 + 8,
            50,
            140,
        )

    reveal, lid, _, _, _, _ = lid_and_top_details(p)
    lid_x = p.lid_length / 2
    lid_y = p.lid_width / 2
    lid_z = (
        p.body_bottom + p.body_height + 1 - p.vent_inlay_bridge_height,
        p.body_bottom + p.body_height + 8,
    )
    lid_mid_z = p.body_bottom + p.body_height + 3.0
    lap_end_x = p.lid_split_x + p.lid_lap_length
    front_core = clip(lid, -lid_x, p.lid_split_x, -lid_y, lid_y, *lid_z)
    front_tongue = clip(
        lid,
        p.lid_split_x,
        lap_end_x,
        -lid_y,
        lid_y,
        lid_z[0],
        lid_mid_z,
    )
    rear_core = clip(lid, lap_end_x, lid_x, -lid_y, lid_y, *lid_z)
    rear_lip = clip(
        lid,
        p.lid_split_x,
        lap_end_x,
        -lid_y,
        lid_y,
        lid_mid_z,
        lid_z[1],
    )
    parts["top_lid_half_front"] = front_core + front_tongue
    parts["top_lid_half_rear"] = rear_core + rear_lip

    reveal_x = (p.lid_length + 8) / 2.0
    reveal_y = (p.lid_width + 8) / 2.0
    reveal_z = (p.body_bottom + p.body_height - 1, p.body_bottom + p.body_height + 2)
    parts["lid_reveal_half_front"] = clip(
        reveal,
        -reveal_x,
        p.lid_split_x,
        -reveal_y,
        reveal_y,
        *reveal_z,
    )
    parts["lid_reveal_half_rear"] = clip(
        reveal,
        p.lid_split_x,
        reveal_x,
        -reveal_y,
        reveal_y,
        *reveal_z,
    )

    return parts


def export_split(p: Params, bed: float, margin: float):
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    manifest_path = EXPORT_DIR / "codex_robot_body_v1_split_manifest.json"
    if manifest_path.exists():
        try:
            previous = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            previous = {}
        for name in previous.get("parts", {}):
            stale_path = EXPORT_DIR / f"{name}.stl"
            if stale_path.exists():
                stale_path.unlink()

    parts = split_parts(p)
    max_print = bed - margin
    manifest = {
        "units": "mm",
        "source": "cad/python/robot_body_split.py",
        "bed_nominal_mm": bed,
        "margin_mm": margin,
        "max_allowed_part_span_mm": max_print,
        "assembly_groups": {
            "body_shell": {
                "pieces": [
                    "body_shell_q_front_left",
                    "body_shell_q_front_right",
                    "body_shell_q_rear_left",
                    "body_shell_q_rear_right",
                ],
                "joiners": [
                    "body_seam_plate_side_left",
                    "body_seam_plate_side_right",
                    "body_seam_plate_end_front",
                    "body_seam_plate_end_rear",
                ],
                "m3_fasteners": 16,
                "alignment_pilots": 8,
                "note": "Eight concealed pilots self-register the four plates before fastening; the scalloped fairings clear this lower seam and mount independently above it.",
            },
            "base_tray": {
                "pieces": ["base_tray_half_front", "base_tray_half_rear"],
                "joiners": ["base_seam_plate"],
                "m3_fasteners": 8,
                "alignment_pilots": 2,
                "carry_hardware": {
                    "webbing_handles": 2,
                    "metal_clamp_plates": 2,
                    "m4_through_bolts": 8,
                    "m4_washers": 16,
                    "m4_locknuts": 8,
                },
                "note": "Each metal carry plate bridges X=0 and through-bolts both tray halves; it supplements rather than replaces the underside M3 seam plate.",
            },
            "bumper": {
                "pieces": [
                    "bumper_q_front_left",
                    "bumper_q_front_right",
                    "bumper_q_rear_left",
                    "bumper_q_rear_right",
                ],
                "joiners": [
                    "bumper_seam_plate_side_left",
                    "bumper_seam_plate_side_right",
                    "bumper_seam_plate_end_front",
                    "bumper_seam_plate_end_rear",
                ],
                "m3_fasteners": 8,
                "alignment_pilots": 8,
            },
            "top_lid": {
                "pieces": ["top_lid_half_front", "top_lid_half_rear"],
                "captured_gasket": ["lid_reveal_half_front", "lid_reveal_half_rear"],
                "m3_fasteners_to_shell": 4,
                "note": "The 12 mm stepped lap aligns the lid seam without a hidden bridge.",
            },
            "side_fairings": {
                "pieces": [
                    "side_fairing_left_front",
                    "side_fairing_left_rear",
                    "side_fairing_right_front",
                    "side_fairing_right_rear",
                ],
                "dedicated_m3_fasteners": 8,
                "shared_body_seam_fasteners": 0,
                "note": "Each half is an independently removable 2 mm wheel-arch skin seated flush in the shared 2.2 mm shell recess; a large center relief exposes the molded shell and clears the lower body seam.",
            },
            "mobility_pods": {
                "pieces": [
                    "motor_pod_left",
                    "motor_pod_right",
                    "motor_pod_cover_left",
                    "motor_pod_cover_right",
                    "front_idler_pod_left",
                    "front_idler_pod_right",
                    "front_idler_retainer_left_inner",
                    "front_idler_retainer_left_outer",
                    "front_idler_retainer_right_inner",
                    "front_idler_retainer_right_outer",
                ],
                "m3_fasteners_to_tray": 16,
                "m3_motor_cover_fasteners": 8,
                "m2_5_bearing_retainer_fasteners": 8,
                "front_idler_hardware": "Two 608-class bearings, four M2.5 retainer screws, and one positively retained 8 mm metal shaft per side.",
                "note": "The front pods are a removable two-motor skid-support baseline and may be swapped after cornering tests.",
            },
            "estop_mount": {
                "pieces": ["estop_backing_plate"],
                "m3_fasteners": 4,
                "m3_heat_set_inserts": 4,
                "primary_switch_retention": "purchased panel-switch nut",
                "note": "Four diagonal shell-rooted bosses and the raised backing collar support the switch; release remains blocked on the purchased drawing and physical push/twist test.",
            },
            "power_harness": {
                "pieces": ["power_harness_rail_left", "power_harness_rail_right"],
                "reusable_strap_stations_per_rail": 4,
                "bundle_assignment": {
                    "left": "signal_audio_sensor",
                    "right": "fused_switched_power_motor",
                },
                "note": "Each rail is captured to the removable power deck through four paired rounded slots; measure real bundle diameters and connector exits before release.",
            },
        },
        "alignment_pilot_contract": {
            "count": 18,
            "diameter_mm": 2.0 * p.split_pilot_radius,
            "projection_mm": p.split_pilot_length - p.split_pilot_overlap,
            "radial_clearance_mm": p.split_pilot_radial_clearance,
            "axial_clearance_mm": p.split_pilot_axial_clearance,
            "body_shell_exterior_wall_remaining_mm": p.wall
            - (
                p.split_pilot_length
                + p.split_pilot_axial_clearance
                - p.split_pilot_overlap
            ),
            "print_gate": "Print and repeatedly assemble one representative pilot/recess interface before committing the large shell and tray parts.",
        },
        "provisional_hardware": {
            "unique_m3_split_assembly_fasteners": 44,
            "m3_heat_set_inserts": 44,
            "warning": "Choose screw lengths only after measuring the purchased inserts and printed coupons. Pilot fit requires a physical print test; carry hardware dimensions and working load require a loaded lift test.",
        },
        "parts": {},
    }
    for name, shape in parts.items():
        if not shape.is_valid:
            raise ValueError(f"Invalid split part: {name}")
        box = shape.bounding_box()
        spans = {
            "x": float(box.max.X - box.min.X),
            "y": float(box.max.Y - box.min.Y),
            "z": float(box.max.Z - box.min.Z),
        }
        if max(spans["x"], spans["y"]) > max_print + 0.01:
            raise ValueError(f"{name} exceeds the nominal bed: {spans}")
        export_stl(shape, EXPORT_DIR / f"{name}.stl")
        manifest["parts"][name] = {"span_mm": spans, "solids": len(shape.solids())}

    export_step(Compound(list(parts.values())), EXPORT_DIR / "codex_robot_body_v1_split.step")
    manifest_path.write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Exported {len(parts)} split-print parts to {EXPORT_DIR}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bed", type=float, default=256.0)
    parser.add_argument("--margin", type=float, default=8.0)
    args = parser.parse_args()
    export_split(Params(), args.bed, args.margin)


if __name__ == "__main__":
    main()
