"""Render the LEGO-style step sequence and part thumbnails for the v2 guide.

Builds the full v2 scene (printed parts from cad/exports/v2 plus simple
color-coded proxies for every purchased part, sized from the registered
inventory), then renders:
- one thumbnail per printed design and per purchased proxy (for the
  parts-needed strips and the what's-in-the-box pages),
- one render per assembly step, with everything assembled so far shown in
  place, the step's new parts "popped" along their true insertion axis,
  and a teal arrow pointing from each popped part to its seat, and
- two inset renders (the shell's 14 insert spots; the flipped lid's 2).

Gold pegs mark every heat-set insert bore in the step where that batch
melts in. The bench step lays the four wheel+tire assemblies flat on the
floor instead of floating them at their assembly stations.

Run AFTER robot_body_v2.py has exported, from the repository root:
    /Applications/Blender.app/Contents/MacOS/Blender -b --python cad/blender/render_assembly_steps_v2.py -- [thumbs|steps|all]
Images land in docs/images/guide_v2/.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Matrix, Vector

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import render_robot_body_v2 as base  # noqa: E402

ROOT = HERE.parents[1]
OUT = ROOT / "docs" / "images" / "guide_v2"
SAMPLES = 64
POP = 40.0

SILVER = (0.72, 0.73, 0.76, 1)
PCB_GREEN = (0.15, 0.45, 0.2, 1)
DARK = (0.13, 0.14, 0.16, 1)

PROXIES = {
    # name: (kind, dims..., location, color)
    "px_motor_L": ("cyl_y", 12.5, 68.45, (74, 75.8, 66), (0.45, 0.47, 0.5, 1)),
    "px_motor_R": ("cyl_y", 12.5, 68.45, (74, -75.8, 66), (0.45, 0.47, 0.5, 1)),
    "px_shaft_L": ("cyl_y", 2.0, 13.0, (74, 115.5, 66), SILVER),
    "px_shaft_R": ("cyl_y", 2.0, 13.0, (74, -115.5, 66), SILVER),
    "px_battery": ("box", (110, 75, 27), (30, 0, 65.5), (0.2, 0.3, 0.55, 1)),
    "px_mdds10": ("box", (67, 101, 14), (-67, 0, 71), (0.34, 0.18, 0.52, 1)),
    "px_mdds10_terms": ("box", (44, 9, 9), (-67, 45, 74), (0.2, 0.55, 0.25, 1)),
    "px_pi": ("box", (85, 56, 16), (-53, 0, 99), PCB_GREEN),
    "px_pi_ports": ("box", (10, 40, 11), (-14, 0, 103), DARK),
    "px_pico": ("box", (52, 21, 6), (3, 63.5, 56), (0.15, 0.45, 0.25, 1)),
    "px_reg1": ("box", (20, 40, 8), (102, -30, 98), (0.2, 0.5, 0.3, 1)),
    "px_reg2": ("box", (25, 25, 9), (73, 7, 97), (0.2, 0.5, 0.3, 1)),
    "px_relay": ("box", (26, 22, 25), (-23, -79, 63.5), (0.12, 0.12, 0.14, 1)),
    "px_relay_bracket": ("box", (52, 22, 2.5), (-20, -79, 50.2), SILVER),
    "px_fuse": ("box", (43, 92, 32), (46, -21, 122), (0.1, 0.1, 0.12, 1)),
    "px_estop_base": ("cyl_z", 30, 2, (59, 56, 183), (0.95, 0.75, 0.05, 1)),
    "px_estop_stem": ("cyl_z", 11, 14, (59, 56, 191), (0.1, 0.1, 0.1, 1)),
    "px_estop_cap": ("cyl_z", 20, 14, (59, 56, 203), (0.8, 0.06, 0.05, 1)),
    "px_mic": ("cyl_z", 35, 10, (60, -25, 168), (0.14, 0.15, 0.17, 1)),
    "px_speaker_L": ("box", (70, 17, 30), (-13, 95, 130), (0.14, 0.15, 0.17, 1)),
    "px_speaker_R": ("box", (70, 17, 30), (-13, -95, 130), (0.14, 0.15, 0.17, 1)),
    "px_tof_L": ("box", (25, 5, 17), (-20, 100, 95), (0.2, 0.35, 0.7, 1)),
    "px_tof_R": ("box", (25, 5, 17), (-20, -100, 95), (0.2, 0.35, 0.7, 1)),
    "px_tof_F": ("box", (5, 20, 15), (-113.5, 16.5, 106), (0.2, 0.35, 0.7, 1)),
    "px_tof_F2": ("box", (5, 20, 15), (-113.5, -16.5, 106), (0.2, 0.35, 0.7, 1)),
    "px_servo": ("box", (13, 29, 30), (-30, 0, 200), (0.45, 0.47, 0.5, 1)),
    "px_camera": ("box", (4, 25, 24), (-58, 0, 254), (0.09, 0.1, 0.12, 1)),
    "px_cam_lens": ("cyl_x", 6.5, 6, (-62.5, 0, 254), (0.05, 0.05, 0.06, 1)),
    # Six feeler switches seated in the six real tray pockets: four corner
    # pockets run their long axis along Y, the front/back pair along X.
    "px_switch": ("box", (6.5, 18.5, 6.5), (-101, 56, 45), (0.2, 0.22, 0.25, 1)),
    "px_switch_2": ("box", (6.5, 18.5, 6.5), (-101, -56, 45), (0.2, 0.22, 0.25, 1)),
    "px_switch_3": ("box", (6.5, 18.5, 6.5), (101, 56, 45), (0.2, 0.22, 0.25, 1)),
    "px_switch_4": ("box", (6.5, 18.5, 6.5), (101, -56, 45), (0.2, 0.22, 0.25, 1)),
    "px_switch_5": ("box", (18.5, 6.5, 6.5), (0, 99, 45), (0.2, 0.22, 0.25, 1)),
    "px_switch_6": ("box", (18.5, 6.5, 6.5), (0, -99, 45), (0.2, 0.22, 0.25, 1)),
    "px_insert": ("cyl_z", 2.3, 5.7, (0, 0, 60), (0.72, 0.55, 0.2, 1)),
    "px_insert_rib": ("cyl_z", 2.65, 1.4, (0, 0, 61.8), (0.6, 0.44, 0.14, 1)),
    "px_insert_rib2": ("cyl_z", 2.65, 1.4, (0, 0, 58.6), (0.6, 0.44, 0.14, 1)),
    "px_screw": ("cyl_z", 1.5, 8.0, (0, 0, 40), (0.55, 0.57, 0.6, 1)),
    "px_screw_head": ("cyl_z", 2.85, 3.0, (0, 0, 45.5), (0.35, 0.37, 0.4, 1)),
}
FASTENER_GROUPS = {"px_insert": ["px_insert", "px_insert_rib", "px_insert_rib2"],
                   "px_screw": ["px_screw", "px_screw_head"]}
# Accessory proxies render inside their primary's thumbnail and never get
# their own arrow; the estop stack thumbs as one button.
THUMB_GROUPS = {
    "px_motor_L": ["px_motor_L", "px_shaft_L"],
    "px_pi": ["px_pi", "px_pi_ports"],
    "px_mdds10": ["px_mdds10", "px_mdds10_terms"],
    "px_relay": ["px_relay", "px_relay_bracket"],
    "px_camera": ["px_camera", "px_cam_lens"],
    "px_estop_cap": ["px_estop_cap", "px_estop_stem", "px_estop_base"],
    **FASTENER_GROUPS,
}
THUMB_SKIP = {"px_insert_rib", "px_insert_rib2", "px_screw_head",
              "px_shaft_L", "px_shaft_R", "px_pi_ports", "px_mdds10_terms",
              "px_relay_bracket", "px_cam_lens", "px_estop_stem", "px_estop_base",
              "px_switch_2", "px_switch_3", "px_switch_4", "px_switch_5", "px_switch_6",
              "px_tof_F", "px_tof_F2", "px_tof_R", "px_speaker_R", "px_motor_R"}
ACCESSORIES = {"px_shaft_L": "px_motor_L", "px_shaft_R": "px_motor_R",
               "px_pi_ports": "px_pi", "px_mdds10_terms": "px_mdds10",
               "px_relay_bracket": "px_relay", "px_cam_lens": "px_camera",
               "px_estop_stem": "px_estop_cap", "px_estop_base": "px_estop_cap"}

# (title_key, printed parts added, proxies added, camera)
STEPS = [
    ("tray", ["tray_v2"], [], "body"),
    ("inserts", [], ["px_insert"], "body"),
    ("motors", ["motor_cap_v2", "motor_cap_v2_m"],
     ["px_motor_L", "px_motor_R", "px_shaft_L", "px_shaft_R"], "rear"),
    ("wheels_bench", ["rear_wheel_v2", "rear_wheel_v2_m", "front_wheel_v2", "front_wheel_v2_m",
                      "tire_v2", "tire_v2_1", "tire_v2_2", "tire_v2_3"], [], "bench"),
    ("front_pods", ["front_pod_left_v2", "front_pod_right_v2"], [], "front"),
    ("wheels_on", ["rear_wheel_v2", "rear_wheel_v2_m", "front_wheel_v2", "front_wheel_v2_m",
                   "tire_v2", "tire_v2_1", "tire_v2_2", "tire_v2_3"], [], "rear_wide"),
    ("tower", ["controller_tower_v2"], ["px_mdds10", "px_mdds10_terms"], "tower"),
    ("pi", [], ["px_pi", "px_pi_ports"], "tower"),
    ("battery", ["battery_pad_frame_v2", "battery_clamp_v2"], ["px_battery"], "body"),
    ("pico", ["pico_clamp_v2"], ["px_pico"], "pico"),
    ("relay", [], ["px_relay", "px_relay_bracket"], "tower"),
    ("deck", ["deck_v2"], ["px_reg1", "px_reg2", "px_fuse"], "body"),
    ("shell", ["shell_v2"], [], "body"),
    ("bumpers", ["bumper_front_v2", "bumper_rear_v2"],
     ["px_switch", "px_switch_2", "px_switch_3", "px_switch_4", "px_switch_5", "px_switch_6"],
     "low"),
    ("panels", ["fascia_v2", "rear_panel_v2"], ["px_tof_F", "px_tof_F2"], "body"),
    ("speakers", ["speaker_clamp_v2", "speaker_clamp_v2_m", "tof_clamp_v2", "tof_clamp_v2_m"],
     ["px_speaker_L", "px_speaker_R", "px_tof_L", "px_tof_R"], "interior"),
    ("lid", ["lid_v2", "mic_cradle_v2"], ["px_estop_base", "px_estop_stem", "px_estop_cap", "px_mic"], "body_tall"),
    ("neck", ["neck_v2", "bayonet_collar_v2"], ["px_servo"], "neckcam"),
    ("head", ["head_shell_v2", "yoke_v2", "head_pan_plate_v2"], ["px_camera", "px_cam_lens"], "head"),
    ("face", ["head_faceplate_v2", "eye_diffuser_bar_v2", "status_diffuser_bar_v2"], [], "face"),
]

# Pop vector per part (base name; mirrored *_m parts flip Y automatically).
# "OUT_Y" pops outboard along the part's own side of the robot.
POP_DIR = {
    "px_motor_L": (0, 0, 48), "px_motor_R": (0, 0, 48),
    "px_shaft_L": (0, 0, 48), "px_shaft_R": (0, 0, 48),
    "motor_cap_v2": (0, 0, 96),
    "front_pod_left_v2": (0, 0, 46), "front_pod_right_v2": (0, 0, 46),
    "rear_wheel_v2": "OUT_Y", "front_wheel_v2": "OUT_Y", "tire_v2": "OUT_Y",
    "controller_tower_v2": (0, 0, 48),
    "px_mdds10": (0, 0, 84), "px_mdds10_terms": (0, 0, 84),
    "px_pi": (0, 0, 46), "px_pi_ports": (0, 0, 46),
    "battery_pad_frame_v2": (0, 0, 34), "px_battery": (0, 0, 62),
    "battery_clamp_v2": (0, 0, 96),
    "px_pico": (0, 0, 42), "pico_clamp_v2": (0, 0, 72),
    "px_relay": (0, 0, 46), "px_relay_bracket": (0, 0, 46),
    "deck_v2": (0, 0, 58), "px_reg1": (0, 0, 26), "px_reg2": (0, 0, 26),
    "px_fuse": (0, 0, 88),
    "shell_v2": (0, 0, 72),
    "bumper_front_v2": (-60, 0, 0), "bumper_rear_v2": (60, 0, 0),
    "px_switch": (-34, 0, 0), "px_switch_2": (-34, 0, 0), "px_switch_3": (34, 0, 0),
    "px_switch_4": (34, 0, 0), "px_switch_5": (0, 34, 0), "px_switch_6": (0, -34, 0),
    "fascia_v2": (-34, 0, 0), "rear_panel_v2": (40, 0, 0),
    "px_tof_F": (-26, 0, 0), "px_tof_F2": (-26, 0, 0),
    "px_speaker_L": (0, 0, 52), "px_speaker_R": (0, 0, 52),
    "px_tof_L": (0, 0, 58), "px_tof_R": (0, 0, 58),
    "speaker_clamp_v2": (0, 0, 78), "tof_clamp_v2": (0, 0, 76),
    "lid_v2": (0, 0, 58),
    "px_estop_base": (0, 0, 70), "px_estop_stem": (0, 0, 70), "px_estop_cap": (0, 0, 70),
    "px_mic": (0, 0, 52), "mic_cradle_v2": (0, 0, 36),
    "neck_v2": (0, 0, 55),
    "bayonet_collar_v2": (0, 0, -42), "px_servo": (0, 0, -42),
    "head_shell_v2": (0, 0, 68), "yoke_v2": (0, 0, 34),
    "head_pan_plate_v2": (0, -75, -8),
    "px_camera": (-40, 0, 68), "px_cam_lens": (-40, 0, 68),
    "head_faceplate_v2": (-36, 0, 0),
    "eye_diffuser_bar_v2": (-26, 0, 0), "status_diffuser_bar_v2": (-46, 0, 0),
}
OUT_Y_POP = 45.0
# Parts whose arrow should anchor off its part center (None keeps that
# axis): dodging interior geometry, or lifting axle-line arrows clear of
# the pegs/shafts that would otherwise swallow them.
ARROW_ANCHOR = {
    "shell_v2": (0, -80, None), "deck_v2": (60, -30, None),
    "rear_wheel_v2": (None, None, 112), "rear_wheel_v2_m": (None, None, 112),
    "front_wheel_v2": (None, None, 112), "front_wheel_v2_m": (None, None, 112),
}
# Parts whose arrow direction differs from their pop (e.g. the camera pops
# up WITH the popped head but slides in horizontally).
ARROW_DIR = {"px_camera": (-40, 0, 0)}
# Tires ride their wheels in the wheels-on step: one arrow per pair.
NO_ARROW = ({"px_insert", "px_screw", "tire_v2", "tire_v2_1", "tire_v2_2", "tire_v2_3"}
            | set(ACCESSORIES))

CAMS = {
    "body": ((-430, -380, 330), (0, 0, 110), 55),
    "body_tall": ((-455, -405, 395), (0, 0, 142), 55),
    "tower": ((-360, -320, 300), (-25, 0, 90), 55),
    "pico": ((-60, -470, 340), (5, 40, 80), 55),
    "neckcam": ((-215, -195, 470), (-8, 8, 188), 55),
    "rear": ((400, 345, 312), (18, 15, 88), 55),
    "rear_wide": ((465, 405, 340), (0, 5, 78), 55),
    "front": ((-420, -300, 240), (-40, 0, 80), 55),
    "bench": ((-135, -310, 260), (0, -8, 30), 55),
    "low": ((-520, -365, 195), (0, 0, 52), 50),
    "interior": ((-230, -210, 600), (-5, 12, 110), 55),
    "head": ((-340, -260, 430), (-26, 0, 268), 55),
    "face": ((-430, -220, 335), (-55, 0, 186), 55),
}

# Bench grid for the wheel-prep step: (part, paired tire, floor target).
BENCH_TARGETS = [
    ("rear_wheel_v2", "tire_v2_2", (-52, -52, 35)),
    ("rear_wheel_v2_m", "tire_v2_3", (52, -52, 35)),
    ("front_wheel_v2", "tire_v2", (-52, 52, 35)),
    ("front_wheel_v2_m", "tire_v2_1", (52, 52, 35)),
]
WHEEL_STATIONS = {"rear_wheel_v2": (74, 118, 66), "rear_wheel_v2_m": (74, -118, 66),
                  "front_wheel_v2": (-74, 118, 66), "front_wheel_v2_m": (-74, -118, 66)}

# Insert-marker batches beyond the tray step: (step key, [(x, y, z, axis)]).
# The shell and lid batches render in their inset views instead.
STEP_MARKERS = {
    "front_pods": [(-74, 134, 66 + 46, "Y"), (-74, -134, 66 + 46, "Y")],
}
SHELL_MARKERS = (
    [(sx * 110, sy * 85, 40.5, "Z") for sx in (1, -1) for sy in (1, -1)]      # corner lugs (bores open DOWN)
    + [(sx * 100, sy * 90, 182.5, "Z") for sx in (1, -1) for sy in (1, -1)]   # lid-ledge holes
    + [(jx, sy * 103.8, 156.5, "Z") for jx in (-52, 26) for sy in (1, -1)]    # speaker posts
    + [(-32, sy * 103.8, 108.5, "Z") for sy in (1, -1)]                       # sensor bosses
)


def make_proxy(name, spec, mats_cache):
    kind = spec[0]
    if kind == "box":
        (lx, ly, lz), loc = spec[1], spec[2]
        bpy.ops.mesh.primitive_cube_add(location=loc)
        obj = bpy.context.object
        obj.scale = (lx / 2, ly / 2, lz / 2)
        color = spec[3]
    else:
        r, h, loc, color = spec[1], spec[2], spec[3], spec[4]
        rotation = {"cyl_z": (0, 0, 0), "cyl_y": (math.pi / 2, 0, 0),
                    "cyl_x": (0, math.pi / 2, 0)}[kind]
        bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=h, location=loc, rotation=rotation)
        obj = bpy.context.object
    obj.name = name
    key = str(color)
    if key not in mats_cache:
        mat = bpy.data.materials.new(key)
        mat.use_nodes = True
        mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = color
        mat.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.45
        mat.diffuse_color = color
        mats_cache[key] = mat
    obj.data.materials.append(mats_cache[key])
    return obj


def make_marker(loc, axis, mats_cache, name="marker"):
    rotation = {"Z": (0, 0, 0), "Y": (math.pi / 2, 0, 0), "X": (0, math.pi / 2, 0)}[axis]
    bpy.ops.mesh.primitive_cylinder_add(radius=3.2, depth=6, location=loc, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    key = "marker_gold"
    if key not in mats_cache:
        mat = bpy.data.materials.new(key)
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes["Principled BSDF"]
        bsdf.inputs["Base Color"].default_value = (0.85, 0.62, 0.15, 1)
        bsdf.inputs["Roughness"].default_value = 0.35
        if "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = (0.85, 0.62, 0.15, 1)
            bsdf.inputs["Emission Strength"].default_value = 0.35
        mat.diffuse_color = (0.85, 0.62, 0.15, 1)
        mats_cache[key] = mat
    obj.data.materials.append(mats_cache[key])
    return obj


def arrow_material(mats_cache):
    """Annotation arrows: translucent magenta — a color no printed part or
    purchased proxy uses — so they read as instructions, not plastic."""
    key = "arrow_annotation"
    if key not in mats_cache:
        mat = bpy.data.materials.new(key)
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes["Principled BSDF"]
        color = (0.85, 0.04, 0.45, 1)
        bsdf.inputs["Base Color"].default_value = color
        bsdf.inputs["Roughness"].default_value = 0.4
        bsdf.inputs["Alpha"].default_value = 0.6
        if "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = color
            bsdf.inputs["Emission Strength"].default_value = 0.25
        # Transparency across EEVEE generations (attribute names differ).
        if hasattr(mat, "surface_render_method"):
            mat.surface_render_method = "BLENDED"
        if hasattr(mat, "blend_method"):
            mat.blend_method = "BLEND"
        if hasattr(mat, "use_transparent_shadow"):
            mat.use_transparent_shadow = True
        mat.diffuse_color = (0.85, 0.04, 0.45, 0.6)
        mats_cache[key] = mat
    return mats_cache[key]


def make_arrow(tail: Vector, tip: Vector, mats_cache, shaft_r=2.4, head_r=5.5, head_len=10.0):
    """A solid arrow from tail to tip (cone at the tip)."""
    made = []
    vec = tip - tail
    length = vec.length
    if length < 12:
        return made
    direction = vec.normalized()
    quat = direction.to_track_quat("Z", "Y")
    shaft_len = max(length - head_len, 4)
    bpy.ops.mesh.primitive_cylinder_add(radius=shaft_r, depth=shaft_len)
    shaft = bpy.context.object
    shaft.rotation_mode = "QUATERNION"
    shaft.rotation_quaternion = quat
    shaft.location = tail + direction * (shaft_len / 2)
    made.append(shaft)
    bpy.ops.mesh.primitive_cone_add(radius1=head_r, radius2=0, depth=head_len)
    head = bpy.context.object
    head.rotation_mode = "QUATERNION"
    head.rotation_quaternion = quat
    head.location = tail + direction * (shaft_len + head_len / 2)
    made.append(head)
    mat = arrow_material(mats_cache)
    for obj in made:
        obj.data.materials.append(mat)
        # Annotation, not a part: cast no shadow onto the model.
        if hasattr(obj, "visible_shadow"):
            obj.visible_shadow = False
    return made


def resolve_pop(obj) -> Vector:
    """The pop vector for one object: POP_DIR by base name, Y mirrored for
    *_m twins, and OUT_Y resolved to the object's own side of the robot."""
    name = obj.name
    base_name = name[:-2] if name.endswith("_m") else name
    if base_name.startswith("tire_v2"):
        base_name = "tire_v2"
    d = POP_DIR.get(base_name, (0, 0, POP))
    if d == "OUT_Y":
        return Vector((0, OUT_Y_POP if world_center(obj).y > 0 else -OUT_Y_POP, 0))
    d = Vector(d)
    if name.endswith("_m"):
        d.y = -d.y
    return d


