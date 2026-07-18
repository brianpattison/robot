# Bambu Studio P1S project

## v2 prototype project

[`codex_robot_body_v2_p1s.3mf`](codex_robot_body_v2_p1s.3mf) is the tracked
printed-only v2 geometry-review project. It is a **prototype artifact, not a
powered-motion release**. Its plate manifest keeps the physical release gates
explicit, and the builder's book must use the same label. The D035 head
mechanism is modeled and kinematically validated; exact-part fit, journal wear,
loaded servo current, harness schedule, software/firmware release, fuse
selection, and commissioning evidence remain open.

Regenerate the v2 model, validator, print exports, and Bambu project with:

```bash
.venv-cad/bin/python cad/python/robot_body_v2.py
.venv-cad/bin/python cad/python/validate_robot_body_v2.py --gate
.venv-cad/bin/python cad/python/robot_body_v2_print.py
.venv-cad/bin/python cad/bambu/generate_bambu_project_v2.py
```

The `--gate` validator is necessary but never substitutes for the named
physical tests. The current project contains 45 pieces on 13 plates in seven
inventory-derived material/color groups: white/black/red PETG, charcoal/teal/
translucent-lime PLA, and charcoal TPU. Shell and head are white PETG because
their candidate PLA evidence gates are still open; never hand-edit the 3MF to
bypass that fallback. Generate and print all 18 coupons before large parts;
keep the battery and motor
branch disconnected while following prototype-only assembly pages.

## v1 historical project

The tracked [`codex_robot_body_v1_p1s.3mf`](codex_robot_body_v1_p1s.3mf)
is the canonical Bambu Studio layout project for a Bambu Lab P1S with the
standard 0.4 mm nozzle and a Textured PEI Plate.

It contains all 101 canonical printable parts exactly once on 26 named plates.
Each plate contains one material-profile/color group; no plate mixes PETG and
TPU or combines colors. The project carries nine physical filament/color
presets and uses a conservative global baseline of four walls and 25% gyroid
infill. The per-plate recommendations in
[`codex_robot_body_v1_p1s_plates.json`](codex_robot_body_v1_p1s_plates.json)
remain authoritative for layer height, wall count, and infill.

Regenerate the canonical STLs and project with:

```bash
.venv-cad/bin/python cad/python/robot_body_print.py
.venv-cad/bin/python cad/bambu/generate_bambu_project.py
```

The generator resolves the installed Bambu Studio machine, process, PETG, and
TPU presets into full CLI profiles, imports the canonical STLs through Bambu
Studio, packs them with brim-aware clearance inside an 8 mm edge reserve, and
round-trips the result through Bambu Studio. It then checks the P1S profile,
0.4 mm nozzle, 256 mm plate, Textured PEI selection, plate grouping, bounds,
packing-envelope separation, and the exact 101-part inventory.

The macOS application bundle remains the default, but custom and non-macOS
installs can supply the official Bambu Studio CLI and BBL profile root without
editing source:

```bash
.venv-cad/bin/python cad/bambu/generate_bambu_project.py \
  --bambu-cli /path/to/bambu-studio \
  --profile-root /path/to/resources/profiles/BBL
```

This is an editable layout project, not pre-sliced G-code and not a hardware
release waiver. Review every plate in the current Bambu Studio slicer before
printing. Honor the release status in the plate manifest and print the calibration
coupons first. The rear drivetrain uses drawing-backed Pololu motors in printed
saddles/caps with direct D-shaft wheel clamps; the v2 head targets two Hitec D85MG servos
and R-ML24 horns around a greased printed pan journal and printed passive tilt
bushing — no 6807/MF84ZZ/shoulder-screw stack. Both still require delivered-part
inspection and loaded testing. The IDEC XW1E E-stop and
Omron D2HW bumper interfaces are also drawing-backed but remain gated on exact
coupons and deterministic cutoff tests. D024 replaces the Albright/custom-
carrier and custom-distribution interfaces with the Panasonic CB1A-R-M-12V
relay and Blue Sea Systems 5045 fuse block, replaces the machined front axle
with the WDS 615-M6-8-65 retail shoulder-bolt stack, removes the carry handles,
and leaves the center rear cartridge blank. The tracked 3MF and plate manifest
predate that synchronization and may still contain legacy names or parts; do
not use them as a D024 hardware release. Regenerate them only after the split
and print generators are updated, then inspect the Panasonic, Blue Sea, WDS,
blank-cartridge, and handle-free inventory before committing to the full body.

![P1S plate layout](../../docs/images/codex_robot_body_v1_p1s_plates.png)
