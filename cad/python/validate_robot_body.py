"""Validate the robot body's solids, packaging, and printer envelope."""

from __future__ import annotations

import argparse
from itertools import combinations

from build123d import Axis, Compound

try:
    from robot_body import (
        Params,
        audio_amp_mount_positions,
        battery_cradle_mount_positions,
        bumper_bottom_z,
        bumper_switch_contact_patch,
        bumper_switch_body_mount_positions,
        bumper_switch_layout,
        bumper_switch_mount_positions,
        bumper_switch_plate_center_z,
        bumper_switch_reference,
        bumper_switch_stop_contact_patches,
        bumper_switch_stop_shapes,
        bumper_switch_travel_target,
        body_inner_roof_z,
        build_parts,
        cable_strain_relief_mount_positions,
        carry_anchor_fastener_positions,
        carry_anchor_slot_positions,
        camera_board_hole_offsets,
        camera_field_of_view_keepout,
        camera_reference,
        cylinder_x,
        cylinder_y,
        cylinder_z,
        electronics_fit,
        estop_backing_center_z,
        estop_keyed_panel_cutout,
        estop_mount_panel_bottom_z,
        estop_mount_panel_top_z,
        estop_mount_positions,
        fairing_mount_positions,
        front_fascia_mount_positions,
        front_idler_mount_positions,
        front_idler_hardware_names,
        front_idler_hub_mount_positions,
        front_idler_retainer_interfaces,
        front_neopixel_pcb_front_x,
        front_tof_pod_mount_positions,
        front_tof_y_positions,
        head_face_mount_positions,
        head_neopixel_pcb_front_x,
        head_rear_mount_positions,
        head_tilt_adapter_center_y,
        head_tilt_adapter_mount_positions,
        head_tilt_horn_mount_positions,
        head_tilt_passive_bushing_center_y,
        head_tilt_yoke_center_y,
        lid_mount_positions,
        motor_pod_mount_positions,
        motor_pod_service_interface,
        drive_motor_bracket_tray_positions,
        drive_motor_face_mount_positions,
        drive_motor_face_y,
        drive_motor_hub_mount_positions,
        mic_array_mount_positions,
        mic_slot_layout,
        mobility_pod_shell_center_z,
        mdds10_board_bottom_z,
        neck_yoke_mount_positions,
        motor_controller_board_mount_positions,
        motor_controller_plate_mount_positions,
        motor_controller_plate_bottom_z,
        motor_controller_plate_top_z,
        motor_cutoff_plate_mount_positions,
        neopixel_mount_positions,
        pan_bearing_key_positions,
        pan_bearing_retainer_mount_positions,
        pan_servo_horn_center_z,
        pan_servo_horn_mount_positions,
        pan_servo_mount_plane_z,
        pan_servo_mount_positions,
        pico2_board_bottom_z,
        pico2_mount_positions,
        pico2_usb_notch_center_x,
        pi_regulator_mount_positions,
        power_deck_mount_positions,
        power_distribution_board_mount_positions,
        power_distribution_holder_positions,
        power_distribution_strain_slots,
        power_harness_strap_slots,
        printable_parts,
        rear_service_cartridge_layout,
        rear_service_cartridge_mount_positions,
        rear_charge_jack_center,
        rear_charge_jack_cutout,
        rear_mute_switch_cutout,
        rear_service_jack_cutout,
        service_jack_carrier_mount_positions,
        service_jack_pcb_mount_positions,
        rounded_box,
        rounded_panel_xz,
        rounded_panel_yz,
        rounded_prism_xy,
        safety_shelf_standoff_positions,
        servo_regulator_mount_positions,
        side_fairing_center_y,
        side_vent_layout,
        side_tof_pod_mount_positions,
        speaker_shell_mount_positions,
        speaker_slot_layout,
        tilt_servo_horn_center_y,
        tilt_servo_mount_plane_y,
        tilt_servo_mount_positions,
        vent_inlay_mount_positions,
        wheel_center_y,
        wheel_ground_z,
        wheel_tread_keepout,
    )
    from robot_body_split import (
        alignment_pilot_interfaces,
        alignment_pilot_shape,
        split_parts,
    )
except ModuleNotFoundError:
    from cad.python.robot_body import (
        Params,
        audio_amp_mount_positions,
        battery_cradle_mount_positions,
        bumper_bottom_z,
        bumper_switch_contact_patch,
        bumper_switch_body_mount_positions,
        bumper_switch_layout,
        bumper_switch_mount_positions,
        bumper_switch_plate_center_z,
        bumper_switch_reference,
        bumper_switch_stop_contact_patches,
        bumper_switch_stop_shapes,
        bumper_switch_travel_target,
        body_inner_roof_z,
        build_parts,
        cable_strain_relief_mount_positions,
        carry_anchor_fastener_positions,
        carry_anchor_slot_positions,
        camera_board_hole_offsets,
        camera_field_of_view_keepout,
        camera_reference,
        cylinder_x,
        cylinder_y,
        cylinder_z,
        electronics_fit,
        estop_backing_center_z,
        estop_keyed_panel_cutout,
        estop_mount_panel_bottom_z,
        estop_mount_panel_top_z,
        estop_mount_positions,
        fairing_mount_positions,
        front_fascia_mount_positions,
        front_idler_mount_positions,
        front_idler_hardware_names,
        front_idler_hub_mount_positions,
        front_idler_retainer_interfaces,
        front_neopixel_pcb_front_x,
        front_tof_pod_mount_positions,
        front_tof_y_positions,
        head_face_mount_positions,
        head_neopixel_pcb_front_x,
        head_rear_mount_positions,
        head_tilt_adapter_center_y,
        head_tilt_adapter_mount_positions,
        head_tilt_horn_mount_positions,
        head_tilt_passive_bushing_center_y,
        head_tilt_yoke_center_y,
        lid_mount_positions,
        motor_pod_mount_positions,
        motor_pod_service_interface,
        drive_motor_bracket_tray_positions,
        drive_motor_face_mount_positions,
        drive_motor_face_y,
        drive_motor_hub_mount_positions,
        mic_array_mount_positions,
        mic_slot_layout,
        mobility_pod_shell_center_z,
        mdds10_board_bottom_z,
        neck_yoke_mount_positions,
        motor_controller_board_mount_positions,
        motor_controller_plate_mount_positions,
        motor_controller_plate_bottom_z,
        motor_controller_plate_top_z,
        motor_cutoff_plate_mount_positions,
        neopixel_mount_positions,
        pan_bearing_key_positions,
        pan_bearing_retainer_mount_positions,
        pan_servo_horn_center_z,
        pan_servo_horn_mount_positions,
        pan_servo_mount_plane_z,
        pan_servo_mount_positions,
        pico2_board_bottom_z,
        pico2_mount_positions,
        pico2_usb_notch_center_x,
        pi_regulator_mount_positions,
        power_deck_mount_positions,
        power_distribution_board_mount_positions,
        power_distribution_holder_positions,
        power_distribution_strain_slots,
        power_harness_strap_slots,
        printable_parts,
        rear_service_cartridge_layout,
        rear_service_cartridge_mount_positions,
        rear_charge_jack_center,
        rear_charge_jack_cutout,
        rear_mute_switch_cutout,
        rear_service_jack_cutout,
        service_jack_carrier_mount_positions,
        service_jack_pcb_mount_positions,
        rounded_box,
        rounded_panel_xz,
        rounded_panel_yz,
        rounded_prism_xy,
        safety_shelf_standoff_positions,
        servo_regulator_mount_positions,
        side_fairing_center_y,
        side_vent_layout,
        side_tof_pod_mount_positions,
        speaker_shell_mount_positions,
        speaker_slot_layout,
        tilt_servo_horn_center_y,
        tilt_servo_mount_plane_y,
        tilt_servo_mount_positions,
        vent_inlay_mount_positions,
        wheel_center_y,
        wheel_ground_z,
        wheel_tread_keepout,
    )
    from cad.python.robot_body_split import (
        alignment_pilot_interfaces,
        alignment_pilot_shape,
        split_parts,
    )


def intersection_volume(a, b) -> float:
    return float((a & b).volume)


def inside_box(shape, x_min, x_max, y_min, y_max, z_min, z_max, tolerance=0.05):
    box = shape.bounding_box()
    return (
        box.min.X >= x_min - tolerance
        and box.max.X <= x_max + tolerance
        and box.min.Y >= y_min - tolerance
        and box.max.Y <= y_max + tolerance
        and box.min.Z >= z_min - tolerance
        and box.max.Z <= z_max + tolerance
    )


def bounding_boxes_overlap(a, b, tolerance=0.01):
    box_a = a.bounding_box()
    box_b = b.bounding_box()
    return (
        min(float(box_a.max.X), float(box_b.max.X))
        - max(float(box_a.min.X), float(box_b.min.X))
        > tolerance
        and min(float(box_a.max.Y), float(box_b.max.Y))
        - max(float(box_a.min.Y), float(box_b.min.Y))
        > tolerance
        and min(float(box_a.max.Z), float(box_b.max.Z))
        - max(float(box_a.min.Z), float(box_b.min.Z))
        > tolerance
    )