def world_center(obj) -> Vector:
    pts = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
    return sum(pts, Vector()) / 8


def camera_to(loc, target, lens=55):
    old = bpy.context.scene.camera
    if old:
        bpy.data.objects.remove(old, do_unlink=True)
    bpy.ops.object.camera_add(location=loc)
    cam = bpy.context.object
    cam.data.lens = lens
    cam.data.sensor_width = 36
    cam.data.clip_end = 5000
    base.look_at(cam, target)
    bpy.context.scene.camera = cam


def render(path, res=(1100, 850)):
    scene = bpy.context.scene
    scene.render.resolution_x, scene.render.resolution_y = res
    if hasattr(scene, "eevee"):
        scene.eevee.taa_render_samples = SAMPLES
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    print("rendered", path.name)


def all_objects():
    objects = base.setup_scene()
    mats_cache = {}
    for name, spec in PROXIES.items():
        objects[name] = make_proxy(name, spec, mats_cache)
    for obj in objects.values():
        obj.hide_render = True
    return objects, mats_cache


def thumbs(objects):
    floor = bpy.data.objects.get("review_floor")
    if floor:
        floor.hide_render = True
    printed = [n for n in objects
               if not n.startswith("px_") and not n.endswith(("_m", "_1", "_2", "_3"))]
    for name in printed + [n for n in PROXIES if n not in THUMB_SKIP]:
        group = THUMB_GROUPS.get(name, [name])
        for g in group:
            objects[g].hide_render = False
        pts = []
        for g in group:
            pts += [objects[g].matrix_world @ Vector(c) for c in objects[g].bound_box]
        center = sum(pts, Vector()) / len(pts)
        radius = max((p - center).length for p in pts)
        direction = Vector((-1, -0.85, 0.75)).normalized()
        camera_to(center + direction * max(radius * 3.2, 60), center, lens=70)
        render(OUT / f"thumb_{name}.png", res=(560, 560))
        for g in group:
            objects[g].hide_render = True
    if floor:
        floor.hide_render = False


