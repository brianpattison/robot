# Builder's Book v2 — Review Findings and Improvement Plan

A full page-by-page review of `output/pdf/codex_robot_body_v2_assembly_guide.pdf`
(originally 37 pages), the step renders in `docs/images/guide_v2/`, the hero renders, and the
v2 CAD model behind them. Findings are grouped by root cause; each has the fix
applied (or proposed). Items marked **[fixed]** were implemented in this pass.

## A. Real model/content bugs (would mislead a builder)

- **A1. Left/right directions mirrored for the deck-area electronics.** The robot
  faces −X, so the robot's RIGHT is +Y. Several instructions used the mirrored
  convention. Per the registered inventory (`robot_body_v2_inventory.py`):
  - Fuse block sits on the deck's **left** half (Y −67..−23), wire service off the
    **left** edge — the book said "right half" / "wire exit RIGHT edge" (steps 12,
    p32 table). **[fixed]**
  - MDDS10 terminal service faces +Y = robot **right** — the book said terminals
    face LEFT (step 7, p32). **[fixed]**
  - Regulators hang under the deck's **rear** portion (X 60..112), and the 6 V
    wire service faces −X = **front** — the book said "right end" and "6 V wire
    exit LEFT" (step 12, p32). **[fixed]**
  - Pico USB corridor faces +X = robot **back** — the book said "USB plug facing
    RIGHT" (step 10, p32). **[fixed]**
  - The controller tower spans the tray's front **center** (Y ±59), not
    "front-left" (step 7). **[fixed]**
  - Correct as written (checked, unchanged): relay on the left, battery wires to
    the back, Pico to the right of the tower, deck notch at back-right.
- **A2. Eye diffuser bar cannot reach the eyes.** The head faceplate's two eye
  slots sit at Y ±40 (80 mm apart, 9 × 14 mm each), but `build_eye_diffuser_bar`
  was a 30 mm bar with pads at ±5 — physically unable to serve both eyes, while
  the part registry says "both eye diffusers as one bar". Rebuilt as a 98 mm bar
  with one 8.4 × 13.4 mm pad entering each slot. **[fixed]**
- **A3. Status diffuser bar pads had zero clearance.** 10 mm pads into 10 mm
  fascia slots. Pads resized to 9.4 × 4.4 mm for a real snap fit. **[fixed]**
