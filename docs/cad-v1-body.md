# CAD v1 Body Preview

This is the current build123d body translated from the supplied robot concept
art. It now includes a bearing-supported printable pan/tilt stack: underside
D85MG pan-servo plate, keyed fixed 6807 carrier, hollow rotating neck journal,
inner-ring retainer, flat cable corridor, D85MG/R-ML24 tilt drive, MF84ZZ
passive bearing, shoulder screw, and removable front and rear head panels. The
validator proves the complete moving printed head at
+/-20 degrees of tilt across a sampled +/-60-degree pan range.

The tilt-load-path pass replaces the yoke's unsupported full-width bore with
two serviceable interfaces. On the active side, a 28 x 3 mm three-screw printed
disk receives the Hitec R-ML24 horn at its 13 and 16 mm M2 stations. On the
passive side, a matching cartridge carries an MF84ZZ bearing around the 4 mm
shoulder of a McMaster 92981A143 screw fixed into a blind yoke insert. Six shell
bosses and all adapter, horn, bearing, and servo paths are validated; purchased
fit and repeated loaded motion remain physical gates.

The pan axis no longer asks the D85MG spline to support the head weight. A
Koyo/JTEKT 6807-2RS bearing sits in a keyed fixed carrier; the rotating neck has
a 34.8 mm inner-ring journal, 37.5 mm upper shoulder, and four-screw lower
retainer. The dedicated coupon tests three outer seats and three journals. A
conservative CAD estimate is about 0.598 kg-cm static tilt torque including a
25 g electronics allowance, versus the D85MG's published 0.9 kg-cm
peak-efficiency torque at 6 V. Measured dynamics and power behavior still rule.

The compact-head pass reduces the structural capsule from 82 x 146 x 80 mm to
72 D x 140 W x 72 H and lowers its center from Z=246 to Z=242, while retaining
the 120 x 56 mm removable faceplate and official camera geometry. The fixed
yoke and servo positions now derive from the shared head width. Two concealed
side roots fuse the projecting cream bezel to the shell; the 30 x 14 mm lower
camera-carrier notch clears both the ribbon and neck at downward pitch; and an
interior-only rear-cover relief follows the yoke envelope through a buffered
+/-21-degree sweep. All printed moving parts remain collision-free at the
validated +/-20-degree operating range across sampled pan poses.

The latest concept-fidelity pass replaces the formerly proud black panel with
an integrated projecting cream bezel and a thinner 3 mm faceplate recessed
3 mm behind it. The eye frames and eyebrows stay inside that bezel, while
9 x 14 mm vertical lime diffusers now match the reference proportions over
larger hidden LED-board pockets. The black faceplate itself carries one fused,
stepped annular camera bezel; this replaces four overlapping loose pieces and
removes the old printed glass/core disks from the optical path. The official
Camera Module 3 Wide is moved forward behind a validated 102-degree horizontal
FOV envelope. All eight face/rear panel screw paths remain validated.

The molded body now uses a 12 mm visible top-edge rollover instead of applying
the same small fillet to every edge. A paired 8.8 mm cavity fillet preserves the
nominal 3.2 mm roof skin, while the lower edge remains crisp for the tray and
concealed shell-seam plates. Three validator probes guard the roof thickness,
and the concept contract rejects an exterior rollover below 10 mm.

The 220 mm-bed configuration now has real joinery rather than clipped pieces:
four wall-backed shell plates, a two-piece tray with underside plate, four low
bumper plates, independently mounted fairing halves, and a stepped lid lap.
Those nine backing plates now add 18 concealed 4 mm pilots that bridge each
split line into matching half-round recesses. The pilots self-register the
shell, tray, and bumper before screw tightening without changing the exterior;
their 0.3 mm radial fit remains gated on the exact three-piece print coupon.

The side-fidelity pass replaces each long slab-like fairing with two shallow
wheel-arch caps joined by a narrow upper bridge. A large center relief exposes
the molded cream shell and side-ToF opening directly; the existing four high
fasteners still retain each one-piece side, while the printer-split halves mount
independently and no longer borrow the structural lower shell-seam screws. The
formerly proud 4 mm caps are now 2 mm skins seated flush at Y +/-110 in 2.2 mm
shell recesses. A 0.3 mm perimeter clearance, 0.2 mm nominal clamp gap, and
1 mm continuous shell backing keep the service seam printable without turning
the side into an open panel cutout. The exact corner, screw, pocket, and backing
geometry now ships as a two-piece calibration coupon.

