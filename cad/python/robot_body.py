"""Parametric, printer-aware body for the Codex house companion.

Coordinate system
-----------------
X runs front (-X) to rear (+X), Y runs left (-Y) to right (+Y), and Z is up.
The dimensions are intentionally a v0 envelope: they are useful for fit checks,
but motor, battery, E-stop, and controller dimensions must be replaced with
measured parts before a safety-critical print is released.

The script is source-first.  Running it exports individual printable modules,
an assembled STEP, and review-only electronics envelopes under cad/exports/.
The electronics envelopes are never included in the printable body exports.
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path

from build123d import (
    Align,
    Axis,
    Box,
    Compound,
    Cone,
    Cylinder,
    Location,
    Plane,
    RectangleRounded,
    export_step,
    export_stl,
    extrude,
    fillet,
)


CAD_DIR = Path(__file__).resolve().parents[1]
EXPORT_DIR = CAD_DIR / "exports"


@dataclass(frozen=True)
class Params:
    # Main body envelope.
    body_length: float = 300.0
    body_width: float = 220.0
    body_bottom: float = 49.0
    body_height: float = 121.0
    body_corner_radius: float = 25.0
    body_edge_radius: float = 12.0
    wall: float = 3.2

    # Printed interfaces.
    tray_thickness: float = 8.0
    lid_thickness: float = 4.0
    lid_length: float = 280.0
    lid_width: float = 196.0
    lid_split_x: float = 35.0
    lid_lap_length: float = 12.0
    vent_inlay_center_x: float = 46.0
    vent_inlay_length: float = 80.0
    vent_inlay_width: float = 62.0
    vent_inlay_thickness: float = 1.6
    vent_inlay_recess_depth: float = 1.4
    vent_inlay_bridge_height: float = 5.0
    vent_inlay_boss_radius: float = 4.6
    vent_inlay_mount_x_positions: tuple[float, float] = (10.0, 82.0)
    vent_inlay_mount_y_offset: float = 27.0
    bumper_length: float = 318.0
    bumper_width: float = 238.0
    bumper_height: float = 28.0
    bumper_body_clearance: float = 1.0
    bumper_outer_corner_radius: float = 28.0

    # Mobility envelope. The rear drivetrain targets Pololu 25D MP 12 V
    # 99:1 encoder gearmotors (#4867), metal brackets (#1569), and 4 mm M3
    # universal hubs (#1997). Front axle hardware remains provisional.
    wheel_radius: float = 43.0
    wheel_thickness: float = 24.0
    wheel_center_z: float = 66.0
    wheel_x_positions: tuple[float, float] = (-92.0, 82.0)
    wheel_clearance: float = 3.0
    wheel_side_inset: float = 4.0
    wheel_tread_count: int = 24
    wheel_tread_width: float = 5.5
    wheel_tread_depth: float = 2.0
    wheel_tread_side_margin: float = 2.0
    minimum_bumper_ground_clearance: float = 6.0
    # The removable side skin is a shallow pair of wheel-arch caps joined by
    # a narrow upper bridge, not a full-height slab over the molded shell.
    side_fairing_length: float = 252.0
    side_fairing_thickness: float = 2.0
    side_fairing_recess_depth: float = 2.2
    side_fairing_perimeter_clearance: float = 0.3
    side_fairing_height: float = 71.0
    side_fairing_center_z: float = 94.5
    side_fairing_bridge_height: float = 12.0
    side_fairing_relief_overlap: float = 4.0
    mobility_pod_shell_height: float = 42.0
    motor_cover_height: float = 42.0
    motor_cover_screw_z_offset: float = 14.0
    motor_face_y: float = 110.0
    motor_body_length: float = 68.45
    motor_gearbox_length: float = 23.0
    motor_can_length: float = 30.8
    motor_encoder_length: float = 14.65
    motor_body_diameter: float = 25.0
    motor_can_diameter: float = 24.4
    motor_shaft_diameter: float = 4.0
    motor_shaft_length: float = 12.5
    motor_shaft_boss_diameter: float = 7.0
    motor_shaft_boss_length: float = 2.5
    motor_face_mount_spacing: float = 17.0
    motor_face_mount_thread: float = 3.0
    motor_face_mount_depth: float = 6.0
    motor_bracket_thickness: float = 1.5
    motor_bracket_base_length: float = 49.0
    motor_bracket_base_width: float = 22.0
    motor_bracket_face_size: float = 25.0
    motor_bracket_center_hole: float = 7.5
    motor_bracket_base_first_hole: float = 7.8
    motor_bracket_base_hole_pitch: float = 6.4
    motor_bracket_spacer_height: float = 3.0
    motor_hub_diameter: float = 19.0
    motor_hub_thickness: float = 5.0
    motor_hub_mount_offset: float = 6.35
    motor_hub_clearance: float = 0.2
    motor_no_load_rpm: float = 79.0
    motor_no_load_current_a: float = 0.10
    motor_stall_current_a: float = 1.8
    motor_stall_torque_kg_cm: float = 11.0
    wheel_core_radius: float = 20.8
    wheel_core_clearance: float = 0.3
    wheel_core_length: float = 30.0
    wheel_core_inboard_flange_radius: float = 22.0
    wheel_core_inboard_flange_thickness: float = 2.0
    wheel_core_rear_hub_cavity_length: float = 17.0
    front_bearing_od: float = 22.0
    front_bearing_id: float = 8.0
    front_bearing_width: float = 7.0
    front_bearing_seat_clearance: float = 0.2
    front_axle_shaft_length: float = 64.5
    front_axle_shaft_diameter: float = 8.0
    # Rotor Clip DSH-8 / DIN 471 external retaining ring. The 8 mm shaft is
    # cut with the manufacturer's 7.54-7.60 x 0.90 mm groove and a 0.60 mm
    # minimum edge margin; the model uses nominal/conservative values.
    front_axle_ring_groove_diameter: float = 7.6
    front_axle_ring_groove_width: float = 0.9
    front_axle_ring_thickness: float = 0.8
    front_axle_ring_envelope_diameter: float = 14.4
    front_axle_ring_edge_margin: float = 0.6
    front_axle_inner_washer_diameter: float = 15.0
    front_axle_inner_washer_width: float = 2.0
    front_axle_inner_spacer_od: float = 12.0
    front_axle_inner_spacer_length: float = 14.0
    front_axle_outer_spacer_od: float = 10.0
    front_axle_outer_spacer_length: float = 19.0
    front_hub_diameter: float = 25.4
    front_hub_length: float = 14.0
    front_hub_mount_circle: float = 19.05
    front_hub_mount_count: int = 6
    front_hub_mount_thread: float = 3.0
    front_hub_cavity_clearance: float = 0.25
    front_axle_spacer_clearance: float = 0.25
    side_tof_center_x: float = -20.0
    side_tof_mount_x: float = -40.0

    # Recessed two-hand carry interface. Two 25 mm webbing loops pass through
    # reinforced slots near the tray sides and are clamped above the tray by
    # deburred metal spreader plates plus M4 through-bolts. The webbing and
    # metal hardware remain purchased parts; the printed tray only locates and
    # protects the interface until a loaded lift test proves it.
    carry_anchor_center_y: float = 81.5
    carry_anchor_slot_x: float = 38.0
    carry_webbing_width: float = 25.0
    carry_slot_width: float = 5.0
    carry_slot_length: float = 28.0
    carry_anchor_plate_length: float = 92.0
    carry_anchor_plate_width: float = 28.0
    carry_anchor_plate_thickness: float = 2.0
    carry_anchor_doubler_height: float = 3.0
    carry_anchor_doubler_overlap: float = 0.4
    carry_stowed_webbing_thickness: float = 1.2
    m4_clearance_hole: float = 4.5

    # Head and expression.
    neck_x: float = -26.0
    neck_bottom: float = 167.5
    neck_height: float = 44.0
    neck_opening_diameter: float = 53.0
    neck_collar_outer_diameter: float = 60.0
    neck_collar_inner_diameter: float = 51.0
    neck_wall: float = 5.5
    neck_bottom_radius: float = 24.0
    neck_waist_radius: float = 15.5
    neck_top_radius: float = 20.0
    neck_waist_height: float = 22.0
    neck_yoke_flange_radius: float = 21.5
    neck_yoke_flange_thickness: float = 4.0
    neck_yoke_mount_radius: float = 18.0
    neck_yoke_insert_depth: float = 4.2
    pan_bearing_id: float = 35.0
    pan_bearing_od: float = 47.0
    pan_bearing_width: float = 7.0
    pan_bearing_center_z: float = 171.0
    pan_bearing_seat_clearance: float = 0.0
    pan_bearing_journal_clearance: float = 0.2
    pan_bearing_carrier_od: float = 52.4
    pan_bearing_shoulder_od: float = 37.5
    pan_bearing_outer_shoulder_bore: float = 45.0
    pan_bearing_retainer_thickness: float = 2.0
    pan_bearing_retainer_mount_radius: float = 13.0
    pan_bearing_key_offset: float = 27.5
    pan_bearing_key_length: float = 4.0
    pan_bearing_key_width: float = 8.0
    neck_visible_base_z: float = 181.0
    neck_waist_z: float = 190.5
    head_center_x: float = -26.0
    head_center_z: float = 242.0
    head_depth: float = 72.0
    head_width: float = 140.0
    head_height: float = 72.0
    head_bezel_depth: float = 9.0
    head_bezel_outer_width: float = 136.0
    head_bezel_outer_height: float = 70.0
    head_bezel_opening_width: float = 122.0
    head_bezel_opening_height: float = 58.0
    head_faceplate_depth: float = 3.0
    head_faceplate_width: float = 120.0
    head_faceplate_height: float = 56.0
    # Concept-matched illuminated apertures. The LED boards remain larger and
    # removable behind these smaller diffusers, so visual tuning does not turn
    # a cosmetic lens into the electronics-retention feature.
    head_eye_aperture_width: float = 13.0
    head_eye_aperture_height: float = 18.0
    head_eye_frame_width: float = 19.0
    head_eye_frame_height: float = 24.0
    head_eye_glow_width: float = 9.0
    head_eye_glow_height: float = 14.0
    head_eye_carrier_width: float = 28.0
    head_eye_carrier_height: float = 30.0
    head_eye_carrier_opening_width: float = 20.0
    head_eye_carrier_opening_height: float = 26.0
    head_eye_carrier_hole_offset: float = 12.0
    head_eye_carrier_mount_gap: float = 0.2
    head_eye_center_z_offset: float = 0.0
    # Adafruit 5975 NeoPixel JST breakout. The board is rotated 90 degrees in
    # each eye so its two side-entry JST-SH connectors exit vertically, clear
    # of the carrier's horizontal M2.5 attachment screws.
    neopixel_board_width: float = 12.192
    neopixel_board_height: float = 11.43
    neopixel_pcb_thickness: float = 1.57
    neopixel_led_front_protrusion: float = 1.4
    neopixel_connector_rear_protrusion: float = 2.96
    neopixel_overall_depth: float = 5.93
    neopixel_mount_hole: float = 2.0
    neopixel_mount_clearance: float = 2.3
    neopixel_mount_center_offset: float = 1.0
    neopixel_mount_spacing: float = 8.636
    neopixel_spacer_od: float = 3.0
    neopixel_carrier_component_clearance: float = 0.3
    neopixel_carrier_depth: float = 3.0
    head_eye_led_board_width: float = 11.43
    head_eye_led_board_height: float = 12.192
    front_status_aperture_width: float = 26.0
    front_status_aperture_height: float = 16.0
    front_status_glow_width: float = 20.0
    front_status_glow_height: float = 10.0
    front_status_carrier_opening_width: float = 28.0
    front_status_carrier_opening_height: float = 18.0
    front_status_led_board_width: float = 12.192
    front_status_led_board_height: float = 11.43
    head_camera_aperture_radius: float = 11.5
    head_lens_outer_radius: float = 19.0
    head_lens_mid_radius: float = 16.5
    head_lens_inner_radius: float = 14.5
    head_lens_clear_radius: float = 13.0
    head_tilt_axis_x: float = -10.0
    head_tilt_axis_z: float = 233.0
    head_tilt_limit_degrees: float = 20.0
    head_tilt_adapter_radius: float = 17.5
    head_tilt_adapter_thickness: float = 3.0
    head_tilt_adapter_mount_radius: float = 9.5
    head_tilt_shell_boss_radius: float = 3.5
    head_tilt_passive_bushing_od: float = 8.0
    head_tilt_passive_bushing_id: float = 4.0
    head_tilt_passive_bushing_length: float = 3.0
    head_tilt_passive_bushing_flange_od: float = 9.2
    head_tilt_passive_bushing_flange_thickness: float = 0.6
    head_tilt_yoke_insert_hole: float = 4.6
    head_tilt_shoulder_length: float = 12.0
    head_tilt_shoulder_thread_length: float = 4.0
    head_tilt_shoulder_head_diameter: float = 6.0
    head_tilt_shoulder_head_height: float = 3.0

    # Hitec D85MG geometry from the manufacturer's v2.2 datasheet and STEP.
    # The same servo is used for pan and tilt to simplify spares and power.
    servo_body_length: float = 29.0
    servo_body_width: float = 13.0
    servo_body_height: float = 30.0
    servo_flange_length: float = 39.8
    servo_flange_thickness: float = 2.0
    servo_mount_spacing: float = 30.8
    servo_mount_hole: float = 4.5
    servo_output_offset: float = 7.8723
    servo_output_diameter: float = 5.76
    servo_output_collar_diameter: float = 11.8
    servo_mount_plane_from_bottom: float = 20.2
    servo_output_stack_height: float = 6.1
    servo_wire_length: float = 250.0
    servo_stall_current_6v: float = 1.4

    # Hitec R-ML24 aluminum single-arm horn. Two M2x0.4 threaded stations at
    # 13 and 16 mm retain each printed drive plate without relying on plastic
    # spline geometry or a friction-only clamp.
    servo_horn_arm_length: float = 22.0
    servo_horn_arm_width: float = 6.0
    servo_horn_arm_thickness: float = 2.5
    servo_horn_hub_diameter: float = 9.0
    servo_horn_overall_thickness: float = 4.3
    servo_horn_threaded_offsets: tuple[float, float] = (13.0, 16.0)
    servo_horn_thread: float = 2.0

    # Conservative printer assumptions.
    min_wall: float = 2.4
    fastener_clearance: float = 0.35
    insert_hole_m3: float = 4.6
    m3_clearance_hole: float = 3.4
    insert_hole_m2_5: float = 3.8
    m2_5_clearance_hole: float = 2.9
    m2_clearance_hole: float = 2.4

    # Hidden alignment pilots used only by the printer-split backing plates.
    # The pilot center lies on the quadrant seam, so each mating half receives
    # a half-round recess and cannot skate independently while screws start.
    split_pilot_radius: float = 2.0
    split_pilot_radial_clearance: float = 0.3
    split_pilot_length: float = 2.0
    split_pilot_overlap: float = 0.4
    split_pilot_axial_clearance: float = 0.4

    # Raspberry Pi 5 mechanical reference envelope. The board footprint and
    # hole inset follow Raspberry Pi's official mechanical drawing; the larger
    # clearance volume still includes cooling, connectors, and cable bend room.
    pi_center_x: float = -65.0
    pi_center_y: float = -35.0
    pi_board_length: float = 85.0
    pi_board_width: float = 56.0
    pi_board_height: float = 4.0
    pi_mount_inset: float = 3.5
    pi_mount_hole_diameter: float = 3.0
    pi_clearance_length: float = 96.0
    pi_clearance_width: float = 68.0
    pi_clearance_height: float = 28.0

    # Raspberry Pi Pico 2 safety-MCU reference from the official mechanical
    # drawing and STEP model RP-009061-CA-2. The non-wireless, no-header board
    # is the baseline: safety traffic is wired, and the shelf preserves USB,
    # SWD, and optional header service volumes rather than relying on radio.
    pico2_board_length: float = 51.0
    pico2_board_width: float = 21.0
    pico2_board_thickness: float = 1.0
    pico2_overall_length: float = 52.3
    pico2_overall_height: float = 3.8
    pico2_mount_spacing_length: float = 48.26
    pico2_mount_spacing_width: float = 17.78
    pico2_mount_hole: float = 2.1
    pico2_mount_clearance: float = 2.4
    pico2_standoff_height: float = 6.0
    pico2_usb_length: float = 6.1
    pico2_usb_width: float = 8.0
    pico2_usb_height: float = 3.5
    pico2_usb_overhang: float = 1.3
    pico2_header_length: float = 46.0
    pico2_header_width: float = 3.0
    pico2_header_height: float = 8.0
    pico2_clearance_length: float = 62.0
    pico2_clearance_width: float = 33.0
    pico2_clearance_height: float = 14.0
    pico2_usb_notch_length: float = 20.0
    pico2_usb_notch_width: float = 10.0

    # Cytron SmartDriveDuo-10 (MDDS10) reference from Cytron's official STEP
    # model. The 101.092 mm axis runs front-to-rear with the six high-current
    # terminals facing robot-front. The STEP's PCB datum has 1.93 mm of pin
    # protrusion below it and 12.275 mm of component height above it.
    mdds10_board_length: float = 101.092
    mdds10_board_width: float = 66.802
    mdds10_board_thickness: float = 1.57
    mdds10_below_pcb: float = 1.93
    mdds10_above_pcb: float = 12.275
    mdds10_mount_spacing_length: float = 95.25
    mdds10_mount_spacing_width: float = 60.96
    mdds10_mount_hole: float = 3.0
    mdds10_mount_clearance: float = 3.4
    mdds10_plate_lift: float = 5.0
    mdds10_standoff_height: float = 6.0
    mdds10_plate_length: float = 124.0
    mdds10_plate_width: float = 74.0
    mdds10_terminal_service_length: float = 24.0
    mdds10_terminal_service_width: float = 44.0
    mdds10_terminal_service_height: float = 16.0
    mdds10_airflow_height: float = 10.0

    # Camera Module 3 Wide reference from Raspberry Pi drawing RP-008155-DS-1.
    # The 25 mm board axis runs across Y and the 23.862 mm axis runs along Z.
    camera_module_length: float = 25.0
    camera_module_width: float = 23.862
    camera_module_height: float = 12.4
    camera_pcb_thickness: float = 1.12
    camera_lens_housing_depth: float = 11.0
    camera_lens_housing_width: float = 10.8
    camera_lens_front_recess: float = 1.0
    camera_carrier_board_offset: float = 3.64
    camera_horizontal_fov_degrees: float = 102.0
    camera_fov_origin_radius: float = 2.5
    camera_mount_hole: float = 2.2
    camera_hole_edge_x: float = 2.0
    camera_hole_rows_from_bottom: tuple[float, float] = (2.0, 14.5)
    camera_lens_from_bottom: float = 14.4

    # BOM reference envelopes for serviceable audio and proximity modules.
    mic_array_diameter: float = 70.0
    mic_array_height: float = 12.0
    mic_array_center_x: float = 40.0
    mic_array_mount_x_offset: float = 20.0
    mic_array_mount_y_offset: float = 40.0
    mic_cradle_outer_margin: float = 3.0
    speaker_length: float = 70.0
    speaker_width: float = 30.0
    speaker_height: float = 17.0
    speaker_mount_length: float = 64.0
    speaker_mount_width: float = 24.0
    speaker_mount_hole: float = 3.1
    # Two Adafruit #3006 MAX98357A mono amplifiers form a documented stereo
    # pair. The official 2022 STEP supplies the exact PCB and two-hole pattern
    # but predates the current pre-soldered terminal block, so its block,
    # screwdriver, wire, and header envelopes remain conservative until one
    # current board is measured.
    audio_amp_pcb_length: float = 17.78
    audio_amp_pcb_width: float = 19.05
    audio_amp_pcb_thickness: float = 1.57
    audio_amp_product_depth: float = 3.0
    audio_amp_mount_hole: float = 2.5
    audio_amp_mount_spacing: float = 12.7
    audio_amp_mount_terminal_edge_offset: float = 6.985
    audio_amp_standoff_height: float = 6.0
    audio_amp_terminal_width: float = 7.0
    audio_amp_terminal_depth: float = 7.0
    audio_amp_terminal_height: float = 10.0
    audio_amp_screwdriver_height: float = 14.0
    audio_amp_speaker_wire_depth: float = 12.0
    audio_amp_header_service_depth: float = 10.0
    tof_board_length: float = 25.5
    tof_board_width: float = 17.5
    tof_board_height: float = 4.6
    # Omron D2HW-C202MR sealed SPST-NC pin-plunger switch. The M3-mount
    # version is rotated onto its narrow side so the bumper loads the plunger
    # normally while the two tapped mounting holes remain vertical.
    bumper_switch_length: float = 18.5
    bumper_switch_case_length: float = 13.3
    bumper_switch_width: float = 5.3
    bumper_switch_height: float = 6.5
    bumper_switch_mount_spacing: float = 13.0
    bumper_switch_mount_hole: float = 3.3
    bumper_switch_mount_head_diameter: float = 6.0
    bumper_switch_mount_head_recess: float = 1.8
    bumper_switch_plunger_diameter: float = 1.7
    bumper_switch_free_position: float = 7.2
    bumper_switch_operating_position: float = 6.4
    bumper_switch_operating_tolerance: float = 0.2
    bumper_switch_total_travel_position: float = 5.1
    bumper_switch_operating_force: float = 0.75
    bumper_switch_wire_length: float = 300.0
    bumper_switch_wire_service_length: float = 5.0
    bumper_switch_wire_service_width: float = 5.0
    bumper_switch_wire_service_height: float = 5.0
    bumper_switch_plate_radial: float = 22.0
    bumper_switch_plate_tangential: float = 40.0
    bumper_switch_plate_thickness: float = 4.0
    bumper_switch_recess_clearance: float = 0.6
    bumper_switch_nominal_gap: float = 0.4
    bumper_switch_actuation_travel: float = 2.0
    bumper_switch_stop_travel: float = 2.4
    bumper_switch_stop_width: float = 4.0
    bumper_switch_stop_length: float = 5.0
    bumper_switch_stop_offset: float = 17.0
    bumper_switch_tray_pocket_clearance: float = 0.8
    bumper_switch_tray_insert_depth: float = 6.0

    # IDEC XW1E-BV402M-R two-NC direct-opening E-stop. The purchased switch
    # clamps only through the removable 4 mm mount panel; the surrounding lid,
    # shell, and backing plate use a larger service opening and do not consume
    # the manufacturer's 0.8-6 mm allowable panel stack.
    estop_center_x: float = 112.0
    estop_panel_hole: float = 22.5
    estop_keyed_width: float = 24.1
    estop_key_notch_width: float = 3.2
    estop_key_corner_radius: float = 0.8
    estop_panel_thickness_min: float = 0.8
    estop_panel_thickness_max: float = 6.0
    estop_mount_panel_thickness: float = 4.0
    estop_mount_panel_outer_radius: float = 33.0
    estop_mount_panel_visible_radius: float = 30.5
    estop_mount_panel_recess_depth: float = 2.0
    estop_mount_panel_insert_depth: float = 3.4
    estop_body_pass_diameter: float = 40.0
    estop_body_width: float = 37.0
    estop_body_depth: float = 48.7
    estop_operator_height: float = 32.0
    estop_operator_diameter: float = 40.0
    estop_gasket_thickness: float = 0.5
    estop_terminal_service_depth: float = 20.0
    estop_terminal_service_width: float = 40.0
    estop_legend_outer_diameter: float = 60.0
    estop_legend_thickness: float = 0.5
    estop_backing_drop: float = 11.5
    estop_backing_plate_thickness: float = 4.0
    estop_backing_outer_radius: float = 33.0
    estop_backing_collar_outer_radius: float = 23.0
    estop_mount_radius: float = 28.0
    estop_mount_boss_radius: float = 4.5
    estop_insert_depth: float = 6.0

    # Interior layout reference points. The selected prototype battery is the
    # Bioenno BLF-1203AB rotated flat: its official 110 x 27 x 75 mm PVC pack
    # becomes 110 x 75 x 27 mm in the cradle. The separate Powerpole discharge
    # and 5.5 x 2.1 mm charge leads exit toward robot-rear through a conservative
    # service corridor; delivered lead geometry still requires measurement.
    battery_center_x: float = 60.9
    battery_center_y: float = 0.0
    battery_max_length: float = 110.0
    battery_max_width: float = 75.0
    battery_max_height: float = 27.0
    battery_cradle_length: float = 117.0
    battery_cradle_width: float = 92.0
    battery_side_clearance: float = 0.6
    battery_end_clearance: float = 0.5
    battery_rail_thickness: float = 5.0
    battery_rail_height: float = 14.0
    battery_end_stop_thickness: float = 3.0
    battery_end_stop_width: float = 64.0
    battery_strap_offset: float = 20.0
    battery_strap_width: float = 20.0
    battery_pad_offset_x: float = 45.0
    battery_pad_offset_y: float = 25.0
    battery_lead_service_length: float = 28.0
    battery_lead_service_width: float = 54.0
    battery_lead_service_height: float = 14.0
    controller_center_x: float = -65.0
    controller_center_y: float = 33.5
    safety_center_x: float = -65.0
    safety_center_y: float = 33.5
    safety_mount_z: float = 90.0

    # Upper power/signal deck. Purchased modules replace these conservative
    # envelopes; the deck reserves serviceable volume without freezing brands.
    power_deck_center_x: float = 65.0
    power_deck_z: float = 104.0
    power_deck_length: float = 145.0
    power_deck_width: float = 116.0
    rear_service_panel_z: float = 140.0
    rear_service_cartridge_width: float = 30.0
    rear_service_cartridge_height: float = 30.0
    rear_service_cartridge_tongue_width: float = 26.0
    rear_service_cartridge_tongue_height: float = 18.0
    rear_service_cartridge_clearance: float = 0.3
    rear_service_cartridge_cap_thickness: float = 1.25
    rear_service_cartridge_tongue_depth: float = 1.85
    rear_service_cartridge_mount_z_offset: float = 13.0
    rear_service_cartridge_center_spacing: float = 34.0

    # E-Switch PVB3F230SS311 maintained SPDT mute control. The center rear
    # cartridge clamps the purchased switch through the drawing's 16 mm
    # two-flat cutout; the red ring and solder-lug harness remain removable
    # with that one cartridge.
    mute_switch_cutout_diameter: float = 16.0
    mute_switch_cutout_flat_width: float = 14.6
    mute_switch_cutout_clearance: float = 0.2
    mute_switch_bezel_diameter: float = 18.0
    mute_switch_bezel_depth: float = 2.6
    mute_switch_actuator_diameter: float = 11.2
    mute_switch_actuator_depth: float = 1.5
    mute_switch_led_ring_diameter: float = 12.8
    mute_switch_body_depth: float = 26.0
    mute_switch_terminal_service_depth: float = 16.0
    mute_switch_terminal_service_width: float = 20.0
    mute_switch_terminal_service_height: float = 20.0
    mute_switch_panel_min: float = 1.0
    mute_switch_panel_max: float = 7.0
    mute_switch_led_forward_voltage: float = 1.8
    mute_switch_led_current_ma: float = 20.0

    # Switchcraft 35RASMT5CHNTRX four-conductor 3.5 mm service jack on a small
    # horizontal custom PCB. This is a protected 3.3 V UART/service interface,
    # not an audio jack and never a motor-enable or raw-power connector. The
    # shallow right-angle package clears the center cartridge's E-stop keepout.
    service_jack_body_length: float = 15.5
    service_jack_body_width: float = 6.8
    service_jack_body_height: float = 5.3
    service_jack_port_width: float = 7.2
    service_jack_port_height: float = 5.8
    service_jack_port_z_offset: float = 0.75
    service_jack_pcb_length: float = 18.0
    service_jack_pcb_width: float = 18.0
    service_jack_pcb_thickness: float = 1.6
    service_jack_pcb_center_x: float = 141.9
    service_jack_pcb_bottom_z: float = 136.5
    service_jack_pcb_mount_x: float = 139.0
    service_jack_pcb_mount_y_offset: float = 7.0
    service_jack_pcb_mount_hole: float = 2.2
    service_jack_carrier_mount_z_offset: float = 7.5
    service_jack_carrier_mount_hole: float = 2.4
    service_jack_carrier_insert_depth: float = 5.0
    service_jack_carrier_flange_depth: float = 3.0
    service_jack_carrier_flange_width: float = 24.0
    service_jack_carrier_flange_height: float = 24.0
    service_jack_carrier_shelf_length: float = 21.0
    service_jack_carrier_shelf_width: float = 24.0
    service_jack_carrier_shelf_thickness: float = 3.0
    service_jack_wire_service_length: float = 4.0
    service_jack_wire_service_width: float = 20.0
    service_jack_wire_service_height: float = 6.0

    # Switchcraft EN2P3M20 3-position sealed charge-only inlet. Two 6.5 A
    # contacts carry the Bioenno charger's 14.6 V/2 A output through a dedicated
    # adapter cable; the third is CHARGER_PRESENT. The battery's Powerpole
    # discharge connector remains internal and electrically separate.
    charge_jack_cutout_diameter: float = 10.92
    charge_jack_cutout_clearance: float = 0.2
    charge_jack_rear_clearance_diameter: float = 18.6
    charge_jack_body_diameter: float = 14.94
    charge_jack_body_depth: float = 15.75
    charge_jack_overall_depth: float = 20.07
    charge_jack_bezel_diameter: float = 15.75
    charge_jack_front_depth: float = 5.13
    charge_jack_terminal_service_depth: float = 12.0
    charge_jack_terminal_service_width: float = 18.2
    charge_jack_terminal_service_height: float = 18.2
    charge_jack_plug_diameter: float = 13.5
    charge_jack_plug_service_length: float = 39.9

    # Drawing-backed upper-deck regulators. The D24V90F5 supplies the Pi's
    # dedicated 5 V rail; the D36V50F6 supplies the separate 6 V head-servo
    # rail. Both mount on metal M2 standoffs and retain conservative wire,
    # airflow, and finger-service corridors around their exact board patterns.
    pi_regulator_center_x: float = 15.0
    pi_regulator_center_y: float = 0.0
    pi_regulator_length: float = 40.6
    pi_regulator_width: float = 20.3
    pi_regulator_height: float = 7.6
    pi_regulator_mount_spacing_x: float = 35.56
    pi_regulator_mount_spacing_y: float = 15.24
    pi_regulator_mount_hole: float = 2.18
    pi_regulator_standoff_height: float = 6.0
    pi_regulator_terminal_service_length: float = 10.0
    pi_regulator_terminal_service_width: float = 16.0
    pi_regulator_terminal_service_height: float = 12.0
    servo_regulator_center_x: float = 100.0
    servo_regulator_center_y: float = 35.0
    servo_regulator_length: float = 25.4
    servo_regulator_width: float = 25.4
    servo_regulator_height: float = 9.5
    servo_regulator_mount_offset: float = 10.55
    servo_regulator_mount_hole: float = 2.18
    servo_regulator_standoff_height: float = 6.0
    servo_regulator_wire_service_length: float = 14.0
    servo_regulator_wire_service_width: float = 22.0
    servo_regulator_wire_service_height: float = 12.0
    motor_cutoff_center_x: float = 52.5
    motor_cutoff_center_y: float = 0.0
    motor_cutoff_body_length: float = 63.0
    motor_cutoff_body_width: float = 37.0
    motor_cutoff_body_height: float = 28.0
    motor_cutoff_terminal_overall_length: float = 81.0
    motor_cutoff_service_length: float = 90.0
    motor_cutoff_service_width: float = 45.0
    motor_cutoff_service_height: float = 35.0
    motor_cutoff_metal_plate_length: float = 50.0
    motor_cutoff_metal_plate_width: float = 90.0
    motor_cutoff_metal_plate_thickness: float = 2.0
    motor_cutoff_plate_mount_spacing_x: float = 40.0
    motor_cutoff_plate_mount_spacing_y: float = 80.0
    motor_cutoff_plate_mount_hole: float = 3.4

    # Compact four-branch accessory distribution PCB. Four Littelfuse
    # 01550900M OMNI-BLOK holders accept replaceable Nano2 fuses; a Molex
    # 43045-1000 right-angle 10-circuit Micro-Fit header mates with a latched
    # 43025-1000 harness. Exact fuse values remain load-test selections. The
    # board is mechanically capped at 6 A total / 5 A per branch pending a
    # reviewed 2 oz-copper layout, trace-temperature analysis, and fault tests.
    power_distribution_center_x: float = 100.0
    power_distribution_center_y: float = -35.0
    power_distribution_board_length: float = 40.0
    power_distribution_board_width: float = 21.0
    power_distribution_board_thickness: float = 1.6
    power_distribution_lower_standoff_height: float = 4.0
    power_distribution_upper_standoff_height: float = 3.0
    power_distribution_mount_hole: float = 2.2
    power_distribution_holder_length: float = 9.73
    power_distribution_holder_width: float = 5.03
    power_distribution_holder_height: float = 3.81
    power_distribution_fuse_length: float = 6.10
    power_distribution_fuse_width: float = 2.69
    power_distribution_fuse_height: float = 2.69
    power_distribution_header_width: float = 18.65
    power_distribution_header_depth: float = 12.24
    power_distribution_header_height: float = 9.91
    power_distribution_receptacle_width: float = 15.85
    power_distribution_receptacle_depth: float = 17.56
    power_distribution_receptacle_height: float = 10.81
    power_distribution_cover_length: float = 44.0
    power_distribution_cover_width: float = 24.0
    power_distribution_cover_height: float = 11.4
    power_distribution_cover_wall: float = 1.2
    power_distribution_cover_top: float = 1.6
    power_distribution_total_limit_a: float = 6.0
    power_distribution_branch_limit_a: float = 5.0
    power_distribution_holder_rating_a: float = 10.0
    power_distribution_connector_limit_a: float = 7.0
    power_distribution_fuse_service_height: float = 35.0
    power_distribution_harness_straight_length: float = 5.0
    power_distribution_harness_bend_length: float = 22.0
    power_distribution_harness_bend_width: float = 12.0

    # Removable under-deck harness rails. The left rail is reserved for
    # signal/audio/sensor wiring and the right rail for fused switched power
    # and motor wiring. Paired slots accept reusable straps through both the
    # deck and rail so the deck can lift as one serviced harness assembly.
    power_harness_center_y: float = 48.0
    power_harness_rail_length: float = 108.0
    power_harness_rail_width: float = 14.0
    power_harness_base_thickness: float = 4.0
    power_harness_lip_thickness: float = 3.0
    power_harness_lip_height: float = 6.0
    power_harness_channel_width: float = 7.6
    power_harness_channel_height: float = 5.0
    power_harness_deck_gap: float = 0.2


def moved(shape, xyz: tuple[float, float, float]):
    return shape.moved(Location(xyz))


def rounded_box(
    length: float,
    width: float,
    height: float,
    radius: float,
    xyz: tuple[float, float, float] = (0.0, 0.0, 0.0),
):
    """Centered 3D box with safe all-edge fillets."""
    shape = Box(
        length,
        width,
        height,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    )
    max_radius = min(length, width, height) / 2.0 - 0.15
    if radius > 0 and max_radius > 0:
        shape = fillet(shape.edges(), min(radius, max_radius))
    return moved(shape, xyz)


def rounded_prism_xy(
    length: float,
    width: float,
    height: float,
    radius: float,
    xyz: tuple[float, float, float] = (0.0, 0.0, 0.0),
    edge_radius: float = 0.0,
    top_edge_only: bool = False,
):
    """Rounded rectangle extruded up from z=0, then moved by its center."""
    face = Plane.XY * RectangleRounded(length, width, radius)
    shape = extrude(face, amount=height)
    if edge_radius > 0:
        max_radius = min(height, length, width) / 2.0 - 0.15
        edges = shape.edges()
        if top_edge_only:
            edges = [edge for edge in edges if abs(float(edge.center().Z) - height) < 0.05]
        shape = fillet(edges, min(edge_radius, max_radius))
    return moved(shape, (xyz[0], xyz[1], xyz[2] - height / 2.0))


def rounded_panel_yz(
    depth: float,
    width: float,
    height: float,
    radius: float,
    xyz: tuple[float, float, float],
):
    """Rounded rectangle panel normal to X, centered at xyz."""
    face = Plane.YZ * RectangleRounded(width, height, radius)
    shape = extrude(face, amount=depth)
    return moved(shape, (xyz[0] - depth / 2.0, xyz[1], xyz[2]))


def rounded_panel_xz(
    depth: float,
    length: float,
    height: float,
    radius: float,
    xyz: tuple[float, float, float],
):
    """Rounded rectangle panel normal to Y, centered at xyz."""
    face = Plane.XZ * RectangleRounded(length, height, radius)
    shape = extrude(face, amount=depth)
    return moved(shape, (xyz[0], xyz[1] + depth / 2.0, xyz[2]))


def cylinder_z(radius: float, height: float, xyz: tuple[float, float, float]):
    return moved(
        Cylinder(radius, height, align=(Align.CENTER, Align.CENTER, Align.CENTER)),
        xyz,
    )


def cylinder_y(radius: float, height: float, xyz: tuple[float, float, float]):
    return moved(
        Cylinder(
            radius,
            height,
            rotation=(90, 0, 0),
            align=(Align.CENTER, Align.CENTER, Align.CENTER),
        ),
        xyz,
    )


def cylinder_x(radius: float, height: float, xyz: tuple[float, float, float]):
    return moved(
        Cylinder(
            radius,
            height,
            rotation=(0, 90, 0),
            align=(Align.CENTER, Align.CENTER, Align.CENTER),
        ),
        xyz,
    )


def lid_mount_positions():
    """Shared lid screw pattern for the lid and shell-side insert bosses."""
    return ((-124.0, -84.0), (-124.0, 84.0), (124.0, -84.0), (124.0, 84.0))


def estop_backing_center_z(p: Params):
    return p.body_bottom + p.body_height - p.estop_backing_drop


def body_inner_roof_z(p: Params):
    """Shared lower surface of the nominal full-thickness shell roof."""
    return p.body_bottom + p.body_height - p.wall


def estop_mount_positions(p: Params):
    """Four removable backing-plate screws around the switch bore."""
    return (
        (p.estop_center_x - p.estop_mount_radius, 0.0),
        (p.estop_center_x + p.estop_mount_radius, 0.0),
        (p.estop_center_x, -p.estop_mount_radius),
        (p.estop_center_x, p.estop_mount_radius),
    )


def estop_mount_panel_bottom_z(p: Params):
    lid_top = p.body_bottom + p.body_height + 3.0 + p.lid_thickness / 2.0
    return lid_top - p.estop_mount_panel_recess_depth


def estop_mount_panel_top_z(p: Params):
    return estop_mount_panel_bottom_z(p) + p.estop_mount_panel_thickness


def estop_keyed_panel_cutout(p: Params, height: float, center_z: float):
    """IDEC XW keyed 22.3 +0.4 mm panel cutout with a 3.2 mm lug notch."""
    cutout = cylinder_z(
        p.estop_panel_hole / 2.0,
        height,
        (p.estop_center_x, 0.0, center_z),
    )
    extension = p.estop_keyed_width - p.estop_panel_hole
    notch = rounded_box(
        extension + 1.0,
        p.estop_key_notch_width,
        height,
        min(p.estop_key_corner_radius, p.estop_key_notch_width / 2.0),
        (
            p.estop_center_x + p.estop_panel_hole / 2.0 + extension / 2.0,
            0.0,
            center_z,
        ),
    )
    return cutout + notch


def estop_body_pass_clearance(p: Params, height: float, center_z: float):
    """Rounded-square clearance for the 37 mm IDEC body and locking ring."""
    return rounded_box(
        p.estop_body_pass_diameter,
        p.estop_body_pass_diameter,
        height,
        4.0,
        (p.estop_center_x, 0.0, center_z),
    )


def fairing_mount_positions():
    """High side-panel screws that remain above both wheel arches."""
    return ((-116.0, 122.0), (-45.0, 122.0), (45.0, 122.0), (116.0, 122.0))


def side_fairing_center_y(p: Params, side_sign: int):
    """Assembled center plane for a flush exterior fairing skin."""
    return side_sign * (p.body_width / 2.0 - p.side_fairing_thickness / 2.0)


def side_fairing_profile(
    p: Params,
    side_sign: int,
    depth: float,
    panel_y: float,
    perimeter_clearance: float = 0.0,
):
    """Shared scalloped fairing profile used by both skin and shell recess."""
    clearance = perimeter_clearance
    arch_radius = p.wheel_radius + 4.0
    panel_bottom = p.side_fairing_center_z - p.side_fairing_height / 2.0
    panel_top = p.side_fairing_center_z + p.side_fairing_height / 2.0
    relief_x_min = (
        p.wheel_x_positions[0] + arch_radius - p.side_fairing_relief_overlap
    )
    relief_x_max = (
        p.wheel_x_positions[1] - arch_radius + p.side_fairing_relief_overlap
    )
    relief_bottom = panel_bottom - 4.0
    relief_top = panel_top - p.side_fairing_bridge_height
    relief_center_x = (relief_x_min + relief_x_max) / 2.0
    relief_center_z = (relief_bottom + relief_top) / 2.0
    panel = rounded_panel_xz(
        depth,
        p.side_fairing_length + 2.0 * clearance,
        p.side_fairing_height + 2.0 * clearance,
        18.0 + clearance,
        (0.0, panel_y, p.side_fairing_center_z),
    )
    for wheel_x in p.wheel_x_positions:
        panel = panel - cylinder_y(
            max(arch_radius - clearance, 1.0),
            depth + 10.0,
            (wheel_x, panel_y, p.wheel_center_z),
        )
    panel = panel - rounded_panel_xz(
        depth + 8.0,
        max(relief_x_max - relief_x_min - 2.0 * clearance, 1.0),
        max(relief_top - relief_bottom - 2.0 * clearance, 1.0),
        max(8.0 - clearance, 1.0),
        (relief_center_x, panel_y, relief_center_z),
    )
    return panel


def power_deck_mount_positions(p: Params):
    return (
        (p.power_deck_center_x - 60.0, -53.0),
        (p.power_deck_center_x - 60.0, 53.0),
        (p.power_deck_center_x + 65.0, -53.0),
        (p.power_deck_center_x + 65.0, 53.0),
    )


def pi_regulator_mount_positions(p: Params):
    """Four M2 stations from Pololu's D24V90F5 1.4 x 0.6 inch pattern."""
    return tuple(
        (
            p.pi_regulator_center_x + x_sign * p.pi_regulator_mount_spacing_y / 2.0,
            p.pi_regulator_center_y + y_sign * p.pi_regulator_mount_spacing_x / 2.0,
        )
        for x_sign in (-1.0, 1.0)
        for y_sign in (-1.0, 1.0)
    )


