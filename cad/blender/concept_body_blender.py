#!/usr/bin/env python3
"""Blender concept pass for the Codex Rover Bean body.

Run from the repo root with:

    /Applications/Blender.app/Contents/MacOS/Blender --background --python cad/blender/concept_body_blender.py

This file is intentionally an industrial-design and packaging model, not a
manufacturing export.  It keeps the current MVP body envelope and serviceable
part language visible while chasing the finished concept art more closely than the first
OpenSCAD and CadQuery preview passes.
"""

from __future__ import annotations

import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs" / "images"


COLORS = {
    # Calibrated against the finished concept art (sampled + delit): the cream is
    # a warm off-white, not a saturated tan, and the teal is a brighter medium
    # teal that reads ~(0.31,0.62,0.64) in direct light.
    "cream": (0.91, 0.82, 0.67, 1.0),
    "cream_light": (0.95, 0.87, 0.71, 1.0),
    "cream_shadow": (0.58, 0.50, 0.40, 1.0),
    "teal": (0.11, 0.50, 0.53, 1.0),
    "teal_dark": (0.04, 0.25, 0.27, 1.0),
    "charcoal": (0.028, 0.030, 0.033, 1.0),
    "panel_black": (0.016, 0.018, 0.020, 1.0),
    "black": (0.0, 0.0, 0.0, 1.0),
    "rubber": (0.105, 0.100, 0.092, 1.0),
    "rubber_tread": (0.090, 0.086, 0.078, 1.0),
    "lime": (0.76, 0.97, 0.34, 1.0),
    "blue": (0.05, 0.27, 0.82, 1.0),
    "red": (0.86, 0.08, 0.04, 1.0),
    "keepout": (0.30, 0.52, 1.0, 0.28),
    "safety_teal": (0.00, 0.72, 0.78, 0.22),
    "safety_red": (1.0, 0.16, 0.08, 0.24),
    "floor": (0.68, 0.52, 0.36, 1.0),
    # Representative internal-component materials (shown in exploded/service).
    "pcb": (0.05, 0.22, 0.10, 1.0),
    "pcb_blue": (0.07, 0.12, 0.30, 1.0),
    "metal": (0.42, 0.43, 0.46, 1.0),
    "metal_dark": (0.20, 0.21, 0.23, 1.0),
    "battery_body": (0.12, 0.14, 0.19, 1.0),
    "copper": (0.72, 0.45, 0.20, 1.0),
    "silver": (0.62, 0.63, 0.66, 1.0),
}


ITERATION_LABELS = [
    "01 blockout",
    "02 wider teal deck",
    "03 softer shell",
    "04 bumper wrap",
    "05 wheel fenders",
    "06 lower stance",
    "07 capsule head",
    "08 friendlier face",
    "09 real E-stop",
    "10 service details",
    "11 package fit",
    "12 matched pass",
]


REFINEMENT_LABELS = [
    "13 darker inset deck",
    "14 lower cream shell",
    "15 shaped hood inset",
    "16 recessed fascia",
    "17 bumper halo",
    "18 lower E-stop",
    "19 softer head bezel",
    "20 smaller eyes",
    "21 curved brows",
    "22 slimmer neck",
    "23 fender wrap",
    "24 refined match",
]


MAT_CACHE: dict[tuple[str, float], bpy.types.Material] = {}


def material(name: str, rgba: tuple[float, float, float, float], roughness: float = 0.62) -> bpy.types.Material:
    key = (name, rgba[3])
    if key in MAT_CACHE:
        return MAT_CACHE[key]

    mat = bpy.data.materials.new(name)
    mat.diffuse_color = rgba
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        if "Base Color" in bsdf.inputs:
            bsdf.inputs["Base Color"].default_value = rgba
        if "Alpha" in bsdf.inputs:
            bsdf.inputs["Alpha"].default_value = rgba[3]
        if "Roughness" in bsdf.inputs:
            bsdf.inputs["Roughness"].default_value = roughness
        if "Metallic" in bsdf.inputs:
            bsdf.inputs["Metallic"].default_value = 0.0
        if name.startswith("lime") and "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = rgba
        if name.startswith("lime") and "Emission Strength" in bsdf.inputs:
            bsdf.inputs["Emission Strength"].default_value = 0.55
    if rgba[3] < 1.0:
        mat.blend_method = "BLEND"
        mat.use_screen_refraction = True
        mat.show_transparent_back = True
    MAT_CACHE[key] = mat
    return mat


def mat(name: str, alpha: float | None = None) -> bpy.types.Material:
    rgba = COLORS[name]
    if alpha is not None:
        rgba = (rgba[0], rgba[1], rgba[2], alpha)
    return material(name if alpha is None else f"{name}_{alpha:.2f}", rgba)


def clean_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    for block in (bpy.data.meshes, bpy.data.curves, bpy.data.cameras, bpy.data.lights):
        for item in list(block):
            if item.users == 0:
                block.remove(item)

    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 0.001
    try:
        scene.unit_settings.length_unit = "MILLIMETERS"
    except TypeError:
        pass


def shade_smooth(obj: bpy.types.Object) -> None:
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.shade_smooth()
    obj.select_set(False)


def add_bevel(obj: bpy.types.Object, width: float, segments: int = 10) -> None:
    if width <= 0:
        return
    bevel = obj.modifiers.new("soft printable bevel", "BEVEL")
    bevel.width = width
    bevel.segments = segments
    bevel.profile = 0.5
    try:
        bevel.affect = "EDGES"
    except Exception:
        pass
    obj.modifiers.new("weighted normals", "WEIGHTED_NORMAL")


def rounded_box(
    name: str,
    loc: tuple[float, float, float],
    dims: tuple[float, float, float],
    material_obj: bpy.types.Material,
    bevel: float,
    segments: int = 12,
    rotation: tuple[float, float, float] = (0, 0, 0),
) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dims
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(material_obj)
    add_bevel(obj, bevel, segments)
    shade_smooth(obj)
    return obj


def cylinder(
    name: str,
    loc: tuple[float, float, float],
    radius: float,
    depth: float,
    material_obj: bpy.types.Material,
    vertices: int = 72,
    rotation: tuple[float, float, float] = (0, 0, 0),
    bevel: float = 0.0,
) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=loc, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material_obj)
    if bevel:
        add_bevel(obj, bevel, 5)
    shade_smooth(obj)
    return obj


def torus(
    name: str,
    loc: tuple[float, float, float],
    major_radius: float,
    minor_radius: float,
    material_obj: bpy.types.Material,
) -> bpy.types.Object:
    bpy.ops.mesh.primitive_torus_add(
        major_segments=96,
        minor_segments=16,
        major_radius=major_radius,
        minor_radius=minor_radius,
        location=loc,
    )
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material_obj)
    shade_smooth(obj)
    return obj


