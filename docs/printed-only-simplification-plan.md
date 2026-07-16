# Printed-Only Body Simplification Plan

Date: 2026-07-16
Status: direction accepted — Brian approved all three recommendations on
2026-07-16 (recorded as D025/D026/D027 in the decision log) and approved
the appearance deltas the same day. Three same-day Codex review rounds
invalidated the first three packing layouts; the current box screen
(layout v5, 238 x 220 x 133 on verified datums) closes with a 2 mm margin
policy including wall margins, and the review's process asks are folded
into Phase 2's exit. Round 4 (same day) reproduced the v5 screen,
verified the corrected datums, and GREEN-LIT Phase 2 with four explicit
carry-in requirements (see the review section). The D027 packing gate
itself remains OPEN pending the v2 BREP model + inventory-driven
validator. Phase 2 is now the active work.

## Goal

Rework the v1 body so that:

1. No purchased metal structure remains — no brackets, standoffs, spacers,
   shoulder bolts, bearings, hubs, washers, or locknuts.
2. The only fastener hardware is heat-set threaded inserts and screws, in
   exactly one thread size and one length each, bought in one order.
3. The printed-part count and print-plate count drop far enough that one
   person can print and assemble the body without a spreadsheet.

Electronics, motors, servos, switches, the battery, and hardware that ships
attached to a purchased component (the E-stop nut, the relay's integral
bracket, servo horns and horn screws, connector nuts) stay. The goal governs
*structural* hardware, not the electrical BOM.

D024 already removed *custom-fabricated* metal. This plan removes the
remaining *retail* metal and collapses the fastener system.

## Where The Metal Is Today

| Item | Qty | Role | Printed replacement |
| --- | ---: | --- | --- |
| Pololu #1569 motor brackets | 2 | Primary motor retention | Tray-integrated motor saddle + bolted clamp cap; motor's own tapped M3 face holes |
| Pololu #1997 aluminum hubs (+ set screws) | 2 | Shaft-to-wheel torque | Printed wheel core with integrated 4 mm D-bore hub + one radial M3 clamp screw |
| WDS 615-M6-8-65 shoulder bolts | 2 | Front idler axle | Printed stub axle integral to the idler pod |
| 608 bearings | 4 | Front idler rotation | Printed journal + replaceable printed bushing (wear part) |
| M6 washers + prevailing-torque locknuts | 2 sets | Idler axial retention | Printed retaining cap + one M3 screw into an axle-end insert |
| goBILDA spacers + shim | 2 sets | Idler axial stack | Printed spacer features integral to axle/pod |
| Koyo 6807-2RS pan bearing | 1 | Head pan support | Printed greased journal ring + printed thrust face; bayonet retainer |
| MF84ZZ flanged bearing | 1 | Passive tilt pivot | Printed shoulder bushing |
| McMaster 92981A143 shoulder screw | 1 | Tilt pivot pin | Standard M3 screw through the printed bushing into an insert |
| M2 metal standoffs (regulators 7, amps 4, Pico 4) | 15 | Board mounting | Printed pocket-and-clamp cradles; no board screws at all |
| M3 metal spacers/standoffs (controller plate 4+4, deck 4, motor brackets 6) | 14 | Elevation | Printed towers integral to tray/plates, M3 into inserts at the top |
| M2/M2.5 screws, washers, locknuts (LEDs, camera, vent, cartridges, head panels, race rings) | ~50 | Small-part retention | Printed pegs + clamp bars/snaps; M3 where a screw survives |
| M4 bolts (Blue Sea 5045) | 2 | Fuse-block mount | Printed saddle clamps over the block's base, M3 into deck inserts |
| M5-class bolt (relay 5.4 mm hole) | 1 | Relay mount | Printed pocket keyed to the integral bracket + M3 clamp tab |
| 20 mm textile battery straps | 2 | Battery retention | Printed PETG clamp bar + printed TPU pads, 2 M3 screws |

Current fastener sprawl: five thread sizes (M2, M2.5, M3, M4, M6), two insert
sizes plus a provisional M4, roughly 30 metal standoffs/spacers in three
sizes, plus washers and locknuts. Target: one insert SKU, one screw SKU.

## The Single Fastener System

Scope (tightened after review): the M3 insert and M3 x 8 screw are the only
**separately purchased body-fastener SKUs**. Hardware that arrives with a
purchased component — servo horn screws, the E-stop and connector nuts, the
relay's bracket hardware — is exempt, requires no separate purchase, and
keeps its own parameters in the model. The validator rule is therefore "no
separately-purchased fastener other than the two SKUs," not "zero non-M3
references."

