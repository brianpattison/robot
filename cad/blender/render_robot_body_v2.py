"""Render the v2 printed-only body exports with the concept lighting rig.

Imports the assembly-coordinate STLs from cad/exports/v2 (run
`robot_body_v2.py` first), instances the mirrored/repeated parts, and
renders three review views into docs/images with the same warm high-key
daylight, AgX Very High Contrast look the v1 renders use.

Run from the repository root with Blender 5.x:
    /Applications/Blender.app/Contents/MacOS/Blender -b --python cad/blender/render_robot_body_v2.py
"""

from __future__ import annotations

import math
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
EXPORT_DIR = ROOT / "cad" / "exports" / "v2"
IMAGE_DIR = ROOT / "docs" / "images"
GROUND_Z = 23.0

COLORS = {
    "cream": (0.94, 0.87, 0.76, 1.0),
    "teal": (0.04, 0.43, 0.52, 1.0),
    "charcoal": (0.025, 0.03, 0.035, 1.0),
    "dark": (0.05, 0.055, 0.06, 1.0),
    "lime": (0.75, 1.0, 0.15, 1.0),
    "petg_natural": (0.82, 0.80, 0.74, 1.0),
    "floor": (0.34, 0.16, 0.055, 1.0),
}

MATERIAL_FOR = {
    "shell_v2": "cream", "tray_v2": "petg_natural", "lid_v2": "teal",
    "bumper_front_v2": "charcoal", "bumper_rear_v2": "charcoal",
    "fascia_v2": "dark", "rear_panel_v2": "dark",
    "head_shell_v2": "cream", "head_faceplate_v2": "dark",
    "neck_v2": "cream", "bayonet_collar_v2": "cream",
    "head_pan_plate_v2": "petg_natural",
    "tire_v2": "charcoal", "rear_wheel_v2": "petg_natural", "front_wheel_v2": "petg_natural",
    "eye_diffuser_bar_v2": "lime", "status_diffuser_bar_v2": "lime",
}
# Parts imported once but present twice, mirrored across Y=0.
MIRROR_Y = {"rear_wheel_v2", "front_wheel_v2", "motor_cap_v2", "speaker_clamp_v2",
            "tof_clamp_v2"}
# The tire design places at all four wheel stations.
TIRE_STATIONS = [(-74, 118, 66), (-74, -118, 66), (74, 118, 66), (74, -118, 66)]
# Small internal parts that only clutter exterior views.
HIDE_ALWAYS = {"printed_washer_v2", "tilt_bushing_v2", "battery_pad_frame_v2",
               "eye_diffuser_bar_v2", "status_diffuser_bar_v2"}  # unplaced part designs
CHASSIS_HIDE = {"shell_v2", "lid_v2", "head_shell_v2", "head_faceplate_v2", "neck_v2",
                "bayonet_collar_v2", "yoke_v2", "head_pan_plate_v2", "eye_diffuser_bar_v2",
                "mic_cradle_v2", "fascia_v2", "rear_panel_v2"}


def material(name, color, roughness=0.42):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Roughness"].default_value = roughness
    mat.diffuse_color = color
    return mat