def servo_regulator_mount_positions(p: Params):
    """Three M2 stations from Pololu's triangular D36V50Fx drill pattern."""
    offset = p.servo_regulator_mount_offset
    return (
        (p.servo_regulator_center_x + offset, p.servo_regulator_center_y - offset),
        (p.servo_regulator_center_x + offset, p.servo_regulator_center_y + offset),
        (p.servo_regulator_center_x - offset, p.servo_regulator_center_y + offset),
    )


def motor_cutoff_plate_mount_positions(p: Params):
    """Four M3 paths through the printed deck into a metal SW60 carrier."""
    return tuple(
        (
            p.motor_cutoff_center_x + x_sign * p.motor_cutoff_plate_mount_spacing_x / 2.0,
            p.motor_cutoff_center_y + y_sign * p.motor_cutoff_plate_mount_spacing_y / 2.0,
        )
        for x_sign in (-1.0, 1.0)
        for y_sign in (-1.0, 1.0)
    )


def power_distribution_board_mount_positions(p: Params):
    """Four M2 stack points clear of the fuse holders and Micro-Fit header."""
    return tuple(
        (p.power_distribution_center_x + dx, p.power_distribution_center_y + dy)
        for dx in (-17.5, 4.5)
        for dy in (-8.5, 8.5)
    )


def power_distribution_holder_positions(p: Params):
    """Four closely packed OMNI-BLOK centers, source side to connector side."""
    return tuple(
        (
            p.power_distribution_center_x - 5.0,
            p.power_distribution_center_y + offset_y,
        )
        for offset_y in (-7.65, -2.55, 2.55, 7.65)
    )


def power_distribution_strain_slots(p: Params):
    """Paired deck slots for a clamp immediately after the Micro-Fit bend."""
    return (
        (128.0, -52.0),
        (136.0, -52.0),
    )


def power_harness_strap_slots(p: Params, side_sign: int):
    """Four paired reusable-strap stations shared by deck and harness rail."""
    station_x = tuple(
        p.power_deck_center_x + offset
        for offset in (-45.0, -15.0, 15.0, 45.0)
    )
    return tuple(
        (x, side_sign * y)
        for x in station_x
        for y in (
            p.power_harness_center_y - 4.0,
            p.power_harness_center_y + 4.0,
        )
    )


def battery_cradle_mount_positions(p: Params):
    return tuple(
        (p.battery_center_x + dx, p.battery_center_y + dy)
        for dx in (-48.0, 48.0)
        for dy in (-50.0, 50.0)
    )


def wheel_ground_z(p: Params):
    return p.wheel_center_z - p.wheel_radius


def wheel_center_y(p: Params, side_sign: int):
    """Tuck each tire partly into its shell arch while clearing the tray/pod."""
    return side_sign * (
        p.body_width / 2.0
        + p.wheel_thickness / 2.0
        - p.wheel_side_inset
    )


def wheel_tread_keepout(p: Params, wheel_x: float, wheel_y: float):
    """Twenty-four shallow transverse grooves inside the tire sidewalls."""
    cut_height = p.wheel_tread_depth + 0.8
    base = rounded_box(
        p.wheel_tread_width,
        p.wheel_thickness - 2.0 * p.wheel_tread_side_margin,
        cut_height,
        0.6,
        (
            wheel_x,
            wheel_y,
            p.wheel_center_z
            + p.wheel_radius
            - p.wheel_tread_depth / 2.0
            + 0.4,
        ),
    )
    axis = Axis((wheel_x, wheel_y, p.wheel_center_z), (0.0, 1.0, 0.0))
    step = 360.0 / p.wheel_tread_count
    return Compound(
        [base.rotate(axis, step / 2.0 + index * step) for index in range(p.wheel_tread_count)]
    )


def bumper_center_z(p: Params):
    return (
        wheel_ground_z(p)
        + p.minimum_bumper_ground_clearance
        + p.bumper_height / 2.0
    )


def bumper_bottom_z(p: Params):
    return bumper_center_z(p) - p.bumper_height / 2.0


def bumper_inner_length(p: Params):
    return p.body_length + 2.0 * p.bumper_body_clearance


def bumper_inner_width(p: Params):
    return p.body_width + 2.0 * p.bumper_body_clearance


def mobility_pod_shell_center_z(p: Params):
    """Center pod shells above the four tray pads while axles sit lower."""
    mobility_pad_top = p.body_bottom + 4.0
    return mobility_pad_top + p.mobility_pod_shell_height / 2.0


def carry_anchor_slot_positions(p: Params, side_sign: int):
    """Webbing pass-through slots for one recessed side carry loop."""
    return tuple(
        (x, side_sign * p.carry_anchor_center_y)
        for x in (-p.carry_anchor_slot_x, p.carry_anchor_slot_x)
    )


def carry_anchor_fastener_positions(p: Params, side_sign: int):
    """Four M4 through-bolts clamping each metal load-spreader plate."""
    return tuple(
        (x, side_sign * p.carry_anchor_center_y + y_offset)
        for x in (-26.0, 26.0)
        for y_offset in (-8.0, 8.0)
    )


def carry_anchor_clamp_plate(p: Params, side_sign: int):
    """Review-only purchased metal clamp plate with open M4 paths."""
    plate_bottom = (
        p.body_bottom
        + p.carry_anchor_doubler_height
        - p.carry_anchor_doubler_overlap
        + 0.2
    )
    plate_z = plate_bottom + p.carry_anchor_plate_thickness / 2.0
    plate = rounded_box(
        p.carry_anchor_plate_length,
        p.carry_anchor_plate_width,
        p.carry_anchor_plate_thickness,
        3.0,
        (0.0, side_sign * p.carry_anchor_center_y, plate_z),
    )
    for x, y in carry_anchor_fastener_positions(p, side_sign):
        plate = plate - cylinder_z(
            p.m4_clearance_hole / 2.0,
            p.carry_anchor_plate_thickness + 4.0,
            (x, y, plate_z),
        )
    return plate


def motor_controller_board_mount_positions(p: Params):
    """Official MDDS10 four-hole pattern after turning terminals toward -X."""
    return tuple(
        (p.controller_center_x + dx, p.controller_center_y + dy)
        for dx in (
            -p.mdds10_mount_spacing_length / 2.0,
            p.mdds10_mount_spacing_length / 2.0,
        )
        for dy in (
            -p.mdds10_mount_spacing_width / 2.0,
            p.mdds10_mount_spacing_width / 2.0,
        )
    )


def motor_pod_mount_positions(p: Params, side_sign: int):
    drive_x = p.wheel_x_positions[1]
    center_y = side_sign * 84.0
    return tuple(
        (drive_x + dx, center_y + dy)
        for dx in (-24.0, 24.0)
        for dy in (-12.0, 12.0)
    )


def motor_pod_service_interface(p: Params, side_sign: int):
    """Inboard service face, cover center, and cover screw locations."""
    drive_x = p.wheel_x_positions[1]
    center_y = side_sign * 84.0
    inner_face_y = center_y - side_sign * 27.0
    cover_center_y = inner_face_y - side_sign * 1.0
    shell_center_z = mobility_pod_shell_center_z(p)
    screw_positions = tuple(
        (drive_x + dx, shell_center_z + dz)
        for dx in (-22.0, 22.0)
        for dz in (-p.motor_cover_screw_z_offset, p.motor_cover_screw_z_offset)
    )
    return inner_face_y, cover_center_y, screw_positions


def drive_motor_face_y(p: Params, side_sign: int):
    return side_sign * p.motor_face_y


def drive_motor_face_mount_positions(p: Params, side_sign: int):
    """Two threaded M3 holes on the official Pololu 25D motor face."""
    face_y = drive_motor_face_y(p, side_sign)
    return tuple(
        (p.wheel_x_positions[1] + dx, face_y, p.wheel_center_z)
        for dx in (-p.motor_face_mount_spacing / 2.0, p.motor_face_mount_spacing / 2.0)
    )


def drive_motor_bracket_tray_positions(p: Params, side_sign: int):
    """Three well-spaced holes from the seven-hole Pololu bracket base row."""
    face_y = drive_motor_face_y(p, side_sign)
    return tuple(
        (
            p.wheel_x_positions[1],
            face_y
            - side_sign
            * (
                p.motor_bracket_base_first_hole
                + index * p.motor_bracket_base_hole_pitch
            ),
        )
        for index in (0, 3, 6)
    )


def drive_motor_hub_mount_positions(p: Params):
    """Four M3 wheel screws in the official Pololu #1997 hub cross pattern."""
    return (
        (p.motor_hub_mount_offset, 0.0),
        (-p.motor_hub_mount_offset, 0.0),
        (0.0, p.motor_hub_mount_offset),
        (0.0, -p.motor_hub_mount_offset),
    )


def front_idler_mount_positions(p: Params, side_sign: int):
    center_x = p.wheel_x_positions[0]
    center_y = side_sign * (p.body_width / 2.0 - 21.0)
    return tuple(
        (center_x + dx, center_y + dy)
        for dx in (-16.0, 16.0)
        for dy in (-11.0, 11.0)
    )


def front_idler_retainer_interfaces(p: Params, side_sign: int):
    """Inner/outer pod faces and their outward directions along the Y axis."""
    center_y = side_sign * (p.body_width / 2.0 - 21.0)
    return tuple(
        (
            face_name,
            center_y + side_sign * face_offset,
            side_sign * (1 if face_offset > 0 else -1),
        )
        for face_name, face_offset in (("inner", -16.0), ("outer", 16.0))
    )


def front_idler_hub_mount_positions(p: Params):
    """Six M3 stations on Pololu #2693's 19.05 mm bolt circle."""
    radius = p.front_hub_mount_circle / 2.0
    return tuple(
        (
            radius * math.cos(
                math.radians(index * 360.0 / p.front_hub_mount_count)
            ),
            radius * math.sin(
                math.radians(index * 360.0 / p.front_hub_mount_count)
            ),
        )
        for index in range(p.front_hub_mount_count)
    )


def front_idler_hardware_names(side: str):
    return (
        f"fit_front_idler_{side}_shaft",
        f"fit_front_idler_{side}_retaining_ring",
        f"fit_front_idler_{side}_inner_washer",
        f"fit_front_idler_{side}_bearing_inner",
        f"fit_front_idler_{side}_bearing_outer",
        f"fit_front_idler_{side}_inner_spacer",
        f"fit_front_idler_{side}_outer_spacer",
        f"fit_front_idler_{side}_hub",
    )


def safety_shelf_standoff_positions(p: Params):
    # The four shelf posts flank the long ends of the MDDS10 rather than
    # piercing its PCB. Their Y positions leave the front terminal fan-out
    # open between the two front posts.
    return (
        (p.controller_center_x - 56.0, p.controller_center_y - 25.0),
        (p.controller_center_x - 56.0, p.controller_center_y + 25.0),
        # Keep the battery-side posts outside both the MDDS10 footprint and
        # the full-width 150 x 75 mm modular battery envelope. They still sit
        # inside the structural shelf with a useful 25 mm fore/aft spread.
        (p.controller_center_x + 56.0, p.controller_center_y + 7.5),
        (p.controller_center_x + 56.0, p.controller_center_y + 32.5),
    )


def motor_controller_plate_mount_positions(p: Params):
    """Four tray-to-controller-plate anchors kept clear of the carry clamps."""
    return tuple(
        (p.controller_center_x + dx, p.controller_center_y + dy)
        for dx in (-56.0, 56.0)
        for dy in (-25.0, 25.0)
    )


def mdds10_board_bottom_z(p: Params):
    """PCB bottom datum above the printed plate and metal standoffs."""
    return motor_controller_plate_top_z(p) + p.mdds10_standoff_height


def motor_controller_plate_bottom_z(p: Params):
    """Elevate the plate over the concealed carry-handle doubler."""
    return p.body_bottom + p.mdds10_plate_lift


def motor_controller_plate_top_z(p: Params):
    return motor_controller_plate_bottom_z(p) + 4.0


def pico2_mount_positions(p: Params):
    """Official Pico 2 four-hole pattern, with USB facing robot-front (-X)."""
    return tuple(
        (p.safety_center_x + dx, p.safety_center_y + dy)
        for dx in (
            -p.pico2_mount_spacing_length / 2.0,
            p.pico2_mount_spacing_length / 2.0,
        )
        for dy in (
            -p.pico2_mount_spacing_width / 2.0,
            p.pico2_mount_spacing_width / 2.0,
        )
    )


def pico2_board_bottom_z(p: Params):
    return p.safety_mount_z + 2.0 + p.pico2_standoff_height


def pico2_usb_center_x(p: Params):
    """USB body center after rotating its official +Y overhang toward -X."""
    return (
        p.safety_center_x
        - p.pico2_board_length / 2.0
        + p.pico2_usb_length / 2.0
        - p.pico2_usb_overhang
    )


def pico2_usb_notch_center_x(p: Params):
    return p.safety_center_x - 48.0 + p.pico2_usb_notch_length / 2.0


def speaker_slot_layout():
    """Two subtle upward-firing grille arrays over the enclosed speakers."""
    return tuple(
        (80.0, side_y + offset)
        for side_y in (-67.0, 67.0)
        for offset in (-8.0, -4.0, 0.0, 4.0, 8.0)
    )


def mic_slot_layout(p: Params):
    """Nine concept-facing slots shared by shell, lid, and vent inlay."""
    return tuple((p.mic_array_center_x, float(y)) for y in range(-20, 21, 5))


def vent_inlay_mount_positions(p: Params):
    """Four high fasteners, two on each side of the printer-split lid seam."""
    return tuple(
        (x, y)
        for x in p.vent_inlay_mount_x_positions
        for y in (-p.vent_inlay_mount_y_offset, p.vent_inlay_mount_y_offset)
    )


def side_vent_layout():
    """High side vents that stay above the nominal wheel-arch circles."""
    return ((-80.0, 127.0), (-80.0, 131.0), (-80.0, 134.0), (70.0, 127.0), (70.0, 131.0), (70.0, 134.0))


def front_tof_y_positions():
    """Two front ToF boards inside the central sensor bar, clear of LEDs."""
    return (("left", -16.5), ("right", 16.5))


def mic_array_mount_positions(p: Params):
    return tuple(
        (
            p.mic_array_center_x + x_sign * p.mic_array_mount_x_offset,
            y_sign * p.mic_array_mount_y_offset,
        )
        for x_sign in (-1.0, 1.0)
        for y_sign in (-1.0, 1.0)
    )


def speaker_shell_mount_positions(side_sign: int):
    return ((38.0, side_sign * 67.0), (122.0, side_sign * 67.0))


def audio_amp_mount_positions(p: Params, side_sign: int):
    """Two M2 stations from Adafruit #3006's official 12.7 mm pattern."""
    center_x = 80.0
    center_y = side_sign * 67.0
    terminal_edge_y = (
        center_y + side_sign * p.audio_amp_mount_terminal_edge_offset
    )
    return tuple(
        (center_x + x_sign * p.audio_amp_mount_spacing / 2.0, terminal_edge_y)
        for x_sign in (-1.0, 1.0)
    )


def cable_strain_relief_mount_positions():
    return ((-20.0, -55.0), (20.0, -55.0))


def front_fascia_mount_positions():
    return tuple(
        (y, z)
        for y in (-50.0, 50.0)
        for z in (83.0, 109.0)
    )


def head_tilt_adapter_center_y(p: Params, side_sign: int):
    """Center an internal adapter between one yoke upright and head sidewall."""
    return side_sign * (p.head_width / 2.0 - 8.5)


def head_tilt_passive_bushing_center_y(p: Params):
    """Seat the MF84ZZ bearing in the moving passive adapter."""
    return head_tilt_adapter_center_y(p, -1)


def head_tilt_yoke_center_y(p: Params):
    """Keep the fixed yoke and servo stack centered inside the head sides."""
    return p.head_width / 2.0 - 16.0


def servo_body_center_x(p: Params, output_x: float):
    """Locate a D85MG case from its drawing-backed offset output spline."""
    return output_x - p.servo_output_offset


def pan_servo_mount_positions(p: Params):
    body_x = servo_body_center_x(p, p.neck_x)
    return tuple(
        (body_x + sign * p.servo_mount_spacing / 2.0, 0.0)
        for sign in (-1.0, 1.0)
    )


def tilt_servo_mount_positions(p: Params):
    body_x = servo_body_center_x(p, p.head_tilt_axis_x)
    return tuple(
        (body_x + sign * p.servo_mount_spacing / 2.0, p.head_tilt_axis_z)
        for sign in (-1.0, 1.0)
    )


def pan_servo_horn_mount_positions(p: Params):
    return tuple(
        (p.neck_x - offset, 0.0)
        for offset in p.servo_horn_threaded_offsets
    )


def pan_bearing_retainer_mount_positions(p: Params):
    return tuple(
        (
            p.neck_x + p.pan_bearing_retainer_mount_radius * math.cos(math.radians(angle)),
            p.pan_bearing_retainer_mount_radius * math.sin(math.radians(angle)),
        )
        for angle in (45.0, 135.0, 225.0, 315.0)
    )


def pan_bearing_key_positions(p: Params):
    return (
        (p.neck_x - p.pan_bearing_key_offset, 0.0),
        (p.neck_x + p.pan_bearing_key_offset, 0.0),
    )


def pan_servo_mount_plane_z(p: Params):
    pan_plate_z = body_inner_roof_z(p) - 12.0
    return pan_plate_z - 2.0 - p.servo_flange_thickness / 2.0


def pan_servo_horn_center_z(p: Params):
    bearing_bottom = p.pan_bearing_center_z - p.pan_bearing_width / 2.0
    retainer_bottom = bearing_bottom - p.pan_bearing_retainer_thickness
    return retainer_bottom - p.servo_horn_overall_thickness / 2.0


def tilt_servo_horn_center_y(p: Params):
    return head_tilt_adapter_center_y(p, 1) - (
        p.head_tilt_adapter_thickness + p.servo_horn_overall_thickness
    ) / 2.0


def tilt_servo_mount_plane_y(p: Params):
    case_top_above_mount = p.servo_body_height - p.servo_mount_plane_from_bottom
    return (
        tilt_servo_horn_center_y(p)
        - p.servo_horn_overall_thickness / 2.0
        - case_top_above_mount
    )


def neck_yoke_mount_positions(p: Params):
    """Four top-flange screws retaining the fixed yoke to the rotating neck."""
    return tuple(
        (
            p.neck_x + p.neck_yoke_mount_radius * math.cos(math.radians(angle)),
            p.neck_yoke_mount_radius * math.sin(math.radians(angle)),
        )
        for angle in (45.0, 135.0, 225.0, 315.0)
    )


def head_tilt_adapter_mount_positions(p: Params):
    """Three M2.5 shell screws around each tilt adapter."""
    return tuple(
        (
            p.head_tilt_axis_x + p.head_tilt_adapter_mount_radius * math.cos(math.radians(angle)),
            p.head_tilt_axis_z + p.head_tilt_adapter_mount_radius * math.sin(math.radians(angle)),
        )
        for angle in (90.0, 210.0, 330.0)
    )


def head_tilt_horn_mount_positions(p: Params):
    """Two M2 holes matching the R-ML24's threaded 13/16 mm stations."""
    return tuple(
        (p.head_tilt_axis_x - offset, p.head_tilt_axis_z)
        for offset in p.servo_horn_threaded_offsets
    )


def front_tof_pod_mount_positions():
    return tuple(
        (side, y + (-17.3 if y < 0 else 17.3), z)
        for side, y in front_tof_y_positions()
        for z in (90.0, 102.0)
    )


def side_tof_pod_mount_positions(p: Params, _side_sign: int):
    return ((p.side_tof_mount_x, 88.0), (p.side_tof_mount_x, 104.0))


def camera_lens_front_x(p: Params):
    head_front_x = p.head_center_x - p.head_depth / 2.0
    face_x = head_front_x - 3.0
    faceplate_front_x = face_x - p.head_faceplate_depth / 2.0
    return faceplate_front_x + p.camera_lens_front_recess


def camera_reference(p: Params):
    """Return PCB center X/Z and carrier X for Camera Module 3 Wide."""
    lens_z = p.head_center_z - 1.0
    board_center_z = lens_z - (p.camera_lens_from_bottom - p.camera_module_width / 2.0)
    pcb_center_x = (
        camera_lens_front_x(p)
        + p.camera_lens_housing_depth
        + p.camera_pcb_thickness / 2.0
    )
    carrier_x = pcb_center_x + p.camera_carrier_board_offset
    return pcb_center_x, board_center_z, carrier_x


def head_lens_stack_positions(p: Params):
    """Return X centers/depths for the fused stepped camera bezel."""
    head_front_x = p.head_center_x - p.head_depth / 2.0
    face_x = head_front_x - 3.0
    faceplate_front_x = face_x - p.head_faceplate_depth / 2.0
    outer_depth = 3.2
    outer_x = faceplate_front_x - outer_depth / 2.0 + 0.1
    mid_depth = 4.0
    mid_x = outer_x - 1.4
    inner_depth = 4.8
    inner_x = mid_x - 1.6
    return outer_x, outer_depth, mid_x, mid_depth, inner_x, inner_depth


def camera_field_of_view_keepout(p: Params):
    """Conservative horizontal-FOV cone from lens face through the bezel."""
    *_prefix, inner_x, inner_depth = head_lens_stack_positions(p)
    bezel_front_x = inner_x - inner_depth / 2.0
    lens_front_x = camera_lens_front_x(p)
    length = lens_front_x - bezel_front_x
    front_radius = p.camera_fov_origin_radius + math.tan(
        math.radians(p.camera_horizontal_fov_degrees / 2.0)
    ) * length
    cone = Cone(
        front_radius,
        p.camera_fov_origin_radius,
        length,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    ).rotate(Axis.Y, 90.0)
    return moved(
        cone,
        ((bezel_front_x + lens_front_x) / 2.0, 0.0, p.head_center_z - 1.0),
    )


def camera_board_hole_offsets(p: Params):
    y_offset = p.camera_module_length / 2.0 - p.camera_hole_edge_x
    return tuple(
        (y, row - p.camera_module_width / 2.0)
        for y in (-y_offset, y_offset)
        for row in p.camera_hole_rows_from_bottom
    )


def head_face_mount_positions(p: Params):
    return tuple(
        (y, z)
        for y in (-52.0, 52.0)
        for z in (p.head_center_z - 20.0, p.head_center_z + 20.0)
    )


def head_rear_mount_positions(p: Params):
    return tuple(
        (y, z)
        for y in (-62.0, 62.0)
        for z in (p.head_center_z - 28.0, p.head_center_z + 28.0)
    )


def camera_module_fit(p: Params):
    """Conservative board plus lens-housing fit based on RP-008155-DS-1."""
    pcb_x, board_z, _carrier_x = camera_reference(p)
    lens_z = p.head_center_z - 1.0
    pcb = rounded_box(
        p.camera_pcb_thickness,
        p.camera_module_length,
        p.camera_module_width,
        0.5,
        (pcb_x, 0.0, board_z),
    )
    lens_depth = p.camera_lens_housing_depth
    lens_rear_x = pcb_x - p.camera_pcb_thickness / 2.0
    lens = rounded_box(
        lens_depth,
        p.camera_lens_housing_width,
        p.camera_lens_housing_width,
        2.0,
        (lens_rear_x - lens_depth / 2.0, 0.0, lens_z),
    )
    return pcb + lens