- **Insert:** M3, 4.6 mm OD x 5.7 mm long (ruthex RX-M3 class — this matches
  the existing `insert_hole_m3 = 4.6` parameter, so calibrated coupon data
  carries over). One 100-pack.
- **Screw:** M3 x 8 mm socket head cap (ISO 4762), one 100-pack. One 2.5 mm
  hex key drives the entire robot.
- Estimated usage in the reworked body: ~60-70 of each, so single 100-packs
  with spares. The M3 x 16 escape hatch remains available but any use of it
  is a deliberate D026 amendment, not a quiet second kit.

Design rules that make one length work everywhere:

1. **Standard joint:** 3.2 mm printed flange over an insert boss gives
   ~4.5 mm engagement of the 5.7 mm insert. This is the default everywhere.
2. **Counterbore rule:** any flange thicker than 3.2 mm gets a counterbore so
   the screw always sees the standard joint. No second screw length exists,
   so the model must enforce this; add a validator check that every screw
   path presents 3.0-3.4 mm of clamped material.
3. **Engagement-limit rule (inverted counterbore):** where the screw enters a
   purchased part with limited thread depth — the Pololu #4867's two M3 face
   holes — thicken the printed flange locally so protrusion stays inside the
   documented maximum depth. Verify against the Pololu drawing during
   implementation.
4. **Printed washers:** anywhere a screw head would bear on TPU or a soft
   part, a printed PETG washer strip is part of the printed inventory.
5. **Screws clamp; geometry carries load.** Torque and shear always go
   through printed keys, D-bores, tongues, dovetails, and pockets. A screw's
   only job is to keep parts seated. This is what makes plastic-thread-free,
   single-size fastening safe.

## Design Language For Purchased Parts

- **Capture, don't screw.** Every PCB (Pi 5, Pico 2, both regulators, both
  MAX98357A amps, ToF boards, NeoPixel breakouts, camera module) sits in a
  printed pocket, located by printed pegs through its mounting holes, and is
  held by a printed clamp bar or frame whose screws are standard M3 into
  inserts *beside* the board. This deletes every M2/M2.5 screw and all 15
  metal standoffs, and no board hole ever sees a thread. The MDDS10 (3 mm
  holes) may keep direct M3 screws into insert towers since that is already
  the standard size.
- **Odd mounting holes become printed features.** The Blue Sea 5045 gets two
  printed saddle clamps hooking its base; the Panasonic relay's integral
  bracket drops into a keyed pocket with one printed clamp tab; each is
  secured by standard M3 joints. The purchased part is captured
  geometrically; its 4.5/5.4 mm holes are simply unused or used as locators
  for printed pegs.
- **Snap and bayonet for cosmetic/service parts.** Vent inlay, front fascia,
  pod covers, service covers, faceplate, and diffuser carriers move to
  snap-fit with release slots (a snap coupon gates this). The head neck gets
  a printed bayonet retaining collar instead of a four-screw retainer.
  Screws remain only where a joint is structural or safety-relevant.
- **Fallback geometry is insurance — stated precisely.** Each fallback has
  a different strength, and only the first three are true drop-ins:
  - Wheel core keeps the #1997 four-hole pattern and hub recess: the
    aluminum hub bolts back in unchanged.
  - Motor saddles keep the #1569 bracket's full installation envelope per
    side — the 49 x 22 base, all three M3 tray stations, the 3 mm spacer
    stack, and screwdriver access — as a registered fit volume in the v2
    model, so the bracket bolts back in unchanged. (Round-2 review point:
    preserving the holes alone is not a drop-in.)
  - Battery bay keeps its strap channels: textile straps return unchanged.
  - Idler bushing cavity matches the 608 envelope: a 608 can replace the
    printed bushing *on the printed axle* — this is NOT the old WDS
    shoulder-bolt stack, and the printed axle remains the load path.
  - Head pan journal has NO drop-in fallback: reverting to the 6807 bearing
    means reprinting the neck carrier and journal parts from a parametric
    switch kept in the source.

## Design For Fewer Parts And Support-Free Printing (D028)

Brian's directive (2026-07-16): minimize part count and print with as few
supports as possible. These are hard, validator-enforced requirements for
the v2 model, not preferences. v1 baseline: 101 printed parts, with the
shell quadrants and head shells requiring build-plate supports per the
print manifest's own guidance.

