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

## Build123d Body v1

`robot_body.py` is the current parametric body source. It builds the rounded
cream shell, teal service lid, bumper carrier, wheel and hub modules, head,
serviceable pan/tilt mounts, front sensor fascia, E-stop support, and
review-only electronics envelopes. Its molded shell now uses a 12 mm top-edge
rollover with a matching 8.8 mm inner
radius, preserving the full 3.2 mm roof while leaving the lower tray and seam
interfaces crisp. The validator probes three quiet roof locations and pins the
visible rollover to a 10 mm minimum so this concept-facing form cannot silently
regress into a box. The current packaging pass also includes a
Camera Module 3 Wide carrier, upper power/safety deck, and a modular rear service frame with a drawing-backed Switchcraft EN2 charge-only inlet, a protected-UART service cartridge on a separate L-carrier, and a drawing-backed PVB3 physical-mute cartridge,
speaker/airflow paths with dual exact-pattern MAX98357A mounts beneath the speaker plates, rear motor pods with removable inboard service covers,
removable two-bearing front idler pods, and a stacked controller/safety-MCU
shelf. The base tray now includes reinforced slots for two recessed 25 mm
webbing carry loops whose review-only metal clamp plates bridge the split seam.
Two removable U-channel rails beneath the power deck provide separate
signal/audio/sensor and fused switched-power/motor bundle paths; paired deck
and rail slots let reusable straps retain the wiring as one serviced assembly.
The 145 x 116 mm deck uses Pololu's exact four-hole D24V90F5 and triangular
three-hole D36V50F6 patterns on 6 mm M2 metal standoffs. It also reserves the
Albright SW60 body, M6-stud service volume, and a custom 50 x 90 x 2 mm metal
carrier bolted through four M3 paths. The printed deck remains an organizer,
not primary contactor retention.
The former anonymous 60 x 26 x 18 mm distribution reserve is now a covered
custom 40 x 21 mm PCB reference. Four Littelfuse 01550900M OMNI-BLOK holders
carry replaceable Nano2 fuses, and a drawing-backed Molex 43045-1000/43025-1000
ten-circuit Micro-Fit pair carries source positive/return plus four separately
fused positive/return branches. Four lower and four upper M2 metal standoffs
retain the board independently of its printable touch cover; dedicated
fuse-service, connector, bend, and strain-strap paths remain open. The 6 A
total / 5 A branch ceilings are provisional mechanical/electrical design limits,
not release approval or final fuse values.
Audio cradles, the front fascia, all four ToF pods, the battery cradle,
and the controller stack now have explicit shell/tray attachment paths. The
controller baseline is the official Cytron MDDS10 STEP footprint and 95.25 x
60.96 mm hole pattern, mounted on four 6 mm M3 standoffs above a locally
notched plate. Four additional 5 mm metal spacers lift that plate over the
concealed carry-handle doubler; front terminal fan-out and a 10 mm cooling
keepout remain open below the Pico shelf. The
E-stop now targets the IDEC XW1E-BV402M-R. A removable 4 mm keyed panel carries
the purchased nut and yellow legend; a raised-collar backing ring, four cardinal
M3 paths, 40 mm surrounding service passage, 37 mm body envelope, and covered
terminal corridor keep the safety hardware reinforced and removable.
The camera head now integrates a projecting cream front bezel around a thinner
recessed black faceplate. Narrow vertical lime diffusers match the concept while
larger hidden LED-board pockets and side-fastened Adafruit 5975 carriers remain serviceable.
The removable faceplate also includes one fused stepped camera annulus instead
of four overlapping decorative parts; the real Camera Module 3 Wide sits
forward behind a validated 102-degree horizontal-FOV cone with no printed disk
across the optical path.
The mobility stance uses the tire tangent as a shared ground datum: 43 mm-radius
wheels are centered at Z=66 and partly inset 4 mm into synchronized shell,
scalloped fairing, and bumper arches. Each fairing now uses a large center
relief plus a narrow upper bridge, so the molded shell and side-ToF opening stay
visible while one serviceable part per side retains four high screws. Each
2 mm skin now seats flush at the body-width datum inside a 2.2 mm shell recess
with 0.3 mm perimeter clearance, a 0.2 mm nominal clamp gap, and 1 mm of
continuous backing wall. The
bumper remains 6 mm above the nominal floor and
uses a 302 x 222 mm inner cavity for 1 mm shell clearance plus concealed low
inboard bridges to stay one printable carrier without occupying the tray. Motor and
idler pod shells remain tray-seated while their retained metal hardware follows the
lower axle, and the side ToF pods sit in the true gap between wheel wells.
Each TPU tire has 24 half-step-offset transverse grooves, 5.5 mm wide by 2 mm
deep, across the central 20 mm band. Two intact 2 mm sidewalls preserve the hub
seat and sidewall-down print face, while the rolling diameter and Z=23 tangent
stay unchanged. Use `codex_robot_body_v1_wheel_detail.png` to review the tread,
arch, hub, and bumper relationship after changing mobility parameters.
The safety bumper separates moving and fixed references: the split TPU carrier
has six local stroke reliefs, while six PETG switch plates seat beneath the tray
on 12 blind inboard inserts. Omron D2HW-C202MR sealed SPST-NC switches use their
13 mm M3 pattern, side-lead corridors, a 0.4 mm rest gap, 2 mm nominal
actuation, and paired 2.4 mm rigid stops. Release still requires exact coupon,
six-direction electrical, strain, rebound, broken-wire, and motor-cut testing.
The battery cradle now targets one Bioenno BLF-1203AB prototype candidate,
rotated flat to 110 x 75 x 27 mm. Its 117 x 92 mm cradle has four pads, two
20 mm real straps, positive locators, power-deck-standoff scallops, and a rear
lead corridor for the separate Powerpole discharge and DC charge leads. This
is a fit/current prototype baseline, not household release: delivered lead
geometry, certification evidence, retention, BMS/regen/thermal behavior,
runtime, and measured <=5.6 A sustained pack current remain gates. All
dimensions are millimetres and live in `Params`.