def body_shell(p: Params):
    """Hollow cream enclosure with open bottom and wheel clearance cuts."""
    outer_center_z = p.body_bottom + p.body_height / 2.0
    outer = rounded_prism_xy(
        p.body_length,
        p.body_width,
        p.body_height,
        p.body_corner_radius,
        (0, 0, outer_center_z),
        edge_radius=p.body_edge_radius,
        top_edge_only=True,
    )

    cavity_height = p.body_height - p.wall + 1.0
    cavity_center_z = p.body_bottom - 1.0 + cavity_height / 2.0
    cavity = rounded_prism_xy(
        p.body_length - 2 * p.wall,
        p.body_width - 2 * p.wall,
        cavity_height,
        max(p.body_corner_radius - p.wall, 1.0),
        (0, 0, cavity_center_z),
        edge_radius=max(p.body_edge_radius - p.wall, 0.0),
        top_edge_only=True,
    )
    shell = outer - cavity

    # The front sensor fascia is a replaceable insert seated into the front
    # wall, rather than a proud decorative bar glued onto the shell.
    sensor_recess = rounded_panel_yz(6, 138, 31, 9, (-p.body_length / 2 + 2.0, 0, 96))
    shell = shell - sensor_recess
    for _side, y, z in front_tof_pod_mount_positions():
        shell = shell - cylinder_x(
            4.4,
            6.0,
            (-p.body_length / 2.0 + 2.0, y, z),
        )
    fascia_inner_x = -p.body_length / 2.0 + 3.0
    for y, z in front_fascia_mount_positions():
        # The same four screws that retain the front LED carriers also clamp
        # the fascia across short shell-rooted spacers. This avoids visible
        # external tabs and keeps the concept's clean black sensor pill.
        carrier_front_x = -145.6
        spacer_length = carrier_front_x - fascia_inner_x
        spacer = cylinder_x(
            6.0,
            spacer_length,
            ((fascia_inner_x + carrier_front_x) / 2.0, y, z),
        )
        shell = shell + spacer
        shell = shell - cylinder_x(
            p.m2_5_clearance_hole / 2.0,
            spacer_length + 4.0,
            ((fascia_inner_x + carrier_front_x) / 2.0, y, z),
        )

    # Continue the top acoustic and E-stop openings through the cream shell;
    # cutting only the removable teal lid would leave a very stylish blockage.
    top_z = p.body_bottom + p.body_height
    for x, y in mic_slot_layout(p):
        shell = shell - rounded_prism_xy(
            36.0,
            3.0,
            14,
            1.2,
            (x, y, top_z),
        )
    for x, y in speaker_slot_layout():
        shell = shell - rounded_prism_xy(28.0, 2.8, 14.0, 1.2, (x, y, top_z))
    shell = shell - estop_body_pass_clearance(p, 20.0, top_z)
    shell = shell - cylinder_z(
        p.neck_opening_diameter / 2.0,
        20.0,
        (p.neck_x, 0.0, top_z),
    )
    for x, y in pan_bearing_key_positions(p):
        shell = shell - rounded_box(
            p.pan_bearing_key_length + 0.5,
            p.pan_bearing_key_width + 0.5,
            20.0,
            1.0,
            (x, y, top_z),
        )
    for x, y in vent_inlay_mount_positions(p):
        shell = shell - cylinder_z(
            p.vent_inlay_boss_radius + 0.35,
            12.0,
            (x, y, top_z - 2.0),
        )

    # Rear drive shafts pass through the side skins into purchased metal hubs.
    for side_sign in (-1, 1):
        for wheel_x, shaft_diameter in (
            (p.wheel_x_positions[0], p.front_bearing_id),
            (p.wheel_x_positions[1], p.motor_shaft_diameter),
        ):
            shell = shell - cylinder_y(
                shaft_diameter / 2.0 + 1.5,
                18.0,
                (wheel_x, side_sign * (p.body_width / 2.0 - 1.0), p.wheel_center_z),
            )

    # The concept wheels are partly nested under the cream body rather than
    # hung entirely outboard. Cut printable side arches around the actual tire
    # envelope so the inset wheels remain removable without rubbing the shell.
    for side_sign in (-1, 1):
        wheel_y = wheel_center_y(p, side_sign)
        for wheel_x in p.wheel_x_positions:
            shell = shell - cylinder_y(
                p.wheel_radius + p.wheel_clearance,
                p.wheel_thickness + 2.0 * (p.wheel_clearance + 1.0),
                (wheel_x, wheel_y, p.wheel_center_z),
            )

    # Seat each removable cream wheel-arch skin into the molded body instead
    # of stacking it outside the concept silhouette. The recess is slightly
    # deeper and wider than the 2 mm fairing, leaving a printable clamp gap
    # and a continuous 1 mm shell membrane behind the non-structural panel.
    for side_sign in (-1, 1):
        recess_y = side_sign * (
            p.body_width / 2.0 - p.side_fairing_recess_depth / 2.0
        )
        shell = shell - side_fairing_profile(
            p,
            side_sign,
            p.side_fairing_recess_depth,
            recess_y,
            perimeter_clearance=p.side_fairing_perimeter_clearance,
        )

    # Four downward bosses receive the removable pan-servo plate. They stay
    # outside the neck opening and keep servo replacement possible through the
    # open base without removing the decorative top lid.
    top_inner_z = body_inner_roof_z(p)

    # Four shell-rooted annular bosses support the removable E-stop panel and
    # backing plate. Long screws pass from the underside backing plate through
    # these bosses into blind inserts in the top panel; the IDEC locking ring
    # clamps only the panel's 4 mm keyed land.
    estop_plate_top = (
        estop_backing_center_z(p) + p.estop_backing_plate_thickness / 2.0
    )
    estop_boss_bottom = estop_plate_top + 0.2
    estop_boss_top = top_inner_z + 0.4
    estop_boss_height = estop_boss_top - estop_boss_bottom
    for x, y in estop_mount_positions(p):
        boss = cylinder_z(
            p.estop_mount_boss_radius,
            estop_boss_height,
            (x, y, (estop_boss_bottom + estop_boss_top) / 2.0),
        )
        shell = shell + boss
        shell = shell - cylinder_z(
            p.m3_clearance_hole / 2.0,
            estop_boss_height + p.wall + 4.0,
            (x, y, (estop_boss_bottom + estop_boss_top) / 2.0),
        )

    # Downward roof bosses turn the audio cradles into removable assemblies.
    # They stop at the printed plates and stay outside the conservative audio
    # hardware envelopes; inserts open from below for service through the base.
    mic_plate_top = 162.5
    mic_boss_height = top_inner_z - mic_plate_top + 0.5
    for x, y in mic_array_mount_positions(p):
        boss = cylinder_z(
            5.0,
            mic_boss_height,
            (x, y, mic_plate_top + mic_boss_height / 2.0),
        )
        shell = shell + boss
        shell = shell - cylinder_z(
            p.insert_hole_m3 / 2.0,
            6.0,
            (x, y, mic_plate_top + 3.0),
        )

    speaker_plate_top = 149.0
    speaker_boss_height = top_inner_z - speaker_plate_top + 0.5
    for sign in (-1, 1):
        for x, y in speaker_shell_mount_positions(sign):
            boss = cylinder_z(
                5.5,
                speaker_boss_height,
                (x, y, speaker_plate_top + speaker_boss_height / 2.0),
            )
            shell = shell + boss
            shell = shell - cylinder_z(
                p.insert_hole_m3 / 2.0,
                8.0,
                (x, y, speaker_plate_top + 4.0),
            )

    for x, y in cable_strain_relief_mount_positions():
        boss = cylinder_z(
            5.0,
            speaker_boss_height,
            (x, y, speaker_plate_top + speaker_boss_height / 2.0),
        )
        shell = shell + boss
        shell = shell - cylinder_z(
            p.insert_hole_m3 / 2.0,
            8.0,
            (x, y, speaker_plate_top + 4.0),
        )

    pan_boss_z = top_inner_z - 4.8
    for dx, dy in ((-24, -24), (-24, 24), (24, -24), (24, 24)):
        x = p.neck_x + dx
        boss = cylinder_z(4.8, 10.4, (x, dy, pan_boss_z))
        shell = shell + boss
        shell = shell - cylinder_z(
            p.insert_hole_m3 / 2.0,
            14.0,
            (x, dy, pan_boss_z),
        )

    # The decorative lid is independently removable. Four roof bosses reach
    # the lid underside, support it across the 1 mm reveal gap, and accept
    # inserts from inside the open-bottom shell.
    lid_boss_bottom = top_z - 10.2
    lid_boss_top = top_z + 1.0
    lid_boss_z = (lid_boss_bottom + lid_boss_top) / 2.0
    for x, y in lid_mount_positions():
        boss = cylinder_z(6.2, lid_boss_top - lid_boss_bottom, (x, y, lid_boss_z))
        shell = shell + boss
        shell = shell - cylinder_z(
            p.insert_hole_m3 / 2.0,
            10.0,
            (x, y, top_z - 6.2),
        )
        shell = shell - cylinder_z(
            p.m3_clearance_hole / 2.0,
            7.0,
            (x, y, top_z - 0.5),
        )

    # Four high side-panel bosses let each fairing half mount independently;
    # this avoids a fragile decorative seam clip between wheel arches.
    side_inner_y = p.body_width / 2.0 - p.wall
    for side_sign in (-1, 1):
        boss_y = side_sign * (side_inner_y - 3.3)
        for x, z in fairing_mount_positions():
            boss = cylinder_y(5.0, 8.0, (x, boss_y, z))
            shell = shell + boss
            shell = shell - cylinder_y(
                p.insert_hole_m3 / 2.0,
                24.0,
                (x, boss_y, z),
            )

    # High side airflow slots provide a real cross-body path for the Pi cooler
    # and power deck while remaining above the nominal wheel openings.
    for side_sign in (-1, 1):
        panel_y = side_sign * (p.body_width / 2.0)
        for x, z in side_vent_layout():
            shell = shell - rounded_panel_xz(
                12.0,
                28.0,
                2.4,
                1.1,
                (x, panel_y, z),
            )

        # Side ToF sensors need a real optical path through the shell and two
        # inward-facing insert bosses for their removable frames.
        shell = shell - rounded_panel_xz(
            14.0,
            20.0,
            14.0,
            4.0,
            (p.side_tof_center_x, panel_y, 96.0),
        )
        pod_outer_y = side_sign * 102.0
        shell_inner_y = side_sign * (p.body_width / 2.0 - p.wall)
        boss_height = abs(shell_inner_y - pod_outer_y) + 0.5
        boss_center_y = side_sign * (abs(pod_outer_y) + boss_height / 2.0)
        for x, z in side_tof_pod_mount_positions(p, side_sign):
            boss = cylinder_y(4.2, boss_height, (x, boss_center_y, z))
            shell = shell + boss
            shell = shell - cylinder_y(
                p.insert_hole_m2_5 / 2.0,
                4.5,
                (x, side_sign * 104.25, z),
            )

    # The reprintable rear frame serves charge/main-power, service/data, and
    # physical mute. The right PVB3 cartridge is selected; the other two bays
    # remain blank until their purchased hardware is measured.
    rear_x = p.body_length / 2.0
    rear_opening = rounded_panel_yz(
        30.0,
        100.0,
        34.0,
        6.0,
        (rear_x, 0.0, p.rear_service_panel_z),
    )
    shell = shell - rear_opening
    for y in (-58.0, 58.0):
        for z in (p.rear_service_panel_z - 22.0, p.rear_service_panel_z + 22.0):
            boss = cylinder_x(5.0, 12.0, (rear_x - 6.0, y, z))
            shell = shell + boss
            shell = shell - cylinder_x(
                p.insert_hole_m3 / 2.0,
                11.0,
                (rear_x - 5.0, y, z),
            )

    # Four heat-set-insert lugs align with clearance holes in the base tray.
    # Short ribs tie each lug into the front/rear shell wall so the bosses are
    # part of the shell rather than unsupported cylinders floating in space.
    mount_z = p.body_bottom + 6.0
    for x, y in [(-124, -84), (-124, 84), (124, -84), (124, 84)]:
        boss = cylinder_z(7.0, 12.0, (x, y, mount_z))
        wall_x = (-1 if x < 0 else 1) * (p.body_length / 2.0 - p.wall)
        rib_length = abs(wall_x - x) + p.wall / 2.0
        rib = rounded_box(
            rib_length,
            12.0,
            12.0,
            2.0,
            ((x + wall_x) / 2.0, y, mount_z),
        )
        shell = shell + boss + rib
        shell = shell - cylinder_z(p.insert_hole_m3 / 2.0, 16.0, (x, y, mount_z))

    return shell


def base_tray(p: Params):
    tray_z = p.body_bottom - p.tray_thickness / 2.0
    tray = rounded_prism_xy(
        p.body_length - 8,
        p.body_width - 8,
        p.tray_thickness,
        16,
        (0, 0, tray_z),
        edge_radius=1.4,
    )

    # Shell screws pass through the tray into heat-set inserts in the shell.
    shell_mount_positions = [
        (-124, -84),
        (-124, 84),
        (124, -84),
        (124, 84),
    ]
    for x, y in shell_mount_positions:
        tray = tray - cylinder_z(p.m3_clearance_hole / 2.0, 16, (x, y, tray_z))

    # Controller-plate standoffs and the battery cradle anchor into explicit
    # tray inserts instead of resting on unreferenced generic holes.
    for x, y in (*motor_controller_plate_mount_positions(p), *battery_cradle_mount_positions(p)):
        tray = tray - cylinder_z(p.insert_hole_m3 / 2.0, 16, (x, y, tray_z))

    # Through-holes for metal standoffs supporting the upper power deck.
    for x, y in power_deck_mount_positions(p):
        tray = tray - cylinder_z(p.m3_clearance_hole / 2.0, 16.0, (x, y, tray_z))

    # Rear pod and drawing-backed metal-bracket patterns. The printed shroud
    # remains removable, while three separate M3 paths per side clamp the
    # Pololu bracket through metal spacers into blind tray inserts.
    for side_sign in (-1, 1):
        for x, y in motor_pod_mount_positions(p, side_sign):
            tray = tray - cylinder_z(p.insert_hole_m3 / 2.0, 16.0, (x, y, tray_z))
        for x, y in drive_motor_bracket_tray_positions(p, side_sign):
            tray = tray - cylinder_z(p.insert_hole_m3 / 2.0, 16.0, (x, y, tray_z))
        for x, y in front_idler_mount_positions(p, side_sign):
            tray = tray - cylinder_z(p.insert_hole_m3 / 2.0, 16.0, (x, y, tray_z))

    # A shallow perimeter lip locates the shell on the tray before any screws
    # are installed. The lip leaves roughly 2.8 mm clearance per side inside
    # the nominal shell cavity for print variation and paint.
    lip_z = p.body_bottom + 2.0
    lip_outer = rounded_prism_xy(
        p.body_length - 12,
        p.body_width - 12,
        4.0,
        14,
        (0, 0, lip_z),
        edge_radius=0.8,
    )
    lip_inner = rounded_prism_xy(
        p.body_length - 20,
        p.body_width - 20,
        8.0,
        10,
        (0, 0, lip_z),
    )
    tray = tray + (lip_outer - lip_inner)

    # Reinforced side zones support two recessed webbing carry loops without
    # adding a visible handle to the concept silhouette. Each metal clamp plate
    # crosses the printer split at X=0 and through-bolts into both tray halves;
    # the raised printed doubler is a locator/load spreader, not the sole lift
    # retention. Slots and bolt paths are cut after all tray unions below.
    carry_doubler_z = (
        p.body_bottom
        + p.carry_anchor_doubler_height / 2.0
        - p.carry_anchor_doubler_overlap
    )
    for side_sign in (-1, 1):
        tray = tray + rounded_prism_xy(
            p.carry_anchor_plate_length + 4.0,
            p.carry_anchor_plate_width + 4.0,
            p.carry_anchor_doubler_height,
            4.0,
            (0.0, side_sign * p.carry_anchor_center_y, carry_doubler_z),
            edge_radius=0.6,
        )

    # Four-point pads bridge each removable mobility pod to the tray. Their
    # tops meet the pod flanges at Z=body_bottom+4 without overlap; the final
    # hole pass below keeps the heat-set-insert paths open after all unions.
    mobility_pad_z = p.body_bottom + 2.0
    for side_sign in (-1, 1):
        for position_fn in (motor_pod_mount_positions, front_idler_mount_positions):
            for x, y in position_fn(p, side_sign):
                boss = cylinder_z(6.0, 4.0, (x, y, mobility_pad_z))
                boss = boss - cylinder_z(
                    p.insert_hole_m3 / 2.0,
                    8.0,
                    (x, y, mobility_pad_z),
                )
                tray = tray + boss

    # Four Pi 5 standoffs. The actual board is 85 x 56 mm with mounting-hole
    # centers inset 3.5 mm from the board edges; use measured hardware before
    # relying on this for a final electronics deck.
    pi_boss_z = p.body_bottom + 3.5
    pi_dx = p.pi_board_length / 2.0 - p.pi_mount_inset
    pi_dy = p.pi_board_width / 2.0 - p.pi_mount_inset
    for dx in (-pi_dx, pi_dx):
        for dy in (-pi_dy, pi_dy):
            x = p.pi_center_x + dx
            y = p.pi_center_y + dy
            boss = cylinder_z(5.0, 7.0, (x, y, pi_boss_z))
            boss = boss - cylinder_z(p.pi_mount_hole_diameter / 2.0, 12.0, (x, y, pi_boss_z))
            tray = tray + boss

    # Re-open motor-pod insert paths after adding the locating lip and other
    # bosses; several positions intentionally pass through that final union.
    for side_sign in (-1, 1):
        for x, y in motor_pod_mount_positions(p, side_sign):
            tray = tray - cylinder_z(p.insert_hole_m3 / 2.0, 30.0, (x, y, tray_z))
        for x, y in drive_motor_bracket_tray_positions(p, side_sign):
            tray = tray - cylinder_z(p.insert_hole_m3 / 2.0, 30.0, (x, y, tray_z))
        for x, y in front_idler_mount_positions(p, side_sign):
            tray = tray - cylinder_z(p.insert_hole_m3 / 2.0, 30.0, (x, y, tray_z))

        # The purchased Pololu bracket crosses the raised shell-locating lip.
        # Plane that local zone back to the structural tray top so the bracket
        # sits on three equal-height metal spacers instead of rocking on a
        # printed ridge. The pocket stops at Z=body_bottom; it is not a cutout
        # through the tray floor.
        face_y = drive_motor_face_y(p, side_sign)
        tray = tray - rounded_box(
            p.motor_bracket_base_width + 0.8,
            p.motor_bracket_base_length + 0.8,
            6.0,
            1.0,
            (
                p.wheel_x_positions[1],
                face_y - side_sign * p.motor_bracket_base_length / 2.0,
                p.body_bottom + 3.0,
            ),
        )

    # Wheel wells continue through the final tray unions. The tire is inset
    # 4 mm into the body envelope, so the tray edge and locating lip need the
    # same real cylindrical relief as the shell and pod shrouds.
    for side_sign in (-1, 1):
        y = wheel_center_y(p, side_sign)
        for wheel_x in p.wheel_x_positions:
            tray = tray - cylinder_y(
                p.wheel_radius + 0.8,
                p.wheel_thickness + 4.0,
                (wheel_x, y, p.wheel_center_z),
            )
    for x, y in (*motor_controller_plate_mount_positions(p), *battery_cradle_mount_positions(p)):
        tray = tray - cylinder_z(p.insert_hole_m3 / 2.0, 30.0, (x, y, tray_z))

    # Re-open the two strap slots and four M4 clamp paths per side after the
    # locating lip and carry doublers have been fused into the tray.
    for side_sign in (-1, 1):
        for x, y in carry_anchor_slot_positions(p, side_sign):
            tray = tray - rounded_prism_xy(
                p.carry_slot_width,
                p.carry_slot_length,
                p.tray_thickness + p.carry_anchor_doubler_height + 8.0,
                min(p.carry_slot_width / 2.0 - 0.2, 2.0),
                (x, y, tray_z + p.carry_anchor_doubler_height / 2.0),
            )
        for x, y in carry_anchor_fastener_positions(p, side_sign):
            tray = tray - cylinder_z(
                p.m4_clearance_hole / 2.0,
                p.tray_thickness + p.carry_anchor_doubler_height + 8.0,
                (x, y, tray_z + p.carry_anchor_doubler_height / 2.0),
            )

    # Six rigid switch plates clamp to blind inserts from below. Their switch
    # bodies pass through local tray pockets while the surrounding TPU bumper
    # remains mechanically independent and free to compress radially.
    tray_bottom = p.body_bottom - p.tray_thickness
    for _name, orientation, x, y in bumper_switch_layout():
        tray = tray - bumper_switch_tray_pocket(p, orientation, x, y)
        for hole_x, hole_y in bumper_switch_mount_positions(orientation, x, y):
            tray = tray - cylinder_z(
                p.insert_hole_m3 / 2.0,
                p.bumper_switch_tray_insert_depth + 0.4,
                (
                    hole_x,
                    hole_y,
                    tray_bottom + p.bumper_switch_tray_insert_depth / 2.0,
                ),
            )

    # The shell's four front/rear wall ribs meet the tray top at Z=49. Notch
    # only the raised locating lip around those ribs so the lip locates the
    # shell without occupying the rib volume.
    lip_z = p.body_bottom + 2.0
    for shell_x, y in ((-124.0, -84.0), (-124.0, 84.0), (124.0, -84.0), (124.0, 84.0)):
        wall_sign = -1 if shell_x < 0 else 1
        tray = tray - rounded_box(
            10.0,
            14.0,
            4.6,
            2.0,
            (wall_sign * 142.0, y, lip_z),
        )

    # The flush outer front-bearing retainers need a removable side service
    # path. Cut a local arch from the tray edge while preserving the four
    # idler mounting pads outside the retainer circle.
    for side_sign in (-1, 1):
        tray = tray - cylinder_y(
            16.2,
            12.0,
            (
                p.wheel_x_positions[0],
                side_sign * (p.body_width / 2.0 - 5.0),
                p.wheel_center_z,
            ),
        )
    return tray


def battery_cradle(p: Params):
    """Removable BLF-1203AB cradle with two wide straps and end stops."""
    center_x = p.battery_center_x
    center_y = p.battery_center_y
    base = rounded_prism_xy(
        p.battery_cradle_length,
        p.battery_cradle_width,
        4,
        10,
        (center_x, center_y, p.body_bottom + 2.0),
        edge_radius=1.0,
    )
    rail_y = p.battery_max_width / 2.0 + p.battery_side_clearance + p.battery_rail_thickness / 2.0
    for y in (-rail_y, rail_y):
        rail = rounded_box(
            p.battery_cradle_length,
            p.battery_rail_thickness,
            p.battery_rail_height,
            2,
            (center_x, center_y + y, p.body_bottom + 10.0),
        )
        base = base + rail
    stop_x = p.battery_max_length / 2.0 + p.battery_end_clearance + p.battery_end_stop_thickness / 2.0
    for x in (center_x - stop_x, center_x + stop_x):
        base = base + rounded_box(
            p.battery_end_stop_thickness,
            p.battery_end_stop_width,
            p.battery_rail_height,
            1.5,
            (x, center_y, p.body_bottom + 10.0),
        )
    for x in (center_x - p.battery_strap_offset, center_x + p.battery_strap_offset):
        strap_slot = rounded_box(
            p.battery_strap_width + 1.0,
            100,
            8,
            2,
            (x, center_y, p.body_bottom + 2.0),
        )
        base = base - strap_slot

    # The cradle reaches the controller plate's near corner, but the selected
    # battery envelope itself still clears the MDDS10 board.
    # Remove only the overlapping printed corner so both floor modules remain
    # independently serviceable instead of silently occupying one another.
    controller_plate_max_x = p.controller_center_x + p.mdds10_plate_length / 2.0
    controller_plate_min_y = p.controller_center_y - p.mdds10_plate_width / 2.0
    notch_min_x = center_x - p.battery_cradle_length / 2.0 - 1.0
    notch_max_x = controller_plate_max_x + 0.5
    notch_min_y = controller_plate_min_y - 0.5
    notch_max_y = center_y + p.battery_cradle_width / 2.0 + 1.0
    if notch_max_x > notch_min_x and notch_max_y > notch_min_y:
        base = base - rounded_box(
            notch_max_x - notch_min_x,
            notch_max_y - notch_min_y,
            12.0,
            1.0,
            (
                (notch_min_x + notch_max_x) / 2.0,
                (notch_min_y + notch_max_y) / 2.0,
                p.body_bottom + 10.0,
            ),
        )

    for x, y in battery_cradle_mount_positions(p):
        ear = rounded_box(12.0, 12.0, 4.0, 2.0, (x, y, p.body_bottom + 2.0))
        base = base + ear
        base = base - cylinder_z(
            p.m3_clearance_hole / 2.0,
            10.0,
            (x, y, p.body_bottom + 2.0),
        )

    # The front pair of continuous metal power-deck standoffs graze the
    # cradle's rounded outer corners. Preserve those independent load paths
    # with explicit service scallops instead of allowing the printed cradle
    # to clamp or preload either standoff.
    for x, y in power_deck_mount_positions(p):
        base = base - cylinder_z(
            3.4,
            20.0,
            (x, y, p.body_bottom + 8.0),
        )

    # Four pads meet the selected pack envelope at Z=50 while leaving the
    # two strap channels unobstructed.
    for x in (
        center_x - p.battery_pad_offset_x,
        center_x + p.battery_pad_offset_x,
    ):
        for y in (
            center_y - p.battery_pad_offset_y,
            center_y + p.battery_pad_offset_y,
        ):
            base = base + cylinder_z(
                6.0,
                7.4,
                (x, y, p.body_bottom + 5.3),
            )
    return base


def audio_mounts(p: Params):
    """Mic-array retaining ring and two enclosed-speaker mounting plates."""
    parts = {}

    mic_center = (p.mic_array_center_x, 0.0, 160.0)
    mic_outer_radius = p.mic_array_diameter / 2.0 + p.mic_cradle_outer_margin
    mic_inner_radius = p.mic_array_diameter / 2.0 + 0.6
    mic = cylinder_z(mic_outer_radius, 5.0, mic_center)
    mic = mic - cylinder_z(mic_inner_radius, 8.0, mic_center)
    for x, y in mic_array_mount_positions(p):
        ear_center = (x, y, mic_center[2])
        mic = mic + rounded_box(12, 12, 5, 2, ear_center)
        mic = mic - cylinder_z(p.m3_clearance_hole / 2.0, 9.0, ear_center)
    parts["mic_array_cradle"] = mic

    speaker_x = 80.0
    speaker_z = 147.0
    for side, sign in (("left", -1), ("right", 1)):
        y = sign * 67.0
        plate = rounded_prism_xy(76, 36, 4, 5, (speaker_x, y, speaker_z), edge_radius=0.8)
        for dx in (-p.speaker_mount_length / 2.0, p.speaker_mount_length / 2.0):
            for dy in (-p.speaker_mount_width / 2.0, p.speaker_mount_width / 2.0):
                plate = plate - cylinder_z(
                    max(p.speaker_mount_hole, p.m3_clearance_hole) / 2.0,
                    10.0,
                    (speaker_x + dx, y + dy, speaker_z),
                )
        for x, mount_y in speaker_shell_mount_positions(sign):
            ear = rounded_box(12.0, 12.0, 4.0, 2.0, (x, mount_y, speaker_z))
            plate = plate + ear
            plate = plate - cylinder_z(
                p.m3_clearance_hole / 2.0,
                10.0,
                (x, mount_y, speaker_z),
            )
        # Mount one current-revision MAX98357A below each speaker plate with
        # its component and terminal side facing downward for service. The
        # header edge points inward toward the signal harness; the speaker
        # terminal edge points outward toward its matching enclosure.
        for x, mount_y in audio_amp_mount_positions(p, sign):
            plate = plate - cylinder_z(
                p.m2_clearance_hole / 2.0,
                10.0,
                (x, mount_y, speaker_z),
            )
        parts[f"speaker_mount_{side}"] = plate
    return parts


def audio_amp_fit_parts(p: Params):
    """Exact #3006 PCB pattern plus provisional current-terminal service volumes.

    Adafruit's official 2022 STEP omits the terminal block that has shipped
    pre-soldered since 2024. The PCB outline, thickness, rounded corners, and
    two 2.5 mm holes are drawing-backed; terminal height and access volumes are
    deliberately conservative until one current board is measured.
    """
    fits = {}
    speaker_plate_bottom = 145.0
    board_top = speaker_plate_bottom - p.audio_amp_standoff_height
    product_center_z = board_top - p.audio_amp_product_depth / 2.0
    terminal_top = board_top - p.audio_amp_pcb_thickness + 0.2
    terminal_bottom = terminal_top - p.audio_amp_terminal_height

    for side, sign in (("left", -1), ("right", 1)):
        center_x = 80.0
        center_y = sign * 67.0
        terminal_y = center_y + sign * (
            p.audio_amp_pcb_width / 2.0 - p.audio_amp_terminal_depth / 2.0
        )
        amp = rounded_box(
            p.audio_amp_pcb_length,
            p.audio_amp_pcb_width,
            p.audio_amp_product_depth,
            2.4,
            (center_x, center_y, product_center_z),
        )
        amp = amp + rounded_box(
            p.audio_amp_terminal_width,
            p.audio_amp_terminal_depth,
            p.audio_amp_terminal_height,
            1.0,
            (
                center_x,
                terminal_y,
                (terminal_top + terminal_bottom) / 2.0,
            ),
        )
        for mount_x, mount_y in audio_amp_mount_positions(p, sign):
            amp = amp - cylinder_z(
                p.audio_amp_mount_hole / 2.0,
                22.0,
                (mount_x, mount_y, board_top - 5.0),
            )
        fits[f"fit_audio_amp_{side}"] = amp

        # Direct-wire or optional-header service enters from the board's inner
        # 1x7 edge and bends toward the left-side signal harness.
        header_y = center_y - sign * (
            p.audio_amp_pcb_width / 2.0
            + p.audio_amp_header_service_depth / 2.0
        )
        fits[f"fit_audio_amp_{side}_header_service"] = rounded_box(
            p.audio_amp_pcb_length,
            p.audio_amp_header_service_depth,
            8.0,
            1.5,
            (center_x, header_y, board_top - 7.0),
        )

        # The current 3.5 mm terminal needs both a vertical screwdriver path
        # and an outward speaker-wire first bend; neither dimension is claimed
        # as drawing-backed until a current production board is measured.
        fits[f"fit_audio_amp_{side}_screwdriver_service"] = rounded_box(
            10.0,
            10.0,
            p.audio_amp_screwdriver_height,
            1.5,
            (
                center_x,
                terminal_y,
                terminal_bottom - p.audio_amp_screwdriver_height / 2.0,
            ),
        )
        speaker_wire_y = center_y + sign * (
            p.audio_amp_pcb_width / 2.0
            + p.audio_amp_speaker_wire_depth / 2.0
        )
        fits[f"fit_audio_amp_{side}_speaker_wire"] = rounded_box(
            12.0,
            p.audio_amp_speaker_wire_depth,
            10.0,
            1.5,
            (center_x, speaker_wire_y, terminal_bottom + 5.0),
        )
        for index, (mount_x, mount_y) in enumerate(
            audio_amp_mount_positions(p, sign), start=1
        ):
            fits[f"fit_audio_amp_{side}_standoff_{index}"] = cylinder_z(
                2.0,
                p.audio_amp_standoff_height,
                (
                    mount_x,
                    mount_y,
                    board_top + p.audio_amp_standoff_height / 2.0,
                ),
            )
    return fits


def tof_sensor_pods(p: Params):
    """Four removable frames for front and side VL53L1X breakout boards."""
    parts = {}
    outer_length = p.tof_board_length + 6.0
    outer_width = p.tof_board_width + 6.0
    inner_length = p.tof_board_length + 0.8
    inner_width = p.tof_board_width + 0.8

    front_pod_x = -136.5
    for side, y in front_tof_y_positions():
        center = (front_pod_x, y, 96.0)
        pod = rounded_panel_yz(8.0, outer_length, outer_width, 4.0, center)
        pod = pod - rounded_panel_yz(12.0, inner_length, inner_width, 2.0, center)
        for mount_side, mount_y, z in front_tof_pod_mount_positions():
            if mount_side != side:
                continue
            ear = cylinder_x(4.5, 8.0, (front_pod_x, mount_y, z))
            pod = pod + ear
            pod = pod - cylinder_x(
                p.m2_5_clearance_hole / 2.0,
                12.0,
                (front_pod_x, mount_y, z),
            )
        parts[f"tof_pod_front_{side}"] = pod

    for side, sign in (("left", -1), ("right", 1)):
        center = (p.side_tof_center_x, sign * 98.0, 96.0)
        pod = rounded_panel_xz(8.0, outer_length, outer_width, 4.0, center)
        pod = pod - rounded_panel_xz(12.0, inner_length, inner_width, 2.0, center)
        for x, z in side_tof_pod_mount_positions(p, sign):
            ear = cylinder_y(4.5, 8.0, (x, sign * 98.0, z))
            pod = pod + ear
            pod = pod - cylinder_y(
                p.m2_5_clearance_hole / 2.0,
                12.0,
                (x, sign * 98.0, z),
            )
        parts[f"tof_pod_side_{side}"] = pod
    return parts


