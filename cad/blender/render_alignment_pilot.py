"""Render the exact three-piece split-alignment coupon at inspection scale."""

from __future__ import annotations

import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[2]
COUPON_DIR = ROOT / "cad" / "exports" / "coupons"
IMAGE_PATH = ROOT / "docs" / "images" / "codex_robot_body_v1_alignment_pilot.png"


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for mat in list(bpy.data.materials):
        bpy.data.materials.remove(mat)


def material(name, color, roughness=0.35, metallic=0.0):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = color
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    return mat


def import_stl(name, mat):
    path = COUPON_DIR / f"{name}.stl"
    if not path.exists():
        raise RuntimeError(f"Missing coupon STL: {path}")
    if hasattr(bpy.ops.wm, "stl_import"):
        bpy.ops.wm.stl_import(filepath=str(path))
    else:
        bpy.ops.import_mesh.stl(filepath=str(path))
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(mat)
    return obj


def ground(obj, z=0.1):
    bpy.context.view_layer.update()
    min_z = min((obj.matrix_world @ Vector(corner)).z for corner in obj.bound_box)
    obj.location.z += z - min_z


def look_at(obj, target):
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def main():
    clear_scene()
    mats = {
        "plate": material("pilot_plate", (0.03, 0.55, 0.66, 1.0), roughness=0.28),
        "shell": material("shell_recess", (0.96, 0.79, 0.53, 1.0), roughness=0.31),
        "bed": material("inspection_bed", (0.035, 0.045, 0.06, 1.0), roughness=0.58, metallic=0.18),
    }

    bpy.ops.mesh.primitive_cube_add(location=(0, 0, -2.0), scale=(48, 34, 2.0))
    bed = bpy.context.object
    bed.name = "inspection_bed"
    bed.data.materials.append(mats["bed"])

    plate = import_stl("split_pilot_coupon_plate", mats["plate"])
    plate.location.x = -23.0
    ground(plate)

    for name, y in (
        ("split_pilot_coupon_shell_front", -9.0),
        ("split_pilot_coupon_shell_rear", 9.0),
    ):
        shell = import_stl(name, mats["shell"])
        shell.rotation_euler.x = math.radians(180.0)
        shell.location.x = 20.0
        shell.location.y = y
        ground(shell)

    bpy.ops.object.light_add(type="AREA", location=(-35, -55, 95))
    key = bpy.context.object
    key.data.energy = 1100
    key.data.size = 70
    look_at(key, (0, 0, 5))

    bpy.ops.object.light_add(type="AREA", location=(65, 25, 65))
    fill = bpy.context.object
    fill.data.energy = 750
    fill.data.size = 55
    look_at(fill, (12, 0, 4))

    bpy.ops.object.camera_add(location=(72, -105, 82))
    camera = bpy.context.object
    camera.data.lens = 62
    camera.data.sensor_width = 36
    look_at(camera, (0, 0, 5))
    bpy.context.scene.camera = camera

    scene = bpy.context.scene
    engines = {
        item.identifier
        for item in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items
    }
    scene.render.engine = (
        "BLENDER_EEVEE" if "BLENDER_EEVEE" in engines else "BLENDER_EEVEE_NEXT"
    )
    scene.render.resolution_x = 1200
    scene.render.resolution_y = 700
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(IMAGE_PATH)
    scene.world.use_nodes = True
    scene.world.node_tree.nodes["Background"].inputs["Color"].default_value = (
        0.12,
        0.09,
        0.07,
        1.0,
    )
    scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.72
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "None"
    scene.view_settings.exposure = 1.15
    bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    main()