def bench_layout(objects):
    """Lay the four wheel+tire assemblies flat on the floor in a 2x2 grid;
    returns marker positions for the two rear-hub insert bores. Mirrored
    *_m wheels share the +Y wheel's mesh with a -Y scale, so their bench
    matrix bakes the mirror in around the +Y mesh station."""
    lay_flat = Matrix.Rotation(math.radians(90), 4, "X")
    mirror_y = Matrix.Diagonal((1, -1, 1, 1))
    markers = []
    for wheel_name, tire_name, target in BENCH_TARGETS:
        target = Vector(target)
        wheel, tire = objects[wheel_name], objects[tire_name]
        station = Vector(WHEEL_STATIONS[wheel_name])
        mesh_station = Vector((station.x, abs(station.y), station.z))
        mat = Matrix.Translation(target) @ lay_flat
        if wheel_name.endswith("_m"):
            mat = mat @ mirror_y
        wheel.matrix_world = mat @ Matrix.Translation(-mesh_station)
        tire.matrix_world = Matrix.Translation(target) @ lay_flat
        if wheel_name.startswith("rear_wheel"):
            # The rim screw bore (and the tire's access port) face the
            # camera after lay-flat; the gold peg hovers just outside.
            markers.append((target.x, target.y - 49, target.z, "Y"))
    return markers