def electronics_mounts(p: Params):
    """MDDS10 controller/safety plates plus top-side cable strain relief."""
    parts = {}
    mount_z = motor_controller_plate_bottom_z(p) + 2.0

    controller = rounded_prism_xy(
        p.mdds10_plate_length,
        p.mdds10_plate_width,
        4,
        7,
        (p.controller_center_x, p.controller_center_y, mount_z),
        edge_radius=0.8,
    )
    # The board barely shares this lane with the right carry-handle doubler.
    # A local corner notch preserves 0.3 mm clearance to the metal clamp while
    # retaining the nearby MDDS10 screw ring and the board's full outline.
    carry_notch_min_y = (
        p.carry_anchor_center_y - p.carry_anchor_plate_width / 2.0 - 0.3
    )
    controller = controller - rounded_box(
        p.carry_anchor_plate_length / 2.0 + 4.0,
        40.0,
        10.0,
        1.0,
        (
            -p.carry_anchor_plate_length / 4.0,
            carry_notch_min_y + 20.0,
            mount_z,
        ),
    )
    for x, y in motor_controller_board_mount_positions(p):
        controller = controller - cylinder_z(
            p.mdds10_mount_clearance / 2.0,
            10.0,
            (x, y, mount_z),
        )
    for x, y in safety_shelf_standoff_positions(p):
        controller = controller - cylinder_z(
            p.m3_clearance_hole / 2.0,
            10.0,
            (x, y, mount_z),
        )
    for x, y in motor_controller_plate_mount_positions(p):
        controller = controller - cylinder_z(
            p.m3_clearance_hole / 2.0,
            10.0,
            (x, y, mount_z),
        )
    parts["motor_controller_mount"] = controller

    safety = rounded_prism_xy(
        p.mdds10_plate_length,
        p.mdds10_plate_width,
        4,
        8,
        (p.safety_center_x, p.safety_center_y, p.safety_mount_z),
        edge_radius=0.8,
    )
    for x, y in pico2_mount_positions(p):
        safety = safety - cylinder_z(
            p.pico2_mount_clearance / 2.0,
            10.0,
            (x, y, p.safety_mount_z),
        )
    # A front-facing U-notch gives the overhanging micro-USB connector and its
    # plug a finger/service path while preserving material around all four M2
    # board holes. The safety link itself remains wired during operation.
    safety = safety - rounded_prism_xy(
        p.pico2_usb_notch_length,
        p.pico2_usb_notch_width,
        10.0,
        2.0,
        (pico2_usb_notch_center_x(p), p.safety_center_y, p.safety_mount_z),
    )
    for x, y in safety_shelf_standoff_positions(p):
        safety = safety - cylinder_z(
            p.m3_clearance_hole / 2.0,
            10.0,
            (x, y, p.safety_mount_z),
        )
    parts["safety_mcu_mount"] = safety

    relief = rounded_prism_xy(50, 18, 4, 4, (0.0, -55.0, 147.0), edge_radius=0.8)
    for x, y in cable_strain_relief_mount_positions():
        relief = relief - cylinder_z(
            p.m3_clearance_hole / 2.0,
            10.0,
            (x, y, 147.0),
        )
    for x in (-15.0, 0.0, 15.0):
        for y in (-59.0, -51.0):
            relief = relief - cylinder_z(2.0, 10.0, (x, y, 147.0))
    parts["top_cable_strain_relief"] = relief
    return parts


def power_distribution_cover(p: Params):
    """Open-bottom touch cover over the custom four-fuse distribution PCB."""
    deck_top = p.power_deck_z + 2.0
    cover_bottom = deck_top + 0.2
    cover_top = cover_bottom + p.power_distribution_cover_height
    center = (
        p.power_distribution_center_x,
        p.power_distribution_center_y,
        (cover_bottom + cover_top) / 2.0,
    )
    cover = rounded_prism_xy(
        p.power_distribution_cover_length,
        p.power_distribution_cover_width,
        p.power_distribution_cover_height,
        3.0,
        center,
        edge_radius=0.8,
    )
    inner_bottom = cover_bottom - 1.0
    inner_top = cover_top - p.power_distribution_cover_top
    cover = cover - rounded_prism_xy(
        p.power_distribution_cover_length - 2.0 * p.power_distribution_cover_wall,
        p.power_distribution_cover_width - 2.0 * p.power_distribution_cover_wall,
        inner_top - inner_bottom,
        2.0,
        (
            p.power_distribution_center_x,
            p.power_distribution_center_y,
            (inner_bottom + inner_top) / 2.0,
        ),
        edge_radius=0.4,
    )

    # The Micro-Fit header and receptacle are already shrouded. Open the
    # cover's connector end rather than trapping the latch or forcing the wire
    # bend through a decorative wall.
    connector_cut_center_x = (
        p.power_distribution_center_x
        + p.power_distribution_cover_length / 2.0
        - 6.5
    )
    cover = cover - rounded_box(
        17.0,
        p.power_distribution_header_width + 2.0,
        p.power_distribution_header_height + 7.0,
        1.5,
        (
            connector_cut_center_x,
            p.power_distribution_center_y,
            deck_top + 9.0,
        ),
    )

    # Metal stacking standoffs retain the PCB independently. Four hollow
    # printed feet bridge only from the cover roof to the upper standoff faces.
    board_top = (
        deck_top
        + p.power_distribution_lower_standoff_height
        + p.power_distribution_board_thickness
    )
    upper_standoff_top = board_top + p.power_distribution_upper_standoff_height
    foot_height = cover_top - upper_standoff_top
    for x, y in power_distribution_board_mount_positions(p):
        cover = cover + cylinder_z(
            2.7,
            foot_height,
            (x, y, upper_standoff_top + foot_height / 2.0),
        )
        cover = cover - cylinder_z(
            p.m2_clearance_hole / 2.0,
            p.power_distribution_cover_height + 4.0,
            (x, y, (cover_bottom + cover_top) / 2.0),
        )
    return cover


def power_mounts(p: Params):
    """Removable upper deck for power, safety cutoff, and small signal boards."""
    deck = rounded_prism_xy(
        p.power_deck_length,
        p.power_deck_width,
        4.0,
        10.0,
        (p.power_deck_center_x, 0.0, p.power_deck_z),
        edge_radius=0.8,
    )
    for x, y in power_deck_mount_positions(p):
        deck = deck - cylinder_z(
            p.m3_clearance_hole / 2.0,
            10.0,
            (x, y, p.power_deck_z),
        )

    # Direct metal-standoff patterns keep both selected regulators removable
    # without straps crossing hot components or high-current solder joints.
    for x, y in (*pi_regulator_mount_positions(p), *servo_regulator_mount_positions(p)):
        deck = deck - cylinder_z(
            max(p.pi_regulator_mount_hole, p.servo_regulator_mount_hole) / 2.0 + 0.12,
            10.0,
            (x, y, p.power_deck_z),
        )
    for x, y in motor_cutoff_plate_mount_positions(p):
        deck = deck - cylinder_z(
            p.motor_cutoff_plate_mount_hole / 2.0,
            10.0,
            (x, y, p.power_deck_z),
        )
    for x, y in power_distribution_board_mount_positions(p):
        deck = deck - cylinder_z(
            p.m2_clearance_hole / 2.0,
            10.0,
            (x, y, p.power_deck_z),
        )
    # The selected IDEC E-stop's covered M3 terminals descend to the rear edge
    # of this deck. A centered 44 mm service notch preserves screwdriver and
    # wire-bend access without disturbing the four corner standoffs.
    deck = deck - rounded_box(
        p.estop_terminal_service_width + 4.0,
        p.estop_terminal_service_width + 4.0,
        10.0,
        5.0,
        (p.estop_center_x, 0.0, p.power_deck_z),
    )

    # Paired slots accept reusable hook-and-loop straps through both the deck
    # and removable under-deck harness rails. The same stations can still
    # retain small top-side modules after their wiring exits are selected.
    for side_sign in (-1, 1):
        for x, y in power_harness_strap_slots(p, side_sign):
            deck = deck - rounded_box(
                10.0,
                3.5,
                10.0,
                1.4,
                (x, y, p.power_deck_z),
            )
    for x, y in power_distribution_strain_slots(p):
        deck = deck - rounded_box(
            3.5,
            8.0,
            10.0,
            1.4,
            (x, y, p.power_deck_z),
        )
    return {
        "power_service_deck": deck,
        "power_distribution_cover": power_distribution_cover(p),
    }


def power_harness_rails(p: Params):
    """Two open-bottom U rails captured to the deck by reusable straps."""
    parts = {}
    deck_bottom = p.power_deck_z - 2.0
    base_top = deck_bottom - p.power_harness_deck_gap
    base_bottom = base_top - p.power_harness_base_thickness
    base_z = (base_bottom + base_top) / 2.0
    lip_top = base_bottom + 0.6
    lip_bottom = lip_top - p.power_harness_lip_height
    lip_z = (lip_bottom + lip_top) / 2.0
    lip_offset = (
        p.power_harness_rail_width / 2.0
        - p.power_harness_lip_thickness / 2.0
    )

    for side, side_sign in (("left", -1), ("right", 1)):
        center_y = side_sign * p.power_harness_center_y
        rail = rounded_prism_xy(
            p.power_harness_rail_length,
            p.power_harness_rail_width,
            p.power_harness_base_thickness,
            3.0,
            (p.power_deck_center_x, center_y, base_z),
            edge_radius=0.7,
        )
        for transverse_sign in (-1, 1):
            rail = rail + rounded_box(
                p.power_harness_rail_length,
                p.power_harness_lip_thickness,
                p.power_harness_lip_height,
                1.0,
                (
                    p.power_deck_center_x,
                    center_y + transverse_sign * lip_offset,
                    lip_z,
                ),
            )
        for x, y in power_harness_strap_slots(p, side_sign):
            rail = rail - rounded_box(
                10.0,
                3.5,
                p.power_harness_base_thickness + 6.0,
                1.4,
                (x, y, base_z),
            )
        parts[f"power_harness_rail_{side}"] = rail
    return parts


def rear_service_cartridge_layout(p: Params):
    """Role and center position of each independently reprintable rear insert."""
    spacing = p.rear_service_cartridge_center_spacing
    return (
        ("power_charge", -spacing, p.rear_service_panel_z),
        ("service_data", 0.0, p.rear_service_panel_z),
        ("mute_status", spacing, p.rear_service_panel_z),
    )


def rear_service_cartridge_mount_positions(p: Params, center_y: float, center_z: float):
    """Two vertical M2.5 insert-backed screw positions for one cartridge."""
    return (
        (center_y, center_z - p.rear_service_cartridge_mount_z_offset),
        (center_y, center_z + p.rear_service_cartridge_mount_z_offset),
    )


def rear_mute_switch_cutout(
    p: Params,
    depth: float,
    center_x: float,
    clearance: float | None = None,
):
    """PVB3 16 mm panel opening clipped to the drawing's 14.6 mm flats."""
    extra = p.mute_switch_cutout_clearance if clearance is None else clearance
    diameter = p.mute_switch_cutout_diameter + extra
    flat_width = p.mute_switch_cutout_flat_width + extra
    center = (
        center_x,
        p.rear_service_cartridge_center_spacing,
        p.rear_service_panel_z,
    )
    circular = cylinder_x(diameter / 2.0, depth, center)
    flat_clip = rounded_box(
        depth + 0.4,
        flat_width,
        diameter + 2.0,
        0.4,
        center,
    )
    return circular & flat_clip


def rear_service_jack_center(p: Params):
    return (
        p.body_length / 2.0 + 4.0,
        0.0,
        p.rear_service_panel_z + p.service_jack_port_z_offset,
    )


def rear_service_jack_cutout(p: Params, depth: float, center_x: float):
    """Rounded center-cartridge opening for the shallow TRRS service jack."""
    _outer_x, center_y, center_z = rear_service_jack_center(p)
    return rounded_box(
        depth,
        p.service_jack_port_width,
        p.service_jack_port_height,
        1.5,
        (center_x, center_y, center_z),
    )


def rear_charge_jack_center(p: Params):
    """Exterior center of the rear-left 14.6 V charge-only inlet."""
    return (
        p.body_length / 2.0 + 4.0,
        -p.rear_service_cartridge_center_spacing,
        p.rear_service_panel_z,
    )


def rear_charge_jack_cutout(p: Params, depth: float, center_x: float):
    """Drawing-backed 10.92 mm panel opening for Switchcraft EN2P3M20."""
    _outer_x, center_y, center_z = rear_charge_jack_center(p)
    return cylinder_x(
        (p.charge_jack_cutout_diameter + p.charge_jack_cutout_clearance) / 2.0,
        depth,
        (center_x, center_y, center_z),
    )


def service_jack_carrier_mount_positions(p: Params):
    """Two exterior M2 screws retain the removable service-jack carrier."""
    center_z = p.rear_service_panel_z + p.service_jack_port_z_offset
    return tuple(
        (0.0, center_z + z_sign * p.service_jack_carrier_mount_z_offset)
        for z_sign in (-1.0, 1.0)
    )


def service_jack_pcb_mount_positions(p: Params):
    """Two M2 insert stations hold the custom UART PCB to its shelf."""
    return tuple(
        (p.service_jack_pcb_mount_x, y_sign * p.service_jack_pcb_mount_y_offset)
        for y_sign in (-1.0, 1.0)
    )


def rear_service_panel(p: Params):
    """Outer M3 frame with three flush, independently replaceable I/O bays."""
    rear_x = p.body_length / 2.0 + 2.0
    panel = rounded_panel_yz(
        4.0,
        126.0,
        58.0,
        9.0,
        (rear_x, 0.0, p.rear_service_panel_z),
    )
    for y in (-58.0, 58.0):
        for z in (p.rear_service_panel_z - 22.0, p.rear_service_panel_z + 22.0):
            panel = panel - cylinder_x(
                p.m3_clearance_hole / 2.0,
                10.0,
                (rear_x, y, z),
            )

    opening_width = (
        p.rear_service_cartridge_tongue_width
        + 2.0 * p.rear_service_cartridge_clearance
    )
    opening_height = (
        p.rear_service_cartridge_tongue_height
        + 2.0 * p.rear_service_cartridge_clearance
    )
    pocket_width = (
        p.rear_service_cartridge_width
        + 2.0 * p.rear_service_cartridge_clearance
    )
    pocket_height = (
        p.rear_service_cartridge_height
        + 2.0 * p.rear_service_cartridge_clearance
    )
    panel_outer_x = rear_x + 2.0
    pocket_inner_x = panel_outer_x - p.rear_service_cartridge_cap_thickness

    for _role, center_y, center_z in rear_service_cartridge_layout(p):
        panel = panel - rounded_panel_yz(
            8.0,
            opening_width,
            opening_height,
            3.0,
            (rear_x, center_y, center_z),
        )
        # A shallow exterior seat keeps every cartridge face flush with the
        # surrounding frame and leaves the final connector cutout isolated to
        # a palm-sized print.
        panel = panel - rounded_panel_yz(
            p.rear_service_cartridge_cap_thickness + 0.2,
            pocket_width,
            pocket_height,
            4.0,
            (
                panel_outer_x - p.rear_service_cartridge_cap_thickness / 2.0 + 0.1,
                center_y,
                center_z,
            ),
        )
        for mount_y, mount_z in rear_service_cartridge_mount_positions(
            p, center_y, center_z
        ):
            boss_depth = 6.0
            boss = cylinder_x(
                3.6,
                boss_depth,
                (pocket_inner_x - boss_depth / 2.0 - 0.05, mount_y, mount_z),
            )
            panel = panel + boss
            panel = panel - cylinder_x(
                p.insert_hole_m2_5 / 2.0,
                boss_depth + 1.0,
                (pocket_inner_x - boss_depth / 2.0 + 0.3, mount_y, mount_z),
            )
    return panel


def rear_service_cartridges(p: Params):
    """Charge-only, service-data, and physical-mute cartridges."""
    rear_x = p.body_length / 2.0 + 2.0
    panel_outer_x = rear_x + 2.0
    cap_center_x = panel_outer_x - p.rear_service_cartridge_cap_thickness / 2.0
    tongue_center_x = (
        panel_outer_x
        - p.rear_service_cartridge_cap_thickness
        - p.rear_service_cartridge_tongue_depth / 2.0
        + 0.025
    )
    cartridges = {}
    for role, center_y, center_z in rear_service_cartridge_layout(p):
        cartridge = rounded_panel_yz(
            p.rear_service_cartridge_cap_thickness,
            p.rear_service_cartridge_width,
            p.rear_service_cartridge_height,
            4.0,
            (cap_center_x, center_y, center_z),
        )
        cartridge = cartridge + rounded_panel_yz(
            p.rear_service_cartridge_tongue_depth,
            p.rear_service_cartridge_tongue_width,
            p.rear_service_cartridge_tongue_height,
            3.0,
            (tongue_center_x, center_y, center_z),
        )
        for mount_y, mount_z in rear_service_cartridge_mount_positions(
            p, center_y, center_z
        ):
            cartridge = cartridge - cylinder_x(
                p.m2_5_clearance_hole / 2.0,
                8.0,
                (rear_x, mount_y, mount_z),
            )
        if role == "power_charge":
            cartridge = cartridge - rear_charge_jack_cutout(p, 8.0, rear_x)
            _charge_x, charge_y, charge_z = rear_charge_jack_center(p)
            cartridge = cartridge - cylinder_x(
                p.charge_jack_rear_clearance_diameter / 2.0,
                p.rear_service_cartridge_tongue_depth + 1.0,
                (tongue_center_x, charge_y, charge_z),
            )
        elif role == "mute_status":
            cartridge = cartridge - rear_mute_switch_cutout(
                p,
                8.0,
                rear_x,
            )
        elif role == "service_data":
            cartridge = cartridge - rear_service_jack_cutout(p, 8.0, rear_x)
            for mount_y, mount_z in service_jack_carrier_mount_positions(p):
                cartridge = cartridge - cylinder_x(
                    p.service_jack_carrier_mount_hole / 2.0,
                    8.0,
                    (rear_x, mount_y, mount_z),
                )
        cartridges[f"rear_service_cartridge_{role}"] = cartridge
    return cartridges


def rear_service_data_carrier(p: Params):
    """Two-piece-friendly L carrier for the shallow UART service PCB."""
    panel_outer_x, _center_y, port_z = rear_service_jack_center(p)
    flange_front_x = (
        panel_outer_x
        - p.rear_service_cartridge_cap_thickness
        - p.rear_service_cartridge_tongue_depth
        - 1.0
    )
    flange_center_x = flange_front_x - p.service_jack_carrier_flange_depth / 2.0
    flange = rounded_panel_yz(
        p.service_jack_carrier_flange_depth,
        p.service_jack_carrier_flange_width,
        p.service_jack_carrier_flange_height,
        2.5,
        (flange_center_x, 0.0, port_z),
    )
    flange = flange - rounded_box(
        p.service_jack_carrier_flange_depth + 4.0,
        p.service_jack_pcb_width + 1.4,
        p.service_jack_body_height + p.service_jack_pcb_thickness + 2.8,
        1.0,
        (
            flange_center_x,
            0.0,
            p.service_jack_pcb_bottom_z
            - 0.8
            + (
                p.service_jack_body_height
                + p.service_jack_pcb_thickness
                + 2.8
            )
            / 2.0,
        ),
    )
    for mount_y, mount_z in service_jack_carrier_mount_positions(p):
        boss_length = p.service_jack_carrier_insert_depth + 1.0
        boss = cylinder_x(
            3.2,
            boss_length,
            (flange_front_x - boss_length / 2.0, mount_y, mount_z),
        )
        flange = flange + boss
        flange = flange - cylinder_x(
            p.m2_clearance_hole / 2.0,
            p.service_jack_carrier_insert_depth + 0.5,
            (
                flange_front_x - p.service_jack_carrier_insert_depth / 2.0 + 0.1,
                mount_y,
                mount_z,
            ),
        )

    shelf_front_x = flange_front_x + 0.2
    shelf_rear_x = shelf_front_x - p.service_jack_carrier_shelf_length
    shelf_top_z = p.service_jack_pcb_bottom_z - 0.2
    shelf = rounded_prism_xy(
        p.service_jack_carrier_shelf_length,
        p.service_jack_carrier_shelf_width,
        p.service_jack_carrier_shelf_thickness,
        2.0,
        (
            (shelf_front_x + shelf_rear_x) / 2.0,
            0.0,
            shelf_top_z - p.service_jack_carrier_shelf_thickness / 2.0,
        ),
        edge_radius=0.6,
    )
    for x, y in service_jack_pcb_mount_positions(p):
        shelf = shelf - cylinder_z(
            p.m2_clearance_hole / 2.0,
            p.service_jack_carrier_shelf_thickness + 1.0,
            (x, y, shelf_top_z - p.service_jack_carrier_shelf_thickness / 2.0),
        )
    carrier = flange + shelf
    # Existing frame-insert bosses sit immediately above and below the center
    # cartridge. Matching scallops prevent the removable carrier from borrowing
    # their volume while preserving the cartridge's original M2.5 interface.
    for _mount_y, frame_mount_z in rear_service_cartridge_mount_positions(
        p, 0.0, p.rear_service_panel_z
    ):
        carrier = carrier - cylinder_x(
            4.0,
            12.0,
            (flange_front_x - 3.0, 0.0, frame_mount_z),
        )
    for mount_y, mount_z in service_jack_carrier_mount_positions(p):
        carrier = carrier - cylinder_x(
            p.m2_clearance_hole / 2.0,
            12.0,
            (flange_front_x - 3.0, mount_y, mount_z),
        )
    return carrier


def charge_jack_fit_parts(p: Params):
    """Switchcraft EN2 inlet plus mated-cord and wire-service envelopes."""
    panel_outer_x, center_y, center_z = rear_charge_jack_center(p)
    body_front_x = panel_outer_x - p.rear_service_cartridge_cap_thickness
    body = cylinder_x(
        p.charge_jack_body_diameter / 2.0,
        p.charge_jack_body_depth,
        (
            body_front_x - p.charge_jack_body_depth / 2.0,
            center_y,
            center_z,
        ),
    )
    bezel = cylinder_x(
        p.charge_jack_bezel_diameter / 2.0,
        p.charge_jack_front_depth,
        (
            panel_outer_x + p.charge_jack_front_depth / 2.0,
            center_y,
            center_z,
        ),
    )
    terminal_service = rounded_box(
        p.charge_jack_terminal_service_depth,
        p.charge_jack_terminal_service_width,
        p.charge_jack_terminal_service_height,
        1.5,
        (
            body_front_x
            - p.charge_jack_body_depth
            - p.charge_jack_terminal_service_depth / 2.0,
            center_y,
            center_z,
        ),
    )
    plug_service = cylinder_x(
        p.charge_jack_plug_diameter / 2.0,
        p.charge_jack_plug_service_length,
        (
            panel_outer_x + p.charge_jack_plug_service_length / 2.0,
            center_y,
            center_z,
        ),
    )
    return {
        "fit_charge_jack_body": body,
        "fit_charge_jack_bezel": bezel,
        "fit_charge_jack_terminal_service": terminal_service,
        "fit_charge_jack_plug_service": plug_service,
    }


def service_jack_fit_parts(p: Params):
    """Drawing-backed jack plus provisional custom-PCB and harness envelopes."""
    panel_outer_x, center_y, port_z = rear_service_jack_center(p)
    jack = rounded_box(
        p.service_jack_body_length,
        p.service_jack_body_width,
        p.service_jack_body_height,
        1.2,
        (
            panel_outer_x - p.service_jack_body_length / 2.0,
            center_y,
            port_z,
        ),
    )
    pcb_center_z = p.service_jack_pcb_bottom_z + p.service_jack_pcb_thickness / 2.0
    pcb = rounded_prism_xy(
        p.service_jack_pcb_length,
        p.service_jack_pcb_width,
        p.service_jack_pcb_thickness,
        1.5,
        (p.service_jack_pcb_center_x, center_y, pcb_center_z),
        edge_radius=0.4,
    )
    for x, y in service_jack_pcb_mount_positions(p):
        pcb = pcb - cylinder_z(
            p.service_jack_pcb_mount_hole / 2.0,
            p.service_jack_pcb_thickness + 1.0,
            (x, y, pcb_center_z),
        )
    wire_service = rounded_box(
        p.service_jack_wire_service_length,
        p.service_jack_wire_service_width,
        p.service_jack_wire_service_height,
        1.5,
        (
            p.service_jack_pcb_center_x - p.service_jack_pcb_length / 2.0
            + p.service_jack_wire_service_length / 2.0,
            -p.service_jack_wire_service_width / 2.0,
            p.service_jack_pcb_bottom_z + p.service_jack_wire_service_height / 2.0,
        ),
    )
    plug_service = cylinder_x(
        4.5,
        22.0,
        (panel_outer_x + 11.0, center_y, port_z),
    )
    return {
        "fit_service_jack_body": jack,
        "fit_service_jack_pcb": pcb,
        "fit_service_jack_wire_service": wire_service,
        "fit_service_jack_plug_service": plug_service,
    }


def mute_switch_fit_parts(p: Params):
    """Drawing-backed PVB3F230SS311 body, red ring, and service corridor."""
    panel_outer_x = p.body_length / 2.0 + 4.0
    center_y = p.rear_service_cartridge_center_spacing
    body_center_x = panel_outer_x - p.mute_switch_body_depth / 2.0
    body = rear_mute_switch_cutout(
        p,
        p.mute_switch_body_depth,
        body_center_x,
        clearance=0.0,
    )
    bezel_center_x = panel_outer_x + p.mute_switch_bezel_depth / 2.0
    bezel = cylinder_x(
        p.mute_switch_bezel_diameter / 2.0,
        p.mute_switch_bezel_depth,
        (bezel_center_x, center_y, p.rear_service_panel_z),
    )
    actuator_center_x = (
        panel_outer_x
        + p.mute_switch_bezel_depth
        + p.mute_switch_actuator_depth / 2.0
    )
    actuator = cylinder_x(
        p.mute_switch_actuator_diameter / 2.0,
        p.mute_switch_actuator_depth,
        (actuator_center_x, center_y, p.rear_service_panel_z),
    )
    led_center_x = actuator_center_x + p.mute_switch_actuator_depth / 2.0 - 0.2
    led_ring = cylinder_x(
        p.mute_switch_led_ring_diameter / 2.0,
        0.4,
        (led_center_x, center_y, p.rear_service_panel_z),
    ) - cylinder_x(
        p.mute_switch_actuator_diameter / 2.0,
        0.8,
        (led_center_x, center_y, p.rear_service_panel_z),
    )
    terminal_center_x = (
        panel_outer_x
        - p.mute_switch_body_depth
        - p.mute_switch_terminal_service_depth / 2.0
    )
    terminal_service = rounded_box(
        p.mute_switch_terminal_service_depth,
        p.mute_switch_terminal_service_width,
        p.mute_switch_terminal_service_height,
        2.0,
        (terminal_center_x, center_y, p.rear_service_panel_z),
    )
    return {
        "fit_mute_switch_body": body,
        "fit_mute_switch_bezel": bezel,
        "fit_mute_switch_actuator": actuator,
        "fit_mute_switch_led_ring": led_ring,
        "fit_mute_switch_terminal_service": terminal_service,
    }


def camera_carrier(p: Params):
    """Camera Module 3 Wide plate using the official 21 x 12.5 mm hole pattern."""
    _fit_x, board_z, carrier_x = camera_reference(p)
    carrier = rounded_panel_yz(3.0, 52.0, 42.0, 6.0, (carrier_x, 0.0, board_z))

    # Open-bottom ribbon exit. The carrier remains one printable U-shaped solid.
    carrier = carrier - rounded_panel_yz(
        8.0,
        30.0,
        14.0,
        4.0,
        (carrier_x, 0.0, board_z - 20.0),
    )
    for y, z_offset in camera_board_hole_offsets(p):
        carrier = carrier - cylinder_x(
            p.camera_mount_hole / 2.0 + 0.1,
            8.0,
            (carrier_x, y, board_z + z_offset),
        )
    for y in (-22.0, 22.0):
        for z in (board_z - 15.0, board_z + 15.0):
            carrier = carrier - cylinder_x(
                p.m3_clearance_hole / 2.0,
                8.0,
                (carrier_x, y, z),
            )
    return carrier


def head_neopixel_pcb_front_x(p: Params):
    """PCB front datum that leaves a 7.9 mm eye light-mixing gap."""
    return p.head_center_x - p.head_depth / 2.0 + 5.9


def front_neopixel_pcb_front_x(p: Params):
    """PCB front datum one millimetre behind the removable front fascia."""
    return -p.body_length / 2.0 + 2.4


def neopixel_mount_positions(
    p: Params,
    center_y: float,
    center_z: float,
    rotate_90: bool,
):
    """Official Adafruit 5975 two-hole pattern in the installed YZ plane."""
    half_spacing = p.neopixel_mount_spacing / 2.0
    if rotate_90:
        return (
            (center_y - half_spacing, center_z + p.neopixel_mount_center_offset),
            (center_y + half_spacing, center_z + p.neopixel_mount_center_offset),
        )
    return (
        (center_y + p.neopixel_mount_center_offset, center_z - half_spacing),
        (center_y + p.neopixel_mount_center_offset, center_z + half_spacing),
    )


def neopixel_breakout_fit(
    p: Params,
    pcb_front_x: float,
    center_y: float,
    center_z: float,
    rotate_90: bool,
):
    """Drawing-backed Adafruit 5975 PCB, LED, connector, and M2 holes."""
    pcb = rounded_box(
        p.neopixel_pcb_thickness,
        p.neopixel_board_width,
        p.neopixel_board_height,
        1.0,
        (
            pcb_front_x + p.neopixel_pcb_thickness / 2.0,
            center_y,
            center_z,
        ),
    )
    led = rounded_box(
        p.neopixel_led_front_protrusion + 0.02,
        5.0,
        5.0,
        0.8,
        (
            pcb_front_x - p.neopixel_led_front_protrusion / 2.0 + 0.01,
            center_y,
            center_z,
        ),
    )
    connector_depth = p.neopixel_connector_rear_protrusion + 0.02
    connector_x = (
        pcb_front_x
        + p.neopixel_pcb_thickness
        + p.neopixel_connector_rear_protrusion / 2.0
        - 0.01
    )
    connectors = None
    for offset_y, offset_z in ((-3.054, -0.032), (3.054, 0.032)):
        connector = rounded_box(
            connector_depth,
            4.95,
            5.0,
            0.7,
            (connector_x, center_y + offset_y, center_z + offset_z),
        )
        connectors = connector if connectors is None else connectors + connector
    board = pcb + led + connectors
    for y, z in neopixel_mount_positions(p, center_y, center_z, False):
        board = board - cylinder_x(
            p.neopixel_mount_hole / 2.0,
            p.neopixel_pcb_thickness + 2.0,
            (pcb_front_x + p.neopixel_pcb_thickness / 2.0, y, z),
        )
    if rotate_90:
        board = board.rotate(
            Axis((pcb_front_x, center_y, center_z), (1.0, 0.0, 0.0)),
            90.0,
        )
    return board


def neopixel_jst_service_fit(
    p: Params,
    pcb_front_x: float,
    center_y: float,
    center_z: float,
    rotate_90: bool,
):
    """Conservative plug, latch, finger, and first-bend corridor."""
    connector_back_x = (
        pcb_front_x
        + p.neopixel_pcb_thickness
        + p.neopixel_connector_rear_protrusion
    )
    carrier_front_x = connector_back_x + p.neopixel_carrier_component_clearance
    carrier_rear_x = carrier_front_x + p.neopixel_carrier_depth
    bridge_x = carrier_rear_x + 2.0
    if rotate_90:
        service = rounded_box(
            4.0,
            5.2,
            24.0,
            1.2,
            (bridge_x, center_y, center_z),
        )
        for sign in (-1.0, 1.0):
            service = service + rounded_box(
                carrier_rear_x - connector_back_x + 0.4,
                5.2,
                6.5,
                1.2,
                (
                    (connector_back_x + carrier_rear_x) / 2.0,
                    center_y,
                    center_z + sign * 8.6,
                ),
            )
    else:
        service = rounded_box(
            4.0,
            24.0,
            5.2,
            1.2,
            (bridge_x, center_y, center_z),
        )
        for sign in (-1.0, 1.0):
            service = service + rounded_box(
                carrier_rear_x - connector_back_x + 0.4,
                6.5,
                5.2,
                1.2,
                (
                    (connector_back_x + carrier_rear_x) / 2.0,
                    center_y + sign * 8.6,
                    center_z,
                ),
            )
    return service


def neopixel_spacer_fits(
    p: Params,
    pcb_front_x: float,
    carrier_x: float,
    center_y: float,
    center_z: float,
    rotate_90: bool,
):
    """Two 3 mm OD M2 spacers between the PCB and printable carrier."""
    pcb_back_x = pcb_front_x + p.neopixel_pcb_thickness
    carrier_front_x = carrier_x - p.neopixel_carrier_depth / 2.0
    spacer_length = carrier_front_x - pcb_back_x
    spacers = []
    for y, z in neopixel_mount_positions(p, center_y, center_z, rotate_90):
        spacer = cylinder_x(
            p.neopixel_spacer_od / 2.0,
            spacer_length,
            ((pcb_back_x + carrier_front_x) / 2.0, y, z),
        )
        spacer = spacer - cylinder_x(
            p.neopixel_mount_clearance / 2.0,
            spacer_length + 2.0,
            ((pcb_back_x + carrier_front_x) / 2.0, y, z),
        )
        spacers.append(spacer)
    return tuple(spacers)


