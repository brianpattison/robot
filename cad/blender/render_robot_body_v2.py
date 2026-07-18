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
import json
from pathlib import Path

import bpy
from mathutils import Matrix, Vector

ROOT = Path(__file__).resolve().parents[2]
EXPORT_DIR = ROOT / "cad" / "exports" / "v2"
IMAGE_DIR = ROOT / "docs" / "images"
GROUND_Z = 23.0
PRINT_MANIFEST = ROOT / "cad" / "exports" / "v2" / "print_ready" / "codex_robot_body_v2_print_manifest.json"

COLORS = {
    "body_primary": (0.94, 0.87, 0.76, 1.0),
    "top_accent": (0.04, 0.43, 0.52, 1.0),
    "dark_panel": (0.05, 0.055, 0.06, 1.0),
    "light_diffuser": (0.75, 1.0, 0.15, 1.0),
    # Instructional cool-grey tint: the actual slot remains white PETG, but a
    # slightly darker render value preserves edges against cream paper.
    "structure_light": (0.70, 0.75, 0.78, 1.0),
    "structure_wear": (0.025, 0.03, 0.035, 1.0),
    "safety_service": (0.65, 0.025, 0.035, 1.0),
    "flexible_dark": (0.025, 0.03, 0.035, 1.0),
    "floor": (0.24, 0.11, 0.04, 1.0),
}

if PRINT_MANIFEST.exists():
    _print_parts = json.loads(PRINT_MANIFEST.read_text(encoding="utf-8"))["parts"]
    MATERIAL_FOR = {name: data["effective_color_slot"] for name, data in _print_parts.items()}
else:
    MATERIAL_FOR = {}
# Parts imported once but present twice, mirrored across Y=0.
MIRROR_Y = {"rear_wheel_v2", "front_wheel_v2", "motor_cap_v2", "speaker_clamp_v2",
            "tof_clamp_v2"}
# The tire design places at all four wheel stations.
TIRE_STATIONS = [(-74, 118, 66), (-74, -118, 66), (74, 118, 66), (74, -118, 66)]
# Small internal parts that only clutter exterior views. The lime diffuser
# bars are exported in local coordinates but get placed into their fascia
# and faceplate seats by place_diffuser_bars(), so they render lit-up in
# the assembled views instead of hiding.
HIDE_ALWAYS = {"printed_washer_v2", "tilt_bushing_v2", "battery_pad_frame_v2"}
# The chassis view hides the shell, so also hide every clamp bar whose
# purchased part is not in this printed-only scene — otherwise the bars
# float in mid-air where the battery/Pico/speakers/ToF boards would be.
CHASSIS_HIDE = {"shell_v2", "lid_v2", "lid_skin_v2", "head_shell_v2", "head_faceplate_v2", "neck_v2",
                "bayonet_collar_v2", "yoke_v2", "head_pan_plate_v2", "eye_diffuser_bar_v2",
                "status_diffuser_bar_v2", "mic_cradle_v2", "fascia_v2", "rear_panel_v2",
                "speaker_clamp_v2", "tof_clamp_v2", "battery_clamp_v2", "pico_clamp_v2"}


def material(name, color, roughness=0.42, emission=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Roughness"].default_value = roughness
    if emission and "Emission Color" in bsdf.inputs:
        bsdf.inputs["Emission Color"].default_value = color
        bsdf.inputs["Emission Strength"].default_value = emission
    mat.diffuse_color = color
    return mat


def place_diffuser_bars(objects):
    """Seat the locally-exported lime bars behind their slot fields: the
    status bar behind the fascia (slots at Z 116), the eye bar behind the
    head faceplate (slots at Z 254). Local X spans world Y, local Y spans
    world Z, and the riser pads point world -X into the slots."""
    rot = Matrix.Rotation(math.radians(90), 4, "X") @ Matrix.Rotation(math.radians(-90), 4, "Y")
    for bar_name, host_name, z in (("status_diffuser_bar_v2", "fascia_v2", 116.0),
                                   ("eye_diffuser_bar_v2", "head_faceplate_v2", 254.0)):
        bar, host = objects.get(bar_name), objects.get(host_name)
        if not bar or not host:
            continue
        host_inner_x = max((host.matrix_world @ Vector(c)).x for c in host.bound_box)
        bar.matrix_world = Matrix.Translation(Vector((host_inner_x + 3.0, 0, z))) @ rot


def look_at(obj, target):
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def setup_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    mats = {k: material(k, v, emission=(1.4 if k == "light_diffuser" else 0.0))
            for k, v in COLORS.items()}

    objects = {}
    for stl in sorted(EXPORT_DIR.glob("*_v2.stl")):
        name = stl.stem
        bpy.ops.wm.stl_import(filepath=str(stl))
        obj = bpy.context.selected_objects[0]
        obj.name = name
        key = MATERIAL_FOR.get(name, "structure_light")
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

    place_diffuser_bars(objects)

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
        ("cool_instruction_rim", (-80, 420, 360), 3600, (0.68, 0.82, 1.0), 260, (0, 0, 145)),
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


def add_hero_estop():
    """The red emergency stop for the assembled/rear hero views: the body
    renders unfinished without its defining button. Review-only proxy."""
    made = []
    for name, radius, depth, z, color in (
        ("hero_estop_base", 30, 2, 183, (0.95, 0.75, 0.05, 1.0)),
        ("hero_estop_stem", 11, 14, 191, (0.08, 0.08, 0.08, 1.0)),
        ("hero_estop_cap", 20, 14, 203, (0.8, 0.06, 0.05, 1.0)),
    ):
        bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=(59, 56, z))
        obj = bpy.context.object
        obj.name = name
        mat = material(name, color)
        obj.data.materials.append(mat)
        made.append(obj)
    return made