### Part-count budget

**Hard budget: <= 40 printed parts** for the complete robot (body + head +
TPU), excluding calibration coupons and explicitly optional cosmetic
variants. The inventory manifest carries the budget and the validator
fails when it is exceeded. Every separately printed part must carry a
one-line justification for existing: service access, material/color
change, print-orientation conflict, calibration interface, or wear-part
replaceability. "It was separate in v1" does not qualify.

Merges beyond the already-planned split-system deletion:

| Merge | Saves |
| --- | --- |
| Bumper switch plates -> pockets molded into the tray underside | 6 parts, 12 inserts, 12 screws |
| Harness rails -> deck underside ribs with strap slots | 2 parts |
| Pi shelf -> one controller-tower part with the MDDS10 plate | 1 part |
| Pico mount -> tray floor bosses + one clamp bar | 1 part |
| Motor pod shrouds + service covers -> shell wheel-arch region | ~4 parts |
| Front ToF pods -> fascia pockets | 2 parts |
| Side ToF pods -> shell pockets + clamp bars | ~2 parts |
| Cable strain plate -> deck/lid feature | 1 part |
| Wheel trim rings -> deleted (optional cosmetic) | 2 parts |
| Vent inlay -> optional (the lid slots print directly) | 1 part |
| Battery TPU pads -> one TPU pad frame | 1 part |

Draft v2 inventory under the budget: body ~26-30 parts + head ~10-12
parts (the printed pan journal already deleted the v1 carrier/retainer
stack). Integration risks to confirm during BREP: switch pockets in the
tray commit the 0.4/2.0/2.4 mm bumper interface to the tray print —
acceptable because the interface coupon is calibrated before any tray
prints; if it fails on the printed tray anyway, the recovery is a shim
plate, not a redesign.

### Support-free rules (enforced by the Phase-2 overhang audit)

1. Every inventory part declares its print orientation; all audits run in
   that orientation, and the print manifest inherits it.
2. Overhang rule: no downward-facing surface beyond 50 degrees from
   vertical outside allowlisted convex-rollover regions (dome-like
   continuous perimeters, which print support-free).
3. No enclosed horizontal cavities: every internal void opens up, down,
   or through a chamfered side.
4. Interior shelves and bosses on vertical walls carry 45-degree gussets.
5. Horizontal holes <= 8 mm print as-is; larger ones become teardrops or
   are redesigned onto vertical axes.
6. Bridges <= 30 mm; flat pocket ceilings chamfer where cosmetics allow.
7. Flat parts print cosmetic-face-down on the textured PEI plate.
8. TPU parts use open cross-sections — the bumper C-halves become
   open-bottom U-profiles with zero bridged cavities.
9. Insert bosses bias to vertical axes in print orientation; a horizontal
   insert is a design smell to eliminate, not accept.
10. The support-exception list starts EMPTY. Any part that needs supports
    requires a named entry with a reason and sign-off; the target is a
    zero-support inventory.

### Orientation strategy for the major parts

| Part | Orientation | Why it prints support-free |
| --- | --- | --- |
| Tray | flat, bottom down | Motor saddles are up-opening troughs; deck towers are vertical; underside switch pockets bridge <= 22 mm |
| Shell | upright, open bottom down | Walls vertical; the 12 mm top rollover is an allowlisted convex perimeter ending <= ~70 deg with the reveal/lid covering the last approach to horizontal; fascia/arch/grille/rear openings get chamfered or arched top edges; interior bosses gusseted |
| Lid | top face down | Underside bosses face up; recesses bridge small spans |
| Bumper halves (TPU) | flat | Open-bottom U-profile, no cavities |
| Head shells (2) | open face down | Convex dome regions allowlisted; internal ledges gusseted |
| Wheels | axis vertical | Radial clamp-screw boss tear-dropped |
| Front pods | outboard face down | Integral stub axle prints vertical; axle bending stress across layers is tiny at these loads (verify in BREP) |
| Plates, deck, panels, brackets | flat | Bosses up; ribs up |

### Validator additions

- Overhang audit: per part, in its declared orientation, measure
  downward-face area beyond the threshold outside allowlisted regions;
  any hit fails.
- Bridge-span audit on flat cavity ceilings.
- Part-count budget check against the registered inventory.
- The print manifest's support field must read "none" for every part not
  on the (initially empty) exception list.