def led_carrier_frame(
    p: Params,
    xyz: tuple[float, float, float],
    outer_width: float,
    outer_height: float,
    opening_width: float,
    opening_height: float,
    hole_offset: float,
    insert_holes: bool,
    hole_axis: str = "z",
    pcb_front_x: float | None = None,
    board_rotate_90: bool = False,
):
    """Reusable LED-board frame with outer M2.5 and inner M2 interfaces."""
    carrier = rounded_panel_yz(
        p.neopixel_carrier_depth,
        outer_width,
        outer_height,
        5.0,
        xyz,
    )
    carrier = carrier - rounded_panel_yz(
        8.0,
        opening_width,
        opening_height,
        3.0,
        xyz,
    )
    hole_radius = (
        p.insert_hole_m2_5 / 2.0
        if insert_holes
        else p.m2_5_clearance_hole / 2.0
    )
    if hole_axis == "y":
        hole_positions = (
            (xyz[1] - hole_offset, xyz[2]),
            (xyz[1] + hole_offset, xyz[2]),
        )
    else:
        hole_positions = (
            (xyz[1], xyz[2] - hole_offset),
            (xyz[1], xyz[2] + hole_offset),
        )
    for y, z in hole_positions:
        carrier = carrier - cylinder_x(hole_radius, 10.0, (xyz[0], y, z))
    if pcb_front_x is not None:
        # Crossbars land behind the board's two M2 holes while leaving the two
        # side-entry JST-SH plug corridors unobstructed. The eye board rotates
        # 90 degrees, so its crossbars rotate with it.
        if board_rotate_90:
            for mount_y, _mount_z in neopixel_mount_positions(
                p, xyz[1], xyz[2], True
            ):
                carrier = carrier + rounded_panel_yz(
                    p.neopixel_carrier_depth,
                    3.2,
                    outer_height,
                    1.2,
                    (xyz[0], mount_y, xyz[2]),
                )
        else:
            for _mount_y, mount_z in neopixel_mount_positions(
                p, xyz[1], xyz[2], False
            ):
                carrier = carrier + rounded_panel_yz(
                    p.neopixel_carrier_depth,
                    outer_width,
                    3.2,
                    1.2,
                    (xyz[0], xyz[1], mount_z),
                )
        for mount_y, mount_z in neopixel_mount_positions(
            p, xyz[1], xyz[2], board_rotate_90
        ):
            carrier = carrier - cylinder_x(
                p.neopixel_mount_clearance / 2.0,
                10.0,
                (xyz[0], mount_y, mount_z),
            )
    return carrier


def bumper_switch_layout():
    """Shared name/orientation/position contract for bumper safety switches."""
    return (
        ("front_left", "end", -141.0, -60.0),
        ("front_right", "end", -141.0, 60.0),
        ("rear_left", "end", 141.0, -60.0),
        ("rear_right", "end", 141.0, 60.0),
        ("side_left", "side", -20.0, -101.0),
        ("side_right", "side", -20.0, 101.0),
    )


def bumper_switch_mount_positions(orientation: str, x: float, y: float):
    """Two inboard tray-insert positions for one fixed switch plate."""
    if orientation == "end":
        hole_x = x + (5.0 if x < 0 else -5.0)
        return ((hole_x, y - 16.0), (hole_x, y + 16.0))
    hole_y = y + (5.0 if y < 0 else -5.0)
    return ((x - 16.0, hole_y), (x + 16.0, hole_y))


def bumper_switch_plate_center_z(p: Params):
    tray_bottom = p.body_bottom - p.tray_thickness
    return tray_bottom - p.bumper_switch_plate_thickness / 2.0


def bumper_switch_hardware_center(p: Params, orientation: str, x: float, y: float):
    """Locate the rotated Omron D2HW body behind its radial pin plunger."""
    return bumper_switch_reference(p, orientation, x, y)["body_center"]


def bumper_switch_reference(p: Params, orientation: str, x: float, y: float):
    """Shared D2HW body, plunger, operating, total-travel, and wire datums."""
    switch_z = (
        p.body_bottom
        - p.tray_thickness
        + 0.3
        + p.bumper_switch_height / 2.0
    )
    if orientation == "end":
        outward_sign = -1 if x < 0 else 1
        inner_face = outward_sign * bumper_inner_length(p) / 2.0
        free_plane = inner_face - outward_sign * p.bumper_switch_nominal_gap
        datum = free_plane - outward_sign * p.bumper_switch_free_position
        body_radial = datum + outward_sign * p.bumper_switch_width / 2.0
        wire_sign = -1 if y > 0 else 1
        wire_center = (
            body_radial,
            y
            + wire_sign
            * (
                p.bumper_switch_length / 2.0
                + p.bumper_switch_wire_service_length / 2.0
            ),
            switch_z,
        )
        return {
            "outward_sign": outward_sign,
            "inner_face": inner_face,
            "free_plane": free_plane,
            "operating_plane": datum
            + outward_sign
            * (p.bumper_switch_operating_position - p.bumper_switch_operating_tolerance),
            "total_plane": datum
            + outward_sign * p.bumper_switch_total_travel_position,
            "body_center": (body_radial, y, switch_z),
            "wire_center": wire_center,
            "wire_sign": wire_sign,
        }
    outward_sign = -1 if y < 0 else 1
    inner_face = outward_sign * bumper_inner_width(p) / 2.0
    free_plane = inner_face - outward_sign * p.bumper_switch_nominal_gap
    datum = free_plane - outward_sign * p.bumper_switch_free_position
    body_radial = datum + outward_sign * p.bumper_switch_width / 2.0
    wire_sign = 1 if x <= 0 else -1
    wire_center = (
        x
        + wire_sign
        * (
            p.bumper_switch_length / 2.0
            + p.bumper_switch_wire_service_length / 2.0
        ),
        body_radial,
        switch_z,
    )
    return {
        "outward_sign": outward_sign,
        "inner_face": inner_face,
        "free_plane": free_plane,
        "operating_plane": datum
        + outward_sign
        * (p.bumper_switch_operating_position - p.bumper_switch_operating_tolerance),
        "total_plane": datum + outward_sign * p.bumper_switch_total_travel_position,
        "body_center": (x, body_radial, switch_z),
        "wire_center": wire_center,
        "wire_sign": wire_sign,
    }


def bumper_switch_body_mount_positions(
    p: Params,
    orientation: str,
    x: float,
    y: float,
):
    """Two vertical M3 paths into the D2HW-C202MR tapped mounting body."""
    body_x, body_y, _body_z = bumper_switch_hardware_center(p, orientation, x, y)
    offset = p.bumper_switch_mount_spacing / 2.0
    if orientation == "end":
        return ((body_x, body_y - offset), (body_x, body_y + offset))
    return ((body_x - offset, body_y), (body_x + offset, body_y))


def bumper_switch_hardware_fit(p: Params, orientation: str, x: float, y: float):
    """Drawing-backed body, free pin plunger, and straight lead-exit corridor."""
    reference = bumper_switch_reference(p, orientation, x, y)
    body_center = reference["body_center"]
    if orientation == "end":
        body = rounded_box(
            p.bumper_switch_width,
            p.bumper_switch_length,
            p.bumper_switch_height,
            1.0,
            body_center,
        )
        body_outer = body_center[0] + reference["outward_sign"] * p.bumper_switch_width / 2.0
        plunger_length = p.bumper_switch_free_position - p.bumper_switch_width
        plunger = cylinder_x(
            p.bumper_switch_plunger_diameter / 2.0,
            plunger_length + 0.2,
            (
                body_outer + reference["outward_sign"] * (plunger_length / 2.0 - 0.1),
                body_center[1],
                body_center[2],
            ),
        )
        wire = rounded_box(
            p.bumper_switch_wire_service_width,
            p.bumper_switch_wire_service_length + 0.2,
            p.bumper_switch_wire_service_height,
            1.0,
            reference["wire_center"],
        )
    else:
        body = rounded_box(
            p.bumper_switch_length,
            p.bumper_switch_width,
            p.bumper_switch_height,
            1.0,
            body_center,
        )
        body_outer = body_center[1] + reference["outward_sign"] * p.bumper_switch_width / 2.0
        plunger_length = p.bumper_switch_free_position - p.bumper_switch_width
        plunger = cylinder_y(
            p.bumper_switch_plunger_diameter / 2.0,
            plunger_length + 0.2,
            (
                body_center[0],
                body_outer + reference["outward_sign"] * (plunger_length / 2.0 - 0.1),
                body_center[2],
            ),
        )
        wire = rounded_box(
            p.bumper_switch_wire_service_length + 0.2,
            p.bumper_switch_wire_service_width,
            p.bumper_switch_wire_service_height,
            1.0,
            reference["wire_center"],
        )
    return body + plunger + wire


def bumper_switch_travel_target(
    p: Params,
    orientation: str,
    x: float,
    y: float,
    target: str,
):
    """Thin radial gauge at the worst-case operating or total-travel plane."""
    reference = bumper_switch_reference(p, orientation, x, y)
    plane = reference[f"{target}_plane"]
    z = reference["body_center"][2]
    if orientation == "end":
        return rounded_box(0.2, 5.0, 4.0, 0.05, (plane, y, z))
    return rounded_box(5.0, 0.2, 4.0, 0.05, (x, plane, z))


def bumper_switch_stop_shapes(p: Params, orientation: str, x: float, y: float):
    """Two rigid PETG stops prevent the TPU from bottoming the D2HW plunger."""
    reference = bumper_switch_reference(p, orientation, x, y)
    stop_plane = reference["inner_face"] - reference["outward_sign"] * p.bumper_switch_stop_travel
    stop_z = p.body_bottom - p.tray_thickness + p.bumper_switch_height / 2.0
    stops = []
    for tangent_sign in (-1, 1):
        if orientation == "end":
            center = (
                stop_plane - reference["outward_sign"] * p.bumper_switch_stop_length / 2.0,
                y + tangent_sign * p.bumper_switch_stop_offset,
                stop_z,
            )
            stops.append(
                rounded_box(
                    p.bumper_switch_stop_length,
                    p.bumper_switch_stop_width,
                    p.bumper_switch_height,
                    0.8,
                    center,
                )
            )
        else:
            center = (
                x + tangent_sign * p.bumper_switch_stop_offset,
                stop_plane - reference["outward_sign"] * p.bumper_switch_stop_length / 2.0,
                stop_z,
            )
            stops.append(
                rounded_box(
                    p.bumper_switch_stop_width,
                    p.bumper_switch_stop_length,
                    p.bumper_switch_height,
                    0.8,
                    center,
                )
            )
    return tuple(stops)


def bumper_switch_stop_contact_patches(
    p: Params,
    orientation: str,
    x: float,
    y: float,
    inward_displacement: float,
):
    """Two TPU wall gauges aligned with the flanking rigid stop blocks."""
    if orientation == "end":
        return tuple(
            bumper_switch_contact_patch(
                p,
                orientation,
                x,
                y + sign * p.bumper_switch_stop_offset,
                inward_displacement,
            )
            for sign in (-1, 1)
        )
    return tuple(
        bumper_switch_contact_patch(
            p,
            orientation,
            x + sign * p.bumper_switch_stop_offset,
            y,
            inward_displacement,
        )
        for sign in (-1, 1)
    )


def bumper_switch_tray_pocket(p: Params, orientation: str, x: float, y: float):
    """Clear the tray around the exact body, side leads, and overtravel stops."""
    reference = bumper_switch_reference(p, orientation, x, y)
    switch_x, switch_y, _switch_z = reference["body_center"]
    clearance = 2.0 * p.bumper_switch_tray_pocket_clearance
    dimensions = (
        (p.bumper_switch_width + clearance, p.bumper_switch_length + clearance)
        if orientation == "end"
        else (p.bumper_switch_length + clearance, p.bumper_switch_width + clearance)
    )
    tray_z = p.body_bottom - p.tray_thickness / 2.0
    pocket = rounded_box(
        dimensions[0],
        dimensions[1],
        p.tray_thickness + 4.0,
        2.0,
        (switch_x, switch_y, tray_z),
    )
    if orientation == "end":
        wire_dimensions = (
            p.bumper_switch_wire_service_width + clearance,
            p.bumper_switch_wire_service_length + clearance,
        )
    else:
        wire_dimensions = (
            p.bumper_switch_wire_service_length + clearance,
            p.bumper_switch_wire_service_width + clearance,
        )
    pocket = pocket + rounded_box(
        wire_dimensions[0],
        wire_dimensions[1],
        p.tray_thickness + 4.0,
        1.5,
        (reference["wire_center"][0], reference["wire_center"][1], tray_z),
    )
    for stop in bumper_switch_stop_shapes(p, orientation, x, y):
        stop_box = stop.bounding_box()
        pocket = pocket + rounded_box(
            float(stop_box.max.X - stop_box.min.X) + clearance,
            float(stop_box.max.Y - stop_box.min.Y) + clearance,
            p.tray_thickness + 4.0,
            1.0,
            (
                float((stop_box.min.X + stop_box.max.X) / 2.0),
                float((stop_box.min.Y + stop_box.max.Y) / 2.0),
                tray_z,
            ),
        )
    return pocket


def bumper_switch_contact_patch(
    p: Params,
    orientation: str,
    x: float,
    y: float,
    inward_displacement: float = 0.0,
):
    """Local TPU inner-wall patch used to prove gap and nominal actuation."""
    switch_z = bumper_switch_hardware_center(p, orientation, x, y)[2]
    if orientation == "end":
        outward_sign = -1 if x < 0 else 1
        inner_face = outward_sign * bumper_inner_length(p) / 2.0
        patch_x = (
            inner_face
            + outward_sign * 1.0
            - outward_sign * inward_displacement
        )
        return rounded_box(2.0, 8.0, 4.0, 0.8, (patch_x, y, switch_z))
    outward_sign = -1 if y < 0 else 1
    inner_face = outward_sign * bumper_inner_width(p) / 2.0
    patch_y = (
        inner_face
        + outward_sign * 1.0
        - outward_sign * inward_displacement
    )
    return rounded_box(8.0, 2.0, 4.0, 0.8, (x, patch_y, switch_z))


def bumper_switch_mounts(p: Params):
    """Six rigid tray-fixed plates beneath the locally compliant TPU bumper."""
    parts = {}
    mount_z = bumper_switch_plate_center_z(p)
    for name, orientation, x, y in bumper_switch_layout():
        if orientation == "end":
            plate = rounded_prism_xy(
                p.bumper_switch_plate_radial,
                p.bumper_switch_plate_tangential,
                p.bumper_switch_plate_thickness,
                4.0,
                (x, y, mount_z),
                edge_radius=0.8,
            )
        else:
            plate = rounded_prism_xy(
                p.bumper_switch_plate_tangential,
                p.bumper_switch_plate_radial,
                p.bumper_switch_plate_thickness,
                4.0,
                (x, y, mount_z),
                edge_radius=0.8,
            )
        for hole_x, hole_y in bumper_switch_mount_positions(orientation, x, y):
            plate = plate - cylinder_z(
                p.m3_clearance_hole / 2.0,
                p.bumper_switch_plate_thickness + 4.0,
                (hole_x, hole_y, mount_z),
            )
        plate_bottom = mount_z - p.bumper_switch_plate_thickness / 2.0
        for hole_x, hole_y in bumper_switch_body_mount_positions(
            p, orientation, x, y
        ):
            plate = plate - cylinder_z(
                p.bumper_switch_mount_hole / 2.0,
                p.bumper_switch_plate_thickness + 2.0,
                (hole_x, hole_y, mount_z),
            )
            plate = plate - cylinder_z(
                p.bumper_switch_mount_head_diameter / 2.0,
                p.bumper_switch_mount_head_recess + 0.2,
                (
                    hole_x,
                    hole_y,
                    plate_bottom + p.bumper_switch_mount_head_recess / 2.0,
                ),
            )
        for stop in bumper_switch_stop_shapes(p, orientation, x, y):
            plate = plate + stop
        parts[f"bumper_switch_mount_{name}"] = plate
    return parts


def bumper_carrier(p: Params):
    bumper_z = bumper_center_z(p)
    outer = rounded_prism_xy(
        p.bumper_length,
        p.bumper_width,
        p.bumper_height,
        p.bumper_outer_corner_radius,
        (0, 0, bumper_z),
        edge_radius=3.5,
    )
    inner = rounded_prism_xy(
        bumper_inner_length(p),
        bumper_inner_width(p),
        p.bumper_height + 8,
        p.body_corner_radius + p.bumper_body_clearance,
        (0, 0, bumper_z),
    )
    bumper = outer - inner

    # Lowered tires pass completely through the visible side rail. Concealed
    # bridges run inboard of the tire faces and below the tray, preserving one
    # printable carrier without adding a visible guard-rail loop.
    bridge_z = bumper_bottom_z(p) + 4.0
    for sign in (-1, 1):
        bumper = bumper + rounded_box(
            bumper_inner_length(p) + 4.0,
            26.0,
            8.0,
            3.0,
            (0.0, sign * (p.body_width / 2.0 - 10.0), bridge_z),
        )

    # Wheel arches remove the tire volume from the perimeter carrier while
    # leaving a low connecting strip beneath each wheel opening.
    for sign in (-1, 1):
        wheel_y = wheel_center_y(p, sign)
        for wheel_x in p.wheel_x_positions:
            bumper = bumper - cylinder_y(
                p.wheel_radius + 4.0,
                p.wheel_thickness + 16.0,
                (wheel_x, wheel_y, p.wheel_center_z),
            )

    # Each fixed PETG switch plate sits in a local TPU relief. Radial clearance
    # includes the nominal actuation stroke; tangential/vertical clearance only
    # prevents the moving bumper from rubbing or clamping the fixed plate.
    switch_plate_z = bumper_switch_plate_center_z(p)
    radial_recess = p.bumper_switch_plate_radial + 2.0 * (
        p.bumper_switch_actuation_travel + p.bumper_switch_recess_clearance
    )
    tangential_recess = (
        p.bumper_switch_plate_tangential
        + 2.0 * p.bumper_switch_recess_clearance
    )
    recess_height = (
        p.bumper_switch_plate_thickness
        + 2.0 * p.bumper_switch_recess_clearance
    )
    for _name, orientation, x, y in bumper_switch_layout():
        if orientation == "end":
            recess = rounded_prism_xy(
                radial_recess,
                tangential_recess,
                recess_height,
                4.2,
                (x, y, switch_plate_z),
            )
        else:
            recess = rounded_prism_xy(
                tangential_recess,
                radial_recess,
                recess_height,
                4.2,
                (x, y, switch_plate_z),
            )
        bumper = bumper - recess

    # Mechanical-looking front screw caps remain cosmetic placeholders. The
    # actual six switch plates are independently retained by tray inserts.
    for y in (-92, 92):
        bumper = bumper + cylinder_x(4.5, 3.5, (-160.0, y, p.body_bottom - 12))
    return bumper


def lid_and_top_details(p: Params):
    reveal_outer = rounded_prism_xy(
        p.lid_length + 8,
        p.lid_width + 8,
        1.0,
        18,
        (0, 0, p.body_bottom + p.body_height + 0.5),
        edge_radius=0.3,
    )
    reveal_inner = rounded_prism_xy(
        p.lid_length - 4,
        p.lid_width - 4,
        3.0,
        14,
        (0, 0, p.body_bottom + p.body_height + 0.5),
    )
    reveal = reveal_outer - reveal_inner
    lid_z = p.body_bottom + p.body_height + 3.0
    lid = rounded_prism_xy(
        p.lid_length,
        p.lid_width,
        p.lid_thickness,
        20,
        (0, 0, lid_z),
        edge_radius=1.0,
    )
    lid_bottom = lid_z - p.lid_thickness / 2.0
    lid_top = lid_z + p.lid_thickness / 2.0

    # Four underside bosses retain a low-profile dark vent inlay. Two lie on
    # each side of the stepped lid split, so the grille doubles as a removable
    # top-side seam clamp without relying on glue or snap tabs.
    vent_insert_depth = 4.2
    boss_bottom = lid_bottom - p.vent_inlay_bridge_height
    boss_top = lid_bottom + 0.6
    for x, y in vent_inlay_mount_positions(p):
        boss = cylinder_z(
            p.vent_inlay_boss_radius,
            boss_top - boss_bottom,
            (x, y, (boss_bottom + boss_top) / 2.0),
        )
        lid = lid + boss
        lid = lid - cylinder_z(
            p.insert_hole_m2_5 / 2.0,
            vent_insert_depth,
            (x, y, boss_bottom + vent_insert_depth / 2.0),
        )
        lid = lid - cylinder_z(
            p.m2_5_clearance_hole / 2.0,
            lid_top - (boss_bottom + vent_insert_depth - 0.2) + 1.0,
            (
                x,
                y,
                (lid_top + boss_bottom + vent_insert_depth - 0.2 + 1.0) / 2.0,
            ),
        )
    for x, y in lid_mount_positions():
        lid = lid - cylinder_z(p.m3_clearance_hole / 2.0, 12, (x, y, lid_z))
    lid = lid - estop_body_pass_clearance(p, 20.0, lid_z)
    estop_panel_recess = cylinder_z(
        p.estop_mount_panel_outer_radius + 0.3,
        p.estop_mount_panel_recess_depth + 1.0,
        (
            p.estop_center_x,
            0.0,
            lid_top - p.estop_mount_panel_recess_depth / 2.0 + 0.5,
        ),
    )
    lid = lid - estop_panel_recess
    for x, y in estop_mount_positions(p):
        lid = lid - cylinder_z(
            p.m3_clearance_hole / 2.0,
            p.lid_thickness + 4.0,
            (x, y, lid_z),
        )
    lid = lid - cylinder_z(
        p.neck_opening_diameter / 2.0,
        20.0,
        (p.neck_x, 0.0, lid_z),
    )
    for x, y in pan_bearing_key_positions(p):
        lid = lid - rounded_box(
            p.pan_bearing_key_length + 0.5,
            p.pan_bearing_key_width + 0.5,
            20.0,
            1.0,
            (x, y, lid_z),
        )
    for x, y in speaker_slot_layout():
        lid = lid - rounded_prism_xy(28.0, 2.8, 10.0, 1.2, (x, y, lid_z))

    # Recess the concept-facing grille into the teal lid. It sits only 0.35 mm
    # proud, retains enough thickness around every slot, and remains separately
    # printable in dark PETG for the reference's clean black vent field.
    recess = rounded_prism_xy(
        p.vent_inlay_length + 0.5,
        p.vent_inlay_width + 0.5,
        p.vent_inlay_recess_depth + 1.0,
        10.25,
        (
            p.vent_inlay_center_x,
            0.0,
            lid_top - p.vent_inlay_recess_depth / 2.0 + 0.5,
        ),
        edge_radius=0.4,
    )
    lid = lid - recess
    inlay_bottom = lid_top - p.vent_inlay_recess_depth + 0.15
    inlay = rounded_prism_xy(
        p.vent_inlay_length,
        p.vent_inlay_width,
        p.vent_inlay_thickness,
        10.0,
        (
            p.vent_inlay_center_x,
            0.0,
            inlay_bottom + p.vent_inlay_thickness / 2.0,
        ),
        edge_radius=0.35,
    )
    for x, y in mic_slot_layout(p):
        inlay_slot = rounded_prism_xy(
            36.0,
            3.0,
            8.0,
            1.2,
            (x, y, lid_top),
        )
        lid_slot = rounded_prism_xy(
            36.0,
            3.0,
            12.0,
            1.2,
            (x, y, lid_z),
        )
        inlay = inlay - inlay_slot
        lid = lid - lid_slot
    for x, y in vent_inlay_mount_positions(p):
        inlay = inlay - cylinder_z(
            p.m2_5_clearance_hole / 2.0,
            p.vent_inlay_thickness + 4.0,
            (x, y, lid_top),
        )

    # The large removable E-stop mount panel intentionally nibbles into the
    # rear-right corner of the concept vent field. Cut that exact flange from
    # the inlay so both parts remain independently removable and the resulting
    # curved reveal reads as a deliberate safety-control clearance.
    inlay = inlay - cylinder_z(
        p.estop_mount_panel_outer_radius + 0.3,
        p.vent_inlay_thickness + 4.0,
        (p.estop_center_x, 0.0, lid_top),
    )

    # Removable IDEC E-stop mount panel. The 66 mm lower flange seats 2 mm into
    # the teal lid while the 56 mm central land remains visible. The purchased
    # switch clamps only this 4 mm keyed panel; the larger body passes freely
    # through lid, shell, and underside backing plate.
    panel_bottom = estop_mount_panel_bottom_z(p)
    panel_top = estop_mount_panel_top_z(p)
    estop_well = cylinder_z(
        p.estop_mount_panel_outer_radius,
        p.estop_mount_panel_recess_depth,
        (
            p.estop_center_x,
            0.0,
            panel_bottom + p.estop_mount_panel_recess_depth / 2.0,
        ),
    )
    estop_well = estop_well + cylinder_z(
        p.estop_mount_panel_visible_radius,
        p.estop_mount_panel_thickness,
        (p.estop_center_x, 0.0, (panel_bottom + panel_top) / 2.0),
    )
    estop_well = estop_well - estop_keyed_panel_cutout(
        p,
        p.estop_mount_panel_thickness + 4.0,
        (panel_bottom + panel_top) / 2.0,
    )
    for x, y in estop_mount_positions(p):
        estop_well = estop_well - cylinder_z(
            p.insert_hole_m3 / 2.0,
            p.estop_mount_panel_insert_depth,
            (x, y, panel_bottom + p.estop_mount_panel_insert_depth / 2.0),
        )

    operator_stem_height = p.estop_operator_height - 6.0
    estop = cylinder_z(
        14.0,
        operator_stem_height,
        (p.estop_center_x, 0.0, panel_top + operator_stem_height / 2.0),
    )
    estop_cap = cylinder_z(
        p.estop_operator_diameter / 2.0,
        6.0,
        (p.estop_center_x, 0.0, panel_top + operator_stem_height + 3.0),
    )
    return reveal, lid, inlay, estop_well, estop, estop_cap


def estop_backing_plate(p: Params):
    """Underside reinforcement for a 22 mm-class panel-mount E-stop."""
    plate_z = estop_backing_center_z(p)
    center = (p.estop_center_x, 0.0, plate_z)
    plate = cylinder_z(
        p.estop_backing_outer_radius,
        p.estop_backing_plate_thickness,
        center,
    )

    # A raised annular collar supports the roof directly around the switch
    # bore while the lower disk carries four removable screws. A small axial
    # clearance lets the screws draw the assembly together despite print
    # variation; the switch's purchased metal nut remains the primary clamp.
    top_inner_z = body_inner_roof_z(p)
    plate_top = plate_z + p.estop_backing_plate_thickness / 2.0
    collar_bottom = plate_top - 0.4
    collar_top = top_inner_z - 0.2
    collar = cylinder_z(
        p.estop_backing_collar_outer_radius,
        collar_top - collar_bottom,
        (p.estop_center_x, 0.0, (collar_bottom + collar_top) / 2.0),
    )
    plate = plate + collar
    plate = plate - estop_body_pass_clearance(
        p,
        collar_top - (plate_z - p.estop_backing_plate_thickness / 2.0) + 4.0,
        (collar_top + plate_z) / 2.0,
    )
    for x, y in estop_mount_positions(p):
        plate = plate - cylinder_z(
            p.m3_clearance_hole / 2.0,
            p.estop_backing_plate_thickness + 4.0,
            (x, y, plate_z),
        )
    return plate


def wheel_parts(p: Params):
    parts = {}
    for side, sign in (("left", -1), ("right", 1)):
        # The shared wheel-well contract nests the inner tire face into the
        # cream shell while leaving the outboard face accessible for service.
        y = wheel_center_y(p, sign)
        for index, wheel_x in enumerate(p.wheel_x_positions, start=1):
            key = f"wheel_{side}_{index}"
            tire = cylinder_y(p.wheel_radius, p.wheel_thickness, (wheel_x, y, p.wheel_center_z))
            tire = tire - wheel_tread_keepout(p, wheel_x, y)
            # A serviceable PETG core now carries the axle/hub load through a
            # true central TPU opening. The inner flange seats in a shallow
            # counterbore; the visible teal ring remains a separate outboard
            # trim/retaining piece matching the concept art.
            tire_outer_y = y + sign * p.wheel_thickness / 2.0
            tire_inner_y = y - sign * p.wheel_thickness / 2.0
            tire = tire - cylinder_y(
                p.wheel_core_radius + p.wheel_core_clearance,
                p.wheel_thickness + 4.0,
                (wheel_x, y, p.wheel_center_z),
            )
            tire = tire - cylinder_y(
                p.wheel_core_inboard_flange_radius + p.wheel_core_clearance,
                p.wheel_core_inboard_flange_thickness + 0.4,
                (
                    wheel_x,
                    tire_inner_y
                    + sign * (p.wheel_core_inboard_flange_thickness / 2.0),
                    p.wheel_center_z,
                ),
            )

            side_y = y + sign * (p.wheel_thickness / 2.0 + 1.0)
            ring = cylinder_y(30, 4.0, (wheel_x, side_y, p.wheel_center_z))
            ring = ring - cylinder_y(
                p.wheel_core_radius + 0.5,
                8.0,
                (wheel_x, side_y, p.wheel_center_z),
            )

            core_center_y = y + sign * (
                (p.wheel_core_length - p.wheel_thickness) / 2.0
            )
            hub = cylinder_y(
                p.wheel_core_radius,
                p.wheel_core_length,
                (wheel_x, core_center_y, p.wheel_center_z),
            )
            hub = hub + cylinder_y(
                p.wheel_core_inboard_flange_radius,
                p.wheel_core_inboard_flange_thickness,
                (
                    wheel_x,
                    tire_inner_y
                    + sign * (p.wheel_core_inboard_flange_thickness / 2.0),
                    p.wheel_center_z,
                ),
            )

            if index == 2:
                # The motor gearbox and 25 mm bracket face overlap the core's
                # inboard end by 4 mm. A shallow 26.4 mm counterbore clears
                # both metal parts while leaving the longer 19.4 mm hub cavity
                # to transmit torque through the four M3 wheel screws.
                hub = hub - rounded_box(
                    p.motor_bracket_base_length + 1.4,
                    7.0,
                    p.motor_bracket_face_size + 6.0,
                    0.0,
                    (
                        wheel_x,
                        tire_inner_y + sign * 3.5,
                        p.wheel_center_z - 0.5,
                    ),
                )
                cavity_center_y = tire_inner_y + sign * (
                    p.wheel_core_rear_hub_cavity_length / 2.0
                )
                hub = hub - cylinder_y(
                    p.motor_hub_diameter / 2.0 + p.motor_hub_clearance,
                    p.wheel_core_rear_hub_cavity_length + 0.4,
                    (wheel_x, cavity_center_y, p.wheel_center_z),
                )
                hub = hub - cylinder_y(
                    p.motor_shaft_diameter / 2.0 + 0.3,
                    p.wheel_core_length + 4.0,
                    (wheel_x, core_center_y, p.wheel_center_z),
                )
                for dx, dz in drive_motor_hub_mount_positions(p):
                    hub = hub - cylinder_y(
                        p.m3_clearance_hole / 2.0,
                        p.wheel_core_length + 4.0,
                        (wheel_x + dx, core_center_y, p.wheel_center_z + dz),
                    )
            else:
                # The front core bolts to a Pololu #2693 8 mm aluminum hub.
                # A 10 mm-OD metal spacer tube passes through the core to the
                # outer 608 inner race; the printed bore never serves as an
                # axle bearing or friction-only retention feature.
                hub = hub - cylinder_y(
                    p.front_axle_outer_spacer_od / 2.0
                    + p.front_axle_spacer_clearance,
                    p.wheel_core_length + 4.0,
                    (wheel_x, core_center_y, p.wheel_center_z),
                )
                front_hub_cavity_length = (
                    p.front_hub_length + 2.0 * p.front_hub_cavity_clearance
                )
                core_outer_y = core_center_y + sign * p.wheel_core_length / 2.0
                front_hub_cavity_y = core_outer_y - sign * (
                    front_hub_cavity_length / 2.0
                )
                hub = hub - cylinder_y(
                    p.front_hub_diameter / 2.0 + p.front_hub_cavity_clearance,
                    front_hub_cavity_length,
                    (
                        wheel_x,
                        front_hub_cavity_y,
                        p.wheel_center_z,
                    ),
                )
                for dx, dz in front_idler_hub_mount_positions(p):
                    hub = hub - cylinder_y(
                        p.m3_clearance_hole / 2.0,
                        p.wheel_core_length + 4.0,
                        (
                            wheel_x + dx,
                            core_center_y,
                            p.wheel_center_z + dz,
                        ),
                    )

            # The teal ring enters the tire by 1 mm; the structural core is
            # independently removable from the inboard side after hardware is
            # released, so no adhesive is required for drivetrain service.
            tire = tire - cylinder_y(
                30.3,
                1.7,
                (
                    wheel_x,
                    tire_outer_y - sign * 0.35,
                    p.wheel_center_z,
                ),
            )
            parts[key] = tire
            parts[f"hub_ring_{side}_{index}"] = ring
            parts[f"hub_{side}_{index}"] = hub
    return parts


