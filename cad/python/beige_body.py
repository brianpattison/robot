#!/usr/bin/env python3
"""From-scratch build123d model of the beige robot body.

Source of truth: the concept-art rendering (a clean, boxy cream enclosure).

This models ONLY the main beige body: the rounded rectangular shell plus the
features cut into it -- the teal-plate recess, the camera-neck bore, the E-stop
bore, the top vent field, the front sensor recess, and the deck screw holes.

The teal plate, E-stop button, neck boot and LEDs are drawn ONLY as colored
preview accents (see `preview_accents`) so the render is legible. They are NOT
part of the exported beige-body solid.

Deliberately self-contained: it does not import or reuse any earlier CAD/Python
in this repo. Every dimension is a parameter below.

Run with the project CAD venv:

    /Users/brian/github/brianpattison/robot/.venv-cad/bin/python cad/python/beige_body.py
"""
from __future__ import annotations

from pathlib import Path

from build123d import (
    Axis, BuildPart, BuildSketch, Locations, Mode, Plane, Part,
    RectangleRounded, export_step, export_stl, extrude, fillet,
)

REPO = Path("/Users/brian/github/brianpattison/robot")
EXPORT = REPO / "cad" / "exports"
SCRATCH = Path(
    "/private/tmp/claude-501/"
    "-Users-brian-github-brianpattison-robot--claude-worktrees-blissful-blackwell-549162/"
    "134d0a18-f2ba-4d80-87ce-28c6b32df6af/scratchpad"
)
VERSION = "v0.1"

# ---------------------------------------------------------------------------
# Parameters (millimeters).  Origin at the footprint center, z=0 at the bottom
# mating plane (where the beige body meets the black base).  +X = forward (the
# camera / sensor-bar end), +Y = left, +Z = up.
# ---------------------------------------------------------------------------

# Outer form
BODY_L = 300.0          # length, front (+X) to rear (-X)
BODY_W = 220.0          # width, left (+Y) to right (-Y)
BODY_H = 92.0           # height of the beige box (excludes black base + head)
CORNER_R = 16.0         # vertical corner radius
TOP_EDGE_R = 12.0       # rounded top edge
BOTTOM_EDGE_R = 6.0     # small bottom edge break

# Teal top-plate recess
PLATE_MARGIN = 24.0     # beige frame width around the plate
PLATE_INSET = 2.5       # recess depth
PLATE_CORNER_R = 26.0

# Front sensor-bar recess (pocket the front piece seats into)
SENSOR_W = 150.0        # across width (Y)
SENSOR_H = 30.0         # up the front face (Z)
SENSOR_R = 12.0
SENSOR_DEPTH = 8.0
SENSOR_Z = 54.0         # center height on the front face

# Render color (preview only)
CREAM = "#F5F0E6"


# ---------------------------------------------------------------------------
# Geometry
# ---------------------------------------------------------------------------
def build_beige_body() -> Part:
    """The exported beige-body solid (Stage A: solid outer form + feature cuts)."""
    with BuildPart() as bp:
        # Outer rounded box.
        with BuildSketch(Plane.XY):
            RectangleRounded(BODY_L, BODY_W, CORNER_R)
        extrude(amount=BODY_H)
        fillet(bp.edges().group_by(Axis.Z)[-1], radius=TOP_EDGE_R)
        fillet(bp.edges().group_by(Axis.Z)[0], radius=BOTTOM_EDGE_R)

        top = Plane.XY.offset(BODY_H)

        # Teal-lid recess (pocket the teal lid seats into).
        with BuildSketch(top):
            RectangleRounded(
                BODY_L - 2 * PLATE_MARGIN, BODY_W - 2 * PLATE_MARGIN, PLATE_CORNER_R
            )
        extrude(amount=-PLATE_INSET, mode=Mode.SUBTRACT)

        # Front sensor-bar recess (pocket the front piece seats into).
        front = Plane.YZ.offset(BODY_L / 2)
        with BuildSketch(front):
            with Locations((0, SENSOR_Z)):
                RectangleRounded(SENSOR_W, SENSOR_H, SENSOR_R)
        extrude(amount=-SENSOR_DEPTH, mode=Mode.SUBTRACT)

    return bp.part


