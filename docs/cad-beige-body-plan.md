# CAD Plan: Beige Robot Body (build123d)

## 1. Purpose And Scope

Model the **main beige robot body** from the concept render in `build123d`: the large
rounded-box enclosure that is the visual mass of the robot. This is the shell that maps
to the `top_service_shell` role in [`cad-mechanical-plan.md`](cad-mechanical-plan.md) —
the visible upper enclosure, not the black lower base/bumper, not the wheels, not the
camera head.

**In scope (the beige shell and the features cut into it):**

- Rounded cuboid outer form with generous, render-matching fillets.
- Recessed top pocket that seats the teal plate.
- Neck/collar bore (camera head rises through it).
- E-stop bore.
- Vent louvers on the top.
- Front sensor recess (black bar + two LED windows).
- Corner screw points for the top plate.
- Lower mating edge that locates into the black base/bumper.

**Out of scope (separate modules, modeled later if wanted):**

- Camera head + neck/boot.
- Teal top plate as its own part (Stage B seats it; the plate itself is a separate model).
- Black base tray / bumper carrier.
- Wheels and hubs.
- E-stop switch, LEDs, and sensor boards (we model their pockets/bores, not the parts).

### Two-Stage Approach

Per the chosen direction, one script evolves through two stages:

- **Stage A — Visual outer form.** A single solid whose silhouette, fillets, and feature
  placement match the render at a 3/4 view. Goal: lock proportions and styling. Not
  hollow, not print-ready.
- **Stage B — Printable enclosure.** Evolve the same script into a real, hollow,
  serviceable printed part: walls, plate seat with screw bosses, functional bores, base
  mating lip, broken edges, interior keepouts.

Why `build123d` and not OpenSCAD: the render's look is compound fillets on a shelled
curved shell (pillowy top edges, filleted pocket, blended bores). That is exactly the
"nicer fillets / BREP shell / STEP export" case the mechanical plan reserves for Python
CAD.

## 2. Design Intent: Spec Envelope, Concept Styling

Keep the **functional envelope** from the mechanical plan, but bias **cosmetic detail**
toward the render's softer, chunkier look. When the two conflict, the envelope wins and
we buy back "chunky" with fillet radius, not with extra millimeters.

| Aspect | Source | Value / Note |
| --- | --- | --- |
| Footprint length x width | Spec (fixed) | 300 x 220 mm |
| Total height excl. head | Spec (cap) | <= 120 mm; beige body is the tall upper share of this |
| Wall thickness | Spec | 3 mm walls, 4 mm floor |
| Vertical corner radius | Concept (cosmetic) | ~22 mm (spec base uses 8 mm; render is pillowy) |
| Top perimeter fillet | Concept (cosmetic) | ~14 mm rounded top edge |
| Teal-plate inset border | Concept (cosmetic) | ~16 mm beige frame around the plate |
| Fastener sizes / keepouts | Spec | M3 heat-set (4.8 mm OD, 5.7 deep), Pi/HAT keepouts unchanged |

**Reconciliation note:** the render is proportionally *taller* than the 120 mm cap
allows once the black base is subtracted. We honor the cap and achieve the chunky read
through large corner/top fillets and by keeping the visible black base shallow — not by
exceeding the envelope.

## 3. Feature Inventory (from the render → CAD operation)

| # | Feature | Render cue | CAD operation |
| --- | --- | --- | --- |
| 1 | Outer form | Rounded cream box | `Box` + fillet vertical corners + fillet top perimeter |
| 2 | Teal-plate seat | Inset top plate with beige frame | Rounded-rect pocket cut on top face |
| 3 | Neck collar bore | Circular hole, black boot, front third | Circle cut on top; Stage B adds collar/boss |
| 4 | E-stop bore | Red mushroom, top rear-right | Circle cut on top; Stage B adds reinforced ring |
| 5 | Vent louvers | ~12-16 parallel slots left of E-stop | `GridLocations` of thin rounded slots, cut |
| 6 | Front sensor recess | Black bar + 2 green LEDs, front face | Rounded-rect pocket on front face + LED bores |
| 7 | Corner screws | Fasteners at plate corners | 4 bosses + insert holes at plate corners |
| 8 | Base mating edge | Beige tucks into black base | Bottom lip/rim (Stage B) |

## 4. Coordinate And Orientation Convention

