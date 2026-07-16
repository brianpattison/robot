"""Render the build123d robot body exports with concept-art materials.

Run from the repository root with Blender 5.x:

    /Applications/Blender.app/Contents/MacOS/Blender -b --python cad/blender/render_robot_body.py

The imported STL files are the same generated inventory used by the CAD
exports. The exploded image moves those parts apart for review; it does not
invent a second set of geometry.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[2]
EXPORT_DIR = ROOT / "cad" / "exports"
IMAGE_DIR = ROOT / "docs" / "images"


COLORS = {
    "cream": (0.94, 0.87, 0.76, 1.0),
    "cream_highlight": (1.0, 0.95, 0.86, 1.0),
    "teal": (0.04, 0.43, 0.52, 1.0),
    "dark_teal": (0.02, 0.20, 0.24, 1.0),
    "charcoal": (0.025, 0.03, 0.035, 1.0),
    "dark_gray": (0.08, 0.09, 0.10, 1.0),
    "lime": (0.75, 1.0, 0.15, 1.0),
    "blue": (0.03, 0.18, 0.78, 1.0),
    "red": (0.82, 0.035, 0.025, 1.0),
    "safety_yellow": (0.95, 0.72, 0.03, 1.0),
    "glass": (0.015, 0.045, 0.08, 1.0),
    "glass_highlight": (0.15, 0.36, 0.52, 1.0),
    # Honey-toned wood proxy: bright enough to bounce the reference image's
    # warm daylight without swallowing the charcoal bumper and wheel details.
    "floor": (0.34, 0.16, 0.055, 1.0),
}


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for material in list(bpy.data.materials):
        bpy.data.materials.remove(material)


def material(name: str, color, metallic=0.0, roughness=0.42, emission=None):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = color
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    if emission:
        bsdf.inputs["Emission Color"].default_value = emission
        # Keep the lime lenses visibly emissive without clipping them to white;
        # their shape and color need to remain reviewable against the concept.
        bsdf.inputs["Emission Strength"].default_value = 0.8
    return mat


def material_for(name: str, mats):
    if name.startswith(("body_shell", "base_tray", "battery_cradle")):
        return mats["cream"]
    if name.startswith("side_fairing"):
        return mats["cream"]
    if name.startswith(("head_shell", "head_rear_cover")) or name == "neck":
        return mats["cream_highlight"]
    if name.startswith(("neck_collar", "pan_servo_mount", "pan_bearing_retainer", "head_tilt_")):
        return mats["dark_gray"]
    if name.startswith("top_lid"):
        return mats["teal"]
    if name.startswith("lid_reveal"):
        return mats["dark_teal"]
    if name.startswith("rear_service_panel"):
        return mats["dark_teal"]
    if name.startswith("top_vent") or name.startswith("front_sensor"):
        return mats["charcoal"]
    if name.startswith("bumper") or name.startswith("wheel_"):
        return mats["charcoal"]
    if name.startswith(("motor_pod", "front_idler_pod")):
        return mats["dark_gray"]
    if name.startswith(("mic_array_cradle", "speaker_mount", "tof_pod")):
        return mats["dark_gray"]
    if name == "power_service_deck":
        return mats["dark_teal"]
    if name.startswith("power_harness_rail_"):
        return mats["dark_gray"]
    if name.startswith("hub_ring"):
        return mats["teal"]
    if name.startswith("hub_"):
        return mats["dark_gray"]
    if name.startswith("head_faceplate") or name.startswith("eye_socket"):
        return mats["charcoal"]
    if name.startswith(("front_status_led_carrier", "head_eye_led_carrier")):
        return mats["dark_gray"]
    if name.startswith("eye_glow") or name.startswith("front_status"):
        return mats["lime"]
    if name.startswith("eyebrow"):
        return mats["blue"]
    if name.startswith("preview_camera_lens_hardware"):
        return mats["glass_highlight"]
    if name.startswith("head_lens"):
        return mats["dark_gray"]
    if name.startswith(("estop_backing", "estop_well")):
        return mats["dark_gray"]
    if name.startswith("preview_estop"):
        if "yellow_legend" in name:
            return mats["safety_yellow"]
        return mats["red"]
    return mats["dark_gray"]


def import_stl(path: Path, mat):
    if hasattr(bpy.ops.wm, "stl_import"):
        bpy.ops.wm.stl_import(filepath=str(path))
    else:
        bpy.ops.import_mesh.stl(filepath=str(path))
    obj = bpy.context.object
    obj.name = path.stem
    obj.data.materials.append(mat)
    return obj


def is_main_preview_part(path: Path):
    """Avoid importing printer-split duplicates into the assembled preview."""
    name = path.stem
    if "_q_" in name or "_half_" in name or "_bridge" in name or "_seam_plate" in name:
        return False
    if name.startswith("side_fairing_") and name.endswith(("_front", "_rear")):
        return False
    return True


def load_parts(mats):
    objects = []
    for path in sorted(EXPORT_DIR.glob("*.stl")):
        if path.name.startswith("fit_") or not is_main_preview_part(path):
            continue
        objects.append(import_stl(path, material_for(path.stem, mats)))
    # The durable yellow E-stop legend is purchased hardware rather than a
    # printable body part, but it belongs in assembled/exploded concept review.
    legend_path = EXPORT_DIR / "fit_estop_yellow_legend.stl"
    if legend_path.exists():
        legend = import_stl(legend_path, mats["safety_yellow"])
        legend.name = "preview_estop_yellow_legend"
        objects.append(legend)
    return objects


def load_fit_parts(mats):
    colors = {
        "fit_pi5": mats["fit_pi"],
        "fit_pi5_board": mats["fit_pi_board"],
        "fit_motor_controller": mats["fit_motor"],
        "fit_motor_controller_board": mats["fit_pi_board"],
        "fit_motor_controller_terminal_service": mats["fit_power"],
        "fit_motor_controller_airflow": mats["fit_service"],
        "fit_drive_motor_left": mats["fit_motor"],
        "fit_drive_motor_right": mats["fit_motor"],
        "fit_drive_motor_bracket_left": mats["fit_structure"],
        "fit_drive_motor_bracket_right": mats["fit_structure"],
        "fit_drive_motor_hub_left": mats["carry_metal"],
        "fit_drive_motor_hub_right": mats["carry_metal"],
        "fit_drive_motor_cable_left": mats["fit_power"],
        "fit_drive_motor_cable_right": mats["fit_power"],
        "fit_battery": mats["fit_battery"],
        "fit_battery_lead_service": mats["fit_power"],
        "fit_safety_mcu": mats["fit_safety"],
        "fit_safety_mcu_board": mats["fit_pi_board"],
        "fit_safety_mcu_header_left": mats["fit_signal"],
        "fit_safety_mcu_header_right": mats["fit_signal"],
        "fit_safety_mcu_usb_service": mats["fit_service"],
        "fit_safety_mcu_swd_service": mats["fit_service"],
        "fit_future_ai_hat_clearance": mats["fit_ai"],
        "fit_pan_servo": mats["fit_servo"],
        "fit_pan_servo_horn": mats["carry_metal"],
        "fit_pan_bearing": mats["carry_metal"],
        "fit_tilt_servo": mats["fit_servo"],
        "fit_tilt_servo_horn": mats["carry_metal"],
        "fit_tilt_passive_bushing": mats["carry_metal"],
        "fit_tilt_shoulder_bolt": mats["carry_metal"],
        "fit_servo_cable_corridor": mats["fit_servo"],
        "fit_camera_module_3": mats["fit_camera"],
        "fit_camera_fov": mats["fit_camera"],
        "fit_head_eye_led_left": mats["fit_led"],
        "fit_head_eye_led_right": mats["fit_led"],
        "fit_front_status_led_left": mats["fit_led"],
        "fit_front_status_led_right": mats["fit_led"],
        "fit_pi_buck_regulator": mats["fit_power"],
        "fit_pi_buck_terminal_service_front": mats["fit_service"],
        "fit_pi_buck_terminal_service_rear": mats["fit_service"],
        "fit_servo_regulator": mats["fit_servo"],
        "fit_servo_regulator_wire_service": mats["fit_service"],
        "fit_motor_cutoff_relay": mats["fit_safety"],
        "fit_motor_cutoff_terminal_service": mats["fit_power"],
        "fit_motor_cutoff_bracket": mats["fit_structure"],
        "fit_power_harness_left": mats["fit_signal"],
        "fit_power_harness_right": mats["fit_power"],
        "fit_rear_service_bay": mats["fit_service"],
        "fit_mic_array": mats["fit_audio"],
        "fit_speaker_left": mats["fit_audio"],
        "fit_speaker_right": mats["fit_audio"],
        "fit_tof_front_left": mats["fit_sensor"],
        "fit_tof_front_right": mats["fit_sensor"],
        "fit_tof_side_left": mats["fit_sensor"],
        "fit_tof_side_right": mats["fit_sensor"],
        "fit_estop_switch_body": mats["fit_safety"],
        "fit_estop_threaded_barrel": mats["fit_safety"],
        "fit_estop_terminal_service": mats["fit_service"],
        "fit_estop_yellow_legend": mats["safety_yellow"],
        "fit_mute_switch_body": mats["fit_structure"],
        "fit_mute_switch_bezel": mats["fit_structure"],
        "fit_mute_switch_actuator": mats["dark_gray"],
        "fit_mute_switch_led_ring": mats["red"],
        "fit_mute_switch_terminal_service": mats["fit_service"],
        "fit_charge_jack_body": mats["dark_gray"],
        "fit_charge_jack_bezel": mats["dark_gray"],
        "fit_charge_jack_terminal_service": mats["fit_power"],
        "fit_charge_jack_plug_service": mats["fit_service"],
    }
    objects = []
    for path in sorted(EXPORT_DIR.glob("fit_*.stl")):
        if path.stem.startswith("fit_bumper_switch_"):
            fallback = mats["fit_safety"]
        elif path.stem.startswith("fit_front_idler_"):
            fallback = mats["fit_structure"]
        elif path.stem.startswith("fit_audio_amp_"):
            if "_standoff_" in path.stem:
                fallback = mats["fit_structure"]
            elif path.stem.endswith(("_header_service", "_screwdriver_service", "_speaker_wire")):
                fallback = mats["fit_service"]
            else:
                fallback = mats["fit_audio"]
        elif path.stem.startswith("fit_power_distribution_"):
            if path.stem.endswith(("_wire_service", "_fuse_service")):
                fallback = mats["fit_service"]
            else:
                fallback = mats["fit_power"]
        elif path.stem.endswith("_jst_service"):
            fallback = mats["fit_service"]
        elif "_led_" in path.stem and "_spacer_" in path.stem:
            fallback = mats["fit_structure"]
        else:
            fallback = (
                mats["fit_structure"]
                if path.stem.startswith(
                (
                    "fit_power_deck_standoff_",
                    "fit_pi_regulator_standoff_",
                    "fit_servo_regulator_standoff_",
                    "fit_safety_shelf_standoff_",
                    "fit_safety_mcu_standoff_",
                    "fit_motor_controller_standoff_",
                    "fit_motor_controller_plate_standoff_",
                    "fit_drive_motor_bracket_spacer_",
                )
                )
                else mats["fit_pi"]
            )
        objects.append(import_stl(path, colors.get(path.stem, fallback)))
    return objects


def load_split_joinery_parts(mats):
    """Load only the current manifest's large split pieces and their joiners."""
    manifest_path = EXPORT_DIR / "codex_robot_body_v1_split_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    selected = set()
    for group_name in ("body_shell", "base_tray", "bumper", "top_lid", "side_fairings"):
        group = manifest["assembly_groups"][group_name]
        for key in ("pieces", "joiners", "captured_gasket"):
            selected.update(group.get(key, []))

    objects = []
    for name in sorted(selected):
        path = EXPORT_DIR / f"{name}.stl"
        mat = mats["joinery"] if "_seam_plate" in name else material_for(name, mats)
        objects.append(import_stl(path, mat))
    return objects


