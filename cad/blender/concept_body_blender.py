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
    "cream": (0.88, 0.78, 0.60, 1.0),
    "cream_light": (0.94, 0.82, 0.62, 1.0),
    "cream_shadow": (0.58, 0.49, 0.36, 1.0),
    "teal": (0.00, 0.31, 0.35, 1.0),
    "teal_dark": (0.00, 0.17, 0.20, 1.0),
    "charcoal": (0.018, 0.020, 0.024, 1.0),
    "panel_black": (0.008, 0.009, 0.011, 1.0),
    "black": (0.0, 0.0, 0.0, 1.0),
    "rubber": (0.105, 0.100, 0.092, 1.0),
    "rubber_tread": (0.090, 0.086, 0.078, 1.0),
    "lime": (0.72, 1.0, 0.22, 1.0),
    "blue": (0.03, 0.23, 0.76, 1.0),
    "red": (0.86, 0.08, 0.04, 1.0),
    "keepout": (0.30, 0.52, 1.0, 0.28),
    "safety_teal": (0.00, 0.72, 0.78, 0.22),
    "safety_red": (1.0, 0.16, 0.08, 0.24),
    "floor": (0.68, 0.52, 0.36, 1.0),
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


def cone(
    name: str,
    loc: tuple[float, float, float],
    radius1: float,
    radius2: float,
    depth: float,
    material_obj: bpy.types.Material,
    vertices: int = 72,
) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cone_add(vertices=vertices, radius1=radius1, radius2=radius2, depth=depth, location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material_obj)
    add_bevel(obj, 1.2, 4)
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


