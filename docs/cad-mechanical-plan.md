# CAD Mechanical Plan: Codex House Companion MVP

## 1. Purpose

This document defines the first mechanical design pass for the Codex house companion body. The goal is not a polished product enclosure yet. The goal is a printable, serviceable, safe rover platform that can carry the Raspberry Pi 5, audio/video hardware, motor system, battery, sensors, and a friendly camera head while leaving room for later upgrades.

The MVP body should be easy to print, easy to open, easy to rework, and hard to accidentally turn into a tiny rolling furniture argument.

## 2. Design Constraints

- Body type: compact indoor differential-drive rover with a friendly camera head.
- Primary compute: Raspberry Pi 5 8GB.
- AI HAT+ 2: not required for MVP, but reserve space, cooling path, power-routing space, and cable clearance for a later HAT stack.
- Fabrication: FDM 3D printer available for fast iteration.
- Primary CAD source: OpenSCAD for first-pass parametric parts.
- Secondary CAD source: `build123d` or CadQuery for complex curved shells, nicer fillets, STEP references, or assemblies that become painful in OpenSCAD.
- First MVP should prioritize safety, maintainability, and sensor placement over visual polish.
- Printed plastic is not trusted as the only safety-critical load path for the battery, E-stop, axle support, or motor retention.

## 3. Mechanical Architecture

### Overall Body

Target envelope for the first printable body:

| Dimension | Target | Notes |
| --- | ---: | --- |
| Base length | 300 mm | Long enough for Pi, battery, motors, sensors, and bumper travel. |
| Base width | 220 mm | Stable indoors while still small enough for halls and chair gaps. |
| Base height | 90-120 mm | Excludes head. Keep battery low. |
| Total height | 230-300 mm | Includes mast/head. Friendly eye-line without getting top-heavy. |
| Wheel diameter | 70-90 mm | Good for thresholds and rugs without becoming a monster truck. |
| Ground clearance | 15-25 mm | Enough for floor transitions, not enough to invite stair fantasies. |
| Max printed module size | Printer-dependent | Keep first modules under 220 x 220 mm unless printer volume is confirmed. |

The first chassis should be a layered assembly:

1. Lower base tray/tub carries motors, battery, caster, and bumper mounts.
2. Removable electronics deck carries Pi, motor controller, regulators, fuse block, and cable strain relief.
3. Top service shell covers electronics while allowing airflow and tool access.
4. Front mast supports the camera head, microphone placement, LED/status features, and optional pan/tilt.
5. Bumper carrier surrounds the base and mechanically triggers switches before hard contact.

### Locomotion Layout

Use differential drive:

- Two powered side wheels near the middle of the base.
- One rear caster for the simplest first build, or two small rear casters if stability needs it.
- Wheel axle centerline roughly 130-150 mm from the front edge on a 300 mm base.
- Battery placed low and slightly rearward of the wheel axle to balance the head/mast.
- Pi and electronics centered over the base, isolated from motor vibration with printed standoffs and rubber washers where practical.

Initial motor mount strategy:

- Use printed motor pods or motor plates bolted into the lower tray.
- Use metal screws, washers, and heat-set inserts.
- Design slotted motor holes for 3-5 mm of belt/gear/wheel alignment adjustment if the selected motor allows it.
- Keep wheel removal possible without disassembling the full body.

### Head And Expression

The MVP head is a camera/sensor assembly, not a heavy sculptural shell.

Target:

- Small mast or neck at the front third of the robot.
- Camera Module 3 Wide or equivalent mounted at 180-240 mm above floor.
- Pan/tilt bracket optional for first bench build, but reserve mounting points.
- LED eyes or light pipe integrated later as a separate faceplate.
- Microphone array should sit high and mechanically isolated from the motor deck.

The head should be modular because this is where personality will evolve. First head: simple bracket and protective shell. Later head: smoother `build123d`/CadQuery shell with nicer fillets and replaceable faceplate. We earn the cute face after the screw holes line up.

## 4. Printable Modules

### Required MVP Modules