def load_ground_z():
    params_path = EXPORT_DIR / "codex_robot_body_v1_parameters.json"
    params = json.loads(params_path.read_text(encoding="utf-8"))
    return params["wheel_center_z"] - params["wheel_radius"]


def add_floor(mats, ground_z):
    bpy.ops.mesh.primitive_plane_add(size=1600, location=(0, 0, ground_z))
    floor = bpy.context.object
    floor.name = "review_floor"
    floor.data.materials.append(mats["floor"])
    return floor


def look_at(obj, target):
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def add_camera(exploded: bool):
    location = (-1020, -900, 690) if exploded else (-525, -445, 335)
    bpy.ops.object.camera_add(location=location)
    camera = bpy.context.object
    camera.data.lens = 60 if exploded else 55
    camera.data.sensor_width = 36
    camera.data.clip_end = 3000
    look_at(camera, (0, 0, 190 if exploded else 132))
    bpy.context.scene.camera = camera
    return camera


def add_lights():
    """Build the concept art's warm, high-key daylight around the CAD model.

    The robot is roughly 300 mm wide, so the large emitters are intentional:
    they produce broad highlights across the cream shell instead of small hot
    spots. A weak warm sun adds the reference's window-light direction while
    the large area sources mimic room and floor bounce into the dark parts.
    """
    bpy.ops.object.light_add(type="AREA", location=(-390, -430, 590))
    key = bpy.context.object
    key.name = "warm_window_key"
    key.data.energy = 8200
    key.data.color = (1.0, 0.80, 0.60)
    key.data.shape = "DISK"
    key.data.size = 430
    look_at(key, (-25, 0, 135))

    bpy.ops.object.light_add(type="AREA", location=(350, -220, 370))
    fill = bpy.context.object
    fill.name = "warm_room_fill"
    fill.data.energy = 5400
    fill.data.color = (1.0, 0.93, 0.84)
    fill.data.shape = "DISK"
    fill.data.size = 430
    look_at(fill, (0, 0, 120))

    bpy.ops.object.light_add(type="AREA", location=(100, 340, 470))
    rim = bpy.context.object
    rim.name = "warm_window_rim"
    rim.data.energy = 4000
    rim.data.color = (1.0, 0.84, 0.68)
    rim.data.shape = "DISK"
    rim.data.size = 320
    look_at(rim, (0, 0, 165))

    # A camera-axis fill opens the black faceplate, bumper, wheel hubs, and
    # recessed sensor fascia without flattening the key/fill directionality.
    bpy.ops.object.light_add(type="AREA", location=(-440, -390, 260))
    front = bpy.context.object
    front.name = "warm_camera_fill"
    front.data.energy = 3500
    front.data.color = (1.0, 0.91, 0.80)
    front.data.shape = "DISK"
    front.data.size = 310
    look_at(front, (0, 0, 115))

    # Broad overhead bounce keeps the teal lid and cream roof rim luminous.
    bpy.ops.object.light_add(type="AREA", location=(0, 20, 650))
    overhead = bpy.context.object
    overhead.name = "warm_ceiling_bounce"
    overhead.data.energy = 2900
    overhead.data.color = (1.0, 0.94, 0.85)
    overhead.data.shape = "DISK"
    overhead.data.size = 600
    look_at(overhead, (0, 0, 100))

    # This low-energy sun supplies the gentle left-to-right directional shadow
    # visible in the concept without turning the review render theatrical.
    bpy.ops.object.light_add(
        type="SUN",
        rotation=(math.radians(28), math.radians(-18), math.radians(-38)),
    )
    sun = bpy.context.object
    sun.name = "warm_daylight_direction"
    sun.data.energy = 1.0
    sun.data.color = (1.0, 0.78, 0.56)
    sun.data.angle = math.radians(14)


