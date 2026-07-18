# CAD Component Coverage

This is the BOM-to-CAD packaging audit for the current build123d body. A green
row means the model has both a fit envelope and a printable support or service
interface. It does **not** mean an unpurchased placeholder is release-ready.

| BOM area | Current CAD coverage | Status |
| --- | --- | --- |
| Raspberry Pi 5 + active cooler | Published board pattern, conservative cooler/connector envelope, tray standoffs, side airflow path | Modeled reference |
| Camera Module 3 Wide | Board/lens envelope, optical aperture, ribbon exit, removable carrier, official four-hole pattern, forward lens placement, faceplate-integrated annular bezel, and validated 102-degree horizontal-FOV cone | Modeled reference; physical corner illumination, focus, and reflection test required |
| Microphone array | 70 mm envelope, retaining ring, four shared roof-boss screw paths on a 40 x 80 pattern, and nine open paths through the shell, split lid, and recessed four-screw vent inlay | Modeled reference with service fasteners |
| Speakers | Two 70 x 30 x 17 envelopes, speaker screw plates, two independent roof-boss fasteners per plate, ten through-shell/lid grille slots | Modeled reference with service fasteners |
| I2S amplifier pair | Two Adafruit #3006 MAX98357A boards mounted component-side-down beneath the speaker plates; exact 17.78 x 19.05 x 1.57 mm PCB datum, two 2.5 mm holes on 12.7 mm spacing, four 6 mm M2 standoffs, inward 1x7 header/direct-wire paths, outward speaker-wire bends, and downward terminal screwdriver corridors | Drawing-backed PCB/mount baseline; official 2022 STEP omits the terminal block added to current production, so buy one and measure terminal height, screwdriver travel, wire entry, header/direct-wire stack, channel-select resistors, current, heat, and audio before releasing both plates |
| Optional I2C mux | No dedicated board frozen; ToF XSHUT/address assignment is the first baseline, with strap-serviced signal-harness space retained if a mux proves necessary | Deferred unless bench wiring proves it is needed |
| Raspberry Pi Pico 2 safety MCU | Official 51 x 21 x 1 mm board and 52.3 x 21 x 3.8 mm STEP envelope, 48.26 x 17.78 mm four-hole pattern, four 6 mm M2 standoffs, front micro-USB notch/cable corridor, rear SWD corridor, optional-header keepouts, and removable upper shelf above the controller | Drawing-backed mechanical baseline; physical connector, watchdog, NC-input, and motor-cut tests required |
| E-stop | IDEC XW1E-BV402M-R 40 mm/2NC reference; removable 4 mm keyed clamp panel; 37 x 37 x 48.7 mm body and 20 mm terminal-service envelopes; 40 mm lid/shell/backing/deck passage; 66 mm raised-collar backing; four cardinal M3 paths; purchased-nut retention; 60 mm yellow legend | Drawing-backed mechanical baseline; purchased-part, terminal, push/twist, dual-NC, and independent cutoff tests required |
| Motor cutoff, Pi regulator, servo regulator, distribution | Drawing-backed Pololu D24V90F5 and D36V50F6 boards on seven metal M2 standoffs; Panasonic CB1A-R-M-12V sealed SPST-NO relay with 26 x 22 x 25 mm body, integral 52 x 22 x 0.8 mm bracket, one 5.4 mm mount, 6.3 mm terminals, 40 A at 14 V contacts, 12 V/134 mA coil, and built-in resistor; Blue Sea Systems 5045 complete covered four-circuit ATO/ATC block at 92.5 x 43.8 x 32.5 mm with two 4.5 mm paths on 65.1 mm centers, terminal/wire/fuse service, and strain slots | Retail-only mechanical baselines. Require purchased identity/fit, relay terminal and conductor sizing, driver/suppression/dropout/fault/thermal tests, battery-near feeder fuse, measured-load branch fuses, covered terminals, strain relief, labels, selective clearing, all-branch thermal soak, no-backfeed, and independent cutoff tests. Keep 6 A total / 5 A any-branch prototype ceilings |
| Internal wiring harness | Two removable 108 x 14 mm under-deck U rails, separate signal and switched-power bundle envelopes, 7.6 x 5 mm channels, four paired reusable-strap stations per rail, shared deck openings, and validated clearance from battery, mobility, standoffs, and future AI-HAT volume | Modeled routing baseline; measure real bundles and connectors |
| Main power, charging, mute, rear cartridges | 100 x 34 x 23 internal bay with six local insert-boss notches; screw-on 126 x 58 rear frame; three flush 30 x 30 cartridges with two M2.5 screws each; rear-left Switchcraft EN2P3M20 charge-only inlet, blank center cartridge, and rear-right E-Switch PVB3F230SS311 physical mute | Require purchased EN2/mute fit, charge polarity and charger-present motion inhibit, privacy behavior, strain relief, and external removability tests. The blank center has no jack, PCB, wiring, power, or service-detect path |
| Battery | Bioenno BLF-1203AB modeled flat at 110 x 75 x 27 mm; 117 x 92 mm removable cradle with four support pads, two 20 mm strap channels, positive side/end locators, four screw tabs, standoff scallops, and a rear lead corridor | Prototype candidate only; require delivered pack/lead fit, product-safety evidence beyond UN38.3, <=5.6 A sustained current, BMS/regen/thermal behavior, retention, and 45-minute runtime with 20% reserve |
| Rear drive motors | Two Pololu #4867 99:1 25D MP 12 V encoder motors, #1569 metal brackets on three tray-backed M3 spacer paths per side, #1997 4 mm aluminum hubs, four-screw PETG wheel cores, annular TPU tires, removable protective pods/covers, and routed encoder-lead corridors | Drawing-backed mechanical and electrical prototype baseline; purchased-revision, <=0.45 A-per-motor target-surface current, thermal, retention, cutoff, and floor tests required |
| Cytron MDDS10 motor controller | Official 101.092 x 66.802 mm STEP footprint, 1.57 mm PCB, 1.93 mm underside protrusion, 12.275 mm component height, 95.25 x 60.96 mm four-hole pattern, four 6 mm M3 board standoffs, locally notched plate on four 5 mm metal spacers, front terminal fan-out, 10 mm cooling keepout, and four-standoff safety shelf | Drawing-backed mechanical baseline; purchased-board revision, polarity, terminal bend, cooling, and loaded-motor tests required |
| ToF + bumper switches | Keyed front fascia and four ToF pods; six Omron D2HW-C202MR sealed SPST-NC switches on tray-fixed PETG plates; 13 mm M3 switch patterns; 12 blind tray inserts; side-lead corridors; independent TPU reliefs; validated 0.4 mm rest gap, 2 mm worst-case actuation, and paired 2.4 mm stops below total travel | Drawing-backed mechanical baseline; purchased-switch/TPU coupon, strain, rebound, broken-wire, and six-direction motor-cut tests required |
| Pan/tilt | V2: two drawing-backed Hitec D85MG servos and R-ML24 horns; three-lug lid bayonet; 39.6/40.3 mm greased printed journal; flat thrust shoulder; integrated servo cradle + two-M3 plate; 20 mm ribbon corridor; four-M3 yoke; active shell horn boss; one-M3 3.2 mm passive shoulder bushing; printed hard stops; and actual-solid sweeps through +/-20 degrees tilt and +/-60 degrees pan | CAD-complete D035 baseline; exact-part/component-hardware fit, bayonet/journal/bushing coupons, PETG-safe grease, measured mass/current, cable drag, axial play, backlash, heat, and loaded wear cycling required |
| LED eyes/status | Four Adafruit 5975 NeoPixel JST breakout STEP envelopes; 12.192 x 11.43 mm PCB, 5.93 mm overall component depth, two 2.0 mm holes on 8.636 mm spacing, two 3-pin JST-SH ports, eight 3 mm-OD M2 spacers, open plug/latch corridors, removable M2.5 carrier frames, stepped pockets, separate diffusers, 9 x 14 mm vertical head eyes, and horizontal body indicators | Drawing-backed mechanical baseline; buy one first and verify delivered dimensions, cable bends, brightness/current cap, diffuser hotspotting/color, camera reflections, and software-off behavior |
| Front support/idlers | Two removable pods; two 608 seats and flush screw-on outer-race retainers per side; WDS 615-M6-8-65 shoulder bolt; M6 washer; prevailing-torque locknut; stock goBILDA spacers/shim; four-point tray pads | Retail-only metal retention baseline; purchased-hardware fit, shoulder/thread engagement, spacer squareness, axial play without bearing preload, locknut retention, wheel alignment, and loaded cornering tests required |
| Lifting | No integrated carry interface or custom load-bearing metal | Power down and lift with two hands under the tray; never lift by shell, lid, head, bumper, fairings, wiring, or cartridges |
| Optional LiDAR | Space not yet proven by a keepout | Deferred |