def reset_bench(objects):
    mirror_y = Matrix.Diagonal((1, -1, 1, 1))
    for wheel_name, tire_name, _ in BENCH_TARGETS:
        objects[wheel_name].matrix_world = (mirror_y if wheel_name.endswith("_m")
                                            else Matrix.Identity(4))
        objects[tire_name].matrix_world = Matrix.Translation(
            Vector(base.TIRE_STATIONS[["tire_v2", "tire_v2_1", "tire_v2_2", "tire_v2_3"]
                                      .index(tire_name)]))


def front_floor_arrow(mats_cache):
    """A hovering arrow pointing at the tray's front edge for step 1."""
    return make_arrow(Vector((-182, -42, 60)), Vector((-128, -18, 54)), mats_cache,
                      shaft_r=3.2, head_r=7.5, head_len=13)


def add_step_arrows(new_objects, pops, mats_cache):
    arrows = []
    for obj in new_objects:
        if obj.name in NO_ARROW or obj.name.startswith(("px_insert", "px_screw")):
            continue
        d = pops.get(obj.name)
        if d is None or d.length < 24:
            continue
        if obj.name in ARROW_DIR:
            d = Vector(ARROW_DIR[obj.name])
        d_unit = d.normalized()
        pts = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
        center = sum(pts, Vector()) / 8
        anchor = ARROW_ANCHOR.get(obj.name)
        if anchor is not None:
            for axis, value in zip(("x", "y", "z"), anchor):
                if value is not None:
                    setattr(center, axis, value)
        min_proj = min((p - center).dot(d_unit) for p in pts)
        tail = center + d_unit * (min_proj - 5)
        tip = tail - d_unit * max(d.length - 14, 18)
        arrows += make_arrow(tail, tip, mats_cache)
    return arrows