def explode_object(obj):
    """Move each real printable part along a readable assembly direction."""
    name = obj.name
    shell_lift = 62.0
    head_lift = 145.0

    if name == "bumper_carrier":
        obj.location.x -= 48.0
        obj.location.z -= 18.0
    elif name.startswith("bumper_switch_mount_"):
        obj.location.z -= 8.0
        if name.endswith("left"):
            obj.location.y -= 10.0
        elif name.endswith("right"):
            obj.location.y += 10.0
    elif name == "base_tray":
        obj.location.z -= 18.0
    elif name in {"battery_cradle", "motor_controller_mount", "safety_mcu_mount"}:
        obj.location.z -= 2.0
    elif name == "power_service_deck":
        obj.location.z += 22.0
    elif name == "power_harness_rail_left":
        obj.location.y -= 14.0
        obj.location.z += 9.0
    elif name == "power_harness_rail_right":
        obj.location.y += 14.0
        obj.location.z += 9.0
    elif name == "body_shell":
        obj.location.z += shell_lift
    elif name.startswith("side_fairing_left"):
        obj.location.y -= 28.0
        obj.location.z += shell_lift
    elif name.startswith("side_fairing_right"):
        obj.location.y += 28.0
        obj.location.z += shell_lift
    elif name == "rear_service_panel":
        obj.location.x += 38.0
        obj.location.z += shell_lift
    elif name.startswith("rear_service_cartridge_"):
        obj.location.x += 58.0
        obj.location.z += shell_lift
    elif name == "front_sensor_fascia":
        obj.location.x -= 34.0
        obj.location.z += shell_lift
    elif name.startswith("front_status_led_carrier_"):
        obj.location.x -= 18.0
        obj.location.z += shell_lift
    elif name == "front_sensor_window" or name.startswith("front_status_"):
        obj.location.x -= 50.0
        obj.location.z += shell_lift
    elif name.startswith("tof_pod_front"):
        obj.location.x -= 12.0
        obj.location.z += shell_lift
    elif name.startswith("tof_pod_side_left"):
        obj.location.y -= 18.0
        obj.location.z += shell_lift
    elif name.startswith("tof_pod_side_right"):
        obj.location.y += 18.0
        obj.location.z += shell_lift
    elif name.startswith(("mic_array_cradle", "speaker_mount", "top_cable_strain_relief")):
        obj.location.z += shell_lift + 4.0
    elif name == "estop_backing_plate":
        obj.location.z += shell_lift + 12.0
    elif name in {"lid_reveal", "top_lid"}:
        obj.location.z += 92.0
    elif name in {"top_vent_inlay", "estop_well", "preview_estop", "preview_estop_cap", "preview_estop_yellow_legend"}:
        obj.location.z += 106.0
    elif name == "pan_servo_mount":
        obj.location.z += 88.0
    elif name == "neck_collar":
        obj.location.z += 108.0
    elif name == "neck":
        obj.location.z += 122.0
    elif name == "head_tilt_yoke":
        obj.location.z += 132.0
    elif name == "head_tilt_passive_cartridge":
        obj.location.y -= 20.0
        obj.location.z += head_lift
    elif name == "head_tilt_drive_adapter":
        obj.location.y += 20.0
        obj.location.z += head_lift
    elif name == "head_rear_cover":
        obj.location.x += 42.0
        obj.location.z += head_lift
    elif name == "camera_carrier":
        obj.location.x -= 18.0
        obj.location.z += head_lift
    elif name.startswith("head_eye_led_carrier"):
        obj.location.x -= 22.0
        obj.location.z += head_lift
    elif name.startswith(
        ("head_faceplate", "head_lens", "preview_camera_lens", "eye_", "eyebrow")
    ):
        obj.location.x -= 46.0
        obj.location.z += head_lift
    elif name == "head_shell":
        obj.location.z += head_lift
    elif name.startswith("wheel_left"):
        obj.location.y -= 26.0
    elif name.startswith("hub_ring_left"):
        obj.location.y -= 40.0
    elif name.startswith("hub_left"):
        obj.location.y -= 52.0
    elif name.startswith("wheel_right"):
        obj.location.y += 26.0
    elif name.startswith("hub_ring_right"):
        obj.location.y += 40.0
    elif name.startswith("hub_right"):
        obj.location.y += 52.0
    elif name.startswith(("front_idler_pod_left", "motor_pod_left")):
        obj.location.y -= 14.0
        obj.location.z -= 3.0
    elif name.startswith(("front_idler_pod_right", "motor_pod_right")):
        obj.location.y += 14.0
        obj.location.z -= 3.0
    elif name.startswith("motor_pod_cover_left"):
        obj.location.y += 18.0
    elif name.startswith("motor_pod_cover_right"):
        obj.location.y -= 18.0
    elif name.startswith("front_idler_retainer_left_inner"):
        obj.location.y += 14.0
    elif name.startswith("front_idler_retainer_left_outer"):
        obj.location.y -= 22.0
    elif name.startswith("front_idler_retainer_right_inner"):
        obj.location.y -= 14.0
    elif name.startswith("front_idler_retainer_right_outer"):
        obj.location.y += 22.0


def render(objects, exploded: bool):
    if exploded:
        for obj in objects:
            explode_object(obj)

    floor = bpy.data.objects.get("review_floor")
    if floor:
        floor.hide_render = False
        floor.location.z = load_ground_z() - (70.0 if exploded else 0.0)

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE" if "BLENDER_EEVEE" in {item.identifier for item in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items} else "BLENDER_EEVEE_NEXT"
    scene.render.resolution_x = 1200
    scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    # Screen-space ambient occlusion restores the small contact shadows that
    # make the shell fillets, wheel arches, lid reveal, and modular seams legible
    # in a high-key environment. The physical CAD remains untouched.
    if hasattr(scene, "eevee"):
        scene.eevee.taa_render_samples = 128
        scene.eevee.use_fast_gi = True
        scene.eevee.fast_gi_method = "AMBIENT_OCCLUSION_ONLY"
        scene.eevee.fast_gi_distance = 32.0
        scene.eevee.fast_gi_quality = 1.0
        scene.eevee.fast_gi_ray_count = 4
        scene.eevee.fast_gi_step_count = 16
        scene.eevee.shadow_ray_count = 4
        scene.eevee.shadow_step_count = 8
    scene.render.filepath = str(
        IMAGE_DIR / ("codex_robot_body_v1_exploded.png" if exploded else "codex_robot_body_v1_assembled.png")
    )
    # The reference sits in a bright cream room. Keep the world warm and high
    # key; object/background separation comes from directional highlights and
    # contact shadows rather than an unrelated blue studio backdrop.
    scene.world.color = (0.34, 0.25, 0.17)
    scene.world.use_nodes = True
    scene.world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.34, 0.25, 0.17, 1.0)
    scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.58
    # AgX gives the bright cream shell and lime LEDs a photographic highlight
    # shoulder. Extra exposure lifts the mids to the concept's sunny level.
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "AgX - Very High Contrast"
    scene.view_settings.exposure = 1.85
    scene.view_settings.use_white_balance = True
    scene.view_settings.white_balance_temperature = 6200
    scene.render.image_settings.color_mode = "RGBA"
    bpy.ops.render.render(write_still=True)


def render_fit(body_objects, fit_objects, mats):
    for obj in body_objects:
        obj.location = (0, 0, 0)
        obj.hide_render = not obj.name.startswith(
            (
                "base_tray",
                "battery_cradle",
                "mic_array_cradle",
                "speaker_mount",
                "tof_pod",
                "motor_pod",
                "front_idler_pod",
                "front_idler_retainer",
                "motor_controller_mount",
                "safety_mcu_mount",
                "top_cable_strain_relief",
                "power_service_deck",
                "power_harness_rail",
                "camera_carrier",
                "rear_service_panel",
                "head_eye_led_carrier",
                "front_status_led_carrier",
                "pan_servo_mount",
                "head_tilt_",
                "neck",
                "neck_collar",
                "estop_backing_plate",
            )
        )
    for obj in fit_objects:
        obj.hide_render = False

    floor = bpy.data.objects.get("review_floor")
    if floor:
        floor.hide_render = False
        floor.location.z = load_ground_z()

    old_camera = bpy.context.scene.camera
    if old_camera:
        bpy.data.objects.remove(old_camera, do_unlink=True)
    bpy.ops.object.camera_add(location=(-500, -440, 310))
    camera = bpy.context.object
    camera.data.lens = 58
    look_at(camera, (0, 0, 105))
    bpy.context.scene.camera = camera

    scene = bpy.context.scene
    scene.view_settings.exposure = 1.0
    scene.render.filepath = str(IMAGE_DIR / "codex_robot_body_v1_electronics_fit.png")
    bpy.ops.render.render(write_still=True)


