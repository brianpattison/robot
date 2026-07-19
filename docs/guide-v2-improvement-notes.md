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
  28-route nominal harness traveler with a red release gate, and executable
  27-step commissioning package. Exact harness terminals and measured lengths,
  MAX98357A mounting, NeoPixel installation, production motor/encoder outputs,
  released fuse values, physical photos, and signed commissioning results still
  require delivered hardware and bench evidence; the book remains a prototype
  preview until they exist.
- **F7. Builder usability follow-up. [fixed]** The 42-page book now adds a
  purchased-electronics visual matching page, 13 cut-apart plate/bin labels,
  an 18-row printable coupon qualification record, and QR links to the
  immutable `v2.0.0-prototype.2` Builder Release Index. That index generates
  the exact prototype BOM, artifact paths, bench commands, and open-gate list
  from the same authored shopping data as the book. The commissioning gate now
  checks fixed acceptance predicates as well as field presence, so a record
  marked pass still fails if (for example) protocol clear succeeded, a service
  cable remained connected, a clamp exceeded its limit, or mirror gap/recovery
  evidence was not observed.

## G. From-scratch buildability review (2026-07-19)

A cold-reader pass: can a stranger with only the PDF and a credit card reach a
finished dry build? Fixes shipped with release `v2.0.0-prototype.3`.

- **G1. Build source unreachable. [fixed]** The QR pointed at a tree URL on a
  then-private repo with no published releases. The repo is now public,
  `RELEASE_URL` points at the GitHub *release* page (downloadable 3MFs + PDF
  assets), and Chapter 2 tip 1 plus both QR captions now say where to download
  the files.
- **G2. BLOCKED rows read as shopping rows. [fixed]** R-ML24 horns, the
  D85MG/R-ML24 hardware pack, and the D36V50F6 regulator now carry qty
  "0 for now" and "DO NOT BUY YET" with a pointer to where the build pauses.
  Steps 18–19 gained red SOURCING GATE banners (STEP_NOTES, rendered above the
  moves so arrow numbering is untouched); step 12 tolerates the empty 6 V
  pocket explicitly.
- **G3. Wiring chapter presented as an executable step. [fixed]** TOC and
  road-to-robot copy now say "reference maps only"; a leading wire rule states
  no step in this book cuts a wire; the meter checklist is labeled a preview;
  steps 11/15/20 no longer promise wiring-chapter actions that don't exist.
- **G4. Missing tools/consumables. [fixed]** Chapter 1 tools now include the
  P1S printer itself, an M2 driver for the head pack, a heat-set insert tip,
  grease (applied in step 18 move 5), and zip ties; the TPU tip covers drying;
  the camera row names the Pi 5 22-pin cable.
- **G5. Consistency bugs. [fixed]** Step 2 insert accounting corrected
  (20 + 27 = 47, the neck/collar 6 were missing); step 20 says "head face" vs
  "body face panel"; cover chips read AGES 10+ WITH AN ADULT and ONE SCREW
  SIZE; "one screw, one key" copy admits the pack's M2 hardware.
- **G6. Electronics table overflow. [fixed]** The taller hold rows pushed page
  1 of 2 past the footer; the split now sends one more row to page 2.

## H. Prime-time pass (2026-07-19, release `v2.0.0-prototype.4`)

A full five-reviewer audit of the 42-page book (four page-range readers plus a
computed cross-consistency check), and the chapter the goal was missing: the
guide now ends at a robot whose brain is running, not just a dry body.

- **H1. Chapter 5 was an anticlimax — and the software path was absent.
  [fixed]** "Check & play" was one page ("admire, measure, and keep the battery
  out") plus the back cover. The chapter now carries the full bring-up a builder
  can do without a single open gate: p42 runs the shipped `robotd --simulate` +
  supervision dashboard on any Mac/Linux (Python 3.11+) with a real captured
  screenshot and a four-point read of the page; p43 condenses the Pi-5 appliance
  install (flash, Tunnel, three secret files, `install.sh`, attestations,
  two-UART proof, and what the installer deliberately refuses to do); p44 seats
  the resident copilot — full Pi authority, the firmware/physical floor it
  cannot cross, the journal, a replayable `--source agent` robotctl session,
  and the honest handoff to the commissioning gates. TOC, road-to-robot strip,
  and the ch4 opener hand-off updated to match; book is now 45 pages.
- **H2. The dashboard picture is evidence, not artwork.**
  `scripts/capture_dashboard_screenshot.py` boots the real simulator +
  dashboard, replays the narrated agent session, screenshots via headless
  Chrome, and fails if the blackbox doesn't contain that exact session (or if
  port 8072 is already occupied — a stale server would silently photograph the
  wrong state). Rerun after any dashboard UI change.
- **H3. Cross-consistency audit: all computed checks pass.** Screws (43 in-step
  + 4 deferred lid corners = 47 everywhere), inserts (20 + 27 with per-step
  batches matching the joint registry), pieces (40+4+1 on 13 plates, per-part
  counts vs registry), coupons (18 tests / 19 objects / 5 plates), friendly
  names (zero fall-throughs), TOC page numbers, and the release tag/assets all
  reconcile. Two nits fixed: the tools table hardcoded "47" (now `N_SCREWS`),
  and the dashboard was missing from the release index artifact map.