def motor_pods(p: Params):
    """Removable shrouds around metal-bracketed Pololu 25D drive motors."""
    parts = {}
    drive_x = p.wheel_x_positions[1]
    shell_center_z = mobility_pod_shell_center_z(p)
    for side, sign in (("left", -1), ("right", 1)):
        center_y = sign * 84.0
        pod = rounded_box(
            60.0,
            54.0,
            p.mobility_pod_shell_height,
            6,
            (drive_x, center_y, shell_center_z),
        )
        flange = rounded_prism_xy(
            60.0,
            54.0,
            6,
            6,
            (drive_x, center_y, p.body_bottom + 7.0),
            edge_radius=1.0,
        )
        pod = pod + flange
        face_y = drive_motor_face_y(p, sign)
        motor_path_center_y = (face_y + sign * 38.0) / 2.0
        pod = pod - cylinder_y(
            p.motor_body_diameter / 2.0 + 0.7,
            abs(face_y - sign * 38.0) + 4.0,
            (drive_x, motor_path_center_y, p.wheel_center_z),
        )
        inner_face_y, cover_center_y, cover_screws = motor_pod_service_interface(p, sign)
        # Open the inboard service mouth and the outboard hub envelope. The
        # motor slides through the removable ring cover, while wheel removal
        # exposes the two face screws in the purchased metal bracket.
        pod = pod - rounded_box(
            32.0,
            18.0,
            32.0,
            4.0,
            (drive_x, inner_face_y - sign * 4.0, p.wheel_center_z),
        )
        pod = pod - cylinder_y(
            p.wheel_core_inboard_flange_radius + 0.5,
            12.0,
            (drive_x, face_y - sign * 4.0, p.wheel_center_z),
        )
        pod = pod - cylinder_y(
            p.wheel_radius + 0.8,
            p.wheel_thickness + 4.0,
            (drive_x, wheel_center_y(p, sign), p.wheel_center_z),
        )

        # Clearance for the official 1.5 mm aluminum L bracket. Three 3 mm
        # metal spacers below its base establish the exact motor-axis height;
        # the printed pod only locates and guards this safety-relevant mount.
        pod = pod - rounded_panel_xz(
            p.motor_bracket_thickness + 0.6,
            p.motor_bracket_face_size + 0.6,
            p.motor_bracket_face_size + 0.6,
            3.0,
            (
                drive_x,
                face_y + sign * p.motor_bracket_thickness / 2.0,
                p.wheel_center_z,
            ),
        )
        pod = pod - rounded_box(
            p.motor_bracket_base_width + 0.6,
            p.motor_bracket_base_length + 0.6,
            p.motor_bracket_thickness + 0.6,
            1.0,
            (
                drive_x,
                face_y - sign * p.motor_bracket_base_length / 2.0,
                p.body_bottom
                + p.motor_bracket_spacer_height
                + p.motor_bracket_thickness / 2.0,
            ),
        )
        for x, y in motor_pod_mount_positions(p, sign):
            pod = pod - cylinder_z(
                p.m3_clearance_hole / 2.0,
                14.0,
                (x, y, p.body_bottom + 7.0),
            )
        cover = rounded_box(
            56.0,
            2.0,
            p.motor_cover_height,
            4.0,
            (drive_x, cover_center_y, shell_center_z),
        )
        cover = cover - cylinder_y(
            p.motor_body_diameter / 2.0 + 0.7,
            8.0,
            (drive_x, cover_center_y, p.wheel_center_z),
        )
        # The actual encoder leads exit upward from the end cap. This notch
        # preserves their bend radius and the 1x6 connector service path.
        cover = cover - rounded_box(
            12.0,
            8.0,
            22.0,
            2.0,
            (
                drive_x + 8.0,
                cover_center_y,
                p.wheel_center_z + p.motor_body_diameter / 2.0 + 9.0,
            ),
        )
        # A thin outboard bridge keeps the side-open cable notch from splitting
        # the service cover into two printable islands. Leads enter from the
        # inboard face, so this rib remains outside their validated corridor.
        cover = cover + rounded_box(
            20.0,
            0.6,
            3.0,
            0.4,
            (
                drive_x + 8.0,
                cover_center_y + sign * 0.7,
                p.wheel_center_z + p.motor_body_diameter / 2.0 + 2.8,
            ),
        )
        for x, z in cover_screws:
            pod = pod - cylinder_y(
                p.insert_hole_m3 / 2.0,
                10.0,
                (x, inner_face_y, z),
            )
            cover = cover - cylinder_y(
                p.m3_clearance_hole / 2.0,
                8.0,
                (x, cover_center_y, z),
            )
        parts[f"motor_pod_{side}"] = pod
        parts[f"motor_pod_cover_{side}"] = cover
    return parts


def drive_motor_fit(p: Params, side_sign: int):
    """Pololu #4867 motor, encoder cap, upward leads, boss, and D shaft."""
    drive_x = p.wheel_x_positions[1]
    face_y = drive_motor_face_y(p, side_sign)
    gearbox_center_y = face_y - side_sign * p.motor_gearbox_length / 2.0
    can_center_y = face_y - side_sign * (
        p.motor_gearbox_length + p.motor_can_length / 2.0
    )
    encoder_center_y = face_y - side_sign * (
        p.motor_gearbox_length + p.motor_can_length + p.motor_encoder_length / 2.0
    )
    gearbox = cylinder_y(
        p.motor_body_diameter / 2.0,
        p.motor_gearbox_length,
        (drive_x, gearbox_center_y, p.wheel_center_z),
    )
    can = cylinder_y(
        p.motor_can_diameter / 2.0,
        p.motor_can_length,
        (drive_x, can_center_y, p.wheel_center_z),
    )
    encoder = cylinder_y(
        p.motor_body_diameter / 2.0,
        p.motor_encoder_length,
        (drive_x, encoder_center_y, p.wheel_center_z),
    )
    lead_keepout = rounded_box(
        8.0,
        12.0,
        7.0,
        1.5,
        (
            drive_x + 8.0,
            encoder_center_y,
            p.wheel_center_z + p.motor_body_diameter / 2.0 + 2.0,
        ),
    )
    boss_y = face_y + side_sign * p.motor_shaft_boss_length / 2.0
    boss = cylinder_y(
        p.motor_shaft_boss_diameter / 2.0,
        p.motor_shaft_boss_length,
        (drive_x, boss_y, p.wheel_center_z),
    )
    shaft_y = face_y + side_sign * p.motor_shaft_length / 2.0
    shaft = cylinder_y(
        p.motor_shaft_diameter / 2.0,
        p.motor_shaft_length,
        (drive_x, shaft_y, p.wheel_center_z),
    )
    return gearbox + can + encoder + lead_keepout + boss + shaft


def drive_motor_bracket_fit(p: Params, side_sign: int):
    """Official Pololu #1569 aluminum L bracket in installed orientation."""
    drive_x = p.wheel_x_positions[1]
    face_y = drive_motor_face_y(p, side_sign)
    face = rounded_panel_xz(
        p.motor_bracket_thickness,
        p.motor_bracket_face_size,
        p.motor_bracket_face_size,
        3.0,
        (
            drive_x,
            face_y + side_sign * p.motor_bracket_thickness / 2.0,
            p.wheel_center_z,
        ),
    )
    face = face - cylinder_y(
        p.motor_bracket_center_hole / 2.0,
        p.motor_bracket_thickness + 4.0,
        (drive_x, face_y, p.wheel_center_z),
    )
    for dx in (-p.motor_face_mount_spacing / 2.0, p.motor_face_mount_spacing / 2.0):
        face = face - cylinder_y(
            1.65,
            p.motor_bracket_thickness + 4.0,
            (drive_x + dx, face_y, p.wheel_center_z),
        )
    base = rounded_box(
        p.motor_bracket_base_width,
        p.motor_bracket_base_length,
        p.motor_bracket_thickness,
        1.0,
        (
            drive_x,
            face_y - side_sign * p.motor_bracket_base_length / 2.0,
            p.body_bottom
            + p.motor_bracket_spacer_height
            + p.motor_bracket_thickness / 2.0,
        ),
    )
    bend = cylinder_x(
        p.motor_bracket_thickness,
        p.motor_bracket_base_width,
        (
            drive_x,
            face_y + side_sign * p.motor_bracket_thickness / 2.0,
            p.body_bottom + p.motor_bracket_spacer_height + p.motor_bracket_thickness,
        ),
    )
    bracket = face + base + bend
    bracket = bracket - cylinder_y(
        p.motor_bracket_center_hole / 2.0,
        p.motor_bracket_thickness + 2.0,
        (
            drive_x,
            face_y + side_sign * p.motor_bracket_thickness / 2.0,
            p.wheel_center_z,
        ),
    )
    for dx, dz in (
        (-p.motor_face_mount_spacing / 2.0, 0.0),
        (p.motor_face_mount_spacing / 2.0, 0.0),
        (0.0, -p.motor_face_mount_spacing / 2.0),
        (0.0, p.motor_face_mount_spacing / 2.0),
    ):
        bracket = bracket - cylinder_y(
            3.3 / 2.0,
            p.motor_bracket_thickness + 2.0,
            (
                drive_x + dx,
                face_y + side_sign * p.motor_bracket_thickness / 2.0,
                p.wheel_center_z + dz,
            ),
        )
    for index in range(7):
        hole_y = face_y - side_sign * (
            p.motor_bracket_base_first_hole
            + index * p.motor_bracket_base_hole_pitch
        )
        bracket = bracket - cylinder_z(
            3.0 / 2.0,
            p.motor_bracket_thickness + 2.0,
            (
                drive_x,
                hole_y,
                p.body_bottom
                + p.motor_bracket_spacer_height
                + p.motor_bracket_thickness / 2.0,
            ),
        )
    return bracket


def drive_motor_hub_fit(p: Params, side_sign: int):
    """Official Pololu #1997 4 mm-shaft aluminum hub."""
    drive_x = p.wheel_x_positions[1]
    face_y = drive_motor_face_y(p, side_sign)
    center_y = face_y + side_sign * (
        p.motor_shaft_length - p.motor_hub_thickness / 2.0
    )
    hub = cylinder_y(
        p.motor_hub_diameter / 2.0,
        p.motor_hub_thickness,
        (drive_x, center_y, p.wheel_center_z),
    )
    hub = hub - cylinder_y(
        p.motor_shaft_diameter / 2.0,
        p.motor_hub_thickness + 2.0,
        (drive_x, center_y, p.wheel_center_z),
    )
    for dx, dz in drive_motor_hub_mount_positions(p):
        hub = hub - cylinder_y(
            p.motor_face_mount_thread / 2.0,
            p.motor_hub_thickness + 2.0,
            (drive_x + dx, center_y, p.wheel_center_z + dz),
        )
    return hub


def drive_motor_cable_service_fit(p: Params, side_sign: int):
    """Upward bend and connector corridor for the six 200 mm encoder leads."""
    drive_x = p.wheel_x_positions[1]
    inner_y = drive_motor_face_y(p, side_sign) - side_sign * p.motor_body_length
    return rounded_box(
        10.0,
        p.power_harness_channel_width - 1.0,
        18.0,
        2.0,
        (
            drive_x + 8.0,
            side_sign * p.power_harness_center_y,
            p.wheel_center_z + p.motor_body_diameter / 2.0 + 9.0,
        ),
    )


def front_idler_pods(p: Params):
    """Two-bearing front support pods for the non-driven concept wheels.

    Printed plastic locates the bearings; an 8 mm metal shaft, two 608-class
    bearings, washers, and positive shaft retention carry the actual load.
    """
    parts = {}
    center_x = p.wheel_x_positions[0]
    shell_center_z = mobility_pod_shell_center_z(p)
    for side, sign in (("left", -1), ("right", 1)):
        center_y = sign * (p.body_width / 2.0 - 21.0)
        pod = rounded_box(
            48.0,
            32.0,
            p.mobility_pod_shell_height,
            4.0,
            (center_x, center_y, shell_center_z),
        )
        flange = rounded_prism_xy(
            48.0,
            34.0,
            6.0,
            6.0,
            (center_x, center_y, p.body_bottom + 7.0),
            edge_radius=1.0,
        )
        pod = pod + flange
        bearing_radius = p.front_bearing_od / 2.0 + p.front_bearing_seat_clearance
        for offset in (-10.5, 10.5):
            pod = pod - cylinder_y(
                bearing_radius,
                p.front_bearing_width + 0.8,
                (center_x, center_y + sign * offset, p.wheel_center_z),
            )
        pod = pod - cylinder_y(
            p.front_axle_inner_spacer_od / 2.0
            + p.front_axle_spacer_clearance,
            42.0,
            (center_x, center_y, p.wheel_center_z),
        )
        retainers = {}
        for face_name, face_y, outward_sign in front_idler_retainer_interfaces(p, sign):
            # The inboard recess also clears the installed DIN 471 ring lugs
            # below the pod's mounting flange; the outer recess only needs to
            # seat the printed bearing-retainer ring.
            recess_depth = 3.2 if face_name == "inner" else 2.2
            recess_offset = 0.6 if face_name == "inner" else 1.1
            recess_center_y = face_y - outward_sign * recess_offset
            pod = pod - cylinder_y(
                15.7,
                recess_depth,
                (center_x, recess_center_y, p.wheel_center_z),
            )
            ring_center_y = face_y - outward_sign * 1.0
            ring = cylinder_y(
                15.5,
                2.0,
                (center_x, ring_center_y, p.wheel_center_z),
            )
            ring = ring - cylinder_y(
                8.5,
                4.0,
                (center_x, ring_center_y, p.wheel_center_z),
            )
            for dx in (-13.5, 13.5):
                pod = pod - cylinder_y(
                    p.insert_hole_m2_5 / 2.0,
                    10.0,
                    (center_x + dx, face_y, p.wheel_center_z),
                )
                ring = ring - cylinder_y(
                    p.m2_5_clearance_hole / 2.0,
                    5.0,
                    (center_x + dx, ring_center_y, p.wheel_center_z),
                )
            retainers[f"front_idler_retainer_{side}_{face_name}"] = ring
        for x, y in front_idler_mount_positions(p, sign):
            pod = pod - cylinder_z(
                p.m3_clearance_hole / 2.0,
                14.0,
                (x, y, p.body_bottom + 7.0),
            )
        parts[f"front_idler_pod_{side}"] = pod
        parts.update(retainers)
    return parts


def front_idler_fit_parts(p: Params, side_sign: int):
    """Metal-retained 608/shaft/spacer/#2693 stack for one front wheel."""
    side = "left" if side_sign < 0 else "right"
    center_x = p.wheel_x_positions[0]
    center_y = side_sign * (p.body_width / 2.0 - 21.0)
    core_center_y = wheel_center_y(p, side_sign) + side_sign * (
        (p.wheel_core_length - p.wheel_thickness) / 2.0
    )
    shaft_outer_y = core_center_y + side_sign * p.wheel_core_length / 2.0
    shaft_inner_y = shaft_outer_y - side_sign * p.front_axle_shaft_length
    shaft_center_y = (shaft_inner_y + shaft_outer_y) / 2.0
    fits = {}
    inner_face_y = center_y - side_sign * 16.0
    groove_outboard_y = inner_face_y
    groove_inboard_y = groove_outboard_y - side_sign * p.front_axle_ring_groove_width
    groove_center_y = (groove_inboard_y + groove_outboard_y) / 2.0
    shaft = cylinder_y(
        p.front_axle_shaft_diameter / 2.0,
        p.front_axle_shaft_length,
        (center_x, shaft_center_y, p.wheel_center_z),
    )
    groove_cut = cylinder_y(
        p.front_axle_shaft_diameter / 2.0 + 0.1,
        p.front_axle_ring_groove_width,
        (center_x, groove_center_y, p.wheel_center_z),
    ) - cylinder_y(
        p.front_axle_ring_groove_diameter / 2.0,
        p.front_axle_ring_groove_width + 0.2,
        (center_x, groove_center_y, p.wheel_center_z),
    )
    fits[f"fit_front_idler_{side}_shaft"] = shaft - groove_cut

    # Keep a 0.10 mm modeling gap at the pod face so the conservative lug
    # envelope does not numerically fuse to printed plastic. The real ring
    # floats within the 0.90 mm groove around its 0.75-0.80 mm thickness.
    ring_center_y = groove_outboard_y - side_sign * (
        p.front_axle_ring_thickness / 2.0 + 0.10
    )
    retaining_ring = cylinder_y(
        p.front_axle_ring_envelope_diameter / 2.0,
        p.front_axle_ring_thickness,
        (center_x, ring_center_y, p.wheel_center_z),
    ) - cylinder_y(
        p.front_axle_ring_groove_diameter / 2.0,
        p.front_axle_ring_thickness + 0.2,
        (center_x, ring_center_y, p.wheel_center_z),
    )
    fits[f"fit_front_idler_{side}_retaining_ring"] = retaining_ring

    bearing_inner_y = center_y - side_sign * 10.5
    bearing_outer_y = center_y + side_sign * 10.5
    washer_center_y = inner_face_y + side_sign * (
        p.front_axle_inner_washer_width / 2.0
    )
    washer = cylinder_y(
        p.front_axle_inner_washer_diameter / 2.0,
        p.front_axle_inner_washer_width,
        (center_x, washer_center_y, p.wheel_center_z),
    )
    fits[f"fit_front_idler_{side}_inner_washer"] = washer - cylinder_y(
        p.front_axle_shaft_diameter / 2.0,
        p.front_axle_inner_washer_width + 2.0,
        (center_x, washer_center_y, p.wheel_center_z),
    )

    for position, bearing_y in (
        ("inner", bearing_inner_y),
        ("outer", bearing_outer_y),
    ):
        bearing = cylinder_y(
            p.front_bearing_od / 2.0,
            p.front_bearing_width,
            (center_x, bearing_y, p.wheel_center_z),
        )
        fits[f"fit_front_idler_{side}_bearing_{position}"] = bearing - cylinder_y(
            p.front_bearing_id / 2.0,
            p.front_bearing_width + 2.0,
            (center_x, bearing_y, p.wheel_center_z),
        )

    inner_spacer_y = (bearing_inner_y + bearing_outer_y) / 2.0
    inner_spacer = cylinder_y(
        p.front_axle_inner_spacer_od / 2.0,
        p.front_axle_inner_spacer_length,
        (center_x, inner_spacer_y, p.wheel_center_z),
    )
    fits[f"fit_front_idler_{side}_inner_spacer"] = inner_spacer - cylinder_y(
        p.front_axle_shaft_diameter / 2.0,
        p.front_axle_inner_spacer_length + 2.0,
        (center_x, inner_spacer_y, p.wheel_center_z),
    )

    hub_center_y = shaft_outer_y - side_sign * p.front_hub_length / 2.0
    hub = cylinder_y(
        p.front_hub_diameter / 2.0,
        p.front_hub_length,
        (center_x, hub_center_y, p.wheel_center_z),
    )
    hub = hub - cylinder_y(
        p.front_axle_shaft_diameter / 2.0,
        p.front_hub_length + 2.0,
        (center_x, hub_center_y, p.wheel_center_z),
    )
    for dx, dz in front_idler_hub_mount_positions(p):
        hub = hub - cylinder_y(
            p.front_hub_mount_thread / 2.0,
            p.front_hub_length + 2.0,
            (center_x + dx, hub_center_y, p.wheel_center_z + dz),
        )
    fits[f"fit_front_idler_{side}_hub"] = hub

    outer_bearing_outboard_face = bearing_outer_y + side_sign * (
        p.front_bearing_width / 2.0
    )
    hub_inboard_face = hub_center_y - side_sign * p.front_hub_length / 2.0
    outer_spacer_y = (outer_bearing_outboard_face + hub_inboard_face) / 2.0
    outer_spacer = cylinder_y(
        p.front_axle_outer_spacer_od / 2.0,
        p.front_axle_outer_spacer_length,
        (center_x, outer_spacer_y, p.wheel_center_z),
    )
    fits[f"fit_front_idler_{side}_outer_spacer"] = outer_spacer - cylinder_y(
        p.front_axle_shaft_diameter / 2.0,
        p.front_axle_outer_spacer_length + 2.0,
        (center_x, outer_spacer_y, p.wheel_center_z),
    )
    return fits


def side_fairings(p: Params):
    """Flush scalloped side skins around the two wheel arches.

    The large center opening exposes the molded shell directly, removing the
    old slab-like overlay. A narrow upper bridge keeps each side a single
    printable/serviceable part and carries four high screws. The exterior face
    shares the body-width datum while a shallow shell recess registers it.
    """
    parts = {}
    for side, sign in (("left", -1), ("right", 1)):
        panel_y = side_fairing_center_y(p, sign)
        panel = side_fairing_profile(
            p,
            sign,
            p.side_fairing_thickness,
            panel_y,
        )
        for x, z in fairing_mount_positions():
            panel = panel - cylinder_y(
                p.m3_clearance_hole / 2.0,
                12.0,
                (x, panel_y, z),
            )
        for x, z in side_vent_layout():
            panel = panel - rounded_panel_xz(
                12.0,
                28.0,
                2.4,
                1.1,
                (x, panel_y, z),
            )
        panel = panel - rounded_panel_xz(
            12.0,
            20.0,
            14.0,
            4.0,
            (p.side_tof_center_x, panel_y, 96.0),
        )
        parts[f"side_fairing_{side}"] = panel
    return parts


def pan_servo_fit(p: Params):
    """Drawing-backed Hitec D85MG in the vertical pan orientation."""
    mount_z = pan_servo_mount_plane_z(p)
    body_x = servo_body_center_x(p, p.neck_x)
    body_center_z = mount_z + (
        p.servo_body_height / 2.0 - p.servo_mount_plane_from_bottom
    )
    body = rounded_box(
        p.servo_body_length,
        p.servo_body_width,
        p.servo_body_height,
        1.5,
        (body_x, 0.0, body_center_z),
    )
    flange = rounded_box(
        p.servo_flange_length,
        p.servo_body_width,
        p.servo_flange_thickness,
        0.9,
        (body_x, 0.0, mount_z),
    )
    case_top = body_center_z + p.servo_body_height / 2.0
    collar = cylinder_z(
        p.servo_output_collar_diameter / 2.0,
        2.5,
        (p.neck_x, 0.0, case_top + 1.25),
    )
    spline = cylinder_z(
        p.servo_output_diameter / 2.0,
        p.servo_output_stack_height - 2.5,
        (
            p.neck_x,
            0.0,
            case_top + 2.5 + (p.servo_output_stack_height - 2.5) / 2.0,
        ),
    )
    servo = body + flange + collar + spline
    for x, y in pan_servo_mount_positions(p):
        servo = servo - cylinder_z(
            p.servo_mount_hole / 2.0,
            p.servo_flange_thickness + 2.0,
            (x, y, mount_z),
        )
    return servo


def pan_bearing_fit(p: Params):
    """Koyo/JTEKT 6807-2RS thin-section pan bearing, 35 x 47 x 7 mm."""
    bearing = cylinder_z(
        p.pan_bearing_od / 2.0,
        p.pan_bearing_width,
        (p.neck_x, 0.0, p.pan_bearing_center_z),
    )
    return bearing - cylinder_z(
        p.pan_bearing_id / 2.0,
        p.pan_bearing_width + 2.0,
        (p.neck_x, 0.0, p.pan_bearing_center_z),
    )


def pan_servo_horn_fit(p: Params):
    """Hitec R-ML24 aluminum horn coupling the D85MG to the neck."""
    horn_z = pan_servo_horn_center_z(p)
    hub = cylinder_z(
        p.servo_horn_hub_diameter / 2.0,
        p.servo_horn_overall_thickness,
        (p.neck_x, 0.0, horn_z),
    )
    arm = rounded_box(
        p.servo_horn_arm_length,
        p.servo_horn_arm_width,
        p.servo_horn_arm_thickness,
        1.2,
        (p.neck_x - p.servo_horn_arm_length / 2.0, 0.0, horn_z),
    )
    horn = hub + arm
    horn = horn - cylinder_z(
        p.servo_output_diameter / 2.0,
        p.servo_horn_overall_thickness + 2.0,
        (p.neck_x, 0.0, horn_z),
    )
    for x, y in pan_servo_horn_mount_positions(p):
        horn = horn - cylinder_z(
            p.servo_horn_thread / 2.0,
            p.servo_horn_overall_thickness + 2.0,
            (x, y, horn_z),
        )
    return horn


def tilt_servo_fit(p: Params):
    """Drawing-backed Hitec D85MG in the horizontal tilt orientation."""
    mount_y = tilt_servo_mount_plane_y(p)
    body_x = servo_body_center_x(p, p.head_tilt_axis_x)
    body_center_y = mount_y + (
        p.servo_body_height / 2.0 - p.servo_mount_plane_from_bottom
    )
    body = rounded_box(
        p.servo_body_length,
        p.servo_body_height,
        p.servo_body_width,
        1.5,
        (body_x, body_center_y, p.head_tilt_axis_z),
    )
    flange = rounded_box(
        p.servo_flange_length,
        p.servo_flange_thickness,
        p.servo_body_width,
        0.9,
        (body_x, mount_y, p.head_tilt_axis_z),
    )
    case_top_y = body_center_y + p.servo_body_height / 2.0
    collar = cylinder_y(
        p.servo_output_collar_diameter / 2.0,
        2.5,
        (p.head_tilt_axis_x, case_top_y + 1.25, p.head_tilt_axis_z),
    )
    spline = cylinder_y(
        p.servo_output_diameter / 2.0,
        p.servo_output_stack_height - 2.5,
        (
            p.head_tilt_axis_x,
            case_top_y + 2.5 + (p.servo_output_stack_height - 2.5) / 2.0,
            p.head_tilt_axis_z,
        ),
    )
    servo = body + flange + collar + spline
    for x, z in tilt_servo_mount_positions(p):
        servo = servo - cylinder_y(
            p.servo_mount_hole / 2.0,
            p.servo_flange_thickness + 2.0,
            (x, mount_y, z),
        )
    return servo


def tilt_servo_horn_fit(p: Params):
    """Hitec R-ML24 aluminum horn between spline and drive adapter."""
    horn_y = tilt_servo_horn_center_y(p)
    hub = cylinder_y(
        p.servo_horn_hub_diameter / 2.0,
        p.servo_horn_overall_thickness,
        (p.head_tilt_axis_x, horn_y, p.head_tilt_axis_z),
    )
    arm = rounded_box(
        p.servo_horn_arm_length,
        p.servo_horn_arm_thickness,
        p.servo_horn_arm_width,
        1.2,
        (
            p.head_tilt_axis_x - p.servo_horn_arm_length / 2.0,
            horn_y,
            p.head_tilt_axis_z,
        ),
    )
    horn = hub + arm
    horn = horn - cylinder_y(
        p.servo_output_diameter / 2.0,
        p.servo_horn_overall_thickness + 2.0,
        (p.head_tilt_axis_x, horn_y, p.head_tilt_axis_z),
    )
    for x, z in head_tilt_horn_mount_positions(p):
        horn = horn - cylinder_y(
            p.servo_horn_thread / 2.0,
            p.servo_horn_overall_thickness + 2.0,
            (x, horn_y, z),
        )
    return horn


def tilt_passive_bushing_fit(p: Params):
    """MF84ZZ 4 x 8 x 3 mm flanged shielded bearing."""
    bushing_y = head_tilt_passive_bushing_center_y(p)
    bearing = cylinder_y(
        p.head_tilt_passive_bushing_od / 2.0,
        p.head_tilt_passive_bushing_length,
        (p.head_tilt_axis_x, bushing_y, p.head_tilt_axis_z),
    )
    bearing = bearing - cylinder_y(
        p.head_tilt_passive_bushing_id / 2.0,
        p.head_tilt_passive_bushing_length + 2.0,
        (p.head_tilt_axis_x, bushing_y, p.head_tilt_axis_z),
    )
    flange_y = (
        bushing_y
        - p.head_tilt_passive_bushing_length / 2.0
        - p.head_tilt_passive_bushing_flange_thickness / 2.0
    )
    flange = cylinder_y(
        p.head_tilt_passive_bushing_flange_od / 2.0,
        p.head_tilt_passive_bushing_flange_thickness,
        (p.head_tilt_axis_x, flange_y, p.head_tilt_axis_z),
    )
    flange = flange - cylinder_y(
        p.head_tilt_passive_bushing_id / 2.0,
        p.head_tilt_passive_bushing_flange_thickness + 2.0,
        (p.head_tilt_axis_x, flange_y, p.head_tilt_axis_z),
    )
    return bearing + flange


def tilt_shoulder_bolt_fit(p: Params):
    """McMaster 92981A143 4 mm shoulder, 12 mm long, M3 thread."""
    shell_outer_y = -p.head_width / 2.0
    shoulder_start_y = shell_outer_y + 2.0
    shoulder_end_y = shoulder_start_y + p.head_tilt_shoulder_length
    shaft = cylinder_y(
        p.head_tilt_passive_bushing_id / 2.0,
        p.head_tilt_shoulder_length,
        (
            p.head_tilt_axis_x,
            (shoulder_start_y + shoulder_end_y) / 2.0,
            p.head_tilt_axis_z,
        ),
    )
    thread_end_y = shoulder_end_y + p.head_tilt_shoulder_thread_length
    thread = cylinder_y(
        1.5,
        p.head_tilt_shoulder_thread_length,
        (
            p.head_tilt_axis_x,
            (shoulder_end_y + thread_end_y) / 2.0,
            p.head_tilt_axis_z,
        ),
    )
    head_y = shoulder_start_y - p.head_tilt_shoulder_head_height / 2.0
    cap = cylinder_y(
        p.head_tilt_shoulder_head_diameter / 2.0,
        p.head_tilt_shoulder_head_height,
        (p.head_tilt_axis_x, head_y, p.head_tilt_axis_z),
    )
    return shaft + thread + cap


def servo_cable_corridor(p: Params):
    """Bent review envelope for wiring around the pan output shaft."""
    # The 15-pin camera ribbon passes as a flat 13 x 1.5 mm strip through the
    # positive-X crescent beside the one-sided pan horn, then relaxes into the
    # central 14 mm bundle corridor above the bearing.
    lower = rounded_box(
        1.5,
        13.0,
        13.0,
        0.6,
        (p.neck_x + 6.8, 0.0, p.neck_bottom + 1.0),
    )
    bend = rounded_box(
        8.0,
        13.0,
        6.0,
        2.0,
        (p.neck_x + 3.4, 0.0, p.neck_bottom + 7.5),
    )
    upper_bottom = p.neck_bottom + 5.5
    upper_top = p.head_tilt_axis_z - 15.0
    upper = cylinder_z(
        7.0,
        upper_top - upper_bottom,
        (p.neck_x, 0.0, (upper_bottom + upper_top) / 2.0),
    )
    return lower + bend + upper