def steps(objects, mats_cache):
    placed = []
    for idx, (key, parts, proxies, cam) in enumerate(STEPS, start=1):
        new = [objects[n] for n in parts + proxies if n in objects]
        bench = key == "wheels_bench"
        for obj in objects.values():
            obj.hide_render = True
        if not bench:
            for obj in placed:
                obj.hide_render = False
        temp = []
        pops = {}
        marker_specs = list(STEP_MARKERS.get(key, []))
        if bench:
            marker_specs += bench_layout(objects)
        for obj in new:
            obj.hide_render = False
            if key == "inserts":
                obj.hide_render = True     # inserts page uses gold markers below
            elif not bench:
                d = resolve_pop(obj)
                pops[obj.name] = d
                obj.location.x += d.x
                obj.location.y += d.y
                obj.location.z += d.z
        if key == "inserts":
            marker_data = json.loads((OUT / "insert_markers.json").read_text())
            marker_specs += [(x, y, z + 8, "Z") for x, y, z in marker_data]
        for mi, (x, y, z, axis) in enumerate(marker_specs):
            temp.append(make_marker((x, y, z), axis, mats_cache, name=f"mk_{mi}"))
        if key == "tray":
            temp += front_floor_arrow(mats_cache)
        if not bench:
            temp += add_step_arrows(new, pops, mats_cache)
        loc, target, lens = CAMS[cam]
        camera_to(loc, target, lens=lens)
        render(OUT / f"step_{idx:02d}_{key}.png")
        for obj in new:
            d = pops.get(obj.name)
            if d is not None:
                obj.location.x -= d.x
                obj.location.y -= d.y
                obj.location.z -= d.z
        for t in temp:
            bpy.data.objects.remove(t, do_unlink=True)
        if bench:
            reset_bench(objects)
            for obj in new:
                obj.hide_render = True   # bench parts wait for the wheels_on step
        else:
            placed.extend(obj for obj in new
                          if not obj.name.startswith(("px_insert", "px_screw")))