## Subsystem Plans

### Rear drivetrain

Motor saddles print as part of the tray; a clamp cap (2 M3) closes over each
gearbox, and the two motor face screws (standard M3 x 8 through a locally
thickened flange per the engagement-limit rule) take the reaction torque.
Wheel cores integrate the hub: a calibrated 4 mm D-bore transmits torque
geometrically; one radial M3 into an insert boss clamps the D-flat for axial
retention only. TPU tires unchanged.

*Deletes:* #1569 brackets, #1997 hubs, 6 spacers, 8 wheel screws, set screws.
*Gates:* D-bore coupon must hold 2x the 11 kg-cm extrapolated stall torque at
temperature without creep or slip; clamp-cap retention shake/pull test;
motor-thread engagement depth verified against the Pololu drawing.
*Policy change:* printed pods become primary motor retention (see AGENTS.md
amendments below).

### Front support

Replace the entire shoulder-bolt/bearing/spacer stack with a printed stub
axle integral to each removable pod, a printed wheel riding on a replaceable
printed bushing, and a printed retaining cap fixed by one M3 into an insert
in the axle end. Loads are small (worst case ~1 kg per wheel) and journal
surface speed at 0.35 m/s robot speed is a few cm/s — well inside greased
PETG-on-PETG territory. The bushing is the designated wear part and a
five-minute reprint.

*Deletes:* 2 shoulder bolts, 4 bearings, all goBILDA spacers, M6 hardware,
8 M2.5 race-ring screws, race rings.
*Gates:* loaded skid-turn wear test (target: no measurable slop after a
defined drag distance on carpet), axle bending check at 2x load, retention
pull test. 608-envelope fallback cavity preserved.
*Alternative (simpler still):* fixed printed skid domes — zero moving parts —
at the cost of carpet drag. See open decision 2.

### Head pan/tilt

Pan: the rotating neck rides in a printed greased journal ring with a flat
printed thrust face carrying the ~0.3 kg head; a printed bayonet collar
retains it. The D85MG has 7x margin over the computed static torque, so
journal friction is affordable. Tilt: the passive side becomes a printed
shoulder bushing with a standard M3 acting as the pivot pin into an insert;
the active side keeps the servo horn. Use the horn hardware bundled with the
servos if serviceable; otherwise the R-ML24 remains an allowed
component-integral purchase (it is part of the servo interface, like the
E-stop nut).

*Deletes:* 6807 bearing, keyed carrier complexity, MF84ZZ, shoulder screw,
four-M2.5 retainer, M2.5 yoke inserts (become M3).
*Gates:* pan wear/current test over a defined cycle count (watch servo
current rise as the proxy for friction growth); tilt backlash check;
grease selection that is PETG-safe.

### Electronics mounting (tray + deck)

The controller plate, Pico shelf, and power deck all sit on printed towers
that print as part of their parent (tray towers rise to the deck datum;
plate-to-shelf towers print with the plate). Standard M3 joints at every
tower top. All small boards move to pocket-peg-clamp cradles per the design
language. Deck keeps the relay pocket and fuse-block saddles.

*Deletes:* all 29 metal standoffs/spacers, M4 bolts, relay bolt.
*Gates:* clamp-bar coupon (board seats firmly, no PCB flex over components,
connectors reachable); deck stiffness check under wiring loads; cradle
service test — every board removable with the hex key only.

### Battery retention

Cradle features print into the tray (the tray is one piece; see below). A
printed clamp bar with printed TPU pads spans the pack on two standard M3
joints. Strap channels remain in the geometry as fallback.

*Gates:* inverted shake and 15-degree tilt-with-drop test with a mass model;
pad compression set check after a week clamped. Note the AGENTS.md policy
amendment below — retention is printed-plus-metal-screws rather than
textile straps.

### Bumper and switches

TPU carrier, 0.4/2.0/2.4 mm switch interface, and six D2HW switches are
unchanged mechanically. Switch plates keep M3 but move from nuts to inserts
in the plates. The carrier splits into front and rear C-halves joined at the
side switch plates with printed dovetail laps (TPU compliance makes the seam
non-critical), so each half prints flat on the 256 bed without the current
four-quadrant, four-low-plate system.

### Shell, tray, lid — the part-count collapse

The 57-part split contract exists only because the 300 x 220 body exceeds
the 240 mm usable bed. Two options:

- **Option A (recommended): shrink the body to a ≤238 mm footprint** so the
  shell, tray, and lid each print as one piece. The entire split system —
  four shell quadrants, four wall plates, tray halves, underside plate, nine
  backing plates, 18 pilots, lap lid, and their ~44 seam inserts — is
  deleted, not simplified. Fairings merge into the shell as sculpted
  surface. The rear three-cartridge system collapses to one rear panel
  carrying the EN2 cutout, mute cutout, and blank region (4 M3 joints).
  Cost: a full interior repack. Battery (110 mm) plus controller stack
  (~105 mm) currently spans ~243 mm end to end, so ~15-25 mm must come from
  stacking the Pi over the battery bay or deck, letting the shell grow
  ~10 mm taller, and tightening keepouts. First CAD task is a packing
  study; if it will not close at ≤238 mm, fall back to Option B.
- **Option B (fallback): keep 300 x 220, split in halves.** Shell and tray
  each become two pieces with integrated lap flanges and insert-backed M3
  joints — no separate backing plates or pilot hardware. Roughly halves the
  split part count instead of deleting it.

Either way: lid one piece (A) or two-piece lap (B); vent inlay snaps in;
head shell parts already fit the bed.

### Print-plate simplification

Part-count reduction alone should take the 26-plate project down to roughly
10-14 plates. Consider printing the first article in a single PETG color
plus TPU (two material groups) to cut plate count further and save the
cream/teal/charcoal scheme for the second print; the plate manifest already
supports material-group regeneration.

## What Stays Purchased (Unchanged Policy)

Electronics and electromechanical parts: Pi 5, Pico 2, MDDS10, motors,
servos, camera, mic array, speakers, amps, ToF boards, NeoPixels, E-stop,
bumper switches, mute switch, EN2 pair, relay, fuse block, regulators,
battery, charger, wiring/connectors/zip ties (harness domain). Hardware that
arrives attached to or bundled with those parts (nuts, integral brackets,
horns, horn screws) does not count against the one-SKU fastener rule.

## Safety Policy Amendments (AGENTS.md + Decision Log)

This plan deliberately changes standing constraints; each needs an explicit
decision-log entry:

- **D025 (proposed): printed-only structure.** Supersedes "printed pods are
  removable shrouds, not primary motor retention," "plastic threads or
  friction fits must never retain the axle" (the axle cap is retained by a
  metal M3 screw in an insert; no plastic thread carries retention), and the
  metal-standoff requirements. Keeps: E-stop independence and its purchased
  nut, fail-stopped electrical architecture, no lifting by shell/head, and
  all electrical release gates. New printed structural parts get the test
  gates listed per subsystem above.
- **D026 (proposed): single fastener SKU.** M3 x 5.7 insert + M3 x 8 SHCS
  everywhere; validator enforces the 3.0-3.4 mm clamp-stack rule and the
  motor-face engagement limit.
- **D027 (proposed): one-piece body footprint** (or half-split fallback),
  superseding the 57-part split contract and the nine-plate pilot system.

Battery retention and motor retention move from "purchased metal required"
to "printed structure + metal screws/inserts, gated by the tests above."
If any gate fails, the preserved fallback geometry (the hub recess and
four-hole pattern, the full #1569 bracket installation envelope, the
608-on-printed-axle cavity, and the strap channels — see the precise
fallback list above) is the recovery path — not a redesign.

## Coupon Program Changes

Drop: 608 seat, 6807 seat/journal, Blue Sea M4 gauge (replaced by saddle-fit
gauge), M2.5/M4 insert and clearance coupons, split-pilot coupon (Option A).

Add: 4 mm D-bore torque coupon (print, mount on a motor, measure slip),
printed axle + bushing wear coupon, clamp-bar/PCB-pocket coupon (use the
Pico as the cheap test board), snap/bayonet coupon, saddle-clamp coupon for
the fuse block and relay.

Keep: M3 insert/clearance (data carries over), wall/lid-lap (Option B only),
bumper-interface, flush-fairing (deleted under Option A), TPU tire fit.

Net: seventeen coupons down to roughly eight.

## Execution Phases (revised 2026-07-16 after review)

The original order put the fastener pass before the v2 geometry existed,
which would have reworked every mount interface inside the old 300 mm body
and then thrown that detailing away. Revised order:

1. **Decisions + box packing screen.** DONE: decisions recorded
   (D025-D027); the box screen closed at layout v5 on verified datums
   after three review rounds (see review outcome above); Brian approved
   the appearance deltas 2026-07-16 (height subsequently revised
   144 -> 133 by the round-3 datum fix).
