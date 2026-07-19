# Robot

An embodied Codex companion project: a small indoor robot body that can listen, talk, look around, and move safely through the house.

The design goal is pet-like presence without overcomplicating the first build. The MVP is a compact wheeled robot with a camera head, microphone array, speaker, LEDs, bumpers, conservative autonomy, and a physical E-stop. Tiny body, serious safety shoes.

## Current Status

The current direction is the **v2 printed-only hybrid-material body** (decision
log D025-D035): 40 installed functional pieces, four spare washers, and one
optional cosmetic lid skin on 13 zero-support plates, with one screw size and
one insert size.

> **Prototype assembly preview — do not use for powered motion.** The tracked v2
> 3MF and builder's book are geometry and dry-assembly artifacts. The head/neck
> load paths are fully modeled and kinematically validated. A versioned Pi 5
> appliance installer/`robotd`, framed UART contract, portable Pico safety core,
> deliberately fail-stopped Pico target, nominal harness traveler, and
> executable commissioning gate now ship. Exact-part fit, production motor
> outputs, exact harness terminals/lengths, released fuse values, loaded
> wear/current testing, and signed physical evidence remain open.

- **Versioned v2 Builder Release Index:** [`docs/builder-release-v2.md`](docs/builder-release-v2.md)
- **The Builder's Book (v2 prototype preview):** [`output/pdf/codex_robot_body_v2_assembly_guide.pdf`](output/pdf/codex_robot_body_v2_assembly_guide.pdf)
- v2 Bambu Studio project: [`cad/bambu/codex_robot_body_v2_p1s.3mf`](cad/bambu/codex_robot_body_v2_p1s.3mf)
- v2 qualification-coupon project: [`cad/bambu/codex_robot_body_v2_coupons_p1s.3mf`](cad/bambu/codex_robot_body_v2_coupons_p1s.3mf)
- v2 book generator: [`docs/generate_assembly_guide_v2.py`](docs/generate_assembly_guide_v2.py)
- bench protocol: [`docs/body-protocol-v1.md`](docs/body-protocol-v1.md)
- Pi runtime/appliance: [`software/robotd/`](software/robotd/), [`software/appliance/`](software/appliance/), and the [provisioning guide](docs/pi-appliance-provisioning.md)
- localhost supervision dashboard: [`software/dashboard/`](software/dashboard/)
- Pico safety-core baseline: [`firmware/pico2-safety/`](firmware/pico2-safety/)
- harness traveler and release gate: [`harness/`](harness/)
- executable commissioning package: [`commissioning/`](commissioning/)

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
- Current v2 purchase authority: [`docs/builder-release-v2.md`](docs/builder-release-v2.md)
- BOM v0 (historical v1 planning): [`docs/bom-v0.md`](docs/bom-v0.md)
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
- Quantity-one US retail hardware for every purchased v2 item; printed front axles, wheels, and motor retention; no custom PCB, machined structure, or carry handles. Unresolved retail/power parts stay visibly blocked.

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
|-- .github/workflows/bench-safety.yml
|-- cad/
|   |-- bambu/
|   |   |-- README.md
|   |   |-- generate_bambu_project_v2.py
|   |   |-- codex_robot_body_v2_p1s.3mf
|   |   `-- codex_robot_body_v2_coupons_p1s.3mf
|   |-- blender/
|   |   |-- render_robot_body_v2.py
|   |   `-- render_assembly_steps_v2.py
|   `-- python/
|       |-- README.md
|       |-- requirements.txt
|       |-- robot_body_v2_inventory.py
|       |-- robot_body_v2.py
|       |-- robot_body_v2_coupons.py
|       `-- validate_robot_body_v2.py
|-- commissioning/
|-- docs/
|   |-- builder-release-v2.md
|   |-- body-protocol-v1.md
|   |-- first-article-evidence.md
|   `-- README.md
|-- firmware/pico2-safety/
|-- harness/
|-- software/robotd/
|-- software/dashboard/
|-- software/appliance/
`-- README.md
```

## Next Steps

1. Run `python3 commissioning/run_host_tests.py`; green proves only the
   hardware-free contracts.
2. Use [`docs/builder-release-v2.md`](docs/builder-release-v2.md), never the
   historical v1 BOM, for the current selection list and explicit blockers.
3. Print and record all 18 v2 coupons before committing to large body parts.
4. Close the protected mobile-Pi input, R-ML24 sourcing, servo-regulator,
   production relay-driver, Pico-reset, USB-mute/backfeed, and exact harness
   decisions before treating the electronics table as a complete shopping list.
5. Keep every fuse value unset until measured current, conductor, inrush,
   time-current, selective-clearing, and thermal evidence supports it.
6. Work through the
   27-step commissioning plan in order using the
   [first-article evidence workflow](docs/first-article-evidence.md). The
   repository release gates are intentionally red until the exact physical
   first article supplies every required measurement and an independently
   trusted signer seals the complete bundle.