def head_motion_mounts(p: Params):
    """Printable pan plate and internal head-tilt yoke."""
    parts = {}

    top_inner_z = body_inner_roof_z(p)
    pan_plate_z = top_inner_z - 12.0
    pan_body_x = servo_body_center_x(p, p.neck_x)
    pan_plate = rounded_prism_xy(56.0, 56.0, 4.0, 7.0, (p.neck_x, 0.0, pan_plate_z))
    pan_plate = pan_plate - rounded_box(
        p.servo_body_length + 1.2,
        p.servo_body_width + 1.2,
        10.0,
        2.0,
        (pan_body_x, 0.0, pan_plate_z),
    )
    for dx, dy in ((-24, -24), (-24, 24), (24, -24), (24, 24)):
        pan_plate = pan_plate - cylinder_z(
            p.m3_clearance_hole / 2.0,
            10.0,
            (p.neck_x + dx, dy, pan_plate_z),
        )
    for x, y in pan_servo_mount_positions(p):
        pan_plate = pan_plate - cylinder_z(
            p.m3_clearance_hole / 2.0,
            10.0,
            (x, y, pan_plate_z),
        )
    parts["pan_servo_mount"] = pan_plate

    head_bottom = p.head_center_z - p.head_height / 2.0
    yoke_y = head_tilt_yoke_center_y(p)
    yoke_width = 2.0 * (yoke_y + 2.5)
    yoke = rounded_box(
        42.0,
        yoke_width,
        5.0,
        2.0,
        (p.neck_x + 4.0, 0.0, head_bottom + 8.0),
    )
    for sign in (-1, 1):
        yoke = yoke + rounded_box(
            30.0,
            5.0,
            46.0,
            2.0,
            (p.head_tilt_axis_x, sign * yoke_y, p.head_tilt_axis_z - 3.0),
        )

    # The D85MG mounting ears sit 9.8 mm behind its output-side case face, so
    # a dedicated internal panel carries the two M3 through-bolts. Top and
    # bottom rails bridge that panel to the active yoke upright while keeping
    # the complete 29 x 13 mm case service opening clear.
    tilt_mount_y = tilt_servo_mount_plane_y(p)
    tilt_body_x = servo_body_center_x(p, p.head_tilt_axis_x)
    support_outer_y = tilt_mount_y - p.servo_flange_thickness / 2.0
    support_depth = 4.0
    support_y = support_outer_y - support_depth / 2.0
    servo_support = rounded_box(
        p.servo_flange_length + 4.0,
        support_depth,
        p.servo_body_width + 6.0,
        1.4,
        (tilt_body_x, support_y, p.head_tilt_axis_z),
    )
    bridge_inner_y = support_outer_y
    bridge_outer_y = yoke_y - 2.5
    bridge_y = (bridge_inner_y + bridge_outer_y) / 2.0
    bridge_depth = bridge_outer_y - bridge_inner_y
    for z_sign in (-1.0, 1.0):
        servo_support = servo_support + rounded_box(
            p.servo_flange_length + 4.0,
            bridge_depth,
            3.0,
            1.0,
            (
                tilt_body_x,
                bridge_y,
                p.head_tilt_axis_z + z_sign * (p.servo_body_width / 2.0 + 1.5),
            ),
        )
    servo_case_clearance = rounded_box(
        p.servo_body_length + 0.8,
        p.servo_body_height + 2.0,
        p.servo_body_width + 0.8,
        1.8,
        (
            tilt_body_x,
            tilt_mount_y
            + (p.servo_body_height / 2.0 - p.servo_mount_plane_from_bottom),
            p.head_tilt_axis_z,
        ),
    )
    servo_support = servo_support - servo_case_clearance
    for x, z in tilt_servo_mount_positions(p):
        servo_support = servo_support - cylinder_y(
            p.m3_clearance_hole / 2.0,
            support_depth + 4.0,
            (x, support_y, z),
        )
    yoke = yoke + servo_support
    yoke = yoke - servo_case_clearance
    yoke = yoke - cylinder_z(8.5, 12.0, (p.neck_x, 0.0, head_bottom + 8.0))
    for x, y in neck_yoke_mount_positions(p):
        yoke = yoke - cylinder_z(
            p.m2_5_clearance_hole / 2.0,
            10.0,
            (x, y, head_bottom + 8.0),
        )
    # The active side clears only the servo shaft. The passive side receives a
    # blind M4 insert for a purchased shoulder bolt instead of sharing one
    # unsupported through-hole across the entire head.
    active_boss = cylinder_y(
        9.5,
        2.0,
        (p.head_tilt_axis_x, yoke_y + 2.7, p.head_tilt_axis_z),
    )
    yoke = yoke + active_boss
    yoke = yoke - rounded_box(
        p.servo_horn_arm_length + 1.0,
        4.0,
        p.servo_horn_arm_width + 0.6,
        1.2,
        (
            p.head_tilt_axis_x - p.servo_horn_arm_length / 2.0,
            yoke_y + 2.7,
            p.head_tilt_axis_z,
        ),
    )
    yoke = yoke - cylinder_y(
        8.0,
        10.0,
        (p.head_tilt_axis_x, yoke_y, p.head_tilt_axis_z),
    )
    horn_sweep = cylinder_y(
        p.servo_horn_hub_diameter / 2.0 + 0.3,
        p.servo_horn_overall_thickness + 0.6,
        (p.head_tilt_axis_x, tilt_servo_horn_center_y(p), p.head_tilt_axis_z),
    )
    horn_sweep = horn_sweep + rounded_box(
        p.servo_horn_arm_length + 0.6,
        p.servo_horn_overall_thickness + 0.6,
        p.servo_horn_arm_width + 0.6,
        1.3,
        (
            p.head_tilt_axis_x - p.servo_horn_arm_length / 2.0,
            tilt_servo_horn_center_y(p),
            p.head_tilt_axis_z,
        ),
    )
    tilt_axis = Axis(
        (p.head_tilt_axis_x, 0.0, p.head_tilt_axis_z),
        (0.0, 1.0, 0.0),
    )
    for angle in range(-22, 23, 2):
        yoke = yoke - horn_sweep.rotate(tilt_axis, float(angle))
    passive_boss = cylinder_y(
        6.0,
        5.0,
        (p.head_tilt_axis_x, -yoke_y, p.head_tilt_axis_z),
    )
    yoke = yoke + passive_boss
    yoke = yoke - cylinder_y(
        p.head_tilt_yoke_insert_hole / 2.0,
        4.6,
        (p.head_tilt_axis_x, -(yoke_y + 0.2), p.head_tilt_axis_z),
    )
    parts["head_tilt_yoke"] = yoke

    adapter_mounts = head_tilt_adapter_mount_positions(p)
    passive_y = head_tilt_adapter_center_y(p, -1)
    passive = cylinder_y(
        p.head_tilt_adapter_radius,
        p.head_tilt_adapter_thickness,
        (p.head_tilt_axis_x, passive_y, p.head_tilt_axis_z),
    )
    passive = passive - cylinder_y(
        p.head_tilt_passive_bushing_od / 2.0 + 0.15,
        p.head_tilt_adapter_thickness + 4.0,
        (p.head_tilt_axis_x, passive_y, p.head_tilt_axis_z),
    )
    passive_flange_y = (
        passive_y
        - p.head_tilt_passive_bushing_length / 2.0
        - p.head_tilt_passive_bushing_flange_thickness / 2.0
    )
    passive = passive - cylinder_y(
        p.head_tilt_passive_bushing_flange_od / 2.0 + 0.15,
        p.head_tilt_passive_bushing_flange_thickness + 0.3,
        (p.head_tilt_axis_x, passive_flange_y, p.head_tilt_axis_z),
    )
    for x, z in adapter_mounts:
        passive = passive - cylinder_y(
            p.m2_5_clearance_hole / 2.0,
            p.head_tilt_adapter_thickness + 4.0,
            (x, passive_y, z),
        )
    parts["head_tilt_passive_cartridge"] = passive

    drive_y = head_tilt_adapter_center_y(p, 1)
    drive = cylinder_y(
        p.head_tilt_adapter_radius,
        p.head_tilt_adapter_thickness,
        (p.head_tilt_axis_x, drive_y, p.head_tilt_axis_z),
    )
    drive = drive - cylinder_y(
        p.servo_output_diameter / 2.0 + 0.4,
        p.head_tilt_adapter_thickness + 4.0,
        (p.head_tilt_axis_x, drive_y, p.head_tilt_axis_z),
    )
    for x, z in adapter_mounts:
        drive = drive - cylinder_y(
            p.m2_5_clearance_hole / 2.0,
            p.head_tilt_adapter_thickness + 4.0,
            (x, drive_y, z),
        )
    for x, z in head_tilt_horn_mount_positions(p):
        drive = drive - cylinder_y(
            1.1,
            p.head_tilt_adapter_thickness + 4.0,
            (x, drive_y, z),
        )
    parts["head_tilt_drive_adapter"] = drive
    return parts


