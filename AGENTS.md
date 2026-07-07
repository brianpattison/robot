# Agent Instructions

This repo is for building an embodied Codex house companion: a small indoor robot body that can listen, talk, look around, and move safely through the house. Keep the work practical, safety-first, and a little fun. We are allowed to enjoy the tiny robot build while still treating motors, batteries, and autonomy with respect.

## Keep This File Fresh

When you learn something that would help the next agent work faster or more safely, update this `AGENTS.md` file before you finish.

Good candidates:

- Settled project decisions.
- New hardware assumptions or measured dimensions.
- CAD/export workflow changes.
- Safety constraints.
- Commands that worked or failed.
- Environment setup details.
- Gotchas that would waste the next agent's time.

Do not turn this into a full changelog. Keep it short, actionable, and project-specific.

## Current Project Direction

- MVP body: compact indoor wheeled differential-drive rover with a friendly camera head.
- Compute baseline: existing Raspberry Pi 5 8GB.
- AI HAT+ 2: not required for MVP. Reserve mechanical clearance, cooling airflow, and power budget for a future upgrade.
- Storage: start MVP with a reliable microSD card. USB 3 storage is an easy later upgrade. Official M.2/NVMe HAT storage and official AI HAT+ 2 both use the Pi 5 PCIe connector, so do not assume they can coexist.
- If USB 3 storage is added later, design a printed cradle with cable strain relief and service access. Avoid dangling external drives inside the body.
- Personality: Codex/ChatGPT is the primary conversational and agentic identity.
- Subsystems may use other models/services for wake word, STT, TTS, perception, or fallback, but they are tools, not alternate personalities.
- Safety/reflexes are deterministic and must not depend on an LLM.
- Build order: documentation -> bench brain -> safety loop -> CAD fit checks -> rolling chassis -> supervised autonomy.

## Read These First

Start with:

1. `README.md`
2. `docs/README.md`
3. `docs/decision-log.md`
4. `docs/mvp-prd.md`
5. `docs/mvp-architecture.md`
6. `docs/bom-v0.md`
7. `docs/cad-mechanical-plan.md`

The docs intentionally separate product requirements, decisions, architecture, BOM, and CAD/mechanical planning. Keep new details in the most specific doc rather than stuffing everything into the README.

## Safety Rules

- The robot should fail stopped.
- Physical E-stop must cut motor power independently of the Pi.
- Bumper switches and watchdog timeout must stop motion without consulting Codex/ChatGPT.
- Codex may issue high-level intents like `stop`, `come_here`, `follow_user`, `go_home`, or `look_at_speaker`.
- Codex must not directly control raw unbounded wheel speeds, disable safety hardware, bypass no-go zones, or override low-battery behavior.
- Local `stop`, `wait`, `mute`, and basic `status` should work even if network/cloud AI is unavailable.

If you touch any motion, power, battery, or safety-control design, update the relevant docs and make the safety implications explicit.

## CAD And Mechanical Conventions

- OpenSCAD is the default first-pass CAD tool for simple parametric printable parts.
- Local OpenSCAD CLI is available at `/Applications/OpenSCAD-2021.01.app/Contents/MacOS/openscad`.
- `build123d` and CadQuery are approved for Python CAD when geometry needs richer fillets, chamfers, STEP exports, or complex assemblies.
- The current concept-art matching pass is `cad/python/concept_body.py`; it uses CadQuery plus VTK to generate the `docs/images/codex_body_python_cad_*.png` review renders.
- Keep editable CAD source in `cad/openscad/` or `cad/python/`.
- Keep generated exports under `cad/exports/`; generated STL/STEP/mesh files are ignored by Git by default.
- Use shared parameters for dimensions, fastener sizes, wheel geometry, sensor offsets, keepouts, and board mount patterns.
- Printed parts should be modular and serviceable: base tray, electronics deck, battery cradle, motor pods, bumper carrier, ToF sensor pods, camera/head bracket, and top shell.
- Use `preview_only()` in OpenSCAD for dummy hardware, LED/status markers, keepout markers, and other review-only solids so generated STLs stay print-focused.
- `cad/openscad/split_print_variants.scad` has smaller-bed exports for base tray halves, electronics deck halves, bumper quadrants, and seam plates; use it before assuming a one-piece 300 x 220 mm tray print.
- Include USB storage mounting as a serviceable later module only if USB SSD/flash storage becomes part of the build.
- Do not rely on printed plastic alone for safety-critical battery retention, E-stop mounting, axle support, or motor retention.

## Python CAD Setup

The macOS system Python found earlier was `3.9.6`, which is too old for current `build123d` expectations. Use a newer Homebrew Python and a venv for CAD work:

```bash
brew install python@3.12
/opt/homebrew/bin/python3.12 -m venv .venv-cad
source .venv-cad/bin/activate
python -m pip install --upgrade pip
python -m pip install -r cad/python/requirements.txt
```

Do not install CAD packages into Apple/system Python.

## Repo Hygiene

- Use `rg` / `rg --files` for searching.
- Use `apply_patch` for manual file edits.
- Do not edit generated CAD exports by hand.
- Do not commit or track `.venv-cad/`, `cad/exports/`, logs, captures, rosbags, or generated STL/STEP files unless the user explicitly asks for release artifacts.
- The working tree may already contain uncommitted user or agent changes. Do not revert unrelated changes.

## Near-Term Next Steps

Likely next useful work:

1. Review and fit-check the initial OpenSCAD body concept in `cad/openscad/` and the rendered overview in `docs/cad-v0-body.md`.
2. Confirm printer build volume and filament/material assumptions before committing to one-piece tray dimensions.
3. Replace generic motor pod, bumper switch, caster, E-stop, and battery geometry with measured real parts; the current E-stop plate is still a datasheet placeholder.
4. Print insert/fastener coupons, then the electronics deck, before printing the whole base tray.
5. Confirm which bench-brain parts are already owned vs need to be ordered from `docs/bom-v0.md`.