- **+X = forward** (toward the camera/front sensor bar), **+Y = left**, **+Z = up**.
- Origin at the **geometric center of the footprint**, `z = 0` at the **bottom mating
  plane** of the beige body (where it meets the base). Body extrudes up in +Z.
- Cross-reference: the spec measures `axle_x` "from the front edge." Front edge is at
  `x = +150`; rear edge at `x = -150`. Keep a helper to convert front-referenced spec
  numbers into centered coordinates so we never fork dimensions.

## 5. Tooling And Environment

`build123d` is **not** installed here and the system Python is 3.9.6 (too old). Per
[`README.md`](../README.md) / [`AGENTS.md`](../AGENTS.md):

```bash
brew install python@3.12
/opt/homebrew/bin/python3.12 -m venv .venv-cad
source .venv-cad/bin/activate
python -m pip install --upgrade pip
python -m pip install -r cad/python/requirements.txt   # build123d, cadquery
```

Files to create:

```text
cad/python/
  robot_params.py     # shared dimensions, mirrors the OpenSCAD contract (Section 6)
  beige_body.py       # the model; build_stage_a() and build_stage_b()
  export_parts.py     # CLI: --part beige_body --stage a|b --format step|stl|3mf
```

Preview: `ocp_vscode` (`show()`) for interactive dev; optional headless PNG into
`cad/exports/preview/` (trimesh/pyrender or VTK offscreen) for side-by-side against the
render.

**Before writing geometry, confirm the current `build123d` API against the installed
version** — builder-mode helpers (`fillet`, `offset` openings, edge selectors like
`.filter_by(Axis.Z)` / `.group_by(Axis.Z)`) have shifted across releases.

## 6. Parameters (`robot_params.py`, proposed starting values)

Mirror the mechanical-plan contract; add a clearly-labeled **cosmetic** block. All mm.
These are starting points to iterate in Stage A, not final.

```python
# --- Functional envelope (from cad-mechanical-plan.md) ---
BASE_LEN = 300
BASE_W   = 220
WALL_TH  = 3
FLOOR_TH = 4
BEIGE_BODY_H = 90          # tall upper share of the <=120 mm total (tune vs base height)

# --- Cosmetic styling (from the render) ---
BODY_CORNER_R    = 22      # vertical edges
BODY_TOP_EDGE_R  = 14      # top perimeter
BODY_BOTTOM_R    = 4
PLATE_MARGIN     = 16      # beige frame width around teal plate
PLATE_POCKET_D   = 2.5     # Stage A visual inset depth

# --- Bores / features ---
NECK_BORE_D   = 48;  NECK_X = 95   # from front edge -> convert to centered X
ESTOP_BORE_D  = 22.5; ESTOP_X = 235; ESTOP_Y = -60
VENT_SLOT_L = 30; VENT_SLOT_W = 3; VENT_COUNT = 14; VENT_PITCH = 5
SENSOR_REC_W = 150; SENSOR_REC_H = 26; SENSOR_REC_D = 6; LED_D = 10

# --- Fasteners (from spec) ---
M3_INSERT_D = 4.8; M3_INSERT_DEPTH = 5.7; BOSS_OD = 8
```

If `cad/openscad/robot_params.scad` gets created later, keep the shared values in sync —
do not fork dimensions silently.

## 7. Stage A — Visual Outer Form

1. `Box(BASE_LEN, BASE_W, BEIGE_BODY_H)` aligned centered in X/Y, min in Z.
2. Fillet the 4 vertical edges (`edges().filter_by(Axis.Z)`) with `BODY_CORNER_R`.
3. Fillet the top perimeter (`edges().group_by(Axis.Z)[-1]`) with `BODY_TOP_EDGE_R`.
   Order matters and large radii can fail on already-filleted corners — do vertical
   first, validate, then top; reduce radius if the kernel complains.
4. Optional small bottom chamfer/fillet (`BODY_BOTTOM_R`).
5. Teal-plate inset: sketch a rounded rectangle on the top face (inset `PLATE_MARGIN`),
   extrude-cut `PLATE_POCKET_D`.
6. Neck + E-stop bores: circles on the top face at their locations, cut through.
7. Front sensor recess: rounded-rect pocket on the front face + two LED bores.
8. Vents: `GridLocations` of thin rounded slots between neck and E-stop, shallow cut.