Generate the body exports and review-only fit volumes with:

```bash
.venv-cad/bin/python cad/python/robot_body.py
```

The generated files go under `cad/exports/`. They are intentionally ignored;
the Python source is the reproducible source of truth. The command clears old
generated STL names and writes `codex_robot_body_v1_manifest.json` so stale
parts cannot quietly survive a renamed interface.

For the P1S 256 mm square printer bed, generate the split shell, tray, lid,
reveal/gasket, bumper, fairing, and insert-backed seam-plate variants with:

```bash
.venv-cad/bin/python cad/python/robot_body_split.py --bed 256 --margin 8
```

Run the main export first and the split export second. The split manifest lists
the current 57-part inventory, assembly groups, provisional fastener counts, and bed
spans. Its actual interfaces are insert-backed wall plates, an underside tray
plate, independently mounted fairing halves, and a 12 mm stepped lid lap. The
nine shell/tray/bumper backing plates carry 18 concealed 4 mm alignment pilots;
matching half-round recesses in the split pieces provide 0.3 mm radial and
0.4 mm axial clearance so the seams locate before the screws are tightened.

Validate solids, component collisions, tire ground contact, bumper and hard-part
ground clearance, six tray-fixed bumper plates, 12 blind screw paths, rest-gap
and nominal TPU actuation, mobility-pod seating, front bearing and shaft paths,
safety-shelf alignment, motor-pod, tray, and wheel clearances,
bumper-switch keepouts, interior bounds, the printer envelope, split-part
reconstruction, open shared fastener paths, and the head at its configured
pan/tilt limits. It also checks the carry slots, M4 paths, metal-plate
clearances, stowed webbing ground clearance, complete E-stop barrel path, four
removable E-stop backing screws, both harness corridors, all shared strap
slots, the head-bezel recess, and all eight head-panel screw paths with:

```bash
.venv-cad/bin/python cad/python/validate_robot_body.py --bed 256 --margin 8
```

The validator also proves all 18 alignment pilots are fused to their backing
plates, clear both mating recess halves, retain at least 1.2 mm of exterior
shell wall, and do not introduce split-joinery overlap.

Export the canonical 103-part prototype inventory in deliberate slicer
orientations with:

```bash
.venv-cad/bin/python cad/python/robot_body_print.py --bed 256 --margin 8
```

This command substitutes the validated split pieces for the seven oversized
assembly parts, grounds and centers every STL, preserves source volume, checks
the usable bed span and first-layer contact, and writes material/support/release
guidance to `cad/exports/print_ready/codex_robot_body_v1_print_manifest.json`.
The same manifest includes current interface-level fastener, insert, standoff,
and locknut counts; lengths and final threads remain coupon/hardware dependent.
"Print-ready" describes orientation and bed fit; battery, axle, carry, harness,
and selected drivetrain/safety parts remain prototype-only until purchased hardware,
physical coupons, measured bundles, and the applicable loaded tests pass.
The faceplate and LED expression parts carry additional physical camera-image
and diffuser-test gates in that manifest.