- **A5. Rear clamp screw buried under the tire.** The rear wheel's radial
  clamp-screw bore exits at the rim's surface (wheel Y-center), and the TPU
  tire is exactly the wheel's width — once the tire is stretched on, the screw
  hole is covered and step 6 ("push the wheel on, then tighten the clamp
  screw") is impossible. The guide's "little bump on the rim" never existed in
  the model. Fixed by molding one 7.2 mm radial access port into the tire
  tread: melt the rim insert with the tire off (step 4 already orders it that
  way), align the port over the screw hole when stretching the tire on, and
  drive the clamp screw through the port in step 6. All four tires share the
  design; the front pair's port is simply unused. Steps 4/6 text updated.
  **[fixed]**
- **A6. Neither wheel retention actually worked (Brian's catch, 2026-07-17).**
  Looking at the step-4 render, Brian asked how the tire insert could possibly
  work — and checking the numbers showed the whole retention stack was fiction:
  - *Rear:* the clamp-screw insert bore opened at the rim surface, so an
    M3 × 8 threaded into it ended ~12 mm short of the motor shaft. The screw
    would spin in free air. The bore is now a stepped well — a 7.4 mm
    head/tool channel from the rim, the 4.6 mm insert seat deep in the wheel,
    and tip clearance ending 0.3 mm past the shaft flat, so the single-SKU
    M3 × 8's tip presses the flat snug. The insert drops down the well and is
    pressed home with the iron tip (still with the tire off, as step 4 orders).
  - *Front:* the printed washer was 8 mm OD — smaller than the front wheel's
    18.5 mm bore, so it retained nothing; the wheel could slide straight off
    past it. It is now a 22 mm OD × 3.2 mm cap washer that overlaps the bore
    lip, and its 3.2 mm face makes the front-axle joint honest against the
    D026 clamp-stack rule (the old 1.6 mm washer violated it).
  Steps 4/6 rewritten to match; step 2 now explains that the gold pegs in the
  pictures are pointers, not parts. **[fixed]**
- **A4. Piece names differ between the plate table (p8) and the piece chart
  (p10).** "deck / controller tower / pico clamp / tof clamp / head pan plate"
  vs "power deck / brain tower / safety-board clamp / sensor clamp / head bottom
  plate". A kid can't match them. Plate table now uses the same friendly names
  as everywhere else. **[fixed]**

## B. Step-render correctness bugs

- **B1. Stray gold dot on the tray in steps 5–12.** The brass-insert proxy
  (`px_insert`, spec location 0,0,60) was appended to the `placed` list after
  step 2, so it rendered mid-tray in every later step. Fastener proxies are no
  longer placed. **[fixed]**
- **B2. Floating clamp bars in the chassis hero render** (Build-It opener p11,
  wiring p32, back cover p37). The chassis view hides the shell but kept the
  speaker/ToF/battery/pico clamp bars, which clamp purchased parts that are not
  in the base scene — so bars float in mid-air. The chassis view now hides
  clamp-type parts too. **[fixed]**
- **B3. Six feeler switches, one proxy.** Step 14's GATHER says ×6 but the scene
  had a single switch proxy (and it was invisible in the shot). Six switch
  proxies now sit in the six real tray pockets, and the step camera is a low
  angle that shows them entering the pockets. **[fixed]**
- **B4. Front distance boards never rendered.** Step 15 lists ×2 front ToF
  boards, but no proxies existed at the front stations; the check line "two tiny
  lenses look out of the face" had no visual support. Front ToF proxies added
  behind the fascia apertures. **[fixed]**
- **B5. Lime light bars absent everywhere.** The diffuser bars were exported
  unplaced and hidden in every render, so the fascia/status slots showed the
  interior (a green Pi surface read as a mystery green square on p27/p28), and
  the "meet the robot" caption pointed at glowing bars that don't glow. The
  bars are now placed (fascia + head) with an emissive lime material in the
  assembled/rear heroes and in steps 15+. **[fixed]**

## C. Step-render clarity (the "renderings don't look right" list)

- **C1. No visual link between a floating part and its destination.** The
  LEGO-style "pop" offsets parts 32 mm, but nothing points at the landing spot —
  ambiguous for the motors (which cradle?), pods, Pico, relay, deck, shell, lid,
  head. The final renderer exports normalized part/destination coordinates
  from the evaluated camera, and the guide draws crisp numbered magenta 2D
  arrows with matching numbered landing dots. This removes shadow, occlusion,
  and perspective-scale ambiguity while keeping every pointer registered to
  the actual CAD scene. Dedicated detail panels replace dense arrows where a
  hidden interface needs a section. **[fixed]**
- **C2. Pops along the wrong axis.** Wheels/washers popped straight up (+Z) even
  though they slide sideways onto shafts; bumper halves popped up instead of
  wrapping front/back; the deck pop (+32) left the deck impaled on a tower;
  speakers popped to exactly rim height, reading as "parked on the rim edge".
  Pops are now per-part: wheels/washers pop outboard ±Y, bumpers pop ±X,
  deck/shell/lid pop higher (+55..70), speakers pop above the rim with the
  interior camera. **[fixed]**
- **C3. Wheel-prep step (4) rendered parts scattered at assembly stations in
  mid-air** at wildly different distances (one giant foreground tire, one wheel
  cut off, phantom shadows). The bench step now lays the four wheel+tire
  assemblies flat on the floor in a neat 2×2 grid at matched scale, back-wheel
  hub inserts marked in gold. **[fixed]**
- **C4. Insert locations only marked for the tray.** Step 2's "gold marks every
  spot" convention was dropped for the shell's 14 inserts (step 13), the lid's 2
  (step 17), the wheels' 2 (step 4), the pods' 2 (step 5), and the head's 1
  (step 19). All insert batches now render gold markers; steps 13 and 17 get an
  **inset panel** (shell alone / lid flipped) showing every insert spot.
  **[fixed]**
- **C5. Cameras bury the action.** One "body" camera serves 12 steps, so small
  parts (Pico, relay, regulators) are far away and the same picture repeats;
  meanwhile the CSS zooms every image to 118%, cropping wheels (pp. 17–23) and
  the E-stop (pp. 28–29). Camera set expanded (interior view for speakers, low
  bumper view, tighter deck/tower framing), and the CSS zoom dropped so the
  full frame shows. **[fixed]**
- **C6. Proxy shapes too abstract to orient.** The Pi was a featureless green
  slab ("USB ports face BACK" — invisible); the MDDS10 was pink though the text
  says "purple board with green terminal blocks"; motors were plain cylinders
  (no shaft to point OUT); the camera was a green slab (reads as a PCB, not a
  lens). Proxies upgraded: Pi gets a dark port block, MDDS10 is purple with a
  green terminal strip on its right edge, motors get silver shafts, the camera
  gets a dark lens barrel, the relay gets its bracket flange. **[fixed]**
- **C7. Hero crops decapitate the robot.** The rear hero camera cut the head at
  the frame top (p2 "from the back", also echoed on p36); the cover crop is
  intentional but the meet-page needs the whole robot. Rear/assembled cameras
  pulled back and re-aimed; meet-page callout percentages re-tuned. **[fixed]**
- **C8. Dark plates unreadable on p7.** Charcoal/TPU parts on Bambu's dark plate
  thumbnails are nearly invisible (plates 7, 9–11). The contact-sheet generator
  now lifts the shadows on dark thumbnails so silhouettes read. **[fixed]**

## D. Guide text / layout improvements

- **D1.** Step 10 checked "USB port is reachable" while the wiring chapter is the
  only time it's needed — reworded to match the correct orientation (A1) and
  when it matters. **[fixed]**
- **D2.** Step 12 re-ordered to match the fixed geometry: regulators under the
  rear half, fuse box on the left half, wire tail over the left edge. **[fixed]**
- **D3.** Step 18's collar/servo work is invisible under the lid; the text now
  tells the builder the picture shows the hole they reach through, and the
  neck-cam frames the lid hole without cropping the E-stop. **[fixed]**
- **D4.** Step 1's orientation anchor ("motor cradles at the back") now matches a
  render with the FRONT arrow overlaid at the tray's front edge (the chip alone
  was easy to miss). Implemented as part of C1's arrow system. **[fixed]**
- **D5.** Meet-page callouts re-anchored after the hero reframe (C7). **[fixed]**

## E. Noted, deliberately not changed (for discussion)

- **E1.** The head render on the cover is cropped tight on purpose (styling); the
  uncropped robot appears on p2.
- **E2.** MAX98357A mounts, channel straps, terminal service, and strain relief
  remain an explicit prototype hold; the current book no longer invents a
  zip-tie location.
- **E3.** Step 14's bumper halves genuinely float loose by design (they squish to
  press the switches); the check line covers it.