def render_safety_mcu_interface(body_objects, fit_objects):
    """Drawing-backed Pico 2 shelf, standoffs, and service corridors."""
    visible_body = {"motor_controller_mount", "safety_mcu_mount"}
    for obj in body_objects:
        obj.location = (0, 0, 0)
        obj.hide_render = obj.name not in visible_body

    for obj in fit_objects:
        obj.location = (0, 0, 0)
        obj.hide_render = not (
            obj.name in {
                "fit_safety_mcu_board",
                "fit_safety_mcu_header_left",
                "fit_safety_mcu_header_right",
                "fit_safety_mcu_usb_service",
                "fit_safety_mcu_swd_service",
            }
            or obj.name.startswith(
                ("fit_safety_shelf_standoff_", "fit_safety_mcu_standoff_")
            )
        )

    floor = bpy.data.objects.get("review_floor")
    if floor:
        floor.hide_render = True

    old_camera = bpy.context.scene.camera
    if old_camera:
        bpy.data.objects.remove(old_camera, do_unlink=True)
    bpy.ops.object.camera_add(location=(-245, -165, 185))
    camera = bpy.context.object
    camera.data.lens = 68
    camera.data.sensor_width = 36
    camera.data.clip_end = 3000
    look_at(camera, (-65, 35, 76))
    bpy.context.scene.camera = camera

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE" if "BLENDER_EEVEE" in {item.identifier for item in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items} else "BLENDER_EEVEE_NEXT"
    scene.world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.30, 0.23, 0.16, 1.0)
    scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.62
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "AgX - Very High Contrast"
    scene.view_settings.exposure = 1.65
    scene.view_settings.use_white_balance = True
    scene.view_settings.white_balance_temperature = 6200
    scene.render.filepath = str(IMAGE_DIR / "codex_robot_body_v1_safety_mcu.png")
    bpy.ops.render.render(write_still=True)


def render_motor_controller_interface(body_objects, fit_objects):
    """Drawing-backed MDDS10 plate, terminal fan-out, cooling, and stack."""
    visible_body = {"base_tray", "motor_controller_mount", "safety_mcu_mount"}
    for obj in body_objects:
        obj.location = (0, 0, 0)
        obj.hide_render = obj.name not in visible_body

    for obj in fit_objects:
        obj.location = (0, 0, 0)
        obj.hide_render = not (
            obj.name in {
                "fit_motor_controller_board",
                "fit_motor_controller_terminal_service",
                "fit_motor_controller_airflow",
            }
            or obj.name.startswith(
                (
                    "fit_motor_controller_standoff_",
                    "fit_motor_controller_plate_standoff_",
                    "fit_safety_shelf_standoff_",
                )
            )
        )

    floor = bpy.data.objects.get("review_floor")
    if floor:
        floor.hide_render = True

    old_camera = bpy.context.scene.camera
    if old_camera:
        bpy.data.objects.remove(old_camera, do_unlink=True)
    bpy.ops.object.camera_add(location=(-250, -175, 175))
    camera = bpy.context.object
    camera.data.lens = 66
    camera.data.sensor_width = 36
    camera.data.clip_end = 3000
    look_at(camera, (-65, 33.5, 70))
    bpy.context.scene.camera = camera

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE" if "BLENDER_EEVEE" in {item.identifier for item in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items} else "BLENDER_EEVEE_NEXT"
    scene.world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.30, 0.23, 0.16, 1.0)
    scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.62
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "AgX - Very High Contrast"
    scene.view_settings.exposure = 1.65
    scene.view_settings.use_white_balance = True
    scene.view_settings.white_balance_temperature = 6200
    scene.render.filepath = str(IMAGE_DIR / "codex_robot_body_v1_motor_controller.png")
    bpy.ops.render.render(write_still=True)


def render_top_detail(body_objects, fit_objects):
    """Concept-facing close review of the lid, vent, E-stop, and neck stack."""
    top_names = {
        "body_shell",
        "lid_reveal",
        "top_lid",
        "top_vent_inlay",
        "estop_well",
        "preview_estop",
        "preview_estop_cap",
        "preview_estop_yellow_legend",
        "neck_collar",
        "neck",
    }
    for obj in body_objects:
        obj.location = (0, 0, 0)
        obj.hide_render = obj.name not in top_names
    for obj in fit_objects:
        obj.hide_render = True

    floor = bpy.data.objects.get("review_floor")
    if floor:
        floor.hide_render = True

    old_camera = bpy.context.scene.camera
    if old_camera:
        bpy.data.objects.remove(old_camera, do_unlink=True)
    bpy.ops.object.camera_add(location=(-390, -430, 370))
    camera = bpy.context.object
    camera.data.lens = 62
    camera.data.sensor_width = 36
    camera.data.clip_end = 3000
    look_at(camera, (20, 0, 174))
    bpy.context.scene.camera = camera

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE" if "BLENDER_EEVEE" in {item.identifier for item in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items} else "BLENDER_EEVEE_NEXT"
    scene.world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.34, 0.25, 0.17, 1.0)
    scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.58
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "AgX - Very High Contrast"
    scene.view_settings.exposure = 1.85
    scene.view_settings.use_white_balance = True
    scene.view_settings.white_balance_temperature = 6200
    scene.render.filepath = str(IMAGE_DIR / "codex_robot_body_v1_top_detail.png")
    bpy.ops.render.render(write_still=True)


def render_wheel_detail(body_objects, fit_objects):
    """Close review of tread, hub inserts, arch clearance, and bumper height."""
    for obj in body_objects:
        obj.location = (0, 0, 0)
        obj.hide_render = not (
            obj.name in {"body_shell", "side_fairing_left", "bumper_carrier"}
            or obj.name.startswith(("wheel_left_", "hub_ring_left_", "hub_left_"))
        )
    for obj in fit_objects:
        obj.hide_render = True

    floor = bpy.data.objects.get("review_floor")
    if floor:
        floor.hide_render = False
        floor.location.z = load_ground_z()

    old_camera = bpy.context.scene.camera
    if old_camera:
        bpy.data.objects.remove(old_camera, do_unlink=True)
    bpy.ops.object.camera_add(location=(-315, -430, 170))
    camera = bpy.context.object
    camera.data.lens = 65
    camera.data.sensor_width = 36
    camera.data.clip_end = 3000
    look_at(camera, (-5, -112, 72))
    bpy.context.scene.camera = camera

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE" if "BLENDER_EEVEE" in {item.identifier for item in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items} else "BLENDER_EEVEE_NEXT"
    scene.world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.34, 0.25, 0.17, 1.0)
    scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.58
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "AgX - Very High Contrast"
    scene.view_settings.exposure = 1.85
    scene.view_settings.use_white_balance = True
    scene.view_settings.white_balance_temperature = 6200
    scene.render.filepath = str(IMAGE_DIR / "codex_robot_body_v1_wheel_detail.png")
    bpy.ops.render.render(write_still=True)


