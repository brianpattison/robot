# Python CAD Tooling

## Current v2 pipeline

Use Python 3.12 in a project virtual environment:

```bash
python3.12 -m venv .venv-cad
source .venv-cad/bin/activate
python -m pip install --upgrade pip
python -m pip install -r cad/python/requirements.txt
```

Generate and validate in this order:

```bash
python cad/python/packing_study_printed_only.py
python cad/python/robot_body_v2.py
python cad/python/validate_robot_body_v2.py --gate
python cad/python/robot_body_v2_print.py
python cad/python/robot_body_v2_coupons.py
python cad/bambu/generate_bambu_project_v2.py
python cad/bambu/generate_bambu_coupons_v2.py
python cad/blender/render_robot_body_v2.py
python cad/blender/render_assembly_steps_v2.py
python docs/generate_assembly_guide_v2.py
```

The authoritative registry is `robot_body_v2_inventory.py`. Current tracked
release counts are 40 installed functional parts, four spare washers, one
optional lid skin, 47 M3 joints, 13 body plates, and 18 logical coupons / 19
coupon objects on five plates. `validate_robot_body_v2.py --gate` is necessary
geometry evidence, never electrical, material, fit, or powered-motion evidence.

## v1 dependency boundary

The v2 implementation imports shared `Params` and helpers from `robot_body.py`.
That file is therefore a retained code dependency even though its v1 geometry,
split/print pipeline, 101-part 3MF, and assembly guide are historical. Do not
delete or move it merely to make the tree look v2-only, and do not use the v1
purchase/assembly artifacts for a v2 build. Small v1 reference changes still
require the v1 validator; any shared-parameter change requires the v2 gate too.
Install `cad/python/requirements-v1.txt` only when rebuilding the historical
ReportLab guide; it layers that legacy dependency on the current v2 toolchain.

## Generated artifacts

Meshes, STEP files, and intermediate manifests live under `cad/exports/` and
are ignored. The tracked body/coupon 3MFs, plate manifests, rendered guide
images, HTML, and PDF are deliberate release artifacts and must be regenerated
from source. Never hand-edit a 3MF archive or generated guide.

The Bambu round-trip, Blender renders, Chrome PDF print, visual page review,
coupon printing, and every physical qualification remain explicit local steps;
hosted CI cannot substitute for their native applications, printer, or parts.