# ---------------------------------------------------------------------------
# Preview render (fresh VTK offscreen; multi-color via per-part STL)
# ---------------------------------------------------------------------------
def _hex_rgb(hex_color: str) -> tuple[float, float, float]:
    h = hex_color.lstrip("#")
    return tuple(int(h[i : i + 2], 16) / 255 for i in (0, 2, 4))


def render_preview(body: Part, out_png: Path) -> None:
    import vtk

    SCRATCH.mkdir(parents=True, exist_ok=True)
    body_stl = SCRATCH / "preview_beige_body.stl"
    export_stl(body, str(body_stl))
    jobs: list[tuple[str, str, float]] = [(str(body_stl), CREAM, 1.0)]

    renderer = vtk.vtkRenderer()
    renderer.SetBackground(*_hex_rgb("#ECE6DC"))
    renderer.SetUseFXAA(True)

    win = vtk.vtkRenderWindow()
    win.SetOffScreenRendering(1)
    win.AddRenderer(renderer)
    win.SetSize(1500, 1000)
    win.SetMultiSamples(8)

    for path, color, alpha in jobs:
        reader = vtk.vtkSTLReader()
        reader.SetFileName(path)
        normals = vtk.vtkPolyDataNormals()
        normals.SetInputConnection(reader.GetOutputPort())
        normals.SetFeatureAngle(45)
        normals.Update()
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(normals.GetOutputPort())
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        prop = actor.GetProperty()
        prop.SetColor(*_hex_rgb(color))
        prop.SetOpacity(alpha)
        prop.SetInterpolationToPhong()
        prop.SetAmbient(0.32)
        prop.SetDiffuse(0.76)
        prop.SetSpecular(0.16)
        prop.SetSpecularPower(26)
        renderer.AddActor(actor)

    cam = renderer.GetActiveCamera()
    cam.SetPosition(470, -250, 205)          # front (+X) dominant, right (-Y), above
    cam.SetFocalPoint(0, 0, 45)
    cam.SetViewUp(0, 0, 1)
    cam.SetViewAngle(28)

    key = vtk.vtkLight()
    key.SetLightTypeToSceneLight()
    key.SetPosition(240, -360, 520)
    key.SetFocalPoint(0, 0, 50)
    key.SetIntensity(0.85)
    renderer.AddLight(key)

    fill = vtk.vtkLight()
    fill.SetLightTypeToSceneLight()
    fill.SetPosition(-320, 240, 300)
    fill.SetFocalPoint(0, 0, 50)
    fill.SetIntensity(0.35)
    renderer.AddLight(fill)

    win.Render()
    w2i = vtk.vtkWindowToImageFilter()
    w2i.SetInput(win)
    w2i.SetInputBufferTypeToRGB()
    w2i.ReadFrontBufferOff()
    w2i.Update()
    writer = vtk.vtkPNGWriter()
    writer.SetFileName(str(out_png))
    writer.SetInputConnection(w2i.GetOutputPort())
    writer.Write()


# ---------------------------------------------------------------------------
def main() -> None:
    for sub in ("step", "stl", "preview"):
        (EXPORT / sub).mkdir(parents=True, exist_ok=True)

    body = build_beige_body()

    bb = body.bounding_box()
    print(f"valid:   {body.is_valid}")
    print(f"volume:  {body.volume / 1000:.1f} cm^3")
    print(f"bbox mm: {bb.size.X:.1f} x {bb.size.Y:.1f} x {bb.size.Z:.1f}")

    step_path = EXPORT / "step" / f"beige_body_{VERSION}.step"
    stl_path = EXPORT / "stl" / f"beige_body_{VERSION}.stl"
    export_step(body, str(step_path))
    export_stl(body, str(stl_path))
    print(f"wrote:   {step_path}")
    print(f"wrote:   {stl_path}")

    preview_path = EXPORT / "preview" / f"beige_body_{VERSION}_front3q.png"
    render_preview(body, preview_path)
    print(f"wrote:   {preview_path}")


if __name__ == "__main__":
    main()