- **E4.** Superseded by D034/D035: the live manifests now report 40 installed
  functional pieces + 4 spare washers + 1 optional skin = 45 pieces, 47 M3
  screws/inserts, 13 plates, seven material/color groups, and 18 coupons.
- **E5.** A dedicated wiring-photo appendix (real harness photos) would help
  once a physical build exists; out of scope for renders.

## F. External assembly-review follow-up (2026-07-17)

- **F1. Prototype truthfulness. [fixed]** Cover, README, 3MF notes, wiring,
  software, fuse, and commissioning pages now distinguish dry-build geometry
  from powered-motion release. Page topology is Pi/`robotd` -> Pico framed UART
  -> MDDS10; Pico USB/SWD are service-only.
- **F2. Hybrid materials. [fixed]** D034 separates family, role, and theme;
  direct PLA, qualified PLA candidates with automatic PETG fallback, the
  optional lid skin, 18 evidence coupons, per-family plates, and exact counts
  all derive from the canonical inventory.
- **F3. Head mechanism. [CAD fixed; physical gates open]** D035 replaces every
  placeholder with a three-lug collar, printed pan journal/thrust face,
  integrated servo cradle, two-M3 pan plate, horn drive, 20 mm ribbon corridor,
  four-M3 yoke, drawing-backed tilt-servo frame, active shell boss, passive
  shoulder bushing, and physical pan/tilt stops. The validator samples actual
  solids through both commanded ranges and proves stop engagement beyond them.
- **F4. Head instructions. [fixed]** Steps 18–19 now list both R-ML24 horns and
  the verified component hardware pack, give an ordered servo/horn/bushing
  sequence, and use separate pan, tilt, passive-pivot, and camera panels.
- **F5. Render legibility. [fixed]** Every assembled hero retains the dark
  camera lens; white PETG gets a temporary cool-grey instructional tint and
  stronger rim; page 32/back use a populated cutaway. Close panels now cover
  Pico orientation, regulator/fuse sides, all six bumper switches, rear panel,
  audio, the full E-stop stack, pan, tilt, and camera. Dimensioned vector
  sections now expose the rear-wheel well and shaft clamp, front cap washer,
  bumper stroke/stop, fascia back, audio orientation, E-stop load path, and
  status-light order. Numbered arrows are exported from the real camera scene.
- **F5a. Coupon project and records. [fixed as an artifact; evidence open.]**
  The 18 logical qualification tests now ship as a tracked five-plate Bambu
  project with 19 material-correct objects; the PETG tire core and TPU ring are
  separate. The book shows the project before the test tables and requires
  machine/filament/settings/result/tester/date records.
- **F6. Executable artifacts fixed; physical evidence still open by design.**
  The repo now ships the framed v1 UART contract, local `robotd`/installer,
  host-tested portable Pico safety core, deliberately fail-stopped Pico target,
  27-conductor nominal harness traveler with a red release gate, and executable
  27-step commissioning package. Exact harness terminals and measured lengths,
  MAX98357A mounting, NeoPixel installation, production motor/encoder outputs,
  released fuse values, physical photos, and signed commissioning results still
  require delivered hardware and bench evidence; the book remains a prototype
  preview until they exist.
- **F7. Builder usability follow-up. [fixed]** The 42-page book now adds a
  purchased-electronics visual matching page, 13 cut-apart plate/bin labels,
  an 18-row printable coupon qualification record, and QR links to the
  immutable `v2.0.0-prototype.1` Builder Release Index. That index generates
  the exact prototype BOM, artifact paths, bench commands, and open-gate list
  from the same authored shopping data as the book. The commissioning gate now
  checks fixed acceptance predicates as well as field presence, so a record
  marked pass still fails if (for example) protocol clear succeeded, a service
  cable remained connected, a clamp exceeded its limit, or mirror gap/recovery
  evidence was not observed.