- **H4. Page-audit fixes (pp. 1–11).** Rear-hero red slivers behind the motor
  wheels are now explained in their callout (they are the red motor caps);
  the cooling-vent callout dot sits on the vent slots instead of the wall;
  "only fasteners you'll buy" caption reconciled with the M2 servo-pack
  hardware (the p3 copy already was); plate-6 spares parenthetical attached to
  the washer entry instead of dangling after "tilt bushing"; plates-page caption
  grammar; hardware-pack contents no longer list a redundant bare "screws";
  the 5 V regulator row now says the part is safe to buy while its wiring
  stays blocked (it read as self-contradictory next to the 6 V hold row); the
  6 V regulator silhouette tile says "skip for now" and the matching page
  admits small buys have no tile; and the coupon project page explains the
  "Body Primary PLA" try-out plate (D034's candidate family), with an optional
  candidate-spool row added to the filament table.
- **H5. Declined:** the plate manifest's TPU role string "battery pads"
  (singular part, but the pad frame carries four cushion pads and fixing the
  string means regenerating the tracked 3MF for a noun); the cream featureless
  screw thumbnail (reads fine at GATHER size, labeled everywhere); the
  footerless full-bleed chapter openers (a deliberate hero-page design); the
  tiny blackbox text inside the dashboard screenshot (the numbered callouts
  carry the meaning).
- **H6. The L/R axis badge was mirrored — the A1 bug class in the overlay.**
  Front-facing cameras put the robot's RIGHT on the image's LEFT, but the
  badge statically read "L ← FRONT → R"; on step 7 it actively taught a 180°
  MDDS10 rotation. `robot_axis_badge()` is now view-aware per step: front
  views read "R ← FRONT · IT FACES YOU → L", the two rear-camera steps keep
  the original, and the side-view Pico step shows no L/R badge at all (its
  horizontal axis is front-back). The "Front and back" primer now teaches the
  handshake flip, and the badge trigger uses word-boundary matching (it used
  to fire on "LEFTOVERS").
- **H7. The battery never left the renders.** Step 9 is a dry fit — the book
  removes battery, clamp, and pad — but the renderer only accumulated parts,
  so steps 10–16 showed them still installed (a picture-first builder would
  leave the battery in). `render_assembly_steps_v2.py` now withdraws
  dry-fit-only parts after their step (`REMOVED_AFTER_STEP`), and every step
  render was regenerated from freshly rebuilt v2 exports (the worktree's
  stale pre-D034 exports were rebuilt first — a render from them would have
  resurrected fixed geometry). Step 12's "notch goes around the battery
  wires" is now future-tense.
- **H8. The numbered-arrow system was redesigned after all three page
  auditors flagged it.** The magenta badges numbered arrow PAIRS in scene
  order, but the anatomy page teaches numbered MOVES — so readers paired
  arrow 2 with sentence 2 and executed wrong pairings on nine pages; several
  projected landings were also geometrically wrong (dots on wheel faces,
  floors, shadow gaps, or buried under detail insets). Arrows are now
  glyphless — the unbroken line pairs a tail dot with a landing ring, so
  nothing can be read as a move number or collide with "Detail A/B" panel
  letters — and `STEP_ARROW_TWEAKS` prunes, per part name, every arrow whose
  landing the audit verified as misleading (steps 1, 3, 5, 6, 7, 9–16, 18,
  19, 20). Surviving arrows: one or two per step that land on real visible
  destinations. The anatomy page and the Build opener now state the
  convention, and the wheel-bench page gained BACK/FRONT identification
  chips (its gold insert markers had been deliberately removed when the
  insert seat moved deep into the wheel, leaving the back wheels
  unidentifiable).
- **H9. Text/diagram truth fixes from the audit.** Step 3's check no longer
  claims gearmotor shafts "spin freely" (they drag through a 99:1 gearbox —
  it contradicted step 6's motor-holds-the-wheel check) and its wire move no
  longer depends on wires the proxies don't render; step 4's port-over-well
  check is now the tactile hex-key probe; step 8 points the head-cable
  promise at step 19 (in-book) instead of "later"; step 9 admits the four
  floor pads hide behind the tower; step 15 explains the see-through light
  slots (the "mystery green square" is the interior until step 20 — truthful,
  now narrated); step 17 disambiguates the lid's two round holes (button vs
  neck); step 18's check names the neck, not an unintroduced "shoulder";
  the glow-board inset says LATER; the power-map relay row's destination is
  the coil (status moved into the middle column); the p39 diagram's
  branch-feed and motor-fuse wires are drawn RED per its own legend (they
  were blue/green/yellow); Detail B's washer is printed-cream (not
  annotation-magenta) with its 22 mm dimension spanning the washer, not the
  wheel; three inset labels got unclipped leaders; the ch5 opener ship list
  is now plain language; and the copilot page explains both drive arguments.