def render_front_idler_interface(body_objects, fit_objects):
    """Exploded retail shoulder-bolt/608/#2693 front-idler stack."""
    visible_body = {
        "front_idler_pod_left",
        "front_idler_retainer_left_inner",
        "front_idler_retainer_left_outer",
        "wheel_left_1",
        "hub_left_1",
        "hub_ring_left_1",
    }
    body_offsets = {
        "front_idler_retainer_left_inner": (0.0, 30.0, 0.0),
        "front_idler_retainer_left_outer": (0.0, -30.0, 0.0),
        "hub_left_1": (0.0, -72.0, 0.0),
        "wheel_left_1": (0.0, -100.0, 0.0),
        "hub_ring_left_1": (0.0, -126.0, 0.0),
    }
    for obj in body_objects:
        obj.location = body_offsets.get(obj.name, (0.0, 0.0, 0.0))
        obj.hide_render = obj.name not in visible_body

    fit_offsets = {
        "fit_front_idler_left_locknut": (0.0, -84.0, 0.0),
        "fit_front_idler_left_thread_washer": (0.0, -75.0, 0.0),
        "fit_front_idler_left_tuning_shim": (0.0, -69.0, 0.0),
        "fit_front_idler_left_tuning_spacer": (0.0, -63.0, 0.0),
        "fit_front_idler_left_bearing_inner": (0.0, 25.0, 0.0),
        "fit_front_idler_left_inner_spacer": (0.0, 10.0, 0.0),
        "fit_front_idler_left_bearing_outer": (0.0, -10.0, 0.0),
        "fit_front_idler_left_outer_spacer": (0.0, -28.0, 0.0),
        "fit_front_idler_left_hub": (0.0, -50.0, 0.0),
        # Lift the one-piece retail bolt and its head/thread so the full span
        # remains visible instead of hiding inside every bore.
        "fit_front_idler_left_shoulder_bolt": (42.0, 0.0, 30.0),
        "fit_front_idler_left_shoulder_head": (42.0, 0.0, 30.0),
        "fit_front_idler_left_thread": (42.0, 0.0, 30.0),
    }
    for obj in fit_objects:
        obj.location = fit_offsets.get(obj.name, (0.0, 0.0, 0.0))
        obj.hide_render = obj.name not in fit_offsets

    floor = bpy.data.objects.get("review_floor")
    if floor:
        floor.hide_render = False
        floor.location.z = load_ground_z()

    old_camera = bpy.context.scene.camera
    if old_camera:
        bpy.data.objects.remove(old_camera, do_unlink=True)
    bpy.ops.object.camera_add(location=(-390, -500, 250))
    camera = bpy.context.object
    camera.data.lens = 60
    camera.data.sensor_width = 36
    camera.data.clip_end = 3000
    look_at(camera, (-90, -112, 70))
    bpy.context.scene.camera = camera

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE" if "BLENDER_EEVEE" in {item.identifier for item in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items} else "BLENDER_EEVEE_NEXT"
    scene.world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.34, 0.25, 0.17, 1.0)
    scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.58
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "AgX - Very High Contrast"
    scene.view_settings.exposure = 1.85
    scene.view_settings.use_white_balance = True
    scene.view_settings.white_balance_temperature = 6200
    scene.render.filepath = str(IMAGE_DIR / "codex_robot_body_v1_front_idler.png")
    bpy.ops.render.render(write_still=True)


def render_drivetrain_interface(body_objects, fit_objects):
    """Exploded rear-left review of the drawing-backed drive stack."""
    visible_body = {
        "base_tray",
        "motor_pod_left",
        "motor_pod_cover_left",
        "wheel_left_2",
        "hub_ring_left_2",
        "hub_left_2",
        "power_harness_rail_left",
    }
    for obj in body_objects:
        obj.location = (0, 0, 0)
        obj.hide_render = obj.name not in visible_body

    # Move only real assembly groups along their service directions. The same
    # generated parts return to the assembled position; no review-only body
    # geometry is invented for this image.
    for obj in body_objects:
        if obj.name == "wheel_left_2":
            obj.location.y -= 48.0
        elif obj.name == "hub_ring_left_2":
            obj.location.y -= 76.0
        elif obj.name == "hub_left_2":
            obj.location.y -= 26.0
        elif obj.name == "motor_pod_cover_left":
            obj.location.y += 26.0

    visible_fits = {
        "fit_drive_motor_left",
        "fit_drive_motor_bracket_left",
        "fit_drive_motor_hub_left",
        "fit_drive_motor_cable_left",
        "fit_drive_motor_bracket_spacer_left_1",
        "fit_drive_motor_bracket_spacer_left_2",
        "fit_drive_motor_bracket_spacer_left_3",
    }
    for obj in fit_objects:
        obj.location = (0, 0, 0)
        obj.hide_render = obj.name not in visible_fits

    floor = bpy.data.objects.get("review_floor")
    if floor:
        floor.hide_render = False
        floor.location.z = load_ground_z()

    old_camera = bpy.context.scene.camera
    if old_camera:
        bpy.data.objects.remove(old_camera, do_unlink=True)
    bpy.ops.object.camera_add(location=(315, -430, 225))
    camera = bpy.context.object
    camera.data.lens = 64
    camera.data.sensor_width = 36
    camera.data.clip_end = 3000
    look_at(camera, (78, -104, 67))
    bpy.context.scene.camera = camera

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE" if "BLENDER_EEVEE" in {item.identifier for item in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items} else "BLENDER_EEVEE_NEXT"
    scene.world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.34, 0.25, 0.17, 1.0)
    scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.58
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "AgX - Very High Contrast"
    scene.view_settings.exposure = 1.85
    scene.view_settings.use_white_balance = True
    scene.view_settings.white_balance_temperature = 6200
    scene.render.filepath = str(IMAGE_DIR / "codex_robot_body_v1_drivetrain.png")
    bpy.ops.render.render(write_still=True)


def render_head_mechanism(body_objects, fit_objects):
    """Exploded review of the bearing-supported pan and retained tilt axes."""
    visible_body = {
        "neck",
        "neck_collar",
        "pan_bearing_retainer",
        "pan_servo_mount",
        "head_tilt_yoke",
        "head_tilt_drive_adapter",
        "head_tilt_passive_cartridge",
    }
    for obj in body_objects:
        obj.location = (0, 0, 0)
        obj.hide_render = obj.name not in visible_body
        if obj.name == "head_tilt_drive_adapter":
            obj.location.y += 34.0
            obj.location.z += 10.0
        elif obj.name == "head_tilt_passive_cartridge":
            obj.location.y -= 34.0
            obj.location.z += 10.0
        elif obj.name == "neck_collar":
            obj.location.z -= 10.0
        elif obj.name == "pan_bearing_retainer":
            obj.location.z -= 24.0
        elif obj.name == "pan_servo_mount":
            obj.location.z -= 48.0

    visible_fits = {
        "fit_pan_servo",
        "fit_pan_servo_horn",
        "fit_pan_bearing",
        "fit_tilt_servo",
        "fit_tilt_servo_horn",
        "fit_tilt_passive_bushing",
        "fit_tilt_shoulder_bolt",
    }
    for obj in fit_objects:
        obj.location = (0, 0, 0)
        obj.hide_render = obj.name not in visible_fits
        if obj.name == "fit_tilt_servo_horn":
            obj.location.y += 20.0
        elif obj.name == "fit_tilt_passive_bushing":
            obj.location.y -= 20.0
        elif obj.name == "fit_tilt_shoulder_bolt":
            obj.location.y -= 34.0
        elif obj.name == "fit_pan_bearing":
            obj.location.z -= 16.0
        elif obj.name == "fit_pan_servo_horn":
            obj.location.z -= 34.0
        elif obj.name == "fit_pan_servo":
            obj.location.z -= 48.0

    floor = bpy.data.objects.get("review_floor")
    if floor:
        floor.hide_render = True

    old_camera = bpy.context.scene.camera
    if old_camera:
        bpy.data.objects.remove(old_camera, do_unlink=True)
    bpy.ops.object.camera_add(location=(-300, -450, 315))
    camera = bpy.context.object
    camera.data.lens = 60
    camera.data.sensor_width = 36
    camera.data.clip_end = 3000
    look_at(camera, (-10, 0, 190))
    bpy.context.scene.camera = camera

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE" if "BLENDER_EEVEE" in {item.identifier for item in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items} else "BLENDER_EEVEE_NEXT"
    scene.world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.34, 0.25, 0.17, 1.0)
    scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.58
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "AgX - Very High Contrast"
    scene.view_settings.exposure = 1.85
    scene.view_settings.use_white_balance = True
    scene.view_settings.white_balance_temperature = 6200
    scene.render.filepath = str(IMAGE_DIR / "codex_robot_body_v1_head_mechanism.png")
    bpy.ops.render.render(write_still=True)