| Module | Source Tool | Purpose |
| --- | --- | --- |
| `base_tray` | OpenSCAD | Main lower chassis, motor pod anchors, battery zone, caster mount, bumper anchors. |
| `electronics_deck` | OpenSCAD | Removable plate for Pi, motor controller, regulators, wire tie points, HAT clearance. |
| `battery_cradle` | OpenSCAD | Holds battery low with strap slots, keyed orientation, and padding clearance. |
| `motor_pod` | OpenSCAD | Mounts gearmotors to tray with adjustable screw slots. |
| `bumper_carrier` | OpenSCAD | Carries soft bumper material and bumper switch trigger paddles. |
| `tof_sensor_pod` | OpenSCAD | Repeatable front/side proximity sensor pods with angled variants. |
| `camera_head_bracket` | OpenSCAD first, Python CAD later if needed | Holds camera and optional pan/tilt servos. |
| `top_service_shell` | OpenSCAD first, Python CAD later | Covers electronics while leaving ventilation and fastener access. |

### Optional Early Modules

| Module | Source Tool | Purpose |
| --- | --- | --- |
| `speaker_grille` | OpenSCAD or Python CAD | Front/upward speaker mounting and acoustic holes. |
| `mic_array_mount` | OpenSCAD | Raised, vibration-isolated microphone mount. |
| `led_faceplate` | OpenSCAD or Python CAD | Replaceable expressive front plate. |
| `carry_handle` | OpenSCAD | Service handle, only if backed by metal fasteners and conservative walls. |
| `lidar_plate` | OpenSCAD | Reserved top/front mounting plate for future 2D LiDAR. |
| `ai_hat_spacer_gauge` | OpenSCAD | Dummy volume to confirm future AI HAT+ 2 clearance. |
| `usb_storage_cradle` | OpenSCAD | Later upgrade module for compact USB SSD, USB flash drive, or USB enclosure with service access and cable strain relief. |

## 5. Parameter Strategy

Create one shared OpenSCAD parameter file:

```text
cad/openscad/robot_params.scad
```

Use it for every OpenSCAD model. The file should define the mechanical contract of the robot:

```scad
// Body envelope
base_len = 300;
base_w = 220;
base_floor_th = 4;
wall_th = 3;
corner_r = 8;

// Drive
wheel_d = 80;
wheel_w = 24;
axle_z = 42;
axle_x = 140;
motor_mount_slot = 5;

// Fasteners
m3_clearance_d = 3.4;
m3_insert_d = 4.8;
m3_insert_depth = 5.7;
m25_clearance_d = 2.8;

// Electronics
pi_len = 85;
pi_w = 56;
pi_mount_x = 58;
pi_mount_y = 49;
hat_keepout_z = 28;
cooling_keepout_z = 18;

// Battery
battery_len = 110;
battery_w = 38;
battery_h = 38;
battery_padding = 3;

// USB storage
usb_storage_len = 90;
usb_storage_w = 35;
usb_storage_h = 12;
usb_cable_bend_r = 25;

// Sensors
tof_pod_w = 22;
tof_pod_h = 18;
front_sensor_angle = 20;

// Export/render quality
$fn = 48;
```

Keep all dimensions in millimeters. Do not bury magic numbers inside part files unless they are local cosmetic details. If a dimension affects fit, serviceability, wiring, safety, or sensor geometry, it belongs in `robot_params.scad`.

### Python CAD Parameters

For `build123d` or CadQuery, mirror the same values in:

```text
cad/python/robot_params.py
```

Do not fork dimensions silently. If OpenSCAD and Python CAD both model the same interface, the screw spacing, keepouts, and external dimensions must match.

## 6. First CAD Files To Create

Create files in this order:

1. `cad/openscad/robot_params.scad`
   - Shared dimensions, fastener sizes, keepouts, and export quality.

2. `cad/openscad/base_tray.scad`
   - 300 x 220 mm lower tray.
   - 4 mm floor, 3 mm walls.
   - Rounded or chamfered corners.
   - Anchor points for motor pods, battery cradle, electronics deck, bumper carrier, and caster.
   - Cable pass-throughs between motor, battery, and electronics zones.

