# Robot

An embodied Codex companion project: a small indoor robot body that can listen, talk, look around, and move safely through the house.

The design goal is pet-like presence without overcomplicating the first build. The MVP is a compact wheeled robot with a camera head, microphone array, speaker, LEDs, bumpers, conservative autonomy, and a physical E-stop. Tiny body, serious safety shoes.

## Current Status

This repo is at the planning and early tooling stage. Start with the docs index:

- Documentation index: [`docs/README.md`](docs/README.md)
- MVP PRD: [`docs/mvp-prd.md`](docs/mvp-prd.md)
- Decision log: [`docs/decision-log.md`](docs/decision-log.md)
- MVP architecture: [`docs/mvp-architecture.md`](docs/mvp-architecture.md)
- BOM v0: [`docs/bom-v0.md`](docs/bom-v0.md)
- CAD mechanical plan: [`docs/cad-mechanical-plan.md`](docs/cad-mechanical-plan.md)
- Python CAD tooling notes: [`cad/python/README.md`](cad/python/README.md)

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
- Battery cradle.
- Wheel guards.
- Camera/head shell.
- Service panels.

OpenSCAD is the default first-pass CAD tool for simple parametric printable parts. `build123d` and CadQuery are approved for Python-based CAD when parts need nicer geometry, fillets, chamfers, STEP exports, or richer assemblies.

Generated mesh/solid exports should go under `cad/exports/` and are ignored by Git by default.

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
|   `-- python/
|       |-- README.md
|       `-- requirements.txt
|-- docs/
|   |-- README.md
|   |-- bom-v0.md
|   |-- cad-mechanical-plan.md
|   |-- decision-log.md
|   |-- mvp-architecture.md
|   `-- mvp-prd.md
|-- .gitignore
`-- README.md
```

## Next Steps

1. Confirm printer model/build volume and first operating area in the house.
2. Buy the bench-brain and safety-prototype batch from [`docs/bom-v0.md`](docs/bom-v0.md).
3. Add `cad/openscad/robot_params.scad`.
4. Generate the first printable electronics deck and base tray.
5. Build the stationary bench brain before powering any drive motors.
