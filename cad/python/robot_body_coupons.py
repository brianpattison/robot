"""Generate small calibration coupons for the robot body's critical interfaces."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from build123d import Axis, Location, export_stl

try:
    from robot_body import (
        EXPORT_DIR,
        Params,
        base_tray,
        body_shell,
        bumper_carrier,
        bumper_switch_contact_patch,
        bumper_switch_body_mount_positions,
        bumper_switch_layout,
        bumper_switch_mount_positions,
        bumper_switch_mounts,
        bumper_switch_plate_center_z,
        bumper_switch_reference,
        bumper_switch_stop_contact_patches,
        bumper_switch_stop_shapes,
        bumper_switch_travel_target,
        cylinder_z,
        electronics_fit,
        power_distribution_mount_positions,
        power_distribution_fit_parts,
        rounded_box,
        rounded_prism_xy,
        side_fairings,
    )
    from robot_body_print import first_layer_contact_area
    from robot_body_split import (
        alignment_pilot_interfaces,
        alignment_pilot_shape,
        clip,
        split_parts,
    )
except ModuleNotFoundError:
    from cad.python.robot_body import (
        EXPORT_DIR,
        Params,
        base_tray,
        body_shell,
        bumper_carrier,
        bumper_switch_contact_patch,
        bumper_switch_body_mount_positions,
        bumper_switch_layout,
        bumper_switch_mount_positions,
        bumper_switch_mounts,
        bumper_switch_plate_center_z,
        bumper_switch_reference,
        bumper_switch_stop_contact_patches,
        bumper_switch_stop_shapes,
        bumper_switch_travel_target,
        cylinder_z,
        electronics_fit,
        power_distribution_mount_positions,
        power_distribution_fit_parts,
        rounded_box,
        rounded_prism_xy,
        side_fairings,
    )
    from cad.python.robot_body_print import first_layer_contact_area
    from cad.python.robot_body_split import (
        alignment_pilot_interfaces,
        alignment_pilot_shape,
        clip,
        split_parts,
    )


COUPON_DIR = EXPORT_DIR / "coupons"


def orientation_notch(shape, x: float, y: float, z: float, height: float):
    """Cut one obvious notch marking the low-X/left end of a coupon."""
    return shape - rounded_box(5.0, 7.0, height + 2.0, 1.2, (x, y, z))


def index_markers(shape, station_x: float, count: int, y: float, z: float, height: float):
    """One-to-five tiny through-holes identify a station without embossed text."""
    for marker_index in range(count):
        marker_x = station_x + (marker_index - (count - 1) / 2.0) * 2.1
        shape = shape - cylinder_z(0.7, height + 2.0, (marker_x, y, z))
    return shape


def insert_coupon(name: str, nominal_diameter: float):
    height = 8.0
    station_xs = (-40.0, -20.0, 0.0, 20.0, 40.0)
    offsets = (-0.4, -0.2, 0.0, 0.2, 0.4)
    diameters = tuple(nominal_diameter + offset for offset in offsets)
    shape = rounded_prism_xy(108.0, 24.0, height, 4.0, (0.0, 0.0, height / 2.0), edge_radius=0.8)
    shape = orientation_notch(shape, -52.0, -9.0, height / 2.0, height)
    stations = []
    for index, (x, diameter) in enumerate(zip(station_xs, diameters), start=1):
        shape = shape - cylinder_z(diameter / 2.0, height + 2.0, (x, 3.0, height / 2.0))
        shape = index_markers(shape, x, index, -8.0, height / 2.0, height)
        stations.append(
            {
                "index": index,
                "center_x_mm": x,
                "diameter_mm": diameter,
                "marker_holes": index,
            }
        )
    return name, shape, {
        "purpose": "heat_set_insert_hole_fit",
        "station_order": "left_to_right_from_notched_end",
        "nominal_diameter_mm": nominal_diameter,
        "stations": stations,
    }


def clearance_coupon(p: Params):
    height = 5.0
    station_xs = (-40.0, -20.0, 0.0, 20.0, 40.0)
    offsets = (-0.4, -0.2, 0.0, 0.2, 0.4)
    shape = rounded_prism_xy(108.0, 34.0, height, 4.0, (0.0, 0.0, height / 2.0), edge_radius=0.8)
    shape = orientation_notch(shape, -52.0, -14.0, height / 2.0, height)
    rows = []
    for label, nominal, y in (
        ("M3", p.m3_clearance_hole, 8.0),
        ("M2.5", p.m2_5_clearance_hole, -8.0),
    ):
        stations = []
        for index, (x, offset) in enumerate(zip(station_xs, offsets), start=1):
            diameter = nominal + offset
            shape = shape - cylinder_z(diameter / 2.0, height + 2.0, (x, y, height / 2.0))
            stations.append(
                {
                    "index": index,
                    "center_x_mm": x,
                    "diameter_mm": diameter,
                }
            )
        rows.append(
            {
                "label": label,
                "center_y_mm": y,
                "nominal_diameter_mm": nominal,
                "stations": stations,
            }
        )
    return "fastener_clearance_coupon", shape, {
        "purpose": "through_fastener_clearance_fit",
        "station_order": "left_to_right_from_notched_end",
        "rows": rows,
    }


def bearing_seat_coupon(p: Params):
    height = 12.0
    seat_depth = p.front_bearing_width + 0.8
    station_xs = (-32.0, 0.0, 32.0)
    seat_diameters = tuple(
        p.front_bearing_od + 2.0 * radial_clearance
        for radial_clearance in (0.1, 0.2, 0.3)
    )
    shape = rounded_prism_xy(100.0, 36.0, height, 5.0, (0.0, 0.0, height / 2.0), edge_radius=0.8)
    shape = orientation_notch(shape, -48.0, -15.0, height / 2.0, height)
    stations = []
    for index, (x, diameter) in enumerate(zip(station_xs, seat_diameters), start=1):
        seat_center_z = height - seat_depth / 2.0
        shape = shape - cylinder_z(diameter / 2.0, seat_depth, (x, 2.0, seat_center_z))
        shape = shape - cylinder_z(
            p.front_bearing_id / 2.0 + 0.3,
            height + 2.0,
            (x, 2.0, height / 2.0),
        )
        shape = index_markers(shape, x, index, -14.0, height / 2.0, height)
        stations.append(
            {
                "index": index,
                "center_x_mm": x,
                "center_y_mm": 2.0,
                "seat_diameter_mm": diameter,
                "seat_depth_mm": seat_depth,
                "shaft_clearance_diameter_mm": p.front_bearing_id + 0.6,
                "marker_holes": index,
            }
        )
    return "bearing_608_seat_coupon", shape, {
        "purpose": "608_bearing_seat_and_shoulder_fit",
        "bearing_reference_mm": {
            "bore": p.front_bearing_id,
            "outside_diameter": p.front_bearing_od,
            "width": p.front_bearing_width,
        },
        "station_order": "left_to_right_from_notched_end",
        "stations": stations,
    }


def pan_bearing_coupon(p: Params):
    """Combined 6807 outer-seat and rotating-journal calibration coupon."""
    base_height = 12.0
    seat_depth = p.pan_bearing_width + 0.4
    station_xs = (-54.0, 0.0, 54.0)
    radial_offsets = (-0.1, 0.0, 0.1)
    seat_diameters = tuple(
        p.pan_bearing_od
        + 2.0 * (p.pan_bearing_seat_clearance + radial_offset)
        for radial_offset in radial_offsets
    )
    journal_nominal = p.pan_bearing_id - p.pan_bearing_journal_clearance
    journal_diameters = tuple(
        journal_nominal + diameter_offset
        for diameter_offset in (-0.2, 0.0, 0.2)
    )
    bore_diameter = p.pan_bearing_id + 0.6
    journal_height = 10.0
    shape = rounded_prism_xy(
        176.0,
        88.0,
        base_height,
        6.0,
        (0.0, 0.0, base_height / 2.0),
        edge_radius=0.8,
    )
    shape = orientation_notch(shape, -86.0, -39.0, base_height / 2.0, base_height)
    seat_stations = []
    journal_stations = []
    for index, (x, seat_diameter, journal_diameter) in enumerate(
        zip(station_xs, seat_diameters, journal_diameters),
        start=1,
    ):
        seat_y = 25.0
        seat_center_z = base_height - seat_depth / 2.0
        shape = shape - cylinder_z(
            seat_diameter / 2.0,
            seat_depth,
            (x, seat_y, seat_center_z),
        )
        shape = shape - cylinder_z(
            bore_diameter / 2.0,
            base_height + 2.0,
            (x, seat_y, base_height / 2.0),
        )
        seat_stations.append(
            {
                "index": index,
                "center_x_mm": x,
                "center_y_mm": seat_y,
                "seat_diameter_mm": seat_diameter,
                "seat_depth_mm": seat_depth,
                "inner_ring_clearance_diameter_mm": bore_diameter,
                "radial_clearance_mm": (seat_diameter - p.pan_bearing_od) / 2.0,
            }
        )

        journal_y = -24.0
        journal_center_z = base_height + journal_height / 2.0 - 0.1
        shape = shape + cylinder_z(
            journal_diameter / 2.0,
            journal_height + 0.2,
            (x, journal_y, journal_center_z),
        )
        journal_stations.append(
            {
                "index": index,
                "center_x_mm": x,
                "center_y_mm": journal_y,
                "journal_diameter_mm": journal_diameter,
                "journal_height_mm": journal_height,
                "diametral_clearance_mm": p.pan_bearing_id - journal_diameter,
            }
        )

    return "pan_6807_bearing_fit_coupon", shape, {
        "purpose": "6807_pan_bearing_outer_seat_and_rotating_journal_fit",
        "material_profile": "production_petg_structural_profile",
        "bearing_reference": "Koyo/JTEKT 6807-2RS",
        "bearing_reference_mm": {
            "bore": p.pan_bearing_id,
            "outside_diameter": p.pan_bearing_od,
            "width": p.pan_bearing_width,
        },
        "station_order": "left_to_right_from_notched_end",
        "seat_row": seat_stations,
        "journal_row": journal_stations,
        "measurement_rule": (
            "Cool fully, test the same purchased bearing at each station, and select "
            "a seat that retains the outer ring without brinelling plus a journal that "
            "slides through the inner ring without perceptible radial play."
        ),
    }


def wall_coupon(p: Params):
    base_height = 2.0
    wall_height = 18.0
    station_xs = (-30.0, 0.0, 30.0)
    wall_thicknesses = (p.min_wall, (p.min_wall + p.wall) / 2.0, p.wall)
    shape = rounded_prism_xy(90.0, 24.0, base_height, 4.0, (0.0, 0.0, 1.0), edge_radius=0.6)
    shape = orientation_notch(shape, -43.0, -9.0, 1.0, base_height)
    stations = []
    for index, (x, thickness) in enumerate(zip(station_xs, wall_thicknesses), start=1):
        wall = rounded_box(
            thickness,
            18.0,
            wall_height,
            0.0,
            (x, 0.0, base_height + wall_height / 2.0 - 0.1),
        )
        shape = shape + wall
        shape = index_markers(shape, x, index, -10.0, 1.0, base_height)
        stations.append(
            {
                "index": index,
                "center_x_mm": x,
                "wall_thickness_mm": thickness,
                "marker_holes": index,
            }
        )
    return "wall_thickness_coupon", shape, {
        "purpose": "wall_strength_surface_and_perimeter_test",
        "station_order": "left_to_right_from_notched_end",
        "stations": stations,
    }


def lid_lap_coupons(p: Params, split):
    x_bounds = (20.0, 60.0)
    y_bounds = (-30.0, 30.0)
    z_bounds = (p.body_bottom + p.body_height, p.body_bottom + p.body_height + 8.0)
    front = clip(split["top_lid_half_front"], *x_bounds, *y_bounds, *z_bounds)
    rear = clip(split["top_lid_half_rear"], *x_bounds, *y_bounds, *z_bounds)
    return (
        (
            "lid_lap_coupon_front",
            front,
            {
                "purpose": "actual_12mm_lid_lap_front_half",
                "assembly_coordinates_mm": {"x": x_bounds, "y": y_bounds, "z": z_bounds},
            },
        ),
        (
            "lid_lap_coupon_rear",
            rear,
            {
                "purpose": "actual_12mm_lid_lap_rear_half",
                "assembly_coordinates_mm": {"x": x_bounds, "y": y_bounds, "z": z_bounds},
            },
        ),
    )


def split_alignment_coupons(p: Params, split):
    """Clip one exact shell/plate pilot interface into three cheap test parts."""
    interface = next(
        item
        for item in alignment_pilot_interfaces(p)
        if item["plate"] == "body_seam_plate_side_left"
    )
    point = interface["points"][0]
    z0, z1 = point[1] - 8.0, point[1] + 8.0
    plate = clip(
        split[interface["plate"]],
        -12.0,
        12.0,
        -p.body_width / 2.0 - 1.0,
        -p.body_width / 2.0 + 12.0,
        z0,
        z1,
    )
    shell_y0 = -p.body_width / 2.0 - 1.0
    shell_y1 = -p.body_width / 2.0 + p.wall + 1.0
    front = clip(
        split["body_shell_q_front_left"],
        -12.0,
        0.0,
        shell_y0,
        shell_y1,
        z0,
        z1,
    )
    rear = clip(
        split["body_shell_q_rear_left"],
        0.0,
        12.0,
        shell_y0,
        shell_y1,
        z0,
        z1,
    )
    common = {
        "purpose": "exact_split_shell_alignment_pilot_fit",
        "pilot_diameter_mm": 2.0 * p.split_pilot_radius,
        "radial_clearance_mm": p.split_pilot_radial_clearance,
        "axial_clearance_mm": p.split_pilot_axial_clearance,
        "assembly_note": "Join the shell-front and shell-rear coupon edges, then press the plate pilot into the shared round recess without forcing it.",
    }
    return (
        (
            "split_pilot_coupon_plate",
            plate,
            {
                **common,
                "role": "pilot_plate",
                "print_rotation_deg": [{"axis": "X", "angle": -90.0}],
            },
        ),
        (
            "split_pilot_coupon_shell_front",
            front,
            {
                **common,
                "role": "front_half_round_recess",
                "print_rotation_deg": [{"axis": "Y", "angle": 90.0}],
            },
        ),
        (
            "split_pilot_coupon_shell_rear",
            rear,
            {
                **common,
                "role": "rear_half_round_recess",
                "print_rotation_deg": [{"axis": "Y", "angle": -90.0}],
            },
        ),
    )


def bumper_interface_coupons(p: Params):
    """Clip one exact front switch zone from the tray and TPU bumper."""
    x_bounds = (-160.0, -124.0)
    y_bounds = (-82.0, -38.0)
    z_bounds = (28.0, 58.0)
    tray = clip(base_tray(p), *x_bounds, *y_bounds, *z_bounds)
    tpu = clip(bumper_carrier(p), *x_bounds, *y_bounds, *z_bounds)
    plate = bumper_switch_mounts(p)["bumper_switch_mount_front_left"]
    common = {
        "purpose": "exact_tray_fixed_bumper_switch_interface",
        "zone": "front_left",
        "assembly_coordinates_mm": {
            "x": x_bounds,
            "y": y_bounds,
            "z": z_bounds,
        },
        "switch_reference_mm": {
            "part": "Omron D2HW-C202MR",
            "length": p.bumper_switch_length,
            "width": p.bumper_switch_width,
            "height": p.bumper_switch_height,
            "mount_spacing": p.bumper_switch_mount_spacing,
            "mount_hole": p.bumper_switch_mount_hole,
            "free_position": p.bumper_switch_free_position,
            "operating_position": p.bumper_switch_operating_position,
            "operating_tolerance": p.bumper_switch_operating_tolerance,
            "total_travel_position": p.bumper_switch_total_travel_position,
            "wire_length": p.bumper_switch_wire_length,
        },
        "nominal_rest_gap_mm": p.bumper_switch_nominal_gap,
        "nominal_actuation_travel_mm": p.bumper_switch_actuation_travel,
        "rigid_stop_travel_mm": p.bumper_switch_stop_travel,
        "assembly_note": "Install two M3 inserts from the tray-coupon underside and fasten the PETG plate upward. Mount one D2HW-C202MR through its two recessed M3 plate paths, keep the right-side molded lead straight through the tray corridor, then align the TPU relief around the fixed plate without clamping it.",
    }
    return (
        (
            "bumper_interface_coupon_tray",
            tray,
            {
                **common,
                "role": "exact_production_tray_edge_with_blind_inserts_and_switch_pocket",
                "material_profile": "production_petg_structural",
            },
        ),
        (
            "bumper_interface_coupon_plate",
            plate,
            {
                **common,
                "role": "exact_production_tray_fixed_switch_plate",
                "material_profile": "production_petg_detail",
            },
        ),
        (
            "bumper_interface_coupon_tpu",
            tpu,
            {
                **common,
                "role": "exact_production_tpu_inner_wall_and_plate_relief",
                "material_profile": "production_tpu_95a_candidate",
            },
        ),
    )


def fairing_recess_coupons(p: Params):
    """Clip one exact flush fairing corner and its matching shell pocket."""
    bounds = (-127.0, -101.0, 103.0, 111.0, 110.0, 132.0)
    shell = clip(body_shell(p), *bounds)
    fairing = clip(side_fairings(p)["side_fairing_right"], *bounds)
    common = {
        "purpose": "exact_flush_side_fairing_recess_fit",
        "side": "right_front_upper_corner",
        "assembly_coordinates_mm": {
            "x": bounds[0:2],
            "y": bounds[2:4],
            "z": bounds[4:6],
        },
        "fairing_thickness_mm": p.side_fairing_thickness,
        "recess_depth_mm": p.side_fairing_recess_depth,
        "nominal_depth_gap_mm": (
            p.side_fairing_recess_depth - p.side_fairing_thickness
        ),
        "perimeter_clearance_mm": p.side_fairing_perimeter_clearance,
        "remaining_shell_wall_mm": p.wall - p.side_fairing_recess_depth,
        "assembly_note": "Print both parts with the production cream PETG profile. Seat the thin skin in the shell pocket, confirm the rounded perimeter enters without force, then install one M3 screw and verify the exterior seam becomes flush without bowing.",
        "print_rotation_deg": [{"axis": "X", "angle": 90.0}],
    }
    return (
        (
            "fairing_recess_coupon_shell",
            shell,
            {
                **common,
                "role": "exact_production_shell_pocket_backing_wall_and_boss",
            },
        ),
        (
            "fairing_recess_coupon_skin",
            fairing,
            {
                **common,
                "role": "exact_production_flush_fairing_corner_and_clearance_hole",
            },
        ),
    )


def power_distribution_fit_gauge(p: Params):
    """Lightweight one-piece envelope gauge for the retail Blue Sea 5045."""
    deck_top = p.power_deck_z + 2.0
    base_thickness = 2.0
    post_size = 8.0
    gauge = rounded_box(
        p.power_distribution_width,
        p.power_distribution_length,
        base_thickness,
        2.0,
        (
            p.power_distribution_center_x,
            p.power_distribution_center_y,
            deck_top + base_thickness / 2.0,
        ),
    )
    post_height = p.power_distribution_height - base_thickness
    for x_sign in (-1.0, 1.0):
        for y_sign in (-1.0, 1.0):
            gauge = gauge + rounded_box(
                post_size,
                post_size,
                post_height,
                1.2,
                (
                    p.power_distribution_center_x
                    + x_sign * (p.power_distribution_width - post_size) / 2.0,
                    p.power_distribution_center_y
                    + y_sign * (p.power_distribution_length - post_size) / 2.0,
                    deck_top + base_thickness + post_height / 2.0,
                ),
            )
    for x, y in power_distribution_mount_positions(p):
        gauge = gauge - cylinder_z(
            p.power_distribution_mount_hole / 2.0,
            base_thickness + 2.0,
            (x, y, deck_top + base_thickness / 2.0),
        )
    return "power_distribution_fit_gauge", gauge, {
        "purpose": "blue_sea_5045_production_footprint_and_deck_fit_preflight",
        "material_profile": "production_petg_detail",
        "fit_only_not_electrical": True,
        "retail_module_reference": "Blue Sea Systems 5045 covered 4-circuit ATO/ATC fuse block",
        "module_envelope_mm": {
            "length": p.power_distribution_length,
            "width": p.power_distribution_width,
            "height": p.power_distribution_height,
            "mount_spacing": p.power_distribution_mount_spacing,
            "mount_hole_diameter": p.power_distribution_mount_hole,
        },
        "assembly_note": (
            "Mount this lightweight unpowered PETG gauge directly on the production "
            "deck through the two M4 paths. Confirm the purchased block footprint, integral cover, "
            "wire exits, labels, fuse-service reach, and neighboring clearances before "
            "release. This solid gauge does not validate current, heat, or fault behavior."
        ),
    }


def oriented_and_grounded(shape, rotations=()):
    axes = {"X": Axis.X, "Y": Axis.Y, "Z": Axis.Z}
    oriented = shape
    for rotation in rotations:
        oriented = oriented.rotate(axes[rotation["axis"]], rotation["angle"])
    box = oriented.bounding_box()
    center_x = (box.min.X + box.max.X) / 2.0
    center_y = (box.min.Y + box.max.Y) / 2.0
    return oriented.moved(Location((-center_x, -center_y, -box.min.Z)))


def spans(shape):
    box = shape.bounding_box()
    return {
        "x": float(box.max.X - box.min.X),
        "y": float(box.max.Y - box.min.Y),
        "z": float(box.max.Z - box.min.Z),
    }


def build_coupons(p: Params):
    coupons = {}
    split = split_parts(p)
    definitions = (
        insert_coupon("m3_insert_coupon", p.insert_hole_m3),
        insert_coupon("m2_5_insert_coupon", p.insert_hole_m2_5),
        clearance_coupon(p),
        bearing_seat_coupon(p),
        pan_bearing_coupon(p),
        wall_coupon(p),
        *lid_lap_coupons(p, split),
        *split_alignment_coupons(p, split),
        *bumper_interface_coupons(p),
        *fairing_recess_coupons(p),
        power_distribution_fit_gauge(p),
    )
    for name, shape, metadata in definitions:
        coupons[name] = {"shape": shape, "metadata": metadata}
    return coupons


def validate_parametric_features(p: Params, coupons):
    openings_checked = 0
    shoulders_checked = 0

    def require_clear(coupon_name, gauge, label):
        nonlocal openings_checked
        volume = float((coupons[coupon_name]["shape"] & gauge).volume)
        if volume > 0.01:
            raise ValueError(f"{coupon_name} blocked {label}: {volume:.4f} mm^3")
        openings_checked += 1

    for coupon_name in ("m3_insert_coupon", "m2_5_insert_coupon"):
        for station in coupons[coupon_name]["metadata"]["stations"]:
            gauge = cylinder_z(
                station["diameter_mm"] / 2.0 - 0.05,
                12.0,
                (station["center_x_mm"], 3.0, 4.0),
            )
            require_clear(coupon_name, gauge, f"station {station['index']}")

    clearance_name = "fastener_clearance_coupon"
    for row in coupons[clearance_name]["metadata"]["rows"]:
        for station in row["stations"]:
            gauge = cylinder_z(
                station["diameter_mm"] / 2.0 - 0.05,
                9.0,
                (station["center_x_mm"], row["center_y_mm"], 2.5),
            )
            require_clear(
                clearance_name,
                gauge,
                f"{row['label']} station {station['index']}",
            )

    bearing_name = "bearing_608_seat_coupon"
    for station in coupons[bearing_name]["metadata"]["stations"]:
        seat_center_z = 12.0 - station["seat_depth_mm"] / 2.0
        seat_gauge = cylinder_z(
            station["seat_diameter_mm"] / 2.0 - 0.05,
            station["seat_depth_mm"] - 0.2,
            (
                station["center_x_mm"],
                station["center_y_mm"],
                seat_center_z + 0.1,
            ),
        )
        require_clear(bearing_name, seat_gauge, f"bearing seat {station['index']}")
        shaft_gauge = cylinder_z(
            station["shaft_clearance_diameter_mm"] / 2.0 - 0.05,
            14.0,
            (station["center_x_mm"], station["center_y_mm"], 6.0),
        )
        require_clear(bearing_name, shaft_gauge, f"shaft bore {station['index']}")

        shoulder_z = 12.0 - station["seat_depth_mm"] - 0.2
        outer = cylinder_z(
            station["seat_diameter_mm"] / 2.0 - 0.5,
            0.4,
            (station["center_x_mm"], station["center_y_mm"], shoulder_z),
        )
        inner = cylinder_z(
            station["shaft_clearance_diameter_mm"] / 2.0 + 0.5,
            0.8,
            (station["center_x_mm"], station["center_y_mm"], shoulder_z),
        )
        shoulder_probe = outer - inner
        support_volume = float(
            (coupons[bearing_name]["shape"] & shoulder_probe).volume
        )
        if support_volume < 5.0:
            raise ValueError(
                f"{bearing_name} station {station['index']} lacks a bearing shoulder"
            )
        shoulders_checked += 1

    pan_name = "pan_6807_bearing_fit_coupon"
    for station in coupons[pan_name]["metadata"]["seat_row"]:
        seat_center_z = 12.0 - station["seat_depth_mm"] / 2.0
        seat_gauge = cylinder_z(
            station["seat_diameter_mm"] / 2.0 - 0.05,
            station["seat_depth_mm"],
            (station["center_x_mm"], station["center_y_mm"], seat_center_z),
        )
        require_clear(pan_name, seat_gauge, f"6807 seat {station['index']}")
        bore_gauge = cylinder_z(
            station["inner_ring_clearance_diameter_mm"] / 2.0 - 0.05,
            14.0,
            (station["center_x_mm"], station["center_y_mm"], 6.0),
        )
        require_clear(pan_name, bore_gauge, f"6807 inner-ring bore {station['index']}")

        shoulder_z = 12.0 - station["seat_depth_mm"] - 0.2
        shoulder_outer = cylinder_z(
            station["seat_diameter_mm"] / 2.0 - 0.5,
            0.4,
            (station["center_x_mm"], station["center_y_mm"], shoulder_z),
        )
        shoulder_inner = cylinder_z(
            station["inner_ring_clearance_diameter_mm"] / 2.0 + 0.5,
            0.8,
            (station["center_x_mm"], station["center_y_mm"], shoulder_z),
        )
        support_volume = float(
            (
                coupons[pan_name]["shape"]
                & (shoulder_outer - shoulder_inner)
            ).volume
        )
        if support_volume < 20.0:
            raise ValueError(
                f"{pan_name} station {station['index']} lacks an outer-ring shoulder"
            )
        shoulders_checked += 1

    for station in coupons[pan_name]["metadata"]["journal_row"]:
        journal_gauge = cylinder_z(
            station["journal_diameter_mm"] / 2.0 - 0.05,
            station["journal_height_mm"] - 0.2,
            (
                station["center_x_mm"],
                station["center_y_mm"],
                12.0 + station["journal_height_mm"] / 2.0,
            ),
        )
        contained_volume = float(
            (coupons[pan_name]["shape"] & journal_gauge).volume
        )
        if float(journal_gauge.volume) - contained_volume > 0.05:
            raise ValueError(
                f"{pan_name} station {station['index']} lost journal material"
            )

    return {
        "openings_checked": openings_checked,
        "bearing_shoulders_checked": shoulders_checked,
        "status": "ok",
    }


def validate_lid_lap(p: Params, coupons):
    front = coupons["lid_lap_coupon_front"]["shape"]
    rear = coupons["lid_lap_coupon_rear"]["shape"]
    overlap = float((front & rear).volume)
    split = split_parts(p)
    source = clip(
        split["top_lid_half_front"] + split["top_lid_half_rear"],
        20.0,
        60.0,
        -30.0,
        30.0,
        p.body_bottom + p.body_height,
        p.body_bottom + p.body_height + 8.0,
    )
    reconstructed = front + rear
    missing = float((source - reconstructed).volume)
    extra = float((reconstructed - source).volume)
    if overlap > 0.05 or missing > 0.05 or extra > 0.05:
        raise ValueError(
            "Lid-lap coupon reconstruction failed: "
            f"overlap={overlap:.3f} missing={missing:.3f} extra={extra:.3f} mm^3"
        )
    return {"overlap_mm3": overlap, "missing_mm3": missing, "extra_mm3": extra}


def validate_split_pilot(p: Params, coupons):
    interface = next(
        item
        for item in alignment_pilot_interfaces(p)
        if item["plate"] == "body_seam_plate_side_left"
    )
    point = interface["points"][0]
    pilot = alignment_pilot_shape(p, interface, point)
    plate = coupons["split_pilot_coupon_plate"]["shape"]
    shell = (
        coupons["split_pilot_coupon_shell_front"]["shape"]
        + coupons["split_pilot_coupon_shell_rear"]["shape"]
    )
    pilot_volume = float(pilot.volume)
    fused_volume = float((pilot & plate).volume)
    blocked_volume = float((pilot & shell).volume)
    recess = alignment_pilot_shape(p, interface, point, recess=True)
    recess_blocked_volume = float((recess & shell).volume)
    if pilot_volume - fused_volume > 0.05:
        raise ValueError(
            "Split-pilot coupon lost part of its pilot: "
            f"{fused_volume:.3f}/{pilot_volume:.3f} mm^3"
        )
    if blocked_volume > 0.05 or recess_blocked_volume > 0.05:
        raise ValueError(
            "Split-pilot coupon recess is blocked: "
            f"pilot={blocked_volume:.3f} recess={recess_blocked_volume:.3f} mm^3"
        )
    return {
        "pilot_volume_mm3": pilot_volume,
        "pilot_fused_volume_mm3": fused_volume,
        "pilot_blocked_volume_mm3": blocked_volume,
        "recess_blocked_volume_mm3": recess_blocked_volume,
        "status": "ok",
    }


def validate_bumper_interface(p: Params, coupons):
    """Prove the coupon is exact, seats cleanly, and preserves actuation."""
    x_bounds = (-160.0, -124.0)
    y_bounds = (-82.0, -38.0)
    z_bounds = (28.0, 58.0)
    sources = {
        "bumper_interface_coupon_tray": clip(
            base_tray(p), *x_bounds, *y_bounds, *z_bounds
        ),
        "bumper_interface_coupon_plate": bumper_switch_mounts(p)[
            "bumper_switch_mount_front_left"
        ],
        "bumper_interface_coupon_tpu": clip(
            bumper_carrier(p), *x_bounds, *y_bounds, *z_bounds
        ),
    }
    reconstruction = {}
    for name, source in sources.items():
        coupon = coupons[name]["shape"]
        missing = float((source - coupon).volume)
        extra = float((coupon - source).volume)
        if missing > 0.05 or extra > 0.05:
            raise ValueError(
                f"Bumper-interface coupon drifted from production source: {name} "
                f"missing={missing:.3f} extra={extra:.3f} mm^3"
            )
        reconstruction[name] = {
            "missing_mm3": missing,
            "extra_mm3": extra,
        }

    tray = coupons["bumper_interface_coupon_tray"]["shape"]
    plate = coupons["bumper_interface_coupon_plate"]["shape"]
    tpu = coupons["bumper_interface_coupon_tpu"]["shape"]
    for name_a, shape_a, name_b, shape_b in (
        ("tray", tray, "plate", plate),
        ("tray", tray, "tpu", tpu),
        ("plate", plate, "tpu", tpu),
    ):
        overlap = float((shape_a & shape_b).volume)
        if overlap > 0.05:
            raise ValueError(
                f"Bumper-interface coupon overlap: {name_a} vs {name_b} "
                f"({overlap:.3f} mm^3)"
            )

    tray_box = tray.bounding_box()
    nominal_plate_top = (
        bumper_switch_plate_center_z(p) + p.bumper_switch_plate_thickness / 2.0
    )
    if abs(float(nominal_plate_top - tray_box.min.Z)) > 0.05:
        raise ValueError("Bumper-interface coupon plate misses tray underside")

    name, orientation, x, y = bumper_switch_layout()[0]
    fit = electronics_fit(p)[f"fit_bumper_switch_{name}"]
    for label, target in (("tray", tray), ("plate", plate), ("tpu", tpu)):
        volume = float((fit & target).volume)
        if volume > 0.05:
            raise ValueError(
                f"Bumper-interface switch envelope collides with {label}: "
                f"{volume:.3f} mm^3"
            )

    rest_patch = bumper_switch_contact_patch(p, orientation, x, y)
    rest_supported = float((rest_patch & tpu).volume)
    if float(rest_patch.volume) - rest_supported > 0.05:
        raise ValueError("Bumper-interface coupon lost its TPU contact patch")
    if float((rest_patch & fit).volume) > 0.05:
        raise ValueError("Bumper-interface coupon preloads the switch at rest")
    compressed_patch = bumper_switch_contact_patch(
        p,
        orientation,
        x,
        y,
        p.bumper_switch_actuation_travel,
    )
    compressed_contact = float((compressed_patch & fit).volume)
    if compressed_contact <= 0.05:
        raise ValueError("Bumper-interface coupon misses switch at nominal stroke")
    operating_target = bumper_switch_travel_target(
        p, orientation, x, y, "operating"
    )
    operating_contact = float((compressed_patch & operating_target).volume)
    if operating_contact <= 0.05:
        raise ValueError(
            "Bumper-interface coupon misses worst-case D2HW operating position"
        )
    total_target = bumper_switch_travel_target(p, orientation, x, y, "total")
    total_contact = float((compressed_patch & total_target).volume)
    if total_contact > 0.05:
        raise ValueError("Bumper-interface coupon bottoms D2HW at nominal stroke")

    stop_patch = bumper_switch_contact_patch(
        p,
        orientation,
        x,
        y,
        p.bumper_switch_stop_travel,
    )
    stop_patches = bumper_switch_stop_contact_patches(
        p,
        orientation,
        x,
        y,
        p.bumper_switch_stop_travel + 0.1,
    )
    stop_shapes = bumper_switch_stop_shapes(p, orientation, x, y)
    stop_contact = sum(
        float((patch & stop).volume)
        for patch, stop in zip(stop_patches, stop_shapes)
    )
    if stop_contact <= 0.05:
        raise ValueError("Bumper-interface coupon misses both rigid overtravel stops")
    if float((stop_patch & total_target).volume) > 0.05:
        raise ValueError("Bumper-interface rigid stops allow D2HW bottoming")

    plate_z = bumper_switch_plate_center_z(p)
    plate_bottom = plate_z - p.bumper_switch_plate_thickness / 2.0
    insert_top = (
        p.body_bottom
        - p.tray_thickness
        + p.bumper_switch_tray_insert_depth
    )
    screw_paths = 0
    for hole_x, hole_y in bumper_switch_mount_positions(orientation, x, y):
        probe_bottom = plate_bottom - 1.0
        probe_top = insert_top - 1.0
        probe = cylinder_z(
            p.m3_clearance_hole / 2.0 - 0.1,
            probe_top - probe_bottom,
            (hole_x, hole_y, (probe_bottom + probe_top) / 2.0),
        )
        if float((probe & plate).volume) > 0.05 or float((probe & tray).volume) > 0.05:
            raise ValueError("Bumper-interface coupon has a blocked plate screw path")
        screw_paths += 1

    switch_screw_paths = 0
    for hole_x, hole_y in bumper_switch_body_mount_positions(
        p, orientation, x, y
    ):
        probe = cylinder_z(
            p.bumper_switch_mount_hole / 2.0 - 0.1,
            p.bumper_switch_plate_thickness + 2.0,
            (hole_x, hole_y, plate_z),
        )
        if float((probe & plate).volume) > 0.05:
            raise ValueError("Bumper-interface coupon blocks a D2HW mounting screw")
        switch_screw_paths += 1

    return {
        "zone": name,
        "reconstruction": reconstruction,
        "assembled_overlaps_mm3": {
            "tray_plate": float((tray & plate).volume),
            "tray_tpu": float((tray & tpu).volume),
            "plate_tpu": float((plate & tpu).volume),
        },
        "rest_patch_supported_mm3": rest_supported,
        "rest_preload_mm3": float((rest_patch & fit).volume),
        "compressed_switch_contact_mm3": compressed_contact,
        "worst_case_operating_target_contact_mm3": operating_contact,
        "nominal_total_travel_contact_mm3": total_contact,
        "rigid_stop_contact_mm3": stop_contact,
        "open_tray_m3_screw_paths": screw_paths,
        "open_d2hw_m3_screw_paths": switch_screw_paths,
        "nominal_rest_gap_mm": p.bumper_switch_nominal_gap,
        "nominal_actuation_travel_mm": p.bumper_switch_actuation_travel,
        "rigid_stop_travel_mm": p.bumper_switch_stop_travel,
        "status": "ok",
    }


def validate_fairing_recess(p: Params, coupons):
    """Prove exact coupon geometry, free insertion, and a real pocket floor."""
    bounds = (-127.0, -101.0, 103.0, 111.0, 110.0, 132.0)
    sources = {
        "fairing_recess_coupon_shell": clip(body_shell(p), *bounds),
        "fairing_recess_coupon_skin": clip(
            side_fairings(p)["side_fairing_right"], *bounds
        ),
    }
    reconstruction = {}
    for name, source in sources.items():
        coupon = coupons[name]["shape"]
        missing = float((source - coupon).volume)
        extra = float((coupon - source).volume)
        if missing > 0.05 or extra > 0.05:
            raise ValueError(
                f"Fairing-recess coupon drifted from production source: {name} "
                f"missing={missing:.3f} extra={extra:.3f} mm^3"
            )
        reconstruction[name] = {"missing_mm3": missing, "extra_mm3": extra}

    shell = coupons["fairing_recess_coupon_shell"]["shape"]
    skin = coupons["fairing_recess_coupon_skin"]["shape"]
    assembled_overlap = float((shell & skin).volume)
    depth_gap = p.side_fairing_recess_depth - p.side_fairing_thickness
    seated_skin = skin.moved(Location((0.0, -depth_gap, 0.0)))
    seated_overlap = float((shell & seated_skin).volume)
    overtravel_skin = skin.moved(Location((0.0, -(depth_gap + 0.1), 0.0)))
    floor_contact = float((shell & overtravel_skin).volume)
    if assembled_overlap > 0.05 or seated_overlap > 0.05:
        raise ValueError(
            "Fairing-recess coupon binds before seating: "
            f"assembled={assembled_overlap:.3f} seated={seated_overlap:.3f} mm^3"
        )
    if floor_contact <= 0.05:
        raise ValueError("Fairing-recess coupon has no backing floor at nominal depth")
    return {
        "reconstruction": reconstruction,
        "assembled_overlap_mm3": assembled_overlap,
        "seated_overlap_mm3": seated_overlap,
        "floor_contact_after_0_1mm_overtravel_mm3": floor_contact,
        "nominal_depth_gap_mm": depth_gap,
        "perimeter_clearance_mm": p.side_fairing_perimeter_clearance,
        "remaining_shell_wall_mm": p.wall - p.side_fairing_recess_depth,
        "status": "ok",
    }


def validate_power_distribution_gauge(p: Params, coupons):
    """Prove the gauge matches the Blue Sea 5045 production footprint."""
    coupon_name = "power_distribution_fit_gauge"
    gauge = coupons[coupon_name]["shape"]
    fits = power_distribution_fit_parts(p)
    source_names = ("fit_power_distribution_block",)
    source = fits[source_names[0]]
    source_box = source.bounding_box()
    gauge_box = gauge.bounding_box()
    source_dims = (
        float(source_box.max.X - source_box.min.X),
        float(source_box.max.Y - source_box.min.Y),
        float(source_box.max.Z - source_box.min.Z),
    )
    gauge_dims = (
        float(gauge_box.max.X - gauge_box.min.X),
        float(gauge_box.max.Y - gauge_box.min.Y),
        float(gauge_box.max.Z - gauge_box.min.Z),
    )
    if any(abs(a - b) > 0.05 for a, b in zip(source_dims, gauge_dims)):
        raise ValueError(
            "Power-distribution fit gauge envelope drifted from production: "
            f"source={source_dims} gauge={gauge_dims}"
        )
    if len(gauge.solids()) != 1:
        raise ValueError("Power-distribution fit gauge is not one printable solid")

    open_mount_paths = 0
    for x, y in power_distribution_mount_positions(p):
        probe = cylinder_z(
            p.power_distribution_mount_hole / 2.0 - 0.05,
            float(gauge_box.max.Z - gauge_box.min.Z) + 4.0,
            (x, y, (gauge_box.min.Z + gauge_box.max.Z) / 2.0),
        )
        blocked = float((gauge & probe).volume)
        if blocked > 0.05:
            raise ValueError(
                "Power-distribution fit gauge blocks an M4 mount path: "
                f"{blocked:.3f} mm^3"
            )
        open_mount_paths += 1

    return {
        "source_envelopes": list(source_names),
        "source_dimensions_mm": source_dims,
        "gauge_dimensions_mm": gauge_dims,
        "open_m4_mount_paths": open_mount_paths,
        "fit_only_not_electrical": True,
        "status": "ok",
    }


def export_coupons(p: Params, bed: float, margin: float):
    COUPON_DIR.mkdir(parents=True, exist_ok=True)
    for path in COUPON_DIR.glob("*.stl"):
        path.unlink()

    coupons = build_coupons(p)
    feature_validation = validate_parametric_features(p, coupons)
    lid_validation = validate_lid_lap(p, coupons)
    split_pilot_validation = validate_split_pilot(p, coupons)
    bumper_interface_validation = validate_bumper_interface(p, coupons)
    fairing_recess_validation = validate_fairing_recess(p, coupons)
    power_distribution_gauge_validation = validate_power_distribution_gauge(
        p, coupons
    )
    max_allowed = bed - margin
    failures = []
    manifest = {
        "units": "mm",
        "source": "cad/python/robot_body_coupons.py",
        "parameter_source": "cad/python/robot_body.py",
        "bed_nominal_mm": bed,
        "margin_mm": margin,
        "max_allowed_xy_span_mm": max_allowed,
        "material": "Use each coupon entry's material profile with the same brand, color, nozzle, layer height, and orientation planned for its final interface.",
        "measurement_rule": "Measure cooled coupons; never tune production geometry from a warm or stringing-heavy print.",
        "lid_lap_reconstruction": lid_validation,
        "split_pilot_validation": split_pilot_validation,
        "bumper_interface_validation": bumper_interface_validation,
        "fairing_recess_validation": fairing_recess_validation,
        "power_distribution_gauge_validation": power_distribution_gauge_validation,
        "feature_validation": feature_validation,
        "coupons": {},
    }

    for name, item in sorted(coupons.items()):
        source_shape = item["shape"]
        shape = oriented_and_grounded(
            source_shape,
            item["metadata"].get("print_rotation_deg", ()),
        )
        if not shape.is_valid:
            failures.append(f"{name}: invalid solid")
        if len(shape.solids()) != 1:
            failures.append(f"{name}: {len(shape.solids())} solids")
        volume_delta = abs(float(source_shape.volume) - float(shape.volume))
        if volume_delta > max(0.05, float(source_shape.volume) * 1e-8):
            failures.append(f"{name}: grounding changed volume by {volume_delta:.4f} mm^3")
        box = shape.bounding_box()
        if abs(float(box.min.Z)) > 0.01:
            failures.append(f"{name}: not grounded")
        part_spans = spans(shape)
        if max(part_spans["x"], part_spans["y"]) > max_allowed + 0.01:
            failures.append(f"{name}: exceeds usable bed span")
        contact = first_layer_contact_area(shape)
        if contact < 20.0:
            failures.append(f"{name}: first-layer contact too small ({contact:.2f} mm^2)")
        export_stl(shape, COUPON_DIR / f"{name}.stl")
        manifest["coupons"][name] = {
            "stl": f"{name}.stl",
            "span_mm": part_spans,
            "first_layer_contact_area_mm2": contact,
            "material_profile": item["metadata"].get(
                "material_profile", "production_petg_profile"
            ),
            **item["metadata"],
        }

    if failures:
        raise SystemExit("Coupon export failed:\n- " + "\n- ".join(failures))

    manifest_path = COUPON_DIR / "codex_robot_body_v1_coupon_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(
        "COUPONS_VALID "
        f"parts={len(coupons)} max_allowed={max_allowed:.0f}mm "
        f"openings={feature_validation['openings_checked']} "
        f"shoulders={feature_validation['bearing_shoulders_checked']} "
        "grounded=ok contact=ok lid_lap=exact split_pilot=clear "
        "bumper_interface=clear_and_actuates fairing_recess=clear_and_seats "
        "power_distribution_gauge=blue_sea_5045_exact_with_2x_m4_paths "
        "pan_bearing=seat_and_journal parameters=shared"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bed", type=float, default=256.0)
    parser.add_argument("--margin", type=float, default=8.0)
    args = parser.parse_args()
    export_coupons(Params(), args.bed, args.margin)


if __name__ == "__main__":
    main()