2. **v2 BREP packing model.** Build the 238 x 220 x 133 body skeleton in
   `robot_body.py` geometry: real shell/tray/lid solids, every purchased
   part from its drawing-backed envelope in the v5 layout, mount/support
   solids, wiring and service volumes (including the battery riser and
   fuse wire exit), thermal volumes, the full AI-HAT reserve, connector
   sweeps, printability checks (bed fit, orientation), and 3D CG /
   load-distribution acceptance from actual part masses. The validator
   must be **inventory-driven**: it enumerates a registered manifest of
   every purchased part and required service/thermal/harness volume with
   explicit clearance margins, so an envelope that was never registered is
   itself a failure — "passing" cannot mean "nothing I happened to model
   collided." It also enforces D028: the <= 40 printed-part budget, the
   per-part declared-orientation overhang and bridge audits, and the
   (initially empty) support-exception list. Exit — and this is the D027
   packing gate — that validator passing on the v2 model.
   Progress (2026-07-16): the registered inventory
   (`robot_body_v2_inventory.py`), the v2 model
   (`robot_body_v2.py`, 18 solids: tray with cradle/Pico
   bosses/molded-in switch pockets, shell with circular arches +
   mullioned openings + speaker ledges + ToF windows, lid with neck
   pass, TPU bumper C-halves with concealed bridges, front pods with
   vertical-printing axles, fascia and rear panels, the one-piece
   controller tower on a channeled plinth with a frame-and-crossbar Pi
   shelf, wheels, tire, and the five-part head skeleton with a domed
   cavity), and the inventory-driven validator
   (`validate_robot_body_v2.py`) are all green in dev mode. The
   validator has caught nine real design errors so far (tower
   placements x4, a battery-stop clip, the pod printing on its axle
   tip, the solid Pi shelf and floating MDDS10 plate as unprintable
   ceilings, and a mispositioned head cavity), and gained a solid-free
   thermal check plus a ring-aware bridge heuristic along the way. Update (same day, second slice): the four
   remaining estimates are eliminated (neck_drop now derives from the
   verified pan_servo_fit bbox; head_roof became the computed pan-sweep
   of the v2 head; the Pi/Pico service volumes are declared cable/tool
   specs), all six owed part merges are executed (the registry sits at
   exactly 40 parts with zero owed — the E-stop backing collar is now a
   lid-integrated boss in geometry), and the D026 fastener system is
   live: a FASTENER spec + nine-family JOINTS registry (30 screws + 30
   inserts total, all M3 x 8 into M3 x 5.7 inserts), every joint
   holding the 3.0-3.4 mm clamp stack, with modeled bosses, counterbores,
   and insert bores across the tray, shell, lid, towers, saddles,
   plinth, pods, rails, plus the motor-cap and battery-clamp solids
   (20 solids total). Validator PASSES IN GATE MODE on the encoded
   conditions (zero estimates, zero unmodeled joints). Still to encode
   before D027 can actually close: harness route volumes, connector
   insertion sweeps, real-mass CG acceptance, and a fresh external
   review round.
3. **Fastener-system pass on v2.** Collapse `Params` to the single
   insert/screw spec; add the clamp-stack (3.0-3.4 mm) and
   engagement-limit validator checks; implement capture-or-M3 mounts for
   every board and purchased part. Exit: validator passes and no
   separately-purchased fastener other than the two SKUs appears in the
   model or manifests (bundled component hardware is exempt and stays).
4. **Drivetrain + front support rework.** Motor saddles/caps,
   integrated-hub wheels, printed axles/bushings. Print and pass the
   D-bore and axle coupons before full parts.
5. **Body consolidation + exports.** Merged fairings, single rear panel,
   snap vent/fascia, bumper C-halves; regenerate `robot_body_split.py`
   (mostly deletions), `robot_body_print.py`, `robot_body_coupons.py`, the
   Bambu project, and the assembly-guide inputs.
6. **Docs + guide.** Update BOM (two fastener SKUs), component-coverage
   matrix, AGENTS.md conventions (full rewrite of superseded lines), and
   regenerate the assembly guide.

Each phase ends with the full regen chain (`robot_body.py` →
`robot_body_split.py` → `validate_robot_body.py` → `robot_body_print.py` →
coupons → Bambu project) per repo convention.

## Expected Outcome

