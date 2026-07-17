"""Render the LEGO-style step sequence and part thumbnails for the v2 guide.

Builds the full v2 scene (printed parts from cad/exports/v2 plus simple
color-coded proxies for every purchased part, sized from the registered
inventory), then renders:
- one thumbnail per printed design and per purchased proxy (for the
  parts-needed strips and the what's-in-the-box pages), and
- one render per assembly step, with everything assembled so far shown
  in place and the step's new parts "popped" 30 mm along their insertion
  axis, LEGO-style.

Run AFTER robot_body_v2.py has exported, from the repository root:
    /Applications/BambuStudio... no —
    /Applications/Blender.app/Contents/MacOS/Blender -b --python cad/blender/render_assembly_steps_v2.py -- [thumbs|steps|all]
Images land in docs/images/guide_v2/.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import render_robot_body_v2 as base  # noqa: E402

ROOT = HERE.parents[1]
OUT = ROOT / "docs" / "images" / "guide_v2"
SAMPLES = 64
POP = 32.0

PROXIES = {
    # name: (size or (kind, dims), location, color, label-ish)
    "px_motor_L": ("cyl_y", 12.5, 68.45, (74, 75.8, 66), (0.45, 0.47, 0.5, 1)),
    "px_motor_R": ("cyl_y", 12.5, 68.45, (74, -75.8, 66), (0.45, 0.47, 0.5, 1)),
    "px_battery": ("box", (110, 75, 27), (30, 0, 65.5), (0.2, 0.3, 0.55, 1)),
    "px_mdds10": ("box", (67, 101, 14), (-67, 0, 71), (0.45, 0.2, 0.5, 1)),
    "px_pi": ("box", (85, 56, 16), (-53, 0, 99), (0.15, 0.45, 0.2, 1)),
    "px_pico": ("box", (52, 21, 6), (3, 63.5, 56), (0.15, 0.45, 0.25, 1)),
    "px_reg1": ("box", (20, 40, 8), (102, -30, 98), (0.2, 0.5, 0.3, 1)),
    "px_reg2": ("box", (25, 25, 9), (73, 7, 97), (0.2, 0.5, 0.3, 1)),
    "px_relay": ("box", (52, 22, 26), (-20, -79, 64), (0.12, 0.12, 0.14, 1)),
    "px_fuse": ("box", (43, 92, 32), (46, -21, 122), (0.1, 0.1, 0.12, 1)),
    "px_estop_base": ("cyl_z", 30, 2, (59, 56, 183), (0.95, 0.75, 0.05, 1)),
    "px_estop_stem": ("cyl_z", 11, 14, (59, 56, 191), (0.1, 0.1, 0.1, 1)),
    "px_estop_cap": ("cyl_z", 20, 14, (59, 56, 203), (0.8, 0.06, 0.05, 1)),
    "px_mic": ("cyl_z", 35, 10, (60, -25, 168), (0.14, 0.15, 0.17, 1)),
    "px_speaker_L": ("box", (70, 17, 30), (-13, 95, 130), (0.14, 0.15, 0.17, 1)),
    "px_speaker_R": ("box", (70, 17, 30), (-13, -95, 130), (0.14, 0.15, 0.17, 1)),
    "px_tof_L": ("box", (25, 5, 17), (-20, 100, 95), (0.2, 0.35, 0.7, 1)),
    "px_tof_R": ("box", (25, 5, 17), (-20, -100, 95), (0.2, 0.35, 0.7, 1)),
    "px_servo": ("box", (13, 29, 30), (-30, 0, 200), (0.45, 0.47, 0.5, 1)),
    "px_camera": ("box", (4, 25, 24), (-58, 0, 254), (0.15, 0.45, 0.2, 1)),
    "px_switch": ("box", (18.5, 6.5, 6.5), (0, -99, 45), (0.2, 0.22, 0.25, 1)),
    "px_insert": ("cyl_z", 2.3, 5.7, (0, 0, 60), (0.72, 0.55, 0.2, 1)),
    "px_insert_rib": ("cyl_z", 2.65, 1.4, (0, 0, 61.8), (0.6, 0.44, 0.14, 1)),
    "px_insert_rib2": ("cyl_z", 2.65, 1.4, (0, 0, 58.6), (0.6, 0.44, 0.14, 1)),
    "px_screw": ("cyl_z", 1.5, 8.0, (0, 0, 40), (0.55, 0.57, 0.6, 1)),
    "px_screw_head": ("cyl_z", 2.85, 3.0, (0, 0, 45.5), (0.35, 0.37, 0.4, 1)),
}
FASTENER_GROUPS = {"px_insert": ["px_insert", "px_insert_rib", "px_insert_rib2"],
                   "px_screw": ["px_screw", "px_screw_head"]}

# (title_key, printed parts added, proxies added, camera)
STEPS = [
    ("tray", ["tray_v2"], [], "body"),
    ("inserts", [], ["px_insert"], "body"),
    ("motors", ["motor_cap_v2", "motor_cap_v2_m"], ["px_motor_L", "px_motor_R"], "rear"),
    ("wheels_bench", ["rear_wheel_v2", "rear_wheel_v2_m", "front_wheel_v2", "front_wheel_v2_m",
                      "tire_v2", "tire_v2_1", "tire_v2_2", "tire_v2_3"], [], "bench"),
    ("front_pods", ["front_pod_left_v2", "front_pod_right_v2"], [], "front"),
    ("wheels_on", ["rear_wheel_v2", "rear_wheel_v2_m", "front_wheel_v2", "front_wheel_v2_m",
                   "tire_v2", "tire_v2_1", "tire_v2_2", "tire_v2_3"], [], "rear"),
    ("tower", ["controller_tower_v2"], ["px_mdds10"], "body"),
    ("pi", [], ["px_pi"], "body"),
    ("battery", ["battery_pad_frame_v2", "battery_clamp_v2"], ["px_battery"], "body"),
    ("pico", ["pico_clamp_v2"], ["px_pico"], "pico"),
    ("relay", [], ["px_relay"], "body"),
    ("deck", ["deck_v2"], ["px_reg1", "px_reg2", "px_fuse"], "body"),
    ("shell", ["shell_v2"], [], "body"),
    ("bumpers", ["bumper_front_v2", "bumper_rear_v2"], [], "body"),
    ("panels", ["fascia_v2", "rear_panel_v2"], [], "body"),
    ("speakers", ["speaker_clamp_v2", "speaker_clamp_v2_m", "tof_clamp_v2", "tof_clamp_v2_m"],
     ["px_speaker_L", "px_speaker_R", "px_tof_L", "px_tof_R"], "body"),
    ("lid", ["lid_v2", "mic_cradle_v2"], ["px_estop_base", "px_estop_stem", "px_estop_cap", "px_mic"], "body"),
    ("neck", ["neck_v2", "bayonet_collar_v2"], ["px_servo"], "neckcam"),
    ("head", ["head_shell_v2", "yoke_v2", "head_pan_plate_v2"], ["px_camera"], "head"),
    ("face", ["head_faceplate_v2", "eye_diffuser_bar_v2"], [], "head"),
]

POP_DIR = {
    "fascia_v2": (-34, 0, 0), "rear_panel_v2": (40, 0, 0),
    "bayonet_collar_v2": (0, 0, -42), "px_servo": (0, 0, -42),
    "px_pico": (0, 0, 64), "pico_clamp_v2": (0, 0, 64),
}
CAMS = {
    "body": ((-430, -380, 330), (0, 0, 110)),
    "pico": ((-60, -470, 340), (5, 40, 80)),
    "neckcam": ((-170, -150, 440), (-26, 0, 195)),
    "rear": ((380, 330, 300), (20, 20, 90)),
    "front": ((-420, -300, 240), (-40, 0, 80)),
    "bench": ((-260, -240, 240), (0, 0, 60)),
    "head": ((-300, -230, 380), (-26, 0, 240)),
}


def make_proxy(name, spec, mats_cache):
    kind = spec[0]
    if kind == "box":
        (lx, ly, lz), loc = spec[1], spec[2]
        bpy.ops.mesh.primitive_cube_add(location=loc)
        obj = bpy.context.object
        obj.scale = (lx / 2, ly / 2, lz / 2)
        color = spec[3]
    elif kind == "cyl_z":
        r, h, loc, color = spec[1], spec[2], spec[3], spec[4]
        bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=h, location=loc)
        obj = bpy.context.object
    else:  # cyl_y
        r, h, loc, color = spec[1], spec[2], spec[3], spec[4]
        bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=h, location=loc,
                                            rotation=(math.pi / 2, 0, 0))
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
    return objects


def thumbs(objects):
    floor = bpy.data.objects.get("review_floor")
    if floor:
        floor.hide_render = True
    printed = [n for n in objects if not n.startswith("px_") and not n.endswith(("_m", "_1", "_2", "_3"))]
    skip = {"px_insert_rib", "px_insert_rib2", "px_screw_head"}
    for name in printed + [n for n in PROXIES if n not in skip]:
        group = FASTENER_GROUPS.get(name, [name])
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


def steps(objects):
    placed = []
    for idx, (key, parts, proxies, cam) in enumerate(STEPS, start=1):
        new = [objects[n] for n in parts + proxies if n in objects]
        bench = key == "wheels_bench"
        for obj in objects.values():
            obj.hide_render = True
        if not bench:
            for obj in placed:
                obj.hide_render = False
        pops = {}
        for obj in new:
            obj.hide_render = False
            if key == "inserts":
                obj.hide_render = True     # inserts page uses markers below
            else:
                d = POP_DIR.get(obj.name.rstrip("_m"), (0, 0, POP))
                pops[obj.name] = d
                obj.location.x += d[0]
                obj.location.y += d[1]
                obj.location.z += d[2]
        markers = []
        if key == "inserts":
            import json
            marker_data = json.loads((OUT / "insert_markers.json").read_text())
            mats_cache = {}
            for mi, (x, y, z) in enumerate(marker_data):
                m = make_proxy(f"mk_{mi}", ("cyl_z", 3.2, 6, (x, y, z + 8), (0.85, 0.62, 0.15, 1)),
                               mats_cache)
                markers.append(m)
        loc, target = CAMS[cam]
        camera_to(loc, target)
        render(OUT / f"step_{idx:02d}_{key}.png")
        for obj in new:
            if key != "inserts":
                d = pops.get(obj.name, (0, 0, POP))
                obj.location.x -= d[0]
                obj.location.y -= d[1]
                obj.location.z -= d[2]
        for m in markers:
            bpy.data.objects.remove(m, do_unlink=True)
        if bench:
            for obj in new:
                obj.hide_render = True   # bench parts wait for the wheels_on step
        else:
            placed.extend(new)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    mode = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else "all"
    objects = all_objects()
    sys.path.insert(0, str(ROOT / "cad" / "python"))
    if mode in ("thumbs", "all"):
        thumbs(objects)
    if mode in ("steps", "all"):
        steps(objects)


if __name__ == "__main__":
    main()