def validate(bed: float, margin: float):
    p = Params()
    main = build_parts(p)
    fits = electronics_fit(p)
    split = split_parts(p)
    power_distribution_fit_names = tuple(
        name for name in fits if name.startswith("fit_power_distribution_")
    )
    failures = []

    for group_name, group in (("main", main), ("fit", fits), ("split", split)):
        for name, shape in group.items():
            if not shape.is_valid:
                failures.append(f"{group_name}:{name} is invalid")
            if len(shape.solids()) != 1:
                failures.append(f"{group_name}:{name} has {len(shape.solids())} solids")

    # Keep the molded-appliance silhouette and the real roof thickness tied to
    # shared parameters. The cavity uses a matching inner fillet so the softer
    # exterior rollover does not quietly turn the top skin into tissue paper.
    if p.body_edge_radius < 10.0:
        failures.append("body-shell exterior edge rollover is below the 10 mm concept baseline")
    if p.body_edge_radius - p.wall < 1.0:
        failures.append("body-shell inner edge radius collapses below 1 mm")
    if p.wall < p.min_wall:
        failures.append(
            f"body-shell nominal wall {p.wall:.2f} mm is below {p.min_wall:.2f} mm minimum"
        )
    roof_bottom = body_inner_roof_z(p)
    roof_probe_height = p.wall - 0.2
    for x, y in ((-105.0, 0.0), (0.0, -88.0), (0.0, 88.0)):
        probe = cylinder_z(
            1.5,
            roof_probe_height,
            (x, y, roof_bottom + p.wall / 2.0),
        )
        missing_volume = float(probe.volume) - intersection_volume(
            probe, main["body_shell"]
        )
        if missing_volume > 0.05:
            failures.append(
                f"body-shell roof is thinner than nominal near ({x:.0f}, {y:.0f}) "
                f"({missing_volume:.2f} mm^3 missing)"
            )

    # Every separately printable assembled part must occupy unique volume.
    # Touching mating faces are fine; any positive-volume overlap indicates an
    # impossible assembly, even if transparent Blender materials hide it.
    assembled_printables = printable_parts(main)
    for (name_a, shape_a), (name_b, shape_b) in combinations(
        assembled_printables.items(), 2
    ):
        if not bounding_boxes_overlap(shape_a, shape_b):
            continue
        volume = intersection_volume(shape_a, shape_b)
        if volume > 0.05:
            failures.append(
                f"printable assembly overlap: {name_a} vs {name_b} "
                f"({volume:.2f} mm^3)"
            )

    allowed_fit_overlaps = {
        frozenset(("fit_pi5", "fit_pi5_board")),
        frozenset(("fit_estop_switch_body", "fit_estop_threaded_barrel")),
        frozenset(("fit_estop_switch_body", "fit_estop_terminal_service")),
        frozenset(("fit_motor_cutoff", "fit_motor_cutoff_terminal_service")),
        frozenset(("fit_camera_module_3", "fit_camera_fov")),
        frozenset(("fit_motor_controller", "fit_motor_controller_board")),
        frozenset(("fit_motor_controller", "fit_motor_controller_airflow")),
        frozenset(("fit_motor_controller", "fit_motor_controller_terminal_service")),
    }
    distribution_service = "fit_power_distribution_fuse_service"
    for fit_name in power_distribution_fit_names:
        if fit_name != distribution_service:
            allowed_fit_overlaps.add(frozenset((distribution_service, fit_name)))
    allowed_fit_overlaps.add(
        frozenset(("fit_power_distribution_board", "fit_power_distribution_header"))
    )
    allowed_fit_overlaps.add(
        frozenset(("fit_power_distribution_header", "fit_power_distribution_receptacle"))
    )
    allowed_fit_overlaps.add(
        frozenset(
            (
                "fit_power_distribution_receptacle",
                "fit_power_distribution_harness_straight",
            )
        )
    )
    allowed_fit_overlaps.add(
        frozenset(
            (
                "fit_power_distribution_receptacle",
                "fit_power_distribution_harness_bend",
            )
        )
    )
    allowed_fit_overlaps.add(
        frozenset(
            (
                "fit_power_distribution_harness_straight",
                "fit_power_distribution_harness_bend",
            )
        )
    )
    for index in range(1, 5):
        allowed_fit_overlaps.add(
            frozenset(
                (
                    f"fit_power_distribution_holder_{index}",
                    f"fit_power_distribution_fuse_{index}",
                )
            )
        )
        allowed_fit_overlaps.add(
            frozenset(
                (
                    "fit_power_distribution_board",
                    f"fit_power_distribution_holder_{index}",
                )
            )
        )
    pico_nested_fits = (
        "fit_safety_mcu_board",
        "fit_safety_mcu_header_left",
        "fit_safety_mcu_header_right",
        "fit_safety_mcu_usb_service",
        "fit_safety_mcu_swd_service",
    )
    for fit_name in pico_nested_fits:
        allowed_fit_overlaps.add(frozenset(("fit_safety_mcu", fit_name)))
    for fit_name in ("fit_safety_mcu_usb_service", "fit_safety_mcu_swd_service"):
        allowed_fit_overlaps.add(frozenset(("fit_safety_mcu_board", fit_name)))
    for index in range(1, 5):
        allowed_fit_overlaps.add(
            frozenset(("fit_motor_controller", f"fit_motor_controller_standoff_{index}"))
        )
    for side in ("left", "right"):
        allowed_fit_overlaps.add(
            frozenset((f"fit_drive_motor_{side}", f"fit_drive_motor_cable_{side}"))
        )
        # The official motor and matching metal bracket share a clamped face;
        # their simplified envelope fillets overlap by a few cubic millimetres
        # at the lower bend even though the purchased pair is compatible.
        allowed_fit_overlaps.add(
            frozenset((f"fit_drive_motor_{side}", f"fit_drive_motor_bracket_{side}"))
        )
        # The motor lead corridor intentionally terminates inside its assigned
        # under-deck harness bundle; this is a routed connection, not a fit
        # collision between purchased components.
        allowed_fit_overlaps.add(
            frozenset(
                (f"fit_drive_motor_cable_{side}", f"fit_power_harness_{side}")
            )
        )
    # The simplified servo collar/spline solids intentionally enter their
    # matching R-ML24 horn spline cavities; the purchased interfaces are a
    # clamped spline fit rather than independent keepout volumes.
    allowed_fit_overlaps.add(frozenset(("fit_pan_servo", "fit_pan_servo_horn")))
    allowed_fit_overlaps.add(frozenset(("fit_tilt_servo", "fit_tilt_servo_horn")))
    for fit_name in ("fit_mute_switch_body", "fit_mute_switch_terminal_service"):
        allowed_fit_overlaps.add(frozenset(("fit_rear_service_bay", fit_name)))
    for fit_name in ("fit_charge_jack_body", "fit_charge_jack_terminal_service"):
        allowed_fit_overlaps.add(frozenset(("fit_rear_service_bay", fit_name)))
    allowed_fit_overlaps.add(
        frozenset(("fit_charge_jack_body", "fit_charge_jack_terminal_service"))
    )
    allowed_fit_overlaps.add(
        frozenset(("fit_charge_jack_body", "fit_charge_jack_bezel"))
    )
    allowed_fit_overlaps.add(
        frozenset(("fit_charge_jack_bezel", "fit_charge_jack_plug_service"))
    )
    allowed_fit_overlaps.add(
        frozenset(("fit_battery", "fit_battery_lead_service"))
    )
    for fit_name in (
        "fit_service_jack_body",
        "fit_service_jack_pcb",
        "fit_service_jack_wire_service",
    ):
        allowed_fit_overlaps.add(frozenset(("fit_rear_service_bay", fit_name)))
    allowed_fit_overlaps.add(
        frozenset(("fit_service_jack_body", "fit_service_jack_pcb"))
    )
    allowed_fit_overlaps.add(
        frozenset(("fit_service_jack_pcb", "fit_service_jack_wire_service"))
    )
    for (name_a, shape_a), (name_b, shape_b) in combinations(fits.items(), 2):
        if frozenset((name_a, name_b)) in allowed_fit_overlaps:
            continue
        volume = intersection_volume(shape_a, shape_b)
        if volume > 0.05:
            failures.append(f"fit collision: {name_a} vs {name_b} ({volume:.2f} mm^3)")

    motor_keepout_fits = (
        "fit_pi5",
        "fit_motor_controller",
        "fit_battery",
        "fit_battery_lead_service",
        "fit_safety_mcu",
        "fit_safety_mcu_board",
        "fit_safety_mcu_header_left",
        "fit_safety_mcu_header_right",
        "fit_safety_mcu_usb_service",
        "fit_safety_mcu_swd_service",
    )
    for fit_name in motor_keepout_fits:
        for pod_name in ("motor_pod_left", "motor_pod_right"):
            volume = intersection_volume(fits[fit_name], main[pod_name])
            if volume > 0.05:
                failures.append(f"motor-pod collision: {fit_name} vs {pod_name} ({volume:.2f} mm^3)")

    # Every mobility pod is a removable printed module seated on the base tray.
    # Mating faces may touch, but neither the shell nor tray may consume its
    # printable volume. This also guards the four-point tray pads beneath it.
    mobility_pod_names = (
        "motor_pod_left",
        "motor_pod_right",
        "front_idler_pod_left",
        "front_idler_pod_right",
    )
    for pod_name in mobility_pod_names:
        for target_name in ("body_shell", "base_tray"):
            volume = intersection_volume(main[pod_name], main[target_name])
            if volume > 0.05:
                failures.append(
                    f"mobility-pod collision: {pod_name} vs {target_name} ({volume:.2f} mm^3)"
                )

    wheel_names = (
        "wheel_left_1",
        "wheel_left_2",
        "wheel_right_1",
        "wheel_right_2",
    )
    for wheel_name in wheel_names:
        side = "left" if "_left_" in wheel_name else "right"
        pod_name = f"front_idler_pod_{side}" if wheel_name.endswith("_1") else f"motor_pod_{side}"
        for target_name in (
            "bumper_carrier",
            "body_shell",
            "base_tray",
            f"side_fairing_{side}",
            pod_name,
        ):
            volume = intersection_volume(main[wheel_name], main[target_name])
            if volume > 0.05:
                failures.append(f"wheel collision: {wheel_name} vs {target_name} ({volume:.2f} mm^3)")

    # The tire tangent plane is the assembled robot's ground datum. The
    # printed bumper and all hard parts must stay above it, while each wheel
    # center follows the shared partial-inset contract.
    ground_z = wheel_ground_z(p)
    if p.wheel_tread_count < 16 or p.wheel_tread_count % 2:
        failures.append("wheel tread must use an even count of at least 16 grooves")
    if not 1.0 <= p.wheel_tread_depth <= 3.0:
        failures.append("wheel tread depth must stay between 1 and 3 mm")
    if p.wheel_tread_side_margin < 1.5:
        failures.append("wheel tread leaves less than 1.5 mm of intact sidewall")
    for wheel_name in wheel_names:
        wheel_box = main[wheel_name].bounding_box()
        side_sign = -1 if "_left_" in wheel_name else 1
        expected_y = wheel_center_y(p, side_sign)
        wheel_index = int(wheel_name.rsplit("_", 1)[1]) - 1
        wheel_x = p.wheel_x_positions[wheel_index]
        actual_y = float((wheel_box.min.Y + wheel_box.max.Y) / 2.0)
        if abs(float(wheel_box.min.Z) - ground_z) > 0.05:
            failures.append(
                f"wheel misses ground datum: {wheel_name} "
                f"({float(wheel_box.min.Z):.2f} vs {ground_z:.2f} mm)"
            )
        if abs(actual_y - expected_y) > 0.05:
            failures.append(
                f"wheel inset mismatch: {wheel_name} ({actual_y:.2f} vs {expected_y:.2f} mm)"
            )
        tread_overlap = intersection_volume(
            wheel_tread_keepout(p, wheel_x, expected_y),
            main[wheel_name],
        )
        if tread_overlap > 0.05:
            failures.append(
                f"wheel tread grooves are blocked: {wheel_name} ({tread_overlap:.2f} mm^3)"
            )

    bumper_box = main["bumper_carrier"].bounding_box()
    expected_bumper_bottom = bumper_bottom_z(p)
    actual_bumper_bottom = float(bumper_box.min.Z)
    if abs(actual_bumper_bottom - expected_bumper_bottom) > 0.05:
        failures.append(
            "bumper bottom does not match shared ground-clearance contract: "
            f"{actual_bumper_bottom:.2f} vs {expected_bumper_bottom:.2f} mm"
        )
    if actual_bumper_bottom - ground_z < p.minimum_bumper_ground_clearance - 0.05:
        failures.append(
            "bumper ground clearance below minimum: "
            f"{actual_bumper_bottom - ground_z:.2f} mm"
        )

    # The compliant bumper wraps around the rigid chassis but must never occupy
    # the same assembled volume. Its inner cavity carries a deliberate radial
    # print/actuation gap around the shell and a larger gap around the tray.
    if p.bumper_body_clearance < 0.8:
        failures.append(
            f"bumper-to-body nominal clearance is too small: {p.bumper_body_clearance:.2f} mm"
        )
    for rigid_name in ("body_shell", "base_tray"):
        volume = intersection_volume(main["bumper_carrier"], main[rigid_name])
        if volume > 0.05:
            failures.append(
                f"bumper occupies rigid chassis volume: bumper_carrier vs {rigid_name} "
                f"({volume:.2f} mm^3)"
            )

    for part_name, part in main.items():
        if part_name in wheel_names:
            continue
        part_bottom = float(part.bounding_box().min.Z)
        if part_bottom < ground_z - 0.05:
            failures.append(
                f"hard part falls below tire ground datum: {part_name} ({part_bottom:.2f} mm)"
            )

    pod_seat_z = p.body_bottom + 4.0
    expected_pod_center_z = mobility_pod_shell_center_z(p)
    for pod_name in mobility_pod_names:
        pod_box = main[pod_name].bounding_box()
        actual_center_z = float((pod_box.min.Z + pod_box.max.Z) / 2.0)
        if abs(float(pod_box.min.Z) - pod_seat_z) > 0.05:
            failures.append(
                f"mobility pod misses tray seating plane: {pod_name} "
                f"({float(pod_box.min.Z):.2f} vs {pod_seat_z:.2f} mm)"
            )
        if abs(actual_center_z - expected_pod_center_z) > 0.05:
            failures.append(
                f"mobility pod shell center mismatch: {pod_name} "
                f"({actual_center_z:.2f} vs {expected_pod_center_z:.2f} mm)"
            )

    # Bumper switches are rigid chassis references; the TPU bumper remains a
    # separate locally compliant part. Each PETG plate seats beneath the tray,
    # its body rises through a tray pocket, and a nominal 2 mm inner-wall
    # displacement must reach the switch envelope without preload at rest.
    tray_bottom = p.body_bottom - p.tray_thickness
    plate_z = bumper_switch_plate_center_z(p)
    plate_bottom = plate_z - p.bumper_switch_plate_thickness / 2.0
    plate_top = plate_z + p.bumper_switch_plate_thickness / 2.0
    insert_top = tray_bottom + p.bumper_switch_tray_insert_depth
    if p.body_bottom - insert_top < 1.2:
        failures.append("bumper-switch tray inserts leave less than 1.2 mm roof")

    required_pretravel = p.bumper_switch_free_position - (
        p.bumper_switch_operating_position - p.bumper_switch_operating_tolerance
    )
    available_nominal_travel = (
        p.bumper_switch_actuation_travel - p.bumper_switch_nominal_gap
    )
    total_plunger_travel = (
        p.bumper_switch_free_position - p.bumper_switch_total_travel_position
    )
    available_stop_travel = p.bumper_switch_stop_travel - p.bumper_switch_nominal_gap
    if available_nominal_travel < required_pretravel + 0.3:
        failures.append(
            "D2HW bumper-switch nominal travel has less than 0.3 mm guaranteed "
            f"electrical margin ({available_nominal_travel:.2f} vs {required_pretravel:.2f} mm)"
        )
    if available_nominal_travel >= total_plunger_travel - 0.2:
        failures.append("D2HW bumper-switch nominal travel leaves inadequate overtravel")
    if available_stop_travel >= total_plunger_travel:
        failures.append("bumper-switch rigid stop allows D2HW plunger bottoming")

    for name, orientation, x, y in bumper_switch_layout():
        fit_name = f"fit_bumper_switch_{name}"
        plate_name = f"bumper_switch_mount_{name}"
        fit_shape = fits[fit_name]
        plate_shape = main[plate_name]
        plate_box = plate_shape.bounding_box()
        fit_box = fit_shape.bounding_box()

        if abs(float(plate_box.min.Z) - plate_bottom) > 0.05:
            failures.append(
                f"bumper-switch plate base thickness drift: {plate_name} "
                f"({float(plate_box.min.Z):.2f} vs {plate_bottom:.2f} mm)"
            )
        if float(plate_box.min.Z) < ground_z - 0.05:
            failures.append(f"bumper-switch plate falls below ground datum: {plate_name}")
        if float(fit_box.min.Z) - plate_top < 0.25:
            failures.append(f"bumper-switch body lacks plate-top clearance: {fit_name}")

        for target_name in (
            "base_tray",
            "bumper_carrier",
            "body_shell",
            plate_name,
            *wheel_names,
            *mobility_pod_names,
        ):
            volume = intersection_volume(fit_shape, main[target_name])
            if volume > 0.05:
                failures.append(
                    f"bumper-switch collision: {fit_name} vs {target_name} "
                    f"({volume:.2f} mm^3)"
                )

        for target_name in (
            "base_tray",
            "bumper_carrier",
            *wheel_names,
            *mobility_pod_names,
        ):
            volume = intersection_volume(plate_shape, main[target_name])
            if volume > 0.05:
                failures.append(
                    f"bumper-switch plate collision: {plate_name} vs {target_name} "
                    f"({volume:.2f} mm^3)"
                )

        rest_patch = bumper_switch_contact_patch(p, orientation, x, y)
        rest_patch_volume = float(rest_patch.volume)
        supported_patch_volume = intersection_volume(rest_patch, main["bumper_carrier"])
        if rest_patch_volume - supported_patch_volume > 0.05:
            failures.append(f"bumper-switch contact patch escapes TPU carrier: {name}")
        if intersection_volume(rest_patch, fit_shape) > 0.05:
            failures.append(f"bumper-switch is preloaded at rest: {name}")
        compressed_patch = bumper_switch_contact_patch(
            p,
            orientation,
            x,
            y,
            p.bumper_switch_actuation_travel,
        )
        if intersection_volume(compressed_patch, fit_shape) <= 0.05:
            failures.append(
                f"bumper-switch does not actuate at {p.bumper_switch_actuation_travel:.1f} mm: {name}"
            )
        operating_target = bumper_switch_travel_target(
            p, orientation, x, y, "operating"
        )
        if intersection_volume(compressed_patch, operating_target) <= 0.05:
            failures.append(
                f"bumper-switch fails worst-case D2HW operating position: {name}"
            )
        total_target = bumper_switch_travel_target(p, orientation, x, y, "total")
        if intersection_volume(compressed_patch, total_target) > 0.05:
            failures.append(f"bumper-switch bottoms D2HW at nominal travel: {name}")

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
            intersection_volume(patch, stop)
            for patch, stop in zip(stop_patches, stop_shapes)
        )
        if stop_contact <= 0.05:
            failures.append(f"bumper-switch rigid stops miss TPU wall: {name}")
        if intersection_volume(stop_patch, total_target) > 0.05:
            failures.append(f"bumper-switch stop reaches D2HW total travel: {name}")
        rest_stop_patches = bumper_switch_stop_contact_patches(
            p,
            orientation,
            x,
            y,
            0.0,
        )
        for patch, stop in zip(rest_stop_patches, stop_shapes):
            if intersection_volume(patch, stop) > 0.05:
                failures.append(f"bumper-switch rigid stop preloads TPU wall: {name}")

        probe_bottom = plate_bottom - 1.0
        probe_top = insert_top - 1.0
        for hole_x, hole_y in bumper_switch_mount_positions(orientation, x, y):
            probe = cylinder_z(
                p.m3_clearance_hole / 2.0 - 0.1,
                probe_top - probe_bottom,
                (hole_x, hole_y, (probe_bottom + probe_top) / 2.0),
            )
            for target_name in (plate_name, "base_tray"):
                volume = intersection_volume(probe, main[target_name])
                if volume > 0.05:
                    failures.append(
                        f"blocked bumper-switch screw on {name} at ({hole_x:.0f},{hole_y:.0f}): "
                        f"{target_name} ({volume:.2f} mm^3)"
                    )

        for hole_x, hole_y in bumper_switch_body_mount_positions(
            p, orientation, x, y
        ):
            probe = cylinder_z(
                p.bumper_switch_mount_hole / 2.0 - 0.1,
                p.bumper_switch_plate_thickness + 2.0,
                (hole_x, hole_y, plate_z),
            )
            volume = intersection_volume(probe, plate_shape)
            if volume > 0.05:
                failures.append(
                    f"blocked D2HW mounting screw on {name} at "
                    f"({hole_x:.1f},{hole_y:.1f}): {volume:.2f} mm^3"
                )

    # The top stack and head are separate printable parts. These interfaces may
    # touch at mating faces but must not occupy the same volume.
    rear_cartridge_names = tuple(
        f"rear_service_cartridge_{role}"
        for role, _center_y, _center_z in rear_service_cartridge_layout(p)
    )
    head_interface_pairs = (
        ("body_shell", "lid_reveal"),
        ("body_shell", "top_lid"),
        ("body_shell", "side_fairing_left"),
        ("body_shell", "side_fairing_right"),
        ("body_shell", "rear_service_panel"),
        ("lid_reveal", "top_lid"),
        ("top_lid", "estop_well"),
        ("top_lid", "top_vent_inlay"),
        ("top_vent_inlay", "estop_well"),
        ("neck_collar", "top_lid"),
        ("neck_collar", "lid_reveal"),
        ("neck_collar", "top_vent_inlay"),
        ("neck", "body_shell"),
        ("neck", "top_lid"),
        ("neck", "neck_collar"),
        ("neck", "head_shell"),
        ("head_tilt_yoke", "head_shell"),
        ("head_tilt_drive_adapter", "head_shell"),
        ("head_tilt_passive_cartridge", "head_shell"),
        ("head_tilt_drive_adapter", "head_tilt_yoke"),
        ("head_tilt_passive_cartridge", "head_tilt_yoke"),
        ("head_faceplate", "head_shell"),
        ("camera_lens_hardware", "head_shell"),
        ("camera_lens_hardware", "head_faceplate"),
        ("head_rear_cover", "head_shell"),
        ("camera_carrier", "head_shell"),
        ("head_eye_led_carrier_1", "head_shell"),
        ("head_eye_led_carrier_2", "head_shell"),
        ("front_status_led_carrier_1", "body_shell"),
        ("front_status_led_carrier_2", "body_shell"),
        ("front_sensor_fascia", "body_shell"),
        ("front_sensor_window", "front_sensor_fascia"),
    ) + tuple(("body_shell", name) for name in rear_cartridge_names) + tuple(
        ("rear_service_panel", name) for name in rear_cartridge_names
    ) + tuple(combinations(rear_cartridge_names, 2))
    for name_a, name_b in head_interface_pairs:
        volume = intersection_volume(main[name_a], main[name_b])
        if volume > 0.05:
            failures.append(f"head interface collision: {name_a} vs {name_b} ({volume:.2f} mm^3)")

    # Shared screw paths must remain open through both mating parts.
    for x, y in lid_mount_positions():
        probe = cylinder_z(
            p.m3_clearance_hole / 2.0 - 0.1,
            20.0,
            (x, y, p.body_bottom + p.body_height),
        )
        for target_name in ("body_shell", "top_lid"):
            volume = intersection_volume(probe, main[target_name])
            if volume > 0.05:
                failures.append(
                    f"blocked lid screw path at ({x:.0f},{y:.0f}): "
                    f"{target_name} ({volume:.2f} mm^3)"
                )

    for side, sign in (("left", -1), ("right", 1)):
        fairing_name = f"side_fairing_{side}"
        fairing_y = abs(side_fairing_center_y(p, sign))
        for x, z in fairing_mount_positions():
            probe = cylinder_y(
                p.m3_clearance_hole / 2.0 - 0.1,
                24.0,
                (x, sign * fairing_y, z),
            )
            for target_name in ("body_shell", fairing_name):
                volume = intersection_volume(probe, main[target_name])
                if volume > 0.05:
                    failures.append(
                        f"blocked fairing screw path on {side} at X={x:.0f}: "
                        f"{target_name} ({volume:.2f} mm^3)"
                    )

            # Every retained screw needs real fairing material around its
            # clearance hole; an open path alone must not pass a detached cap.
            support_probe = cylinder_y(4.8, 3.0, (x, sign * fairing_y, z))
            support_probe = support_probe - cylinder_y(
                p.m3_clearance_hole / 2.0 + 0.1,
                5.0,
                (x, sign * fairing_y, z),
            )
            if intersection_volume(support_probe, main[fairing_name]) < 50.0:
                failures.append(
                    f"fairing screw lacks surrounding material on {side} at X={x:.0f}"
                )

        # The concept-facing side skin must remain a scalloped pair of arch
        # caps, not regress to the old full-height slab. The center is open
        # around the side ToF, while a narrow high bridge keeps one solid.
        mid_x = sum(p.wheel_x_positions) / 2.0
        relief_probe = rounded_box(
            34.0,
            8.0,
            30.0,
            3.0,
            (mid_x, sign * fairing_y, 96.0),
        )
        if intersection_volume(relief_probe, main[fairing_name]) > 0.05:
            failures.append(f"side-fairing center relief is blocked on {side}")
        panel_top = p.side_fairing_center_z + p.side_fairing_height / 2.0
        bridge_probe = rounded_box(
            20.0,
            3.0,
            5.0,
            1.0,
            (
                mid_x,
                sign * fairing_y,
                panel_top - p.side_fairing_bridge_height / 2.0,
            ),
        )
        if intersection_volume(bridge_probe, main[fairing_name]) < 100.0:
            failures.append(f"side-fairing upper bridge is disconnected on {side}")

        # The removable skin replaces the old proud cap visually: its exterior
        # face shares the molded body datum, while the deeper shell pocket
        # leaves a small clamp gap and a real continuous backing membrane.
        fairing_box = main[fairing_name].bounding_box()
        exterior_y = float(fairing_box.min.Y if sign < 0 else fairing_box.max.Y)
        expected_exterior_y = sign * p.body_width / 2.0
        if abs(exterior_y - expected_exterior_y) > 0.05:
            failures.append(
                f"side-fairing exterior is not flush on {side}: "
                f"{exterior_y:.2f} vs {expected_exterior_y:.2f} mm"
            )
        clamp_gap = p.side_fairing_recess_depth - p.side_fairing_thickness
        if not 0.15 <= clamp_gap <= 0.5:
            failures.append(
                f"side-fairing clamp gap is outside 0.15-0.5 mm: {clamp_gap:.2f} mm"
            )
        backing_wall = p.wall - p.side_fairing_recess_depth
        if backing_wall < 0.8:
            failures.append(
                f"side-fairing recess leaves only {backing_wall:.2f} mm of shell wall"
            )
        backing_center_y = sign * (
            p.body_width / 2.0 - p.side_fairing_recess_depth - backing_wall / 2.0
        )
        backing_probe = cylinder_y(
            1.0,
            max(backing_wall - 0.1, 0.1),
            (-105.0, backing_center_y, 125.0),
        )
        missing_backing = float(backing_probe.volume) - intersection_volume(
            backing_probe, main["body_shell"]
        )
        if missing_backing > 0.05:
            failures.append(
                f"side-fairing recess lacks continuous backing wall on {side} "
                f"({missing_backing:.2f} mm^3 missing)"
            )

    # BOM coverage contracts: every currently selected or reserved MVP module
    # needs both a review envelope and a printable support/service interface.
    audio_amp_fit_names = tuple(
        f"fit_audio_amp_{side}{suffix}"
        for side in ("left", "right")
        for suffix in (
            "",
            "_header_service",
            "_screwdriver_service",
            "_speaker_wire",
            "_standoff_1",
            "_standoff_2",
        )
    )
    front_idler_fit_names = tuple(
        name
        for side in ("left", "right")
        for name in front_idler_hardware_names(side)
    )
    component_contracts = {
        "Raspberry Pi 5": (("fit_pi5",), ("base_tray",)),
        "Camera Module 3 Wide": (
            ("fit_camera_module_3", "fit_camera_fov"),
            ("camera_carrier", "head_faceplate"),
        ),
        "microphone array": (("fit_mic_array",), ("mic_array_cradle",)),
        "speaker pair": (("fit_speaker_left", "fit_speaker_right"), ("speaker_mount_left", "speaker_mount_right")),
        "stereo I2S amplifier pair": (
            audio_amp_fit_names,
            ("speaker_mount_left", "speaker_mount_right"),
        ),
        "Pi buck regulator": (
            (
                "fit_pi_buck_regulator",
                "fit_pi_buck_terminal_service_front",
                "fit_pi_buck_terminal_service_rear",
                "fit_pi_regulator_standoff_1",
                "fit_pi_regulator_standoff_2",
                "fit_pi_regulator_standoff_3",
                "fit_pi_regulator_standoff_4",
            ),
            ("power_service_deck",),
        ),
        "servo regulator": (
            (
                "fit_servo_regulator",
                "fit_servo_regulator_wire_service",
                "fit_servo_regulator_standoff_1",
                "fit_servo_regulator_standoff_2",
                "fit_servo_regulator_standoff_3",
            ),
            ("power_service_deck",),
        ),
        "motor cutoff": (
            (
                "fit_motor_cutoff",
                "fit_motor_cutoff_terminal_service",
                "fit_motor_cutoff_metal_plate",
            ),
            ("power_service_deck",),
        ),
        "power distribution": (
            power_distribution_fit_names,
            ("power_service_deck", "power_distribution_cover"),
        ),
        "rear switches/connectors": (("fit_rear_service_bay",), ("rear_service_panel",)),
        "rear charge-only inlet": (
            (
                "fit_charge_jack_body",
                "fit_charge_jack_bezel",
                "fit_charge_jack_terminal_service",
                "fit_charge_jack_plug_service",
            ),
            ("rear_service_cartridge_power_charge", "rear_service_panel"),
        ),
        "physical mute switch": (
            (
                "fit_mute_switch_body",
                "fit_mute_switch_bezel",
                "fit_mute_switch_actuator",
                "fit_mute_switch_led_ring",
                "fit_mute_switch_terminal_service",
            ),
            ("rear_service_cartridge_mute_status", "rear_service_panel"),
        ),
        "rear UART service jack": (
            (
                "fit_service_jack_body",
                "fit_service_jack_pcb",
                "fit_service_jack_wire_service",
                "fit_service_jack_plug_service",
            ),
            (
                "rear_service_cartridge_service_data",
                "rear_service_data_carrier",
                "rear_service_panel",
            ),
        ),
        "safety MCU": (
            (
                "fit_safety_mcu",
                "fit_safety_mcu_board",
                "fit_safety_mcu_header_left",
                "fit_safety_mcu_header_right",
                "fit_safety_mcu_usb_service",
                "fit_safety_mcu_swd_service",
            ),
            ("safety_mcu_mount",),
        ),
        "motor controller": (
            (
                "fit_motor_controller",
                "fit_motor_controller_board",
                "fit_motor_controller_terminal_service",
                "fit_motor_controller_airflow",
            ),
            ("motor_controller_mount",),
        ),
        "rear drive motors": (
            (
                "fit_drive_motor_left",
                "fit_drive_motor_right",
                "fit_drive_motor_bracket_left",
                "fit_drive_motor_bracket_right",
                "fit_drive_motor_hub_left",
                "fit_drive_motor_hub_right",
                "fit_drive_motor_cable_left",
                "fit_drive_motor_cable_right",
                "fit_drive_motor_bracket_spacer_left_1",
                "fit_drive_motor_bracket_spacer_left_2",
                "fit_drive_motor_bracket_spacer_left_3",
                "fit_drive_motor_bracket_spacer_right_1",
                "fit_drive_motor_bracket_spacer_right_2",
                "fit_drive_motor_bracket_spacer_right_3",
            ),
            (
                "motor_pod_left",
                "motor_pod_right",
                "motor_pod_cover_left",
                "motor_pod_cover_right",
            ),
        ),
        "front support idlers": (
            front_idler_fit_names,
            (
                "front_idler_pod_left",
                "front_idler_pod_right",
                "front_idler_retainer_left_inner",
                "front_idler_retainer_left_outer",
                "front_idler_retainer_right_inner",
                "front_idler_retainer_right_outer",
            ),
        ),
        "bumper switches": (
            tuple(f"fit_bumper_switch_{name}" for name, _orientation, _x, _y in bumper_switch_layout()),
            tuple(f"bumper_switch_mount_{name}" for name, _orientation, _x, _y in bumper_switch_layout()),
        ),
        "expression LEDs": (
            (
                "fit_head_eye_led_left",
                "fit_head_eye_led_right",
                "fit_front_status_led_left",
                "fit_front_status_led_right",
                "fit_head_eye_led_left_jst_service",
                "fit_head_eye_led_right_jst_service",
                "fit_front_status_led_left_jst_service",
                "fit_front_status_led_right_jst_service",
                "fit_head_eye_led_left_spacer_1",
                "fit_head_eye_led_left_spacer_2",
                "fit_head_eye_led_right_spacer_1",
                "fit_head_eye_led_right_spacer_2",
                "fit_front_status_led_left_spacer_1",
                "fit_front_status_led_left_spacer_2",
                "fit_front_status_led_right_spacer_1",
                "fit_front_status_led_right_spacer_2",
            ),
            (
                "head_eye_led_carrier_1",
                "head_eye_led_carrier_2",
                "front_status_led_carrier_1",
                "front_status_led_carrier_2",
            ),
        ),
        "battery": (
            ("fit_battery", "fit_battery_lead_service"),
            ("battery_cradle",),
        ),
        "E-stop": (
            (
                "fit_estop_switch_body",
                "fit_estop_threaded_barrel",
                "fit_estop_terminal_service",
                "fit_estop_yellow_legend",
            ),
            ("estop_well", "estop_backing_plate"),
        ),
        "carry interface": (
            (
                "fit_carry_clamp_plate_left",
                "fit_carry_clamp_plate_right",
                "fit_carry_webbing_stowed_left",
                "fit_carry_webbing_stowed_right",
            ),
            ("base_tray",),
        ),
        "power harness routing": (
            ("fit_power_harness_left", "fit_power_harness_right"),
            (
                "power_harness_rail_left",
                "power_harness_rail_right",
                "power_service_deck",
            ),
        ),
        "pan/tilt mechanism": (
            (
                "fit_pan_servo",
                "fit_pan_servo_horn",
                "fit_pan_bearing",
                "fit_tilt_servo",
                "fit_tilt_servo_horn",
                "fit_tilt_passive_bushing",
                "fit_tilt_shoulder_bolt",
                "fit_servo_cable_corridor",
            ),
            (
                "pan_servo_mount",
                "pan_bearing_retainer",
                "neck",
                "head_tilt_yoke",
                "head_tilt_drive_adapter",
                "head_tilt_passive_cartridge",
            ),
        ),
    }
    for label, (fit_names, part_names) in component_contracts.items():
        missing_fits = [name for name in fit_names if name not in fits]
        missing_parts = [name for name in part_names if name not in main]
        if missing_fits or missing_parts:
            failures.append(
                f"component coverage missing for {label}: "
                f"fits={','.join(missing_fits) or 'ok'} parts={','.join(missing_parts) or 'ok'}"
            )

    # The carry loops are soft purchased webbing, but their load enters the
    # robot through metal plates and M4 through-bolts across both tray halves.
    # Prove every strap/bolt path is open and the stowed loops stay above the
    # wheel-ground plane without consuming electronics or mobility geometry.
    carry_print_targets = (
        "body_shell",
        "base_tray",
        "battery_cradle",
        "motor_controller_mount",
        "motor_pod_left",
        "motor_pod_right",
        "front_idler_pod_left",
        "front_idler_pod_right",
    )
    carry_stow_targets = (
        "base_tray",
        "bumper_carrier",
        "motor_pod_left",
        "motor_pod_right",
        "front_idler_pod_left",
        "front_idler_pod_right",
        *wheel_names,
    )
    carry_ground_z = wheel_ground_z(p)
    for side, side_sign in (("left", -1), ("right", 1)):
        plate_name = f"fit_carry_clamp_plate_{side}"
        strap_name = f"fit_carry_webbing_stowed_{side}"
        plate = fits[plate_name]
        strap = fits[strap_name]

        plate_box = plate.bounding_box()
        if not (plate_box.min.X < -0.05 and plate_box.max.X > 0.05):
            failures.append(f"carry clamp plate does not bridge tray split: {side}")
        if float(strap.bounding_box().min.Z) < carry_ground_z + 3.0:
            failures.append(
                f"stowed carry webbing lacks ground clearance: {side} "
                f"({float(strap.bounding_box().min.Z) - carry_ground_z:.2f} mm)"
            )

        for target_name in carry_print_targets:
            volume = intersection_volume(plate, main[target_name])
            if volume > 0.05:
                failures.append(
                    f"carry clamp collision: {plate_name} vs {target_name} "
                    f"({volume:.2f} mm^3)"
                )
        for target_name in carry_stow_targets:
            volume = intersection_volume(strap, main[target_name])
            if volume > 0.05:
                failures.append(
                    f"stowed carry webbing collision: {strap_name} vs {target_name} "
                    f"({volume:.2f} mm^3)"
                )

        for x, y in carry_anchor_slot_positions(p, side_sign):
            probe = rounded_prism_xy(
                p.carry_slot_width - 0.2,
                p.carry_slot_length - 0.2,
                p.tray_thickness + p.carry_anchor_doubler_height + 5.0,
                min(p.carry_slot_width / 2.0 - 0.3, 1.9),
                (x, y, p.body_bottom - p.tray_thickness / 2.0),
            )
            for target_name in (
                "base_tray",
                "base_tray_half_front" if x < 0 else "base_tray_half_rear",
            ):
                target = main[target_name] if target_name in main else split[target_name]
                volume = intersection_volume(probe, target)
                if volume > 0.05:
                    failures.append(
                        f"blocked carry webbing slot on {side} at X={x:.0f}: "
                        f"{target_name} ({volume:.2f} mm^3)"
                    )

        for x, y in carry_anchor_fastener_positions(p, side_sign):
            probe = cylinder_z(
                p.m4_clearance_hole / 2.0 - 0.1,
                p.tray_thickness + p.carry_anchor_doubler_height + 8.0,
                (x, y, p.body_bottom - p.tray_thickness / 2.0),
            )
            for target_name in (
                "base_tray",
                "base_tray_half_front" if x < 0 else "base_tray_half_rear",
            ):
                target = main[target_name] if target_name in main else split[target_name]
                volume = intersection_volume(probe, target)
                if volume > 0.05:
                    failures.append(
                        f"blocked carry M4 path on {side} at ({x:.0f},{y:.0f}): "
                        f"{target_name} ({volume:.2f} mm^3)"
                    )

    # The IDEC E-stop clamps only the removable 4 mm keyed mount panel. The
    # larger contact body passes through lid/shell/backing, while four long M3
    # screws sandwich the top panel, annular shell bosses, and underside plate.
    estop_plate = main["estop_backing_plate"]
    estop_panel = main["estop_well"]
    estop_shell_overlap = intersection_volume(estop_plate, main["body_shell"])
    if estop_shell_overlap > 0.05:
        failures.append(
            f"E-stop backing plate collides with body shell ({estop_shell_overlap:.2f} mm^3)"
        )

    required_boss_clearance = (
        p.estop_backing_collar_outer_radius + p.estop_mount_boss_radius + 0.5
    )
    if p.estop_mount_radius < required_boss_clearance:
        failures.append(
            "E-stop boss radius overlaps central collar: "
            f"{p.estop_mount_radius:.2f} < {required_boss_clearance:.2f} mm"
        )

    if not (
        p.estop_panel_thickness_min
        <= p.estop_mount_panel_thickness
        <= p.estop_panel_thickness_max
    ):
        failures.append(
            "IDEC E-stop clamp panel is outside the 0.8-6.0 mm range: "
            f"{p.estop_mount_panel_thickness:.2f} mm"
        )

    panel_bottom = estop_mount_panel_bottom_z(p)
    panel_top = estop_mount_panel_top_z(p)
    panel_box = estop_panel.bounding_box()
    if abs(float(panel_box.min.Z) - panel_bottom) > 0.05:
        failures.append("E-stop mount panel misses its lid recess floor")
    if abs(float(panel_box.max.Z) - panel_top) > 0.05:
        failures.append("E-stop mount panel clamp thickness drifted")
    if intersection_volume(estop_panel, main["top_lid"]) > 0.05:
        failures.append("E-stop mount panel collides with recessed top lid")

    keyed_gauge = estop_keyed_panel_cutout(
        p,
        p.estop_mount_panel_thickness + 2.0,
        (panel_bottom + panel_top) / 2.0,
    )
    if intersection_volume(keyed_gauge, estop_panel) > 0.05:
        failures.append("IDEC E-stop keyed 22.5 mm panel cutout is blocked")

    threaded_barrel = fits["fit_estop_threaded_barrel"]
    for target_name in ("body_shell", "top_lid", "estop_well", "estop_backing_plate"):
        volume = intersection_volume(threaded_barrel, main[target_name])
        if volume > 0.05:
            failures.append(
                f"blocked E-stop threaded-barrel path: {target_name} ({volume:.2f} mm^3)"
            )

    estop_body = fits["fit_estop_switch_body"]
    for target_name in ("body_shell", "top_lid", "estop_backing_plate"):
        volume = intersection_volume(estop_body, main[target_name])
        if volume > 0.05:
            failures.append(
                f"blocked IDEC E-stop 37 mm body pass: {target_name} "
                f"({volume:.2f} mm^3)"
            )

    plate_z = estop_backing_center_z(p)
    plate_bottom = plate_z - p.estop_backing_plate_thickness / 2.0
    plate_top = plate_z + p.estop_backing_plate_thickness / 2.0
    boss_bottom = plate_top + 0.2
    screw_probe_bottom = plate_bottom - 0.4
    screw_probe_top = panel_bottom + p.estop_mount_panel_insert_depth - 0.2
    for x, y in estop_mount_positions(p):
        probe = cylinder_z(
            p.m3_clearance_hole / 2.0 - 0.1,
            screw_probe_top - screw_probe_bottom,
            (x, y, (screw_probe_bottom + screw_probe_top) / 2.0),
        )
        for target_name in (
            "estop_backing_plate",
            "body_shell",
            "top_lid",
            "estop_well",
        ):
            volume = intersection_volume(probe, main[target_name])
            if volume > 0.05:
                failures.append(
                    f"blocked E-stop backing screw at ({x:.0f},{y:.0f}): "
                    f"{target_name} ({volume:.2f} mm^3)"
                )

    # Camera carrier fasteners use the official Camera Module 3 board pattern;
    # separate carrier-to-head screws remain open into blind insert posts.
    camera_fit_x, camera_board_z, camera_carrier_x = camera_reference(p)
    for y, z_offset in camera_board_hole_offsets(p):
        probe = cylinder_x(
            p.camera_mount_hole / 2.0,
            8.0,
            (camera_carrier_x, y, camera_board_z + z_offset),
        )
        volume = intersection_volume(probe, main["camera_carrier"])
        if volume > 0.05:
            failures.append(
                f"blocked camera board screw at Y={y:.1f}, Z={camera_board_z + z_offset:.1f} "
                f"({volume:.2f} mm^3)"
            )
    for y in (-22.0, 22.0):
        for z in (camera_board_z - 15.0, camera_board_z + 15.0):
            probe = cylinder_x(
                p.m3_clearance_hole / 2.0 - 0.1,
                12.25,
                (camera_carrier_x - 4.5, y, z),
            )
            for target_name in ("camera_carrier", "head_shell"):
                volume = intersection_volume(probe, main[target_name])
                if volume > 0.05:
                    failures.append(
                        f"blocked camera carrier screw at Y={y:.0f}, Z={z:.1f}: "
                        f"{target_name} ({volume:.2f} mm^3)"
                    )

    if not (
        p.head_lens_outer_radius
        > p.head_lens_mid_radius
        > p.head_lens_inner_radius
        > p.head_lens_clear_radius
    ):
        failures.append("camera bezel radii no longer form a descending stepped annulus")
    camera_lens_corner_radius = (p.camera_lens_housing_width / 2.0) * (2.0**0.5)
    if p.head_lens_clear_radius - camera_lens_corner_radius < 0.5:
        failures.append("camera bezel leaves less than 0.5 mm around the lens housing corners")
    head_front_x = p.head_center_x - p.head_depth / 2.0
    camera_optical_probe = cylinder_x(
        min(p.head_lens_clear_radius, p.head_camera_aperture_radius) - 0.25,
        32.0,
        (head_front_x - 1.0, 0.0, p.head_center_z - 1.0),
    )
    for target_name in ("head_faceplate", "head_shell"):
        volume = intersection_volume(camera_optical_probe, main[target_name])
        if volume > 0.05:
            failures.append(
                f"blocked camera optical path: {target_name} ({volume:.2f} mm^3)"
            )
    expected_fov = camera_field_of_view_keepout(p)
    fov_volume_delta = abs(
        float(expected_fov.volume) - float(fits["fit_camera_fov"].volume)
    )
    if fov_volume_delta > 0.05:
        failures.append(
            "camera FOV envelope drifted from shared parameters "
            f"({fov_volume_delta:.2f} mm^3)"
        )
    for target_name in ("head_faceplate", "head_shell"):
        volume = intersection_volume(fits["fit_camera_fov"], main[target_name])
        if volume > 0.05:
            failures.append(
                f"camera horizontal FOV is vignetted by {target_name} ({volume:.2f} mm^3)"
            )

    # Preserve the concept's cream front frame and prove both removable head
    # panels still have complete screw paths after cosmetic geometry changes.
    head_front_x = p.head_center_x - p.head_depth / 2.0
    bezel_front_x = head_front_x - 3.0 - p.head_bezel_depth / 2.0
    face_x = head_front_x - 3.0
    faceplate_front_x = face_x - p.head_faceplate_depth / 2.0
    if faceplate_front_x - bezel_front_x < 1.0:
        failures.append(
            "head faceplate is not visibly recessed behind cream bezel: "
            f"{faceplate_front_x - bezel_front_x:.2f} mm"
        )
    if p.head_bezel_opening_width - p.head_faceplate_width < 1.0:
        failures.append("head faceplate lacks side clearance inside bezel opening")
    if p.head_bezel_opening_height - p.head_faceplate_height < 1.0:
        failures.append("head faceplate lacks vertical clearance inside bezel opening")
    if p.head_width / p.body_width > 0.65:
        failures.append(
            f"head width regressed beyond compact concept ratio: "
            f"{p.head_width / p.body_width:.3f}"
        )
    if p.head_height / p.head_width > 0.53:
        failures.append(
            f"head capsule is too tall for concept ratio: "
            f"{p.head_height / p.head_width:.3f}"
        )
    if p.head_depth / p.head_width > 0.53:
        failures.append(
            f"head capsule is too deep for concept ratio: "
            f"{p.head_depth / p.head_width:.3f}"
        )
    if p.head_width - p.head_bezel_outer_width < 4.0:
        failures.append("head shell leaves less than 2 mm per side around cream bezel")
    if p.head_height - p.head_bezel_outer_height < 2.0:
        failures.append("head shell leaves less than 1 mm above/below cream bezel")

    yoke_y = head_tilt_yoke_center_y(p)
    yoke_outer_y = yoke_y + 2.5
    adapter_inner_y = (
        head_tilt_adapter_center_y(p, 1) - p.head_tilt_adapter_thickness / 2.0
    )
    if adapter_inner_y - yoke_outer_y < 3.0:
        failures.append(
            "compact head leaves less than 3 mm between fixed yoke and drive adapter"
        )

    face_probe_front = faceplate_front_x - 0.4
    face_probe_rear = head_front_x + 13.4
    for y, z in head_face_mount_positions(p):
        probe = cylinder_x(
            p.m2_5_clearance_hole / 2.0 - 0.1,
            face_probe_rear - face_probe_front,
            ((face_probe_front + face_probe_rear) / 2.0, y, z),
        )
        for target_name in ("head_faceplate", "head_shell"):
            volume = intersection_volume(probe, main[target_name])
            if volume > 0.05:
                failures.append(
                    f"blocked head-face screw at Y={y:.0f}, Z={z:.0f}: "
                    f"{target_name} ({volume:.2f} mm^3)"
                )

    head_rear_x = p.head_center_x + p.head_depth / 2.0
    for y, z in head_rear_mount_positions(p):
        probe = cylinder_x(
            p.m2_5_clearance_hole / 2.0 - 0.1,
            20.0,
            (head_rear_x - 5.0, y, z),
        )
        for target_name in ("head_rear_cover", "head_shell"):
            volume = intersection_volume(probe, main[target_name])
            if volume > 0.05:
                failures.append(
                    f"blocked head-rear screw at Y={y:.0f}, Z={z:.0f}: "
                    f"{target_name} ({volume:.2f} mm^3)"
                )

    # Upward speaker paths and high side vents must pass through every skin.
    top_z = p.body_bottom + p.body_height
    for x, y in speaker_slot_layout():
        probe = rounded_prism_xy(26.0, 2.4, 18.0, 1.0, (x, y, top_z + 2.0))
        for target_name in ("body_shell", "top_lid"):
            volume = intersection_volume(probe, main[target_name])
            if volume > 0.05:
                failures.append(
                    f"blocked speaker path at ({x:.0f},{y:.0f}): "
                    f"{target_name} ({volume:.2f} mm^3)"
                )
    for x, y in mic_slot_layout(p):
        probe = rounded_prism_xy(34.0, 2.4, 20.0, 1.0, (x, y, top_z + 2.0))
        for target_name in ("body_shell", "top_lid", "top_vent_inlay"):
            volume = intersection_volume(probe, main[target_name])
            if volume > 0.05:
                failures.append(
                    f"blocked microphone path at ({x:.0f},{y:.0f}): "
                    f"{target_name} ({volume:.2f} mm^3)"
                )

    lid_top = p.body_bottom + p.body_height + 5.0
    for x, y in vent_inlay_mount_positions(p):
        probe = cylinder_z(
            p.m2_5_clearance_hole / 2.0 - 0.1,
            p.lid_thickness + p.vent_inlay_bridge_height + 4.0,
            (x, y, lid_top - p.vent_inlay_bridge_height / 2.0),
        )
        for target_name in ("top_lid", "top_vent_inlay"):
            volume = intersection_volume(probe, main[target_name])
            if volume > 0.05:
                failures.append(
                    f"blocked vent-inlay screw at ({x:.0f},{y:.0f}): "
                    f"{target_name} ({volume:.2f} mm^3)"
                )
        inlay_center_z = (
            lid_top
            - p.vent_inlay_recess_depth
            + 0.15
            + p.vent_inlay_thickness / 2.0
        )
        support_probe = cylinder_z(
            3.6,
            p.vent_inlay_thickness,
            (x, y, inlay_center_z),
        )
        support_probe = support_probe - cylinder_z(
            p.m2_5_clearance_hole / 2.0 + 0.1,
            p.vent_inlay_thickness + 2.0,
            (x, y, inlay_center_z),
        )
        if intersection_volume(support_probe, main["top_vent_inlay"]) < 20.0:
            failures.append(
                f"vent-inlay screw lacks surrounding material at ({x:.0f},{y:.0f})"
            )
    for side, sign in (("left", -1), ("right", 1)):
        panel_y = sign * (p.body_width / 2.0 + 1.0)
        for x, z in side_vent_layout():
            probe = rounded_panel_xz(18.0, 26.0, 2.0, 0.9, (x, panel_y, z))
            for target_name in ("body_shell", f"side_fairing_{side}"):
                volume = intersection_volume(probe, main[target_name])
                if volume > 0.05:
                    failures.append(
                        f"blocked side vent on {side} at X={x:.0f}, Z={z:.0f}: "
                        f"{target_name} ({volume:.2f} mm^3)"
                    )

    # Audio supports are removable from below. Shared screw paths prove that
    # the printed rings/plates line up with real roof-side insert bosses.
    for x, y in mic_array_mount_positions(p):
        probe = cylinder_z(
            p.m3_clearance_hole / 2.0 - 0.1,
            10.5,
            (x, y, 162.75),
        )
        for target_name in ("mic_array_cradle", "body_shell"):
            volume = intersection_volume(probe, main[target_name])
            if volume > 0.05:
                failures.append(
                    f"blocked mic-cradle screw at ({x:.0f},{y:.0f}): "
                    f"{target_name} ({volume:.2f} mm^3)"
                )

    for side, sign in (("left", -1), ("right", 1)):
        mount_name = f"speaker_mount_{side}"
        for x, y in speaker_shell_mount_positions(sign):
            probe = cylinder_z(
                p.m3_clearance_hole / 2.0 - 0.1,
                12.0,
                (x, y, 151.0),
            )
            for target_name in (mount_name, "body_shell"):
                volume = intersection_volume(probe, main[target_name])
                if volume > 0.05:
                    failures.append(
                        f"blocked speaker-mount screw on {side} at X={x:.0f}: "
                        f"{target_name} ({volume:.2f} mm^3)"
                    )

        amp_name = f"fit_audio_amp_{side}"
        amp_box = fits[amp_name].bounding_box()
        if abs(float(amp_box.max.X - amp_box.min.X) - p.audio_amp_pcb_length) > 0.05:
            failures.append(f"MAX98357A PCB length drift on {side}")
        if abs(float(amp_box.max.Y - amp_box.min.Y) - p.audio_amp_pcb_width) > 0.05:
            failures.append(f"MAX98357A PCB width drift on {side}")
        amp_mounts = audio_amp_mount_positions(p, sign)
        if abs(amp_mounts[1][0] - amp_mounts[0][0] - p.audio_amp_mount_spacing) > 0.01:
            failures.append(f"MAX98357A mount spacing drift on {side}")
        for index, (x, y) in enumerate(amp_mounts, start=1):
            probe = cylinder_z(
                p.m2_clearance_hole / 2.0 - 0.1,
                22.0,
                (x, y, 139.0),
            )
            for target_name in (mount_name, amp_name):
                volume = intersection_volume(probe, main[target_name] if target_name in main else fits[target_name])
                if volume > 0.05:
                    failures.append(
                        f"blocked MAX98357A M2 screw on {side} station {index}: "
                        f"{target_name} ({volume:.2f} mm^3)"
                    )
            standoff = fits[f"fit_audio_amp_{side}_standoff_{index}"]
            standoff_box = standoff.bounding_box()
            if abs(float(standoff_box.max.Z) - 145.0) > 0.05:
                failures.append(f"MAX98357A standoff misses speaker plate on {side} station {index}")
            if abs(float(standoff_box.min.Z) - 139.0) > 0.05:
                failures.append(f"MAX98357A standoff misses board on {side} station {index}")

    for x, y in cable_strain_relief_mount_positions():
        probe = cylinder_z(
            p.m3_clearance_hole / 2.0 - 0.1,
            12.0,
            (x, y, 151.0),
        )
        for target_name in ("top_cable_strain_relief", "body_shell"):
            volume = intersection_volume(probe, main[target_name])
            if volume > 0.05:
                failures.append(
                    f"blocked cable-relief screw at ({x:.0f},{y:.0f}): "
                    f"{target_name} ({volume:.2f} mm^3)"
                )

    # Four black-on-black fascia screws anchor the whole front expression to
    # shell bosses; each front ToF frame then screws into bosses on the fascia.
    fascia_probe_x = -145.35
    for y, z in front_fascia_mount_positions():
        carrier_name = "front_status_led_carrier_1" if y < 0 else "front_status_led_carrier_2"
        probe = cylinder_x(
            p.m2_5_clearance_hole / 2.0 - 0.1,
            9.5,
            (fascia_probe_x, y, z),
        )
        for target_name in ("front_sensor_fascia", "body_shell", carrier_name):
            volume = intersection_volume(probe, main[target_name])
            if volume > 0.05:
                failures.append(
                    f"blocked front-fascia screw at Y={y:.0f}, Z={z:.0f}: "
                    f"{target_name} ({volume:.2f} mm^3)"
                )

    for side, y, z in front_tof_pod_mount_positions():
        pod_name = f"tof_pod_front_{side}"
        probe = cylinder_x(
            p.m2_5_clearance_hole / 2.0 - 0.1,
            14.0,
            (-139.5, y, z),
        )
        for target_name in (pod_name, "front_sensor_fascia"):
            volume = intersection_volume(probe, main[target_name])
            if volume > 0.05:
                failures.append(
                    f"blocked front-ToF screw on {side} at Z={z:.0f}: "
                    f"{target_name} ({volume:.2f} mm^3)"
                )
        for target_name in ("front_sensor_fascia", "body_shell"):
            volume = intersection_volume(main[pod_name], main[target_name])
            if volume > 0.05:
                failures.append(
                    f"front-ToF pod collision: {pod_name} vs {target_name} "
                    f"({volume:.2f} mm^3)"
                )

    # Side ToF frames sit inward of the shell and use two screws along their
    # forward edge, clear of the shell seam plate and front idler pod.
    for side, sign in (("left", -1), ("right", 1)):
        pod_name = f"tof_pod_side_{side}"
        fairing_name = f"side_fairing_{side}"
        for x, z in side_tof_pod_mount_positions(p, sign):
            probe = cylinder_y(
                p.m2_5_clearance_hole / 2.0 - 0.1,
                12.5,
                (x, sign * 100.25, z),
            )
            for target_name in (pod_name, "body_shell"):
                volume = intersection_volume(probe, main[target_name])
                if volume > 0.05:
                    failures.append(
                        f"blocked side-ToF screw on {side} at X={x:.0f}, Z={z:.0f}: "
                        f"{target_name} ({volume:.2f} mm^3)"
                    )
        for target_name in ("body_shell", fairing_name):
            volume = intersection_volume(main[pod_name], main[target_name])
            if volume > 0.05:
                failures.append(
                    f"side-ToF pod collision: {pod_name} vs {target_name} "
                    f"({volume:.2f} mm^3)"
                )
        sightline = rounded_panel_xz(
            24.0,
            16.0,
            10.0,
            3.0,
            (p.side_tof_center_x, sign * 104.0, 96.0),
        )
        for target_name in (pod_name, "body_shell", fairing_name):
            volume = intersection_volume(sightline, main[target_name])
            if volume > 0.05:
                failures.append(
                    f"blocked side-ToF sightline on {side}: "
                    f"{target_name} ({volume:.2f} mm^3)"
                )

    # Front ToF modules live in the central black sensor bar; the outer lime
    # windows are now dedicated LED diffusers. Prove each sensor sightline.
    front_face_x = -p.body_length / 2.0
    for side, y in front_tof_y_positions():
        probe = rounded_panel_yz(
            30.0,
            10.0,
            8.0,
            2.5,
            (-143.0, y, 96.0),
        )
        for target_name in (
            "body_shell",
            "front_sensor_fascia",
            "front_sensor_window",
            f"tof_pod_front_{side}",
        ):
            volume = intersection_volume(probe, main[target_name])
            if volume > 0.05:
                failures.append(
                    f"blocked front ToF sightline on {side}: "
                    f"{target_name} ({volume:.2f} mm^3)"
                )

    led_fit_targets = {
        "fit_head_eye_led_left": ("head_eye_led_carrier_1", "head_shell", "head_faceplate", "eye_socket_1"),
        "fit_head_eye_led_right": ("head_eye_led_carrier_2", "head_shell", "head_faceplate", "eye_socket_2"),
        "fit_front_status_led_left": ("front_status_led_carrier_1", "body_shell", "front_sensor_fascia"),
        "fit_front_status_led_right": ("front_status_led_carrier_2", "body_shell", "front_sensor_fascia"),
    }
    for fit_name, target_names in led_fit_targets.items():
        for target_name in target_names:
            volume = intersection_volume(fits[fit_name], main[target_name])
            if volume > 0.05:
                failures.append(
                    f"LED hardware collision: {fit_name} vs {target_name} ({volume:.2f} mm^3)"
                )

    led_service_targets = {
        "fit_head_eye_led_left_jst_service": (
            "head_eye_led_carrier_1",
            "head_shell",
            "head_faceplate",
            "camera_carrier",
            "head_tilt_yoke",
        ),
        "fit_head_eye_led_right_jst_service": (
            "head_eye_led_carrier_2",
            "head_shell",
            "head_faceplate",
            "camera_carrier",
            "head_tilt_yoke",
        ),
        "fit_front_status_led_left_jst_service": (
            "front_status_led_carrier_1",
            "body_shell",
            "front_sensor_fascia",
        ),
        "fit_front_status_led_right_jst_service": (
            "front_status_led_carrier_2",
            "body_shell",
            "front_sensor_fascia",
        ),
    }
    for fit_name, target_names in led_service_targets.items():
        for target_name in target_names:
            volume = intersection_volume(fits[fit_name], main[target_name])
            if volume > 0.05:
                failures.append(
                    f"NeoPixel JST service collision: {fit_name} vs {target_name} "
                    f"({volume:.2f} mm^3)"
                )

    eye_z = p.head_center_z + p.head_eye_center_z_offset
    if p.head_eye_aperture_height <= p.head_eye_aperture_width:
        failures.append("head eye apertures are no longer vertical as required by the concept")
    if p.head_eye_glow_width >= p.head_eye_aperture_width or p.head_eye_glow_height >= p.head_eye_aperture_height:
        failures.append("head eye diffuser must remain inset inside its structural aperture")
    if (
        p.head_eye_led_board_width >= p.head_eye_carrier_opening_width
        or p.head_eye_led_board_height >= p.head_eye_carrier_opening_height
    ):
        failures.append("head LED board envelope lacks clearance inside its carrier opening")
    if (
        p.head_eye_carrier_opening_width >= p.head_eye_carrier_width
        or p.head_eye_carrier_opening_height >= p.head_eye_carrier_height
    ):
        failures.append("head LED carrier opening consumed its retaining frame")
    if p.front_status_aperture_width <= p.front_status_aperture_height:
        failures.append("front status apertures are no longer horizontal as required by the concept")
    if p.front_status_glow_width >= p.front_status_aperture_width or p.front_status_glow_height >= p.front_status_aperture_height:
        failures.append("front status diffuser must remain inset inside its structural aperture")
    if (
        p.front_status_led_board_width >= p.front_status_carrier_opening_width
        or p.front_status_led_board_height >= p.front_status_carrier_opening_height
    ):
        failures.append("front status LED board lacks clearance inside its carrier opening")

    neopixel_expected = {
        "fit_head_eye_led_left": (p.neopixel_overall_depth, p.neopixel_board_height, p.neopixel_board_width),
        "fit_head_eye_led_right": (p.neopixel_overall_depth, p.neopixel_board_height, p.neopixel_board_width),
        "fit_front_status_led_left": (p.neopixel_overall_depth, p.neopixel_board_width, p.neopixel_board_height),
        "fit_front_status_led_right": (p.neopixel_overall_depth, p.neopixel_board_width, p.neopixel_board_height),
    }
    for fit_name, expected_spans in neopixel_expected.items():
        box = fits[fit_name].bounding_box()
        actual_spans = (
            float(box.max.X - box.min.X),
            float(box.max.Y - box.min.Y),
            float(box.max.Z - box.min.Z),
        )
        if any(
            abs(actual - expected) > 0.03
            for actual, expected in zip(actual_spans, expected_spans)
        ):
            failures.append(
                f"Adafruit 5975 envelope drift on {fit_name}: "
                f"{tuple(round(value, 3) for value in actual_spans)}"
            )

    led_mount_contracts = (
        (
            "head_eye_led_left",
            -42.0,
            eye_z,
            True,
            head_neopixel_pcb_front_x(p),
            "head_eye_led_carrier_1",
        ),
        (
            "head_eye_led_right",
            42.0,
            eye_z,
            True,
            head_neopixel_pcb_front_x(p),
            "head_eye_led_carrier_2",
        ),
        (
            "front_status_led_left",
            -50.0,
            96.0,
            False,
            front_neopixel_pcb_front_x(p),
            "front_status_led_carrier_1",
        ),
        (
            "front_status_led_right",
            50.0,
            96.0,
            False,
            front_neopixel_pcb_front_x(p),
            "front_status_led_carrier_2",
        ),
    )
    for prefix, center_y, center_z, rotate_90, pcb_front_x, carrier_name in led_mount_contracts:
        carrier_box = main[carrier_name].bounding_box()
        pcb_back_x = pcb_front_x + p.neopixel_pcb_thickness
        carrier_front_x = float(carrier_box.min.X)
        for index, (mount_y, mount_z) in enumerate(
            neopixel_mount_positions(p, center_y, center_z, rotate_90),
            start=1,
        ):
            spacer_name = f"fit_{prefix}_spacer_{index}"
            spacer_box = fits[spacer_name].bounding_box()
            if abs(float(spacer_box.min.X) - pcb_back_x) > 0.05:
                failures.append(f"NeoPixel spacer {spacer_name} misses PCB back")
            if abs(float(spacer_box.max.X) - carrier_front_x) > 0.05:
                failures.append(f"NeoPixel spacer {spacer_name} misses carrier front")
            screw_depth = float(carrier_box.max.X) - pcb_front_x + 2.0
            screw_center_x = (pcb_front_x + float(carrier_box.max.X)) / 2.0
            screw_probe = cylinder_x(
                p.neopixel_mount_hole / 2.0 - 0.1,
                screw_depth,
                (screw_center_x, mount_y, mount_z),
            )
            for target_name, target_shape in (
                (f"fit_{prefix}", fits[f"fit_{prefix}"]),
                (spacer_name, fits[spacer_name]),
                (carrier_name, main[carrier_name]),
            ):
                volume = intersection_volume(screw_probe, target_shape)
                if volume > 0.05:
                    failures.append(
                        f"blocked NeoPixel M2 path {prefix}/{index}: "
                        f"{target_name} ({volume:.2f} mm^3)"
                    )

    for index, y in enumerate((-42.0, 42.0), start=1):
        light_front_x = p.head_center_x - p.head_depth / 2.0 - 7.0
        light_rear_x = head_neopixel_pcb_front_x(p) - p.neopixel_led_front_protrusion
        probe = rounded_panel_yz(
            light_rear_x - light_front_x,
            p.head_eye_glow_width,
            p.head_eye_glow_height,
            4.0,
            ((light_front_x + light_rear_x) / 2.0, y, eye_z),
        )
        for target_name in ("head_shell", "head_faceplate", f"eye_socket_{index}", f"head_eye_led_carrier_{index}"):
            volume = intersection_volume(probe, main[target_name])
            if volume > 0.05:
                failures.append(
                    f"blocked head-eye light path {index}: {target_name} ({volume:.2f} mm^3)"
                )

    for index, y in enumerate((-50.0, 50.0), start=1):
        light_front_x = front_face_x - 2.0
        light_rear_x = front_neopixel_pcb_front_x(p) - p.neopixel_led_front_protrusion
        probe = rounded_panel_yz(
            light_rear_x - light_front_x,
            p.front_status_glow_width,
            p.front_status_glow_height,
            4.0,
            ((light_front_x + light_rear_x) / 2.0, y, 96.0),
        )
        for target_name in ("body_shell", "front_sensor_fascia", f"front_status_led_carrier_{index}"):
            volume = intersection_volume(probe, main[target_name])
            if volume > 0.05:
                failures.append(
                    f"blocked front-status light path {index}: {target_name} ({volume:.2f} mm^3)"
                )

    pololu_motor_expected = {
        "body_length": (p.motor_body_length, 68.45),
        "body_diameter": (p.motor_body_diameter, 25.0),
        "shaft_diameter": (p.motor_shaft_diameter, 4.0),
        "shaft_length": (p.motor_shaft_length, 12.5),
        "face_spacing": (p.motor_face_mount_spacing, 17.0),
        "face_thread_depth": (p.motor_face_mount_depth, 6.0),
        "bracket_base_length": (p.motor_bracket_base_length, 49.0),
        "bracket_face_size": (p.motor_bracket_face_size, 25.0),
        "hub_diameter": (p.motor_hub_diameter, 19.0),
        "hub_thickness": (p.motor_hub_thickness, 5.0),
        "hub_mount_offset": (p.motor_hub_mount_offset, 6.35),
        "no_load_rpm": (p.motor_no_load_rpm, 79.0),
        "no_load_current_a": (p.motor_no_load_current_a, 0.10),
        "stall_current_a": (p.motor_stall_current_a, 1.8),
        "stall_torque_kg_cm": (p.motor_stall_torque_kg_cm, 11.0),
    }
    for label, (actual, expected) in pololu_motor_expected.items():
        if abs(actual - expected) > 0.01:
            failures.append(
                f"Pololu rear drivetrain {label} drifted from drawing: "
                f"{actual:.3f} vs {expected:.3f} mm"
            )

    for side, sign in (("left", -1), ("right", 1)):
        motor_fit = f"fit_drive_motor_{side}"
        bracket_fit = f"fit_drive_motor_bracket_{side}"
        hub_fit = f"fit_drive_motor_hub_{side}"
        cable_fit = f"fit_drive_motor_cable_{side}"
        pod_name = f"motor_pod_{side}"
        cover_name = f"motor_pod_cover_{side}"
        tire_name = f"wheel_{side}_2"
        ring_name = f"hub_ring_{side}_2"
        core_name = f"hub_{side}_2"

        for fit_name, targets in (
            (motor_fit, (pod_name, cover_name, "body_shell", "base_tray")),
            (bracket_fit, (pod_name, cover_name, "body_shell", "base_tray")),
            (hub_fit, (pod_name, "body_shell", tire_name, ring_name, core_name)),
            (cable_fit, (pod_name, cover_name, "body_shell", "base_tray")),
        ):
            for target_name in targets:
                volume = intersection_volume(fits[fit_name], main[target_name])
                if volume > 0.05:
                    failures.append(
                        f"rear drivetrain collision: {fit_name} vs {target_name} "
                        f"({volume:.2f} mm^3)"
                    )

        for x, y in motor_pod_mount_positions(p, sign):
            probe = cylinder_z(
                p.m3_clearance_hole / 2.0 - 0.1,
                18.0,
                (x, y, p.body_bottom + 3.0),
            )
            for target_name in ("base_tray", pod_name):
                volume = intersection_volume(probe, main[target_name])
                if volume > 0.05:
                    failures.append(
                        f"blocked motor-pod screw on {side} at ({x:.0f},{y:.0f}): "
                        f"{target_name} ({volume:.2f} mm^3)"
                    )

        bracket_box = fits[bracket_fit].bounding_box()
        for index, (x, y) in enumerate(
            drive_motor_bracket_tray_positions(p, sign), start=1
        ):
            spacer_name = f"fit_drive_motor_bracket_spacer_{side}_{index}"
            spacer_box = fits[spacer_name].bounding_box()
            if abs(float(spacer_box.min.Z - p.body_bottom)) > 0.05:
                failures.append(f"{side} motor-bracket spacer {index} misses tray")
            if abs(float(spacer_box.max.Z - bracket_box.min.Z)) > 0.05:
                failures.append(f"{side} motor-bracket spacer {index} misses bracket")
            probe = cylinder_z(
                1.4,
                p.tray_thickness + p.motor_bracket_spacer_height + 5.0,
                (x, y, p.body_bottom - 1.0),
            )
            for target_name in ("base_tray", pod_name):
                volume = intersection_volume(probe, main[target_name])
                if volume > 0.05:
                    failures.append(
                        f"blocked metal motor-bracket tray screw on {side}/{index}: "
                        f"{target_name} ({volume:.2f} mm^3)"
                    )
            volume = intersection_volume(probe, fits[bracket_fit])
            if volume > 0.05:
                failures.append(
                    f"blocked metal motor-bracket hole on {side}/{index} "
                    f"({volume:.2f} mm^3)"
                )

        for x, face_y, z in drive_motor_face_mount_positions(p, sign):
            screw_center_y = face_y - sign * (
                p.motor_face_mount_depth / 2.0
                - p.motor_bracket_thickness / 2.0
            )
            probe = cylinder_y(
                1.4,
                p.motor_face_mount_depth + p.motor_bracket_thickness + 2.0,
                (x, screw_center_y, z),
            )
            for target_name in (pod_name, cover_name):
                volume = intersection_volume(probe, main[target_name])
                if volume > 0.05:
                    failures.append(
                        f"blocked motor-face screw on {side}: {target_name} "
                        f"({volume:.2f} mm^3)"
                    )
            volume = intersection_volume(probe, fits[bracket_fit])
            if volume > 0.05:
                failures.append(
                    f"blocked Pololu bracket face hole on {side} ({volume:.2f} mm^3)"
                )

        core_center_y = wheel_center_y(p, sign) + sign * (
            (p.wheel_core_length - p.wheel_thickness) / 2.0
        )
        for dx, dz in drive_motor_hub_mount_positions(p):
            probe = cylinder_y(
                1.4,
                p.wheel_core_length + 4.0,
                (
                    p.wheel_x_positions[1] + dx,
                    core_center_y,
                    p.wheel_center_z + dz,
                ),
            )
            for target_name in (tire_name, ring_name, core_name):
                volume = intersection_volume(probe, main[target_name])
                if volume > 0.05:
                    failures.append(
                        f"blocked rear wheel-to-hub screw on {side}: {target_name} "
                        f"({volume:.2f} mm^3)"
                    )
            volume = intersection_volume(probe, fits[hub_fit])
            if volume > 0.05:
                failures.append(
                    f"blocked Pololu hub thread path on {side} ({volume:.2f} mm^3)"
                )

        inner_face_y, _cover_center_y, cover_screws = motor_pod_service_interface(p, sign)
        face_y = drive_motor_face_y(p, sign)
        service_start_y = face_y - sign * (p.motor_body_length + 8.0)
        service_path = cylinder_y(
            p.motor_body_diameter / 2.0 + 0.7,
            abs(face_y - service_start_y),
            (
                p.wheel_x_positions[1],
                (face_y + service_start_y) / 2.0,
                p.wheel_center_z,
            ),
        )
        volume = intersection_volume(service_path, main[pod_name])
        if volume > 0.05:
            failures.append(
                f"blocked motor installation path on {side}: {pod_name} ({volume:.2f} mm^3)"
            )
        for x, z in cover_screws:
            probe = cylinder_y(
                p.m3_clearance_hole / 2.0 - 0.1,
                9.0,
                (x, inner_face_y + sign * 0.5, z),
            )
            for target_name in (pod_name, cover_name):
                volume = intersection_volume(probe, main[target_name])
                if volume > 0.05:
                    failures.append(
                        f"blocked motor-cover screw on {side} at X={x:.0f}, Z={z:.0f}: "
                        f"{target_name} ({volume:.2f} mm^3)"
                    )

    # The two-motor MVP keeps the concept's front wheels as non-driven idlers.
    # Each removable pod locates two 608-class bearings and an 8 mm metal shaft.
    # The shaft must clear the pod and shell, then extend into the wheel hub.
    front_idler_keepouts = (
        "fit_pi5",
        "fit_motor_controller",
        "fit_battery",
        "fit_safety_mcu",
        "fit_future_ai_hat_clearance",
    )
    for side, sign, wheel_name in (
        ("left", -1, "hub_left_1"),
        ("right", 1, "hub_right_1"),
    ):
        pod_name = f"front_idler_pod_{side}"
        hardware_names = front_idler_hardware_names(side)
        shaft_name = f"fit_front_idler_{side}_shaft"
        hub_name = f"fit_front_idler_{side}_hub"
        for hardware_name in hardware_names:
            for target_name in (pod_name, "body_shell"):
                volume = intersection_volume(fits[hardware_name], main[target_name])
                if volume > 0.05:
                    failures.append(
                        f"front-idler hardware collision: {hardware_name} vs {target_name} "
                        f"({volume:.2f} mm^3)"
                    )
        for keepout_name in front_idler_keepouts:
            volume = intersection_volume(main[pod_name], fits[keepout_name])
            if volume > 0.05:
                failures.append(
                    f"front-idler keepout collision: {pod_name} vs {keepout_name} "
                    f"({volume:.2f} mm^3)"
                )

        def signed_y_bounds(shape):
            box = shape.bounding_box()
            return tuple(sorted((sign * float(box.min.Y), sign * float(box.max.Y))))

        stack_names = (
            f"fit_front_idler_{side}_retaining_ring",
            f"fit_front_idler_{side}_inner_washer",
            f"fit_front_idler_{side}_bearing_inner",
            f"fit_front_idler_{side}_inner_spacer",
            f"fit_front_idler_{side}_bearing_outer",
            f"fit_front_idler_{side}_outer_spacer",
            hub_name,
        )
        for first_name, second_name in zip(stack_names, stack_names[1:]):
            first_bounds = signed_y_bounds(fits[first_name])
            second_bounds = signed_y_bounds(fits[second_name])
            allowed_gap = (
                p.front_axle_ring_groove_width - p.front_axle_ring_thickness + 0.01
                if first_name.endswith("_retaining_ring")
                else 0.05
            )
            if abs(first_bounds[1] - second_bounds[0]) > allowed_gap:
                failures.append(
                    f"front-idler axial stack gap on {side}: {first_name} -> {second_name}"
                )
        shaft_bounds = signed_y_bounds(fits[shaft_name])
        hub_bounds = signed_y_bounds(fits[hub_name])
        if abs(shaft_bounds[1] - hub_bounds[1]) > 0.05:
            failures.append(f"front-idler shaft misses hub outer face on {side}")
        ring_bounds = signed_y_bounds(fits[stack_names[0]])
        if shaft_bounds[0] > ring_bounds[0] - p.front_axle_ring_edge_margin + 0.05:
            failures.append(f"front-idler shaft lacks retaining-ring edge margin on {side}")
        if intersection_volume(fits[hub_name], main[wheel_name]) > 0.05:
            failures.append(f"front-idler #2693 hub collides with wheel core on {side}")
        if not inside_box(
            fits[hub_name],
            main[wheel_name].bounding_box().min.X,
            main[wheel_name].bounding_box().max.X,
            main[wheel_name].bounding_box().min.Y,
            main[wheel_name].bounding_box().max.Y,
            main[wheel_name].bounding_box().min.Z,
            main[wheel_name].bounding_box().max.Z,
        ):
            failures.append(f"front-idler #2693 hub escapes wheel-core envelope on {side}")
        hub_center_y = sum(hub_bounds) / 2.0 * sign
        for station, (dx, dz) in enumerate(front_idler_hub_mount_positions(p), start=1):
            probe = cylinder_y(
                p.front_hub_mount_thread / 2.0 - 0.1,
                p.front_hub_length + 4.0,
                (
                    p.wheel_x_positions[0] + dx,
                    hub_center_y,
                    p.wheel_center_z + dz,
                ),
            )
            for target_name, target in ((wheel_name, main[wheel_name]), (hub_name, fits[hub_name])):
                volume = intersection_volume(probe, target)
                if volume > 0.05:
                    failures.append(
                        f"blocked front-idler #2693 M3 path on {side} station {station}: "
                        f"{target_name} ({volume:.2f} mm^3)"
                    )
        for x, y in front_idler_mount_positions(p, sign):
            probe = cylinder_z(
                p.m3_clearance_hole / 2.0 - 0.1,
                18.0,
                (x, y, p.body_bottom + 3.0),
            )
            for target_name in ("base_tray", pod_name):
                volume = intersection_volume(probe, main[target_name])
                if volume > 0.05:
                    failures.append(
                        f"blocked front-idler screw on {side} at ({x:.0f},{y:.0f}): "
                        f"{target_name} ({volume:.2f} mm^3)"
                    )
        for face_name, face_y, outward_sign in front_idler_retainer_interfaces(p, sign):
            retainer_name = f"front_idler_retainer_{side}_{face_name}"
            for target_name in (pod_name, "body_shell"):
                volume = intersection_volume(main[retainer_name], main[target_name])
                if volume > 0.05:
                    failures.append(
                        f"front-idler retainer collision: {retainer_name} vs {target_name} "
                        f"({volume:.2f} mm^3)"
                    )
            for hardware_name in hardware_names:
                volume = intersection_volume(main[retainer_name], fits[hardware_name])
                if volume > 0.05:
                    failures.append(
                        f"front-idler retainer hardware collision: {retainer_name} vs {hardware_name} "
                        f"({volume:.2f} mm^3)"
                    )
            for dx in (-13.5, 13.5):
                probe = cylinder_y(
                    p.m2_5_clearance_hole / 2.0 - 0.1,
                    5.0,
                    (
                        p.wheel_x_positions[0] + dx,
                        face_y - outward_sign * 2.5,
                        p.wheel_center_z,
                    ),
                )
                for target_name in (pod_name, retainer_name):
                    volume = intersection_volume(probe, main[target_name])
                    if volume > 0.05:
                        failures.append(
                            f"blocked front-idler retainer screw on {side}/{face_name}: "
                            f"{target_name} ({volume:.2f} mm^3)"
                        )

    # The safety MCU sits on a removable shelf above the motor controller.
    # Four metal standoffs establish that stack and their shared screw paths
    # must stay open through both printed plates.
    controller_top = main["motor_controller_mount"].bounding_box().max.Z
    safety_bottom = main["safety_mcu_mount"].bounding_box().min.Z
    for index, (x, y) in enumerate(safety_shelf_standoff_positions(p), start=1):
        fit_name = f"fit_safety_shelf_standoff_{index}"
        standoff_box = fits[fit_name].bounding_box()
        if abs(float(standoff_box.min.Z - controller_top)) > 0.05:
            failures.append(f"safety shelf standoff {index} does not meet controller plate")
        if abs(float(standoff_box.max.Z - safety_bottom)) > 0.05:
            failures.append(f"safety shelf standoff {index} does not meet safety shelf")
        for target_name in (
            "motor_controller_mount",
            "safety_mcu_mount",
            "front_idler_pod_left",
            "front_idler_pod_right",
            "motor_pod_left",
            "motor_pod_right",
            "body_shell",
        ):
            volume = intersection_volume(fits[fit_name], main[target_name])
            if volume > 0.05:
                failures.append(
                    f"safety shelf standoff collision: {fit_name} vs {target_name} "
                    f"({volume:.2f} mm^3)"
                )
        probe = cylinder_z(
            p.m3_clearance_hole / 2.0 - 0.1,
            p.safety_mount_z - motor_controller_plate_top_z(p) + 12.0,
            (x, y, (p.safety_mount_z + motor_controller_plate_top_z(p)) / 2.0),
        )
        for target_name in ("motor_controller_mount", "safety_mcu_mount"):
            volume = intersection_volume(probe, main[target_name])
            if volume > 0.05:
                failures.append(
                    f"blocked safety-shelf screw at ({x:.0f},{y:.0f}): "
                    f"{target_name} ({volume:.2f} mm^3)"
                )

    # Cytron's official MDDS10 STEP establishes the board, hole pattern, pin
    # protrusion, component height, and terminal end used by this stack. Keep
    # the front terminal fan-out and an unobstructed cooling layer below the
    # Pico shelf; the board has no reverse-polarity protection, so this remains
    # a serviceable module rather than a buried mystery rectangle.
    mdds10_expected = {
        "board_length": (p.mdds10_board_length, 101.092),
        "board_width": (p.mdds10_board_width, 66.802),
        "board_thickness": (p.mdds10_board_thickness, 1.57),
        "below_pcb": (p.mdds10_below_pcb, 1.93),
        "above_pcb": (p.mdds10_above_pcb, 12.275),
        "mount_spacing_length": (p.mdds10_mount_spacing_length, 95.25),
        "mount_spacing_width": (p.mdds10_mount_spacing_width, 60.96),
        "mount_hole": (p.mdds10_mount_hole, 3.0),
    }
    for label, (actual, expected) in mdds10_expected.items():
        if abs(actual - expected) > 0.01:
            failures.append(
                f"MDDS10 {label} drifted from official STEP: {actual:.3f} vs {expected:.3f} mm"
            )
    if p.mdds10_mount_clearance - p.mdds10_mount_hole < 0.3:
        failures.append("MDDS10 mounting holes leave less than 0.3 mm diametral clearance")
    if p.mdds10_standoff_height - p.mdds10_below_pcb < 3.0:
        failures.append("MDDS10 underside pins have less than 3 mm plate clearance")
    controller_top_z = (
        mdds10_board_bottom_z(p)
        + p.mdds10_above_pcb
        + p.mdds10_airflow_height
    )
    if controller_top_z > p.safety_mount_z - 2.0 + 0.05:
        failures.append("MDDS10 airflow envelope reaches the Pico safety shelf")
    for fit_name in (
        "fit_motor_controller_terminal_service",
        "fit_motor_controller_airflow",
    ):
        for target_name in (
            "motor_controller_mount",
            "safety_mcu_mount",
            "base_tray",
            "body_shell",
            "front_idler_pod_left",
            "front_idler_pod_right",
            "motor_pod_left",
            "motor_pod_right",
        ):
            volume = intersection_volume(fits[fit_name], main[target_name])
            if volume > 0.05:
                failures.append(
                    f"MDDS10 service collision: {fit_name} vs {target_name} "
                    f"({volume:.2f} mm^3)"
                )

    # The deterministic safety controller is now a drawing-backed Raspberry Pi
    # Pico 2 rather than an anonymous development-board box. Its exact M2 hole
    # pattern, board/USB envelope, metal standoffs, front USB notch, and rear
    # SWD service corridor must remain synchronized.
    pico_expected = {
        "board_length": (p.pico2_board_length, 51.0),
        "board_width": (p.pico2_board_width, 21.0),
        "board_thickness": (p.pico2_board_thickness, 1.0),
        "overall_length": (p.pico2_overall_length, 52.3),
        "overall_height": (p.pico2_overall_height, 3.8),
        "mount_spacing_length": (p.pico2_mount_spacing_length, 48.26),
        "mount_spacing_width": (p.pico2_mount_spacing_width, 17.78),
        "mount_hole": (p.pico2_mount_hole, 2.1),
    }
    for label, (actual, expected) in pico_expected.items():
        if abs(actual - expected) > 0.01:
            failures.append(
                f"Pico 2 {label} drifted from official reference: {actual:.2f} vs {expected:.2f}"
            )

    pico_positions = pico2_mount_positions(p)
    pico_x = sorted({round(x, 3) for x, _y in pico_positions})
    pico_y = sorted({round(y, 3) for _x, y in pico_positions})
    if len(pico_positions) != 4 or len(pico_x) != 2 or len(pico_y) != 2:
        failures.append("Pico 2 mount pattern is not a four-corner rectangle")
    else:
        if abs((pico_x[1] - pico_x[0]) - p.pico2_mount_spacing_length) > 0.01:
            failures.append("Pico 2 longitudinal hole spacing mismatch")
        if abs((pico_y[1] - pico_y[0]) - p.pico2_mount_spacing_width) > 0.01:
            failures.append("Pico 2 transverse hole spacing mismatch")

    pico_board_box = fits["fit_safety_mcu_board"].bounding_box()
    pico_board_spans = (
        float(pico_board_box.max.X - pico_board_box.min.X),
        float(pico_board_box.max.Y - pico_board_box.min.Y),
        float(pico_board_box.max.Z - pico_board_box.min.Z),
    )
    if abs(pico_board_spans[0] - p.pico2_overall_length) > 0.05:
        failures.append(
            f"Pico 2 board/USB envelope length mismatch: {pico_board_spans[0]:.2f}"
        )
    if abs(pico_board_spans[1] - p.pico2_board_width) > 0.05:
        failures.append(
            f"Pico 2 board/USB envelope width mismatch: {pico_board_spans[1]:.2f}"
        )
    if pico_board_spans[2] > p.pico2_overall_height + 0.05:
        failures.append(
            f"Pico 2 board/USB envelope height exceeds STEP reference: {pico_board_spans[2]:.2f}"
        )

    safety_shelf_top = main["safety_mcu_mount"].bounding_box().max.Z
    pico_board_bottom = pico2_board_bottom_z(p)
    for index, (x, y) in enumerate(pico_positions, start=1):
        probe = cylinder_z(
            p.pico2_mount_clearance / 2.0 - 0.1,
            8.0,
            (x, y, p.safety_mount_z),
        )
        volume = intersection_volume(probe, main["safety_mcu_mount"])
        if volume > 0.05:
            failures.append(
                f"blocked Pico 2 M2 board screw at ({x:.2f},{y:.2f}): {volume:.2f} mm^3"
            )
        fit_name = f"fit_safety_mcu_standoff_{index}"
        standoff_box = fits[fit_name].bounding_box()
        if abs(float(standoff_box.min.Z - safety_shelf_top)) > 0.05:
            failures.append(f"Pico 2 standoff {index} does not meet safety shelf")
        if abs(float(standoff_box.max.Z - pico_board_bottom)) > 0.05:
            failures.append(f"Pico 2 standoff {index} does not meet board bottom")
        for target_name in ("safety_mcu_mount", "fit_safety_mcu_board"):
            target = main[target_name] if target_name in main else fits[target_name]
            volume = intersection_volume(fits[fit_name], target)
            if volume > 0.05:
                failures.append(
                    f"Pico 2 standoff collision: {fit_name} vs {target_name} ({volume:.2f} mm^3)"
                )

    usb_notch_probe = rounded_prism_xy(
        p.pico2_usb_notch_length - 0.4,
        p.pico2_usb_notch_width - 0.4,
        6.0,
        1.8,
        (pico2_usb_notch_center_x(p) + 0.2, p.safety_center_y, p.safety_mount_z),
    )
    usb_notch_blockage = intersection_volume(
        usb_notch_probe, main["safety_mcu_mount"]
    )
    if usb_notch_blockage > 0.05:
        failures.append(
            f"Pico 2 front USB notch is blocked ({usb_notch_blockage:.2f} mm^3)"
        )
    for fit_name in ("fit_safety_mcu_usb_service", "fit_safety_mcu_swd_service"):
        for target_name in (
            "safety_mcu_mount",
            "body_shell",
            "power_service_deck",
            "motor_controller_mount",
        ):
            volume = intersection_volume(fits[fit_name], main[target_name])
            if volume > 0.05:
                failures.append(
                    f"Pico 2 service path collision: {fit_name} vs {target_name} "
                    f"({volume:.2f} mm^3)"
                )

    # The battery cradle sits directly on the tray. The controller plate is
    # lifted 5 mm on metal spacers to bridge the concealed carry-handle
    # doubler; all shared holes and both tiers of standoffs must remain open.
    for part_name in ("battery_cradle", "motor_controller_mount"):
        volume = intersection_volume(main[part_name], main["base_tray"])
        if volume > 0.05:
            failures.append(
                f"tray-mounted part collision: {part_name} vs base_tray ({volume:.2f} mm^3)"
            )

    for x, y in battery_cradle_mount_positions(p):
        probe = cylinder_z(
            p.m3_clearance_hole / 2.0 - 0.1,
            12.0,
            (x, y, p.body_bottom - 2.0),
        )
        for target_name in ("base_tray", "battery_cradle"):
            volume = intersection_volume(probe, main[target_name])
            if volume > 0.05:
                failures.append(
                    f"blocked battery-cradle screw at ({x:.0f},{y:.0f}): "
                    f"{target_name} ({volume:.2f} mm^3)"
                )

    battery_box = fits["fit_battery"].bounding_box()
    battery_spans = (
        float(battery_box.max.X - battery_box.min.X),
        float(battery_box.max.Y - battery_box.min.Y),
        float(battery_box.max.Z - battery_box.min.Z),
    )
    expected_battery_spans = (
        p.battery_max_length,
        p.battery_max_width,
        p.battery_max_height,
    )
    for axis, actual, expected in zip("XYZ", battery_spans, expected_battery_spans):
        if abs(actual - expected) > 0.05:
            failures.append(
                f"selected battery envelope {axis} drifted: {actual:.2f} vs {expected:.2f} mm"
            )
    official_blf1203ab_spans = (110.0, 75.0, 27.0)
    for axis, actual, expected in zip(
        "XYZ", expected_battery_spans, official_blf1203ab_spans
    ):
        if abs(actual - expected) > 0.05:
            failures.append(
                f"Bioenno BLF-1203AB rotated span {axis} drifted: "
                f"{actual:.2f} vs {expected:.2f} mm"
            )
    battery_bottom = p.body_bottom + 9.0
    if abs(float(battery_box.min.Z - battery_bottom)) > 0.05:
        failures.append("maximum battery envelope misses four cradle support pads")
    if p.battery_side_clearance < 0.5 or p.battery_end_clearance < 0.5:
        failures.append("battery locator clearance is below the 0.5 mm prototype minimum")
    for x in (
        p.battery_center_x - p.battery_pad_offset_x,
        p.battery_center_x + p.battery_pad_offset_x,
    ):
        for y in (
            p.battery_center_y - p.battery_pad_offset_y,
            p.battery_center_y + p.battery_pad_offset_y,
        ):
            contact_probe = cylinder_z(5.0, 0.2, (x, y, battery_bottom))
            if intersection_volume(contact_probe, main["battery_cradle"]) <= 5.0:
                failures.append(f"battery support pad missing at ({x:.1f},{y:.1f})")
            if intersection_volume(contact_probe, fits["fit_battery"]) <= 4.0:
                failures.append(f"battery envelope misses pad at ({x:.1f},{y:.1f})")
    for x in (
        p.battery_center_x - p.battery_strap_offset,
        p.battery_center_x + p.battery_strap_offset,
    ):
        strap_probe = rounded_box(
            p.battery_strap_width + 0.6,
            90.0,
            6.0,
            1.8,
            (x, p.battery_center_y, p.body_bottom + 2.0),
        )
        if intersection_volume(strap_probe, main["battery_cradle"]) > 2.0:
            failures.append(f"blocked battery strap channel at X={x:.1f}")
    if p.battery_strap_width < 20.0:
        failures.append("battery retention straps are narrower than 20 mm")
    for x, y in motor_controller_plate_mount_positions(p):
        probe = cylinder_z(
            p.m3_clearance_hole / 2.0 - 0.1,
            12.0,
            (x, y, p.body_bottom - 2.0),
        )
        for target_name in ("base_tray", "motor_controller_mount"):
            volume = intersection_volume(probe, main[target_name])
            if volume > 0.05:
                failures.append(
                    f"blocked controller-plate tray screw at ({x:.0f},{y:.0f}): "
                    f"{target_name} ({volume:.2f} mm^3)"
                )

    controller_plate_bottom = main["motor_controller_mount"].bounding_box().min.Z
    for index, _position in enumerate(motor_controller_plate_mount_positions(p), start=1):
        fit_name = f"fit_motor_controller_plate_standoff_{index}"
        standoff_box = fits[fit_name].bounding_box()
        if abs(float(standoff_box.min.Z - p.body_bottom)) > 0.05:
            failures.append(f"controller plate spacer {index} does not meet base tray")
        if abs(float(standoff_box.max.Z - controller_plate_bottom)) > 0.05:
            failures.append(f"controller plate spacer {index} does not meet mounting plate")
        for target_name in ("base_tray", "motor_controller_mount"):
            volume = intersection_volume(fits[fit_name], main[target_name])
            if volume > 0.05:
                failures.append(
                    f"controller plate spacer collision: {fit_name} vs {target_name} "
                    f"({volume:.2f} mm^3)"
                )

    controller_plate_top = main["motor_controller_mount"].bounding_box().max.Z
    controller_board_bottom = fits["fit_motor_controller_board"].bounding_box().min.Z
    for index, _position in enumerate(motor_controller_board_mount_positions(p), start=1):
        fit_name = f"fit_motor_controller_standoff_{index}"
        standoff_box = fits[fit_name].bounding_box()
        if abs(float(standoff_box.min.Z - controller_plate_top)) > 0.05:
            failures.append(f"controller standoff {index} does not meet mounting plate")
        if abs(float(standoff_box.max.Z - controller_board_bottom)) > 0.05:
            failures.append(f"controller standoff {index} does not meet board envelope")
        for target_name in ("base_tray", "motor_controller_mount", "safety_mcu_mount"):
            volume = intersection_volume(fits[fit_name], main[target_name])
            if volume > 0.05:
                failures.append(
                    f"controller standoff collision: {fit_name} vs {target_name} "
                    f"({volume:.2f} mm^3)"
                )

    # The fixed yoke bolts to a real top flange on the rotating neck. Its four
    # screws pass through the yoke base into blind neck insert pockets while
    # the hourglass waist preserves the separate servo-cable corridor.
    if not (
        p.neck_bottom_radius
        > p.neck_top_radius
        > p.neck_waist_radius
        > p.neck_wall
    ):
        failures.append("neck radii no longer form a lower flare, waist, and upper flare")
    if p.neck_waist_radius - p.neck_wall < 9.0:
        failures.append("hourglass neck leaves less than 18 mm clear diameter at its waist")
    if p.neck_yoke_flange_radius - p.neck_top_radius < 1.0:
        failures.append("neck yoke flange projects less than 1 mm beyond upper flare")
    neck_top = p.neck_bottom + p.neck_height
    yoke_seat_z = p.head_center_z - p.head_height / 2.0 + 8.0 - 2.5
    if abs(neck_top - yoke_seat_z) > 0.05:
        failures.append(
            f"neck top misses fixed-yoke seating plane: {neck_top:.2f} vs {yoke_seat_z:.2f} mm"
        )
    for x, y in neck_yoke_mount_positions(p):
        probe_bottom = neck_top - p.neck_yoke_insert_depth + 0.2
        probe_top = yoke_seat_z + 5.4
        probe = cylinder_z(
            p.m2_5_clearance_hole / 2.0 - 0.1,
            probe_top - probe_bottom,
            (x, y, (probe_bottom + probe_top) / 2.0),
        )
        for target_name in ("neck", "head_tilt_yoke"):
            volume = intersection_volume(probe, main[target_name])
            if volume > 0.05:
                failures.append(
                    f"blocked neck-yoke screw at ({x:.1f}, {y:.1f}): "
                    f"{target_name} ({volume:.2f} mm^3)"
                )

    # Both side adapters are removable from the open rear head. Their three
    # shell screws must pass through a supported annulus into blind bosses.
    for side, side_sign, adapter_name in (
        ("passive", -1, "head_tilt_passive_cartridge"),
        ("drive", 1, "head_tilt_drive_adapter"),
    ):
        adapter_y = head_tilt_adapter_center_y(p, side_sign)
        path_start_y = adapter_y - side_sign * (
            p.head_tilt_adapter_thickness / 2.0 + 0.2
        )
        path_end_y = side_sign * (p.head_width / 2.0 - 3.6)
        path_y = (path_start_y + path_end_y) / 2.0
        path_length = abs(path_end_y - path_start_y)
        for x, z in head_tilt_adapter_mount_positions(p):
            probe = cylinder_y(
                p.m2_5_clearance_hole / 2.0 - 0.1,
                path_length,
                (x, path_y, z),
            )
            for target_name in (adapter_name, "head_shell"):
                volume = intersection_volume(probe, main[target_name])
                if volume > 0.05:
                    failures.append(
                        f"blocked {side} tilt-adapter screw at X={x:.1f}, Z={z:.1f}: "
                        f"{target_name} ({volume:.2f} mm^3)"
                    )
            support = cylinder_y(3.2, p.head_tilt_adapter_thickness, (x, adapter_y, z))
            support = support - cylinder_y(
                p.m2_5_clearance_hole / 2.0 + 0.1,
                p.head_tilt_adapter_thickness + 2.0,
                (x, adapter_y, z),
            )
            if intersection_volume(support, main[adapter_name]) < 50.0:
                failures.append(
                    f"{side} tilt-adapter screw lacks surrounding material at X={x:.1f}, Z={z:.1f}"
                )

    drive_y = head_tilt_adapter_center_y(p, 1)
    for x, z in head_tilt_horn_mount_positions(p):
        probe = cylinder_y(1.0, p.head_tilt_adapter_thickness + 3.0, (x, drive_y, z))
        if intersection_volume(probe, main["head_tilt_drive_adapter"]) > 0.05:
            failures.append(f"blocked servo-horn screw at X={x:.1f}, Z={z:.1f}")

    passive_y = head_tilt_passive_bushing_center_y(p)
    passive_probe = cylinder_y(
        p.head_tilt_passive_bushing_id / 2.0 - 0.1,
        19.0,
        (p.head_tilt_axis_x, passive_y, p.head_tilt_axis_z),
    )
    for target_name in (
        "head_shell",
        "head_tilt_passive_cartridge",
        "head_tilt_yoke",
    ):
        volume = intersection_volume(passive_probe, main[target_name])
        if volume > 0.05:
            failures.append(
                f"blocked passive tilt shoulder-bolt path: {target_name} ({volume:.2f} mm^3)"
            )

    # Hitec D85MG and R-ML24 drawing contracts. Both axes use the same servo,
    # reducing spare parts while keeping every asymmetric output/mount offset
    # explicit. The passive side uses a real MF84ZZ bearing and ISO-style
    # 4 mm shoulder/M3 thread path rather than a printed journal.
    official_servo_dimensions = {
        "body_length": (p.servo_body_length, 29.0),
        "body_width": (p.servo_body_width, 13.0),
        "body_height": (p.servo_body_height, 30.0),
        "flange_length": (p.servo_flange_length, 39.8),
        "mount_spacing": (p.servo_mount_spacing, 30.8),
        "mount_hole": (p.servo_mount_hole, 4.5),
        "output_offset": (p.servo_output_offset, 7.8723),
        "spline_diameter": (p.servo_output_diameter, 5.76),
        "stall_current_6v": (p.servo_stall_current_6v, 1.4),
    }
    for label, (actual, expected) in official_servo_dimensions.items():
        if abs(actual - expected) > 0.01:
            failures.append(
                f"Hitec D85MG {label} drifted from drawing: {actual:.4f} vs {expected:.4f}"
            )
    if tuple(p.servo_horn_threaded_offsets) != (13.0, 16.0):
        failures.append("R-ML24 threaded horn stations drifted from 13/16 mm")
    if not (
        abs(p.head_tilt_passive_bushing_id - 4.0) < 0.01
        and abs(p.head_tilt_passive_bushing_od - 8.0) < 0.01
        and abs(p.head_tilt_passive_bushing_length - 3.0) < 0.01
        and abs(p.head_tilt_passive_bushing_flange_od - 9.2) < 0.01
        and abs(p.head_tilt_passive_bushing_flange_thickness - 0.6) < 0.01
    ):
        failures.append("MF84ZZ passive-bearing dimensions drifted from 4x8x3 / 9.2x0.6 mm")
    if not (
        abs(p.head_tilt_shoulder_length - 12.0) < 0.01
        and abs(p.head_tilt_shoulder_thread_length - 4.0) < 0.01
        and abs(p.head_tilt_shoulder_head_diameter - 6.0) < 0.01
        and abs(p.head_tilt_shoulder_head_height - 3.0) < 0.01
    ):
        failures.append("passive shoulder-screw contract drifted from 4x12/M3x4/6x3 mm")

    pan_plate_z = body_inner_roof_z(p) - 12.0
    for index, (x, y) in enumerate(pan_servo_mount_positions(p), start=1):
        probe = cylinder_z(
            p.m3_clearance_hole / 2.0 - 0.1,
            10.0,
            (x, y, pan_plate_z),
        )
        for target_name in ("pan_servo_mount",):
            volume = intersection_volume(probe, main[target_name])
            if volume > 0.05:
                failures.append(
                    f"blocked D85MG pan mount path {index}: {target_name} ({volume:.2f} mm^3)"
                )
        flange_probe = cylinder_z(
            p.m3_clearance_hole / 2.0 - 0.1,
            p.servo_flange_thickness + 0.2,
            (x, y, pan_servo_mount_plane_z(p)),
        )
        if intersection_volume(flange_probe, fits["fit_pan_servo"]) > 0.05:
            failures.append(f"D85MG pan flange hole {index} misses the plate screw path")

    tilt_mount_y = tilt_servo_mount_plane_y(p)
    for index, (x, z) in enumerate(tilt_servo_mount_positions(p), start=1):
        probe = cylinder_y(
            p.m3_clearance_hole / 2.0 - 0.1,
            9.0,
            (x, tilt_mount_y - 1.0, z),
        )
        if intersection_volume(probe, main["head_tilt_yoke"]) > 0.05:
            failures.append(f"blocked D85MG tilt mount path {index} through yoke cradle")
        flange_probe = cylinder_y(
            p.m3_clearance_hole / 2.0 - 0.1,
            p.servo_flange_thickness + 0.2,
            (x, tilt_mount_y, z),
        )
        if intersection_volume(flange_probe, fits["fit_tilt_servo"]) > 0.05:
            failures.append(f"D85MG tilt flange hole {index} misses the cradle screw path")

    pan_horn_z = pan_servo_horn_center_z(p)
    for index, (x, y) in enumerate(pan_servo_horn_mount_positions(p), start=1):
        path_bottom = pan_horn_z - p.servo_horn_overall_thickness / 2.0
        path_top = p.pan_bearing_center_z - p.pan_bearing_width / 2.0
        probe = cylinder_z(
            p.servo_horn_thread / 2.0 - 0.1,
            path_top - path_bottom,
            (x, y, (path_bottom + path_top) / 2.0),
        )
        for target_name in ("pan_bearing_retainer",):
            volume = intersection_volume(probe, main[target_name])
            if volume > 0.05:
                failures.append(
                    f"blocked R-ML24 pan horn screw {index}: {target_name} ({volume:.2f} mm^3)"
                )
        if intersection_volume(probe, fits["fit_pan_servo_horn"]) > 0.05:
            failures.append(f"R-ML24 pan horn threaded station {index} is blocked")

    if not (
        abs(p.pan_bearing_id - 35.0) < 0.01
        and abs(p.pan_bearing_od - 47.0) < 0.01
        and abs(p.pan_bearing_width - 7.0) < 0.01
        and abs(p.pan_bearing_outer_shoulder_bore - 45.0) < 0.01
    ):
        failures.append("6807-2RS pan-bearing dimensions drifted from 35x47x7 / 45 mm housing shoulder")
    bearing_box = fits["fit_pan_bearing"].bounding_box()
    bearing_bottom = p.pan_bearing_center_z - p.pan_bearing_width / 2.0
    bearing_top = p.pan_bearing_center_z + p.pan_bearing_width / 2.0
    if abs(float(bearing_box.min.Z) - bearing_bottom) > 0.05 or abs(
        float(bearing_box.max.Z) - bearing_top
    ) > 0.05:
        failures.append("6807 pan-bearing envelope misses its axial seat")
    retainer_box = main["pan_bearing_retainer"].bounding_box()
    if abs(float(retainer_box.max.Z) - bearing_bottom) > 0.05:
        failures.append("pan-bearing retainer does not meet the inner-ring lower face")

    inner_shoulder_probe = cylinder_z(
        p.pan_bearing_shoulder_od / 2.0 - 0.1,
        0.4,
        (p.neck_x, 0.0, bearing_top + 0.2),
    ) - cylinder_z(
        p.pan_bearing_id / 2.0 + 0.1,
        0.8,
        (p.neck_x, 0.0, bearing_top + 0.2),
    )
    if intersection_volume(inner_shoulder_probe, main["neck"]) < 10.0:
        failures.append("rotating neck lacks a bearing-inner-ring upper shoulder")
    outer_shoulder_probe = cylinder_z(
        p.pan_bearing_od / 2.0 - 0.1,
        0.4,
        (p.neck_x, 0.0, bearing_top + 0.2),
    ) - cylinder_z(
        p.pan_bearing_outer_shoulder_bore / 2.0 + 0.1,
        0.8,
        (p.neck_x, 0.0, bearing_top + 0.2),
    )
    if intersection_volume(outer_shoulder_probe, main["neck_collar"]) < 5.0:
        failures.append("fixed collar lacks a bearing-outer-ring upper shoulder")

    retainer_bottom = bearing_bottom - p.pan_bearing_retainer_thickness
    for index, (x, y) in enumerate(
        pan_bearing_retainer_mount_positions(p), start=1
    ):
        probe = cylinder_z(
            p.m2_5_clearance_hole / 2.0 - 0.1,
            8.0,
            (x, y, retainer_bottom + 4.0),
        )
        for target_name in ("pan_bearing_retainer", "neck"):
            volume = intersection_volume(probe, main[target_name])
            if volume > 0.05:
                failures.append(
                    f"blocked pan-bearing retainer screw {index}: "
                    f"{target_name} ({volume:.2f} mm^3)"
                )

    for index, (x, y) in enumerate(pan_bearing_key_positions(p), start=1):
        key_probe = rounded_box(
            p.pan_bearing_key_length - 0.3,
            p.pan_bearing_key_width - 0.3,
            18.0,
            0.7,
            (x, y, p.pan_bearing_center_z + 1.0),
        )
        for target_name in ("body_shell", "top_lid"):
            volume = intersection_volume(key_probe, main[target_name])
            if volume > 0.05:
                failures.append(
                    f"blocked pan-bearing anti-rotation key {index}: "
                    f"{target_name} ({volume:.2f} mm^3)"
                )
        if intersection_volume(key_probe, main["neck_collar"]) < 20.0:
            failures.append(f"pan-bearing anti-rotation key {index} is not fused to collar")

    servo_fit_targets = {
        "fit_pan_servo": ("body_shell", "pan_servo_mount", "neck"),
        "fit_pan_servo_horn": (
            "body_shell",
            "pan_servo_mount",
            "neck",
            "neck_collar",
        ),
        "fit_pan_bearing": (
            "body_shell",
            "top_lid",
            "neck_collar",
            "neck",
            "pan_bearing_retainer",
        ),
        "fit_tilt_servo": ("head_shell", "head_tilt_yoke", "head_tilt_drive_adapter"),
        "fit_tilt_servo_horn": (
            "head_shell",
            "head_tilt_yoke",
            "head_tilt_drive_adapter",
        ),
        "fit_tilt_passive_bushing": (
            "head_shell",
            "head_tilt_yoke",
            "head_tilt_passive_cartridge",
        ),
        "fit_tilt_shoulder_bolt": (
            "head_shell",
            "head_tilt_yoke",
            "head_tilt_passive_cartridge",
        ),
        "fit_servo_cable_corridor": (
            "body_shell",
            "top_lid",
            "neck_collar",
            "neck",
            "head_tilt_yoke",
        ),
    }
    for fit_name, target_names in servo_fit_targets.items():
        for target_name in target_names:
            volume = intersection_volume(fits[fit_name], main[target_name])
            if volume > 0.05:
                failures.append(
                    f"head hardware collision: {fit_name} vs {target_name} ({volume:.2f} mm^3)"
                )

    # Prove the complete moving printed head clears the fixed yoke/neck at both
    # pitch limits, then sample the same extreme poses across useful pan range.
    tilt_axis = Axis(
        (p.head_tilt_axis_x, 0.0, p.head_tilt_axis_z),
        (0.0, 1.0, 0.0),
    )
    pan_axis = Axis((p.neck_x, 0.0, 0.0), (0.0, 0.0, 1.0))
    moving_head_names = (
        "head_shell",
        "head_faceplate",
        "head_rear_cover",
        "camera_carrier",
        "head_eye_led_carrier_1",
        "head_eye_led_carrier_2",
        "eye_socket_1",
        "eye_socket_2",
        "eye_glow_1",
        "eye_glow_2",
        "eyebrow_1",
        "eyebrow_2",
        "head_tilt_drive_adapter",
        "head_tilt_passive_cartridge",
    )
    moving_head = Compound([main[name] for name in moving_head_names])
    moving_horn_arm = fits["fit_tilt_servo_horn"] - cylinder_y(
        8.0,
        p.servo_horn_overall_thickness + 4.0,
        (p.head_tilt_axis_x, tilt_servo_horn_center_y(p), p.head_tilt_axis_z),
    )
    for tilt_angle in range(
        -int(p.head_tilt_limit_degrees),
        int(p.head_tilt_limit_degrees) + 1,
        5,
    ):
        posed_horn_arm = moving_horn_arm.rotate(tilt_axis, float(tilt_angle))
        for target_name, target_shape in (
            ("head_tilt_yoke", main["head_tilt_yoke"]),
            ("fit_tilt_servo", fits["fit_tilt_servo"]),
        ):
            volume = intersection_volume(posed_horn_arm, target_shape)
            if volume > 0.05:
                failures.append(
                    f"R-ML24 horn sweep collision at tilt {tilt_angle:+d} deg: "
                    f"{target_name} ({volume:.2f} mm^3)"
                )
    for tilt_angle in (-p.head_tilt_limit_degrees, p.head_tilt_limit_degrees):
        tilted_head = moving_head.rotate(tilt_axis, tilt_angle)
        for target_name in ("head_tilt_yoke", "neck"):
            volume = intersection_volume(tilted_head, main[target_name])
            if volume > 0.05:
                failures.append(
                    f"head tilt collision at {tilt_angle:+.0f} deg: "
                    f"moving head vs {target_name} ({volume:.2f} mm^3)"
                )
        for pan_angle in (-60.0, 0.0, 60.0):
            posed_head = tilted_head.rotate(pan_axis, pan_angle)
            for target_name in ("top_lid", "top_vent_inlay", "estop_well", "estop"):
                volume = intersection_volume(posed_head, main[target_name])
                if volume > 0.05:
                    failures.append(
                        f"head pose collision at tilt {tilt_angle:+.0f}/pan {pan_angle:+.0f} deg: "
                        f"moving head vs {target_name} ({volume:.2f} mm^3)"
                    )

    inner_x = p.body_length / 2.0 - p.wall
    inner_y = p.body_width / 2.0 - p.wall
    inner_z_max = p.body_bottom + p.body_height - p.wall
    body_interior_fits = (
        "fit_pi5",
        "fit_motor_controller",
        "fit_motor_controller_board",
        "fit_motor_controller_terminal_service",
        "fit_motor_controller_airflow",
        "fit_battery",
        "fit_battery_lead_service",
        "fit_safety_mcu",
        "fit_future_ai_hat_clearance",
        "fit_mic_array",
        "fit_speaker_left",
        "fit_speaker_right",
        "fit_tof_front_left",
        "fit_tof_front_right",
        "fit_tof_side_left",
        "fit_tof_side_right",
        "fit_estop_terminal_service",
        "fit_pi_buck_regulator",
        "fit_pi_buck_terminal_service_front",
        "fit_pi_buck_terminal_service_rear",
        "fit_servo_regulator",
        "fit_servo_regulator_wire_service",
        "fit_motor_cutoff",
        "fit_motor_cutoff_terminal_service",
        "fit_motor_cutoff_metal_plate",
        *power_distribution_fit_names,
        *audio_amp_fit_names,
        "fit_power_harness_left",
        "fit_power_harness_right",
        "fit_power_deck_standoff_1",
        "fit_power_deck_standoff_2",
        "fit_power_deck_standoff_3",
        "fit_power_deck_standoff_4",
        "fit_pi_regulator_standoff_1",
        "fit_pi_regulator_standoff_2",
        "fit_pi_regulator_standoff_3",
        "fit_pi_regulator_standoff_4",
        "fit_servo_regulator_standoff_1",
        "fit_servo_regulator_standoff_2",
        "fit_servo_regulator_standoff_3",
        "fit_motor_controller_standoff_1",
        "fit_motor_controller_standoff_2",
        "fit_motor_controller_standoff_3",
        "fit_motor_controller_standoff_4",
        "fit_motor_controller_plate_standoff_1",
        "fit_motor_controller_plate_standoff_2",
        "fit_motor_controller_plate_standoff_3",
        "fit_motor_controller_plate_standoff_4",
        "fit_drive_motor_bracket_spacer_left_1",
        "fit_drive_motor_bracket_spacer_left_2",
        "fit_drive_motor_bracket_spacer_left_3",
        "fit_drive_motor_bracket_spacer_right_1",
        "fit_drive_motor_bracket_spacer_right_2",
        "fit_drive_motor_bracket_spacer_right_3",
        "fit_safety_shelf_standoff_1",
        "fit_safety_shelf_standoff_2",
        "fit_safety_shelf_standoff_3",
        "fit_safety_shelf_standoff_4",
        "fit_safety_mcu_standoff_1",
        "fit_safety_mcu_standoff_2",
        "fit_safety_mcu_standoff_3",
        "fit_safety_mcu_standoff_4",
    )
    for name in body_interior_fits:
        if not inside_box(
            fits[name],
            -inner_x,
            inner_x,
            -inner_y,
            inner_y,
            p.body_bottom,
            inner_z_max,
        ):
            failures.append(f"interior envelope escaped body cavity: {name}")

    service_fit_targets = {
        "fit_camera_module_3": ("camera_carrier", "head_shell"),
        "fit_rear_service_bay": ("body_shell", "rear_service_panel", "top_cable_strain_relief"),
        "fit_charge_jack_body": (
            "body_shell",
            "rear_service_panel",
            "rear_service_cartridge_power_charge",
        ),
        "fit_charge_jack_bezel": (
            "body_shell",
            "rear_service_panel",
            "rear_service_cartridge_power_charge",
        ),
        "fit_charge_jack_terminal_service": (
            "body_shell",
            "rear_service_panel",
            "rear_service_cartridge_power_charge",
            "top_cable_strain_relief",
        ),
        "fit_charge_jack_plug_service": (
            "body_shell",
            "rear_service_panel",
            "rear_service_cartridge_power_charge",
        ),
        "fit_mute_switch_body": ("body_shell", "rear_service_panel", "rear_service_cartridge_mute_status"),
        "fit_mute_switch_bezel": ("body_shell", "rear_service_panel", "rear_service_cartridge_mute_status"),
        "fit_mute_switch_actuator": ("body_shell", "rear_service_panel", "rear_service_cartridge_mute_status"),
        "fit_mute_switch_led_ring": ("body_shell", "rear_service_panel", "rear_service_cartridge_mute_status"),
        "fit_mute_switch_terminal_service": (
            "body_shell",
            "rear_service_panel",
            "rear_service_cartridge_mute_status",
            "top_cable_strain_relief",
        ),
        "fit_service_jack_body": (
            "body_shell",
            "rear_service_panel",
            "rear_service_cartridge_service_data",
            "rear_service_data_carrier",
        ),
        "fit_service_jack_pcb": (
            "body_shell",
            "rear_service_panel",
            "rear_service_cartridge_service_data",
            "rear_service_data_carrier",
        ),
        "fit_service_jack_wire_service": (
            "body_shell",
            "rear_service_panel",
            "rear_service_cartridge_service_data",
            "rear_service_data_carrier",
            "top_cable_strain_relief",
        ),
        "fit_service_jack_plug_service": (
            "body_shell",
            "rear_service_panel",
            "rear_service_cartridge_service_data",
        ),
        "fit_pi_buck_regulator": ("power_service_deck",),
        "fit_pi_buck_terminal_service_front": ("power_service_deck",),
        "fit_pi_buck_terminal_service_rear": ("power_service_deck",),
        "fit_servo_regulator": ("power_service_deck",),
        "fit_servo_regulator_wire_service": ("power_service_deck",),
        "fit_motor_cutoff": ("power_service_deck",),
        "fit_motor_cutoff_terminal_service": ("power_service_deck",),
        "fit_motor_cutoff_metal_plate": ("power_service_deck",),
        "fit_power_harness_left": ("power_harness_rail_left", "power_service_deck"),
        "fit_power_harness_right": ("power_harness_rail_right", "power_service_deck"),
        "fit_motor_controller": ("motor_controller_mount",),
        "fit_motor_controller_board": ("motor_controller_mount",),
        "fit_drive_motor_left": ("motor_pod_left", "motor_pod_cover_left", "body_shell"),
        "fit_drive_motor_right": ("motor_pod_right", "motor_pod_cover_right", "body_shell"),
        "fit_drive_motor_bracket_left": ("motor_pod_left", "base_tray"),
        "fit_drive_motor_bracket_right": ("motor_pod_right", "base_tray"),
        "fit_drive_motor_hub_left": ("wheel_left_2", "hub_ring_left_2", "hub_left_2"),
        "fit_drive_motor_hub_right": ("wheel_right_2", "hub_ring_right_2", "hub_right_2"),
        "fit_drive_motor_cable_left": ("motor_pod_left", "motor_pod_cover_left"),
        "fit_drive_motor_cable_right": ("motor_pod_right", "motor_pod_cover_right"),
        "fit_safety_mcu": ("safety_mcu_mount",),
        "fit_safety_mcu_board": ("safety_mcu_mount",),
        "fit_safety_mcu_header_left": ("safety_mcu_mount",),
        "fit_safety_mcu_header_right": ("safety_mcu_mount",),
        "fit_battery": ("battery_cradle",),
        "fit_battery_lead_service": ("battery_cradle",),
        "fit_mic_array": ("mic_array_cradle", "body_shell", "top_lid"),
        "fit_speaker_left": ("speaker_mount_left", "body_shell"),
        "fit_speaker_right": ("speaker_mount_right", "body_shell"),
        "fit_tof_front_left": ("tof_pod_front_left", "front_sensor_fascia", "body_shell"),
        "fit_tof_front_right": ("tof_pod_front_right", "front_sensor_fascia", "body_shell"),
        "fit_tof_side_left": ("tof_pod_side_left", "body_shell", "side_fairing_left"),
        "fit_tof_side_right": ("tof_pod_side_right", "body_shell", "side_fairing_right"),
    }
    distribution_cover_clearance_fits = {
        "fit_power_distribution_board",
        "fit_power_distribution_header",
        "fit_power_distribution_receptacle",
        "fit_power_distribution_harness_straight",
        "fit_power_distribution_harness_bend",
        *(f"fit_power_distribution_holder_{index}" for index in range(1, 5)),
        *(f"fit_power_distribution_fuse_{index}" for index in range(1, 5)),
    }
    for fit_name in power_distribution_fit_names:
        targets = ["power_service_deck"]
        if fit_name in distribution_cover_clearance_fits:
            targets.append("power_distribution_cover")
        service_fit_targets[fit_name] = tuple(targets)
    for side in ("left", "right"):
        for fit_name in audio_amp_fit_names:
            if fit_name.startswith(f"fit_audio_amp_{side}"):
                service_fit_targets[fit_name] = (f"speaker_mount_{side}",)
    for fit_name, target_names in service_fit_targets.items():
        for target_name in target_names:
            volume = intersection_volume(fits[fit_name], main[target_name])
            if volume > 0.05:
                failures.append(
                    f"service hardware collision: {fit_name} vs {target_name} ({volume:.2f} mm^3)"
                )

    for index, (x, y) in enumerate(power_deck_mount_positions(p), start=1):
        fit_name = f"fit_power_deck_standoff_{index}"
        standoff_box = fits[fit_name].bounding_box()
        if abs(float(standoff_box.min.Z - p.body_bottom)) > 0.05:
            failures.append(f"power-deck standoff {index} does not meet base tray")
        if abs(float(standoff_box.max.Z - (p.power_deck_z - 2.0))) > 0.05:
            failures.append(f"power-deck standoff {index} does not meet power deck")
        for target_name in ("base_tray", "power_service_deck", "battery_cradle", "motor_pod_left", "motor_pod_right"):
            volume = intersection_volume(fits[fit_name], main[target_name])
            if volume > 0.05:
                failures.append(
                    f"power-deck standoff collision: {fit_name} vs {target_name} ({volume:.2f} mm^3)"
                )

    # Drawing-backed Pololu regulator boards mount directly to the removable
    # deck on metal M2 standoffs. Prove every standoff reaches both mating
    # faces and every screw axis remains open through deck and board.
    deck_top = p.power_deck_z + 2.0
    regulator_contracts = (
        (
            "Pi D24V90F5",
            "fit_pi_buck_regulator",
            pi_regulator_mount_positions(p),
            p.pi_regulator_mount_hole,
            p.pi_regulator_standoff_height,
            "fit_pi_regulator_standoff_",
        ),
        (
            "servo D36V50F6",
            "fit_servo_regulator",
            servo_regulator_mount_positions(p),
            p.servo_regulator_mount_hole,
            p.servo_regulator_standoff_height,
            "fit_servo_regulator_standoff_",
        ),
    )
    for label, board_name, positions, hole_diameter, standoff_height, prefix in regulator_contracts:
        board_box = fits[board_name].bounding_box()
        board_bottom = deck_top + standoff_height
        if abs(float(board_box.min.Z - board_bottom)) > 0.05:
            failures.append(f"{label} board misses its standoff plane")
        for index, (x, y) in enumerate(positions, start=1):
            standoff_name = f"{prefix}{index}"
            standoff_box = fits[standoff_name].bounding_box()
            if abs(float(standoff_box.min.Z - deck_top)) > 0.05:
                failures.append(f"{label} standoff {index} misses power deck")
            if abs(float(standoff_box.max.Z - board_bottom)) > 0.05:
                failures.append(f"{label} standoff {index} misses board")
            if intersection_volume(fits[standoff_name], main["power_service_deck"]) > 0.05:
                failures.append(f"{label} standoff {index} collides with power deck")
            probe_bottom = p.power_deck_z - 3.0
            probe_top = float(board_box.max.Z) + 1.0
            probe = cylinder_z(
                hole_diameter / 2.0 - 0.1,
                probe_top - probe_bottom,
                (x, y, (probe_bottom + probe_top) / 2.0),
            )
            for target_name, target in (
                ("power_service_deck", main["power_service_deck"]),
                (board_name, fits[board_name]),
            ):
                volume = intersection_volume(probe, target)
                if volume > 0.05:
                    failures.append(
                        f"blocked {label} M2 path {index}: {target_name} ({volume:.2f} mm^3)"
                    )


    # Albright SW60 drawing contract. The contactor sits on a custom metal
    # carrier plate so the printed deck organizes the assembly but is not the
    # sole safety-hardware retention or cable-torque path.
    sw60_dimensions = {
        "body_length": (p.motor_cutoff_body_length, 63.0),
        "body_width": (p.motor_cutoff_body_width, 37.0),
        "body_height": (p.motor_cutoff_body_height, 28.0),
        "terminal_overall_length": (p.motor_cutoff_terminal_overall_length, 81.0),
    }
    for dimension, (actual, expected) in sw60_dimensions.items():
        if abs(actual - expected) > 0.05:
            failures.append(
                f"Albright SW60 {dimension} drifted: {actual:.2f} vs {expected:.2f} mm"
            )
    cutoff_plate = fits["fit_motor_cutoff_metal_plate"]
    cutoff_body_box = fits["fit_motor_cutoff"].bounding_box()
    cutoff_plate_box = cutoff_plate.bounding_box()
    if abs(float(cutoff_plate_box.min.Z - deck_top)) > 0.05:
        failures.append("SW60 metal carrier misses power-deck top")
    if abs(float(cutoff_body_box.min.Z - cutoff_plate_box.max.Z)) > 0.05:
        failures.append("SW60 body misses metal carrier top")
    for index, (x, y) in enumerate(motor_cutoff_plate_mount_positions(p), start=1):
        probe_bottom = p.power_deck_z - 3.0
        probe_top = float(cutoff_plate_box.max.Z) + 1.0
        probe = cylinder_z(
            p.motor_cutoff_plate_mount_hole / 2.0 - 0.1,
            probe_top - probe_bottom,
            (x, y, (probe_bottom + probe_top) / 2.0),
        )
        for target_name, target in (
            ("power_service_deck", main["power_service_deck"]),
            ("fit_motor_cutoff_metal_plate", cutoff_plate),
        ):
            volume = intersection_volume(probe, target)
            if volume > 0.05:
                failures.append(
                    f"blocked SW60 metal-carrier M3 path {index}: "
                    f"{target_name} ({volume:.2f} mm^3)"
                )

    # Custom four-branch accessory board. The geometry is pinned to four
    # Littelfuse 01550900M OMNI-BLOK Nano2 holders and Molex's drawing-backed
    # 43045-1000 / 43025-1000 Micro-Fit interface. This proves packaging and
    # service access only; PCB copper, exact fuse values, and fault behavior
    # remain electrical-review and physical-test gates.
    distribution_dimensions = {
        "board_length": (p.power_distribution_board_length, 40.0),
        "board_width": (p.power_distribution_board_width, 21.0),
        "board_thickness": (p.power_distribution_board_thickness, 1.6),
        "holder_length": (p.power_distribution_holder_length, 9.73),
        "holder_width": (p.power_distribution_holder_width, 5.03),
        "holder_height": (p.power_distribution_holder_height, 3.81),
        "header_width": (p.power_distribution_header_width, 18.65),
        "header_depth": (p.power_distribution_header_depth, 12.24),
        "header_height": (p.power_distribution_header_height, 9.91),
        "receptacle_width": (p.power_distribution_receptacle_width, 15.85),
        "receptacle_depth": (p.power_distribution_receptacle_depth, 17.56),
        "receptacle_height": (p.power_distribution_receptacle_height, 10.81),
    }
    for dimension, (actual, expected) in distribution_dimensions.items():
        if abs(actual - expected) > 0.05:
            failures.append(
                f"power-distribution {dimension} drifted: "
                f"{actual:.2f} vs {expected:.2f} mm"
            )
    if len(power_distribution_holder_positions(p)) != 4:
        failures.append("power-distribution board must carry exactly four fuse holders")
    if p.power_distribution_total_limit_a > 6.0:
        failures.append("power-distribution provisional total limit exceeds 6 A")
    if p.power_distribution_branch_limit_a > 5.0:
        failures.append("power-distribution provisional branch limit exceeds 5 A")
    if p.power_distribution_total_limit_a > p.power_distribution_connector_limit_a:
        failures.append("power-distribution total limit exceeds derated connector contact")
    if p.power_distribution_branch_limit_a > p.power_distribution_holder_rating_a:
        failures.append("power-distribution branch limit exceeds OMNI-BLOK rating")

    distribution_board = fits["fit_power_distribution_board"]
    distribution_cover = main["power_distribution_cover"]
    distribution_service = fits["fit_power_distribution_fuse_service"]
    if len(distribution_cover.solids()) != 1:
        failures.append("power-distribution cover is not one printable solid")
    if intersection_volume(distribution_cover, main["power_service_deck"]) > 0.05:
        failures.append("power-distribution cover collides with power deck")
    missing_cover_service = float(distribution_cover.volume) - intersection_volume(
        distribution_cover, distribution_service
    )
    if missing_cover_service > 0.05:
        failures.append(
            "power-distribution cover escapes its fuse-service volume "
            f"({missing_cover_service:.2f} mm^3)"
        )

    board_box = distribution_board.bounding_box()
    board_bottom = deck_top + p.power_distribution_lower_standoff_height
    board_top = board_bottom + p.power_distribution_board_thickness
    if abs(float(board_box.min.Z - board_bottom)) > 0.05:
        failures.append("power-distribution PCB misses lower standoff plane")
    for index, (x, y) in enumerate(power_distribution_board_mount_positions(p), start=1):
        lower_name = f"fit_power_distribution_lower_standoff_{index}"
        upper_name = f"fit_power_distribution_upper_standoff_{index}"
        lower_box = fits[lower_name].bounding_box()
        upper_box = fits[upper_name].bounding_box()
        if abs(float(lower_box.min.Z - deck_top)) > 0.05:
            failures.append(f"power-distribution lower standoff {index} misses deck")
        if abs(float(lower_box.max.Z - board_bottom)) > 0.05:
            failures.append(f"power-distribution lower standoff {index} misses PCB")
        if abs(float(upper_box.min.Z - board_top)) > 0.05:
            failures.append(f"power-distribution upper standoff {index} misses PCB")
        probe = cylinder_z(
            p.power_distribution_mount_hole / 2.0 - 0.1,
            p.power_distribution_cover_height + 10.0,
            (
                x,
                y,
                deck_top + (p.power_distribution_cover_height + 4.0) / 2.0,
            ),
        )
        for target_name, target in (
            ("power_service_deck", main["power_service_deck"]),
            ("fit_power_distribution_board", distribution_board),
            ("power_distribution_cover", distribution_cover),
        ):
            volume = intersection_volume(probe, target)
            if volume > 0.05:
                failures.append(
                    f"blocked power-distribution M2 stack path {index}: "
                    f"{target_name} ({volume:.2f} mm^3)"
                )

    for index in range(1, 5):
        holder_name = f"fit_power_distribution_holder_{index}"
        fuse_name = f"fit_power_distribution_fuse_{index}"
        for fit_name in (holder_name, fuse_name):
            shape = fits[fit_name]
            missing = float(shape.volume) - intersection_volume(shape, distribution_service)
            if missing > 0.05:
                failures.append(
                    f"power-distribution service volume misses {fit_name} "
                    f"({missing:.2f} mm^3)"
                )

    service_box = distribution_service.bounding_box()
    expected_service_top = deck_top + p.power_distribution_fuse_service_height
    if abs(float(service_box.max.Z - expected_service_top)) > 0.05:
        failures.append("power-distribution fuse-puller service height drifted")
    body_inner_rear = p.body_length / 2.0 - p.wall
    harness_box = fits["fit_power_distribution_harness_bend"].bounding_box()
    if float(harness_box.max.X) > body_inner_rear + 0.05:
        failures.append("power-distribution harness bend escapes body cavity")

    for x, y in power_distribution_strain_slots(p):
        probe = rounded_box(3.1, 7.6, 12.0, 1.2, (x, y, p.power_deck_z))
        volume = intersection_volume(probe, main["power_service_deck"])
        if volume > 0.05:
            failures.append(
                f"blocked power-distribution strain slot at ({x:.0f}, {y:.0f}) "
                f"({volume:.2f} mm^3)"
            )

    # Two U-channel rails retain separate signal and switched-power bundles
    # beneath the removable deck. Their paired strap slots must remain open
    # through both parts, and neither rail may consume battery, mobility, or
    # standoff space.
    harness_main_targets = (
        "power_service_deck",
        "battery_cradle",
        "body_shell",
        "motor_pod_left",
        "motor_pod_right",
        "front_idler_pod_left",
        "front_idler_pod_right",
    )
    harness_fit_targets = (
        "fit_battery",
        "fit_drive_motor_left",
        "fit_drive_motor_right",
        *front_idler_fit_names,
        "fit_future_ai_hat_clearance",
    )
    for side, side_sign in (("left", -1), ("right", 1)):
        rail_name = f"power_harness_rail_{side}"
        rail = main[rail_name]
        for target_name in harness_main_targets:
            volume = intersection_volume(rail, main[target_name])
            if volume > 0.05:
                failures.append(
                    f"power harness rail collision: {rail_name} vs {target_name} "
                    f"({volume:.2f} mm^3)"
                )
        for fit_name in harness_fit_targets:
            volume = intersection_volume(rail, fits[fit_name])
            if volume > 0.05:
                failures.append(
                    f"power harness rail hardware collision: {rail_name} vs {fit_name} "
                    f"({volume:.2f} mm^3)"
                )

        for x, y in power_harness_strap_slots(p, side_sign):
            probe = rounded_box(9.6, 3.1, 12.0, 1.2, (x, y, p.power_deck_z - 2.0))
            for target_name in ("power_service_deck", rail_name):
                volume = intersection_volume(probe, main[target_name])
                if volume > 0.05:
                    failures.append(
                        f"blocked power-harness strap slot on {side} at X={x:.0f}: "
                        f"{target_name} ({volume:.2f} mm^3)"
                    )

    rear_x = p.body_length / 2.0 + 2.0
    for y in (-58.0, 58.0):
        for z in (p.rear_service_panel_z - 22.0, p.rear_service_panel_z + 22.0):
            probe = cylinder_x(
                p.m3_clearance_hole / 2.0 - 0.1,
                15.0,
                (rear_x - 4.5, y, z),
            )
            for target_name in ("body_shell", "rear_service_panel"):
                volume = intersection_volume(probe, main[target_name])
                if volume > 0.05:
                    failures.append(
                        f"blocked rear service-panel screw at Y={y:.0f}, Z={z:.0f}: "
                        f"{target_name} ({volume:.2f} mm^3)"
                    )

    # Each blank rear cartridge must remain a genuinely independent print:
    # its stepped tongue enters the panel opening without collision, while two
    # M2.5 screws pass through the cartridge into real insert-backed frame
    # material. Future connector variants may replace one cartridge without
    # disturbing the other two or the shell-to-frame M3 interface.
    panel_outer_x = rear_x + 2.0
    for role, center_y, center_z in rear_service_cartridge_layout(p):
        cartridge_name = f"rear_service_cartridge_{role}"
        cartridge = main[cartridge_name]
        if len(cartridge.solids()) != 1:
            failures.append(f"rear service cartridge is not one solid: {cartridge_name}")
        box = cartridge.bounding_box()
        if abs(float(box.max.X) - panel_outer_x) > 0.05:
            failures.append(
                f"rear service cartridge is not flush with frame: {cartridge_name}"
            )

        tongue_probe = rounded_panel_yz(
            p.rear_service_cartridge_tongue_depth - 0.1,
            p.rear_service_cartridge_tongue_width - 0.2,
            p.rear_service_cartridge_tongue_height - 0.2,
            2.8,
            (
                panel_outer_x
                - p.rear_service_cartridge_cap_thickness
                - p.rear_service_cartridge_tongue_depth / 2.0
                + 0.025,
                center_y,
                center_z,
            ),
        )
        if intersection_volume(tongue_probe, main["rear_service_panel"]) > 0.05:
            failures.append(
                f"rear service cartridge tongue collides with frame: {cartridge_name}"
            )

        for mount_y, mount_z in rear_service_cartridge_mount_positions(
            p, center_y, center_z
        ):
            probe = cylinder_x(
                p.m2_5_clearance_hole / 2.0 - 0.1,
                11.0,
                (rear_x - 0.5, mount_y, mount_z),
            )
            for target_name in ("rear_service_panel", cartridge_name):
                volume = intersection_volume(probe, main[target_name])
                if volume > 0.05:
                    failures.append(
                        f"blocked rear cartridge screw on {role} at Z={mount_z:.1f}: "
                        f"{target_name} ({volume:.2f} mm^3)"
                    )
            support = cylinder_x(4.0, 4.0, (rear_x - 3.0, mount_y, mount_z))
            support = support - cylinder_x(
                p.insert_hole_m2_5 / 2.0 + 0.1,
                6.0,
                (rear_x - 3.0, mount_y, mount_z),
            )
            if intersection_volume(support, main["rear_service_panel"]) < 45.0:
                failures.append(
                    f"rear cartridge insert lacks frame support: {role} at Z={mount_z:.1f}"
                )

    # The left cartridge is a charge-only inlet for the selected Bioenno pack.
    # It must never expose the Powerpole discharge branch or serve as a robot
    # output. The Switchcraft EN2P3M20 clamps through its exact 10.92 mm opening.
    charge_cutout_probe = rear_charge_jack_cutout(p, 8.0, rear_x)
    if intersection_volume(
        charge_cutout_probe,
        main["rear_service_cartridge_power_charge"],
    ) > 0.05:
        failures.append("Switchcraft charge-jack cartridge cutout is blocked")
    charge_dimensions = {
        "cutout_diameter": (p.charge_jack_cutout_diameter, 10.92),
        "body_depth": (p.charge_jack_body_depth, 15.75),
        "overall_depth": (p.charge_jack_overall_depth, 20.07),
        "bezel_diameter": (p.charge_jack_bezel_diameter, 15.75),
        "mated_cord_diameter": (p.charge_jack_plug_diameter, 13.5),
    }
    for dimension, (actual, expected) in charge_dimensions.items():
        if abs(actual - expected) > 0.05:
            failures.append(
                f"Switchcraft EN2P3M20 {dimension} drifted: "
                f"{actual:.2f} vs {expected:.2f} mm"
            )
    charge_expected_spans = {
        "fit_charge_jack_body": (
            p.charge_jack_body_depth,
            p.charge_jack_body_diameter,
            p.charge_jack_body_diameter,
        ),
        "fit_charge_jack_bezel": (
            p.charge_jack_front_depth,
            p.charge_jack_bezel_diameter,
            p.charge_jack_bezel_diameter,
        ),
        "fit_charge_jack_terminal_service": (
            p.charge_jack_terminal_service_depth,
            p.charge_jack_terminal_service_width,
            p.charge_jack_terminal_service_height,
        ),
        "fit_charge_jack_plug_service": (
            p.charge_jack_plug_service_length,
            p.charge_jack_plug_diameter,
            p.charge_jack_plug_diameter,
        ),
    }
    for fit_name, expected in charge_expected_spans.items():
        box = fits[fit_name].bounding_box()
        spans = (
            float(box.max.X - box.min.X),
            float(box.max.Y - box.min.Y),
            float(box.max.Z - box.min.Z),
        )
        if any(abs(actual - target) > 0.05 for actual, target in zip(spans, expected)):
            failures.append(f"Switchcraft charge-jack envelope drift: {fit_name}")
    charge_edge_ligament = (
        p.rear_service_cartridge_width / 2.0
        - (
            p.charge_jack_cutout_diameter + p.charge_jack_cutout_clearance
        )
        / 2.0
    )
    charge_screw_ligament = (
        p.rear_service_cartridge_mount_z_offset
        - (
            p.charge_jack_cutout_diameter + p.charge_jack_cutout_clearance
        )
        / 2.0
        - p.m2_5_clearance_hole / 2.0
    )
    if charge_edge_ligament < 4.0 or charge_screw_ligament < 3.0:
        failures.append("charge-jack cutout consumes cartridge or screw ligament")
    for fit_name in (
        "fit_charge_jack_body",
        "fit_charge_jack_terminal_service",
    ):
        for protected_name in (
            "fit_estop_switch_body",
            "fit_estop_terminal_service",
            "fit_mute_switch_body",
            "fit_mute_switch_terminal_service",
            "fit_service_jack_body",
            "fit_service_jack_pcb",
            "fit_service_jack_wire_service",
        ):
            volume = intersection_volume(fits[fit_name], fits[protected_name])
            if volume > 0.05:
                failures.append(
                    f"charge-inlet hardware collision: {fit_name} vs "
                    f"{protected_name} ({volume:.2f} mm^3)"
                )
    if not inside_box(
        fits["fit_charge_jack_terminal_service"],
        -inner_x,
        inner_x,
        -inner_y,
        inner_y,
        p.body_bottom,
        inner_z_max,
    ):
        failures.append("charge-jack terminal service escaped body cavity")

    # The center cartridge now exposes a shallow, protected 3.3 V UART service
    # interface. Its right-angle TRRS jack and horizontal PCB stay entirely
    # behind the panel but in front of the E-stop body.
    service_cutout_probe = rear_service_jack_cutout(p, 8.0, rear_x)
    if intersection_volume(
        service_cutout_probe,
        main["rear_service_cartridge_service_data"],
    ) > 0.05:
        failures.append("Switchcraft service-jack cartridge cutout is blocked")
    service_dimensions = {
        "body_length": (p.service_jack_body_length, 15.5),
        "body_width": (p.service_jack_body_width, 6.8),
        "body_height": (p.service_jack_body_height, 5.3),
    }
    for dimension, (actual, expected) in service_dimensions.items():
        if abs(actual - expected) > 0.05:
            failures.append(
                f"Switchcraft 35RASMT5CHNTRX {dimension} drifted: "
                f"{actual:.2f} vs {expected:.2f} mm"
            )
    carrier = main["rear_service_data_carrier"]
    if len(carrier.solids()) != 1:
        failures.append("rear service-data carrier is not one printable solid")
    for index, (mount_y, mount_z) in enumerate(
        service_jack_carrier_mount_positions(p), start=1
    ):
        probe = cylinder_x(
            p.service_jack_carrier_mount_hole / 2.0 - 0.1,
            12.0,
            (rear_x - 1.0, mount_y, mount_z),
        )
        for target_name in (
            "rear_service_cartridge_service_data",
            "rear_service_data_carrier",
        ):
            volume = intersection_volume(probe, main[target_name])
            if volume > 0.05:
                failures.append(
                    f"blocked service-carrier M2 path {index}: "
                    f"{target_name} ({volume:.2f} mm^3)"
                )
        support = cylinder_x(3.0, 4.5, (148.0, mount_y, mount_z))
        support = support - cylinder_x(
            p.m2_clearance_hole / 2.0 + 0.1,
            6.0,
            (148.0, mount_y, mount_z),
        )
        if intersection_volume(support, carrier) < 25.0:
            failures.append(f"service-carrier M2 path {index} lacks boss support")

    pcb_box = fits["fit_service_jack_pcb"].bounding_box()
    shelf_top_z = p.service_jack_pcb_bottom_z - 0.2
    if abs(float(pcb_box.min.Z) - (shelf_top_z + 0.2)) > 0.05:
        failures.append("service UART PCB misses carrier shelf")
    for index, (x, y) in enumerate(service_jack_pcb_mount_positions(p), start=1):
        probe = cylinder_z(
            p.service_jack_pcb_mount_hole / 2.0 - 0.1,
            p.service_jack_carrier_shelf_thickness
            + p.service_jack_pcb_thickness
            + 2.0,
            (
                x,
                y,
                p.service_jack_pcb_bottom_z
                - p.service_jack_carrier_shelf_thickness / 2.0
                + p.service_jack_pcb_thickness / 2.0,
            ),
        )
        for target_name, target in (
            ("rear_service_data_carrier", carrier),
            ("fit_service_jack_pcb", fits["fit_service_jack_pcb"]),
        ):
            volume = intersection_volume(probe, target)
            if volume > 0.05:
                failures.append(
                    f"blocked service-PCB M2 path {index}: "
                    f"{target_name} ({volume:.2f} mm^3)"
                )
    for fit_name in (
        "fit_service_jack_body",
        "fit_service_jack_pcb",
        "fit_service_jack_wire_service",
    ):
        for protected_name in (
            "fit_estop_switch_body",
            "fit_estop_terminal_service",
            "fit_mute_switch_body",
            "fit_mute_switch_terminal_service",
        ):
            volume = intersection_volume(fits[fit_name], fits[protected_name])
            if volume > 0.05:
                failures.append(
                    f"service-data hardware collision: {fit_name} vs "
                    f"{protected_name} ({volume:.2f} mm^3)"
                )
    estop_rear_x = float(fits["fit_estop_switch_body"].bounding_box().max.X)
    jack_inner_x = float(fits["fit_service_jack_body"].bounding_box().min.X)
    if jack_inner_x - estop_rear_x < 2.0:
        failures.append("service jack has less than 2 mm E-stop body clearance")

    # The right cartridge clamps the exact E-Switch PVB3F230SS311 through its
    # two-flat 16 mm panel opening. Verify
    # the purchase envelope, anti-rotation cutout, nut-capable panel thickness,
    # screw ligaments, and rear terminal service space as one contract.
    if not (
        p.mute_switch_panel_min
        <= p.rear_service_cartridge_cap_thickness
        <= p.mute_switch_panel_max
    ):
        failures.append("PVB3 mute cartridge thickness is outside the 1-7 mm panel range")
    mute_cutout_probe = rear_mute_switch_cutout(
        p,
        8.0,
        rear_x,
        clearance=-0.1,
    )
    if intersection_volume(
        mute_cutout_probe,
        main["rear_service_cartridge_mute_status"],
    ) > 0.05:
        failures.append("PVB3 mute-switch two-flat cutout is blocked")
    mute_expected_spans = {
        "fit_mute_switch_body": (
            p.mute_switch_body_depth,
            p.mute_switch_cutout_flat_width,
            p.mute_switch_cutout_diameter,
        ),
        "fit_mute_switch_bezel": (
            p.mute_switch_bezel_depth,
            p.mute_switch_bezel_diameter,
            p.mute_switch_bezel_diameter,
        ),
        "fit_mute_switch_actuator": (
            p.mute_switch_actuator_depth,
            p.mute_switch_actuator_diameter,
            p.mute_switch_actuator_diameter,
        ),
        "fit_mute_switch_terminal_service": (
            p.mute_switch_terminal_service_depth,
            p.mute_switch_terminal_service_width,
            p.mute_switch_terminal_service_height,
        ),
    }
    for fit_name, expected in mute_expected_spans.items():
        box = fits[fit_name].bounding_box()
        spans = (
            float(box.max.X - box.min.X),
            float(box.max.Y - box.min.Y),
            float(box.max.Z - box.min.Z),
        )
        if any(abs(actual - target) > 0.05 for actual, target in zip(spans, expected)):
            failures.append(f"PVB3 mute-switch envelope drift: {fit_name}")
    led_box = fits["fit_mute_switch_led_ring"].bounding_box()
    if abs(float(led_box.max.Y - led_box.min.Y) - p.mute_switch_led_ring_diameter) > 0.05:
        failures.append("PVB3 mute-switch red LED ring diameter drift")
    edge_ligament = (
        p.rear_service_cartridge_width / 2.0
        - (p.mute_switch_cutout_diameter + p.mute_switch_cutout_clearance) / 2.0
    )
    screw_ligament = (
        p.rear_service_cartridge_mount_z_offset
        - (p.mute_switch_cutout_diameter + p.mute_switch_cutout_clearance) / 2.0
        - p.m2_5_clearance_hole / 2.0
    )
    if edge_ligament < 3.0 or screw_ligament < 2.0:
        failures.append("PVB3 mute-switch cutout consumes cartridge or screw ligament")
    if not inside_box(
        fits["fit_mute_switch_terminal_service"],
        -inner_x,
        inner_x,
        -inner_y,
        inner_y,
        p.body_bottom,
        inner_z_max,
    ):
        failures.append("PVB3 mute-switch terminal service escaped body cavity")

    head_x_min = p.head_center_x - p.head_depth / 2.0
    head_x_max = p.head_center_x + p.head_depth / 2.0
    head_y_min = -p.head_width / 2.0
    head_y_max = p.head_width / 2.0
    head_z_min = p.head_center_z - p.head_height / 2.0
    head_z_max = p.head_center_z + p.head_height / 2.0
    camera_head_x_min = head_x_min - p.head_bezel_depth
    if not inside_box(
        fits["fit_camera_module_3"],
        camera_head_x_min,
        head_x_max,
        head_y_min,
        head_y_max,
        head_z_min,
        head_z_max,
    ):
        failures.append("head envelope escaped bezel-inclusive bounds: fit_camera_module_3")
    for name in ("fit_tilt_servo",):
        if not inside_box(
            fits[name],
            head_x_min,
            head_x_max,
            head_y_min,
            head_y_max,
            head_z_min,
            head_z_max,
        ):
            failures.append(f"head envelope escaped shell bounds: {name}")

    max_allowed = bed - margin
    split_coverage = {
        "body_shell": (
            "body_shell_q_front_left",
            "body_shell_q_front_right",
            "body_shell_q_rear_left",
            "body_shell_q_rear_right",
        ),
        "base_tray": (
            "base_tray_half_front",
            "base_tray_half_rear",
        ),
        "bumper_carrier": (
            "bumper_q_front_left",
            "bumper_q_front_right",
            "bumper_q_rear_left",
            "bumper_q_rear_right",
        ),
        "lid_reveal": ("lid_reveal_half_front", "lid_reveal_half_rear"),
        "top_lid": ("top_lid_half_front", "top_lid_half_rear"),
        "side_fairing_left": ("side_fairing_left_front", "side_fairing_left_rear"),
        "side_fairing_right": ("side_fairing_right_front", "side_fairing_right_rear"),
    }
    for name, shape in main.items():
        if name in ("estop", "estop_cap"):
            continue
        box = shape.bounding_box()
        span = max(float(box.max.X - box.min.X), float(box.max.Y - box.min.Y))
        if span <= max_allowed + 0.01:
            continue
        required_parts = split_coverage.get(name)
        if not required_parts:
            failures.append(f"oversized main part has no split variant: {name} ({span:.2f} mm)")
            continue
        missing = [part_name for part_name in required_parts if part_name not in split]
        if missing:
            failures.append(f"split coverage missing for {name}: {', '.join(missing)}")

    required_join_parts = (
        "base_seam_plate",
        "body_seam_plate_side_left",
        "body_seam_plate_side_right",
        "body_seam_plate_end_front",
        "body_seam_plate_end_rear",
        "bumper_seam_plate_side_left",
        "bumper_seam_plate_side_right",
        "bumper_seam_plate_end_front",
        "bumper_seam_plate_end_rear",
    )
    missing_join_parts = [name for name in required_join_parts if name not in split]
    if missing_join_parts:
        failures.append(f"split joinery missing: {', '.join(missing_join_parts)}")

    # Backing plates are modeled in assembled coordinates. They should contact
    # their mating surfaces without occupying the printed quadrants/halves.
    joinery_groups = (
        ("body_seam_plate_", "body_shell_q_"),
        ("bumper_seam_plate_", "bumper_q_"),
        ("base_seam_plate", "base_tray_half_"),
    )
    for plate_prefix, target_prefix in joinery_groups:
        for plate_name, plate_shape in split.items():
            if not plate_name.startswith(plate_prefix):
                continue
            for target_name, target_shape in split.items():
                if not target_name.startswith(target_prefix):
                    continue
                volume = intersection_volume(plate_shape, target_shape)
                if volume > 0.05:
                    failures.append(
                        f"split joinery collision: {plate_name} vs {target_name} ({volume:.2f} mm^3)"
                    )

    # The backing plates now self-register with concealed cylindrical pilots.
    # Every pilot must be fused to its plate, occupy material in the unsplit
    # source, and clear both half-round recesses after the source is split.
    pilot_interfaces = alignment_pilot_interfaces(p)
    pilot_count = sum(len(interface["points"]) for interface in pilot_interfaces)
    if pilot_count != 18:
        failures.append(f"alignment pilot inventory changed: expected 18, found {pilot_count}")
    if p.split_pilot_radial_clearance < 0.2:
        failures.append("alignment pilot radial clearance is below the 0.2 mm print baseline")
    if p.split_pilot_axial_clearance < 0.2:
        failures.append("alignment pilot axial clearance is below the 0.2 mm print baseline")
    if not 0.0 < p.split_pilot_overlap < p.split_pilot_length:
        failures.append("alignment pilot overlap must retain each pilot without burying it")
    recess_depth = (
        p.split_pilot_length
        + p.split_pilot_axial_clearance
        - p.split_pilot_overlap
    )
    if p.wall - recess_depth < 1.0:
        failures.append(
            "body-shell alignment recess leaves less than 1.0 mm of exterior wall"
        )

    pilot_source_names = {
        "body": "body_shell",
        "base": "base_tray",
        "bumper": "bumper_carrier",
    }
    for interface in pilot_interfaces:
        plate_name = interface["plate"]
        if plate_name not in split:
            failures.append(f"alignment pilot plate missing: {plate_name}")
            continue
        missing_targets = [name for name in interface["targets"] if name not in split]
        if missing_targets:
            failures.append(
                f"alignment pilot targets missing for {plate_name}: {', '.join(missing_targets)}"
            )
            continue
        source_shape = main[pilot_source_names[interface["group"]]]
        for index, point in enumerate(interface["points"], start=1):
            pilot = alignment_pilot_shape(p, interface, point)
            pilot_volume = float(pilot.volume)
            fused_volume = intersection_volume(pilot, split[plate_name])
            if pilot_volume - fused_volume > 0.05:
                failures.append(
                    f"alignment pilot {plate_name}:{index} is not fully fused to its plate "
                    f"({fused_volume:.2f}/{pilot_volume:.2f} mm^3)"
                )
            if intersection_volume(pilot, source_shape) <= 0.05:
                failures.append(
                    f"alignment pilot {plate_name}:{index} misses its unsplit source surface"
                )
            recess = alignment_pilot_shape(p, interface, point, recess=True)
            for target_name in interface["targets"]:
                volume = intersection_volume(recess, split[target_name])
                if volume > 0.05:
                    failures.append(
                        f"blocked alignment recess {plate_name}:{index} vs {target_name} "
                        f"({volume:.2f} mm^3)"
                    )

    shell_seam_z = p.body_bottom + 18.0
    for side, sign in (("left", -1), ("right", 1)):
        for x in (-18.0, 18.0):
            x_half = "front" if x < 0 else "rear"
            for dz in (-7.0, 7.0):
                probe = cylinder_y(
                    p.m3_clearance_hole / 2.0 - 0.1,
                    32.0,
                    (x, sign * (p.body_width / 2.0 - 2.0), shell_seam_z + dz),
                )
                target_names = (
                    f"body_shell_q_{x_half}_{side}",
                    f"side_fairing_{side}_{x_half}",
                    f"body_seam_plate_side_{side}",
                )
                for target_name in target_names:
                    volume = intersection_volume(probe, split[target_name])
                    if volume > 0.05:
                        failures.append(
                            f"blocked shared shell/fairing seam screw on {side} at "
                            f"X={x:.0f}, Z={shell_seam_z + dz:.0f}: "
                            f"{target_name} ({volume:.2f} mm^3)"
                        )

    # The lid's stepped lap and the captured reveal halves must reconstruct
    # their unsplit source exactly, with no overlap or missing material.
    reconstruction_groups = {
        "top_lid": ("top_lid_half_front", "top_lid_half_rear"),
        "lid_reveal": ("lid_reveal_half_front", "lid_reveal_half_rear"),
    }
    for main_name, (part_a, part_b) in reconstruction_groups.items():
        overlap = intersection_volume(split[part_a], split[part_b])
        if overlap > 0.05:
            failures.append(
                f"split reconstruction overlap: {part_a} vs {part_b} ({overlap:.2f} mm^3)"
            )
        reconstructed = split[part_a] + split[part_b]
        missing_volume = float((main[main_name] - reconstructed).volume)
        extra_volume = float((reconstructed - main[main_name]).volume)
        if missing_volume > 0.05 or extra_volume > 0.05:
            failures.append(
                f"split reconstruction mismatch for {main_name}: "
                f"missing={missing_volume:.2f} extra={extra_volume:.2f} mm^3"
            )

    max_span = 0.0
    largest_name = ""
    for name, shape in split.items():
        box = shape.bounding_box()
        span = max(float(box.max.X - box.min.X), float(box.max.Y - box.min.Y))
        if span > max_span:
            max_span = span
            largest_name = name
        if span > max_allowed + 0.01:
            failures.append(f"split part exceeds bed: {name} ({span:.2f} > {max_allowed:.2f} mm)")

    if failures:
        raise SystemExit("CAD validation failed:\n- " + "\n- ".join(failures))

    print(
        "CAD_VALID "
        f"main={len(main)} fit={len(fits)} split={len(split)} "
        f"largest={largest_name}:{max_span:.1f}mm allowed={max_allowed:.1f}mm "
        "fit_collisions=0 printable_part_overlaps=0 mobility_pod_collisions=0 front_idler_collisions=0 "
        f"wheel_collisions=0 wheel_tread={p.wheel_tread_count}x{p.wheel_tread_depth:.1f}mm mobility_ground=ok bumper_chassis_clearance=ok bumper_actuation=ok safety_stack_collisions=0 safety_switch_collisions=0 "
        "head_motion_collisions=0 head_servos=hitec_d85mg pan_bearing=6807_2rs "
        "tilt_pivot=r_ml24_mf84zz_shoulder_screw split_joinery_collisions=0 "
        "component_contracts=ok expression_contracts=ok camera_optics=ok "
        "attachment_paths=ok sensor_sightlines=ok "
        "motor_service_paths=ok rear_motors=pololu_4867_mp carry_paths=ok "
        "battery=bioenno_blf1203ab_fit rear_charge=en2p3m20_charge_only "
        "power_distribution=4x_01550900m_nano2_microfit_covered_serviced "
        "estop_paths=ok physical_mute=pvb3_two_flat_service_clear "
        "rear_service=trrs_uart_clear harness_paths=ok "
        "pico2=official_mount_usb_swd_service "
        f"alignment_pilots={pilot_count} head_panels=ok service_paths=ok"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bed", type=float, default=256.0)
    parser.add_argument("--margin", type=float, default=8.0)
    args = parser.parse_args()
    validate(args.bed, args.margin)


if __name__ == "__main__":
    main()