def curve_tube(
    name: str,
    points: list[tuple[float, float, float]],
    material_obj: bpy.types.Material,
    radius: float,
    resolution: int = 4,
    cyclic: bool = False,
) -> bpy.types.Object:
    curve = bpy.data.curves.new(name, "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = resolution
    curve.bevel_depth = radius
    curve.bevel_resolution = 5
    curve.use_fill_caps = True
    spline = curve.splines.new("BEZIER")
    spline.bezier_points.add(len(points) - 1)
    spline.use_cyclic_u = cyclic
    for point, co in zip(spline.bezier_points, points):
        point.co = co
        point.handle_left_type = "AUTO"
        point.handle_right_type = "AUTO"
    obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(material_obj)
    return obj


def superellipse_shell(
    name: str,
    loc: tuple[float, float, float],
    rings: list[tuple[float, float, float]],
    material_obj: bpy.types.Material,
    exponent: float = 3.8,
    points: int = 96,
) -> bpy.types.Object:
    verts: list[tuple[float, float, float]] = []
    for z, half_x, half_y in rings:
        for index in range(points):
            angle = 2 * math.pi * index / points
            ca = math.cos(angle)
            sa = math.sin(angle)
            x = half_x * math.copysign(abs(ca) ** (2 / exponent), ca)
            y = half_y * math.copysign(abs(sa) ** (2 / exponent), sa)
            verts.append((loc[0] + x, loc[1] + y, loc[2] + z))

    # Cap centroids so the top/bottom close as clean triangle fans instead of a
    # single many-sided n-gon (an n-gon cap fan-triangulates from one vertex and,
    # once smooth-shaded against the sloped sides, smears a dark triangle across
    # the surface).  Flat-shading the caps keeps them reading as crisp panels.
    top_center = len(verts)
    verts.append((loc[0], loc[1], loc[2] + rings[-1][0]))
    bottom_center = len(verts)
    verts.append((loc[0], loc[1], loc[2] + rings[0][0]))

    faces: list[tuple[int, ...]] = []
    for ring in range(len(rings) - 1):
        start = ring * points
        next_start = (ring + 1) * points
        for index in range(points):
            faces.append(
                (
                    start + index,
                    start + (index + 1) % points,
                    next_start + (index + 1) % points,
                    next_start + index,
                )
            )
    side_face_count = len(faces)
    for index in range(points):  # bottom cap fan (normal points down)
        faces.append((bottom_center, (index + 1) % points, index))
    top_start = (len(rings) - 1) * points
    for index in range(points):  # top cap fan (normal points up)
        faces.append((top_center, top_start + index, top_start + (index + 1) % points))

    mesh = bpy.data.meshes.new(f"{name}_mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(material_obj)
    obj.modifiers.new("shell weighted normals", "WEIGHTED_NORMAL")
    shade_smooth(obj)
    for poly in obj.data.polygons[side_face_count:]:
        poly.use_smooth = False
    return obj


def capsule_outline(
    y_half: float,
    z_center: float,
    z_half: float,
    points: int,
) -> list[tuple[float, float]]:
    """Return y/z points around a horizontal pill outline."""
    straight_half = max(0.0, y_half - z_half)
    outline: list[tuple[float, float]] = []
    for index in range(points):
        angle = 2 * math.pi * index / points
        ca = math.cos(angle)
        sa = math.sin(angle)
        y = straight_half * math.copysign(1.0, ca) + z_half * ca
        outline.append((y, z_center + z_half * sa))
    return outline


def _superellipse_front_x(y: float, half_x: float, half_y: float, exponent: float) -> float:
    """Front (-X) surface x of a superellipse ring at lateral position y."""
    ratio = abs(y) / half_y
    if ratio >= 1.0:
        return 0.0
    return half_x * (1.0 - ratio ** exponent) ** (1.0 / exponent)


# Molded cream body shell profile (shared by the shell build and the boolean
# cutters that carve recessed front windows into it, so the cutters follow the
# exact same curved surface).
BODY_RINGS = [(16, 122, 88), (28, 139, 101), (50, 144, 105), (68, 139, 101), (76, 126, 91)]
BODY_SHELL_EXP = 3.75


def body_ring_params(z: float) -> tuple[float, float]:
    """Interpolate (half_x, half_y) of the body shell superellipse at height z."""
    if z <= BODY_RINGS[0][0]:
        return BODY_RINGS[0][1], BODY_RINGS[0][2]
    if z >= BODY_RINGS[-1][0]:
        return BODY_RINGS[-1][1], BODY_RINGS[-1][2]
    for i in range(len(BODY_RINGS) - 1):
        z0, hx0, hy0 = BODY_RINGS[i]
        z1, hx1, hy1 = BODY_RINGS[i + 1]
        if z0 <= z <= z1:
            t = (z - z0) / (z1 - z0)
            return hx0 + (hx1 - hx0) * t, hy0 + (hy1 - hy0) * t
    return BODY_RINGS[-1][1], BODY_RINGS[-1][2]


def body_front_x(y: float, z: float) -> float:
    """Magnitude of the front (-X) body shell surface x at lateral y, height z."""
    hx, hy = body_ring_params(z)
    return _superellipse_front_x(y, hx, hy, BODY_SHELL_EXP)


def front_recess_cutter(
    name: str,
    loc: tuple[float, float, float],
    outline_yz: list[tuple[float, float]],
    back_off: float,
    front_off: float,
) -> bpy.types.Object:
    """Rounded-rectangle 'tunnel' whose back face sits back_off inside the front
    shell surface and whose front face is front_off proud — used as a BOOLEAN
    DIFFERENCE cutter to carve a clean recessed window into the smooth front."""
    n = len(outline_yz)
    verts: list[tuple[float, float, float]] = []
    for y, z in outline_yz:  # front loop (well proud, outside the shell)
        sx = body_front_x(y, z)
        verts.append((loc[0] - sx - front_off, loc[1] + y, loc[2] + z))
    for y, z in outline_yz:  # back loop (recess floor, inside the shell)
        sx = body_front_x(y, z)
        verts.append((loc[0] - sx + back_off, loc[1] + y, loc[2] + z))
    faces: list[tuple[int, ...]] = []
    for i in range(n):
        j = (i + 1) % n
        faces.append((i, j, n + j, n + i))
    faces.append(tuple(range(n - 1, -1, -1)))  # front cap
    faces.append(tuple(range(n, 2 * n)))  # back cap
    mesh = bpy.data.meshes.new(f"{name}_mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return obj


def front_recess_liner(
    name: str,
    loc: tuple[float, float, float],
    outline_yz: list[tuple[float, float]],
    floor_off: float,
    rim_off: float = 0.0,
    material_obj: bpy.types.Material | None = None,
) -> bpy.types.Object:
    """Open-front dark 'cup' that lines a carved recess: walls run from the front
    rim (at the cream surface) back to a floor cap, so the recess interior reads
    solid dark with no lit cream sill. The floor cap is the recessed sensor face."""
    n = len(outline_yz)
    verts: list[tuple[float, float, float]] = []
    for y, z in outline_yz:  # rim loop (at/near the cream surface)
        sx = body_front_x(y, z)
        verts.append((loc[0] - sx + rim_off, loc[1] + y, loc[2] + z))
    for y, z in outline_yz:  # floor loop (recessed)
        sx = body_front_x(y, z)
        verts.append((loc[0] - sx + floor_off, loc[1] + y, loc[2] + z))
    faces: list[tuple[int, ...]] = []
    for i in range(n):
        j = (i + 1) % n
        faces.append((i, n + i, n + j, j))  # wall
    faces.append(tuple(range(2 * n - 1, n - 1, -1)))  # floor cap facing -X
    mesh = bpy.data.meshes.new(f"{name}_mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    if material_obj is not None:
        obj.data.materials.append(material_obj)
    return obj


def box_cutter(loc: tuple[float, float, float], dims: tuple[float, float, float]) -> bpy.types.Object:
    """A plain box used as a boolean-difference cutter."""
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    obj = bpy.context.object
    obj.name = "box cutter"
    obj.dimensions = dims
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return obj


def boolean_carve(target: bpy.types.Object, cutter: bpy.types.Object) -> None:
    """Difference `cutter` out of `target`, then restore clean smooth shading."""
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = target
    target.select_set(True)
    if target.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    for m in list(target.modifiers):
        bpy.ops.object.modifier_apply(modifier=m.name)
    boolean = target.modifiers.new("front recess cut", "BOOLEAN")
    boolean.operation = "DIFFERENCE"
    boolean.object = cutter
    boolean.solver = "EXACT"
    bpy.ops.object.modifier_apply(modifier="front recess cut")
    bpy.data.objects.remove(cutter, do_unlink=True)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode="OBJECT")
    target.modifiers.new("recut weighted normals", "WEIGHTED_NORMAL")
    shade_smooth(target)
    target.select_set(False)


def x_capsule_shell(
    name: str,
    loc: tuple[float, float, float],
    slices: list[tuple[float, float, float]],
    material_obj: bpy.types.Material,
    exponent: float = 3.0,
    points: int = 80,
) -> bpy.types.Object:
    verts: list[tuple[float, float, float]] = []
    for x, half_y, half_z in slices:
        for index in range(points):
            angle = 2 * math.pi * index / points
            ca = math.cos(angle)
            sa = math.sin(angle)
            y = half_y * math.copysign(abs(ca) ** (2 / exponent), ca)
            z = half_z * math.copysign(abs(sa) ** (2 / exponent), sa)
            verts.append((loc[0] + x, loc[1] + y, loc[2] + z))

    # Cap centroids -> clean triangle fans + flat-shaded caps (see superellipse_shell).
    front_center = len(verts)
    verts.append((loc[0] + slices[0][0], loc[1], loc[2]))
    back_center = len(verts)
    verts.append((loc[0] + slices[-1][0], loc[1], loc[2]))

    faces: list[tuple[int, ...]] = []
    for ring in range(len(slices) - 1):
        start = ring * points
        next_start = (ring + 1) * points
        for index in range(points):
            faces.append(
                (
                    start + index,
                    next_start + index,
                    next_start + (index + 1) % points,
                    start + (index + 1) % points,
                )
            )
    side_face_count = len(faces)
    for index in range(points):  # front cap fan (normal -X)
        faces.append((front_center, (index + 1) % points, index))
    back_start = (len(slices) - 1) * points
    for index in range(points):  # back cap fan (normal +X)
        faces.append((back_center, back_start + index, back_start + (index + 1) % points))

    mesh = bpy.data.meshes.new(f"{name}_mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(material_obj)
    obj.modifiers.new("capsule weighted normals", "WEIGHTED_NORMAL")
    shade_smooth(obj)
    for poly in obj.data.polygons[side_face_count:]:
        poly.use_smooth = False
    return obj


def lerp(start: float, end: float, t: float) -> float:
    return start + (end - start) * t


def variant(progress: float, refinement: float = 0.0) -> dict[str, float]:
    matched = {
        "body_bevel": lerp(15, 30, progress),
        "body_h": lerp(62, 68, progress),
        "deck_len": lerp(198, 232, progress),
        "deck_w": lerp(126, 152, progress),
        "deck_bevel": lerp(9, 20, progress),
        "bumper_bevel": lerp(7, 15, progress),
        "bumper_depth": lerp(18, 30, progress),
        "fender_cover": lerp(108, 156, progress),
        "wheel_x": lerp(52, 70, progress),
        "wheel_y": lerp(123, 123, progress),
        "head_w": lerp(90, 118, progress),
        "head_d": lerp(50, 70, progress),
        "head_h": lerp(48, 58, progress),
        "head_bevel": lerp(10, 24, progress),
        "face_w": lerp(70, 88, progress),
        "face_h": lerp(32, 40, progress),
        "neck_h": lerp(44, 50, progress),
        "top_black_len": lerp(62, 60, progress),
        "side_panel_len": lerp(54, 82, progress),
        "estop_scale": lerp(0.72, 1.0, progress),
    }

    if refinement <= 0:
        return matched

    return {
        **matched,
        "body_bevel": lerp(matched["body_bevel"], 36, refinement),
        "body_h": lerp(matched["body_h"], 62, refinement),
        "deck_len": lerp(matched["deck_len"], 194, refinement),
        "deck_w": lerp(matched["deck_w"], 134, refinement),
        "deck_bevel": lerp(matched["deck_bevel"], 18, refinement),
        "bumper_depth": lerp(matched["bumper_depth"], 24, refinement),
        "fender_cover": lerp(matched["fender_cover"], 176, refinement),
        "wheel_x": lerp(matched["wheel_x"], 55, refinement),
        "wheel_y": lerp(matched["wheel_y"], 105, refinement),
        "head_w": lerp(matched["head_w"], 106, refinement),
        "head_d": lerp(matched["head_d"], 54, refinement),
        "head_h": lerp(matched["head_h"], 52, refinement),
        "head_bevel": lerp(matched["head_bevel"], 27, refinement),
        "face_w": lerp(matched["face_w"], 89, refinement),
        "face_h": lerp(matched["face_h"], 36, refinement),
        "neck_h": lerp(matched["neck_h"], 42, refinement),
        "top_black_len": lerp(matched["top_black_len"], 64, refinement),
        "side_panel_len": lerp(matched["side_panel_len"], 74, refinement),
        "estop_scale": lerp(matched["estop_scale"], 0.82, refinement),
    }


def make_fender(side: int, v: dict[str, float], z_offset: float = 0.0) -> bpy.types.Object:
    # Slim cream arch that caps just the top of the (larger) exposed wheel, like
    # a car fender fairing — the tire and hub read clearly below it.
    arch = side_arch_band(
        f"cream integrated wheel arch fairing {'right' if side > 0 else 'left'}",
        center_x=v["wheel_x"] - 1,
        y_center=side * 105.0,
        center_z=42 + z_offset,
        outer_radius_x=46,
        outer_radius_z=45,
        band_width=6.5,
        depth=21,
        side=side,
        material_obj=mat("cream_light"),
        start_deg=12,
        end_deg=168,
        points=52,
        bevel=1.8,
    )
    return arch


def add_tire_tread_marks(
    side: int,
    wheel_loc: tuple[float, float, float],
    tire_radius: float,
    tire_w: float,
) -> None:
    # Chunky tread lugs on the rolling (circumferential) surface, spanning the
    # tire width, with a slight herringbone tilt like a real tire.
    n = 34
    lug_w = tire_w * 0.82
    for index in range(n):
        theta = 2 * math.pi * index / n
        x = wheel_loc[0] + tire_radius * math.cos(theta)
        z = wheel_loc[2] + tire_radius * math.sin(theta)
        tilt = 0.32 if index % 2 == 0 else -0.32
        rounded_box(
            "tire tread lug",
            (x, wheel_loc[1], z),
            (4.0, lug_w, 4.6),
            mat("rubber_tread"),
            0.5,
            3,
            rotation=(tilt, -theta, 0),
        )


def side_arch_band(
    name: str,
    center_x: float,
    y_center: float,
    center_z: float,
    outer_radius_x: float,
    outer_radius_z: float,
    band_width: float,
    depth: float,
    side: int,
    material_obj: bpy.types.Material,
    start_deg: float = 26,
    end_deg: float = 154,
    points: int = 28,
    bevel: float = 1.2,
) -> bpy.types.Object:
    """Build a flattened U-shaped side fender band over a wheel."""
    y_outer = y_center + side * depth / 2
    y_inner = y_center - side * depth / 2
    inner_radius_x = outer_radius_x - band_width
    inner_radius_z = outer_radius_z - band_width

    verts: list[tuple[float, float, float]] = []
    for index in range(points):
        t = index / (points - 1)
        theta = math.radians(start_deg + (end_deg - start_deg) * t)
        outer_x = center_x + outer_radius_x * math.cos(theta)
        outer_z = center_z + outer_radius_z * math.sin(theta)
        inner_x = center_x + inner_radius_x * math.cos(theta)
        inner_z = center_z + inner_radius_z * math.sin(theta)
        verts.extend(
            [
                (outer_x, y_outer, outer_z),
                (inner_x, y_outer, inner_z),
                (outer_x, y_inner, outer_z),
                (inner_x, y_inner, inner_z),
            ]
        )

    faces: list[tuple[int, ...]] = []
    for index in range(points - 1):
        a = index * 4
        b = (index + 1) * 4
        faces.extend(
            [
                (a, b, b + 2, a + 2),
                (a + 1, a + 3, b + 3, b + 1),
                (a, a + 1, b + 1, b),
                (a + 2, b + 2, b + 3, a + 3),
            ]
        )
    faces.append((0, 2, 3, 1))
    last = (points - 1) * 4
    faces.append((last, last + 1, last + 3, last + 2))

    mesh = bpy.data.meshes.new(f"{name}_mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(material_obj)
    add_bevel(obj, bevel, 6)
    shade_smooth(obj)
    return obj


def add_floor() -> None:
    rounded_box("warm floor shadow card", (10, 0, -5), (520, 380, 4), mat("floor"), 0)


def build_robot(progress: float = 1.0, mode: str = "assembled", refinement: float = 1.0) -> None:
    v = variant(progress, refinement)
    exploded = mode == "exploded"
    service = mode == "service"
    safety = mode == "safety"

    offsets = {
        "tray": (0, 0, -38 if exploded else 0),
        "body": (0, 0, 118 if exploded else 0),
        "deck": (-1 if exploded else 0, 0, 208 if exploded else 74 if service else 0),
        "head": (0, 0, 292 if exploded else 126 if service else 0),
        "bumper": (-46 if exploded else 0, 0, 118 if exploded else 0),
        "wheel": (0, 0, -20 if exploded else 0),
        # Internal component layers, revealed between the dropped tray and the
        # lifted body shell in the exploded view (hidden inside in assembled).
        "chassis": (0, 0, -24 if exploded else 0),
        "electronics": (0, 0, 24 if exploded else 12 if service else 0),
    }

    def off(group: str, loc: tuple[float, float, float]) -> tuple[float, float, float]:
        dx, dy, dz = offsets[group]
        return (loc[0] + dx, loc[1] + dy, loc[2] + dz)

    add_floor()

    # Lower tray and cream appliance shell.
    rounded_box("lower cream tray", off("tray", (0, 0, 18)), (276, 190, 18), mat("cream_shadow"), 14, 12)
    for x, y, radius, height in [
        (-112, -70, 5.0, 21),
        (-112, 70, 5.0, 21),
        (-30, -72, 4.5, 18),
        (-30, 72, 4.5, 18),
        (48, -64, 4.5, 19),
        (48, 64, 4.5, 19),
        (108, -56, 4.2, 18),
        (108, 56, 4.2, 18),
    ]:
        cylinder("lower tray service standoff", off("tray", (x, y, 31 + height / 2)), radius, height, mat("cream_light"), 36, bevel=0.6)
        cylinder("standoff screw bore marker", off("tray", (x, y, 31 + height + 0.8)), radius * 0.34, 1.6, mat("charcoal"), 24, bevel=0.2)
    body_shell = superellipse_shell(
        "molded cream body shell",
        off("body", (0, 0, 0)),
        BODY_RINGS,
        mat("cream_light"),
        exponent=BODY_SHELL_EXP,
        points=112,
    )
    # Top service opening under the removable teal deck: the deck is a real
    # service hatch, so lifting it (service view) exposes the electronics bay.
    # The deck fully overhangs this opening, so it stays hidden when assembled.
    boolean_carve(body_shell, box_cutter(off("body", (4, 0, 86)), (172, 108, 46)))
    rounded_box("subtle horizontal shell seam", off("body", (-14, -106, 52)), (218, 1.0, 1.8), mat("cream_shadow"), 0.25, 2)

    # Flush removable service deck and front black hood insert.
    deck_z = 78.0
    deck_len = v["deck_len"] + 4
    deck_w = v["deck_w"] - 2
    superellipse_shell(
        "fixed shell service deck landing ledge",
        off("body", (4, 0, 0)),
        [
            (deck_z - 4.9, deck_len / 2 + 4.5, deck_w / 2 + 4.5),
            (deck_z - 4.2, deck_len / 2 + 5.0, deck_w / 2 + 5.0),
            (deck_z - 3.7, deck_len / 2 + 3.8, deck_w / 2 + 3.8),
        ],
        mat("cream_shadow"),
        exponent=3.95,
        points=128,
    )
    superellipse_shell(
        "dark recessed service bay opening shadow",
        off("body", (4, 0, 0)),
        [
            (deck_z - 3.6, deck_len / 2 - 11.0, deck_w / 2 - 11.0),
            (deck_z - 3.0, deck_len / 2 - 10.4, deck_w / 2 - 10.4),
        ],
        mat("charcoal"),
        exponent=3.75,
        points=128,
    )
    superellipse_shell(
        "thin dark deck reveal gasket",
        off("deck", (4, 0, 0)),
        [
            (deck_z - 1.1, deck_len / 2 + 0.4, deck_w / 2 + 0.4),
            (deck_z - 0.5, deck_len / 2 + 0.9, deck_w / 2 + 0.9),
            (deck_z + 0.0, deck_len / 2 + 0.4, deck_w / 2 + 0.4),
        ],
        mat("charcoal"),
        exponent=3.85,
        points=128,
    )
    superellipse_shell(
        "teal removable top service deck",
        off("deck", (3, 0, 0)),
        [
            (deck_z - 1.2, deck_len / 2 - 0.6, deck_w / 2 - 0.6),
            (deck_z - 0.2, deck_len / 2 + 0.4, deck_w / 2 + 0.4),
            (deck_z + 0.35, deck_len / 2, deck_w / 2),
        ],
        mat("teal"),
        exponent=3.75,
        points=128,
    )
    # (The wide black hood trim band + vent louvers are built in the front
    # fascia section below, where the shared front-curve helpers are defined.)
    # Dense vent comb between the neck and E-stop: many thin slots running
    # across the deck (long in Y), arrayed front-to-back, near-flush.
    for x in range(-14, 47, 4):
        rounded_box("deck vent slot", off("deck", (x, 0, deck_z + 0.7)), (2.0, 22.0, 1.4), mat("charcoal"), 0.4, 3)
    for x, y in [(-93, -57), (-93, 57), (86, -57), (86, 57)]:
        cylinder("black deck screw", off("deck", (x, y, deck_z + 3)), 1.55, 1.2, mat("charcoal"), 28, bevel=0.2)
    for x, y in [(-93, -57), (-93, 57), (86, -57), (86, 57), (-10, -58), (-10, 58)]:
        cylinder("deck underside alignment peg", off("deck", (x, y, deck_z - 8)), 2.2, 12, mat("teal_dark"), 28, bevel=0.25)

    # Smooth rounded cream front: this is just the molded body shell now (the old
    # protruding nose pieces are gone). The black LED sensor bar sits in a
    # RECESSED cutout BOOLEAN-carved into the smooth surface, following the
    # shell's own superellipse so the opening hugs the curved front.
    bloc = off("body", (0, 0, 0))
    sensor_z = 45.0
    cam_glass = material("cam_glass2", (0.02, 0.03, 0.05, 1.0))
    # Capsule window carved into the smooth front, then a dark open-front cup
    # lines the whole interior (walls + floor) so it reads solid black behind a
    # thin cream bezel — no lit cream sill. The cup floor is the sensor face.
    # Tall enough to fully contain the lime lights + cameras as one dark bar.
    sensor_outline = capsule_outline(76.0, sensor_z, 12.5, 176)
    boolean_carve(body_shell, front_recess_cutter("sensor window cutter", bloc, sensor_outline, back_off=4.5, front_off=40.0))
    liner_outline = capsule_outline(75.4, sensor_z, 12.0, 176)
    front_recess_liner("recessed black sensor bar", bloc, liner_outline, floor_off=4.5, rim_off=-0.2, material_obj=mat("panel_black"))
    # Lime end lights.
    for y in (-62, 62):
        sx = body_front_x(y, sensor_z)
        rounded_box(
            "front lime light",
            (bloc[0] - sx + 1.4, bloc[1] + y, bloc[2] + sensor_z),
            (2.2, 6.6, 14.0),
            mat("lime"),
            2.0,
            10,
        )
    # Prominent stereo camera pair, clustered left-of-center, raised glossy lenses.
    for y in (-16, -3):
        sx = body_front_x(y, sensor_z)
        cylinder("front camera lens barrel", (bloc[0] - sx + 3.0, bloc[1] + y, bloc[2] + sensor_z), 6.0, 3.0, mat("charcoal"), 44, rotation=(0, math.pi / 2, 0), bevel=0.6)
        cylinder("front camera glass", (bloc[0] - sx + 1.6, bloc[1] + y, bloc[2] + sensor_z), 4.2, 1.4, cam_glass, 44, rotation=(0, math.pi / 2, 0), bevel=0.35)
    # Separate round sensor, right-of-center.
    ssx = body_front_x(24, sensor_z)
    cylinder("front round sensor barrel", (bloc[0] - ssx + 2.8, bloc[1] + 24, bloc[2] + sensor_z), 6.8, 2.6, mat("charcoal"), 44, rotation=(0, math.pi / 2, 0), bevel=0.6)
    cylinder("front round sensor glass", (bloc[0] - ssx + 1.6, bloc[1] + 24, bloc[2] + sensor_z), 4.4, 1.2, cam_glass, 44, rotation=(0, math.pi / 2, 0), bevel=0.35)

    # Wide black hood-trim vent above the sensor bar: a broad, shallow recessed
    # panel spanning most of the front, with the louver slots clustered in the
    # center (lighter ribs standing between dark slots).
    vent_z = 67.0
    vent_outline = capsule_outline(80.0, vent_z, 6.0, 176)
    boolean_carve(body_shell, front_recess_cutter("vent window cutter", bloc, vent_outline, back_off=2.5, front_off=40.0))
    front_recess_liner(
        "recessed vent panel",
        bloc,
        capsule_outline(79.4, vent_z, 5.6, 176),
        floor_off=2.5,
        rim_off=-0.2,
        material_obj=mat("panel_black"),
    )
    for y in (-21, -14, -7, 0, 7, 14, 21):
        sx = body_front_x(y, vent_z)
        rounded_box(
            "front vent louver rib",
            (bloc[0] - sx + 1.3, bloc[1] + y, bloc[2] + vent_z),
            (1.4, 1.5, 8.2),
            material("vent_rib", (0.17, 0.17, 0.18, 1.0)),
            0.3,
            3,
        )

    # Simple smooth curved black bumper across the FRONT BOTTOM only (no side
    # wrap). One clean rounded TPU bar following the front arc from corner to
    # corner, hanging low near the floor.
    bumper_z = 19.0
    bump_a, bump_b, bump_n = 148.0, 113.0, 3.4

    def bumper_point(deg: float, z: float = bumper_z) -> tuple[float, float, float]:
        t = math.radians(deg)
        ca, sa = math.cos(t), math.sin(t)
        x = bump_a * math.copysign(abs(ca) ** (2 / bump_n), ca)
        y = bump_b * math.copysign(abs(sa) ** (2 / bump_n), sa)
        return (x, y, z)

    # deg 114..246 keeps the bar on the front face only (never reaches the sides).
    bumper_path = [off("bumper", bumper_point(deg)) for deg in range(114, 247, 5)]
    curve_tube("simple front bumper", bumper_path, mat("rubber"), 12.0, 8)

    # Wheels, hubs, cream fenders, and side service panels.
    for side in (-1, 1):
        wheel_y = side * v["wheel_y"]
        if exploded:
            wheel_y += side * 28
        wheel_loc = off("wheel", (v["wheel_x"], wheel_y, 42))
        tire_radius = 37.0
        tire_w = 20.0
        cylinder("black rubber tire", wheel_loc, tire_radius, tire_w, mat("rubber"), 96, rotation=(math.pi / 2, 0, 0), bevel=1.0)
        outside_y = wheel_loc[1] + side * (tire_w / 2 + 0.6)
        # Concentric face rings sized to leave a substantial black tread band:
        # black tread rim -> cream sidewall -> teal -> hub.
        cylinder("cream tire sidewall ring", (wheel_loc[0], outside_y, wheel_loc[2]), 28.0, 2.4, mat("cream_light"), 84, rotation=(math.pi / 2, 0, 0), bevel=0.5)
        cylinder("teal wheel accent ring", (wheel_loc[0], outside_y + side * 1.0, wheel_loc[2]), 23.5, 2.6, mat("teal"), 84, rotation=(math.pi / 2, 0, 0), bevel=0.5)
        cylinder("cream wheel hub", (wheel_loc[0], outside_y + side * 2.1, wheel_loc[2]), 17.0, 3.2, mat("cream_light"), 84, rotation=(math.pi / 2, 0, 0), bevel=0.6)
        add_tire_tread_marks(side, wheel_loc, tire_radius, tire_w)
        make_fender(side, v, offsets["body"][2])
        # Clean flat teal side service panel recessed flush into the cream, with
        # a row of screws set into the teal (no heavy gray frame).
        panel_len = v["side_panel_len"] + 30
        rounded_box("side service panel recessed pocket", off("body", (8, side * 101.4, 46)), (panel_len + 6, 2.4, 28), mat("cream_shadow"), 3, 6)
        rounded_box("teal side service panel", off("body", (8, side * 102.6, 46)), (panel_len, 2.2, 24), mat("teal"), 2.5, 8)
        for x in (-46, -18, 10, 38, 66):
            cylinder("side panel screw", off("body", (x, side * 103.9, 46)), 1.25, 1.2, mat("charcoal"), 24, rotation=(math.pi / 2, 0, 0), bevel=0.2)

    # Mechanical service bay bosses/rails that carry the electronics deck and
    # battery cradle. The representative components they hold are built below.
    rounded_box("lower service bay pocket", off("tray", (62, 0, 40)), (142, 66, 6), mat("cream_shadow"), 4, 6)
    for x in (-4, 128):
        rounded_box("service bay end stop", off("tray", (x, 0, 51)), (8, 66, 24), mat("cream_light"), 3, 5)
    for y in (-34, 34):
        rounded_box("service bay alignment rail", off("tray", (62, y, 52)), (142, 5, 22), mat("cream_light"), 2, 4)
    for x, y in [(-108, -68), (-108, 68), (-16, -68), (-16, 68), (34, -48), (34, -16)]:
        cylinder("deck support standoff post", off("tray", (x, y, 51)), 3.4, 24, mat("cream_light"), 28, bevel=0.4)
    for x, y in [(-108, -68), (-108, 68), (-16, -68), (-16, 68), (34, -48), (34, -16), (62, -22), (62, 22)]:
        cylinder("service bay screw bore marker", off("tray", (x, y, 64)), 1.15, 2.0, mat("charcoal"), 20, bevel=0.15)

    # ------------------------------------------------------------------------
    # Representative internal components (sized to docs/bom-v0.md and the
    # cad-mechanical-plan parameter contract), revealed in the exploded/service
    # views so the body demonstrably houses the real build. Hidden inside the
    # closed shell in the assembled (concept-match) view.
    # ------------------------------------------------------------------------
    if exploded or service:
        # --- Low chassis layer: battery, drive motors, caster ---
        # 12V LiFePO4 pack (~110x38x38) low and rearward of the wheel axle.
        rounded_box("battery pack 12V LiFePO4", off("chassis", (94, 0, 33)), (40, 110, 38), mat("battery_body"), 3, 6)
        for sy in (-30, 30):
            rounded_box("battery strap", off("chassis", (94, sy, 33)), (44, 8, 42), mat("charcoal"), 1.5, 4)
        for ty in (-18, 18):
            cylinder("battery terminal", off("chassis", (74, ty, 50)), 2.6, 6, mat("copper"), 20, rotation=(0, math.pi / 2, 0), bevel=0.3)
        for side in (-1, 1):
            cylinder("drive gearmotor", off("chassis", (55, side * 66, 42)), 14, 46, mat("metal"), 40, rotation=(math.pi / 2, 0, 0), bevel=1.0)
            rounded_box("motor gearbox", off("chassis", (55, side * 40, 42)), (26, 24, 26), mat("metal_dark"), 3, 6)
            cylinder("motor encoder", off("chassis", (55, side * 90, 42)), 9, 5, mat("pcb"), 32, rotation=(math.pi / 2, 0, 0), bevel=0.4)
            cylinder("wheel drive hub", off("chassis", (55, side * 98, 42)), 6, 10, mat("silver"), 24, rotation=(math.pi / 2, 0, 0), bevel=0.4)
        cylinder("caster mount", off("chassis", (126, 0, 30)), 10, 12, mat("metal_dark"), 24, bevel=0.6)
        cylinder("caster ball", off("chassis", (126, 0, 20)), 9, 9, mat("silver"), 32, bevel=2.0)

        # --- Removable electronics deck layer ---
        rounded_box("electronics deck plate", off("electronics", (-8, 0, 55)), (196, 164, 2.5), mat("metal_dark"), 2, 4)
        # Raspberry Pi 5 (85x56) + active cooler + I/O stack, centered-forward.
        rounded_box("Raspberry Pi 5 8GB", off("electronics", (-38, 0, 59)), (85, 56, 3.0), mat("pcb"), 0.6, 3)
        rounded_box("Pi active cooler", off("electronics", (-38, 6, 66)), (40, 40, 11), mat("charcoal"), 1.5, 4)
        rounded_box("Pi USB/LAN ports", off("electronics", (-79, -14, 62)), (6, 30, 8), mat("silver"), 0.6, 3)
        for cy in (-18, 18):
            rounded_box("Pi GPIO header", off("electronics", (-20, cy, 62)), (52, 5, 5), mat("charcoal"), 0.4, 2)
        # Cytron dual motor driver + heatsink, rearward near the motors.
        rounded_box("dual motor driver", off("electronics", (58, 0, 59)), (74, 56, 3.0), mat("pcb_blue"), 0.6, 3)
        rounded_box("driver heatsink", off("electronics", (58, 0, 65)), (60, 24, 9), mat("metal"), 1.0, 4)
        # 5V buck + secondary servo/LED regulator.
        rounded_box("5V buck regulator", off("electronics", (16, 58, 60)), (34, 24, 9), mat("pcb"), 0.8, 3)
        rounded_box("servo/LED regulator", off("electronics", (16, -58, 60)), (30, 22, 8), mat("pcb"), 0.8, 3)
        # Pico 2 safety MCU + power distribution/fuse block + main switch.
        rounded_box("Pico 2 safety MCU", off("electronics", (-40, -66, 60)), (52, 22, 3), mat("pcb"), 0.5, 3)
        rounded_box("power distribution / fuses", off("electronics", (96, -58, 61)), (34, 30, 14), mat("metal_dark"), 2, 4)
        cylinder("main power switch", off("electronics", (110, 46, 62)), 5, 10, mat("red"), 24, bevel=0.6)
        # USB far-field mic array (round), mounted high/forward, isolated.
        cylinder("USB mic array", off("electronics", (-80, 0, 66)), 34, 5, mat("pcb"), 48, bevel=0.6)
        for mi in range(6):
            ang = 2 * math.pi * mi / 6
            cylinder("mic capsule", off("electronics", (-80 + 26 * math.cos(ang), 26 * math.sin(ang), 69)), 3.2, 2, mat("silver"), 20, bevel=0.3)

        # --- Front sensing + speaker (mounted to the body shell front) ---
        cylinder("3W speaker", off("body", (-131, 0, 60)), 17, 15, mat("metal_dark"), 40, rotation=(0, math.pi / 2, 0), bevel=1.0)
        cylinder("speaker cone", off("body", (-139, 0, 60)), 13, 3, mat("charcoal"), 40, rotation=(0, math.pi / 2, 0), bevel=0.5)
        for ty in (-70, -24, 24, 70):
            rounded_box("VL53L1X ToF sensor", off("body", (-133, ty, 43)), (5, 12, 13), mat("pcb"), 0.8, 3)
            cylinder("ToF lens", off("body", (-136, ty, 43)), 2.4, 2, mat("metal_dark"), 20, rotation=(0, math.pi / 2, 0), bevel=0.3)

    # E-stop: top/rear/right, visually obvious and mechanically proud.
    estop = v["estop_scale"]
    estop_x = 70
    estop_y = 0
    # Flush recessed black well, then a rounded red mushroom DOME on a short stem.
    cylinder("estop black recessed well", off("deck", (estop_x, estop_y, deck_z - 0.5)), 23 * estop, 3, mat("black"), 72, bevel=0.7)
    cylinder("estop red stem", off("deck", (estop_x, estop_y, deck_z + 6.0)), 12.5 * estop, 11.0, mat("red"), 72, bevel=0.8)
    cylinder("estop red mushroom cap", off("deck", (estop_x, estop_y, deck_z + 14.0)), 23.5 * estop, 8.4, mat("red"), 96, bevel=4.0)
    cylinder("estop shallow top inset", off("deck", (estop_x, estop_y, deck_z + 18.3)), 14.0 * estop, 0.45, material("red_top_inset", (0.96, 0.18, 0.13, 1.0)), 96, bevel=0.35)

    # Neck and camera head. The cream column emerges from a distinct BLACK flared
    # rubber boot; teal is only a low outer collar ring at the deck.
    neck_x = -48
    cylinder("neck socket dark deck opening", off("deck", (neck_x, 0, deck_z + 3.0)), 20.0, 2.0, mat("black"), 72, bevel=0.45)
    cylinder("teal retained neck collar", off("deck", (neck_x, 0, deck_z + 2.0)), 22.5, 3.2, mat("teal"), 72, bevel=0.8)
    superellipse_shell(
        "neck black rubber boot",
        off("head", (neck_x, 0, 0)),
        [
            (deck_z + 3.0, 19.0, 19.0),
            (deck_z + 6.5, 17.0, 17.0),
            (deck_z + 10.0, 15.2, 15.2),
            (deck_z + 13.0, 14.4, 14.4),
        ],
        mat("black"),
        exponent=3.2,
        points=56,
    )
    neck_top = deck_z + 7.8 + v["neck_h"]
    superellipse_shell(
        "cream smooth flared neck column",
        off("head", (neck_x, 0, 0)),
        [
            (deck_z + 11.5, 14.0, 12.6),
            (deck_z + 14.0, 14.8, 12.6),
            (deck_z + 22.0, 11.0, 9.4),
            (neck_top - 12.0, 9.6, 8.3),
            (neck_top - 6.0, 11.8, 9.8),
            (neck_top - 2.0, 14.2, 11.5),
            (neck_top, 15.4, 12.4),
        ],
        mat("cream_light"),
        exponent=2.35,
        points=72,
    )
    torus("head black upper gasket", off("head", (neck_x, 0, neck_top)), 13.4, 1.8, mat("black"))

    # Head juts forward of the neck (the neck meets the lower-back of the head),
    # and the back stays full then rounds off — a rounded box, not a bullet.
    head_center = off("head", (neck_x - 16.0, 0, neck_top + 9.6))
    x_capsule_shell(
        "cream capsule camera head",
        head_center,
        [
            (-v["head_d"] / 2, v["head_w"] / 2 - 7, v["head_h"] / 2 - 5.5),
            (-v["head_d"] / 2 + 4.0, v["head_w"] / 2 + 1.5, v["head_h"] / 2 + 1.2),
            (-6, v["head_w"] / 2 + 4.2, v["head_h"] / 2 + 2.0),
            (12, v["head_w"] / 2 + 3.4, v["head_h"] / 2 + 1.8),
            (v["head_d"] / 2 - 3, v["head_w"] / 2 - 0.5, v["head_h"] / 2 - 0.5),
            (v["head_d"] / 2 + 0.5, v["head_w"] / 2 - 7, v["head_h"] / 2 - 5.0),
            (v["head_d"] / 2 + 3.0, v["head_w"] / 2 - 18, v["head_h"] / 2 - 11.0),
        ],
        mat("cream_light"),
        exponent=3.5,
        points=96,
    )
    face_x = head_center[0] - v["head_d"] / 2 - 1.4
    x_capsule_shell(
        "cream raised rounded face bezel",
        (face_x - 0.1, 0, head_center[2] - 0.3),
        [
            (-1.8, (v["face_w"] + 14) / 2, (v["face_h"] + 11) / 2),
            (1.8, (v["face_w"] + 14) / 2, (v["face_h"] + 11) / 2),
        ],
        mat("cream_light"),
        exponent=5.0,
        points=112,
    )
    x_capsule_shell(
        "thin shadow line around black faceplate",
        (face_x - 1.5, 0, head_center[2] - 0.2),
        [
            (-0.9, (v["face_w"] + 0.5) / 2, (v["face_h"] - 0.5) / 2),
            (0.9, (v["face_w"] + 0.5) / 2, (v["face_h"] - 0.5) / 2),
        ],
        mat("cream_shadow"),
        exponent=5.0,
        points=112,
    )
    x_capsule_shell(
        "inset rounded black head faceplate",
        (face_x - 2.0, 0, head_center[2] - 0.2),
        [
            (-1.0, (v["face_w"] - 6) / 2, (v["face_h"] - 3) / 2),
            (1.0, (v["face_w"] - 6) / 2, (v["face_h"] - 3) / 2),
        ],
        mat("charcoal"),
        exponent=5.2,
        points=112,
    )
    # Large prominent fisheye camera lens (dominant focal point), with a convex
    # domed glass and no stray offset glint.
    lens_cz = head_center[2] - 0.1
    cylinder("camera lens outer", (face_x - 6.2, 0, lens_cz), 12.6, 7.4, mat("black"), 84, rotation=(0, math.pi / 2, 0), bevel=0.8)
    cylinder("camera lens satin retaining ring", (face_x - 9.6, 0, lens_cz), 10.2, 2.2, material("lens_ring", (0.035, 0.043, 0.055, 1.0)), 84, rotation=(0, math.pi / 2, 0), bevel=0.4)
    cylinder("camera lens inner barrel", (face_x - 11.0, 0, lens_cz), 8.2, 2.0, mat("black"), 84, rotation=(0, math.pi / 2, 0), bevel=0.35)
    cylinder("camera lens glass base", (face_x - 12.1, 0, lens_cz), 6.6, 1.4, material("camera_glass", (0.015, 0.038, 0.07, 1.0)), 80, rotation=(0, math.pi / 2, 0), bevel=0.3)
    # Convex glass dome (UV-sphere cap scaled thin in X) so the lens reads domed.
    bpy.ops.mesh.primitive_uv_sphere_add(radius=6.5, location=(face_x - 12.1, 0, lens_cz), segments=48, ring_count=24)
    dome = bpy.context.object
    dome.name = "camera lens dome"
    dome.scale = (0.5, 1.0, 1.0)
    bpy.ops.object.transform_apply(scale=True)
    dome.data.materials.append(material("camera_glass", (0.015, 0.038, 0.07, 1.0)))
    shade_smooth(dome)
    for y in (-24.0, 24.0):
        sign = 1.0 if y > 0 else -1.0
        x_capsule_shell(
            "head oval lime eye",
            (face_x - 5.9, y, head_center[2] - 0.6),
            [
                (-1.2, 3.5, 6.7),
                (1.2, 3.5, 6.7),
            ],
            mat("lime"),
            exponent=2.4,
            points=48,
        )
        # Bold, thick, fairly flat blue brow riding the upper plate above the
        # lens: inner end high toward center, sweeping gently down-and-out to
        # the top corner (long, flat sweep like the concept).
        curve_tube(
            "curved blue brow cap",
            [
                (face_x - 3.8, sign * 9.5, head_center[2] + 15.0),
                (face_x - 4.4, sign * 22.0, head_center[2] + 14.3),
                (face_x - 3.6, sign * 36.0, head_center[2] + 12.0),
            ],
            mat("blue"),
            3.8,
            6,
        )
    for y in (-53, 53):
        rounded_box("subtle head side seam", (head_center[0] + 7, y, head_center[2] + 4), (28, 0.9, 1.8), mat("cream_shadow"), 0.35, 2)

    if safety:
        rounded_box("bumper travel envelope", (-15, 0, 28), (320, 242, 36), mat("safety_teal"), 12, 8)


def look_at(obj: bpy.types.Object, target: tuple[float, float, float]) -> None:
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def setup_camera(view: str) -> None:
    # (position, target, scale, projection, lens)
    # For PERSP cameras `scale` is ignored and `lens` (mm) drives the framing;
    # for ORTHO cameras `scale` is the ortho width and `lens` is unused.
    configs = {
        # Concept-matched hero: raised front-left three-quarter (~26 deg above the
        # floor so the teal deck reads), mild perspective so the near bumper looks
        # slightly larger, exactly like the finished art.
        "front_3q": ((-500, -410, 235), (-12, 7, 74), 410, "PERSP", 62),
        "side": ((10, -520, 145), (12, 0, 72), 340, "ORTHO", 70),
        "top": ((0, 0, 580), (0, 0, 65), 440, "ORTHO", 70),
        "exploded": ((-520, -420, 360), (2, 0, 205), 900, "ORTHO", 70),
        "service": ((-470, -380, 300), (0, 0, 120), 600, "ORTHO", 70),
        "iteration": ((-430, -315, 195), (-6, 0, 76), 420, "ORTHO", 70),
    }
    position, target, scale, projection, lens = configs[view]
    cam_data = bpy.data.cameras.new(f"{view}_camera")
    cam = bpy.data.objects.new(f"{view}_camera", cam_data)
    bpy.context.collection.objects.link(cam)
    cam.location = position
    look_at(cam, target)
    cam_data.type = projection
    cam_data.ortho_scale = scale
    cam_data.lens = lens
    cam_data.sensor_width = 36
    bpy.context.scene.camera = cam


def add_lighting() -> None:
    world = bpy.context.scene.world or bpy.data.worlds.new("World")
    bpy.context.scene.world = world
    world.color = (0.965, 0.93, 0.87)

    # Soft product-studio setup matching the warm, evenly lit concept art. Only
    # the big key and a wide soft sun cast shadows (large sources -> soft, no hard
    # blob shadows on the body); the fill and rim are shadowless so they lift the
    # shadows and sculpt the form without stamping edges onto the cream shell.
    # Warm the emitters so the cream reads as the concept's warm ivory rather
    # than a cool studio grey (default white emitters were washing out the warm
    # world color).
    warm = (1.0, 0.90, 0.78)

    bpy.ops.object.light_add(type="AREA", location=(-250, -330, 380))
    key = bpy.context.object
    key.name = "large softbox key"
    key.data.energy = 95000
    key.data.size = 360
    key.data.color = warm
    look_at(key, (-40, 0, 70))

    bpy.ops.object.light_add(type="AREA", location=(330, -140, 250))
    fill = bpy.context.object
    fill.name = "warm front fill"
    fill.data.energy = 24000
    fill.data.size = 420
    fill.data.color = warm
    fill.data.use_shadow = False
    look_at(fill, (0, 0, 70))

    bpy.ops.object.light_add(type="AREA", location=(210, 300, 320))
    rim = bpy.context.object
    rim.name = "cool rim"
    rim.data.energy = 11000
    rim.data.size = 300
    rim.data.color = (0.92, 0.95, 1.0)
    rim.data.use_shadow = False
    look_at(rim, (0, 0, 90))

    bpy.ops.object.light_add(type="AREA", location=(-150, -170, 210))
    face = bpy.context.object
    face.name = "face sparkle"
    face.data.energy = 5200
    face.data.size = 90
    face.data.color = warm
    face.data.use_shadow = False
    look_at(face, (-70, 0, 130))

    bpy.ops.object.light_add(type="SUN", location=(-40, -60, 300))
    sun = bpy.context.object
    sun.name = "soft product sun"
    sun.data.energy = 1.1
    sun.data.angle = math.radians(9.0)
    sun.data.use_shadow = False  # key owns the (soft) shadow; sun is pure fill
    look_at(sun, (10, 20, 0))


def setup_render(width: int, height: int) -> None:
    scene = bpy.context.scene
    for engine in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE", "BLENDER_WORKBENCH"):
        try:
            scene.render.engine = engine
            break
        except TypeError:
            continue
    scene.render.resolution_x = width
    scene.render.resolution_y = height
    scene.render.film_transparent = False
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.view_transform = "Standard"
    try:
        scene.view_settings.look = "None"
    except TypeError:
        pass
    scene.view_settings.exposure = 0.95
    scene.view_settings.gamma = 1
    if hasattr(scene, "eevee"):
        try:
            scene.eevee.taa_render_samples = 48
            scene.eevee.use_gtao = False
            scene.eevee.gtao_distance = 4
            scene.eevee.gtao_factor = 1.25
        except Exception:
            pass


def render_scene(
    path: Path,
    view: str,
    progress: float = 1.0,
    mode: str = "assembled",
    refinement: float = 1.0,
    width: int = 1600,
    height: int = 1000,
) -> None:
    clean_scene()
    build_robot(progress=progress, mode=mode, refinement=refinement)
    add_lighting()
    setup_camera(view)
    setup_render(width, height)
    bpy.context.scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    # Literal iteration loops requested by the user. These are thumbnails, not
    # final manufacturing evidence; the second loop keeps pushing fidelity.
    for index in range(12):
        progress = index / 11
        render_scene(
            OUT / f"codex_body_blender_iter_{index + 1:02d}.png",
            "iteration",
            progress=progress,
            mode="assembled",
            refinement=0.0,
            width=900,
            height=620,
        )

    for index in range(12):
        refinement = index / 11
        render_scene(
            OUT / f"codex_body_blender_iter_{index + 13:02d}.png",
            "iteration",
            progress=1.0,
            mode="assembled",
            refinement=refinement,
            width=900,
            height=620,
        )

    final_jobs = [
        ("codex_body_blender_front_3q.png", "front_3q", "assembled"),
        ("codex_body_blender_side.png", "side", "assembled"),
        ("codex_body_blender_top.png", "top", "assembled"),
        ("codex_body_blender_exploded_fit.png", "exploded", "exploded"),
        ("codex_body_blender_service_top_off.png", "service", "service"),
        ("codex_body_blender_safety_review.png", "front_3q", "safety"),
    ]
    for filename, view, mode in final_jobs:
        render_scene(OUT / filename, view, progress=1.0, mode=mode, refinement=1.0, width=1600, height=1000)

    print("generated Blender renders:")
    for path in sorted(OUT.glob("codex_body_blender_*.png")):
        print(f"  {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