The top-fidelity pass replaces the former floating 3 mm vent hood with a
recessed 80 x 62 x 1.6 mm dark grille that sits only 0.35 mm proud of the teal
lid. Nine 36 x 3 mm slots remain open through the grille, both lid halves, and
shell. Four M2.5 screws enter underside bosses at X=10/82 and Y=+/-27; two
fasteners land on each side of the stepped lid split, so the removable inlay
also provides a secondary top-side seam clamp. The microphone cradle now uses
a shared 40 x 80 mm rectangular roof pattern, and the cable strain plate shifts
to Y=-55 so all three service interfaces remain collision-free.

The packaging pass also adds a removable upper power/safety deck, a four-M3
rear service frame with three flush two-M2.5 cartridges,
speaker grilles, side airflow, official-pattern Camera Module
3 Wide carrier, and drawing-backed Pololu #4867 rear gearmotors on #1569 metal
brackets with #1997 aluminum hubs. The printed pods are removable guards rather
than primary motor retention, and the PETG wheel cores carry four real M3 hub
paths inside separately printable TPU tires.
The rear-right cartridge now carries a drawing-backed E-Switch PVB3F230SS311
maintained SPDT physical-mute control. Its exact 16.0 mm / 14.6 mm-flat opening,
18 mm bezel, red ring, 26 mm rear body, and terminal corridor clear the nearby
IDEC E-stop only in that right lane. The center cartridge now carries a
drawing-backed Switchcraft 35RASMT5CHNTRX four-conductor jack on an 18 x 18 mm
protected 3.3 V UART PCB and separate M2-retained L-carrier. Its shallow stack
stays in front of the E-stop and routes sideways. Rear-left now carries a
drawing-backed Switchcraft EN2P3M20 charge-only inlet with an EN2C3F20G2 cord
mate; two contacts are charger +/- and the third is protected
`CHARGER_PRESENT`, with no battery output exposed.
The two speaker plates now carry a documented stereo pair of Adafruit #3006
MAX98357A mono amplifiers. Their official 17.78 x 19.05 mm PCB outlines and
12.7 mm mounting patterns sit component-side-down on four 6 mm M2 standoffs;
signal/header paths face inward and speaker terminals face outward. Adafruit's
official STEP predates the current pre-soldered terminal block, so the modeled
screwdriver and wire corridors remain conservative physical-test gates.
The mobility pass now makes the concept's front wheels functional as removable
non-driven idlers: each pod locates two 608-class bearings around a retained
8 mm metal shaft, uses two flush screw-on bearing-retainer rings, and all four
mobility pods clamp to deliberate tray pads. Each 64.5 mm shaft now has a
drawing-backed Rotor Clip DSH-8 groove at its inboard end, followed by a DIN
471 ring, steel washer, paired bearings and metal spacer tubes; a Pololu #2693
8 mm hub provides two-set-screw outboard retention and six M3 wheel-core paths.
The safety MCU is now a
drawing-backed non-wireless Raspberry Pi Pico 2 on four 6 mm M2 standoffs, with
its official 48.26 x 17.78 mm hole pattern, front-facing micro-USB notch/cable
path, and rear SWD service corridor on a serviceable shelf above the controller, freeing
the front-right volume without sacrificing its independent wiring path.
The motor controller beneath it is now a drawing-backed Cytron MDDS10 rather
than a generic box: its official board and four-hole pattern sit on 6 mm M3
standoffs, the lower plate floats 5 mm above the tray to clear the concealed
carry-handle doubler, the six high-current terminals face robot-front, and a
10 mm cooling keepout remains below the Pico shelf.
The latest stance refinement lowers every 43 mm-radius wheel center to Z=66,
partly nests each tire 4 mm into the body envelope, and derives the review floor
from the resulting Z=23 tire tangent. The bumper now starts at Z=29 for 6 mm of
static ground clearance; two concealed inboard bridges keep its four wheel-cut
segments one printable carrier below the tray. Its 302 x 222 mm inner cavity
now clears the rigid 300 x 220 mm shell by 1 mm per side and the tray by 5 mm,
eliminating the former impossible solid overlap while retaining the same outer
silhouette. The 42 mm-high motor and idler
pod shells remain seated at Z=53 while their hardware centers follow the lower
axle. Matching shell, fairing, and bumper arches plus explicit tray/pod/wheel
collision checks keep that more concept-like stance functional. The side ToF
windows moved to X=-20, with bosses at X=-40, so they sit in the actual gap
between the lowered front and rear wheel wells.
Each TPU tire now adds 24 offset transverse grooves, 5.5 mm wide and 2 mm deep,
across its central 20 mm tread band. The untouched 2 mm sidewalls preserve the
recessed teal ring seat and support-free sidewall-down print orientation, while
the half-step angular offset leaves the exact tire tangent out of a groove.
The safety-bumper interface now has a real fixed-versus-moving contract. Six
22 x 40 x 4 mm PETG plates seat beneath the tray and fasten independently into
12 blind inboard inserts. Six drawing-backed Omron D2HW-C202MR sealed SPST-NC
pin-plunger switches rise through tray pockets, while the black TPU carrier
receives local radial reliefs instead of being clamped by the plate screws.
The validator proves a 0.4 mm no-preload rest gap, worst-case electrical
actuation after 2 mm of local compression, and paired rigid-stop contact at
2.4 mm without reaching the switch's total-travel position. Purchased switches
and the selected TPU still require force, rebound, strain-relief, broken-wire,
six-zone electrical, and fail-stopped motor tests.
The expression pass separates the two front ToF modules into central black-bar
apertures and gives all four lime status/eye diffusers drawing-backed carriers
for Adafruit 5975 NeoPixel JST breakouts plus unobstructed light paths. Each
12.192 x 11.43 x 5.93 mm board uses two M2 holes and 3 mm-OD spacers, while the
rotated eye boards send their two plug paths vertically clear of the fixed yoke.
The fascia and front sensor pods now have explicit
screw interfaces, while both side ToF pods use shell bosses behind real openings
through the shell and fairings. Audio supports, the battery cradle, and the
controller/safety stack are likewise anchored to shell or tray interfaces
instead of floating at their fit coordinates.
The tray now also has a concealed two-hand carry system: two recessed 25 mm
webbing loops clamp to metal plates that bridge both printer-split halves. It
does not alter the concept silhouette and remains gated on a physical loaded
lift test.
The rear E-stop is now drawing-backed to an IDEC XW1E-BV402M-R. Its 40 mm red
operator clamps only a removable 4 mm keyed top panel, avoiding the former
over-thick printed stack. A 40 mm service passage continues through the lid,
shell, raised backing collar, and power-deck notch; four cardinal M3 screws tie
the backing to blind panel inserts. The purchased nut remains primary switch
retention, and a durable 60 mm yellow legend surrounds the operator. Release
still requires delivered-part inspection, terminal and wire-bend checks,
push/twist loading, both direct-opening NC channels, and independent motor cut.
The power deck now lifts with its wiring: two removable under-deck U rails use
four paired reusable-strap stations each, with signal/audio/sensors on the left
and fused switched power/motors on the right. Conservative bundle envelopes
clear the battery, mobility pods, deck standoffs, and future AI-HAT volume.
The deck now also carries exact Pololu D24V90F5 and D36V50F6 mounting patterns,
seven metal-standoff paths, and terminal/wire corridors. An Albright SW60
normally-open contactor fits on a separate custom metal carrier with four open
deck paths; the printed deck is not its primary structural or cable-torque
interface. The battery cradle targets one Bioenno BLF-1203AB prototype candidate
rotated flat to 110 x 75 x 27 mm. The 117 x 92 mm cradle adds two 20 mm straps,
four support pads, positive side/end locators, standoff scallops, and a rear
lead corridor. Delivered geometry, product-safety evidence, <=5.6 A sustained
pack current, runtime, BMS/regen/thermal behavior, and loaded retention remain
open release gates. A full drawing-backed fit attempt also ruled
out the Littelfuse 880024 four-way MINI fuse block: its housing, terminal, and
cover service volumes collide with the E-stop/rear-service/audio stack. The
replacement is a custom 40 x 21 mm four-branch PCB with four Littelfuse
01550900M OMNI-BLOK Nano2 holders and a Molex 43045-1000/43025-1000 latched
ten-circuit harness. Eight stacked M2 metal standoffs retain the board beneath
a separate 44 x 24 mm printed touch cover; the CAD also protects fuse-puller,
connector, first-bend, and strain-strap access. The board stays capped at 6 A
total / 5 A any branch pending reviewed copper, measured fuse selection, and
fault/thermal tests. The calibration suite includes an exact one-piece PETG
board/holder/fuse/header gauge so the deck, eight M2 standoffs, header opening,
and production cover can be trial-assembled before ordering the PCB; the gauge
is mechanical only.
See [CAD Component Coverage](cad-component-coverage.md) for the honest line
between modeled references and hardware decisions that remain open.