Deliverable: `beige_body_v0.1_form.step` / `.stl` + a preview PNG. **Iterate the
cosmetic params against the render until the silhouette reads right.**

## 8. Stage B — Printable Enclosure

Evolve the same script (`build_stage_b()` reuses the Stage A outer solid):

1. **Shell it:** `offset(amount=-WALL_TH, openings=<bottom face>)` → hollow, open bottom
   (or a modeled floor at `FLOOR_TH`). Validate manifold/watertight after shelling —
   shelling a heavily filleted box can produce bad geometry; back off radii if needed.
2. **Plate seat:** turn the visual pocket into a real ledge + 4 corner bosses
   (`Locations`) with `M3_INSERT_D` holes so the teal plate is removable.
3. **Neck collar:** internal boss/ring around the bore for the boot to clamp; cable
   pass-through.
4. **E-stop:** reinforced internal ring — **not a thin wall** (safety rule: E-stop
   mounting must not depend on a thin printed wall); preserve top *and* side access.
5. **Vents:** cut through to the interior; keep them on the Pi cooling exhaust path, not
   over a closed pocket.
6. **Front sensor recess:** real pocket with a mounting shelf + through windows.
7. **Base mating lip:** bottom rim/locating lip + screw tabs into the base tray.
8. **Finish:** fillet interior edges, break sharp outer edges (safety), honor the
   Pi/HAT/cooling keepouts from the spec.

Deliverable: `beige_body_v0.2_enclosure.step` / `.stl`, watertight and print-checked.

## 9. Export And Preview Workflow

- `python cad/python/export_parts.py --part beige_body --stage a --format step`
- Outputs: `cad/exports/step/`, `cad/exports/stl/`, `cad/exports/preview/` (all Git-ignored).
- Revision tags per the plan convention:
  `beige_body_v0.1_form.step`, `beige_body_v0.2_enclosure.step`,
  `beige_body_v0.3_print-split.stl`, ...
- Keep source (`.py`) as the truth; exports are build products.

## 10. Verification / Acceptance

**Stage A done when:**

- Bounding box footprint == 300 x 220 mm (assert in code).
- Silhouette, fillets, and feature placement match the render side-by-side at a 3/4 view.
- Solid is valid (`volume > 0`, `is_valid()`), exports STEP + STL without error.

**Stage B done when:**

- Watertight/manifold; min wall >= 3 mm (measure, don't eyeball).
- Teal plate is removable via screws; neck/E-stop/vent/sensor features are functional.
- Mates to the base lip; interior clears Pi/HAT + cooling keepouts.
- E-stop and battery-adjacent features respect the safety rules in the mechanical plan.
- Exports STL + STEP cleanly; sharp edges broken.

## 11. Open Questions To Resolve At Implementation

- Does "beige body" = only the `top_service_shell`, or the whole upper enclosure above
  the bumper line? Drives the height split.
- Exact black-base vs beige-body height split and where the parting line sits.
- Real E-stop model → actual mounting-hole diameter and mushroom-cap clearance.
- Neck boot outer diameter / whether a pan-tilt mechanism dictates the collar bore.
- Teal plate: separate printed/laser part or just a colored inset? Its footprint + screw pattern.
- Must vents align to the Pi fan exhaust path? That constrains their position.
- Do wheel arches intrude into the beige side walls, or stay entirely in the base?
- **Printer build volume:** 300 mm length likely exceeds a typical FDM bed. The spec
  flags keeping modules under ~220 x 220 mm unless volume is confirmed — the beige body
  may need to split into sections (front/rear or left/right), which reshapes Stage B.

## 12. Risks And Notes

- **Print splitting:** the 300 mm length probably forces a multi-part split with
  alignment features and joints — plan Stage B so a split is a parameter, not a rewrite.
- **Fillet + shell robustness:** large fillets followed by shelling is where the
  OpenCASCADE kernel most often fails. Keep radii adjustable, validate after each op, and
  be ready to reduce `BODY_CORNER_R` / `BODY_TOP_EDGE_R`.
- **Single-view proportions:** styling values are estimated from one 3/4 render and will
  need iteration; treat Section 6 numbers as a first guess.
- **Safety carries over:** even a "cute" shell obeys the mechanical plan's safety rules —
  E-stop reinforcement, no sharp edges near wires, cooling airflow preserved.