def render_head_detail(body_objects, fit_objects):
    """Close review of the printable concept-facing head inventory."""
    head_prefixes = (
        "head_shell",
        "head_faceplate",
        "head_lens_",
        "preview_camera_lens_",
        "head_eye_led_carrier_",
        "eye_socket_",
        "eye_glow_",
        "eyebrow_",
        "neck",
    )
    for obj in body_objects:
        obj.location = (0, 0, 0)
        obj.hide_render = not obj.name.startswith(head_prefixes)
    for obj in fit_objects:
        obj.hide_render = True

    floor = bpy.data.objects.get("review_floor")
    if floor:
        floor.hide_render = True

    old_camera = bpy.context.scene.camera
    if old_camera:
        bpy.data.objects.remove(old_camera, do_unlink=True)
    bpy.ops.object.camera_add(location=(-235, -255, 320))
    camera = bpy.context.object
    camera.data.lens = 62
    look_at(camera, (-26, 0, 245))
    bpy.context.scene.camera = camera

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE" if "BLENDER_EEVEE" in {item.identifier for item in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items} else "BLENDER_EEVEE_NEXT"
    scene.world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.12, 0.09, 0.07, 1.0)
    scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.55
    scene.view_settings.exposure = 1.35
    scene.render.filepath = str(IMAGE_DIR / "codex_robot_body_v1_head_detail.png")
    bpy.ops.render.render(write_still=True)


def render_led_interface(body_objects, fit_objects):
    """Exploded comparison of the head-eye and front-status LED modules."""
    visible_body = {
        "head_eye_led_carrier_1",
        "eye_socket_1",
        "eye_glow_1",
        "front_status_led_carrier_1",
        "front_status_left",
    }
    for obj in body_objects:
        obj.location = (0, 0, 0)
        obj.hide_render = obj.name not in visible_body
        if obj.name.startswith(("head_eye_", "eye_")):
            obj.location.x -= 40.0
            obj.location.y += 82.0
            obj.location.z -= 60.0
        elif obj.name.startswith("front_status"):
            obj.location.x += 40.0
            obj.location.y += 10.0
            obj.location.z += 64.0
        if obj.name in {"eye_socket_1", "eye_glow_1", "front_status_left"}:
            obj.location.x -= 12.0

    visible_fit_prefixes = (
        "fit_head_eye_led_left",
        "fit_front_status_led_left",
    )
    for obj in fit_objects:
        obj.location = (0, 0, 0)
        obj.hide_render = not obj.name.startswith(visible_fit_prefixes)
        if obj.hide_render:
            continue
        if obj.name.startswith("fit_head_eye_led_left"):
            obj.location.x -= 40.0
            obj.location.y += 82.0
            obj.location.z -= 60.0
        else:
            obj.location.x += 40.0
            obj.location.y += 10.0
            obj.location.z += 64.0
        if obj.name.endswith("_jst_service"):
            obj.location.x += 10.0
        elif "_spacer_" in obj.name:
            obj.location.x -= 4.0
        else:
            obj.location.x -= 8.0

    floor = bpy.data.objects.get("review_floor")
    if floor:
        floor.hide_render = True

    old_camera = bpy.context.scene.camera
    if old_camera:
        bpy.data.objects.remove(old_camera, do_unlink=True)
    bpy.ops.object.camera_add(location=(-335, -365, 285))
    camera = bpy.context.object
    camera.data.lens = 62
    look_at(camera, (-90, 0, 174))
    bpy.context.scene.camera = camera

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE" if "BLENDER_EEVEE" in {item.identifier for item in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items} else "BLENDER_EEVEE_NEXT"
    scene.world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.34, 0.25, 0.17, 1.0)
    scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.58
    scene.view_settings.exposure = 1.65
    scene.render.filepath = str(IMAGE_DIR / "codex_robot_body_v1_led_interface.png")
    bpy.ops.render.render(write_still=True)


def render_carry_interface(body_objects, fit_objects, split_objects):
    """Show the clean split tray and seam plate after handle deletion."""
    for obj in body_objects:
        obj.hide_render = True
    for obj in split_objects:
        obj.location = (0, 0, 0)
        obj.hide_render = obj.name not in {
            "base_tray_half_front",
            "base_tray_half_rear",
            "base_seam_plate",
        }
        if obj.name == "base_tray_half_front":
            obj.location.x -= 5.0
        elif obj.name == "base_tray_half_rear":
            obj.location.x += 5.0
        elif obj.name == "base_seam_plate":
            obj.location.x += 175.0
            obj.location.z += 4.0

    for obj in fit_objects:
        obj.location = (0, 0, 0)
        obj.hide_render = True

    floor = bpy.data.objects.get("review_floor")
    if floor:
        floor.hide_render = True

    old_camera = bpy.context.scene.camera
    if old_camera:
        bpy.data.objects.remove(old_camera, do_unlink=True)
    bpy.ops.object.camera_add(location=(-380, -470, 390))
    camera = bpy.context.object
    camera.data.lens = 58
    look_at(camera, (0, 0, 46))
    bpy.context.scene.camera = camera

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.display.shading.light = "STUDIO"
    scene.display.shading.color_type = "MATERIAL"
    scene.display.shading.show_shadows = True
    scene.display.shading.show_cavity = True
    scene.display.shading.cavity_type = "WORLD"
    scene.display.shading.background_type = "VIEWPORT"
    scene.display.shading.background_color = (0.035, 0.045, 0.06)
    scene.view_settings.exposure = 0.0
    scene.render.filepath = str(IMAGE_DIR / "codex_robot_body_v1_carry_interface.png")
    bpy.ops.render.render(write_still=True)


def render_harness_interface(body_objects, fit_objects, split_objects):
    """Explode the removable deck's separated signal and power raceways."""
    for obj in split_objects:
        obj.hide_render = True
    for obj in body_objects:
        obj.location = (0, 0, 0)
        obj.hide_render = obj.name not in {
            "power_service_deck",
            "power_harness_rail_left",
            "power_harness_rail_right",
        }
        if obj.name == "power_service_deck":
            obj.location.z += 22.0
        elif obj.name.endswith("_left"):
            obj.location.y -= 10.0
        elif obj.name.endswith("_right"):
            obj.location.y += 10.0

    for obj in fit_objects:
        obj.location = (0, 0, 0)
        obj.hide_render = not obj.name.startswith("fit_power_harness_")
        if obj.hide_render:
            continue
        obj.location.y += -10.0 if obj.name.endswith("_left") else 10.0
        obj.location.z -= 10.0

    floor = bpy.data.objects.get("review_floor")
    if floor:
        floor.hide_render = True

    old_camera = bpy.context.scene.camera
    if old_camera:
        bpy.data.objects.remove(old_camera, do_unlink=True)
    bpy.ops.object.camera_add(location=(-270, -330, 235))
    camera = bpy.context.object
    camera.data.lens = 60
    look_at(camera, (65, 0, 100))
    bpy.context.scene.camera = camera

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.display.shading.light = "STUDIO"
    scene.display.shading.color_type = "MATERIAL"
    scene.display.shading.show_shadows = True
    scene.display.shading.show_cavity = True
    scene.display.shading.cavity_type = "WORLD"
    scene.display.shading.background_type = "VIEWPORT"
    scene.display.shading.background_color = (0.035, 0.045, 0.06)
    scene.view_settings.exposure = 0.0
    scene.render.filepath = str(IMAGE_DIR / "codex_robot_body_v1_harness_routing.png")
    bpy.ops.render.render(write_still=True)