3. `cad/openscad/electronics_deck.scad`
   - Removable flat deck.
   - Pi 5 mounting holes.
   - Future full-HAT vertical keepout above Pi.
   - Regulator and motor-controller generic hole grids.
   - Zip-tie slots and wire channel edges.
   - Ventilation cutouts under/around Pi, not under structural screw bosses.

4. `cad/openscad/battery_cradle.scad`
   - Battery pocket with 3 mm padding clearance.
   - Two strap slots.
   - End stops that prevent sliding under acceleration.
   - Clearance for battery wires without sharp bends.

5. `cad/openscad/motor_pod.scad`
   - Parametric motor hole pattern.
   - Slotted adjustment holes.
   - Reinforced ribs around motor screws.
   - Wheel clearance visualizer mode.

6. `cad/openscad/bumper_carrier.scad`
   - Front and side bumper support ring.
   - Soft bumper attachment channel.
   - Bumper switch trigger tabs.
   - 5-10 mm compression travel before hard chassis contact.

7. `cad/openscad/tof_sensor_pod.scad`
   - Straight, left-angle, and right-angle variants.
   - Small hood to reduce floor reflections.
   - M2/M2.5 holes or generic board clamp geometry.

8. `cad/openscad/camera_head_bracket.scad`
   - Camera board holder.
   - Cable relief path.
   - Optional servo mount placeholder.
   - Simple protective brow/shell.

Optional later:

- `cad/openscad/usb_storage_cradle.scad`
  - Adjustable pocket for a compact USB 3 SSD, flash drive, or M.2 USB enclosure.
  - Hook-and-loop strap slots or screw-down retaining bar.
  - USB cable bend-radius clearance.
  - Strain relief so vibration does not work the connector loose.
  - Tool access so storage can be removed without opening the full chassis.

After those exist, decide whether the top shell and final head shape stay in OpenSCAD or move to Python CAD.

## 7. Fasteners And Inserts

Default hardware strategy:

- Use M3 screws for structural printed parts.
- Use M2.5 or M2 screws only for electronics boards that require them.
- Use brass heat-set inserts anywhere the part will be opened repeatedly.
- Use washers under screw heads on plastic load paths.
- Use locknuts or threadlocker where vibration can loosen hardware.
- Avoid self-tapping screws for service panels unless a part is explicitly disposable.

Suggested insert defaults:

| Use | Fastener | Insert |
| --- | --- | --- |
| Chassis modules | M3 | M3 heat-set insert, 4.6-5.0 mm outer diameter class |
| Electronics deck | M2.5 or M3 | Inserts only if repeatedly removed |
| Pi standoffs | M2.5 | Brass standoff or printed standoff plus screw, depending on clearance |
| Sensor pods | M2/M2.5 | Small inserts or clamped board pocket |
| Bumper carrier | M3 | Inserts strongly recommended |
| Motor mounts | M3 or motor-specific | Inserts plus washers; printed plastic is backed by multiple screws |

Heat-set holes should be test-printed before committing the whole chassis. Printer calibration, insert brand, and filament choice all change fit. The insert test coupon is the humble hero of not ruining a 9-hour print.

## 8. Materials And Print Settings

### Filament

- PLA or PLA+ is acceptable for first fit-checks and bench parts.
- PETG is preferred for chassis parts that live near motors, battery, warm electronics, or repeated service.
- TPU or foam strip can be used for bumper contact surfaces; a rigid printed bumper alone is not enough.
- Avoid relying on brittle decorative filaments for load-bearing mounts.

### First-Pass Print Defaults

| Part Type | Layer Height | Walls | Infill | Notes |
| --- | ---: | ---: | ---: | --- |
| Fit-check coupons | 0.20 mm | 3 | 15-20% | Fast, cheap, disposable. |
| Electronics deck | 0.20 mm | 4 | 25% | Flat, stable, many holes. |
| Base tray | 0.24 mm | 4-5 | 25-35% | PETG preferred after first PLA check. |
| Motor pods | 0.16-0.20 mm | 5 | 40-60% | Higher walls around screw bosses. |
| Bumper carrier | 0.20-0.24 mm | 4 | 25-35% | Validate compression travel. |
| Camera/head parts | 0.16-0.20 mm | 3-4 | 15-25% | Lighter is better up high. |

