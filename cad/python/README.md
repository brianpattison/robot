# Python CAD Tooling

This folder is for parametric Python CAD models used by the robot body.

Use this path when a part is awkward in OpenSCAD, especially:

- Curved shells.
- High-quality fillets and chamfers.
- STEP exports.
- Mating surfaces that need BREP geometry.
- Assemblies that benefit from Python data structures.

## Recommended Setup

Current Python CAD packages need a newer Python than the macOS system Python in this workspace.

Recommended local setup:

```bash
python3.12 -m venv .venv-cad
source .venv-cad/bin/activate
python -m pip install --upgrade pip
python -m pip install -r cad/python/requirements.txt
```

Python 3.11 or 3.12 is the conservative target for this project. Use a virtual environment so CAD dependencies do not leak into the system Python installation.

## Source And Exports

- Keep editable Python CAD source in `cad/python/`.
- Keep generated meshes and solids in `cad/exports/`.
- Treat generated `.stl` and `.step` files as build outputs unless we decide otherwise.

## Concept Body Pass

`cad/python/concept_body.py` is the current CadQuery/VTK visual packaging pass for matching the finished concept art more closely than the first OpenSCAD body. It writes PNG review renders to `docs/images/`:

```bash
source .venv-cad/bin/activate
python cad/python/concept_body.py
```

Those PNGs are concept-review artifacts. Use them to compare silhouette, color placement, and service layering before turning the shapes into print-ready parts or STEP exports.