def render_power_deck_interface(body_objects, fit_objects, split_objects):
    """Close review of the retail relay, covered fuse block, and regulators."""
    for obj in split_objects:
        obj.hide_render = True
    for obj in body_objects:
        obj.location = (0, 0, 0)
        obj.hide_render = obj.name != "power_service_deck"

    visible_fit_prefixes = (
        "fit_pi_buck_",
        "fit_pi_regulator_standoff_",
        "fit_servo_regulator",
        "fit_motor_cutoff",
        "fit_power_distribution",
    )
    for obj in fit_objects:
        obj.location = (0, 0, 0)
        obj.hide_render = not obj.name.startswith(visible_fit_prefixes)

    floor = bpy.data.objects.get("review_floor")
    if floor:
        floor.hide_render = True

    old_camera = bpy.context.scene.camera
    if old_camera:
        bpy.data.objects.remove(old_camera, do_unlink=True)
    bpy.ops.object.camera_add(location=(-210, -285, 245))
    camera = bpy.context.object
    camera.data.lens = 62
    camera.data.sensor_width = 36
    camera.data.clip_end = 3000
    look_at(camera, (60, 0, 116))
    bpy.context.scene.camera = camera

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.display.shading.light = "STUDIO"
    scene.display.shading.color_type = "MATERIAL"
    scene.display.shading.show_shadows = True
    scene.display.shading.show_cavity = True
    scene.display.shading.cavity_type = "WORLD"
    scene.display.shading.background_type = "VIEWPORT"
    scene.display.shading.background_color = (0.035, 0.045, 0.06)
    scene.view_settings.exposure = 0.0
    scene.render.filepath = str(IMAGE_DIR / "codex_robot_body_v1_power_deck.png")
    bpy.ops.render.render(write_still=True)


def render_battery_interface(body_objects, fit_objects, split_objects):
    """Review the selected flat battery, lead corridor, straps, and cradle."""
    for obj in split_objects:
        obj.hide_render = True
    for obj in body_objects:
        obj.location = (0, 0, 0)
        obj.hide_render = obj.name not in {"battery_cradle", "motor_controller_mount"}
    for obj in fit_objects:
        obj.location = (0, 0, 0)
        obj.hide_render = obj.name not in {
            "fit_battery",
            "fit_battery_lead_service",
            "fit_motor_controller",
        }

    floor = bpy.data.objects.get("review_floor")
    if floor:
        floor.hide_render = True

    old_camera = bpy.context.scene.camera
    if old_camera:
        bpy.data.objects.remove(old_camera, do_unlink=True)
    bpy.ops.object.camera_add(location=(-260, -300, 215))
    camera = bpy.context.object
    camera.data.lens = 60
    camera.data.sensor_width = 36
    camera.data.clip_end = 3000
    look_at(camera, (20, 0, 65))
    bpy.context.scene.camera = camera

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.display.shading.light = "STUDIO"
    scene.display.shading.color_type = "MATERIAL"
    scene.display.shading.show_shadows = True
    scene.display.shading.show_cavity = True
    scene.display.shading.cavity_type = "WORLD"
    scene.display.shading.background_type = "VIEWPORT"
    scene.display.shading.background_color = (0.035, 0.045, 0.06)
    scene.view_settings.exposure = 0.0
    scene.render.filepath = str(IMAGE_DIR / "codex_robot_body_v1_battery_interface.png")
    bpy.ops.render.render(write_still=True)


def render_bumper_interface(body_objects, fit_objects, split_objects):
    """Explode the fixed switch plates from the compliant TPU bumper and tray."""
    for obj in split_objects:
        obj.hide_render = True
    for obj in body_objects:
        obj.location = (0, 0, 0)
        obj.hide_render = not (
            obj.name in {"base_tray", "bumper_carrier"}
            or obj.name.startswith("bumper_switch_mount_")
        )
        if obj.name == "base_tray":
            obj.location.z += 16.0
        elif obj.name == "bumper_carrier":
            obj.location.z -= 10.0

    for obj in fit_objects:
        obj.location = (0, 0, 0)
        obj.hide_render = not obj.name.startswith("fit_bumper_switch_")

    floor = bpy.data.objects.get("review_floor")
    if floor:
        floor.hide_render = True

    old_camera = bpy.context.scene.camera
    if old_camera:
        bpy.data.objects.remove(old_camera, do_unlink=True)
    bpy.ops.object.camera_add(location=(-430, -390, 250))
    camera = bpy.context.object
    camera.data.lens = 58
    look_at(camera, (0, 0, 43))
    bpy.context.scene.camera = camera

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.display.shading.light = "STUDIO"
    scene.display.shading.color_type = "MATERIAL"
    scene.display.shading.show_shadows = True
    scene.display.shading.show_cavity = True
    scene.display.shading.cavity_type = "WORLD"
    scene.display.shading.background_type = "VIEWPORT"
    scene.display.shading.background_color = (0.035, 0.045, 0.06)
    scene.view_settings.exposure = 0.0
    scene.render.filepath = str(
        IMAGE_DIR / "codex_robot_body_v1_bumper_interface.png"
    )
    bpy.ops.render.render(write_still=True)


def render_audio_interface(body_objects, fit_objects):
    """Exploded speaker plates with exact-pattern dual MAX98357A mounts."""
    visible_body = {"speaker_mount_left", "speaker_mount_right"}
    for obj in body_objects:
        obj.location = (0, 0, 0)
        obj.hide_render = obj.name not in visible_body

    for obj in fit_objects:
        obj.location = (0, 0, 0)
        obj.hide_render = not obj.name.startswith(("fit_speaker_", "fit_audio_amp_"))
        if obj.hide_render:
            continue
        if obj.name.startswith("fit_speaker_"):
            obj.location.z += 24.0
        elif "_standoff_" in obj.name:
            obj.location.z -= 7.0
        else:
            obj.location.z -= 20.0

    floor = bpy.data.objects.get("review_floor")
    if floor:
        floor.hide_render = True

    old_camera = bpy.context.scene.camera
    if old_camera:
        bpy.data.objects.remove(old_camera, do_unlink=True)
    bpy.ops.object.camera_add(location=(-150, -285, 245))
    camera = bpy.context.object
    camera.data.lens = 66
    camera.data.sensor_width = 36
    camera.data.clip_end = 3000
    look_at(camera, (80, 0, 142))
    bpy.context.scene.camera = camera

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE" if "BLENDER_EEVEE" in {item.identifier for item in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items} else "BLENDER_EEVEE_NEXT"
    scene.world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.34, 0.25, 0.17, 1.0)
    scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.58
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "AgX - Very High Contrast"
    scene.view_settings.exposure = 1.85
    scene.view_settings.use_white_balance = True
    scene.view_settings.white_balance_temperature = 6200
    scene.render.filepath = str(IMAGE_DIR / "codex_robot_body_v1_audio_interface.png")
    bpy.ops.render.render(write_still=True)


def render_rear_service_interface(body_objects, fit_objects):
    """Rear frame with sealed charge, blank access, and physical mute."""
    visible_body = {
        "body_shell",
        "rear_service_panel",
        "rear_service_cartridge_power_charge",
        "rear_service_cartridge_mute_status",
        "rear_service_cartridge_blank_access",
    }
    for obj in body_objects:
        obj.location = (0, 0, 0)
        obj.hide_render = obj.name not in visible_body
        if obj.name == "rear_service_panel":
            obj.location.x += 20.0
        elif obj.name.startswith("rear_service_cartridge_"):
            obj.location.x += 42.0

    for obj in fit_objects:
        obj.location = (0, 0, 0)
        obj.hide_render = not (
            obj.name == "fit_rear_service_bay"
            or obj.name.startswith("fit_charge_jack_")
            or obj.name.startswith("fit_mute_switch_")
        )
        if obj.name.startswith("fit_charge_jack_"):
            obj.location.x += 82.0
        elif obj.name.startswith("fit_mute_switch_"):
            obj.location.x += 90.0

    floor = bpy.data.objects.get("review_floor")
    if floor:
        floor.hide_render = True

    old_camera = bpy.context.scene.camera
    if old_camera:
        bpy.data.objects.remove(old_camera, do_unlink=True)
    bpy.ops.object.camera_add(location=(470, -310, 255))
    camera = bpy.context.object
    camera.data.lens = 68
    camera.data.sensor_width = 36
    camera.data.clip_end = 3000
    look_at(camera, (152, 0, 140))
    bpy.context.scene.camera = camera

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE" if "BLENDER_EEVEE" in {item.identifier for item in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items} else "BLENDER_EEVEE_NEXT"
    scene.world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.34, 0.25, 0.17, 1.0)
    scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.58
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "AgX - Very High Contrast"
    scene.view_settings.exposure = 1.85
    scene.view_settings.use_white_balance = True
    scene.view_settings.white_balance_temperature = 6200
    scene.render.filepath = str(IMAGE_DIR / "codex_robot_body_v1_rear_service.png")
    bpy.ops.render.render(write_still=True)


