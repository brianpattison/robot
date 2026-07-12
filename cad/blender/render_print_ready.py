"""Render representative grounded STLs from the canonical print inventory."""

from __future__ import annotations

import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[2]
PRINT_DIR = ROOT / "cad" / "exports" / "print_ready"
IMAGE_PATH = ROOT / "docs" / "images" / "codex_robot_body_v1_print_ready.png"


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for material in list(bpy.data.materials):
        bpy.data.materials.remove(material)


def material(name, color, roughness=0.4, metallic=0.0):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = color
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    return mat


def import_stl(name, mat, location):
    path = PRINT_DIR / f"{name}.stl"
    if hasattr(bpy.ops.wm, "stl_import"):
        bpy.ops.wm.stl_import(filepath=str(path))
    else:
        bpy.ops.import_mesh.stl(filepath=str(path))
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(mat)
    obj.location = location
    return obj


def look_at(obj, target):
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def add_plate(x, mat):
    bpy.ops.mesh.primitive_cube_add(location=(x, 0, -2.0), scale=(110, 110, 2.0))
    plate = bpy.context.object
    plate.name = f"print_bed_{x:+.0f}"
    plate.data.materials.append(mat)


def main():
    manifest = json.loads(
        (PRINT_DIR / "codex_robot_body_v1_print_manifest.json").read_text(encoding="utf-8")
    )
    expected = {
        "body_shell_q_front_left",
        "head_shell",
        "side_fairing_left_front",
        "motor_pod_right",
        "motor_pod_cover_right",
        "front_idler_pod_right",
        "front_idler_retainer_right_outer",
        "body_seam_plate_side_left",
    }
    missing = sorted(expected - set(manifest["parts"]))
    if missing:
        raise RuntimeError(f"Print manifest missing representative parts: {missing}")

    clear_scene()
    mats = {
        "petg_shell": material("petg_shell", (0.98, 0.82, 0.56, 1.0), roughness=0.30),
        "petg_structural": material("petg_structural", (0.04, 0.55, 0.68, 1.0), roughness=0.32),
        "bed": material("bed", (0.055, 0.065, 0.08, 1.0), roughness=0.58, metallic=0.20),
    }

    for x in (-240.0, 0.0, 240.0):
        add_plate(x, mats["bed"])

    placements = {
        "body_shell_q_front_left": (-240.0, 0.0, 0.1),
        "head_shell": (-66.0, 0.0, 0.1),
        "side_fairing_left_front": (72.0, 0.0, 0.1),
        "motor_pod_right": (195.0, -55.0, 0.1),
        "motor_pod_cover_right": (195.0, 48.0, 0.1),
        "front_idler_pod_right": (285.0, -55.0, 0.1),
        "front_idler_retainer_right_outer": (285.0, 48.0, 0.1),
        "body_seam_plate_side_left": (20.0, 82.0, 0.1),
    }
    for name, location in placements.items():
        profile = manifest["parts"][name]["material_profile"]
        import_stl(name, mats.get(profile, mats["petg_structural"]), location)

    bpy.ops.object.light_add(type="AREA", location=(-120, -320, 650))
    key = bpy.context.object
    key.data.energy = 2600
    key.data.size = 500
    look_at(key, (0, 0, 50))

    bpy.ops.object.light_add(type="AREA", location=(380, 180, 500))
    fill = bpy.context.object
    fill.data.energy = 1700
    fill.data.size = 360
    look_at(fill, (120, 0, 45))

    bpy.ops.object.camera_add(location=(0, -760, 620))
    camera = bpy.context.object
    camera.data.lens = 44
    camera.data.sensor_width = 36
    camera.data.clip_end = 3000
    look_at(camera, (0, 0, 48))
    bpy.context.scene.camera = camera

    scene = bpy.context.scene
    engines = {
        item.identifier
        for item in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items
    }
    scene.render.engine = (
        "BLENDER_EEVEE" if "BLENDER_EEVEE" in engines else "BLENDER_EEVEE_NEXT"
    )
    scene.render.resolution_x = 1400
    scene.render.resolution_y = 800
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(IMAGE_PATH)
    scene.world.color = (0.34, 0.25, 0.17)
    scene.world.use_nodes = True
    scene.world.node_tree.nodes["Background"].inputs["Color"].default_value = (
        0.34,
        0.25,
        0.17,
        1.0,
    )
    scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.8
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "AgX - Very High Contrast"
    scene.view_settings.exposure = 1.85
    scene.view_settings.use_white_balance = True
    scene.view_settings.white_balance_temperature = 6200
    bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    main()
