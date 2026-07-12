"""Render the complete robot-body calibration coupon plate."""

from __future__ import annotations

import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[2]
COUPON_DIR = ROOT / "cad" / "exports" / "coupons"
IMAGE_PATH = ROOT / "docs" / "images" / "codex_robot_body_v1_coupons.png"


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


def import_stl(name, mat, location):
    path = COUPON_DIR / f"{name}.stl"
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


def main():
    manifest = json.loads(
        (COUPON_DIR / "codex_robot_body_v1_coupon_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    expected = {
        "m3_insert_coupon",
        "m2_5_insert_coupon",
        "fastener_clearance_coupon",
        "bearing_608_seat_coupon",
        "pan_6807_bearing_fit_coupon",
        "wall_thickness_coupon",
        "lid_lap_coupon_front",
        "lid_lap_coupon_rear",
        "split_pilot_coupon_plate",
        "split_pilot_coupon_shell_front",
        "split_pilot_coupon_shell_rear",
        "bumper_interface_coupon_tray",
        "bumper_interface_coupon_plate",
        "bumper_interface_coupon_tpu",
        "fairing_recess_coupon_shell",
        "fairing_recess_coupon_skin",
        "power_distribution_fit_gauge",
    }
    missing = sorted(expected - set(manifest["coupons"]))
    if missing:
        raise RuntimeError(f"Coupon manifest missing parts: {missing}")

    clear_scene()
    mats = {
        "insert": material("insert", (0.05, 0.52, 0.64, 1.0)),
        "clearance": material("clearance", (0.10, 0.28, 0.78, 1.0)),
        "bearing": material("bearing", (0.94, 0.42, 0.06, 1.0)),
        "pan_bearing": material("pan_bearing", (0.70, 0.72, 0.76, 1.0), roughness=0.25, metallic=0.35),
        "wall": material("wall", (0.96, 0.82, 0.60, 1.0)),
        "lap": material("lap", (0.03, 0.36, 0.42, 1.0)),
        "pilot": material("pilot", (0.22, 0.72, 0.76, 1.0)),
        "pilot_shell": material("pilot_shell", (0.96, 0.82, 0.60, 1.0)),
        "bumper_tray": material("bumper_tray", (0.88, 0.82, 0.70, 1.0)),
        "bumper_plate": material("bumper_plate", (0.95, 0.28, 0.04, 1.0)),
        "bumper_tpu": material("bumper_tpu", (0.025, 0.03, 0.035, 1.0), roughness=0.55),
        "fairing_shell": material("fairing_shell", (0.96, 0.82, 0.60, 1.0)),
        "fairing_skin": material("fairing_skin", (0.98, 0.88, 0.68, 1.0)),
        "distribution": material("distribution", (0.96, 0.58, 0.04, 1.0)),
        "bed": material("bed", (0.035, 0.04, 0.05, 1.0), roughness=0.62, metallic=0.22),
    }

    for x, suffix in ((-160.0, "interfaces"), (160.0, "pan_bearing")):
        bpy.ops.mesh.primitive_cube_add(location=(x, 0, -2.0), scale=(145, 145, 2.0))
        bed = bpy.context.object
        bed.name = f"coupon_print_bed_{suffix}"
        bed.data.materials.append(mats["bed"])

    placements = {
        "m3_insert_coupon": ((0.0, -110.0, 0.1), mats["insert"]),
        "m2_5_insert_coupon": ((0.0, -82.0, 0.1), mats["insert"]),
        "fastener_clearance_coupon": ((0.0, -52.0, 0.1), mats["clearance"]),
        "bearing_608_seat_coupon": ((0.0, -12.0, 0.1), mats["bearing"]),
        "wall_thickness_coupon": ((0.0, 22.0, 0.1), mats["wall"]),
        "lid_lap_coupon_front": ((-18.0, 60.0, 0.1), mats["lap"]),
        "lid_lap_coupon_rear": ((18.0, 60.0, 0.1), mats["lap"]),
        "split_pilot_coupon_plate": ((-28.0, 98.0, 0.1), mats["pilot"]),
        "split_pilot_coupon_shell_front": ((4.0, 98.0, 0.1), mats["pilot_shell"]),
        "split_pilot_coupon_shell_rear": ((22.0, 98.0, 0.1), mats["pilot_shell"]),
        "bumper_interface_coupon_tray": ((68.0, 106.0, 0.1), mats["bumper_tray"]),
        "bumper_interface_coupon_plate": ((98.0, 106.0, 0.1), mats["bumper_plate"]),
        "bumper_interface_coupon_tpu": ((122.0, 106.0, 0.1), mats["bumper_tpu"]),
        "fairing_recess_coupon_shell": ((-118.0, 106.0, 0.1), mats["fairing_shell"]),
        "fairing_recess_coupon_skin": ((-84.0, 106.0, 0.1), mats["fairing_skin"]),
    }
    placements = {
        name: ((location[0] - 160.0, location[1], location[2]), mat)
        for name, (location, mat) in placements.items()
    }
    placements["pan_6807_bearing_fit_coupon"] = ((160.0, 0.0, 0.1), mats["pan_bearing"])
    placements["power_distribution_fit_gauge"] = ((160.0, 82.0, 0.1), mats["distribution"])
    for name, (location, mat) in placements.items():
        import_stl(name, mat, location)

    bpy.ops.object.light_add(type="AREA", location=(-80, -180, 430))
    key = bpy.context.object
    key.data.energy = 2100
    key.data.size = 300
    look_at(key, (0, 0, 10))

    bpy.ops.object.light_add(type="AREA", location=(170, 100, 280))
    fill = bpy.context.object
    fill.data.energy = 1200
    fill.data.size = 240
    look_at(fill, (0, 20, 10))

    bpy.ops.object.camera_add(location=(0, -660, 560))
    camera = bpy.context.object
    camera.data.lens = 52
    camera.data.sensor_width = 36
    camera.data.clip_end = 2000
    look_at(camera, (0, -2, 10))
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
    scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(IMAGE_PATH)
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