def render_split_joinery(body_objects, fit_objects, split_objects):
    """Render the printer-split shell layers with their real backing plates."""
    for obj in (*body_objects, *fit_objects):
        obj.hide_render = True

    for obj in split_objects:
        obj.location = (0, 0, 0)
        obj.hide_render = False
        name = obj.name
        x_shift = -8 if "_front" in name else (8 if "_rear" in name else 0)
        y_shift = -8 if "_left" in name else (8 if "_right" in name else 0)

        if name.startswith(("body_shell_q_", "body_seam_plate_")):
            obj.location.z += 38
        elif name.startswith("base_tray_half_"):
            obj.location.z += 20
        elif name == "base_seam_plate":
            obj.location.z += 12
        elif name.startswith(("top_lid_half_", "lid_reveal_half_")):
            obj.location.z += 82 if name.startswith("top_lid") else 74
        elif name.startswith("side_fairing_"):
            obj.location.z += 38
            obj.location.y += -18 if "_left_" in name else 18

        if name.startswith(("body_shell_q_", "bumper_q_", "top_lid_half_", "lid_reveal_half_", "side_fairing_")):
            spread = 2.0 if name.startswith("body_shell_q_") else (1.5 if name.startswith("bumper_q_") else 1.0)
            obj.location.x += x_shift * spread
            obj.location.y += y_shift * spread

    old_camera = bpy.context.scene.camera
    if old_camera:
        bpy.data.objects.remove(old_camera, do_unlink=True)
    bpy.ops.object.camera_add(location=(-620, -540, 430))
    camera = bpy.context.object
    camera.data.lens = 58
    look_at(camera, (0, 0, 135))
    bpy.context.scene.camera = camera

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE" if "BLENDER_EEVEE" in {item.identifier for item in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items} else "BLENDER_EEVEE_NEXT"
    scene.world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.12, 0.09, 0.07, 1.0)
    scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.35
    scene.view_settings.exposure = 1.0
    scene.render.filepath = str(IMAGE_DIR / "codex_robot_body_v1_split_joinery.png")
    bpy.ops.render.render(write_still=True)


def main():
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    clear_scene()
    mats = {
        "cream": material("cream", COLORS["cream"], roughness=0.32),
        "cream_highlight": material("cream_highlight", COLORS["cream_highlight"], roughness=0.30),
        "teal": material("teal", COLORS["teal"], roughness=0.26),
        "dark_teal": material("dark_teal", COLORS["dark_teal"], roughness=0.34),
        "charcoal": material("charcoal", COLORS["charcoal"], roughness=0.38),
        "dark_gray": material("dark_gray", COLORS["dark_gray"], roughness=0.52),
        "lime": material("lime", COLORS["lime"], roughness=0.25, emission=COLORS["lime"]),
        "blue": material("blue", COLORS["blue"], roughness=0.25),
        "red": material("red", COLORS["red"], roughness=0.24),
        "safety_yellow": material("safety_yellow", COLORS["safety_yellow"], roughness=0.30),
        "glass": material("glass", COLORS["glass"], metallic=0.4, roughness=0.15),
        "glass_highlight": material("glass_highlight", COLORS["glass_highlight"], metallic=0.5, roughness=0.15),
        "floor": material("floor", COLORS["floor"], roughness=0.75),
        "fit_pi": material("fit_pi", (0.08, 0.42, 0.22, 1.0), roughness=0.35),
        "fit_pi_board": material("fit_pi_board", (0.16, 0.72, 0.30, 1.0), roughness=0.3),
        "fit_motor": material("fit_motor", (0.88, 0.34, 0.08, 1.0), roughness=0.35),
        "fit_battery": material("fit_battery", (0.88, 0.58, 0.05, 1.0), roughness=0.4),
        "fit_safety": material("fit_safety", (0.78, 0.08, 0.04, 1.0), roughness=0.38),
        "fit_ai": material("fit_ai", (0.04, 0.55, 0.82, 1.0), roughness=0.35),
        "fit_servo": material("fit_servo", (0.50, 0.12, 0.65, 1.0), roughness=0.4),
        "fit_camera": material("fit_camera", (0.12, 0.36, 0.76, 1.0), roughness=0.28),
        "fit_audio": material("fit_audio", (0.72, 0.18, 0.74, 1.0), roughness=0.32),
        "fit_sensor": material("fit_sensor", (0.16, 0.72, 0.86, 1.0), roughness=0.28),
        "fit_power": material("fit_power", (0.95, 0.58, 0.04, 1.0), roughness=0.32),
        "fit_signal": material("fit_signal", (0.95, 0.18, 0.55, 1.0), roughness=0.3),
        "fit_service": material("fit_service", (0.32, 0.55, 0.72, 1.0), roughness=0.36),
        "fit_structure": material("fit_structure", (0.45, 0.48, 0.52, 1.0), metallic=0.35, roughness=0.3),
        "carry_metal": material("carry_metal", (0.95, 0.52, 0.08, 1.0), metallic=0.42, roughness=0.24),
        "carry_webbing": material("carry_webbing", (0.0, 0.62, 0.82, 1.0), roughness=0.58),
        "fit_led": material("fit_led", (0.72, 1.0, 0.12, 1.0), roughness=0.24, emission=(0.72, 1.0, 0.12, 1.0)),
        "joinery": material("joinery", (0.95, 0.28, 0.04, 1.0), roughness=0.32),
    }
    objects = load_parts(mats)
    fit_objects = load_fit_parts(mats)
    split_objects = load_split_joinery_parts(mats)
    for obj in fit_objects:
        obj.hide_render = True
    for obj in split_objects:
        obj.hide_render = True
    add_floor(mats, load_ground_z())
    add_camera(False)
    add_lights()
    render(objects, exploded=False)

    for obj in objects:
        obj.location = (0, 0, 0)
    # Recreate camera orientation for the second framing.
    bpy.data.objects.remove(bpy.context.scene.camera, do_unlink=True)
    add_camera(True)
    render(objects, exploded=True)
    render_top_detail(objects, fit_objects)
    render_wheel_detail(objects, fit_objects)
    render_front_idler_interface(objects, fit_objects)
    render_drivetrain_interface(objects, fit_objects)
    render_head_mechanism(objects, fit_objects)
    render_safety_mcu_interface(objects, fit_objects)
    render_motor_controller_interface(objects, fit_objects)
    render_power_deck_interface(objects, fit_objects, split_objects)
    render_battery_interface(objects, fit_objects, split_objects)
    render_fit(objects, fit_objects, mats)
    render_head_detail(objects, fit_objects)
    render_led_interface(objects, fit_objects)
    render_carry_interface(objects, fit_objects, split_objects)
    render_harness_interface(objects, fit_objects, split_objects)
    render_audio_interface(objects, fit_objects)
    render_rear_service_interface(objects, fit_objects)
    render_split_joinery(objects, fit_objects, split_objects)
    render_bumper_interface(objects, fit_objects, split_objects)


if __name__ == "__main__":
    main()