def add_hero_camera_lens():
    """Visible Camera Module 3 lens stack for every assembled hero."""
    made = []
    for name, radius, depth, x, color in (
        ("hero_lens_bezel", 10.5, 3.0, -64.2, (0.025, 0.028, 0.032, 1.0)),
        ("hero_lens_glass", 6.4, 1.8, -66.6, (0.015, 0.035, 0.055, 1.0)),
    ):
        bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth,
                                             location=(x, 0, 254),
                                             rotation=(0, math.pi / 2, 0))
        obj = bpy.context.object
        obj.name = name
        obj.data.materials.append(material(name, color, roughness=0.22))
        made.append(obj)
    return made


def add_populated_electronics():
    """Review-only purchased-part proxies for the guide's cutaway map."""
    made = []
    specs = (
        ("map_battery", (110, 75, 27), (30, 0, 65.5), (0.18, 0.28, 0.55, 1)),
        ("map_mdds10", (67, 101, 14), (-67, 0, 71), (0.34, 0.18, 0.52, 1)),
        ("map_pi", (85, 56, 16), (-53, 0, 99), (0.12, 0.42, 0.18, 1)),
        ("map_pico", (52, 21, 6), (3, 63.5, 56), (0.12, 0.48, 0.25, 1)),
        ("map_reg_5v", (40.6, 20.3, 8), (102, -30, 98), (0.18, 0.46, 0.27, 1)),
        ("map_reg_6v", (25.4, 25.4, 9.5), (73, 7, 97), (0.18, 0.52, 0.31, 1)),
        ("map_relay", (26, 22, 25), (-23, -79, 63.5), (0.10, 0.11, 0.13, 1)),
        ("map_fuse", (43.8, 92.5, 32.5), (46, -21, 122), (0.07, 0.08, 0.10, 1)),
        ("map_speaker_L", (70, 17, 30), (-13, 95, 130), (0.12, 0.13, 0.15, 1)),
        ("map_speaker_R", (70, 17, 30), (-13, -95, 130), (0.12, 0.13, 0.15, 1)),
    )
    for name, dims, loc, color in specs:
        bpy.ops.mesh.primitive_cube_add(location=loc)
        obj = bpy.context.object
        obj.name = name
        obj.scale = tuple(d / 2 for d in dims)
        obj.data.materials.append(material(name, color))
        obj.hide_render = True
        made.append(obj)
    return made


def main():
    objects = setup_scene()
    hero_estop = add_hero_estop()
    hero_lens = add_hero_camera_lens()
    electronics = add_populated_electronics()
    render_view(objects, "codex_robot_body_v2_assembled.png",
                (-460, -400, 300), (0, 0, 140))
    render_view(objects, "codex_robot_body_v2_rear.png",
                (500, 400, 350), (0, 0, 152))
    for obj in hero_estop + hero_lens:
        obj.hide_render = True
    render_view(objects, "codex_robot_body_v2_chassis.png",
                (-320, -300, 420), (0, 0, 85), hide=CHASSIS_HIDE)
    for obj in electronics:
        obj.hide_render = False
    populated_hide = {"shell_v2", "lid_v2", "lid_skin_v2", "head_shell_v2",
                      "head_faceplate_v2", "fascia_v2", "rear_panel_v2"}
    render_view(objects, "codex_robot_body_v2_populated_cutaway.png",
                (-300, -315, 455), (0, 0, 92), lens=58, hide=populated_hide)


if __name__ == "__main__":
    main()