It remains a visual and fit-check baseline, not a release-ready final print.
The selected drivetrain, battery candidate, rear charge pair, and safety
switches still need purchased-part and loaded/electrical tests; the custom
distribution board still needs PCB/crimp/fuse/fault/thermal release. The selected NeoPixel boards still require a
one-board delivered-part, cable-bend, brightness, diffusion, and reflection test.

![Assembled Codex robot body](images/codex_robot_body_v1_assembled.png)

![Inset cream head bezel and recessed faceplate](images/codex_robot_body_v1_head_detail.png)

![Retained active and passive head-tilt mechanism](images/codex_robot_body_v1_head_mechanism.png)

![Exploded Codex robot body](images/codex_robot_body_v1_exploded.png)

![Top lid, recessed vent inlay, E-stop, and neck detail](images/codex_robot_body_v1_top_detail.png)

![TPU tread, recessed hub inserts, wheel arches, and bumper clearance](images/codex_robot_body_v1_wheel_detail.png)

![Exploded Pololu rear drivetrain and printed wheel stack](images/codex_robot_body_v1_drivetrain.png)

![Electronics fit volumes](images/codex_robot_body_v1_electronics_fit.png)

![Drawing-backed Raspberry Pi Pico 2 safety shelf](images/codex_robot_body_v1_safety_mcu.png)

