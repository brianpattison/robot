"""Export a canonical, grounded, slicer-ready robot-body inventory.

The assembly model stays in assembled coordinates. This script replaces the
seven oversized one-piece body parts with their validated split variants,
rotates parts onto deliberate print faces, grounds/centers them, and writes a
manifest with material and support guidance. These are prototype-ready exports;
hardware-dependent parts remain gated until purchased components are measured.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from build123d import Align, Axis, Box, CenterOf, Location, export_stl

try:
    from robot_body import EXPORT_DIR, Params, build_parts, printable_parts
    from robot_body_split import split_parts
except ModuleNotFoundError:
    from cad.python.robot_body import EXPORT_DIR, Params, build_parts, printable_parts
    from cad.python.robot_body_split import split_parts


PRINT_READY_DIR = EXPORT_DIR / "print_ready"
TARGET_PRINTER = "Bambu Lab P1S"
TARGET_NOZZLE_MM = 0.4
TARGET_BED_MM = 256.0
TARGET_BED_MARGIN_MM = 8.0

REPLACED_MAIN_PARTS = {
    "body_shell",
    "base_tray",
    "bumper_carrier",
    "lid_reveal",
    "top_lid",
    "side_fairing_left",
    "side_fairing_right",
}

MOVING_HEAD_PARTS = (
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


def head_static_torque_estimate(p: Params, inventory):
    """Conservative 100%-dense printed-head gravity estimate about tilt Y."""
    petg_density_g_per_mm3 = 1.27e-3
    printed_mass_g = 0.0
    first_moment_g_mm = 0.0
    for name in MOVING_HEAD_PARTS:
        shape = inventory[name]["shape"]
        mass_g = float(shape.volume) * petg_density_g_per_mm3
        printed_mass_g += mass_g
        first_moment_g_mm += mass_g * float(shape.center(CenterOf.MASS).X)
    com_x = first_moment_g_mm / printed_mass_g
    offset_mm = abs(com_x - p.head_tilt_axis_x)
    printed_torque_kg_cm = printed_mass_g / 1000.0 * offset_mm / 10.0
    payload_allowance_g = 25.0
    payload_lever_arm_mm = 50.0
    payload_torque_kg_cm = payload_allowance_g / 1000.0 * payload_lever_arm_mm / 10.0
    combined_torque_kg_cm = printed_torque_kg_cm + payload_torque_kg_cm
    d85_peak_efficiency_torque_kg_cm = 0.9
    return {
        "method": "CAD material volume at 1.27 g/cm3 plus a 25 g electronics allowance at a 50 mm lever arm",
        "printed_material_density_g_per_cm3": 1.27,
        "printed_mass_g": printed_mass_g,
        "printed_com_x_mm": com_x,
        "tilt_axis_x_mm": p.head_tilt_axis_x,
        "printed_com_offset_mm": offset_mm,
        "printed_static_gravity_torque_kg_cm": printed_torque_kg_cm,
        "electronics_payload_allowance_g": payload_allowance_g,
        "electronics_payload_lever_arm_mm": payload_lever_arm_mm,
        "estimated_combined_static_gravity_torque_kg_cm": combined_torque_kg_cm,
        "d85mg_peak_efficiency_torque_at_6v_kg_cm": d85_peak_efficiency_torque_kg_cm,
        "static_ratio_to_peak_efficiency": d85_peak_efficiency_torque_kg_cm / combined_torque_kg_cm,
        "warning": "This is a static CAD sanity check, not a motion release. Weigh the complete head and test acceleration, cable drag, current, temperature, backlash, and holding behavior on purchased hardware.",
    }


def is_split_replacement(name: str) -> bool:
    return name.startswith(
        (
            "body_shell_q_",
            "body_seam_plate_",
            "base_tray_half_",
            "bumper_q_",
            "bumper_seam_plate_",
            "side_fairing_",
            "top_lid_half_",
            "lid_reveal_half_",
        )
    ) or name == "base_seam_plate"


def canonical_inventory(p: Params):
    main = printable_parts(build_parts(p))
    inventory = {
        name: {"shape": shape, "source": "main"}
        for name, shape in main.items()
        if name not in REPLACED_MAIN_PARTS
    }
    for name, shape in split_parts(p).items():
        if not is_split_replacement(name):
            continue
        if name in inventory:
            raise ValueError(f"Duplicate canonical print name: {name}")
        inventory[name] = {"shape": shape, "source": "split"}
    return inventory


def orientation_for(name: str):
    """Return orthogonal rotations and the deliberate print-face rationale."""
    if name.startswith("body_shell_q_front_"):
        return (("y", 90.0),), "flat front/rear split seam on bed"
    if name.startswith("body_shell_q_rear_"):
        return (("y", -90.0),), "flat front/rear split seam on bed"

    if name.startswith(("body_seam_plate_side_left", "bumper_seam_plate_side_left")):
        return (("x", -90.0),), "broad insert-plate face on bed; alignment pilots point upward"
    if name.startswith(("body_seam_plate_side_right", "bumper_seam_plate_side_right")):
        return (("x", 90.0),), "broad insert-plate face on bed; alignment pilots point upward"
    if name.startswith(("body_seam_plate_end_front", "bumper_seam_plate_end_front")):
        return (("y", 90.0),), "broad insert-plate face on bed; alignment pilots point upward"
    if name.startswith(("body_seam_plate_end_rear", "bumper_seam_plate_end_rear")):
        return (("y", -90.0),), "broad insert-plate face on bed; alignment pilots point upward"

    if name.startswith("side_fairing_"):
        return (("x", 90.0),), "broad cosmetic panel face on bed"

    if name in ("head_tilt_drive_adapter", "head_tilt_passive_cartridge"):
        return (("x", 90.0),), "broad pivot-adapter face on bed; axial holes print vertically"

    if name == "pan_bearing_retainer":
        return (), "broad annular bearing-retainer face on bed"

    if name == "power_harness_rail_left":
        return (("x", 90.0),), "long U-channel sidewall on bed; strap bridges print vertically"
    if name == "power_harness_rail_right":
        return (("x", -90.0),), "long U-channel sidewall on bed; strap bridges print vertically"

    left_axle_parts = (
        "motor_pod_left",
        "motor_pod_cover_left",
        "front_idler_pod_left",
        "front_idler_retainer_left_",
    )
    right_axle_parts = (
        "motor_pod_right",
        "motor_pod_cover_right",
        "front_idler_pod_right",
        "front_idler_retainer_right_",
    )
    if name in left_axle_parts[:3] or name.startswith(left_axle_parts[3]):
        return (("x", 90.0),), "outer axle face on bed; bores print vertically"
    if name in right_axle_parts[:3] or name.startswith(right_axle_parts[3]):
        return (("x", -90.0),), "outer axle face on bed; bores print vertically"

    if name.startswith(("wheel_", "hub_ring_", "hub_")):
        return (("x", 90.0),), "wheel or hub sidewall on bed"

    if name.startswith("tof_pod_side_"):
        return (("x", 90.0),), "sensor-frame face on bed"
    if name.startswith("tof_pod_front_"):
        return (("y", 90.0),), "sensor-frame face on bed"

    if name == "head_shell":
        return (("y", 90.0),), "open rear service face on bed; finished face upward"
    if name == "head_faceplate":
        return (
            (("y", 90.0),),
            "rear panel face on bed; integrated camera annulus and eye frames print upward",
        )
    if name.startswith("rear_service_cartridge_"):
        return (
            (("y", 90.0),),
            "flush cosmetic cap on bed; locating tongue and insert screws print upward",
        )

    x_normal_prefixes = (
        "head_faceplate",
        "head_rear_cover",
        "camera_carrier",
        "head_lens_",
        "eye_socket_",
        "eye_glow_",
        "head_eye_led_carrier_",
        "eyebrow_",
        "front_sensor_",
        "front_status_",
        "rear_service_panel",
    )
    if name.startswith(x_normal_prefixes):
        return (("y", 90.0),), "broad front/rear panel face on bed"

    return (), "assembled lower face already suitable"


MATERIAL_PROFILES = {
    "petg_shell": {
        "material": "PETG",
        "layer_height_mm": 0.20,
        "perimeters": 3,
        "infill_percent": 15,
        "note": "Cosmetic shell baseline; tune temperature and flow with a wall coupon.",
    },
    "petg_structural": {
        "material": "PETG",
        "layer_height_mm": 0.20,
        "perimeters": 5,
        "infill_percent": 40,
        "note": "Prototype structural baseline; increase local solid layers around inserts.",
    },
    "petg_detail": {
        "material": "PETG",
        "layer_height_mm": 0.16,
        "perimeters": 4,
        "infill_percent": 25,
        "note": "Small service/detail part baseline.",
    },
    "tpu_95a": {
        "material": "TPU 95A",
        "layer_height_mm": 0.24,
        "perimeters": 3,
        "infill_percent": 15,
        "note": "Start slow and dry; tune compliance with a bumper coupon before full quadrants.",
    },
    "translucent_petg": {
        "material": "Translucent PETG",
        "layer_height_mm": 0.12,
        "perimeters": 2,
        "infill_percent": 100,
        "note": "Optical prototype only; tune wall count and surface finish for diffusion.",
    },
}


COLOR_PROFILES = {
    "cream": {"hex": "#F0DEC2", "role": "visible molded shell surfaces"},
    "teal": {"hex": "#0B8392", "role": "top lid and wheel accent rings"},
    "dark_teal": {"hex": "#073A42", "role": "service panels and lid reveal"},
    "charcoal": {"hex": "#15171B", "role": "face, sensor, vent, tire, and bumper surfaces"},
    "dark_gray": {"hex": "#34373D", "role": "hidden structural and service parts"},
    "translucent_lime": {"hex": "#D7FF52", "role": "illuminated diffusers"},
    "blue": {"hex": "#1248D8", "role": "eyebrow expression inserts"},
}


ASSEMBLY_HARDWARE = {
    "warning": "Counts are interface counts; screw lengths and final thread choices require printed coupons and purchased hardware drawings.",
    "interfaces": {
        "split_joinery": {
            "thread": "M3",
            "fasteners": 44,
            "inserts": 44,
            "alignment_pilots": 18,
            "note": "Pilots locate the seam before screw tightening; prove fit on a representative printed interface before printing the large split shells.",
        },
        "shell_to_tray": {"thread": "M3", "fasteners": 4, "inserts": 4},
        "mobility_pods_to_tray": {"thread": "M3", "fasteners": 16, "inserts": 16},
        "motor_pod_service_covers": {"thread": "M3", "fasteners": 8, "inserts": 8},
        "rear_drive_motor_brackets": {
            "motors": "2 x Pololu #4867 99:1 25D MP 12 V encoder gearmotor",
            "brackets": "2 x Pololu #1569 metal 25D bracket",
            "hubs": "2 x Pololu #1997 4 mm shaft M3 aluminum hub",
            "thread": "M3",
            "tray_fasteners": 6,
            "metal_spacers": 6,
            "motor_face_fasteners": 4,
            "wheel_hub_fasteners": 8,
            "note": "Drawing-backed geometry; verify the purchased revisions, D-shaft/set-screw engagement, fastener lengths, loaded current, temperature, wheel retention, and floor behavior before driving.",
        },
        "front_bearing_retainers": {"thread": "M2.5", "fasteners": 8, "inserts": 8},
        "front_idler_axles": {
            "bearings": "4 x 608, 8 x 22 x 7 mm",
            "shoulder_bolts": "2 x WDS 615-M6-8-65, 8 mm x 65 mm shoulder with M6 threaded end",
            "orientation": "Shoulder-bolt head inboard; M6 washer and prevailing-torque locknut outboard",
            "thread_washers": "2 x stock M6 washers, 12 mm OD x 1.6 mm nominal",
            "locknuts": "2 x stock M6 prevailing-torque locknuts",
            "inner_spacers": "2 x 12 OD x 8 ID x 14 mm metal tubes",
            "outer_spacers": "2 x 10 OD x 8 ID x 19 mm metal tubes",
            "tuning_spacers": "2 x 10 OD x 8 ID x 3 mm stock spacers",
            "tuning_shims": "2 x 11 OD x 8 ID x 0.5 mm stock shims",
            "hubs": "2 x Pololu #2693 8 mm-shaft M3 aluminum hubs",
            "wheel_hub_fasteners": 12,
            "note": "Use only stock hardware; verify bolt shoulder support, head access, full locknut engagement, #2693 set screws, axial play, free rotation, alignment, and loaded skid-turn behavior before driving.",
        },
        "battery_cradle_to_tray": {"thread": "M3", "fasteners": 4, "inserts": 4},
        "controller_plate_to_tray": {
            "thread": "M3",
            "fasteners": 8,
            "inserts": 4,
            "standoffs": 4,
            "standoff_height_mm": 5,
            "note": "Metal spacers preserve tray clearance and keep the controller plate mechanically serviceable.",
        },
        "controller_board_standoffs": {
            "thread": "M3",
            "standoffs": 4,
            "fasteners": 8,
            "standoff_height_mm": 6,
            "note": "Cytron MDDS10 official 95.25 x 60.96 mm hole pattern; terminals face robot-front.",
        },
        "safety_shelf_standoffs": {"thread": "M3", "standoffs": 4, "fasteners": 8},
        "safety_mcu_board_standoffs": {
            "board": "Raspberry Pi Pico 2 without headers",
            "thread": "M2",
            "standoffs": 4,
            "fasteners": 8,
            "standoff_height_mm": 6,
            "note": "Use metal or rated nylon hardware; preserve front micro-USB and rear SWD service access.",
        },
        "power_deck_standoffs": {"thread": "M3", "standoffs": 4, "fasteners": 8},
        "upper_deck_regulators": {
            "pi_regulator": "Pololu D24V90F5, 5 V nominal, 40.6 x 20.3 mm, four M2 holes",
            "servo_regulator": "Pololu D36V50F6, 6 V nominal, 25.4 x 25.4 mm, three M2 holes",
            "thread": "M2",
            "metal_standoffs": 7,
            "fasteners": 14,
            "standoff_height_mm": 6,
            "note": "Use soldered appropriately sized conductors rather than a breadboard. Preserve terminal/wire service, airflow, strain relief, fusing, and the two electrically separate output rails.",
        },
        "motor_power_contactor": {
            "relay": "Panasonic CB1A-R-M-12V sealed SPST-NO automotive relay",
            "contact_rating": "40 A at 14 V DC",
            "coil": "12 V, 134 mA, integral suppression resistor",
            "terminals": "6.3 mm quick-connect",
            "integral_bracket_mount": "One 5.4 mm path for an M5 fastener",
            "note": "Use the relay's integral metal bracket and the single modeled mount. Verify purchased-part fit, terminal retention and insulation, conductor support, dropout time, fault current, and independent fail-stopped cutoff before motion.",
        },
        "accessory_distribution_block": {
            "module": "Blue Sea Systems 5045 covered four-circuit ATO/ATC fuse block",
            "module_mm": [92.5, 43.8, 32.5],
            "mounting": "Two M4 paths on 65.1 mm centers",
            "cover": "Purchased integral insulating cover with labels",
            "reusable_strain_strap": 1,
            "limits": "Prototype ceiling: 6 A total and 5 A any branch; exact fuse values remain measured-load selections.",
            "note": "Confirm the delivered footprint, power-off cover removal with the service deck lifted, wire bends, terminal guards, labels, feeder protection, selective clearing, and thermal behavior before release.",
        },
        "power_harness_rails": {
            "printed_rails": 2,
            "paired_strap_stations": 8,
            "reusable_straps": 8,
            "note": "Route signal/audio/sensor wiring on the left and fused switched power/motor wiring on the right; confirm bundle and connector dimensions before release.",
        },
        "mic_cradle_to_shell": {"thread": "M3", "fasteners": 4, "inserts": 4},
        "speaker_plates_to_shell": {"thread": "M3", "fasteners": 4, "inserts": 4},
        "speakers_to_plates": {"thread": "M3 provisional", "fasteners": 8, "locknuts": 8},
        "stereo_audio_amplifiers": {
            "boards": "2 x Adafruit #3006 MAX98357A mono I2S amplifier",
            "thread": "M2",
            "fasteners": 4,
            "metal_standoffs": "4 x 6 mm",
            "channel_assignment": "Shared BCLK/LRCLK/DIN; one SD/MODE network selects left and the other right",
            "note": "Official PCB and two-hole pattern are modeled. The official 2022 STEP omits the terminal block now shipped pre-soldered; buy one current board and measure terminal, screwdriver, wire-bend, and header/direct-wire access before releasing both speaker plates.",
        },
        "cable_strain_relief_to_shell": {"thread": "M3", "fasteners": 2, "inserts": 2},
        "front_fascia_and_status_led_carriers": {"thread": "M2.5", "fasteners": 4, "inserts": 4},
        "front_tof_pods_to_fascia": {"thread": "M2.5", "fasteners": 4, "inserts": 4},
        "side_tof_pods_to_shell": {"thread": "M2.5", "fasteners": 4, "inserts": 4},
        "bumper_switch_plates": {
            "switches": "6 x Omron D2HW-C202MR sealed SPST-NC pin-plunger switches",
            "thread": "M3",
            "tray_fasteners": 12,
            "switch_fasteners": 12,
            "inserts": 12,
            "mounting": "Six rigid PETG plates clamp independently to blind inserts in the tray underside; the TPU bumper is not clamped by these screws.",
            "note": "Drawing-backed 13 mm switch-hole spacing, 0.4 mm nominal rest gap, 2.0 mm nominal actuation, side-lead strain clearance, and paired 2.4 mm rigid overtravel stops. Verify purchased parts and every direction before motor power.",
        },
        "rear_service_panel": {
            "thread": "M3",
            "fasteners": 4,
            "inserts": 4,
            "note": "Outer frame stays on the shell while individual connector cartridges are serviced.",
        },
        "rear_service_cartridges": {
            "parts": 3,
            "blank_parts": 1,
            "roles_left_to_right_from_rear": ["power/charge", "blank/access", "mute/status"],
            "thread": "M2.5",
            "fasteners": 6,
            "inserts": 6,
            "mute_switch": "E-Switch PVB3F230SS311 maintained SPDT, red ring LED, 16 mm two-flat panel cutout",
            "mute_switch_cutout": "16.0 mm diameter, 14.6 mm flats, 1.25 mm cartridge face",
            "mute_wiring": "Common receives fused microphone 5 V; listen throw feeds microphone VBUS; mute throw feeds the red ring through a calculated series resistor and a protected 3.3 V-compatible state input. Verify polarity and no USB backfeed.",
            "center_access": "Blank removable cartridge; no UART jack, PCB, carrier, or exposed power",
            "charge_inlet": "Switchcraft EN2P3M20 three-position sealed panel connector; EN2C3F20G2 cord mate",
            "charge_wiring": "Two contacts carry charge positive/negative from the Bioenno 14.6 V/2 A charger adapter; the third is CHARGER_PRESENT. Charge-only: no battery output or motor power. Mate/unmate only with charger AC removed.",
            "note": "Charge-only remains at left, the center stays blank for future qualified access, and physical mute remains at right.",
        },
        "estop_backing_plate": {
            "switch": "1 x IDEC XW1E-BV402M-R, 40 mm red mushroom, 2NC direct-opening",
            "thread": "M3",
            "fasteners": 4,
            "inserts": 4,
            "retention": "purchased panel-switch nut",
            "yellow_legend": "60 mm durable yellow emergency-stop legend/nameplate",
            "note": "The switch clamps only the removable 4 mm keyed mount panel. The lid, shell, backing collar, and power deck provide a 40 mm body/service passage; four shell-rooted bosses spread push/twist load. Confirm the delivered switch revision before final assembly.",
        },
        "head_face_and_rear_panels": {"thread": "M2.5", "fasteners": 8, "inserts": 8},
        "camera_carrier_to_head": {"thread": "M3", "fasteners": 4, "inserts": 4},
        "camera_board_to_carrier": {"thread": "M2 provisional", "fasteners": 4},
        "vent_inlay_to_lid": {"thread": "M2.5", "fasteners": 4, "inserts": 4},
        "head_led_carriers": {"thread": "M2.5", "fasteners": 4, "inserts": 4},
        "expression_neopixel_boards": {
            "boards": "4 x Adafruit 5975 NeoPixel JST breakout",
            "thread": "M2",
            "fasteners": 8,
            "spacers": "8 x 3 mm OD, board-to-carrier length selected after delivered-part measurement",
            "locknuts": 8,
            "connectors": "two 3-pin JST-SH 1 mm ports per board",
            "note": "Use separate fused 5 V LED power and common ground. Preserve the two independent data-chain option, cap brightness in software, and verify delivered STEP dimensions, cable bends, hotspotting, camera reflections, and diffuser color before final assembly.",
        },
        "pan_servo_plate": {"thread": "M3", "fasteners": 4, "inserts": 4},
        "head_servos": {
            "servos": "2 x Hitec D85MG 24T digital metal-gear servo",
            "mount_thread": "M3 with washers and locknuts",
            "mount_fasteners": 4,
            "note": "Two flange fasteners retain each servo. Size the regulated 6 V rail for both servos' measured dynamic and stall-current behavior; never power them from the Pi rail.",
        },
        "pan_axis": {
            "bearing": "1 x Koyo/JTEKT 6807-2RS, 35 x 47 x 7 mm",
            "horn": "1 x Hitec R-ML24 aluminum 24T horn",
            "retainer_thread": "M2.5",
            "retainer_fasteners": 4,
            "retainer_inserts": 4,
            "horn_thread": "M2",
            "horn_fasteners": 2,
            "note": "The fixed keyed collar captures the outer ring; the rotating neck journal, upper shoulder, and screw-on retainer capture the inner ring. Calibrate both printed diameters with the 6807 coupon before printing the full neck stack.",
        },
        "neck_to_tilt_yoke": {
            "thread": "M2.5",
            "fasteners": 4,
            "inserts": 4,
            "note": "Four screws clamp the fixed yoke base to blind pockets in the rotating neck's top flange; keep the central cable bore open.",
        },
        "tilt_adapters_to_head": {"thread": "M2.5", "fasteners": 6, "inserts": 6},
        "tilt_drive_horn": {
            "horn": "1 x Hitec R-ML24 aluminum 24T horn",
            "thread": "M2 x 0.4",
            "fasteners": 2,
            "threaded_stations_mm": [13, 16],
        },
        "tilt_passive_pivot": {
            "bearing": "1 x MF84ZZ flanged bearing, 4 x 8 x 3 mm, 9.2 x 0.6 mm flange",
            "shoulder_screw": "1 x McMaster 92981A143, 4 x 12 mm shoulder with M3 x 4 mm thread",
            "fasteners": 1,
            "purchased_bearings": 1,
            "note": "The shoulder screw fixes into the blind yoke insert while its 4 mm shoulder runs in the MF84ZZ inner ring; do not clamp the moving shell directly to the fixed yoke.",
        },
    },
}


def material_profile_for(name: str) -> str:
    if name.startswith(("bumper_q_", "lid_reveal_half_", "wheel_")):
        return "tpu_95a"
    if name.startswith(("eye_glow_", "front_status_left", "front_status_right")):
        return "translucent_petg"
    if name.startswith(
        (
            "base_tray_half_",
            "base_seam_plate",
            "body_seam_plate_",
            "bumper_seam_plate_",
            "battery_cradle",
            "motor_pod",
            "front_idler_",
            "power_service_deck",
            "motor_controller_mount",
            "safety_mcu_mount",
            "pan_servo_mount",
            "pan_bearing_retainer",
            "head_tilt_",
            "estop_backing_plate",
            "estop_well",
        )
    ):
        return "petg_structural"
    if name.startswith(
        (
            "tof_pod_",
            "speaker_mount_",
            "mic_array_cradle",
            "camera_carrier",
            "head_eye_led_carrier_",
            "front_status_led_carrier_",
            "bumper_switch_mount_",
            "top_cable_strain_relief",
            "top_vent_inlay",
            "power_harness_rail_",
            "rear_service_cartridge_",
        )
    ):
        return "petg_detail"
    return "petg_shell"


def color_profile_for(name: str) -> str:
    if name.startswith(
        (
            "body_shell_q_",
            "side_fairing_",
            "head_shell",
            "head_rear_cover",
        )
    ) or name == "neck":
        return "cream"
    if name.startswith(("top_lid_half_", "hub_ring_")):
        return "teal"
    if name.startswith(("lid_reveal_half_", "rear_service_panel")) or name == "power_service_deck":
        return "dark_teal"
    if name.startswith(
        (
            "bumper_q_",
            "wheel_",
            "front_sensor_",
            "eye_socket_",
        )
    ) or name in (
        "head_faceplate",
        "top_vent_inlay",
        "neck_collar",
        "estop_well",
    ):
        return "charcoal"
    if name.startswith(("eye_glow_", "front_status_")) and not name.startswith(
        "front_status_led_carrier_"
    ):
        return "translucent_lime"
    if name.startswith("eyebrow_"):
        return "blue"
    return "dark_gray"


def support_guidance_for(name: str):
    if name.startswith("body_shell_q_"):
        return {
            "supports": "build_plate_only",
            "brim_mm": 8,
            "note": "Review the roof and sensor recess in the slicer; keep supports off cosmetic exterior faces.",
        }
    if name in ("head_shell", "head_tilt_yoke"):
        return {
            "supports": "build_plate_only",
            "brim_mm": 6,
            "note": "Inspect yoke/post bridges and remove support only through service openings.",
        }
    if name in ("head_tilt_drive_adapter", "head_tilt_passive_cartridge"):
        return {
            "supports": "none_expected",
            "brim_mm": 2,
            "note": "Print broad face down; inspect three shell holes plus the horn or sleeve-bushing center interface.",
        }
    if name == "head_faceplate":
        return {
            "supports": "none_expected",
            "brim_mm": 2,
            "note": "Keep the stepped camera annulus facing upward and supports out of the optical bore; inspect all concentric walls in the slicer.",
        }
    if name == "top_vent_inlay":
        return {
            "supports": "none_expected",
            "brim_mm": 1,
            "note": "Print the broad underside on the bed; verify all nine acoustic slots and four M2.5 clearance holes remain open.",
        }
    if name == "estop_well":
        return {
            "supports": "none_expected",
            "brim_mm": 2,
            "note": "Print the broad recessed flange down; clean the keyed 22.5 mm switch opening and all four underside M3 insert pockets before the hardware fit test.",
        }
    if name.startswith("wheel_"):
        return {
            "supports": "none_expected",
            "brim_mm": 3,
            "note": "Print on one intact sidewall; inspect all 24 transverse tread grooves and the recessed hub seat before slicing.",
        }
    if name.startswith(("motor_pod_", "front_idler_pod_")):
        return {
            "supports": "none_expected",
            "brim_mm": 5,
            "note": "Axle/bearing axis is vertical; inspect the service opening and flange preview before slicing.",
        }
    if name.startswith("side_fairing_"):
        return {"supports": "none_expected", "brim_mm": 4, "note": "Print broad face down."}
    if name.startswith(("body_seam_plate_", "bumper_seam_plate_")) or name == "base_seam_plate":
        return {
            "supports": "none_expected",
            "brim_mm": 2,
            "note": "Print the broad plate face down with both alignment pilots vertical and pointing upward; inspect pilot roots in the slicer.",
        }
    if name.startswith("power_harness_rail_"):
        return {
            "supports": "none_expected",
            "brim_mm": 3,
            "note": "Print on the long sidewall so the U-channel and paired strap slots remain support-free.",
        }
    if name.startswith("rear_service_cartridge_"):
        return {
            "supports": "none_expected",
            "brim_mm": 1,
            "note": "Print the flush outer cap on the bed; inspect the stepped tongue and both M2.5 clearance holes.",
        }
    if name.startswith("bumper_switch_mount_"):
        return {
            "supports": "none_expected",
            "brim_mm": 2,
            "note": "Print broad face down; keep both tray-fastener holes clean and flat-test the tray seating face.",
        }
    return {"supports": "none_expected", "brim_mm": 0, "note": "Verify slicer preview for local bridges."}


def release_status_for(name: str) -> str:
    if name == "head_faceplate":
        return "prototype_only_pending_camera_fov_focus_and_reflection_test"
    if name.startswith(
        ("eye_glow_", "eye_socket_", "head_eye_led_carrier_", "front_status_")
    ):
        return "prototype_only_pending_adafruit_5975_fit_cable_and_diffusion_test"
    if name.startswith("base_tray_half_"):
        return "prototype_only_pending_split_pilot_and_bumper_switch_hardware_tests"
    if name.startswith("bumper_q_"):
        return "prototype_only_pending_split_pilot_tpu_material_and_six_direction_actuation_test"
    if name.startswith("bumper_switch_mount_"):
        return "prototype_only_pending_purchased_d2hw_fit_actuation_rebound_and_broken_wire_test"
    if name.startswith(
        ("body_shell_q_", "body_seam_plate_", "bumper_seam_plate_")
    ) or name == "base_seam_plate":
        return "prototype_only_pending_split_pilot_fit_test"
    if name in ("estop_backing_plate", "estop_well"):
        return "prototype_only_pending_purchased_xw1e_fit_push_twist_and_independent_cutoff_test"
    if name.startswith("power_harness_rail_"):
        return "prototype_only_pending_bundle_connector_and_strap_measurement"
    if name.startswith(("wheel_", "hub_ring_", "hub_", "motor_pod_")):
        return "prototype_only_pending_purchased_pololu_drivetrain_and_loaded_floor_test"
    if name.startswith("head_tilt_") or name in (
        "neck",
        "neck_collar",
        "pan_servo_mount",
        "pan_bearing_retainer",
    ):
        return "prototype_only_pending_d85mg_horns_bearings_and_complete_head_motion_test"
    if name.startswith("front_idler_"):
        return "prototype_only_pending_wds_615_m6_8_65_608_stock_spacer_locknut_axial_play_and_loaded_floor_test"
    if name == "safety_mcu_mount":
        return "prototype_only_pending_pico2_board_standoff_usb_swd_and_watchdog_test"
    if name == "motor_controller_mount":
        return "prototype_only_pending_mdds10_board_terminal_cooling_polarity_and_load_test"
    if name == "power_service_deck":
        return "prototype_only_pending_regulator_panasonic_cb1a_relay_blue_sea_5045_fit_wiring_fusing_and_cutoff_test"
    if name == "battery_cradle":
        return "prototype_only_pending_bioenno_blf1203ab_purchased_fit_lead_current_runtime_padding_and_loaded_retention_test"
    if name.startswith("speaker_mount_"):
        return "prototype_only_pending_current_adafruit_3006_terminal_header_and_audio_test"
    if name == "rear_service_panel":
        return "prototype_only_pending_cartridge_insert_fit_flushness_and_external_service_test"
    if name == "rear_service_cartridge_mute_status":
        return "prototype_only_pending_pvb3_switch_nut_harness_led_resistor_usb_backfeed_and_privacy_test"
    if name == "rear_service_cartridge_power_charge":
        return "prototype_only_pending_en2_charge_adapter_polarity_charger_present_motion_inhibit_and_mating_test"
    if name == "rear_service_cartridge_blank_access":
        return "prototype_only_blank_access_cartridge_no_connector_installed"
    if name.startswith("rear_service_cartridge_"):
        return "prototype_only_blank_pending_selected_connector_cutout_keying_strain_relief_and_electrical_test"
    return "prototype_print_candidate"


def oriented_and_grounded(shape, rotations):
    oriented = shape
    axes = {"x": Axis.X, "y": Axis.Y, "z": Axis.Z}
    for axis_name, angle in rotations:
        oriented = oriented.rotate(axes[axis_name], angle)
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


def first_layer_contact_area(shape, sample_height: float = 0.2) -> float:
    """Approximate bed contact using the first sample-height slice volume."""
    box = shape.bounding_box()
    probe = Box(
        float(box.max.X - box.min.X) + 2.0,
        float(box.max.Y - box.min.Y) + 2.0,
        sample_height,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    return float((shape & probe).volume) / sample_height


def export_print_ready(p: Params, bed: float, margin: float):
    PRINT_READY_DIR.mkdir(parents=True, exist_ok=True)
    for path in PRINT_READY_DIR.glob("*.stl"):
        path.unlink()

    inventory = canonical_inventory(p)
    head_torque = head_static_torque_estimate(p, inventory)
    if (
        head_torque["estimated_combined_static_gravity_torque_kg_cm"]
        >= head_torque["d85mg_peak_efficiency_torque_at_6v_kg_cm"]
    ):
        raise SystemExit(
            "Head static torque estimate exceeds the D85MG peak-efficiency torque; "
            "rebalance or lighten the moving head before exporting."
        )
    max_allowed = bed - margin
    manifest = {
        "units": "mm",
        "source": "cad/python/robot_body_print.py",
        "assembly_source": "cad/python/robot_body.py",
        "split_source": "cad/python/robot_body_split.py",
        "bed_nominal_mm": bed,
        "margin_mm": margin,
        "max_allowed_xy_span_mm": max_allowed,
        "printer_target": {
            "model": TARGET_PRINTER,
            "nozzle_diameter_mm": TARGET_NOZZLE_MM,
            "build_volume_mm": [256.0, 256.0, 256.0],
            "plate_type": "Textured PEI Plate",
        },
        "first_layer_contact_sample_height_mm": 0.2,
        "minimum_first_layer_contact_area_mm2": 50.0,
        "release_warning": (
            "Print-ready means oriented and bed-validated, not hardware-release-ready. "
            "Honor each part's release_status and the CAD component coverage gates."
        ),
        "alignment_pilot_contract": {
            "count": 18,
            "diameter_mm": 2.0 * p.split_pilot_radius,
            "projection_mm": p.split_pilot_length - p.split_pilot_overlap,
            "radial_clearance_mm": p.split_pilot_radial_clearance,
            "axial_clearance_mm": p.split_pilot_axial_clearance,
            "print_orientation": "All nine joiner plates place their pilots vertically upward.",
            "release_gate": "Print and cycle-test one representative pilot/recess interface before the large split shell, tray, or bumper pieces.",
        },
        "camera_optical_contract": {
            "module": "Raspberry Pi Camera Module 3 Wide",
            "horizontal_fov_degrees": p.camera_horizontal_fov_degrees,
            "lens_front_recess_mm": p.camera_lens_front_recess,
            "shell_faceplate_aperture_radius_mm": p.head_camera_aperture_radius,
            "front_bezel_clear_radius_mm": p.head_lens_clear_radius,
            "construction": "Stepped annular bezel fused to the removable black faceplate; no printed disk crosses the optical path.",
            "release_gate": "Install the purchased camera and verify full-resolution corner illumination, focus, reflections, and pan/tilt image quality before release.",
        },
        "head_motion_contract": {
            "servos": "2 x Hitec D85MG",
            "servo_size_mm": [p.servo_body_length, p.servo_body_width, p.servo_body_height],
            "servo_mount_spacing_mm": p.servo_mount_spacing,
            "servo_mount_hole_diameter_mm": p.servo_mount_hole,
            "servo_spline": "24T, 5.76 mm nominal major diameter",
            "horns": "2 x Hitec R-ML24 aluminum horn",
            "horn_threaded_stations_mm": list(p.servo_horn_threaded_offsets),
            "pan_support_bearing": "Koyo/JTEKT 6807-2RS, 35 x 47 x 7 mm",
            "tilt_passive_bearing": "MF84ZZ, 4 x 8 x 3 mm with 9.2 x 0.6 mm flange",
            "tilt_shoulder_screw": "McMaster 92981A143, 4 x 12 mm shoulder, M3 x 4 mm thread",
            "motion_range_degrees": {"pan": [-60, 60], "tilt": [-20, 20]},
            "release_gate": "Print the 6807 coupon, install purchased hardware, confirm free bearing fits and fastener lengths, weigh the complete moving head, verify regulator current margin and cable sweep, then cycle the complete head through every sampled pan/tilt pose without collision or bearing preload.",
            "static_torque_estimate": head_torque,
        },
        "safety_mcu_contract": {
            "board": "Raspberry Pi Pico 2 without headers",
            "mechanical_reference": "Raspberry Pi Pico 2 Datasheet Figure 3 and STEP RP-009061-CA-2",
            "board_mm": [p.pico2_board_length, p.pico2_board_width, p.pico2_board_thickness],
            "overall_step_envelope_mm": [p.pico2_overall_length, p.pico2_board_width, p.pico2_overall_height],
            "mount_hole_diameter_mm": p.pico2_mount_hole,
            "mount_spacing_mm": [p.pico2_mount_spacing_length, p.pico2_mount_spacing_width],
            "orientation": "Micro-USB faces robot-front (-X); SWD faces inward/rear (+X).",
            "release_gate": "Install the purchased board and prove USB programming, SWD access, connector retention, watchdog output, normally-closed bumper input handling, and independent fail-stopped motor cutoff before driving.",
        },
        "power_regulator_contract": {
            "pi_rail": {
                "regulator": "Pololu D24V90F5",
                "output": "5 V nominal",
                "board_mm": [p.pi_regulator_length, p.pi_regulator_width, p.pi_regulator_height],
                "mount_spacing_mm": [p.pi_regulator_mount_spacing_x, p.pi_regulator_mount_spacing_y],
                "mount_hole_mm": p.pi_regulator_mount_hole,
                "metal_standoff_height_mm": p.pi_regulator_standoff_height,
            },
            "head_servo_rail": {
                "regulator": "Pololu D36V50F6",
                "output": "6 V nominal",
                "board_mm": [p.servo_regulator_length, p.servo_regulator_width, p.servo_regulator_height],
                "triangular_mount_offset_mm": p.servo_regulator_mount_offset,
                "mount_hole_mm": p.servo_regulator_mount_hole,
                "metal_standoff_height_mm": p.servo_regulator_standoff_height,
            },
            "release_gate": "Inspect purchased revisions; use fused, strain-relieved conductors; verify polarity, output voltage, startup/inrush, Pi undervoltage margin, dual-servo transients, thermal behavior, airflow, EMI/audio behavior, and fault shutdown before mobile use.",
        },
        "accessory_distribution_contract": {
            "module": "Blue Sea Systems 5045 covered four-circuit ATO/ATC fuse block",
            "module_mm": [p.power_distribution_length, p.power_distribution_width, p.power_distribution_height],
            "mount_spacing_mm": p.power_distribution_mount_spacing,
            "mount_hole_mm": p.power_distribution_mount_hole,
            "purchased_cover": "Integral insulating cover and labels; no printed distribution cover",
            "block_rating_a": p.power_distribution_block_rating_a,
            "per_circuit_rating_a": p.power_distribution_circuit_rating_a,
            "provisional_limits_a": {"total": p.power_distribution_total_limit_a, "any_branch": p.power_distribution_branch_limit_a},
            "source_protection": "Battery-near accessory feeder fuse remains mandatory; branch fuses do not protect the feeder upstream of the block.",
            "release_gate": "Inspect the purchased module and cover; clamp the harness independently; measure all loads; select fuse values; verify terminal guards and wire bends; short each far-end output for selective clearing; thermal-soak all branches; verify labels, polarity, no backfeed, power-off-only fuse service, and no path around motor cutoff or charger inhibit.",
        },
        "mobile_power_mechanical_contract": {
            "battery_status": "Bioenno BLF-1203AB prototype fit baseline; not a household-motion release endorsement.",
            "battery": "Bioenno BLF-1203AB 12 V 3 Ah LiFePO4, rotated flat",
            "battery_envelope_mm": [p.battery_max_length, p.battery_max_width, p.battery_max_height],
            "cradle_mm": [p.battery_cradle_length, p.battery_cradle_width],
            "retention": "Two 20 mm real straps, positive printed side/end locators, nonconductive padding, and four M3 cradle fasteners; printed rails are not sole retention.",
            "charger": "Bioenno BPC-1502DC 14.6 V/2 A through a dedicated EN2 adapter cable",
            "rear_charge_inlet": "Switchcraft EN2P3M20 with EN2C3F20G2 cord mate; charge-only plus CHARGER_PRESENT",
            "motor_cutoff_relay": "Panasonic CB1A-R-M-12V with integral metal bracket",
            "relay_body_mm": [p.motor_cutoff_body_length, p.motor_cutoff_body_width, p.motor_cutoff_body_height],
            "relay_bracket_mm": [p.motor_cutoff_bracket_length, p.motor_cutoff_bracket_width, p.motor_cutoff_bracket_thickness],
            "relay_mount_hole_mm": p.motor_cutoff_mount_hole,
            "relay_contact_rating_a": p.motor_cutoff_contact_rating_a,
            "relay_coil_current_a": p.motor_cutoff_coil_current_a,
            "release_gate": "Inspect the purchased BLF-1203AB, charger, EN2 pair, Panasonic relay, and Blue Sea block; verify lead exits, charging, no live output at the rear inlet, charger-present motion inhibit, fusing, reverse-polarity protection, terminal insulation and restraint, relay suppression/dropout, sustained current below 5.6 A, BMS behavior, 45-minute runtime with reserve, retention, thermal behavior, and independent fail-stopped motor cutoff. Electrical-engineering review is required before household motion release.",
        },
        "rear_drivetrain_contract": {
            "motor": "Pololu #4867 99:1 Metal Gearmotor 25Dx69L mm MP 12V with 48 CPR Encoder",
            "motor_ratio": "98.78:1",
            "no_load_rpm_at_12v": p.motor_no_load_rpm,
            "stall_current_a_each": p.motor_stall_current_a,
            "stall_torque_kg_cm_each": p.motor_stall_torque_kg_cm,
            "motor_body_length_mm": p.motor_body_length,
            "motor_body_diameter_mm": p.motor_body_diameter,
            "shaft_mm": [p.motor_shaft_diameter, p.motor_shaft_length],
            "bracket": "Pololu #1569 metal 25D bracket",
            "hub": "Pololu #1997 4 mm shaft M3 aluminum hub",
            "wheel_core": "Printed PETG core with TPU tire and four M3 aluminum-hub screws",
            "release_gate": "Install purchased motors, brackets, and hubs; verify D-shaft/set-screw engagement, screw lengths, encoder routing, wheel retention, loaded current and temperature, deterministic cutoff, and supervised skid-turn behavior on target floors.",
        },
        "estop_safety_contract": {
            "switch": "IDEC XW1E-BV402M-R",
            "operator": "40 mm red mushroom, push-lock, pull-or-clockwise-turn reset",
            "contacts": "2NC direct-opening; use in low-voltage cutoff/enable channels, never as the motor-current switching element",
            "mount_panel_thickness_mm": p.estop_mount_panel_thickness,
            "keyed_panel_opening_mm": {
                "circular_diameter": p.estop_panel_hole,
                "keyed_width": p.estop_keyed_width,
                "notch_width": p.estop_key_notch_width,
            },
            "body_envelope_mm": [p.estop_body_width, p.estop_body_width, p.estop_body_depth],
            "terminal_service_depth_mm": p.estop_terminal_service_depth,
            "yellow_legend_outer_diameter_mm": p.estop_legend_outer_diameter,
            "release_gate": "Install the purchased switch and durable yellow legend; verify nut engagement, anti-rotation, terminal access, wire bend, push/twist loading, both NC channels, and independent motor-power cutoff before powered motion.",
        },
        "bumper_actuation_contract": {
            "switch_count": 6,
            "switch": "Omron D2HW-C202MR sealed SPST-NC pin-plunger",
            "switch_logic": "normally_closed_broken_wire_detecting_input",
            "switch_envelope_mm": [p.bumper_switch_length, p.bumper_switch_height, p.bumper_switch_width],
            "switch_mount_spacing_mm": p.bumper_switch_mount_spacing,
            "free_position_max_mm": p.bumper_switch_free_position,
            "operating_position_mm": p.bumper_switch_operating_position,
            "operating_position_tolerance_mm": p.bumper_switch_operating_tolerance,
            "total_travel_position_max_mm": p.bumper_switch_total_travel_position,
            "fixed_reference": "PETG switch plates fastened to blind tray inserts",
            "moving_reference": "locally compliant TPU bumper inner wall",
            "nominal_rest_gap_mm": p.bumper_switch_nominal_gap,
            "nominal_actuation_travel_mm": p.bumper_switch_actuation_travel,
            "rigid_stop_travel_mm": p.bumper_switch_stop_travel,
            "plate_bottom_z_mm": p.body_bottom - p.tray_thickness - p.bumper_switch_plate_thickness,
            "plate_top_z_mm": p.body_bottom - p.tray_thickness,
            "release_gate": "Install purchased D2HW-C202MR switches and prove no preload, worst-case positive actuation, rigid-stop protection, strain-relieved leads, electrical continuity break, rebound, broken-wire detection, and fail-stopped motor cutoff from all six zones before powered driving.",
        },
        "replaced_main_parts": sorted(REPLACED_MAIN_PARTS),
        "material_profiles": MATERIAL_PROFILES,
        "color_profiles": COLOR_PROFILES,
        "assembly_hardware": ASSEMBLY_HARDWARE,
        "parts": {},
    }

    failures = []
    for name, item in sorted(inventory.items()):
        source_shape = item["shape"]
        rotations, rationale = orientation_for(name)
        shape = oriented_and_grounded(source_shape, rotations)

        if not shape.is_valid:
            failures.append(f"{name}: invalid after orientation")
        if len(shape.solids()) != 1:
            failures.append(f"{name}: {len(shape.solids())} solids after orientation")

        volume_delta = abs(float(source_shape.volume) - float(shape.volume))
        if volume_delta > max(0.05, float(source_shape.volume) * 1e-8):
            failures.append(f"{name}: orientation changed volume by {volume_delta:.4f} mm^3")

        box = shape.bounding_box()
        if abs(float(box.min.Z)) > 0.01:
            failures.append(f"{name}: not grounded (min Z={float(box.min.Z):.4f})")

        part_spans = spans(shape)
        if max(part_spans["x"], part_spans["y"]) > max_allowed + 0.01:
            failures.append(
                f"{name}: oriented XY span exceeds bed "
                f"({max(part_spans['x'], part_spans['y']):.2f} > {max_allowed:.2f})"
            )

        contact_area = first_layer_contact_area(shape)
        if contact_area < 50.0:
            failures.append(
                f"{name}: first-layer contact area is too small ({contact_area:.2f} < 50.00 mm^2)"
            )

        profile = material_profile_for(name)
        color_profile = color_profile_for(name)
        support = support_guidance_for(name)
        filename = f"{name}.stl"
        export_stl(shape, PRINT_READY_DIR / filename)
        manifest["parts"][name] = {
            "stl": filename,
            "geometry_source": item["source"],
            "rotation_deg": [
                {"axis": axis_name.upper(), "angle": angle}
                for axis_name, angle in rotations
            ],
            "orientation_rationale": rationale,
            "span_mm": part_spans,
            "grounded_z_mm": float(box.min.Z),
            "source_volume_mm3": float(source_shape.volume),
            "first_layer_contact_area_mm2": contact_area,
            "material_profile": profile,
            "filament_material": "TPU 95A" if profile == "tpu_95a" else "PETG",
            "color_profile": color_profile,
            "color_hex": COLOR_PROFILES[color_profile]["hex"],
            "filament_group": f"{profile}:{color_profile}",
            "support_guidance": support,
            "release_status": release_status_for(name),
        }

    if failures:
        raise SystemExit("Print-ready export failed:\n- " + "\n- ".join(failures))

    manifest_path = PRINT_READY_DIR / "codex_robot_body_v1_print_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(
        "PRINT_READY_VALID "
        f"parts={len(inventory)} bed={bed:.0f}mm margin={margin:.0f}mm "
        f"max_allowed={max_allowed:.0f}mm grounded=ok contact=ok "
        "volumes=preserved materials=assigned"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bed", type=float, default=TARGET_BED_MM)
    parser.add_argument("--margin", type=float, default=TARGET_BED_MARGIN_MM)
    args = parser.parse_args()
    export_print_ready(Params(), args.bed, args.margin)


if __name__ == "__main__":
    main()