## Camera reference

The Camera Module 3 Wide carrier follows Raspberry Pi drawing
[RP-008155-DS-1](https://pip-assets.raspberrypi.com/categories/1207-design-files/documents/RP-008155-DS-1-camera-module-3-wide-mechanical-drawing.pdf):
25 x 23.862 mm PCB, four 2.2 mm holes, 21 mm horizontal spacing, and 12.5 mm
vertical row spacing. The fit model separates the PCB slab from the lens
housing so the lens can occupy the optical opening without falsely colliding
the PCB corners with the head wall.

The lens face now sits 1 mm behind the faceplate front. A single stepped
annulus is fused to that removable black panel, leaving a 13 mm clear radius at
its front and an 11.5 mm radius through the faceplate and shell. A conservative
circular cone uses the module's 102-degree horizontal field of view, so the CAD
also protects the narrower vertical view. This proves geometric clearance, not
image quality: print texture, reflections, focus, corner shading, and pan/tilt
cable behavior still require a full-resolution physical camera test.

## Pan and tilt reference

Both axes use the [Hitec D85MG](https://www.hiteccs.com/actuators/product-details/D85MG),
a 29 x 13 x 30 mm 24T digital metal-gear servo. The CAD follows Hitec's
published STEP model for the 7.8723 mm output offset, 39.8 mm flange, 30.8 mm
mount spacing, and 4.5 mm flange holes. Each axis uses an R-ML24 aluminum horn
with M2 x 0.4 threaded stations at 13 and 16 mm. At 6 V Hitec publishes 0.9
kg-cm peak-efficiency torque, 4.3 kg-cm stall torque, and 1.4 A stall current;
stall is a fault boundary, not an operating target.

For v2, the servo splines transmit torque while printed PETG interfaces carry
the head. The fixed collar's 40.3 mm bore supports a 39.6 mm rotating journal
and flat thrust shoulder; three lugs bayonet into the structural lid. A
two-screw plate captures the pan servo, and the horn drives the neck beside the
20 mm camera-ribbon corridor. The yoke uses four M3 neck joints, a drawing-backed
tilt-servo frame, and printed hard stops. The active horn screws to the shell
drive boss at the 13/16 mm stations; the passive side rotates around a 3.2 mm
printed shoulder bushing clamped by one M3 x 8 into the yoke.

The validator samples the actual printed solids through commanded +/-60 pan
and +/-20 tilt, checks both D85MG case clearances and the cable corridor, and
requires contact beyond each range. This is a sanity check only: weigh the
assembled head and verify exact hardware, grease compatibility, acceleration,
cable drag, regulated current, temperature, axial play, backlash, holding
behavior, and repeated loaded motion.

## Safety MCU reference

The deterministic safety controller now targets the non-wireless Raspberry Pi
Pico 2 without headers. The independent stop/watchdog path uses wired links;
Wi-Fi or Bluetooth is unnecessary for its safety role. Raspberry Pi's
[Pico 2 datasheet](https://datasheets.raspberrypi.com/pico/pico-2-datasheet.pdf)
defines a 51 x 21 x 1 mm board, four 2.1 mm mounting holes, and 48.26 x 17.78 mm
hole spacing. The official STEP model RP-009061-CA-2 expands the complete bare
board/USB envelope to 52.3 x 21 x 3.8 mm.

The board sits on four 6 mm M2 metal or rated-nylon standoffs above the removable
safety shelf. Its micro-USB connector faces robot-front into a U-notch and open
cable corridor; the three-pad SWD edge faces inward/rear into a separate service
corridor. Two optional header keepouts preserve a locking wired harness without
assuming loose Dupont leads. The validator checks the official dimensions and
hole pattern, all four screw paths and standoff endpoints, the USB notch, both
service corridors, body containment, and collision clearance.

## Expression LED reference

All four expression apertures target the
[Adafruit 5975 NeoPixel breakout](https://www.adafruit.com/product/5975). Adafruit
publishes two M2 mounting holes, keyed 3-pin JST-SH input and output, 3.3 V or
5 V operation, and an official
[STEP model](https://github.com/adafruit/Adafruit_CAD_Parts/tree/main/5975%20NeoPixel%20Breakout).
The imported STEP resolves a 12.192 x 11.43 mm PCB, 1.57 mm substrate, 5.93 mm
overall LED-to-connector depth, and 8.636 mm hole spacing. The CAD preserves
the complete component envelope rather than flattening the connectors into the
PCB slab.

Each board bolts to its removable carrier through two 3 mm-OD M2 spacers. The
head boards rotate 90 degrees so their JST-SH plug and first-bend corridors run
vertically between the carrier attachment screws; that orientation remains
collision-free throughout the validated head motion. The front boards retain
the default orientation and route both plugs horizontally inside the fascia
carrier openings. Use a fused 5 V branch, common ground, suitable 3.3-to-5 V
data translation, and a software brightness cap. These lights communicate
state only; they are not safety interlocks.

Mechanical fit does not prove safety behavior. The purchased board must still
pass USB programming and SWD recovery, connector-retention, watchdog timeout,
normally-closed bumper input, broken-wire fault, heartbeat-loss, and independent
motor-power cutoff tests before powered driving.

## Motor controller reference

The motor controller baseline now targets the Cytron SmartDriveDuo-10 MDDS10.
Cytron's [official product page and CAD resource](https://th.cytron.io/p-10amp-7v-35v-smartdrive-dc-motor-driver-2-channels)
specify the 66.8 x 101.09 mm board and provide the STEP model used here. The
STEP resolves the exact 101.092 x 66.802 mm footprint, 95.25 x 60.96 mm four-hole
pattern, 1.93 mm underside pin projection, and 12.275 mm maximum height above
the PCB datum.

The long axis runs along robot X with the six high-current terminals facing
robot-front. Four 6 mm M3 standoffs leave more than 4 mm beneath the pins. The
printed plate sits on four additional 5 mm metal spacers, while a 10 mm cooling
keepout remains below the Pico shelf. The validator checks the official dimensions, all twelve standoff
endpoints, terminal corridor, cooling volume, and full
interior collision audit. Cytron warns that the board has no reverse-polarity
protection; keyed power connectors, fuse/cutoff behavior, terminal strain
relief, temperature under real motor load, and the purchased board revision
still require bench verification.

## Rear charge-only reference

The rear-left cartridge targets the
[Switchcraft EN2P3M20](https://www.switchcraft.com/en2-panel-connector-3-position-20-male-pins-20-contact-size/en2p3m20/)
panel connector and
[EN2C3F20G2](https://www.switchcraft.com/en2-cord-connector-3-position-20-female-sockets-20-contact-size-0-140-0-180-3-6-4-6mm-grommet-ribbed-coupling-ring/en2c3f20g2/)
cord mate. The CAD pins the 10.92 mm panel opening, 15.75 mm bezel, 14.94 mm
rear body, 20.07 mm total panel-side depth, 13.5 mm cord body, protected
terminal volume, and cartridge ligaments. Two contacts carry isolated charger
positive and negative; the third is a protected `CHARGER_PRESENT` input.

This is a charge-only interface for the Bioenno BPC-1502DC 14.6 V/2 A charger,
not a battery outlet or main-power disconnect. The cord side is female so an
energized adapter does not expose pins. Switchcraft specifies that EN2 is not
for current interruption: remove charger AC before mating or unmating. Insertion
must request a deterministic motor inhibit, de-energize the Panasonic relay/motor
enable, and require explicit reset after removal. Purchased-part fit, pinout,
polarity, insulation, strain relief, charge current, BMS interaction, insertion
shorts, and no-automatic-restart behavior remain physical release gates.

## Rear drivetrain reference

The rear drivetrain now targets the [Pololu #4867 99:1 25D MP 12 V encoder
gearmotor](https://www.pololu.com/product/4867), the matching [#1569 metal
bracket](https://www.pololu.com/file/download/1569-bracket-dimensions.pdf?file_id=0J725),
and the [#1997 4 mm-shaft M3 aluminum hub](https://www.pololu.com/product/1997).
The motor fit follows Pololu's 25D drawing and STEP geometry: 68.45 mm from
gearbox face to encoder rear, 25 mm gearbox diameter, 4 x 12.5 mm D shaft,
7 x 2.5 mm boss, and two M3 face holes on 17 mm spacing. The bracket clamps to
three blind tray inserts through equal-height 3 mm metal spacers; it, not the
printed pod, carries motor reaction. Four M3 screws couple each 19 mm aluminum
hub to a removable PETG wheel core inside the annular TPU tire.

The selected 98.78:1 motor is listed at 79 rpm and 0.10 A no-load at 12 V,
with 1.8 A / 11 kg-cm extrapolated stall. With the modeled 86 mm wheel, that is
approximately 0.356 m/s no-load, closely matching the 0.35 m/s MVP speed cap.
Stall operation can damage the motor and gearbox. Release therefore remains
blocked on purchased-part inspection, D-shaft/set-screw engagement, screw-length
confirmation, encoder function, wheel retention, <=0.45 A steady per motor on
target surfaces, measured temperature, independent motor cutoff, obstruction
tests, and skid-turn testing on carpet, rugs, and hard floors.

## Front idler reference

The non-driven front wheel pods preserve the four-wheel concept silhouette
without adding two more motors. Each side reserves two 608-class bearings using
the [SKF 608 reference dimensions](https://www.skf.com/sg/products/rolling-bearings/ball-bearings/deep-groove-ball-bearings/productid-608-2Z%2FC3LHT23):
8 mm bore, 22 mm outside diameter, and 7 mm width. A WDS 615-M6-8-65 shoulder
bolt runs its 65 mm-long, 8 mm shoulder through both bearings. An M6 washer,
prevailing-torque locknut, and stock goBILDA spacers/shim establish the axial
stack and positive metal retention. The printed pod locates the bearings
and transmits their reaction into the four-point tray interface; the
bearings, shoulder bolt, washer, locknut, stock spacers/shim, and positive metal retention
must prevent plastic threads or friction fits from becoming the axle-retention
system. Four flush printed rings and eight M2.5 screws retain the bearing outer
races for service.

This is deliberately a removable baseline, not a declaration that four-wheel
scrub steering will behave well on every household floor. Loaded turning tests
on the intended carpet, rugs, and hard flooring decide whether these pods stay
or are replaced by omni, caster, or ball-transfer modules using the same tray
interface.

All four nominal 86 mm tires now share a Z=23 tangent plane, with centers at
Z=66 and inner faces 4 mm inside the body envelope. The pod shells remain
seated at Z=53 independently of axle height. The validator requires the bumper
to retain 6 mm of ground clearance and checks each wheel against the tray,
matching pod, shell, fairing, and bumper. These are geometry contracts only;
real tire compression, wheel runout, floor transitions, and loaded deflection
still require physical testing.

## Bumper switch reference

The black bumper is the moving/compliant TPU reference. The six switch plates
are rigid PETG chassis references seated against the tray underside; two M3
screws per plate enter blind inboard tray inserts, so no switch-plate screw
clamps the TPU. Each Omron D2HW-C202MR mounts through its drawing-backed 13 mm
M3 pattern and rises through its own tray pocket with a straight molded-lead
corridor. Paired PETG stops flank the plunger so impact load does not bottom the
switch or pull its wire seal.
The carrier's 302 x 222 mm inner cavity also keeps 1 mm nominal radial clearance
from the cream shell and 5 mm from the tray. Hidden low bridges connect the
wheel-cut segments beneath the rigid chassis; neither bridge nor visible rail
may occupy shell or tray volume.

The validator proves the plates and switch bodies do not collide with the tray,
bumper, wheels, or mobility pods; all 12 tray and 12 switch screw paths remain
open; no TPU patch touches a plunger at the 0.4 mm rest gap; 2 mm inward travel
crosses the worst-case operating plane; and paired stops engage near 2.4 mm
without reaching the 5.1 mm total-travel plane. This is not proof of force,
rebound, TPU fatigue, wire-seal strain, contact welding, or stopping performance.
Print the exact PETG/tray/TPU coupon with a purchased switch, then prove every
zone opens the safety loop and cuts motor power before driving.

## E-stop mount

The selected IDEC XW1E-BV402M-R clamps only through a removable 4 mm top panel
with its keyed 22.5 mm opening. The panel's 66 mm lower flange seats in the teal
lid; a 60 mm durable yellow legend surrounds the red 40 mm operator. A matching
raised-collar backing ring joins the panel through four cardinal M3 paths on a
28 mm radius. Larger 40 mm openings through the lid, shell, backing, and power
deck keep those printed layers outside the manufacturer's clamp stack and leave
the 37 mm body plus covered terminals removable from below.

The purchased nut remains primary switch retention; printed plastic spreads
load and supports the panel. The validator proves keyed-opening clearance,
panel thickness, body/barrel/service passages, power-module clearance, and all
four backing paths. Physical release still requires delivered-part inspection,
nut engagement, anti-rotation, terminal insulation, wire bend, push/twist load,
both direct-opening NC channels, and independent motor-power cutoff.

## Physical mute reference

The rear-right cartridge targets the maintained, red-ring
[E-Switch PVB3F230SS311](https://www.e-switch.com/wp-content/uploads/2024/01/PVB3.pdf).
The drawing-backed model uses its 16.0 mm cutout with 14.6 mm anti-rotation
flats, 18 mm bezel, 11.2 mm flat actuator, 12.8 mm LED ring, 26 mm rear body,
1-7 mm panel range, and SPDT On-On function. Moving the switch out of the center
bay clears the concept-positioned IDEC E-stop body by at least 8.2 mm and its
modeled terminal-service corridor by at least 5.5 mm.

The intended privacy circuit routes fused microphone 5 V to the switch common.
The listen throw feeds the USB microphone's VBUS; the mute throw feeds the red
ring through a calculated series resistor and a protected 3.3 V-compatible
state input. The manufacturer lists the base red LED at 1.8 V / 20 mA; resistor
power, LED polarity, input conditioning, harness strain relief, and connector
serviceability remain electrical checks. Physical release requires proving
that mute removes microphone capture locally, remains visibly indicated with
software stopped, cannot back-power the microphone over USB data, and restores
capture only after an intentional maintained-switch change.

## Blank center rear cartridge

The center cartridge is a plain 30 x 30 mm removable cap with the shared
26 x 18 mm tongue and two M2.5 frame screws. It has no connector, PCB, carrier,
wiring, power output, or service-detect function. Internal diagnostics require
shutdown or physical motor-branch isolation, and closure never authorizes an
automatic restart. D024 supersedes the D021 UART design while preserving it in
the decision log as rejected history.

## Upper service deck

The 145 x 116 mm deck sits above the removable battery on four metal M3
standoffs. It carries or reserves independent volumes for:

- Pi 5 V regulator: Pololu D24V90F5, 40.6 x 20.3 x 7.6 mm, four M2 stations on 35.56 x 15.24 mm spacing, two wire/terminal corridors.
- Servo regulator: Pololu D36V50F6, 25.4 x 25.4 x 9.5 mm overall envelope, triangular three-M2 pattern, one wire corridor.
- Motor cutoff: Panasonic CB1A-R-M-12V, 26 x 22 x 25 mm body, integral 52 x 22 x 0.8 mm bracket, one 5.4 mm mounting hole, 6.3 mm terminals, and terminal-service envelope.
- Accessory distribution: complete Blue Sea Systems 5045 covered four-circuit ATO/ATC block, 92.5 x 43.8 x 32.5 mm, two mounting holes on 65.1 mm centers, and modeled cover/fuse/terminal/wire service plus deck strain slots.

The two MAX98357A boards mount below their matching speaker plates rather
than consuming deck area. The regulators, relay, and fuse block are mechanical
selections, not electrical release approval. The distribution system's
provisional ceiling is 6 A total and 5 A on any branch. Exact ATO/ATC fuse
values must follow measured startup, steady, transient, fault, conductor,
and time-current data; a battery-near feeder fuse remains mandatory because the
four branch fuses cannot protect the cable upstream of the block. Use correctly
crimped terminals, fused conductors, terminal protection, and strain relief;
the printed deck is an organizer, not a safety device or relay-bracket substitute.

Two removable rails run beneath the deck outside the battery envelope. The
left rail is reserved for signal, audio, and sensor wiring; the right rail is
reserved for fused switched power and motor wiring. Each rail and the deck
share four pairs of rounded slots, allowing reusable straps to retain the rail
and bundle as one serviceable deck assembly. This is routing separation, not
electrical insulation: conductor sizing, fusing, shielding, connector locks,
bend radii, and abrasion protection still come from the selected hardware.

### Accessory distribution reference

The Blue Sea Systems 5045 is a complete quantity-one retail four-circuit
ATO/ATC fuse block with insulating cover and labels. The model uses its
92.5 x 43.8 x 32.5 mm assembly envelope, two mounting holes on 65.1 mm centers,
fuse-service height, terminal side, single-side wire exit, and deck strain slots.

Release requires a battery-near feeder fuse, power-off-only fuse changes,
measured-load fuse selection, conductor and terminal sizing, inspected crimps
and pull tests, covered live parts, durable source/branch labels, selective
far-end short tests, all-branch thermal soak, vibration/tug tests, and proof
that the block cannot feed the motor controller around the separate source
fuse, Panasonic relay, E-stop chain, or charger-present inhibit. The legacy
D023 gauge and cover qualify none of this hardware.

## Lifting

The normal assembled silhouette and tray are handle-free. There are no webbing
slots, carry doubler, custom clamp plates, or M4 carry paths. Power down and lift
with two hands under the tray. Do not lift by the shell, lid, head, bumper,
fairings, wiring, or rear cartridges. Any future integrated handle requires a
new retail-only load-path decision and physical qualification.

## Gates before release printing

1. Purchase the selected Pololu motors, brackets, and hubs; inspect the delivered revisions, print one rear core/pod interface, and bench-test encoder direction, D-shaft/set-screw engagement, wheel retention, current, temperature, and independent cutoff before powered floor tests.
2. Purchase and measure the 608 bearings, WDS 615-M6-8-65 shoulder bolts, M6
   washers, prevailing-torque locknuts, and stock goBILDA spacers/shims; then load-test the removable idler pods and
   verify acceptable skid steering on the target floors. Swap the pods if scrub
   torque or carpet snagging is excessive.
3. Buy and measure one BLF-1203AB, BPC-1502DC, EN2P3M20/EN2C3F20G2 pair, and
   #4867 motor before ordering the full mobility set. Inspect purchased regulator
   revisions, trial-fit the purchased Panasonic CB1A-R-M-12V relay and Blue Sea
   5045 complete assembly, then obtain electrical review of charger inhibit,
   relay drive/suppression/reset, feeder and branch fusing, terminal and conductor
   sizing, regen/BMS behavior, and full-charge motor-voltage behavior.
4. Purchase the selected D85MG/R-ML24 stacks and verify their component-integral spline, horn-link, and mounting hardware. Buy one Adafruit 5975 breakout plus representative JST-SH cables; print and measure the v2 bayonet/journal/bushing coupons and one eye carrier/diffuser, assemble the complete printed-bearing servo stack, weigh the moving head, and test regulated current, cable sweep, axial play, backlash, heat, wear, repeated motion, LED hotspotting, and camera reflections.
   Print one eye carrier/diffuser set first and verify brightness, hotspots,
   light leakage, color, and service access before printing the second set.
5. Purchase one IDEC XW1E-BV402M-R, fit it to the printed keyed panel/backing
   interface, and perform terminal-access, controlled push/twist, dual-NC, and
   independent motor-cut tests.
6. Purchase at least two Omron D2HW-C202MR switches and select the TPU
   material/profile with the exact coupon; verify no preload, positive
   actuation, rigid-stop protection, lead strain relief, rebound, broken-wire
   fail-stop, and motor cutoff before buying/installing all six.
7. Verify the tray is handle-free and document an unpowered two-hand lift from
   beneath the tray. Do not install webbing or custom load-bearing metal.
8. Print the insert, split-pilot, deck-standoff, camera-carrier, motor-pod,
   front-bearing-seat, vent, and acoustic coupons before full PETG parts.
9. Print one harness rail and load it with representative power and signal
   bundles; verify connector passage, strap retention, bend radius, abrasion
   clearance, and clean separation before printing the second rail and deck.
10. Install the Camera Module 3 Wide in the printed head and inspect a
   full-resolution image at the pan/tilt center and limits. Reject the bezel if
   any corner shades, focus shifts, reflections appear, or the ribbon snags.