![Drawing-backed Cytron MDDS10 controller stack](images/codex_robot_body_v1_motor_controller.png)

![Dual MAX98357A speaker-plate interfaces](images/codex_robot_body_v1_audio_interface.png)

![Drawing-backed Adafruit 5975 expression modules](images/codex_robot_body_v1_led_interface.png)

![Upper power deck with exact regulator and cutoff service envelopes](images/codex_robot_body_v1_power_deck.png)

![Modular maximum-envelope battery cradle and controller clearance](images/codex_robot_body_v1_battery_interface.png)

![Split-tray carry interface](images/codex_robot_body_v1_carry_interface.png)

![Under-deck harness routing](images/codex_robot_body_v1_harness_routing.png)

![Modular rear service frame and cartridges](images/codex_robot_body_v1_rear_service.png)

![Tray-fixed bumper switch plates and TPU interface](images/codex_robot_body_v1_bumper_interface.png)

![Printer-split joinery](images/codex_robot_body_v1_split_joinery.png)

![Representative print-ready orientations](images/codex_robot_body_v1_print_ready.png)

![Calibration coupon plate](images/codex_robot_body_v1_coupons.png)

![Split-pilot coupon detail](images/codex_robot_body_v1_alignment_pilot.png)

The editable source is [`cad/python/robot_body.py`](../cad/python/robot_body.py).
Generated STL and STEP files are placed in the ignored `cad/exports/` directory.
The generated main, split, and canonical print manifests list current part
spans, assembly groups, slicer orientations, material profiles, support notes,
and hardware release gates; export commands remove obsolete generated STL names
before rebuilding.

The tracked [P1S Bambu Studio project](../cad/bambu/codex_robot_body_v1_p1s.3mf)
targets the standard 0.4 mm nozzle and Textured PEI Plate. It contains all 103
canonical parts exactly once on 26 named, brim-aware plates grouped by material
profile and color. The adjacent JSON plate manifest records every placement,
filament color, recommended process, and part release status. It is an editable
layout project rather than pre-sliced G-code; coupons and hardware release gates
still apply before full-body printing.

![P1S material and color plate layout](images/codex_robot_body_v1_p1s_plates.png)

The generated [illustrated assembly guide](../output/pdf/codex_robot_body_v1_assembly_guide.pdf)
turns these review renders and the current hardware manifest into a 20-page
stage-by-stage build sequence. Regenerate it with
[`docs/generate_assembly_guide.py`](generate_assembly_guide.py) after changing
geometry, hardware, assembly order, plate grouping, or release gates.
