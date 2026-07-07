#!/usr/bin/env python3
"""Python CAD concept pass for the Codex Rover Bean finished shell.

This is a visual/packaging iteration, not the release manufacturing model.  It
keeps the OpenSCAD v0 envelope and component keepouts while moving the outer
language closer to docs/images/codex_body_finished_concept.png.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import cadquery as cq
from PIL import Image, ImageDraw, ImageFont
import vtk


OUT = Path("docs/images")
REF = OUT / "codex_body_finished_concept.png"


COLORS = {
    "cream": "#F5EAD8",
    "cream_shadow": "#E8D6BB",
    "teal": "#10AEB4",
    "teal_dark": "#0A7880",
    "charcoal": "#202229",
    "bumper": "#25272C",
    "black": "#090A0C",
    "rubber": "#111216",
    "blue": "#2462D9",
    "lime": "#C7FF5E",
    "red": "#D92F27",
    "metal": "#777A80",
    "pi": "#20242B",
    "battery": "#3B3D42",
    "wire_red": "#B72E28",
}


# Mechanical contract from the current OpenSCAD v0 parameters.
BASE_LEN = 300.0
BASE_W = 220.0
BODY_H = 54.0
WHEEL_D = 80.0
WHEEL_W = 24.0
AXLE_X = 145.0
AXLE_Z = 42.0
WHEEL_CLEARANCE = 5.0
DECK_Z = 82.0

PI_LEN = 85.0
PI_W = 56.0
PI_H = 14.0
HAT_KEEP_H = 46.0
BATTERY_LEN = 110.0
BATTERY_W = 38.0
BATTERY_H = 38.0


@dataclass
class Part:
    name: str
    shape: cq.Shape
    color: str
    group: str = "body"
    alpha: float = 1.0


def hex_to_rgb(hex_color: str) -> tuple[float, float, float]:
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i : i + 2], 16) / 255 for i in (0, 2, 4))


def label_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for font_path in (
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ):
        if Path(font_path).exists():
            return ImageFont.truetype(font_path, size)
    return ImageFont.load_default()


def as_shape(obj: cq.Workplane | cq.Shape) -> cq.Shape:
    return obj.val() if isinstance(obj, cq.Workplane) else obj


def translate(obj: cq.Workplane | cq.Shape, loc: tuple[float, float, float]) -> cq.Shape:
    return as_shape(obj).translate(cq.Vector(*loc))


def rounded_box(
    size: tuple[float, float, float],
    radius: float,
    loc: tuple[float, float, float],
    vertical_only: bool = False,
) -> cq.Shape:
    wp = cq.Workplane("XY").box(*size)
    if radius > 0:
        try:
            edge_selector = "|Z" if vertical_only else None
            wp = wp.edges(edge_selector).fillet(radius) if edge_selector else wp.edges().fillet(radius)
        except Exception:
            wp = cq.Workplane("XY").box(*size).edges("|Z").fillet(min(radius, size[0] / 4, size[1] / 4))
    return translate(wp, loc)


def cyl(
    radius: float,
    height: float,
    center: tuple[float, float, float],
    axis: tuple[float, float, float] = (0, 0, 1),
) -> cq.Shape:
    axis_v = cq.Vector(*axis).normalized()
    base = cq.Vector(*center) - axis_v.multiply(height / 2)
    return cq.Solid.makeCylinder(radius, height, pnt=base, dir=axis_v)


def cone(
    r1: float,
    r2: float,
    height: float,
    center: tuple[float, float, float],
    axis: tuple[float, float, float] = (0, 0, 1),
) -> cq.Shape:
    axis_v = cq.Vector(*axis).normalized()
    base = cq.Vector(*center) - axis_v.multiply(height / 2)
    return cq.Solid.makeCone(r1, r2, height, pnt=base, dir=axis_v)


def fender(side: int) -> cq.Shape:
    """Cream half-arch wheel guard, axis along Y."""
    y = side * (BASE_W / 2 + WHEEL_W / 2 - 5)
    center = (218, y, AXLE_Z)
    outer = cyl(55, 30, center, (0, 1, 0))
    inner = cyl(42, 34, center, (0, 1, 0))
    lower_cut = rounded_box((126, 42, 76), 2, (218, y, AXLE_Z - 39), vertical_only=True)
    rear_cut = rounded_box((42, 42, 130), 2, (274, y, AXLE_Z + 4), vertical_only=True)
    return outer.cut(inner).cut(lower_cut).cut(rear_cut)


def screw_heads_on_deck() -> list[Part]:
    locs = [(54, -70, DECK_Z + 5), (54, 70, DECK_Z + 5), (226, -70, DECK_Z + 5), (226, 70, DECK_Z + 5)]
    return [Part("deck screw", cyl(3.2, 1.5, loc), COLORS["charcoal"], "deck") for loc in locs]


def build_parts(exploded: bool = False, service: bool = False, safety: bool = False) -> list[Part]:
    offsets = {
        "bumper": (0, 0, -34 if exploded else 0),
        "tray": (0, 0, -16 if exploded else 0),
        "shell": (0, 0, 0),
        "internal": (0, 0, 28 if exploded else 0),
        "deck": (0, 0, 58 if exploded or service else 0),
        "estop": (0, 0, 92 if exploded or service else 0),
        "head": (0, 0, 120 if exploded or service else 0),
        "wheel": (0, 0, -8 if exploded else 0),
        "safety": (0, 0, 0),
    }

    def off(group: str, loc: tuple[float, float, float]) -> tuple[float, float, float]:
        ox, oy, oz = offsets[group]
        return (loc[0] + ox, loc[1] + oy, loc[2] + oz)

    parts: list[Part] = []

    # Lower cream tray and appliance shell.
    parts.append(
        Part(
            "lower tray",
            rounded_box((284, 194, 18), 18, off("tray", (150, 0, 18))),
            COLORS["cream_shadow"],
            "tray",
        )
    )
    shell_outer = rounded_box((292, 206, BODY_H), 24, off("shell", (150, 0, 50)))
    if exploded or service:
        shell_opening = rounded_box((220, 148, 90), 10, off("shell", (164, 0, 77)))
        parts.append(Part("cream open service shell", shell_outer.cut(shell_opening), COLORS["cream"], "shell"))
        for name, loc, size in [
            ("cream top left rim", (152, -88, 79), (248, 18, 10)),
            ("cream top right rim", (152, 88, 79), (248, 18, 10)),
            ("cream top front rim", (42, 0, 79), (82, 176, 10)),
            ("cream top rear rim", (266, 0, 79), (54, 176, 10)),
        ]:
            parts.append(Part(name, rounded_box(size, 8, off("shell", loc)), COLORS["cream"], "shell"))
    else:
        deck_aperture = rounded_box((222, 144, 80), 16, off("shell", (158, 0, 62)))
        parts.append(Part("cream body shell with deck aperture", shell_outer.cut(deck_aperture), COLORS["cream"], "shell"))
        for name, loc, size in [
            ("cream top left rim", (152, -88, 79), (248, 18, 10)),
            ("cream top right rim", (152, 88, 79), (248, 18, 10)),
            ("cream top front rim", (42, 0, 79), (82, 176, 10)),
            ("cream top rear rim", (266, 0, 79), (54, 176, 10)),
        ]:
            parts.append(Part(name, rounded_box(size, 8, off("shell", loc)), COLORS["cream"], "shell"))

    # Front nose inserts.
    parts.append(
        Part(
            "black front sensor band",
            rounded_box((10, 166, 18), 7, off("shell", (4, 0, 45))),
            COLORS["black"],
            "shell",
        )
    )
    parts.append(
        Part(
            "front top black vent panel",
            rounded_box((78, 138, 5), 8, off("shell", (48, 0, DECK_Z + 2))),
            COLORS["charcoal"],
            "shell",
        )
    )
    for y in (-60, 60):
        parts.append(Part("front lime light", rounded_box((4, 24, 9), 3, off("shell", (-1, y, 45))), COLORS["lime"], "shell"))
    for y, r in [(-20, 6), (0, 4), (22, 7)]:
        parts.append(Part("front sensor lens", cyl(r, 3.5, off("shell", (-3, y, 45)), (1, 0, 0)), COLORS["charcoal"], "shell"))

    # Soft segmented bumper and side rails.
    for name, loc, size in [
        ("front bumper center", (0, 0, 25), (30, 118, 28)),
        ("front bumper left", (10, -81, 25), (34, 58, 28)),
        ("front bumper right", (10, 81, 25), (34, 58, 28)),
        ("side rail left", (145, -116, 23), (220, 18, 24)),
        ("side rail right", (145, 116, 23), (220, 18, 24)),
    ]:
        parts.append(Part(name, rounded_box(size, 12, off("bumper", loc)), COLORS["bumper"], "bumper"))

    # Wheels, hubs, fenders, side panels.
    for side in (-1, 1):
        wheel_y = side * (BASE_W / 2 + WHEEL_W / 2 + WHEEL_CLEARANCE)
        parts.append(Part("wheel tire", cyl(WHEEL_D / 2, WHEEL_W, off("wheel", (218, wheel_y, AXLE_Z)), (0, 1, 0)), COLORS["rubber"], "wheel"))
        parts.append(Part("cream wheel hub", cyl(25, WHEEL_W + 3, off("wheel", (218, wheel_y + side * 0.5, AXLE_Z)), (0, 1, 0)), COLORS["cream"], "wheel"))
        parts.append(Part("teal wheel ring", cyl(31, 3.5, off("wheel", (218, wheel_y - side * 13, AXLE_Z)), (0, 1, 0)), COLORS["teal"], "wheel"))
        parts.append(Part("cream fender", fender(side).translate(cq.Vector(*offsets["wheel"])), COLORS["cream"], "wheel"))
        parts.append(Part("teal side service panel", rounded_box((82, 4, 26), 6, off("shell", (172, side * 104, 44))), COLORS["teal_dark"], "shell"))
        for sx in (142, 202):
            parts.append(Part("side panel screw", cyl(2.2, 2, off("shell", (sx, side * 107, 51)), (0, 1, 0)), COLORS["charcoal"], "shell"))

    # Internal fit evidence.
    if exploded or service:
        parts.append(Part("battery pack", rounded_box((112, 42, 34), 5, off("internal", (218, 0, 54))), COLORS["battery"], "internal"))
        for x in (190, 246):
            parts.append(Part("battery strap", rounded_box((8, 48, 38), 2, off("internal", (x, 0, 55))), COLORS["black"], "internal"))
        parts.append(Part("pi board", rounded_box((86, 58, 4), 3, off("internal", (102, 6, 68))), "#2E7D51", "internal"))
        parts.append(Part("pi keepout", rounded_box((85, 56, HAT_KEEP_H), 3, off("internal", (102, 6, 93))), "#A6C8FF", "internal", alpha=0.18))
        parts.append(Part("motor controller", rounded_box((58, 42, 8), 3, off("internal", (150, -48, 68))), COLORS["pi"], "internal"))
        parts.append(Part("battery wire red", rounded_box((58, 4, 4), 1, off("internal", (172, -22, 60))), COLORS["wire_red"], "internal"))

    # Teal removable top deck with vents and screw language.
    deck_shape = rounded_box((226, 148, 8), 18, off("deck", (158, 0, DECK_Z)))
    parts.append(Part("teal top service deck", deck_shape, COLORS["teal"], "deck"))
    for y in (-24, -12, 0, 12, 24):
        parts.append(Part("deck vent slot", rounded_box((42, 4, 2), 1.5, off("deck", (152, y, DECK_Z + 4))), COLORS["charcoal"], "deck"))
    parts.extend([Part(p.name, p.shape.translate(cq.Vector(*offsets["deck"])), p.color, p.group, p.alpha) for p in screw_heads_on_deck()])

    # E-stop assembly.
    parts.append(Part("estop black collar", cyl(19, 8, off("estop", (234, 45, DECK_Z + 8))), COLORS["black"], "estop"))
    parts.append(Part("estop stem", cyl(14, 16, off("estop", (234, 45, DECK_Z + 20))), "#A8231F", "estop"))
    parts.append(Part("estop red cap", cyl(25, 13, off("estop", (234, 45, DECK_Z + 35))), COLORS["red"], "estop"))

    # Neck, collar, and cream camera head.
    neck_x = 112
    parts.append(Part("neck black lower collar", cyl(25, 8, off("head", (neck_x, 0, DECK_Z + 7))), COLORS["black"], "head"))
    parts.append(Part("neck teal collar", cyl(32, 5, off("head", (neck_x, 0, DECK_Z + 10))), COLORS["teal_dark"], "head"))
    parts.append(Part("cream neck pedestal", cone(17, 13, 54, off("head", (neck_x, 0, DECK_Z + 40))), COLORS["cream_shadow"], "head"))

    head_center = off("head", (86, 0, 176))
    parts.append(Part("cream head shell", rounded_box((62, 110, 58), 16, head_center), COLORS["cream"], "head"))
    parts.append(Part("black faceplate", rounded_box((5, 88, 40), 8, off("head", (53, 0, 176))), COLORS["charcoal"], "head"))
    parts.append(Part("camera lens outer", cyl(15, 9, off("head", (36, 0, 176)), (1, 0, 0)), COLORS["black"], "head"))
    parts.append(Part("camera lens ring", cyl(11, 4, off("head", (31, 0, 176)), (1, 0, 0)), "#2B2E35", "head"))
    parts.append(Part("camera glass", cyl(7, 2, off("head", (28, 0, 176)), (1, 0, 0)), "#1E2630", "head"))
    for y in (-28, 28):
        parts.append(Part("head lime eye", rounded_box((5, 13, 22), 4, off("head", (33, y, 176))), COLORS["lime"], "head"))
        parts.append(Part("blue brow", rounded_box((8, 32, 8), 3, off("head", (34, y, 196))), COLORS["blue"], "head"))

    if safety:
        # Transparent evidence envelopes for review renders.
        parts.append(Part("bumper travel envelope", rounded_box((316, 236, 34), 22, (150, 0, 27)), COLORS["teal"], "safety", alpha=0.12))
        parts.append(Part("pi hat keepout", rounded_box((85, 56, HAT_KEEP_H), 2, (102, 6, 98)), "#2F6BFF", "safety", alpha=0.18))
        parts.append(Part("battery keepout", rounded_box((128, 56, 44), 3, (218, 0, 54)), COLORS["orange"] if "orange" in COLORS else COLORS["red"], "safety", alpha=0.2))

    return parts


def tessellate_part(part: Part, tolerance: float = 0.9) -> tuple[list[tuple[float, float, float]], list[tuple[int, int, int]]]:
    verts, tris = part.shape.tessellate(tolerance)
    pts = [(v.x, v.y, v.z) for v in verts]
    return pts, [(int(a), int(b), int(c)) for a, b, c in tris]


def add_vtk_actor(renderer: vtk.vtkRenderer, part: Part) -> None:
    pts, tris = tessellate_part(part)
    if not tris:
        return

    vtk_points = vtk.vtkPoints()
    vtk_points.SetNumberOfPoints(len(pts))
    for idx, point in enumerate(pts):
        vtk_points.SetPoint(idx, point)

    cells = vtk.vtkCellArray()
    for tri in tris:
        cells.InsertNextCell(3)
        for point_idx in tri:
            cells.InsertCellPoint(point_idx)

    poly = vtk.vtkPolyData()
    poly.SetPoints(vtk_points)
    poly.SetPolys(cells)

    normals = vtk.vtkPolyDataNormals()
    normals.SetInputData(poly)
    normals.ConsistencyOn()
    normals.SplittingOff()
    normals.Update()

    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(normals.GetOutputPort())

    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    prop = actor.GetProperty()
    prop.SetColor(*hex_to_rgb(part.color))
    prop.SetOpacity(part.alpha)
    prop.SetInterpolationToPhong()
    prop.SetAmbient(0.34)
    prop.SetDiffuse(0.72)
    prop.SetSpecular(0.16)
    prop.SetSpecularPower(24)
    renderer.AddActor(actor)


def render(
    parts: Iterable[Part],
    out: Path,
    view: str,
    title: str,
) -> None:
    view_cfg = {
        "front_3q": ((-310, -250, 165), (146, 0, 78), (0, 0, 1), 172),
        "side": ((150, -520, 135), (150, 0, 72), (0, 0, 1), 155),
        "top": ((150, 0, 620), (150, 0, 58), (0, 1, 0), 150),
        "front": ((-520, 0, 120), (145, 0, 68), (0, 0, 1), 150),
        "exploded": ((-330, -290, 250), (148, 0, 142), (0, 0, 1), 245),
    }
    position, focal_point, view_up, parallel_scale = view_cfg[view]

    renderer = vtk.vtkRenderer()
    renderer.SetBackground(*hex_to_rgb("#F6EFE5"))
    renderer.SetUseFXAA(True)

    render_window = vtk.vtkRenderWindow()
    render_window.SetOffScreenRendering(1)
    render_window.AddRenderer(renderer)
    render_window.SetSize(1400, 900)
    render_window.SetMultiSamples(8)

    for part in parts:
        add_vtk_actor(renderer, part)

    camera = renderer.GetActiveCamera()
    camera.SetPosition(*position)
    camera.SetFocalPoint(*focal_point)
    camera.SetViewUp(*view_up)
    camera.ParallelProjectionOn()
    camera.SetParallelScale(parallel_scale)

    key_light = vtk.vtkLight()
    key_light.SetLightTypeToSceneLight()
    key_light.SetPosition(-280, -360, 420)
    key_light.SetFocalPoint(130, 0, 65)
    key_light.SetIntensity(0.78)
    renderer.AddLight(key_light)

    fill_light = vtk.vtkLight()
    fill_light.SetLightTypeToSceneLight()
    fill_light.SetPosition(360, 300, 260)
    fill_light.SetFocalPoint(150, 0, 70)
    fill_light.SetIntensity(0.34)
    renderer.AddLight(fill_light)

    render_window.Render()

    image_filter = vtk.vtkWindowToImageFilter()
    image_filter.SetInput(render_window)
    image_filter.SetInputBufferTypeToRGB()
    image_filter.ReadFrontBufferOff()
    image_filter.Update()

    writer = vtk.vtkPNGWriter()
    writer.SetFileName(str(out))
    writer.SetInputConnection(image_filter.GetOutputPort())
    writer.Write()

    image = Image.open(out).convert("RGB")
    d = ImageDraw.Draw(image)
    d.text((38, 28), title, fill="#22242A", font=label_font(24))
    image.save(out)


def make_comparison(render_path: Path, out: Path) -> None:
    ref = Image.open(REF).convert("RGB")
    cad = Image.open(render_path).convert("RGB")
    target_h = 760
    ref = ref.resize((int(ref.width * target_h / ref.height), target_h))
    cad = cad.resize((int(cad.width * target_h / cad.height), target_h))
    pad = 28
    title_h = 56
    canvas = Image.new("RGB", (ref.width + cad.width + pad * 3, target_h + title_h + pad), "#F6EFE5")
    canvas.paste(ref, (pad, title_h))
    canvas.paste(cad, (ref.width + pad * 2, title_h))
    d = ImageDraw.Draw(canvas)
    font = label_font(18)
    d.text((pad, 20), "Concept art reference", fill="#22242A", font=font)
    d.text((ref.width + pad * 2, 20), "Latest Python CAD render", fill="#22242A", font=font)
    canvas.save(out)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    render(build_parts(), OUT / "codex_body_python_cad_front_3q.png", "front_3q", "Python CAD concept pass - front three-quarter")
    render(build_parts(), OUT / "codex_body_python_cad_side.png", "side", "Python CAD concept pass - side packaging")
    render(build_parts(), OUT / "codex_body_python_cad_top.png", "top", "Python CAD concept pass - top service deck")
    render(build_parts(exploded=True), OUT / "codex_body_python_cad_exploded_fit.png", "exploded", "Python CAD concept pass - exploded fit")
    render(build_parts(service=True), OUT / "codex_body_python_cad_service_top_off.png", "exploded", "Python CAD concept pass - top-off service")
    render(build_parts(safety=True), OUT / "codex_body_python_cad_safety_review.png", "front_3q", "Python CAD concept pass - safety review overlays")
    make_comparison(OUT / "codex_body_python_cad_front_3q.png", OUT / "codex_body_python_cad_concept_comparison.png")
    print("generated:")
    for p in sorted(OUT.glob("codex_body_python_cad_*.png")):
        print(f"  {p}")


if __name__ == "__main__":
    main()