Orient motor pods so layer lines do not split across the primary motor load. Where that is impossible, add ribs, increase wall count, or use a metal backing plate.

## 9. Safety And Load-Bearing Rules

These are mechanical requirements, not vibes:

- The E-stop must be mechanically accessible from above and from the side.
- E-stop mounting must not depend on a thin printed wall alone.
- Battery must be retained by a strap or mechanical latch, not just friction.
- Battery wires must have strain relief and must not rub against wheel hardware.
- Motor mounts must use multiple fasteners and enough wall/rib thickness to survive stalls.
- Wheels must not contact printed bodywork at full expected axle wobble.
- Bumper switches must trigger before the rigid chassis hits an obstacle.
- Caster mount must not punch through the chassis floor during a threshold impact.
- Ventilation must allow Pi cooling air to enter and exit without blowing directly into a closed pocket.
- The future AI HAT+ 2 space must not steal cooling clearance from the MVP Pi setup.
- Sharp printed edges near wires, hands, battery, or camera ribbon cable should be chamfered or rounded.

If any printed part fails in a way that could release the battery, jam a wheel, or hide the E-stop, redesign that part before adding autonomy. The robot may have personality; the chassis gets no dramatic license.

## 10. Upgrade Keepouts

Reserve the following spaces from the start:

| Upgrade | Reserved Space |
| --- | --- |
| AI HAT+ 2 or other full HAT stack | Full Raspberry Pi HAT footprint above Pi, plus at least 28 mm vertical board clearance and separate cooling airflow. |
| Active Pi cooling | Fan/heatsink clearance above Pi, intake path, exhaust path, and screw access. |
| USB 3 storage | Side or rear-accessible cradle for a compact USB SSD/flash drive plus short cable bend and strain-relief zone. |
| 2D LiDAR | Top or front-top plate with 60-75 mm circular keepout and unobstructed 360 degree or forward FOV, depending on sensor. |
| Depth camera | Front mast/front top panel with cable path and extra width. |
| Charging contacts | Rear low panel with protected contacts and strain relief path. |
| Larger battery | Battery bay length margin of at least 15-20 mm if possible. |
| Pan/tilt head | Mast screw pattern and cable loop slack. |

Do not install all upgrades now. Just do not make the body hostile to them. Future us is easier to impress than present us is to forgive.

## 11. Print Iteration Plan

### Phase 0: Measurement And Dummy Volumes

- Confirm printer build volume.
- Measure actual Pi case/heatsink/fan, battery candidate, motors, wheels, caster, mic array, camera board, speaker, and motor controller.
- Create simple dummy blocks in CAD for each component.
- Print small fastener/insert test coupons.

### Phase 1: Flat Layout

- Print `electronics_deck` only.
- Mount Pi, regulators, motor controller placeholder, and cable ties.
- Verify tool clearance for every screw.
- Confirm HAT/cooling keepout using a printed gauge.

### Phase 2: Rolling Skeleton

- Print `base_tray`, `motor_pod`, `battery_cradle`, and caster mount.
- Mount motors, wheels, caster, and battery dummy.
- Roll by hand and check wheel clearance, caster swing, balance, and bumper envelope.
- Do not power motors until mechanical binding is gone.

### Phase 3: Bumper And Sensors

- Print `bumper_carrier` and two or three `tof_sensor_pod` variants.
- Mount switches and confirm actuation before hard contact.
- Check front/side sensor angles from real floor height.
- Verify sensor pods are protected from normal bumps.

### Phase 4: Head And Audio Fit

- Print `camera_head_bracket`, mic mount, and speaker grille.
- Verify camera ribbon path and bend radius.
- Check head/mast wobble while rolling by hand.
- Keep high-mounted mass low until the base is stable.

### Phase 5: Service Shell