def head_parts(p: Params):
    parts = {}
    lid_top = p.body_bottom + p.body_height + 5.0
    visible_collar = cylinder_z(
        p.neck_collar_outer_diameter / 2.0,
        6.0,
        (p.neck_x, 0.0, lid_top + 3.0),
    )
    visible_collar = visible_collar - cylinder_z(
        p.neck_collar_inner_diameter / 2.0,
        10.0,
        (p.neck_x, 0.0, lid_top + 3.0),
    )

    # A keyed fixed carrier passes through the 53 mm roof/lid opening and
    # press-seats a 6807-2RS bearing. The visible 60 mm ring stays faithful to
    # the concept while the hidden barrel transfers the head's radial/axial
    # load into the body instead of the D85MG output spline.
    carrier_bottom = (
        p.pan_bearing_center_z
        - p.pan_bearing_width / 2.0
        - p.pan_bearing_retainer_thickness
    )
    carrier_top = lid_top
    carrier = cylinder_z(
        p.pan_bearing_carrier_od / 2.0,
        carrier_top - carrier_bottom,
        (p.neck_x, 0.0, (carrier_bottom + carrier_top) / 2.0),
    )
    for x, y in pan_bearing_key_positions(p):
        carrier = carrier + rounded_box(
            p.pan_bearing_key_length,
            p.pan_bearing_key_width,
            carrier_top - carrier_bottom,
            0.8,
            (x, y, (carrier_bottom + carrier_top) / 2.0),
        )
    bearing_top = p.pan_bearing_center_z + p.pan_bearing_width / 2.0
    bearing_pocket = cylinder_z(
        p.pan_bearing_od / 2.0 + p.pan_bearing_seat_clearance,
        bearing_top - carrier_bottom + 0.2,
        (p.neck_x, 0.0, (carrier_bottom + bearing_top) / 2.0 - 0.1),
    )
    carrier = carrier - bearing_pocket
    outer_shoulder = cylinder_z(
        p.pan_bearing_carrier_od / 2.0,
        0.8,
        (p.neck_x, 0.0, bearing_top + 0.4),
    )
    outer_shoulder = outer_shoulder - cylinder_z(
        p.pan_bearing_outer_shoulder_bore / 2.0,
        2.0,
        (p.neck_x, 0.0, bearing_top + 0.4),
    )
    collar = visible_collar + carrier + outer_shoulder
    collar = collar - cylinder_z(
        p.pan_bearing_outer_shoulder_bore / 2.0,
        lid_top + 6.5 - bearing_top,
        (
            p.neck_x,
            0.0,
            (bearing_top + lid_top + 6.5) / 2.0,
        ),
    )

    # The rotating neck uses a 34.8 mm printed journal through the bearing, a
    # 37.5 mm upper shoulder on the inner race, and the original hourglass
    # silhouette above the dark collar. A separate four-screw lower retainer
    # captures the inner race and carries the aluminum pan horn.
    bearing_bottom = p.pan_bearing_center_z - p.pan_bearing_width / 2.0
    journal_radius = (p.pan_bearing_id - p.pan_bearing_journal_clearance) / 2.0
    journal = cylinder_z(
        journal_radius,
        p.pan_bearing_width,
        (p.neck_x, 0.0, p.pan_bearing_center_z),
    )
    shoulder = cylinder_z(
        p.pan_bearing_shoulder_od / 2.0,
        1.0,
        (p.neck_x, 0.0, bearing_top + 0.5),
    )
    hidden_transition = Cone(
        p.pan_bearing_shoulder_od / 2.0,
        p.neck_bottom_radius,
        p.neck_visible_base_z - bearing_top,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    hidden_transition = moved(hidden_transition, (p.neck_x, 0.0, bearing_top))
    visible_lower = Cone(
        p.neck_bottom_radius,
        p.neck_waist_radius,
        p.neck_waist_z - p.neck_visible_base_z,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    visible_lower = moved(visible_lower, (p.neck_x, 0.0, p.neck_visible_base_z))
    visible_upper = Cone(
        p.neck_waist_radius,
        p.neck_top_radius,
        p.neck_bottom + p.neck_height - p.neck_waist_z,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    visible_upper = moved(visible_upper, (p.neck_x, 0.0, p.neck_waist_z))
    neck = journal + shoulder + hidden_transition + visible_lower + visible_upper
    neck = neck - cylinder_z(
        10.0,
        p.neck_height + 4.0,
        (
            p.neck_x,
            0.0,
            p.neck_bottom + p.neck_height / 2.0,
        ),
    )
    for x, y in pan_bearing_retainer_mount_positions(p):
        neck = neck - cylinder_z(
            p.insert_hole_m2_5 / 2.0,
            6.0,
            (x, y, bearing_bottom + 3.0),
        )

    pan_retainer = cylinder_z(
        p.pan_bearing_shoulder_od / 2.0,
        p.pan_bearing_retainer_thickness,
        (
            p.neck_x,
            0.0,
            bearing_bottom - p.pan_bearing_retainer_thickness / 2.0,
        ),
    )
    pan_retainer = pan_retainer - cylinder_z(
        10.2,
        p.pan_bearing_retainer_thickness + 2.0,
        (
            p.neck_x,
            0.0,
            bearing_bottom - p.pan_bearing_retainer_thickness / 2.0,
        ),
    )
    for x, y in pan_bearing_retainer_mount_positions(p):
        pan_retainer = pan_retainer - cylinder_z(
            p.m2_5_clearance_hole / 2.0,
            p.pan_bearing_retainer_thickness + 2.0,
            (
                x,
                y,
                bearing_bottom - p.pan_bearing_retainer_thickness / 2.0,
            ),
        )
    for x, y in pan_servo_horn_mount_positions(p):
        pan_retainer = pan_retainer - cylinder_z(
            p.servo_horn_thread / 2.0 + 0.15,
            p.pan_bearing_retainer_thickness + 2.0,
            (
                x,
                y,
                bearing_bottom - p.pan_bearing_retainer_thickness / 2.0,
            ),
        )

    neck_top = p.neck_bottom + p.neck_height
    yoke_flange = cylinder_z(
        p.neck_yoke_flange_radius,
        p.neck_yoke_flange_thickness,
        (
            p.neck_x,
            0.0,
            neck_top - p.neck_yoke_flange_thickness / 2.0,
        ),
    )
    yoke_flange = yoke_flange - cylinder_z(
        p.neck_top_radius - p.neck_wall,
        p.neck_yoke_flange_thickness + 2.0,
        (
            p.neck_x,
            0.0,
            neck_top - p.neck_yoke_flange_thickness / 2.0,
        ),
    )
    neck = neck + yoke_flange
    for x, y in neck_yoke_mount_positions(p):
        neck = neck - cylinder_z(
            p.insert_hole_m2_5 / 2.0,
            p.neck_yoke_insert_depth + 0.2,
            (
                x,
                y,
                neck_top - p.neck_yoke_insert_depth / 2.0 + 0.1,
            ),
        )

    head_center = (p.head_center_x, 0, p.head_center_z)
    head_outer = rounded_box(
        p.head_depth,
        p.head_width,
        p.head_height,
        18,
        head_center,
    )
    # Open the rear for servicing while retaining a solid front face wall.
    inner = rounded_box(
        p.head_depth + 8,
        p.head_width - 8,
        p.head_height - 8,
        12,
        (p.head_center_x + 6, 0, p.head_center_z),
    )
    head = head_outer - inner

    # Bottom clearance lets the fixed yoke enter the moving head and leaves
    # room for the requested pitch range around the horizontal pivot axis.
    head_bottom = p.head_center_z - p.head_height / 2.0
    head = head - rounded_box(
        92.0,
        p.head_width - 16.0,
        20.0,
        8.0,
        (p.head_center_x + 9.0, 0.0, head_bottom + 4.0),
    )
    # The MF84ZZ bearing seats in the internal passive cartridge. A recessed
    # service bore through the left wall admits the 4 mm shoulder screw while
    # the active servo shaft remains completely hidden inside the right wall.
    passive_bushing_y = head_tilt_passive_bushing_center_y(p)
    head = head - cylinder_y(
        p.head_tilt_passive_bushing_id / 2.0 + 0.25,
        10.0,
        (p.head_tilt_axis_x, -66.0, p.head_tilt_axis_z),
    )
    head = head - cylinder_y(
        p.head_tilt_shoulder_head_diameter / 2.0 + 0.2,
        3.0,
        (p.head_tilt_axis_x, -69.5, p.head_tilt_axis_z),
    )

    # Three blind M2.5 bosses per side retain the moving passive cartridge and
    # active drive adapter against the head's inner sidewalls.
    for side_sign in (-1, 1):
        adapter_y = head_tilt_adapter_center_y(p, side_sign)
        head = head - cylinder_y(
            p.head_tilt_adapter_radius + 0.3,
            p.head_tilt_adapter_thickness + 0.4,
            (p.head_tilt_axis_x, adapter_y, p.head_tilt_axis_z),
        )
        adapter_outer_y = (
            abs(adapter_y) + p.head_tilt_adapter_thickness / 2.0
        )
        boss_inner_y = adapter_outer_y + 0.3
        boss_outer_y = p.head_width / 2.0 - 3.0
        boss_length = boss_outer_y - boss_inner_y
        boss_y = side_sign * ((boss_inner_y + boss_outer_y) / 2.0)
        pocket_length = 4.0
        pocket_y = side_sign * (boss_outer_y - pocket_length / 2.0)
        for x, z in head_tilt_adapter_mount_positions(p):
            head = head + cylinder_y(
                p.head_tilt_shell_boss_radius,
                boss_length,
                (x, boss_y, z),
            )
            head = head - cylinder_y(
                p.insert_hole_m2_5 / 2.0,
                pocket_length,
                (x, pocket_y, z),
            )

    # Leave a real optical path through the head shell for the camera module;
    # the printed face and rings frame the purchased lens rather than blocking
    # it with a decorative solid disk.
    camera_aperture = cylinder_x(
        p.head_camera_aperture_radius,
        p.head_depth + 14.0,
        (p.head_center_x, 0.0, p.head_center_z - 1.0),
    )
    head = head - camera_aperture

    head_front_x = p.head_center_x - p.head_depth / 2.0
    _camera_fit_x, camera_board_z, camera_carrier_x = camera_reference(p)
    post_front = head_front_x + 2.0
    post_rear = camera_carrier_x - 1.5
    post_x = (post_front + post_rear) / 2.0
    for y in (-22.0, 22.0):
        for z in (camera_board_z - 15.0, camera_board_z + 15.0):
            post = cylinder_x(4.5, post_rear - post_front, (post_x, y, z))
            head = head + post
            # Blind insert pocket opens from the carrier side and leaves the
            # exterior front wall intact behind the black faceplate.
            head = head - cylinder_x(
                p.insert_hole_m3 / 2.0,
                10.0,
                (camera_carrier_x - 6.0, y, z),
            )

    eye_z = p.head_center_z + p.head_eye_center_z_offset
    eye_carriers = []
    for y in (-42.0, 42.0):
        eye_aperture = rounded_panel_yz(
            16.0,
            p.head_eye_aperture_width,
            p.head_eye_aperture_height,
            5.5,
            (head_front_x + 2.0, y, eye_z),
        )
        head = head - eye_aperture
        # A larger pocket opens only from inside the head. This preserves the
        # narrow concept-facing light aperture while allowing a replaceable LED
        # board and carrier to remain larger than the visible diffuser.
        eye_board_pocket = rounded_panel_yz(
            12.0,
            p.head_eye_carrier_opening_width,
            p.head_eye_carrier_opening_height,
            5.0,
            (head_front_x + 9.0, y, eye_z),
        )
        head = head - eye_board_pocket
        eye_pcb_front_x = head_neopixel_pcb_front_x(p)
        carrier_x = (
            eye_pcb_front_x
            + p.neopixel_pcb_thickness
            + p.neopixel_connector_rear_protrusion
            + p.neopixel_carrier_component_clearance
            + p.neopixel_carrier_depth / 2.0
        )
        post_front = head_front_x + 2.0
        post_rear = (
            carrier_x
            - p.neopixel_carrier_depth / 2.0
            - p.head_eye_carrier_mount_gap
        )
        for post_y in (
            y - p.head_eye_carrier_hole_offset,
            y + p.head_eye_carrier_hole_offset,
        ):
            post = cylinder_x(
                3.0,
                post_rear - post_front,
                ((post_front + post_rear) / 2.0, post_y, eye_z),
            )
            head = head + post
            head = head - cylinder_x(
                p.insert_hole_m2_5 / 2.0,
                5.0,
                (post_rear - 2.0, post_y, eye_z),
            )
        eye_carriers.append(
            led_carrier_frame(
                p,
                (carrier_x, y, eye_z),
                p.head_eye_carrier_width,
                p.head_eye_carrier_height,
                p.head_eye_carrier_opening_width,
                p.head_eye_carrier_opening_height,
                p.head_eye_carrier_hole_offset,
                insert_holes=False,
                hole_axis="y",
                pcb_front_x=eye_pcb_front_x,
                board_rotate_90=True,
            )
        )

    # The concept's black face is inset inside a visible cream appliance-like
    # bezel. Integrate the frame into the structural head shell so it prints
    # with the shell, while keeping the black panel independently removable.
    bezel_x = head_front_x - 3.0
    bezel_outer = rounded_panel_yz(
        p.head_bezel_depth,
        p.head_bezel_outer_width,
        p.head_bezel_outer_height,
        16.0,
        (bezel_x, 0.0, p.head_center_z),
    )
    bezel_opening = rounded_panel_yz(
        p.head_bezel_depth + 4.0,
        p.head_bezel_opening_width,
        p.head_bezel_opening_height,
        11.0,
        (bezel_x, 0.0, p.head_center_z),
    )
    head = head + (bezel_outer - bezel_opening)

    # Two concealed side roots carry the projecting cream bezel into the head
    # sidewalls. The old larger shell happened to fuse by edge tangency; these
    # deliberate overlaps preserve a one-solid load path as the capsule gets
    # shorter and narrower.
    bezel_rear_x = bezel_x + p.head_bezel_depth / 2.0
    root_front_x = bezel_rear_x - 0.8
    root_rear_x = head_front_x + 10.0
    root_length = root_rear_x - root_front_x
    root_y = (
        p.head_bezel_opening_width / 2.0
        + (p.head_bezel_outer_width - p.head_bezel_opening_width) / 4.0
    )
    for side_sign in (-1, 1):
        head = head + rounded_box(
            root_length,
            7.0,
            28.0,
            2.0,
            (
                (root_front_x + root_rear_x) / 2.0,
                side_sign * root_y,
                p.head_center_z,
            ),
        )

    face_x = bezel_x
    faceplate = rounded_panel_yz(
        p.head_faceplate_depth,
        p.head_faceplate_width,
        p.head_faceplate_height,
        10.0,
        (face_x, 0, p.head_center_z),
    )
    faceplate = faceplate - cylinder_x(
        p.head_camera_aperture_radius,
        16.0,
        (face_x, 0, p.head_center_z - 1),
    )
    for y in (-42.0, 42.0):
        faceplate = faceplate - rounded_panel_yz(
            14.0,
            p.head_eye_aperture_width,
            p.head_eye_aperture_height,
            5.5,
            (face_x, y, eye_z),
        )

    # Front and rear inserts both use four screws into printable bosses. The
    # bosses are deliberately generous placeholders for M2.5 hardware.
    faceplate_back_x = face_x + p.head_faceplate_depth / 2.0
    face_boss_front_x = faceplate_back_x + 0.2
    face_boss_rear_x = head_front_x + 13.0
    face_boss_length = face_boss_rear_x - face_boss_front_x
    face_boss_x = (face_boss_front_x + face_boss_rear_x) / 2.0
    for y, z in head_face_mount_positions(p):
        boss = cylinder_x(5.0, face_boss_length, (face_boss_x, y, z))
        head = head + boss
        hole = cylinder_x(1.45, face_boss_length + 4.0, (face_boss_x, y, z))
        head = head - hole
        faceplate = faceplate - cylinder_x(1.7, 8.0, (face_x, y, z))

    rear_x = p.head_center_x + p.head_depth / 2.0
    rear_cover = rounded_panel_yz(
        4.0,
        p.head_width - 8.0,
        p.head_height - 8.0,
        12.0,
        (rear_x + 2.0, 0.0, p.head_center_z),
    )
    for y, z in head_rear_mount_positions(p):
        boss = cylinder_x(4.8, 14.0, (rear_x - 7.0, y, z))
        head = head + boss
        head = head - cylinder_x(1.45, 20.0, (rear_x - 7.0, y, z))
        rear_cover = rear_cover - cylinder_x(1.7, 10.0, (rear_x + 2.0, y, z))

    # Recess only the inner face of the rear panel along the fixed yoke's
    # buffered extreme-pitch envelope. This preserves the clean exterior and
    # one-piece cover while making the full +/-20 degree range a geometric
    # contract instead of relying on near-tangent surfaces.
    tilt_axis = Axis(
        (p.head_tilt_axis_x, 0.0, p.head_tilt_axis_z),
        (0.0, 1.0, 0.0),
    )
    fixed_yoke = head_motion_mounts(p)["head_tilt_yoke"]
    for moving_angle in (
        -p.head_tilt_limit_degrees - 1.0,
        -p.head_tilt_limit_degrees,
        p.head_tilt_limit_degrees,
        p.head_tilt_limit_degrees + 1.0,
    ):
        relative_yoke = fixed_yoke.rotate(tilt_axis, -moving_angle)
        rear_cover = rear_cover - relative_yoke
        rear_cover = rear_cover - moved(relative_yoke, (0.4, 0.0, 0.0))

    eye_y = (-42, 42)
    eyes = []
    eye_glows = []
    for y in eye_y:
        eye_frame = rounded_panel_yz(
            2.0,
            p.head_eye_frame_width,
            p.head_eye_frame_height,
            6.0,
            (face_x - 2.5, y, eye_z),
        )
        eye_frame = eye_frame - rounded_panel_yz(
            5.0,
            p.head_eye_aperture_width,
            p.head_eye_aperture_height,
            5.5,
            (face_x - 2.5, y, eye_z),
        )
        eyes.append(eye_frame)
        eye_glows.append(
            rounded_panel_yz(
                1.2,
                p.head_eye_glow_width,
                p.head_eye_glow_height,
                4.0,
                (face_x - 3.0, y, eye_z),
            )
        )

    # One fused stepped annulus replaces the old overlapping four-piece lens
    # stack. The 26 mm front clear bore stays open for the real camera lens and
    # its conservative wide-FOV cone; no
    # printed decorative disk is allowed to become an accidental lens cap.
    lens_z = p.head_center_z - 1.0
    outer_x, outer_depth, mid_x, mid_depth, inner_x, inner_depth = (
        head_lens_stack_positions(p)
    )
    lens_outer = cylinder_x(p.head_lens_outer_radius, outer_depth, (outer_x, 0, lens_z))
    lens_outer = lens_outer - cylinder_x(
        p.head_lens_mid_radius - 0.2,
        outer_depth + 2.0,
        (outer_x, 0, lens_z),
    )
    lens_mid = cylinder_x(p.head_lens_mid_radius, mid_depth, (mid_x, 0, lens_z))
    lens_mid = lens_mid - cylinder_x(
        p.head_lens_inner_radius - 0.2,
        mid_depth + 2.0,
        (mid_x, 0, lens_z),
    )
    lens_inner = cylinder_x(
        p.head_lens_inner_radius,
        inner_depth,
        (inner_x, 0, lens_z),
    )
    lens_inner = lens_inner - cylinder_x(
        p.head_lens_clear_radius,
        inner_depth + 2.0,
        (inner_x, 0, lens_z),
    )
    lens_bezel = lens_outer + lens_mid + lens_inner
    faceplate = faceplate + lens_bezel
    camera_lens_hardware = cylinder_x(
        5.2,
        1.0,
        (camera_lens_front_x(p), 0.0, lens_z),
    )

    brows = [
        rounded_panel_yz(2.0, 30, 6, 2.8, (face_x - 2.5, -42, p.head_center_z + 23)),
        rounded_panel_yz(2.0, 30, 6, 2.8, (face_x - 2.5, 42, p.head_center_z + 23)),
    ]

    # Re-open both moving-adapter pockets after all bezel roots, panel bosses,
    # and lower-shell unions. This keeps the enlarged R-ML24 drive cartridge
    # serviceable without allowing a later cosmetic union to grow back into
    # its swept volume.
    for side_sign in (-1, 1):
        head = head - cylinder_y(
            p.head_tilt_adapter_radius + 0.45,
            p.head_tilt_adapter_thickness + 1.2,
            (
                p.head_tilt_axis_x,
                head_tilt_adapter_center_y(p, side_sign),
                p.head_tilt_axis_z,
            ),
        )
    parts.update(
        {
            "neck_collar": collar,
            "neck": neck,
            "pan_bearing_retainer": pan_retainer,
            "head_shell": head,
            "head_faceplate": faceplate,
            "head_rear_cover": rear_cover,
            "camera_carrier": camera_carrier(p),
            "camera_lens_hardware": camera_lens_hardware,
        }
    )
    for index, shape in enumerate(eyes, start=1):
        parts[f"eye_socket_{index}"] = shape
    for index, shape in enumerate(eye_glows, start=1):
        parts[f"eye_glow_{index}"] = shape
    for index, shape in enumerate(eye_carriers, start=1):
        parts[f"head_eye_led_carrier_{index}"] = shape
    for index, shape in enumerate(brows, start=1):
        parts[f"eyebrow_{index}"] = shape
    return parts


def front_expression(p: Params):
    face_x = -p.body_length / 2.0 + 1.4
    fascia = rounded_panel_yz(3.2, 138, 31, 9, (face_x, 0, 96))
    fascia = fascia - rounded_panel_yz(10.0, 74.0, 19.0, 7.0, (face_x, 0.0, 96.0))
    fascia_inner_x = face_x + 1.6
    front_pod_face_x = -140.5
    pod_boss_length = front_pod_face_x - fascia_inner_x
    for _side, y, z in front_tof_pod_mount_positions():
        boss = cylinder_x(
            4.2,
            pod_boss_length,
            ((fascia_inner_x + front_pod_face_x) / 2.0, y, z),
        )
        fascia = fascia + boss
        fascia = fascia - cylinder_x(
            p.insert_hole_m2_5 / 2.0,
            6.0,
            (front_pod_face_x - 3.0, y, z),
        )
    sensor_x = face_x - 2.6
    sensor = rounded_panel_yz(2.0, 72, 17, 7, (sensor_x, 0, 96))
    for _side, y in front_tof_y_positions():
        sensor = sensor - rounded_panel_yz(
            8.0,
            12.0,
            10.0,
            3.0,
            (sensor_x, y, 96.0),
        )
    carriers = []
    lights = []
    for y in (-50.0, 50.0):
        fascia = fascia - rounded_panel_yz(
            10.0,
            p.front_status_aperture_width,
            p.front_status_aperture_height,
            4.5,
            (face_x, y, 96.0),
        )
        for z in (83.0, 109.0):
            fascia = fascia - cylinder_x(
                p.m2_5_clearance_hole / 2.0,
                10.0,
                (face_x, y, z),
            )
        lights.append(
            rounded_panel_yz(
                2.0,
                p.front_status_glow_width,
                p.front_status_glow_height,
                4.0,
                (face_x - 2.6, y, 96.0),
            )
        )
        status_pcb_front_x = front_neopixel_pcb_front_x(p)
        status_carrier_x = (
            status_pcb_front_x
            + p.neopixel_pcb_thickness
            + p.neopixel_connector_rear_protrusion
            + p.neopixel_carrier_component_clearance
            + p.neopixel_carrier_depth / 2.0
        )
        carrier = led_carrier_frame(
            p,
            (status_carrier_x, y, 96.0),
            34.0,
            32.0,
            p.front_status_carrier_opening_width,
            p.front_status_carrier_opening_height,
            13.0,
            insert_holes=True,
            pcb_front_x=status_pcb_front_x,
        )
        # The adjacent ToF pod uses two fascia-rooted cylindrical bosses just
        # inside the status carrier edge. Exact half-round notches preserve the
        # board-safe ToF screw positions without interpenetrating either part.
        boss_y = next(
            mount_y
            for _side, mount_y, _boss_z in front_tof_pod_mount_positions()
            if (mount_y < 0) == (y < 0)
        )
        carrier = carrier - rounded_panel_yz(
            10.0,
            9.0,
            22.0,
            4.2,
            (status_carrier_x, boss_y, 96.0),
        )
        carriers.append(carrier)
    parts = {
        "front_sensor_fascia": fascia,
        "front_sensor_window": sensor,
        "front_status_left": lights[0],
        "front_status_right": lights[1],
    }
    for index, carrier in enumerate(carriers, start=1):
        parts[f"front_status_led_carrier_{index}"] = carrier
    return parts


def power_distribution_fit_parts(p: Params):
    """Drawing-backed custom fuse-board hardware and serviced keepouts."""
    deck_top = p.power_deck_z + 2.0
    board_bottom = deck_top + p.power_distribution_lower_standoff_height
    board_top = board_bottom + p.power_distribution_board_thickness
    board = rounded_box(
        p.power_distribution_board_length,
        p.power_distribution_board_width,
        p.power_distribution_board_thickness,
        0.6,
        (
            p.power_distribution_center_x,
            p.power_distribution_center_y,
            board_bottom + p.power_distribution_board_thickness / 2.0,
        ),
    )
    for x, y in power_distribution_board_mount_positions(p):
        board = board - cylinder_z(
            p.power_distribution_mount_hole / 2.0,
            p.power_distribution_board_thickness + 2.0,
            (x, y, board_bottom + p.power_distribution_board_thickness / 2.0),
        )

    fits = {"fit_power_distribution_board": board}
    for index, (x, y) in enumerate(power_distribution_holder_positions(p), start=1):
        holder = rounded_box(
            p.power_distribution_holder_length,
            p.power_distribution_holder_width,
            p.power_distribution_holder_height,
            0.7,
            (
                x,
                y,
                board_top + p.power_distribution_holder_height / 2.0,
            ),
        )
        fuse = rounded_box(
            p.power_distribution_fuse_length,
            p.power_distribution_fuse_width,
            p.power_distribution_fuse_height,
            0.45,
            (
                x,
                y,
                board_top
                + p.power_distribution_holder_height
                - p.power_distribution_fuse_height / 2.0
                + 0.2,
            ),
        )
        fits[f"fit_power_distribution_holder_{index}"] = holder
        fits[f"fit_power_distribution_fuse_{index}"] = fuse

    header_center_x = (
        p.power_distribution_center_x
        + p.power_distribution_board_length / 2.0
        - p.power_distribution_header_depth / 2.0
    )
    fits["fit_power_distribution_header"] = rounded_box(
        p.power_distribution_header_depth,
        p.power_distribution_header_width,
        p.power_distribution_header_height,
        1.0,
        (
            header_center_x,
            p.power_distribution_center_y,
            board_top + p.power_distribution_header_height / 2.0,
        ),
    )
    receptacle_center_x = (
        p.power_distribution_center_x
        + p.power_distribution_board_length / 2.0
        + p.power_distribution_receptacle_depth / 2.0
    )
    fits["fit_power_distribution_receptacle"] = rounded_box(
        p.power_distribution_receptacle_depth,
        p.power_distribution_receptacle_width,
        p.power_distribution_receptacle_height,
        1.2,
        (
            receptacle_center_x,
            p.power_distribution_center_y,
            board_top + p.power_distribution_receptacle_height / 2.0,
        ),
    )
    harness_straight_center_x = (
        p.power_distribution_center_x
        + p.power_distribution_board_length / 2.0
        + p.power_distribution_receptacle_depth
        + p.power_distribution_harness_straight_length / 2.0
    )
    fits["fit_power_distribution_harness_straight"] = rounded_box(
        p.power_distribution_harness_straight_length,
        16.0,
        10.0,
        1.5,
        (
            harness_straight_center_x,
            p.power_distribution_center_y,
            board_top + 5.0,
        ),
    )
    fits["fit_power_distribution_harness_bend"] = rounded_box(
        p.power_distribution_harness_bend_width,
        p.power_distribution_harness_bend_length,
        10.0,
        2.0,
        (
            harness_straight_center_x - 1.0,
            p.power_distribution_center_y
            - p.power_distribution_harness_bend_length / 2.0
            + 2.0,
            board_top + 5.0,
        ),
    )
    fits["fit_power_distribution_fuse_service"] = rounded_prism_xy(
        p.power_distribution_cover_length,
        p.power_distribution_cover_width,
        p.power_distribution_fuse_service_height,
        3.0,
        (
            p.power_distribution_center_x,
            p.power_distribution_center_y,
            deck_top + p.power_distribution_fuse_service_height / 2.0,
        ),
        edge_radius=0.8,
    )
    for index, (x, y) in enumerate(power_distribution_board_mount_positions(p), start=1):
        fits[f"fit_power_distribution_lower_standoff_{index}"] = cylinder_z(
            1.7,
            p.power_distribution_lower_standoff_height,
            (
                x,
                y,
                deck_top + p.power_distribution_lower_standoff_height / 2.0,
            ),
        )
        fits[f"fit_power_distribution_upper_standoff_{index}"] = cylinder_z(
            1.7,
            p.power_distribution_upper_standoff_height,
            (
                x,
                y,
                board_top + p.power_distribution_upper_standoff_height / 2.0,
            ),
        )
    return fits


def electronics_fit(p: Params):
    """Review-only volumes; not part of the printable body exports."""
    pi_board_z = p.body_bottom + 7.0 + p.pi_board_height / 2.0
    pi_clearance_z = pi_board_z + (p.pi_clearance_height - p.pi_board_height) / 2.0
    z = p.body_bottom + p.tray_thickness + 19
    _camera_pcb_x, _camera_board_z, _camera_carrier_x = camera_reference(p)
    deck_top = p.power_deck_z + 2.0
    pi_regulator_bottom = deck_top + p.pi_regulator_standoff_height
    servo_regulator_bottom = deck_top + p.servo_regulator_standoff_height
    pico_board_bottom = pico2_board_bottom_z(p)
    mdds10_pcb_bottom = mdds10_board_bottom_z(p)
    mdds10_overall_height = p.mdds10_below_pcb + p.mdds10_above_pcb
    mdds10_overall_center_z = (
        mdds10_pcb_bottom
        + (p.mdds10_above_pcb - p.mdds10_below_pcb) / 2.0
    )
    mdds10_front_x = p.controller_center_x - p.mdds10_board_length / 2.0
    mdds10_terminal_center_x = (
        mdds10_front_x - 1.0 - p.mdds10_terminal_service_length / 2.0
    )
    mdds10_top_z = mdds10_pcb_bottom + p.mdds10_above_pcb
    pico_board_center_z = pico_board_bottom + p.pico2_board_thickness / 2.0
    pico_board = rounded_box(
        p.pico2_board_length,
        p.pico2_board_width,
        p.pico2_board_thickness,
        0.8,
        (p.safety_center_x, p.safety_center_y, pico_board_center_z),
    )
    pico_usb = rounded_box(
        p.pico2_usb_length,
        p.pico2_usb_width,
        p.pico2_usb_height,
        0.8,
        (
            pico2_usb_center_x(p),
            p.safety_center_y,
            pico_board_bottom + 0.2 + p.pico2_usb_height / 2.0,
        ),
    )
    pico_hardware = pico_board + pico_usb
    rear_service_bay = rounded_box(
        23.0,
        100.0,
        32.0,
        5.0,
        (136.5, 0.0, p.rear_service_panel_z),
    ) - rounded_box(
        p.estop_terminal_service_width + 4.0,
        p.estop_terminal_service_width + 4.0,
        60.0,
        5.0,
        (p.estop_center_x, 0.0, p.rear_service_panel_z),
    )
    # The six small frame bosses are deliberate local intrusions into the
    # otherwise open connector bay. Recording the notches in the keepout keeps
    # future cartridge cutouts honest without throwing away the useful volume
    # between them.
    for _role, center_y, center_z in rear_service_cartridge_layout(p):
        for mount_y, mount_z in rear_service_cartridge_mount_positions(
            p, center_y, center_z
        ):
            rear_service_bay = rear_service_bay - cylinder_x(
                4.0,
                10.0,
                (148.0, mount_y, mount_z),
            )
    fits = {
        "fit_pi5_board": rounded_box(
            p.pi_board_length,
            p.pi_board_width,
            p.pi_board_height,
            2.0,
            (p.pi_center_x, p.pi_center_y, pi_board_z),
        ),
        "fit_pi5": rounded_box(
            p.pi_clearance_length,
            p.pi_clearance_width,
            p.pi_clearance_height,
            5,
            (p.pi_center_x, p.pi_center_y, pi_clearance_z),
        ),
        "fit_motor_controller": rounded_box(
            p.mdds10_board_length,
            p.mdds10_board_width,
            mdds10_overall_height,
            2.8,
            (
                p.controller_center_x,
                p.controller_center_y,
                mdds10_overall_center_z,
            ),
        ),
        "fit_motor_controller_board": rounded_box(
            p.mdds10_board_length,
            p.mdds10_board_width,
            p.mdds10_board_thickness,
            2.8,
            (
                p.controller_center_x,
                p.controller_center_y,
                mdds10_pcb_bottom + p.mdds10_board_thickness / 2.0,
            ),
        ),
        "fit_motor_controller_terminal_service": rounded_box(
            p.mdds10_terminal_service_length,
            p.mdds10_terminal_service_width,
            p.mdds10_terminal_service_height,
            2.0,
            (
                mdds10_terminal_center_x,
                p.controller_center_y,
                mdds10_pcb_bottom + 4.0,
            ),
        ),
        "fit_motor_controller_airflow": rounded_box(
            p.mdds10_board_length - 8.0,
            p.mdds10_board_width - 8.0,
            p.mdds10_airflow_height,
            2.0,
            (
                p.controller_center_x,
                p.controller_center_y,
                mdds10_top_z + p.mdds10_airflow_height / 2.0,
            ),
        ),
        "fit_drive_motor_left": drive_motor_fit(p, -1),
        "fit_drive_motor_right": drive_motor_fit(p, 1),
        "fit_drive_motor_bracket_left": drive_motor_bracket_fit(p, -1),
        "fit_drive_motor_bracket_right": drive_motor_bracket_fit(p, 1),
        "fit_drive_motor_hub_left": drive_motor_hub_fit(p, -1),
        "fit_drive_motor_hub_right": drive_motor_hub_fit(p, 1),
        "fit_drive_motor_cable_left": drive_motor_cable_service_fit(p, -1),
        "fit_drive_motor_cable_right": drive_motor_cable_service_fit(p, 1),
        "fit_battery": rounded_box(
            p.battery_max_length,
            p.battery_max_width,
            p.battery_max_height,
            8,
            (
                p.battery_center_x,
                p.battery_center_y,
                p.body_bottom + 9.0 + p.battery_max_height / 2.0,
            ),
        ),
        "fit_battery_lead_service": rounded_box(
            p.battery_lead_service_length,
            p.battery_lead_service_width,
            p.battery_lead_service_height,
            2.0,
            (
                p.battery_center_x
                + p.battery_max_length / 2.0
                + p.battery_lead_service_length / 2.0,
                p.battery_center_y,
                p.body_bottom
                + 9.0
                + p.battery_max_height
                - p.battery_lead_service_height / 2.0,
            ),
        ),
        "fit_safety_mcu": rounded_box(
            p.pico2_clearance_length,
            p.pico2_clearance_width,
            p.pico2_clearance_height,
            3,
            (
                p.safety_center_x,
                p.safety_center_y,
                pico_board_bottom + p.pico2_clearance_height / 2.0,
            ),
        ),
        "fit_safety_mcu_board": pico_hardware,
        "fit_safety_mcu_header_left": rounded_box(
            p.pico2_header_length,
            p.pico2_header_width,
            p.pico2_header_height,
            0.8,
            (
                p.safety_center_x,
                p.safety_center_y - (p.pico2_board_width - p.pico2_header_width) / 2.0,
                pico_board_bottom + p.pico2_board_thickness + p.pico2_header_height / 2.0,
            ),
        ),
        "fit_safety_mcu_header_right": rounded_box(
            p.pico2_header_length,
            p.pico2_header_width,
            p.pico2_header_height,
            0.8,
            (
                p.safety_center_x,
                p.safety_center_y + (p.pico2_board_width - p.pico2_header_width) / 2.0,
                pico_board_bottom + p.pico2_board_thickness + p.pico2_header_height / 2.0,
            ),
        ),
        "fit_safety_mcu_usb_service": rounded_box(
            25.0,
            12.0,
            8.0,
            2.0,
            (
                p.safety_center_x - 35.5,
                p.safety_center_y,
                pico_board_bottom + 4.0,
            ),
        ),
        "fit_safety_mcu_swd_service": rounded_box(
            24.0,
            12.0,
            8.0,
            2.0,
            (
                p.safety_center_x + 36.5,
                p.safety_center_y,
                pico_board_bottom + 4.0,
            ),
        ),
        "fit_future_ai_hat_clearance": rounded_box(
            96,
            74,
            22,
            5,
            (p.pi_center_x, p.pi_center_y, z + 30),
        ),
        "fit_pan_servo": pan_servo_fit(p),
        "fit_pan_servo_horn": pan_servo_horn_fit(p),
        "fit_pan_bearing": pan_bearing_fit(p),
        "fit_tilt_servo": tilt_servo_fit(p),
        "fit_tilt_servo_horn": tilt_servo_horn_fit(p),
        "fit_tilt_passive_bushing": tilt_passive_bushing_fit(p),
        "fit_tilt_shoulder_bolt": tilt_shoulder_bolt_fit(p),
        "fit_servo_cable_corridor": servo_cable_corridor(p),
        "fit_pi_buck_regulator": rounded_box(
            p.pi_regulator_width,
            p.pi_regulator_length,
            p.pi_regulator_height,
            1.5,
            (
                p.pi_regulator_center_x,
                p.pi_regulator_center_y,
                pi_regulator_bottom + p.pi_regulator_height / 2.0,
            ),
        ),
        "fit_pi_buck_terminal_service_front": rounded_box(
            p.pi_regulator_terminal_service_width,
            p.pi_regulator_terminal_service_length,
            p.pi_regulator_terminal_service_height,
            2.0,
            (
                p.pi_regulator_center_x,
                p.pi_regulator_center_y - p.pi_regulator_length / 2.0
                - p.pi_regulator_terminal_service_length / 2.0,
                pi_regulator_bottom + p.pi_regulator_terminal_service_height / 2.0,
            ),
        ),
        "fit_pi_buck_terminal_service_rear": rounded_box(
            p.pi_regulator_terminal_service_width,
            p.pi_regulator_terminal_service_length,
            p.pi_regulator_terminal_service_height,
            2.0,
            (
                p.pi_regulator_center_x,
                p.pi_regulator_center_y + p.pi_regulator_length / 2.0
                + p.pi_regulator_terminal_service_length / 2.0,
                pi_regulator_bottom + p.pi_regulator_terminal_service_height / 2.0,
            ),
        ),
        "fit_servo_regulator": rounded_box(
            p.servo_regulator_length,
            p.servo_regulator_width,
            p.servo_regulator_height,
            1.5,
            (
                p.servo_regulator_center_x,
                p.servo_regulator_center_y,
                servo_regulator_bottom + p.servo_regulator_height / 2.0,
            ),
        ),
        "fit_servo_regulator_wire_service": rounded_box(
            p.servo_regulator_wire_service_length,
            p.servo_regulator_wire_service_width,
            p.servo_regulator_wire_service_height,
            2.0,
            (
                p.servo_regulator_center_x
                + p.servo_regulator_length / 2.0
                + p.servo_regulator_wire_service_length / 2.0,
                p.servo_regulator_center_y,
                servo_regulator_bottom + p.servo_regulator_wire_service_height / 2.0,
            ),
        ),
        "fit_motor_cutoff": rounded_box(
            p.motor_cutoff_body_width,
            p.motor_cutoff_body_length,
            p.motor_cutoff_body_height,
            3.0,
            (
                p.motor_cutoff_center_x,
                p.motor_cutoff_center_y,
                deck_top
                + p.motor_cutoff_metal_plate_thickness
                + p.motor_cutoff_body_height / 2.0,
            ),
        ),
        "fit_motor_cutoff_terminal_service": rounded_box(
            p.motor_cutoff_service_width,
            p.motor_cutoff_service_length,
            p.motor_cutoff_service_height,
            3.0,
            (
                p.motor_cutoff_center_x,
                p.motor_cutoff_center_y,
                deck_top
                + p.motor_cutoff_metal_plate_thickness
                + p.motor_cutoff_service_height / 2.0,
            ),
        ),
        "fit_motor_cutoff_metal_plate": rounded_box(
            p.motor_cutoff_metal_plate_length,
            p.motor_cutoff_metal_plate_width,
            p.motor_cutoff_metal_plate_thickness,
            2.0,
            (
                p.motor_cutoff_center_x,
                p.motor_cutoff_center_y,
                deck_top + p.motor_cutoff_metal_plate_thickness / 2.0,
            ),
        ),
        "fit_rear_service_bay": rear_service_bay,
        "fit_camera_module_3": camera_module_fit(p),
        "fit_camera_fov": camera_field_of_view_keepout(p),
        "fit_head_eye_led_left": neopixel_breakout_fit(
            p,
            head_neopixel_pcb_front_x(p),
            -42.0,
            p.head_center_z + p.head_eye_center_z_offset,
            True,
        ),
        "fit_head_eye_led_right": neopixel_breakout_fit(
            p,
            head_neopixel_pcb_front_x(p),
            42.0,
            p.head_center_z + p.head_eye_center_z_offset,
            True,
        ),
        "fit_front_status_led_left": neopixel_breakout_fit(
            p,
            front_neopixel_pcb_front_x(p),
            -50.0,
            96.0,
            False,
        ),
        "fit_front_status_led_right": neopixel_breakout_fit(
            p,
            front_neopixel_pcb_front_x(p),
            50.0,
            96.0,
            False,
        ),
    }
    fits.update(front_idler_fit_parts(p, -1))
    fits.update(front_idler_fit_parts(p, 1))
    fits.update(power_distribution_fit_parts(p))
    fits.update(mute_switch_fit_parts(p))
    fits.update(charge_jack_fit_parts(p))
    fits.update(service_jack_fit_parts(p))
    eye_carrier_x = (
        head_neopixel_pcb_front_x(p)
        + p.neopixel_pcb_thickness
        + p.neopixel_connector_rear_protrusion
        + p.neopixel_carrier_component_clearance
        + p.neopixel_carrier_depth / 2.0
    )
    status_carrier_x = (
        front_neopixel_pcb_front_x(p)
        + p.neopixel_pcb_thickness
        + p.neopixel_connector_rear_protrusion
        + p.neopixel_carrier_component_clearance
        + p.neopixel_carrier_depth / 2.0
    )
    for side, y in (("left", -42.0), ("right", 42.0)):
        fits[f"fit_head_eye_led_{side}_jst_service"] = neopixel_jst_service_fit(
            p,
            head_neopixel_pcb_front_x(p),
            y,
            p.head_center_z + p.head_eye_center_z_offset,
            True,
        )
        for index, spacer in enumerate(
            neopixel_spacer_fits(
                p,
                head_neopixel_pcb_front_x(p),
                eye_carrier_x,
                y,
                p.head_center_z + p.head_eye_center_z_offset,
                True,
            ),
            start=1,
        ):
            fits[f"fit_head_eye_led_{side}_spacer_{index}"] = spacer
    for side, y in (("left", -50.0), ("right", 50.0)):
        fits[f"fit_front_status_led_{side}_jst_service"] = neopixel_jst_service_fit(
            p,
            front_neopixel_pcb_front_x(p),
            y,
            96.0,
            False,
        )
        for index, spacer in enumerate(
            neopixel_spacer_fits(
                p,
                front_neopixel_pcb_front_x(p),
                status_carrier_x,
                y,
                96.0,
                False,
            ),
            start=1,
        ):
            fits[f"fit_front_status_led_{side}_spacer_{index}"] = spacer
    for x, y in pi_regulator_mount_positions(p):
        fits["fit_pi_buck_regulator"] = fits["fit_pi_buck_regulator"] - cylinder_z(
            p.pi_regulator_mount_hole / 2.0,
            p.pi_regulator_height + 2.0,
            (x, y, pi_regulator_bottom + p.pi_regulator_height / 2.0),
        )
    for x, y in servo_regulator_mount_positions(p):
        fits["fit_servo_regulator"] = fits["fit_servo_regulator"] - cylinder_z(
            p.servo_regulator_mount_hole / 2.0,
            p.servo_regulator_height + 2.0,
            (x, y, servo_regulator_bottom + p.servo_regulator_height / 2.0),
        )
    for x, y in motor_cutoff_plate_mount_positions(p):
        fits["fit_motor_cutoff_metal_plate"] = fits["fit_motor_cutoff_metal_plate"] - cylinder_z(
            p.motor_cutoff_plate_mount_hole / 2.0,
            p.motor_cutoff_metal_plate_thickness + 2.0,
            (x, y, deck_top + p.motor_cutoff_metal_plate_thickness / 2.0),
        )
    controller_plate_top = motor_controller_plate_top_z(p)
    controller_board_bottom = mdds10_pcb_bottom
    for index, (x, y) in enumerate(motor_controller_board_mount_positions(p), start=1):
        fits[f"fit_motor_controller_standoff_{index}"] = cylinder_z(
            3.0,
            controller_board_bottom - controller_plate_top,
            (x, y, (controller_board_bottom + controller_plate_top) / 2.0),
        )
    for side, side_sign in (("left", -1), ("right", 1)):
        for index, (x, y) in enumerate(
            drive_motor_bracket_tray_positions(p, side_sign), start=1
        ):
            fits[f"fit_drive_motor_bracket_spacer_{side}_{index}"] = cylinder_z(
                3.0,
                p.motor_bracket_spacer_height,
                (
                    x,
                    y,
                    p.body_bottom + p.motor_bracket_spacer_height / 2.0,
                ),
            )
    controller_plate_bottom = motor_controller_plate_bottom_z(p)
    for index, (x, y) in enumerate(motor_controller_plate_mount_positions(p), start=1):
        fits[f"fit_motor_controller_plate_standoff_{index}"] = cylinder_z(
            3.0,
            controller_plate_bottom - p.body_bottom,
            (x, y, (controller_plate_bottom + p.body_bottom) / 2.0),
        )
    for index, (x, y) in enumerate(power_deck_mount_positions(p), start=1):
        tray_top = p.body_bottom
        deck_bottom = p.power_deck_z - 2.0
        fits[f"fit_power_deck_standoff_{index}"] = cylinder_z(
            3.0,
            deck_bottom - tray_top,
            (x, y, (deck_bottom + tray_top) / 2.0),
        )
    for index, (x, y) in enumerate(pi_regulator_mount_positions(p), start=1):
        fits[f"fit_pi_regulator_standoff_{index}"] = cylinder_z(
            2.5,
            p.pi_regulator_standoff_height,
            (x, y, deck_top + p.pi_regulator_standoff_height / 2.0),
        )
    for index, (x, y) in enumerate(servo_regulator_mount_positions(p), start=1):
        fits[f"fit_servo_regulator_standoff_{index}"] = cylinder_z(
            2.5,
            p.servo_regulator_standoff_height,
            (x, y, deck_top + p.servo_regulator_standoff_height / 2.0),
        )
    harness_deck_bottom = p.power_deck_z - 2.0
    harness_base_top = harness_deck_bottom - p.power_harness_deck_gap
    harness_base_bottom = harness_base_top - p.power_harness_base_thickness
    harness_channel_top = harness_base_bottom - 0.2
    harness_channel_z = harness_channel_top - p.power_harness_channel_height / 2.0
    for side, side_sign in (("left", -1), ("right", 1)):
        fits[f"fit_power_harness_{side}"] = rounded_box(
            p.power_harness_rail_length - 8.0,
            p.power_harness_channel_width,
            p.power_harness_channel_height,
            1.8,
            (
                p.power_deck_center_x,
                side_sign * p.power_harness_center_y,
                harness_channel_z,
            ),
        )
    safety_shelf_bottom = p.safety_mount_z - 2.0
    for index, (x, y) in enumerate(safety_shelf_standoff_positions(p), start=1):
        fits[f"fit_safety_shelf_standoff_{index}"] = cylinder_z(
            3.0,
            safety_shelf_bottom - controller_plate_top,
            (x, y, (safety_shelf_bottom + controller_plate_top) / 2.0),
        )
    safety_shelf_top = p.safety_mount_z + 2.0
    for index, (x, y) in enumerate(pico2_mount_positions(p), start=1):
        fits[f"fit_safety_mcu_standoff_{index}"] = cylinder_z(
            2.5,
            pico_board_bottom - safety_shelf_top,
            (x, y, (pico_board_bottom + safety_shelf_top) / 2.0),
        )
    fits["fit_mic_array"] = cylinder_z(
        p.mic_array_diameter / 2.0,
        p.mic_array_height,
        (p.mic_array_center_x, 0.0, 160.0),
    )
    fits.update(audio_amp_fit_parts(p))
    for side, y in (("left", -67.0), ("right", 67.0)):
        fits[f"fit_speaker_{side}"] = rounded_box(
            p.speaker_length,
            p.speaker_width,
            p.speaker_height,
            3.0,
            (80.0, y, 157.5),
        )
    for side, y in front_tof_y_positions():
        fits[f"fit_tof_front_{side}"] = rounded_panel_yz(
            p.tof_board_height,
            p.tof_board_length,
            p.tof_board_width,
            2.0,
            (-137.5, y, 96.0),
        )
    for side, sign in (("left", -1), ("right", 1)):
        fits[f"fit_tof_side_{side}"] = rounded_panel_xz(
            p.tof_board_height,
            p.tof_board_length,
            p.tof_board_width,
            2.0,
            (p.side_tof_center_x, sign * 99.5, 96.0),
        )
    for name, orientation, x, y in bumper_switch_layout():
        fits[f"fit_bumper_switch_{name}"] = bumper_switch_hardware_fit(
            p, orientation, x, y
        )

    # Purchased carry hardware is represented as fit-only geometry. The metal
    # clamp plate sits above the reinforced tray zone; the soft webbing loop
    # stows flat below the tray, above the wheel-ground plane, while driving.
    stowed_webbing_z = (
        p.body_bottom
        - p.tray_thickness
        - 0.25
        - p.carry_stowed_webbing_thickness / 2.0
    )
    for side, side_sign in (("left", -1), ("right", 1)):
        fits[f"fit_carry_clamp_plate_{side}"] = carry_anchor_clamp_plate(p, side_sign)
        fits[f"fit_carry_webbing_stowed_{side}"] = rounded_box(
            p.carry_anchor_plate_length - 4.0,
            p.carry_webbing_width,
            p.carry_stowed_webbing_thickness,
            2.5,
            (0.0, side_sign * p.carry_anchor_center_y, stowed_webbing_z),
        )
    panel_bottom = estop_mount_panel_bottom_z(p)
    panel_top = estop_mount_panel_top_z(p)
    fits["fit_estop_switch_body"] = rounded_box(
        p.estop_body_width,
        p.estop_body_width,
        p.estop_body_depth,
        3.0,
        (
            p.estop_center_x,
            0.0,
            panel_bottom - p.estop_body_depth / 2.0,
        ),
    )
    barrel_bottom = panel_bottom - 2.0
    barrel_top = panel_top + p.estop_operator_height
    fits["fit_estop_threaded_barrel"] = cylinder_z(
        p.estop_panel_hole / 2.0,
        barrel_top - barrel_bottom,
        (p.estop_center_x, 0.0, (barrel_bottom + barrel_top) / 2.0),
    )
    body_bottom = panel_bottom - p.estop_body_depth
    fits["fit_estop_terminal_service"] = rounded_box(
        p.estop_terminal_service_width,
        p.estop_terminal_service_width,
        p.estop_terminal_service_depth,
        4.0,
        (
            p.estop_center_x,
            0.0,
            body_bottom - p.estop_terminal_service_depth / 2.0,
        ),
    )
    legend = cylinder_z(
        p.estop_legend_outer_diameter / 2.0,
        p.estop_legend_thickness,
        (p.estop_center_x, 0.0, panel_top + p.estop_legend_thickness / 2.0),
    )
    legend = legend - cylinder_z(
        p.estop_panel_hole / 2.0 + 0.5,
        p.estop_legend_thickness + 2.0,
        (p.estop_center_x, 0.0, panel_top + p.estop_legend_thickness / 2.0),
    )
    fits["fit_estop_yellow_legend"] = legend
    return fits


def build_parts(p: Params):
    parts = {
        "body_shell": body_shell(p),
        "base_tray": base_tray(p),
        "battery_cradle": battery_cradle(p),
        "bumper_carrier": bumper_carrier(p),
        "estop_backing_plate": estop_backing_plate(p),
    }
    reveal, lid, vent_inlay, estop_well, estop, estop_cap = lid_and_top_details(p)
    parts.update(
        {
            "lid_reveal": reveal,
            "top_lid": lid,
            "top_vent_inlay": vent_inlay,
            "estop_well": estop_well,
            "estop": estop,
            "estop_cap": estop_cap,
        }
    )
    parts.update(wheel_parts(p))
    parts.update(motor_pods(p))
    parts.update(front_idler_pods(p))
    parts.update(side_fairings(p))
    parts.update(audio_mounts(p))
    parts.update(tof_sensor_pods(p))
    parts.update(electronics_mounts(p))
    parts.update(power_mounts(p))
    parts.update(power_harness_rails(p))
    parts.update(bumper_switch_mounts(p))
    parts.update(head_motion_mounts(p))
    parts.update(head_parts(p))
    parts.update(front_expression(p))
    parts["rear_service_panel"] = rear_service_panel(p)
    parts.update(rear_service_cartridges(p))
    parts["rear_service_data_carrier"] = rear_service_data_carrier(p)
    return parts


def component_coverage_status():
    """Machine-readable BOM-to-CAD status; detailed rationale lives in docs."""
    return {
        "compute_camera_audio": "modeled_reference_with_service_fasteners_and_two_adafruit_3006_step_pattern_stereo_amp_mounts_pending_current_terminal_measurement",
        "safety_mcu": "raspberry_pi_pico_2_official_board_hole_usb_swd_and_standoff_contract",
        "motor_controller": "cytron_mdds10_official_step_board_hole_terminal_airflow_and_standoff_contract",
        "safety_sensors_estop": "idec_xw1e_bv402m_r_keyed_panel_body_terminal_and_backing_contract_pending_physical_cutoff_test",
        "bumper_switches": "six_omron_d2hw_c202mr_drawing_backed_mount_gap_actuation_and_rigid_stop_contract_pending_coupon_and_motor_cut_test",
        "power_distribution_and_cutoff": "custom_four_branch_littelfuse_01550900m_nano2_molex_microfit_board_with_touch_cover_service_and_strain_contract_plus_sw60_and_pololu_regulators",
        "internal_harness_routing": "modeled_dual_under_deck_rails_pending_bundle_measurement",
        "rear_drive_motors": "pololu_4867_mp_motor_1569_bracket_1997_hub_drawing_backed_contract_pending_loaded_test",
        "pan_tilt_servos": "two_hitec_d85mg_r_ml24_horns_6807_pan_bearing_mf84zz_passive_tilt_drawing_backed_contract_pending_physical_motion_test",
        "battery": "bioenno_blf_1203ab_110x75x27_rotated_pack_with_wide_strapped_end_stopped_cradle_and_rear_lead_service_pending_purchased_fit_current_and_household_release_tests",
        "rear_switches_and_connectors": "drawing_backed_switchcraft_en2p3m20_charge_only_inlet_plus_35rasmt5chntrx_uart_service_and_pvb3f230ss311_physical_mute_cartridges",
        "front_support_or_caster": "modeled_two_bearing_idler_pending_hardware_test",
        "physical_led_hardware": "four_adafruit_5975_neopixel_jst_breakouts_with_exact_step_envelopes_m2_spacers_and_plug_service_paths_pending_diffusion_test",
        "head_expression_and_bezel": "modeled_vertical_diffusers_integrated_camera_bezel_and_validated_panel_paths",
        "camera_optics": "modeled_102deg_fov_keepout_pending_physical_image_test",
        "carry_handle": "modeled_recessed_webbing_and_metal_clamps_pending_loaded_test",
        "optional_lidar": "deferred",
    }


def printable_parts(parts):
    excluded = {"estop", "estop_cap", "camera_lens_hardware"}
    return {name: shape for name, shape in parts.items() if name not in excluded}


def export_all(p: Params, include_fit: bool = True):
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    # This directory is build output only. Start the main export from a clean
    # STL set so renamed parts cannot linger and be mistaken for current ones.
    for path in EXPORT_DIR.glob("*.stl"):
        path.unlink()
    for filename in (
        "codex_robot_body_v1.step",
        "codex_robot_electronics_fit_v1.step",
        "codex_robot_body_v1_manifest.json",
        "codex_robot_body_v1_parameters.json",
    ):
        path = EXPORT_DIR / filename
        if path.exists():
            path.unlink()

    parts = build_parts(p)
    print_parts = printable_parts(parts)
    assembled = Compound(list(print_parts.values()))
    export_step(assembled, EXPORT_DIR / "codex_robot_body_v1.step")
    for name, shape in print_parts.items():
        export_stl(shape, EXPORT_DIR / f"{name}.stl")

    # These files are review-only visual stand-ins for purchased hardware. They
    # are intentionally excluded from the printable assembly.
    review_only_exports = {
        "estop": "preview_estop",
        "estop_cap": "preview_estop_cap",
        "camera_lens_hardware": "preview_camera_lens_hardware",
    }
    for source_name, export_name in review_only_exports.items():
        export_stl(parts[source_name], EXPORT_DIR / f"{export_name}.stl")

    fits = electronics_fit(p) if include_fit else {}
    if fits:
        export_step(Compound(list(fits.values())), EXPORT_DIR / "codex_robot_electronics_fit_v1.step")
        for name, shape in fits.items():
            export_stl(shape, EXPORT_DIR / f"{name}.stl")

    def spans(shape):
        box = shape.bounding_box()
        return {
            "x": float(box.max.X - box.min.X),
            "y": float(box.max.Y - box.min.Y),
            "z": float(box.max.Z - box.min.Z),
        }

    manifest = {
        "units": "mm",
        "source": "cad/python/robot_body.py",
        "printable_parts": {
            name: {"span_mm": spans(shape), "solids": len(shape.solids())}
            for name, shape in print_parts.items()
        },
        "review_only_hardware": list(review_only_exports.values()),
        "fit_envelopes": {
            name: {"span_mm": spans(shape), "solids": len(shape.solids())}
            for name, shape in fits.items()
        },
        "component_coverage": component_coverage_status(),
    }
    (EXPORT_DIR / "codex_robot_body_v1_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )

    (EXPORT_DIR / "codex_robot_body_v1_parameters.json").write_text(
        json.dumps(asdict(p), indent=2) + "\n",
        encoding="utf-8",
    )
    return print_parts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--no-fit", action="store_true", help="Skip review-only electronics envelopes")
    args = parser.parse_args()
    parts = export_all(Params(), include_fit=not args.no_fit)
    print(f"Exported {len(parts)} printable/review body parts to {EXPORT_DIR}")


if __name__ == "__main__":
    main()