def insets(objects, mats_cache):
    """Two standalone insert-location views: the shell's 14 spots, and the
    lid flipped upside down showing its 2 mic bosses."""
    for obj in objects.values():
        obj.hide_render = True
    shell = objects["shell_v2"]
    shell.hide_render = False
    temp = [make_marker((x, y, z), axis, mats_cache, name=f"si_{i}")
            for i, (x, y, z, axis) in enumerate(SHELL_MARKERS)]
    camera_to((-390, -350, 320), (0, 0, 112))
    render(OUT / "step_13b_shell_inserts.png", res=(900, 700))
    for t in temp:
        bpy.data.objects.remove(t, do_unlink=True)
    shell.hide_render = True

    lid = objects["lid_v2"]
    lid.hide_render = False
    lid_center = world_center(lid)
    lid.matrix_world = (Matrix.Translation(lid_center) @ Matrix.Rotation(math.pi, 4, "X")
                        @ Matrix.Translation(-lid_center))
    temp = []
    for i, (bx, by) in enumerate(((30, -25), (90, -25))):
        flipped = lid_center + (Matrix.Rotation(math.pi, 3, "X")
                                @ (Vector((bx, by, 171)) - lid_center))
        temp.append(make_marker((flipped.x, flipped.y, flipped.z + 8), "Z",
                                mats_cache, name=f"li_{i}"))
    camera_to((-190, -275, 470), (0, -12, 183))
    render(OUT / "step_17b_lid_inserts.png", res=(900, 700))
    for t in temp:
        bpy.data.objects.remove(t, do_unlink=True)
    lid.matrix_world = Matrix.Identity(4)
    lid.hide_render = True


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    mode = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else "all"
    objects, mats_cache = all_objects()
    sys.path.insert(0, str(ROOT / "cad" / "python"))
    if mode in ("thumbs", "all"):
        thumbs(objects)
    if mode in ("steps", "all"):
        steps(objects, mats_cache)
        insets(objects, mats_cache)


if __name__ == "__main__":
    main()