def look_at(obj, target):
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def setup_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    mats = {k: material(k, v) for k, v in COLORS.items()}

    objects = {}
    for stl in sorted(EXPORT_DIR.glob("*_v2.stl")):
        name = stl.stem
        bpy.ops.wm.stl_import(filepath=str(stl))
        obj = bpy.context.selected_objects[0]
        obj.name = name
        key = MATERIAL_FOR.get(name, "petg_natural")
        obj.data.materials.append(mats[key])
        objects[name] = obj
        if name in HIDE_ALWAYS:
            obj.hide_render = True
        if name in MIRROR_Y:
            dup = obj.copy()
            dup.data = obj.data
            dup.name = name + "_m"
            dup.scale[1] = -1
            bpy.context.collection.objects.link(dup)
            objects[dup.name] = dup
    tire = objects.get("tire_v2")
    if tire:
        tire.location = Vector(TIRE_STATIONS[0])
        for i, station in enumerate(TIRE_STATIONS[1:], start=1):
            dup = tire.copy()
            dup.data = tire.data
            dup.name = f"tire_v2_{i}"
            dup.location = Vector(station)
            bpy.context.collection.objects.link(dup)
            objects[dup.name] = dup

    bpy.ops.mesh.primitive_plane_add(size=1600, location=(0, 0, GROUND_Z))
    floor = bpy.context.object
    floor.name = "review_floor"
    floor.data.materials.append(mats["floor"])

    # The v1 concept rig: warm window key, room/rim/front/overhead bounce,
    # low-energy sun, cream world.
    for name, loc, energy, color, size, target in (
        ("warm_window_key", (-390, -430, 590), 8200, (1.0, 0.80, 0.60), 430, (-25, 0, 130)),
        ("warm_room_fill", (350, -220, 370), 5400, (1.0, 0.93, 0.84), 430, (0, 0, 115)),
        ("warm_window_rim", (100, 340, 470), 4000, (1.0, 0.84, 0.68), 320, (0, 0, 160)),
        ("warm_camera_fill", (-440, -390, 260), 3500, (1.0, 0.91, 0.80), 310, (0, 0, 110)),
        ("warm_ceiling_bounce", (0, 20, 650), 2900, (1.0, 0.94, 0.85), 600, (0, 0, 100)),
    ):
        bpy.ops.object.light_add(type="AREA", location=loc)
        light = bpy.context.object
        light.name = name
        light.data.energy = energy
        light.data.color = color
        light.data.shape = "DISK"
        light.data.size = size
        look_at(light, target)
    bpy.ops.object.light_add(type="SUN", rotation=(math.radians(28), math.radians(-18), math.radians(-38)))
    sun = bpy.context.object
    sun.data.energy = 1.0
    sun.data.color = (1.0, 0.78, 0.56)
    sun.data.angle = math.radians(14)

    scene = bpy.context.scene
    engines = {item.identifier for item in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items}
    scene.render.engine = "BLENDER_EEVEE" if "BLENDER_EEVEE" in engines else "BLENDER_EEVEE_NEXT"
    scene.render.resolution_x = 1200
    scene.render.resolution_y = 900
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    if hasattr(scene, "eevee"):
        scene.eevee.taa_render_samples = 128
        scene.eevee.use_fast_gi = True
        scene.eevee.fast_gi_method = "AMBIENT_OCCLUSION_ONLY"
        scene.eevee.fast_gi_distance = 32.0
        scene.eevee.shadow_ray_count = 4
        scene.eevee.shadow_step_count = 8
    scene.world.use_nodes = True
    bg = scene.world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.34, 0.25, 0.17, 1.0)
    bg.inputs["Strength"].default_value = 0.58
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "AgX - Very High Contrast"
    scene.view_settings.exposure = 1.85
    if hasattr(scene.view_settings, "use_white_balance"):
        scene.view_settings.use_white_balance = True
        scene.view_settings.white_balance_temperature = 6200
    return objects


def render_view(objects, filename, cam_loc, cam_target, lens=55, hide=frozenset()):
    for obj in objects.values():
        base = obj.name.rstrip("_m0123456789")
        obj.hide_render = base in HIDE_ALWAYS or base in hide or obj.name in hide
    old = bpy.context.scene.camera
    if old:
        bpy.data.objects.remove(old, do_unlink=True)
    bpy.ops.object.camera_add(location=cam_loc)
    cam = bpy.context.object
    cam.data.lens = lens
    cam.data.sensor_width = 36
    cam.data.clip_end = 4000
    look_at(cam, cam_target)
    bpy.context.scene.camera = cam
    bpy.context.scene.render.filepath = str(IMAGE_DIR / filename)
    bpy.ops.render.render(write_still=True)
    print("rendered", filename)


def main():
    objects = setup_scene()
    render_view(objects, "codex_robot_body_v2_assembled.png",
                (-460, -400, 300), (0, 0, 140))
    render_view(objects, "codex_robot_body_v2_rear.png",
                (430, 330, 290), (0, 0, 125))
    render_view(objects, "codex_robot_body_v2_chassis.png",
                (-320, -300, 420), (0, 0, 85), hide=CHASSIS_HIDE)


if __name__ == "__main__":
    main()
