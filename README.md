# Robot

An embodied Codex companion project: a small indoor robot body that can listen, talk, look around, and move safely through the house.

The design goal is pet-like presence without overcomplicating the first build. The MVP is a compact wheeled robot with a camera head, microphone array, speaker, LEDs, bumpers, conservative autonomy, and a physical E-stop. Tiny body, serious safety shoes.

## Current Status

The current direction is the **v2 printed-only hybrid-material body** (decision
log D025-D034): 40 installed functional pieces, four spare washers, and one
optional cosmetic lid skin on 13 zero-support plates, with one screw size and
one insert size.

> **Prototype assembly preview — do not use for powered motion.** The tracked v2
> 3MF and builder's book are geometry and dry-assembly artifacts. The head/neck
> load paths, executable harness schedule, released fuse values, Pi/Pico software,
> and commissioning evidence are still open.

- **The Builder's Book (v2 prototype preview):** [`output/pdf/codex_robot_body_v2_assembly_guide.pdf`](output/pdf/codex_robot_body_v2_assembly_guide.pdf)
- v2 Bambu Studio project: [`cad/bambu/codex_robot_body_v2_p1s.3mf`](cad/bambu/codex_robot_body_v2_p1s.3mf)
- v2 book generator: [`docs/generate_assembly_guide_v2.py`](docs/generate_assembly_guide_v2.py)

Visible replaceable panels and diffusers now use configurable PLA theme slots;
functional PETG is restricted to white structure, black wear parts, and red
service retainers. The shell and head remain white-PETG fallbacks until the
exact candidate PLA family passes the recorded physical gates (D034).

Everything below the book is the engineering paper trail and the current source
of truth for open release gates. Start with the docs index:

- Documentation index: [`docs/README.md`](docs/README.md)
- MVP PRD: [`docs/mvp-prd.md`](docs/mvp-prd.md)
- Decision log: [`docs/decision-log.md`](docs/decision-log.md)
- MVP architecture: [`docs/mvp-architecture.md`](docs/mvp-architecture.md)
- Agentic control plan: [`docs/agentic-control-plan.md`](docs/agentic-control-plan.md)
- BOM v0: [`docs/bom-v0.md`](docs/bom-v0.md)
- Retail sourcing policy: [`docs/retail-sourcing-policy.md`](docs/retail-sourcing-policy.md)
- CAD mechanical plan: [`docs/cad-mechanical-plan.md`](docs/cad-mechanical-plan.md)
- CAD v1 body and renders: [`docs/cad-v1-body.md`](docs/cad-v1-body.md)
- CAD component/release coverage: [`docs/cad-component-coverage.md`](docs/cad-component-coverage.md)
- CAD calibration coupons: [`docs/cad-coupons.md`](docs/cad-coupons.md)
- Python CAD tooling notes: [`cad/python/README.md`](cad/python/README.md)
- Bambu Studio P1S project: [`cad/bambu/README.md`](cad/bambu/README.md)
- v1 illustrated assembly guide (historical): [`output/pdf/codex_robot_body_v1_assembly_guide.pdf`](output/pdf/codex_robot_body_v1_assembly_guide.pdf)
- v1 assembly-guide generator (historical): [`docs/generate_assembly_guide.py`](docs/generate_assembly_guide.py)

## MVP Direction

- Existing Raspberry Pi 5 8GB as the main computer.
- No AI HAT+ 2 required for MVP; reserve room to add it later for local AI experiments.
- Raspberry Pi Camera Module 3 Wide for the main head camera.
- Wheeled differential-drive base for the first physical body.
- Pan/tilt camera head for expression and perception.
- Physical E-stop, bumper switches, watchdog, velocity limits, and conservative movement defaults.
- The resident agent (Claude or Codex) owns the robot's computer: live SSH, code on the fly, package installs, and direct motion setpoints above a firmware safety floor it cannot alter (D030-D032).
- Local dashboard for health, logs, camera preview, manual drive, emergency stop, and the agent panel.
- Quantity-one US retail hardware throughout the production design: Panasonic CB1A-R-M-12V motor-cut relay, Blue Sea Systems 5045 covered fuse block, WDS 615-M6-8-65 front shoulder bolts with stock hardware, no carry handles, and a blank center rear cartridge.

## Safety First

The robot should fail stopped. The resident agent (Claude or Codex) has full authority over the robot's computer — live SSH, code written on the fly, package installs, direct motion setpoints — but not over physics: the safety MCU firmware clamps every velocity setpoint and latches stops on bumper, E-stop, watchdog, or charger events, and it cannot be reflashed from the Pi (D030-D032, [`docs/agentic-control-plan.md`](docs/agentic-control-plan.md)).

Motor power must be cut by a physical E-stop independent of the Raspberry Pi. Root on the Pi is not root on physics.

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
3. Print and measure the applicable calibration suite, including the 6807 pan-bearing seat/journal block, exact three-piece split-pilot, three-piece tray/PETG/TPU bumper-interface, two-piece flush-fairing recess test, and the production-derived Blue Sea 5045 fit gauge before any large chassis part.
4. Purchase and bench-check one Pololu #4867 motor plus one BLF-1203AB/BPC-1502DC/EN2 charge set, then the selected Hitec head hardware, IDEC XW1E E-stop, two Omron D2HW bumper switches, both Pololu regulators, the Panasonic CB1A-R-M-12V relay, Blue Sea Systems 5045 fuse block, WDS 615-M6-8-65 shoulder-bolt hardware, and E-Switch PVB3F230SS311 physical-mute switch. Qualify delivered fit, current, runtime, charger inhibit, relay dropout, branch fusing/selective faults/thermal behavior, axle retention, and safety/privacy interfaces before buying the remaining mobility/safety set or powering both motors.
5. Print representative harness, seam, motor-pod, idler, camera, vent, and acoustic parts before a full shell.
6. Build the stationary bench brain and deterministic safety loop before powering drive motors.
