# Robot

An embodied Codex companion project: a small indoor robot body that can listen, talk, look around, and move safely through the house.

The design goal is pet-like presence without overcomplicating the first build. The MVP is a compact wheeled robot with a camera head, microphone array, speaker, LEDs, bumpers, conservative autonomy, and a physical E-stop. Tiny body, serious safety shoes.

## Current Status

This repo is at the planning and parametric CAD-prototype stage. Start with the docs index:

- Documentation index: [`docs/README.md`](docs/README.md)
- MVP PRD: [`docs/mvp-prd.md`](docs/mvp-prd.md)
- Decision log: [`docs/decision-log.md`](docs/decision-log.md)
- MVP architecture: [`docs/mvp-architecture.md`](docs/mvp-architecture.md)
- BOM v0: [`docs/bom-v0.md`](docs/bom-v0.md)
- CAD mechanical plan: [`docs/cad-mechanical-plan.md`](docs/cad-mechanical-plan.md)
- CAD v1 body and renders: [`docs/cad-v1-body.md`](docs/cad-v1-body.md)
- CAD component/release coverage: [`docs/cad-component-coverage.md`](docs/cad-component-coverage.md)
- CAD calibration coupons: [`docs/cad-coupons.md`](docs/cad-coupons.md)
- Python CAD tooling notes: [`cad/python/README.md`](cad/python/README.md)
- Bambu Studio P1S project: [`cad/bambu/README.md`](cad/bambu/README.md)
- Illustrated assembly guide: [`output/pdf/codex_robot_body_v1_assembly_guide.pdf`](output/pdf/codex_robot_body_v1_assembly_guide.pdf)
- Assembly-guide generator: [`docs/generate_assembly_guide.py`](docs/generate_assembly_guide.py)

## MVP Direction

- Existing Raspberry Pi 5 8GB as the main computer.
- No AI HAT+ 2 required for MVP; reserve room to add it later for local AI experiments.
- Raspberry Pi Camera Module 3 Wide for the main head camera.
- Wheeled differential-drive base for the first physical body.
- Pan/tilt camera head for expression and perception.
- Physical E-stop, bumper switches, watchdog, velocity limits, and conservative movement defaults.
- Local dashboard for health, logs, camera preview, manual drive, and emergency stop.

## Safety First

The robot should fail stopped. Codex should issue high-level intents like `come here`, `follow`, or `stop`, not raw unbounded motor commands.

The safety controller and navigation layer must be able to reject or clamp movement commands. Motor power must be cut by a physical E-stop independent of the Raspberry Pi.

## CAD Strategy

The body is designed around 3D-printable, modular parts:

- Base tray.
- Sensor pods.
- Bumper carrier.
- Tray-fixed bumper-switch plates and switch-body pockets.
- Battery cradle.
- Wheel guards.
- Camera/head shell.
- Service panels.

The current body is implemented in `build123d` because the rounded shell,
service interfaces, STEP exports, and collision-checked assembly benefit from
Python BREP geometry. OpenSCAD remains approved for simple parametric parts.
Blender renders the generated STL inventory for concept, fit, split, and print
review, including the fixed-plate versus compliant-TPU bumper interface; it is
not a second source of body geometry.

Generated mesh/solid exports should go under `cad/exports/` and are ignored by Git by default.
The settled print target is a Bambu Lab P1S with a 0.4 mm nozzle. The tracked
multi-plate Bambu Studio project is regenerated from the canonical exports in
`cad/bambu/`; it is the intentional exception to the generated-mesh ignore rule.

## Python CAD Setup

The macOS system Python in this workspace is older than current Python CAD packages expect, so use a newer Homebrew Python and a project virtual environment.

Recommended:

```bash
brew install python@3.12
/opt/homebrew/bin/python3.12 -m venv .venv-cad
source .venv-cad/bin/activate
python -m pip install --upgrade pip
python -m pip install -r cad/python/requirements.txt
```

## Repo Layout

```text
.
|-- cad/
|   |-- bambu/
|   |   |-- README.md
|   |   |-- generate_bambu_project.py
|   |   |-- codex_robot_body_v1_p1s.3mf
|   |   `-- codex_robot_body_v1_p1s_plates.json
|   |-- blender/
|   |   |-- render_robot_body.py
|   |   |-- render_print_ready.py
|   |   |-- render_coupons.py
|   |   `-- render_alignment_pilot.py
|   `-- python/
|       |-- README.md
|       |-- requirements.txt
|       |-- robot_body.py
|       |-- robot_body_split.py
|       |-- robot_body_print.py
|       |-- robot_body_coupons.py
|       `-- validate_robot_body.py
|-- docs/
|   |-- README.md
|   |-- bom-v0.md
|   |-- cad-v1-body.md
|   |-- cad-component-coverage.md
|   |-- cad-coupons.md
|   |-- images/
|   |-- cad-mechanical-plan.md
|   |-- decision-log.md
|   |-- mvp-architecture.md
|   `-- mvp-prd.md
|-- .gitignore
`-- README.md
```

## Next Steps

1. Print and measure the P1S calibration coupons before committing to large body parts.
2. Buy the bench-brain and safety-prototype batch from [`docs/bom-v0.md`](docs/bom-v0.md).
3. Print and measure the seventeen-part calibration suite, including the 6807 pan-bearing seat/journal block, exact three-piece split-pilot, three-piece tray/PETG/TPU bumper-interface, two-piece flush-fairing recess test, and production-derived distribution-board fit gauge, before any large chassis part or PCB order.
4. Purchase and bench-check one Pololu #4867 motor plus one BLF-1203AB/BPC-1502DC/EN2 charge set, then the selected Hitec head hardware, IDEC XW1E E-stop, two Omron D2HW bumper switches, both Pololu regulators, the E-Switch PVB3F230SS311 physical-mute switch, and one Switchcraft 35RASMT5CHNTRX service jack. Print the distribution cover and exact one-piece 40 x 21 mm board/hardware gauge, then trial-assemble them on the deck before ordering the four-holder Nano2/Micro-Fit PCB. Qualify fit, current, runtime, charger inhibit, fusing/crimps/selective faults/thermal behavior, and safety/privacy/service interfaces before buying the remaining mobility/safety set or powering both motors.
5. Print representative harness, seam, motor-pod, idler, camera, vent, and acoustic parts before a full shell.
6. Build the stationary bench brain and deterministic safety loop before powering drive motors.