| Metric | Today | Target |
| --- | --- | --- |
| Hardware SKUs beyond electronics | ~15 (brackets, hubs, bolts, bearings, spacers, standoff/screw/insert kits, straps) | 2 (one insert pack, one screw pack) |
| Thread sizes | 5 (M2, M2.5, M3, M4, M6) | 1 (M3) |
| Screw lengths | many (kit) | 1 (8 mm) |
| Tools for body assembly | hex keys, nut drivers, wrenches | one 2.5 mm hex key + soldering iron (inserts) |
| Printed parts | 101 | <= 40 (hard budget, D028) |
| Print plates | 26 | ~8-12 |
| Parts needing supports | shell quadrants + head shells (build-plate supports) | 0 (validator-audited; empty exception list) |
| Calibration coupons | 17 | ~8 |
| Hardware cost removed | — | roughly $120-280 (brackets, hubs, bolts, bearings, spacers, kits) |

## Resolved Decisions (2026-07-16)

Brian approved all three recommendations:

1. **Footprint:** Option A — shrink to a 238 x 220 one-piece body (D027).
2. **Front support:** passive printed wheels on printed axles, with fixed
   skids as the fallback if wear tests disappoint (part of D025).
3. **Screw length:** strictly one — M3 x 8 with validator-enforced
   counterbores; M3 x 16 remains an escape hatch only if a future joint
   genuinely cannot be counterbored (D026).

## Packing Study — Review Outcome (2026-07-16)

**The first study's FEASIBLE result was false and is withdrawn.** A Codex
review found, and spot-checks against `Params` confirmed exactly:

- It claimed to use `Params` but hardcoded reduced envelopes and omitted
  the E-stop's 66 mm panel/backing (at X=92 it reaches X=125, past the
  238-body edge at 119 and the rollover-limited roof flat at ~107), the
  28 mm battery-lead corridor (reaching X≈135.5), the required AI HAT+ 2
  reserve, real Pi connector/cable service (the vertical Pi left 9.8 mm
  below the inner roof), and keepout-keepout collisions.
- Its rotated MDDS10 kept a front-facing terminal corridor, which the real
  board cannot do: rotating the long axis to Y turns the terminal short
  edge toward a side. The exact 238 mm packing chain built on that
  orientation was invalid.

The study was rewritten (`cad/python/packing_study_printed_only.py`): it now
imports `Params`, models all of the above, checks keepout-keepout pairs, and
prints every conflict. Its layout v3 closed at the box level.

**Round 2 (same day): the v3 close was also rejected, correctly.** A second
Codex review found four more omissions, all verified against the source:
the mute switch needs 26 mm body + 16 mm terminal service = 42 mm (v3
reserved 28); the fuse block's 22 mm wire-exit service was absent entirely;
the MDDS10's 10 mm airflow contract was violated by 5.8 mm under the
full-width Pi shelf; and the AI-HAT reserve is 96 x 74 x 22 per
`cad-mechanical-plan.md`, not the 85 x 60 x 18 v3 used — so v3's +10 mm
height was unvalidated. It also rejected incidental 0.1-1 mm clearances and
the unmodeled battery-to-rear-connector riser. Rebuilding with those
envelopes (and a new wheel-envelope check that caught the rear axle at X=78
poking the wheel 2 mm past the 238 shell) produced layout v4 at a computed
238 x 220 x 144.

**Round 3 (same day): v4's datums were wrong, and it was rejected too —
verified against the model itself.** The tray top is Z=49 (`body_bottom`),
not 49+8: `motor_controller_plate_bottom_z()` returns 54 (= 49 + the 5 mm
plate lift), which puts the MDDS10 thermal ceiling at 86.275, not 95.845
(the old formula also double-counted the 1.57 mm PCB — `mdds10_above_pcb`
measures from the mount plane). The pan-servo drop bottom is 131.6
(`pan_servo_fit` bounding box), not 130, and the deck plate is 102..106
(`power_deck_z` ± 2). Round 3 also found the D24V90F5's two terminal
corridors missing (the north one overlapped the D36 by 4.6 mm), the
D36V50F6's wire corridor missing (east exit leaves the body by 12.6 mm —
it now faces west), the fuse wire corridor modeled at 23 mm instead of the
full 32.5 mm block height, the floor relay undersized (modeled 42 x 20
against the real 52 x 22 bracket + body/terminal volume), and three policy
holes (allowlisted pairs could hide true overlaps; wall margins unchecked —
the deck sat 1 mm from the wall; over-broad group matching). All fixed:
overlap is now never waivable, the allowlist is exact name pairs for
margin-waiver only, and wall margins are enforced. The result is **layout
v5 at 238 x 220 x 133, closing with zero violations and no margin under
2 mm**:

| Delta | Why |
| --- | --- |
| Body grows to 238 x 220 x **133** (+12 mm vs v1's 121) | Computed on verified datums: thermal ceiling 86.275 + 4 shelf + 28 Pi + 22 HAT + 3 margin = 143.275 required pan-servo drop bottom vs the v1-derived 131.6. Offset-shelf alternatives fail at box level (over-battery evicts the deck, the fuse block's only home; a south floor shelf hits the idler pods and arch). Phase 2 note: the stacked 28+22 band is conservative — the physical HAT sits ~17 mm above the Pi PCB, so BREP with the real HAT drawing may recover ~10 mm |
| Axles pull in to ±74 (148 mm wheelbase) | Keeps both 86 mm wheels ≥2 mm inside the shell length |
| MDDS10 rotated, terminals NORTH into a side corridor; explicit 10 mm thermal volume above the board | Physically consistent orientation; frees the front X-chain; thermal contract modeled, not assumed |
| Pi 5 shelf at Z 96 (the thermal ceiling) above the controller stack, ports east; full 96 x 74 x 22 AI-HAT reserve above; Pico on a NW shelf wing | The only stack order that honors both the airflow contract and the HAT reserve |
| Fuse block owns the deck's south half, wire service overhanging the deck edge; E-stop drops through the north half at (55, 52) — entirely above the deck, no aperture needed | The 92.5 mm block + 22 mm service and the 40 mm E-stop drop cannot share a deck column; at 133 mm height the E-stop body+terminals fit fully above the 102..106 deck plate (terminals bottom 110.1) |
| Rear connectors swap: EN2 charge inlet NORTH, mute SOUTH at its full 42 mm depth | Clears the E-stop drop (north roof) and the Pi port service (east) |
| Battery mid-rear; 28 mm lead corridor ends X=113; riser channel rises through a deck notch to the EN2 | The riser volume is now modeled, with the deck notched around it |
| Relay moves to the floor, front-left; both regulators hang under the deck's east end | Deck top belongs to the fuse block and E-stop; relay keeps its terminal service volume |
| Mic offsets south to (60, -25); vent slims to a south strip; E-stop panel off-center rear-right | 76 mm mic cradle + 66 mm E-stop panel cannot both sit centered on the rollover-limited roof flat |
| Speakers move to the FORWARD side walls (X -48..22, Z 115..145) | Rear side walls now carry the fuse wire service; 6 mm printed web above the wheel arches (round-2 minimum was 5-6) |

Critical margins reported by the screen: HAT-to-servo-drop 3.3; E-stop
terminals to deck 4.1; speaker-arch web 6; rear wheel to shell 2; lead
corridor to wall 2.8. Rough CG X≈7, between the ±74 axles.

**Round 4 (same day): green light.** Codex reproduced v5, verified the
corrected datums (thermal ceiling 86.275, pan-servo bottom 131.6, deck
102..106, derived height 133), confirmed the corridor/margin/policy
behavior and the relay fit, and approved starting Phase 2 while keeping
the D027 gate itself open. Four requirements carry into Phase 2 as
registered inventory obligations:

1. Register the Pico USB and SWD service corridors — done immediately at
   box level (v5.1): the former NW-wing placement put the USB corridor
   into the front bay, so the Pico moved to the floor NE quadrant with an
   east-facing USB corridor and top-access SWD volume.
2. Model the battery's real support padding and clamp geometry — the
   3 mm pad lift is now in the screen (pack top 79); the printed clamp
   bar joins the BREP model.
3. Represent the relay as separate 52 x 22 bracket, 26 x 22 body, and
   terminal-service volumes — done in v5.1; location unchanged.
4. Any height recovery from the real AI-HAT drawing is a BREP-discovered
   bonus, never an assumed reduction — 133 stands until the v2 model
   proves otherwise.

**This box screen is evidence of viability, not a gate pass.** The D027
packing gate stays open until the v2 BREP packing model — real curved shell
interior, mount/support solids, full harness routes, connector sweeps, and
CG from actual part masses — passes the inventory-driven production
validator (Phase 2). Fallback remains Option B (300 x 220 half-splits) if
BREP detailing breaks these margins.