def trapezoid_prism(
    name: str,
    loc: tuple[float, float, float],
    length: float,
    front_width: float,
    rear_width: float,
    height: float,
    material_obj: bpy.types.Material,
    bevel: float,
    segments: int = 8,
) -> bpy.types.Object:
    x0 = loc[0] - length / 2
    x1 = loc[0] + length / 2
    y0f = -front_width / 2
    y1f = front_width / 2
    y0r = -rear_width / 2
    y1r = rear_width / 2
    z0 = loc[2] - height / 2
    z1 = loc[2] + height / 2
    verts = [
        (x0, y0f, z0),
        (x0, y1f, z0),
        (x1, y1r, z0),
        (x1, y0r, z0),
        (x0, y0f, z1),
        (x0, y1f, z1),
        (x1, y1r, z1),
        (x1, y0r, z1),
    ]
    faces = [
        (0, 1, 2, 3),
        (4, 7, 6, 5),
        (0, 4, 5, 1),
        (1, 5, 6, 2),
        (2, 6, 7, 3),
        (3, 7, 4, 0),
    ]
    mesh = bpy.data.meshes.new(f"{name}_mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(material_obj)
    add_bevel(obj, bevel, segments)
    shade_smooth(obj)
    return obj


def rounded_trapezoid_plate(
    name: str,
    loc: tuple[float, float, float],
    length: float,
    front_width: float,
    rear_width: float,
    corner: float,
    material_obj: bpy.types.Material,
) -> bpy.types.Object:
    """Build a flat trapezoid-like hood inlay without vertical slab sides."""
    f = front_width / 2
    r = rear_width / 2
    half_len = length / 2
    exponent = max(2.4, min(4.8, length / max(corner, 1.0) * 0.65))
    verts: list[tuple[float, float, float]] = []
    for index in range(96):
        angle = 2 * math.pi * index / 96
        ca = math.cos(angle)
        sa = math.sin(angle)
        x_local = half_len * math.copysign(abs(ca) ** (2 / exponent), ca)
        taper = (x_local + half_len) / length
        half_y = f + (r - f) * taper
        y_local = half_y * math.copysign(abs(sa) ** (2 / exponent), sa)
        verts.append((loc[0] + x_local, loc[1] + y_local, loc[2]))

    mesh = bpy.data.meshes.new(f"{name}_mesh")
    mesh.from_pydata(verts, [], [tuple(range(len(verts)))])
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(material_obj)
    obj.modifiers.new("hood weighted normals", "WEIGHTED_NORMAL")
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
    faces.append(tuple(reversed(range(points))))
    top_start = (len(rings) - 1) * points
    faces.append(tuple(top_start + index for index in range(points)))

    mesh = bpy.data.meshes.new(f"{name}_mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(material_obj)
    obj.modifiers.new("shell weighted normals", "WEIGHTED_NORMAL")
    shade_smooth(obj)
    return obj


def superellipse_plate(
    name: str,
    loc: tuple[float, float, float],
    half_x: float,
    half_y: float,
    material_obj: bpy.types.Material,
    exponent: float = 3.5,
    points: int = 96,
) -> bpy.types.Object:
    """Build a flat rounded inlay surface without visible vertical side walls."""
    verts: list[tuple[float, float, float]] = []
    for index in range(points):
        angle = 2 * math.pi * index / points
        ca = math.cos(angle)
        sa = math.sin(angle)
        x = half_x * math.copysign(abs(ca) ** (2 / exponent), ca)
        y = half_y * math.copysign(abs(sa) ** (2 / exponent), sa)
        verts.append((loc[0] + x, loc[1] + y, loc[2]))

    mesh = bpy.data.meshes.new(f"{name}_mesh")
    mesh.from_pydata(verts, [], [tuple(range(points))])
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(material_obj)
    obj.modifiers.new("plate weighted normals", "WEIGHTED_NORMAL")
    return obj


def curved_front_band(
    name: str,
    loc: tuple[float, float, float],
    y_half: float,
    z_center: float,
    height: float,
    outer_x: float,
    inner_x: float,
    side_recede: float,
    material_obj: bpy.types.Material,
    points: int = 44,
    exponent: float = 1.85,
    bevel: float = 3.0,
) -> bpy.types.Object:
    """Build a curved, constant-thickness front bumper or fascia band."""
    z0 = loc[2] + z_center - height / 2
    z1 = loc[2] + z_center + height / 2
    samples: list[tuple[float, float, float, float]] = []
    for index in range(points):
        t = index / (points - 1)
        y = -y_half + 2 * y_half * t
        recede = side_recede * (abs(y) / y_half) ** exponent
        samples.append((loc[0] + outer_x + recede, loc[0] + inner_x + recede, loc[1] + y, recede))

    verts: list[tuple[float, float, float]] = []
    for outer, inner, y, _ in samples:
        verts.extend(
            [
                (outer, y, z0),
                (inner, y, z0),
                (outer, y, z1),
                (inner, y, z1),
            ]
        )

    faces: list[tuple[int, ...]] = []
    for index in range(points - 1):
        a = index * 4
        b = (index + 1) * 4
        faces.extend(
            [
                (a, b, b + 2, a + 2),  # outer face
                (a + 1, a + 3, b + 3, b + 1),  # inner face
                (a + 2, b + 2, b + 3, a + 3),  # top face
                (a, a + 1, b + 1, b),  # bottom face
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
    add_bevel(obj, bevel, 10)
    shade_smooth(obj)
    return obj


def curved_front_band_segment(
    name: str,
    loc: tuple[float, float, float],
    y_start: float,
    y_end: float,
    y_half: float,
    z_center: float,
    height: float,
    outer_x: float,
    inner_x: float,
    side_recede: float,
    material_obj: bpy.types.Material,
    points: int = 24,
    exponent: float = 1.85,
    bevel: float = 5.0,
) -> bpy.types.Object:
    """Build one curved bumper/fascia segment on the shared front arc."""
    segment_mid = (y_start + y_end) / 2
    segment_half = abs(y_end - y_start) / 2
    z_half = height / 2
    verts: list[tuple[float, float, float]] = []
    for index in range(points):
        t = index / (points - 1)
        y = y_start + (y_end - y_start) * t
        recede = side_recede * (abs(y) / y_half) ** exponent
        local_z_half = capsule_z_radius(y - segment_mid, segment_half, z_half)
        verts.extend(
            [
                (loc[0] + outer_x + recede, loc[1] + y, loc[2] + z_center - local_z_half),
                (loc[0] + inner_x + recede, loc[1] + y, loc[2] + z_center - local_z_half),
                (loc[0] + outer_x + recede, loc[1] + y, loc[2] + z_center + local_z_half),
                (loc[0] + inner_x + recede, loc[1] + y, loc[2] + z_center + local_z_half),
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
                (a + 2, b + 2, b + 3, a + 3),
                (a, a + 1, b + 1, b),
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
    add_bevel(obj, bevel, 10)
    shade_smooth(obj)
    return obj


def curved_front_oval_band(
    name: str,
    loc: tuple[float, float, float],
    y_half: float,
    z_center: float,
    x_center: float,
    radius_x: float,
    radius_z: float,
    side_recede: float,
    material_obj: bpy.types.Material,
    points: int = 96,
    ring_points: int = 28,
    exponent: float = 1.85,
) -> bpy.types.Object:
    """Build a rounded curved bumper band with an oval x/z cross-section."""
    verts: list[tuple[float, float, float]] = []
    for index in range(points):
        t = index / (points - 1)
        y = -y_half + 2 * y_half * t
        recede = side_recede * (abs(y) / y_half) ** exponent
        cx = loc[0] + x_center + recede
        for ring_index in range(ring_points):
            angle = 2 * math.pi * ring_index / ring_points
            verts.append(
                (
                    cx + radius_x * math.cos(angle),
                    loc[1] + y,
                    loc[2] + z_center + radius_z * math.sin(angle),
                )
            )

    faces: list[tuple[int, ...]] = []
    for index in range(points - 1):
        a = index * ring_points
        b = (index + 1) * ring_points
        for ring_index in range(ring_points):
            faces.append(
                (
                    a + ring_index,
                    a + (ring_index + 1) % ring_points,
                    b + (ring_index + 1) % ring_points,
                    b + ring_index,
                )
            )
    faces.append(tuple(reversed(range(ring_points))))
    last = (points - 1) * ring_points
    faces.append(tuple(last + index for index in range(ring_points)))

    mesh = bpy.data.meshes.new(f"{name}_mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(material_obj)
    obj.modifiers.new("bumper weighted normals", "WEIGHTED_NORMAL")
    shade_smooth(obj)
    return obj


def front_curve_x(y: float, base_x: float, y_half: float, side_recede: float, exponent: float = 1.85) -> float:
    """Return the x position on the shared curved nose/bumper arc."""
    clamped = min(abs(y), y_half) / y_half
    return base_x + side_recede * clamped**exponent


def front_curve_points(
    base_x: float,
    y_half: float,
    z: float,
    side_recede: float,
    exponent: float = 1.85,
    count: int = 9,
) -> list[tuple[float, float, float]]:
    points: list[tuple[float, float, float]] = []
    for index in range(count):
        t = index / (count - 1)
        y = -y_half + 2 * y_half * t
        points.append((front_curve_x(y, base_x, y_half, side_recede, exponent), y, z))
    return points


def capsule_z_radius(y: float, y_half: float, z_half: float) -> float:
    """Return the vertical half-height for a horizontal pill at position y."""
    straight_half = max(0.0, y_half - z_half)
    distance = abs(y)
    if distance <= straight_half:
        return z_half
    cap_distance = min(z_half, distance - straight_half)
    return max(0.7, math.sqrt(max(0.0, z_half * z_half - cap_distance * cap_distance)))


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


def curved_front_pill_frame(
    name: str,
    loc: tuple[float, float, float],
    outer_y_half: float,
    outer_z_center: float,
    outer_z_half: float,
    inner_y_half: float,
    inner_z_center: float,
    inner_z_half: float,
    front_x: float,
    back_x: float,
    side_recede: float,
    material_obj: bpy.types.Material,
    points: int = 96,
    exponent: float = 1.65,
    bevel: float = 1.4,
) -> bpy.types.Object:
    """Build a curved cream frame around a recessed pill opening."""
    outer = capsule_outline(outer_y_half, outer_z_center, outer_z_half, points)
    inner = capsule_outline(inner_y_half, inner_z_center, inner_z_half, points)
    loops: list[list[tuple[float, float, float]]] = []
    for base_x, outline in ((front_x, outer), (front_x, inner), (back_x, outer), (back_x, inner)):
        loop: list[tuple[float, float, float]] = []
        for y, z in outline:
            clamped = min(abs(y), outer_y_half) / outer_y_half
            x = loc[0] + base_x + side_recede * clamped**exponent
            loop.append((x, loc[1] + y, loc[2] + z))
        loops.append(loop)

    verts = [point for loop in loops for point in loop]
    outer_front = 0
    inner_front = points
    outer_back = points * 2
    inner_back = points * 3
    faces: list[tuple[int, ...]] = []
    for index in range(points):
        next_index = (index + 1) % points
        faces.extend(
            [
                (outer_front + index, outer_front + next_index, inner_front + next_index, inner_front + index),
                (outer_back + index, inner_back + index, inner_back + next_index, outer_back + next_index),
                (outer_front + index, outer_back + index, outer_back + next_index, outer_front + next_index),
                (inner_front + next_index, inner_back + next_index, inner_back + index, inner_front + index),
            ]
        )

    mesh = bpy.data.meshes.new(f"{name}_mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(material_obj)
    add_bevel(obj, bevel, 6)
    shade_smooth(obj)
    return obj


def curved_front_pill_band(
    name: str,
    loc: tuple[float, float, float],
    y_half: float,
    z_center: float,
    z_half: float,
    outer_x: float,
    inner_x: float,
    side_recede: float,
    material_obj: bpy.types.Material,
    points: int = 72,
    exponent: float = 1.65,
    bevel: float = 2.6,
) -> bpy.types.Object:
    """Build a curved front inset with rounded pill ends in the y/z plane."""
    samples: list[tuple[float, float, float, float, float]] = []
    for index in range(points):
        t = index / (points - 1)
        y = -y_half + 2 * y_half * t
        recede = side_recede * (abs(y) / y_half) ** exponent
        zh = capsule_z_radius(y, y_half, z_half)
        samples.append(
            (
                loc[0] + outer_x + recede,
                loc[0] + inner_x + recede,
                loc[1] + y,
                loc[2] + z_center - zh,
                loc[2] + z_center + zh,
            )
        )

    verts: list[tuple[float, float, float]] = []
    for outer, inner, y, z0, z1 in samples:
        verts.extend(
            [
                (outer, y, z0),
                (inner, y, z0),
                (outer, y, z1),
                (inner, y, z1),
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
                (a + 2, b + 2, b + 3, a + 3),
                (a, a + 1, b + 1, b),
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
    add_bevel(obj, bevel, 8)
    shade_smooth(obj)
    return obj


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
    faces.append(tuple(reversed(range(points))))
    back_start = (len(slices) - 1) * points
    faces.append(tuple(back_start + index for index in range(points)))

    mesh = bpy.data.meshes.new(f"{name}_mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(material_obj)
    obj.modifiers.new("capsule weighted normals", "WEIGHTED_NORMAL")
    shade_smooth(obj)
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
        "head_d": lerp(matched["head_d"], 58, refinement),
        "head_h": lerp(matched["head_h"], 40, refinement),
        "head_bevel": lerp(matched["head_bevel"], 27, refinement),
        "face_w": lerp(matched["face_w"], 84, refinement),
        "face_h": lerp(matched["face_h"], 33, refinement),
        "neck_h": lerp(matched["neck_h"], 33, refinement),
        "top_black_len": lerp(matched["top_black_len"], 64, refinement),
        "side_panel_len": lerp(matched["side_panel_len"], 74, refinement),
        "estop_scale": lerp(matched["estop_scale"], 0.82, refinement),
    }


def make_fender(side: int, v: dict[str, float], z_offset: float = 0.0) -> bpy.types.Object:
    arch = side_arch_band(
        f"cream integrated wheel arch fairing {'right' if side > 0 else 'left'}",
        center_x=v["wheel_x"] - 1,
        y_center=side * 104.0,
        center_z=38 + z_offset,
        outer_radius_x=39,
        outer_radius_z=35,
        band_width=11,
        depth=22,
        side=side,
        material_obj=mat("cream_light"),
        start_deg=12,
        end_deg=168,
        points=42,
        bevel=2.2,
    )
    rounded_box(
        f"cream fender front blend pad {'right' if side > 0 else 'left'}",
        (v["wheel_x"] - 31, side * 103.5, 35 + z_offset),
        (15, 13, 13),
        mat("cream_light"),
        6,
        12,
    )
    rounded_box(
        f"cream fender rear blend pad {'right' if side > 0 else 'left'}",
        (v["wheel_x"] + 31, side * 103.5, 35 + z_offset),
        (15, 13, 13),
        mat("cream_light"),
        6,
        12,
    )
    return arch


def add_tire_tread_marks(side: int, wheel_loc: tuple[float, float, float], outside_y: float) -> None:
    face_y = outside_y + side * 0.7
    for index in range(18):
        theta = 2 * math.pi * index / 18
        x = wheel_loc[0] + 28.5 * math.cos(theta)
        z = wheel_loc[2] + 28.5 * math.sin(theta)
        rounded_box(
            "sidewall tire tread mark",
            (x, face_y, z),
            (1.2, 0.7, 6.2),
            mat("rubber_tread"),
            0.25,
            3,
            rotation=(0, -theta, 0),
        )


def wheel_arch_points(
    center_x: float,
    y: float,
    center_z: float,
    radius_x: float,
    radius_z: float,
    start_deg: float = 28,
    end_deg: float = 154,
    count: int = 11,
) -> list[tuple[float, float, float]]:
    points: list[tuple[float, float, float]] = []
    for index in range(count):
        t = index / (count - 1)
        theta = math.radians(start_deg + (end_deg - start_deg) * t)
        points.append((center_x + radius_x * math.cos(theta), y, center_z + radius_z * math.sin(theta)))
    return points


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
        "tray": (0, 0, -28 if exploded else 0),
        "body": (0, 0, 36 if exploded else 0),
        "deck": (-1 if exploded else 0, 0, 112 if exploded else 74 if service else 0),
        "head": (0, 0, 190 if exploded else 126 if service else 0),
        "bumper": (-34 if exploded else 0, 0, -8 if exploded else 0),
        "wheel": (0, 0, -10 if exploded else 0),
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
    superellipse_shell(
        "molded cream body shell",
        off("body", (0, 0, 0)),
        [
            (16, 122, 88),
            (28, 139, 101),
            (50, 144, 105),
            (68, 139, 101),
            (76, 126, 91),
        ],
        mat("cream_light"),
        exponent=3.75,
        points=112,
    )
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
    rounded_trapezoid_plate(
        "front black hood grille panel",
        off("body", (-127, 0, deck_z + 0.92)),
        length=44,
        front_width=76,
        rear_width=58,
        corner=8.0,
        material_obj=mat("panel_black"),
    )
    for y in (-18, -9, 0, 9, 18):
        rounded_box("front hood grille slot", off("body", (-137, y, deck_z + 1.16)), (12, 1.35, 0.35), mat("charcoal"), 0.4, 3)
    for y in (-22, -11, 0, 11, 22):
        rounded_box("deck vent slot", off("deck", (8, y, deck_z + 3)), (34, 3.0, 1.5), mat("charcoal"), 1.0, 3)
    for x, y in [(-93, -57), (-93, 57), (86, -57), (86, 57)]:
        cylinder("black deck screw", off("deck", (x, y, deck_z + 3)), 1.55, 1.2, mat("charcoal"), 28, bevel=0.2)
    for x, y in [(-93, -57), (-93, 57), (86, -57), (86, 57), (-10, -58), (-10, 58)]:
        cylinder("deck underside alignment peg", off("deck", (x, y, deck_z - 8)), 2.2, 12, mat("teal_dark"), 28, bevel=0.25)

    # Recessed front sensor fascia: every visible front element follows the
    # same broad arc as the molded nose. The cream nose should read as one
    # smooth front surface; the black LED strip sits back inside it.
    front_y_half = 126
    front_recede = 64
    front_exponent = 1.42
    curved_front_pill_band(
        "smooth cream lower front nose",
        off("body", (0, 0, 0)),
        y_half=front_y_half,
        z_center=32.5,
        z_half=14.6,
        outer_x=-161.5,
        inner_x=-124.0,
        side_recede=front_recede,
        material_obj=mat("cream_light"),
        points=104,
        exponent=front_exponent,
        bevel=8.0,
    )
    curved_front_pill_band(
        "thin dark bumper docking shadow",
        off("body", (0, 0, 0)),
        y_half=116,
        z_center=25.7,
        z_half=1.35,
        outer_x=-160.5,
        inner_x=-142.4,
        side_recede=58,
        material_obj=mat("charcoal"),
        points=96,
        exponent=front_exponent,
        bevel=0.9,
    )
    for y in (-78, 78):
        socket_x = front_curve_x(y, -158.6, 120, 60, front_exponent)
        rounded_box(
            "cream front bumper mounting pocket",
            off("body", (socket_x + 2.2, y, 28.4)),
            (3.4, 9.2, 3.2),
            mat("cream_shadow"),
            1.8,
            6,
            rotation=(0, 0, 0.11 if y > 0 else -0.11),
        )
    curved_front_pill_frame(
        "cream molded sensor recess raised lip",
        off("body", (0, 0, 0)),
        outer_y_half=91,
        outer_z_center=42.5,
        outer_z_half=10.6,
        inner_y_half=79,
        inner_z_center=42.2,
        inner_z_half=7.2,
        front_x=-166.4,
        back_x=-159.3,
        side_recede=28,
        material_obj=mat("cream_light"),
        points=96,
        exponent=front_exponent,
        bevel=1.8,
    )
    curved_front_pill_band(
        "recessed black curved pill sensor insert",
        off("body", (0, 0, 0)),
        y_half=78,
        z_center=42.2,
        z_half=6.7,
        outer_x=-162.7,
        inner_x=-151.0,
        side_recede=20,
        material_obj=mat("panel_black"),
        points=92,
        exponent=front_exponent,
        bevel=3.4,
    )
    for y in (-62, 62):
        lamp_x = front_curve_x(y, -162.7, 78, 20, front_exponent)
        rounded_box(
            "recessed front black lamp pocket",
            off("body", (lamp_x - 0.30, y, 41.1)),
            (1.0, 20, 7.3),
            mat("black"),
            4.0,
            10,
            rotation=(0, 0, 0.12 if y > 0 else -0.12),
        )
        rounded_box(
            "front lime light",
            off("body", (lamp_x - 0.85, y, 41.7)),
            (1.15, 15.2, 4.7),
            mat("lime"),
            3.0,
            10,
            rotation=(0, 0, 0.12 if y > 0 else -0.12),
        )
    for y, r in [(-18, 2.8), (18, 3.0)]:
        lens_x = front_curve_x(y, -162.8, 78, 20, front_exponent)
        cylinder("front subtle sensor dimple", off("body", (lens_x - 0.35, y, 42.5)), r, 0.8, mat("charcoal"), 32, rotation=(0, math.pi / 2, 0), bevel=0.2)

    # Soft bumper: one continuous curved TPU front piece attached to the curved nose.
    bumper_z = 26.4
    curved_front_pill_band(
        "soft continuous curved front bumper backing",
        off("bumper", (0, 0, 0)),
        y_half=122,
        z_center=bumper_z,
        z_half=8.1,
        outer_x=-173.2,
        inner_x=-136.4,
        side_recede=58,
        material_obj=mat("rubber"),
        points=112,
        exponent=front_exponent,
        bevel=5.6,
    )
    curved_front_oval_band(
        "soft puffy rounded front bumper face",
        off("bumper", (0, 0, 0)),
        y_half=121,
        z_center=bumper_z - 0.1,
        x_center=-164.0,
        radius_x=13.8,
        radius_z=10.5,
        side_recede=58,
        material_obj=mat("rubber"),
        points=112,
        ring_points=24,
        exponent=front_exponent,
    )
    for side in (-1, 1):
        return_start_x = front_curve_x(side * 111, -164.5, 121, 58, front_exponent)
        curve_tube(
            "soft curved bumper side return",
            [off("bumper", point) for point in [
                (return_start_x, side * 111, bumper_z + 0.1),
                (-86, side * 105, bumper_z - 0.4),
                (-44, side * 100.5, bumper_z - 1.1),
            ]],
            mat("rubber"),
            5.4,
            5,
        )
        rounded_box(
            "flat side lower rubber bumper rail",
            off("bumper", (18, side * 98.8, bumper_z - 3.0)),
            (92, 5.0, 7.2),
            mat("rubber"),
            2.2,
            12,
        )
        for x in (-62, 14, 74):
            cylinder(
                "side bumper recessed fastener",
                off("bumper", (x, side * 101.4, bumper_z - 0.2)),
                1.25,
                1.2,
                mat("charcoal"),
                24,
                rotation=(math.pi / 2, 0, 0),
                bevel=0.25,
            )
    for y, angle in [(-39, -0.07), (39, 0.07)]:
        seam_x = front_curve_x(y, -176.0, 122, 58, front_exponent)
        rounded_box("front bumper split seam", off("bumper", (seam_x, y, bumper_z - 0.2)), (0.65, 0.65, 9.2), mat("rubber_tread"), 0.10, 2, rotation=(0, 0, angle))
    for side in (-1, 1):
        rounded_box("short rear bumper cap", off("bumper", (74, side * 98.0, bumper_z - 2.8)), (18, 5.8, 7.0), mat("rubber"), 2.6, 8)

    # Wheels, hubs, cream fenders, and side service panels.
    for side in (-1, 1):
        wheel_y = side * v["wheel_y"]
        if exploded:
            wheel_y += side * 28
        wheel_loc = off("wheel", (v["wheel_x"], wheel_y, 42))
        tire_radius = 30
        cylinder("black rubber tire", wheel_loc, tire_radius, 16.5, mat("rubber"), 96, rotation=(math.pi / 2, 0, 0), bevel=0.9)
        outside_y = wheel_loc[1] + side * 8.8
        cylinder("teal wheel accent ring", (wheel_loc[0], outside_y, wheel_loc[2]), 22.6, 3.0, mat("teal"), 72, rotation=(math.pi / 2, 0, 0), bevel=0.5)
        cylinder("cream wheel hub", (wheel_loc[0], outside_y + side * 1.1, wheel_loc[2]), 16.8, 3.7, mat("cream_light"), 72, rotation=(math.pi / 2, 0, 0), bevel=0.65)
        add_tire_tread_marks(side, wheel_loc, outside_y)
        make_fender(side, v, offsets["body"][2])
        curve_tube(
            "thin wheel arch seam shadow",
            wheel_arch_points(v["wheel_x"] - 2, side * 94.0, 35 + offsets["body"][2], 36, 29, 20, 160, 15),
            mat("cream_shadow"),
            1.0,
            3,
        )
        panel_len = v["side_panel_len"] + 30
        rounded_box("side service panel recessed pocket", off("body", (8, side * 101.0, 46)), (panel_len + 10, 2.0, 30), mat("cream_shadow"), 8, 12)
        rounded_box("teal side service panel", off("body", (8, side * 103.2, 46)), (panel_len, 3.6, 24), mat("teal"), 8, 12)
        for x, z in [(-48, 54), (-48, 38), (68, 54), (68, 38)]:
            cylinder("side panel screw", off("body", (x, side * 105.2, z)), 1.3, 1.4, mat("charcoal"), 24, rotation=(math.pi / 2, 0, 0), bevel=0.22)

    # Empty mechanical service bay. These are real body features present in
    # assembled and exploded states; no internal electronics are modeled here.
    rounded_box("empty lower service bay pocket", off("tray", (62, 0, 40)), (142, 66, 6), mat("cream_shadow"), 4, 6)
    for x in (-4, 128):
        rounded_box("service bay end stop", off("tray", (x, 0, 51)), (8, 66, 24), mat("cream_light"), 3, 5)
    for y in (-34, 34):
        rounded_box("service bay alignment rail", off("tray", (62, y, 52)), (142, 5, 22), mat("cream_light"), 2, 4)
    for x, y in [(-108, -68), (-108, 68), (-16, -68), (-16, 68), (34, -48), (34, -16)]:
        cylinder("deck support standoff post", off("tray", (x, y, 51)), 3.4, 24, mat("cream_light"), 28, bevel=0.4)
    for x, y in [(-108, -68), (-108, 68), (-16, -68), (-16, 68), (34, -48), (34, -16), (62, -22), (62, 22)]:
        cylinder("service bay screw bore marker", off("tray", (x, y, 64)), 1.15, 2.0, mat("charcoal"), 20, bevel=0.15)

    # E-stop: top/rear/right, visually obvious and mechanically proud.
    estop = v["estop_scale"]
    estop_x = 70
    estop_y = 0
    cylinder("estop black recessed well", off("deck", (estop_x, estop_y, deck_z + 4)), 23 * estop, 5, mat("black"), 72, bevel=0.7)
    cylinder("estop red stem", off("deck", (estop_x, estop_y, deck_z + 11.8)), 12.5 * estop, 9.4, mat("red"), 72, bevel=0.8)
    cylinder("estop red mushroom cap", off("deck", (estop_x, estop_y, deck_z + 19.6)), 23.5 * estop, 6.8, mat("red"), 96, bevel=2.0)
    cylinder("estop shallow top inset", off("deck", (estop_x, estop_y, deck_z + 23.25)), 15.0 * estop, 0.45, material("red_top_inset", (0.96, 0.18, 0.13, 1.0)), 96, bevel=0.35)

    # Neck and camera head.
    neck_x = -48
    cylinder("neck socket dark deck opening", off("deck", (neck_x, 0, deck_z + 4.0)), 18.5, 2.4, mat("black"), 72, bevel=0.45)
    torus("neck black lower gasket", off("deck", (neck_x, 0, deck_z + 5.0)), 18.8, 2.1, mat("black"))
    cylinder("teal retained neck collar", off("deck", (neck_x, 0, deck_z + 7.0)), 22.0, 3.4, mat("teal"), 72, bevel=0.7)
    neck_top = deck_z + 7.8 + v["neck_h"]
    superellipse_shell(
        "cream smooth flared neck column",
        off("head", (neck_x, 0, 0)),
        [
            (deck_z + 8.0, 15.8, 13.4),
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

    head_center = off("head", (neck_x - 11.5, 0, neck_top + 9.6))
    x_capsule_shell(
        "cream capsule camera head",
        head_center,
        [
            (-v["head_d"] / 2, v["head_w"] / 2 - 7, v["head_h"] / 2 - 5.5),
            (-v["head_d"] / 2 + 4.0, v["head_w"] / 2 + 1.8, v["head_h"] / 2 + 1.5),
            (-8, v["head_w"] / 2 + 4.6, v["head_h"] / 2 + 2.2),
            (8, v["head_w"] / 2 + 4.0, v["head_h"] / 2 + 2.0),
            (v["head_d"] / 2 - 9, v["head_w"] / 2 + 0.5, v["head_h"] / 2 + 0.6),
            (v["head_d"] / 2 - 2.0, v["head_w"] / 2 - 7.5, v["head_h"] / 2 - 4.2),
            (v["head_d"] / 2 + 1.8, v["head_w"] / 2 - 18, v["head_h"] / 2 - 9.5),
        ],
        mat("cream_light"),
        exponent=2.85,
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
        exponent=3.55,
        points=96,
    )
    x_capsule_shell(
        "thin shadow line around black faceplate",
        (face_x - 1.5, 0, head_center[2] - 0.2),
        [
            (-0.9, (v["face_w"] + 0.5) / 2, (v["face_h"] - 0.5) / 2),
            (0.9, (v["face_w"] + 0.5) / 2, (v["face_h"] - 0.5) / 2),
        ],
        mat("cream_shadow"),
        exponent=3.7,
        points=96,
    )
    x_capsule_shell(
        "inset rounded black head faceplate",
        (face_x - 2.0, 0, head_center[2] - 0.2),
        [
            (-1.0, (v["face_w"] - 6) / 2, (v["face_h"] - 3) / 2),
            (1.0, (v["face_w"] - 6) / 2, (v["face_h"] - 3) / 2),
        ],
        mat("charcoal"),
        exponent=3.65,
        points=96,
    )
    cylinder("camera lens outer", (face_x - 5.9, 0, head_center[2] - 0.1), 14.2, 7.0, mat("black"), 80, rotation=(0, math.pi / 2, 0), bevel=0.65)
    cylinder("camera lens satin retaining ring", (face_x - 9.4, 0, head_center[2] - 0.1), 10.9, 2.0, material("lens_ring", (0.035, 0.043, 0.055, 1.0)), 80, rotation=(0, math.pi / 2, 0), bevel=0.35)
    cylinder("camera lens inner barrel", (face_x - 10.8, 0, head_center[2] - 0.1), 8.0, 1.9, mat("black"), 80, rotation=(0, math.pi / 2, 0), bevel=0.3)
    cylinder("camera lens glass", (face_x - 12.0, 0, head_center[2] - 0.1), 5.8, 1.2, material("camera_glass", (0.015, 0.038, 0.07, 1.0)), 72, rotation=(0, math.pi / 2, 0), bevel=0.25)
    cylinder("camera lens blue glint", (face_x - 12.8, -2.4, head_center[2] + 2.7), 1.0, 0.5, material("lens_glint", (0.20, 0.42, 0.82, 1.0)), 24, rotation=(0, math.pi / 2, 0), bevel=0.08)
    for y in (-22.5, 22.5):
        x_capsule_shell(
            "head oval lime eye",
            (face_x - 5.9, y, head_center[2] - 0.2),
            [
                (-1.2, 3.2, 7.0),
                (1.2, 3.2, 7.0),
            ],
            mat("lime"),
            exponent=2.4,
            points=48,
        )
        curve_tube(
            "curved blue brow cap",
            [
                (face_x - 5.4, y - 9, head_center[2] + 11.7),
                (face_x - 5.9, y, head_center[2] + 13.5),
                (face_x - 5.4, y + 9, head_center[2] + 11.7),
            ],
            mat("blue"),
            2.1,
            5,
        )
    for y in (-53, 53):
        rounded_box("subtle head side seam", (head_center[0] + 7, y, head_center[2] + 4), (28, 0.9, 1.8), mat("cream_shadow"), 0.35, 2)

    if safety:
        rounded_box("bumper travel envelope", (-15, 0, 28), (320, 242, 36), mat("safety_teal"), 12, 8)


def look_at(obj: bpy.types.Object, target: tuple[float, float, float]) -> None:
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def setup_camera(view: str) -> None:
    configs = {
        "front_3q": ((-430, -315, 195), (-6, 0, 72), 410),
        "side": ((10, -520, 145), (12, 0, 72), 340),
        "top": ((0, 0, 580), (0, 0, 65), 440),
        "exploded": ((-475, -380, 300), (0, 0, 132), 610),
        "service": ((-475, -375, 285), (0, 0, 120), 580),
        "iteration": ((-430, -315, 195), (-6, 0, 76), 420),
    }
    position, target, scale = configs[view]
    cam_data = bpy.data.cameras.new(f"{view}_camera")
    cam = bpy.data.objects.new(f"{view}_camera", cam_data)
    bpy.context.collection.objects.link(cam)
    cam.location = position
    look_at(cam, target)
    cam_data.type = "ORTHO"
    cam_data.ortho_scale = scale
    cam_data.lens = 70
    bpy.context.scene.camera = cam


def add_lighting() -> None:
    world = bpy.context.scene.world or bpy.data.worlds.new("World")
    bpy.context.scene.world = world
    world.color = (0.965, 0.93, 0.87)

    bpy.ops.object.light_add(type="AREA", location=(-230, -310, 360))
    key = bpy.context.object
    key.name = "large softbox key"
    key.data.energy = 90000
    key.data.size = 230

    bpy.ops.object.light_add(type="AREA", location=(260, 230, 250))
    fill = bpy.context.object
    fill.name = "warm fill"
    fill.data.energy = 28000
    fill.data.size = 320

    bpy.ops.object.light_add(type="POINT", location=(-160, 120, 170))
    face = bpy.context.object
    face.name = "face sparkle"
    face.data.energy = 9000

    bpy.ops.object.light_add(type="SUN", location=(0, 0, 260))
    sun = bpy.context.object
    sun.name = "soft product sun"
    sun.data.energy = 1.8


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
    scene.view_settings.exposure = 0.85
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