- Print top shell/service panels after wiring routes are known.
- Add labels, access holes, ventilation, and fastener locations.
- Confirm the robot can be opened without removing wheels or the battery first.

## 12. Fit-Check Tests

Run these before calling any body revision "good":

### Mechanical Fit

- All screws install without forcing plastic.
- Inserts seat cleanly without bulging walls.
- Pi USB, power, camera, and GPIO access remain reachable.
- Camera ribbon has a protected route with no sharp bends.
- Battery can be removed without unplugging unrelated electronics.
- Wheel removal does not require full chassis teardown.
- Caster rotates freely at all body angles.
- No printed edge cuts into wire insulation.

### Clearance

- Wheels clear body by at least 3 mm static and more if tire flex is expected.
- Bumper has 5-10 mm travel before hard contact.
- Ground clearance is at least 15 mm under loaded weight.
- Pi cooling intake and exhaust are not blocked.
- Future HAT keepout remains open with top shell installed.
- Camera FOV is not blocked by head shell, mast, or bumper.

### Stability

- Robot does not tip with normal acceleration/braking targets.
- Robot does not tip when the head turns or tilts.
- Robot survives a gentle hand push from front, side, and rear without exposing wiring.
- Battery cannot escape under a firm shake test.

### Safety

- E-stop can be reached quickly from normal standing/kneeling positions.
- Bumper switches trigger before rigid body contact.
- No wheel pinch points are exposed where fingers naturally grab the robot.
- Carry points do not flex enough to crack printed layers.
- Motor wires cannot reach the wheels.

## 13. Export Workflow

Generated exports should not be hand-edited. Source files are the truth.

Recommended structure:

```text
cad/
  openscad/
    robot_params.scad
    base_tray.scad
    electronics_deck.scad
    battery_cradle.scad
    motor_pod.scad
    bumper_carrier.scad
    tof_sensor_pod.scad
    camera_head_bracket.scad
  python/
    robot_params.py
    README.md
    requirements.txt
  exports/
    stl/
    step/
    preview/
```

OpenSCAD export examples:

```bash
openscad -o cad/exports/stl/base_tray_v0.1.stl cad/openscad/base_tray.scad
openscad -o cad/exports/stl/electronics_deck_v0.1.stl cad/openscad/electronics_deck.scad
```

For Python CAD, scripts should export both inspection and print artifacts when possible:

```bash
source .venv-cad/bin/activate
python cad/python/export_parts.py --part camera_head_shell --format stl
python cad/python/export_parts.py --part camera_head_shell --format step
```

Use semantic-ish revision tags for printed files:

```text
base_tray_v0.1_fit.stl
base_tray_v0.2_motor-clearance.stl
base_tray_v0.3_petg-candidate.stl
```

Keep slicer/project files out of source unless a print profile becomes important enough to document explicitly. STL exports are build products; the CAD source and parameter files are the design.

## 14. Initial Open Questions

- Exact 3D printer model and build volume.
- Actual motor, wheel, caster, battery, speaker, mic array, and sensor part choices.
- Whether the first camera head is fixed, pan-only, or pan/tilt.
- Whether the base should fit a future 2D LiDAR from day one.
- Preferred filament for functional parts: PLA+, PETG, or another known-good material.
- Whether a charging dock should influence rear geometry now or wait until after rolling MVP.

These should be answered through measurements and first prints, not abstract debate. CAD is where optimism goes to become caliper readings.

## 15. Definition Of Done For Mechanical CAD v0

Mechanical CAD v0 is complete when:

- Shared parameters exist.
- Base tray, electronics deck, battery cradle, motor pods, bumper carrier, sensor pods, and camera head bracket exist as source files.
- Each required module exports to STL without errors.
- A flat electronics deck print can mount the Pi and demonstrate HAT/cooling keepout.
- A rolling skeleton can be assembled and pushed by hand.
- Bumper travel and switch trigger geometry can be physically tested.
- Safety-critical limitations are documented on the relevant parts.
- The design reserves space for AI HAT+ 2, better cooling, and future navigation sensors without requiring them for MVP.