Build the tracked P1S 0.4 mm Bambu Studio project after the canonical exports:

```bash
.venv-cad/bin/python cad/bambu/generate_bambu_project.py
```

The project contains all 103 parts on 26 single-material/single-color plates.
See [`cad/bambu/README.md`](../bambu/README.md) and the generated plate manifest
for the exact filament groups and per-plate process recommendations.

After regenerating the CAD manifests and Blender review images, build the
illustrated assembly guide with the project CAD environment. The requirements
file installs its Pillow and ReportLab dependencies:

```bash
.venv-cad/bin/python docs/generate_assembly_guide.py
```

The result is `output/pdf/codex_robot_body_v1_assembly_guide.pdf`. Render and
visually inspect every page with `pdftoppm` before treating it as current.

Generate the seventeen shared-parameter calibration coupons with:

```bash
.venv-cad/bin/python cad/python/robot_body_coupons.py --bed 256 --margin 8
```

The coupon manifest records left-to-right station dimensions for M3/M2.5
inserts and clearance holes, three 608 bearing seats, a combined three-seat and
three-journal Koyo 6807 pan-bearing test, the wall-thickness test,
the exact production lid-lap pair, and a three-piece pilot/recess fit test
clipped from the real shell joinery. It also includes the exact three-piece
bumper-switch interface, a two-piece shell/fairing corner that proves the
flush recess enters freely and reaches its backing floor, and a one-piece
production-derived distribution-board gauge that proves the PCB/holder/fuse/header
stack fits its deck, M2 paths, and actual cover before a PCB order. See the tracked
[coupon protocol](../../docs/cad-coupons.md) before selecting a station or
changing `Params`.

The head mechanism targets two drawing-backed 29 x 13 x 30 mm Hitec D85MG 24T
servos and two R-ML24 aluminum horns. A Koyo/JTEKT 6807-2RS bearing carries the
pan-axis weight between a keyed fixed collar and the rotating neck journal; a
four-screw printed retainer captures the inner ring below the horn. The passive
tilt side uses an MF84ZZ flanged bearing and McMaster 92981A143 shoulder screw.
The fixed yoke, removable drive/passive adapters, screw-on faceplate and rear
cover, camera-ribbon path, and 72 D x 140 W x 72 H capsule remain fully
serviceable. The print manifest computes a conservative static torque sanity
check, while the validator rotates the complete moving printed head—not only
the shell—through every sampled pose. Purchased-part fit, cable drag, power,
current, heat, backlash, and repeated motion remain physical release gates.

The generated main manifest includes a `component_coverage` section. The
tracked [CAD component coverage matrix](../../docs/cad-component-coverage.md)
is the human-readable release gate; it must not call generic envelopes
"finished" until purchased hardware is measured.

## Concept Reference And Review Renders

The visual reference currently tracked in this repository is
`docs/images/concept-rendering.png`. The Blender scripts render the same STL
inventory produced by `robot_body.py`; there is no separate concept mesh to
drift away from printable geometry.

```bash
/Applications/Blender.app/Contents/MacOS/Blender -b --python cad/blender/render_robot_body.py
/Applications/Blender.app/Contents/MacOS/Blender -b --python cad/blender/render_print_ready.py
/Applications/Blender.app/Contents/MacOS/Blender -b --python cad/blender/render_coupons.py
/Applications/Blender.app/Contents/MacOS/Blender -b --python cad/blender/render_alignment_pilot.py
```

The assembled/exploded renderer uses a warm high-key daylight rig modeled on
the reference: broad window key, room/front/rim/overhead bounce, soft sun,
cream environment, honey floor, AgX highlight rolloff, and local ambient
occlusion. Keep its exposure and camera-axis fill synchronized across
regenerated review views; these images are mechanical-review aids, not a
separate concept mesh.

The top stack uses a separately printable 80 x 62 x 1.6 mm dark vent inlay in
a 1.4 mm lid recess. Four M2.5 screws retain it to underside bosses—two per lid
half—and nine shared 36 x 3 mm slots stay open through the inlay, lid, and shell
over the 70 mm microphone reference. `codex_robot_body_v1_top_detail.png` is the
dedicated visual check for this lid/vent/E-stop/neck interface.

Use the resulting tracked images to compare silhouette, color placement,
service layering, split joinery, harness routing, and print orientation against
the actual generated parts.
