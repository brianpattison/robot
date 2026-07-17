# Decision Log

This file captures settled project decisions so future planning, CAD, and software work do not need to re-argue the basics every time. Future us has enough screws on the floor already.

## D001: Build A Wheeled MVP, Not A Legged Robot

Status: accepted

The MVP body will be a compact wheeled indoor companion, not a legged robot. Dog-like behavior should come from motion language, voice, attention, following, looking toward the user, and idle presence.

Rationale:

- Wheeled locomotion is safer, cheaper, and much easier to make reliable indoors.
- The first win is a responsive physical companion, not complex biomechanics.
- Legged locomotion would consume the budget and schedule before we prove the interaction loop.

## D002: Use The Existing Raspberry Pi 5 8GB For MVP

Status: accepted

The existing Raspberry Pi 5 8GB is the MVP compute baseline.

Rationale:

- It is already owned.
- MVP responsiveness depends more on deterministic local reflexes, clean power, audio, sensors, and safety than on larger RAM.
- 16GB can remain an optional future upgrade if local models or memory-heavy workloads demand it.

## D003: Defer AI HAT+ 2

Status: accepted

AI HAT+ 2 is not required for MVP. The mechanical and power design should reserve room for a future AI HAT+ 2, but the first body should not depend on it.

Rationale:

- MVP safety, movement, voice, dashboard, and basic perception can work without a local AI accelerator.
- ChatGPT/Codex can remain the primary personality through a networked service.
- The first hardware budget should prioritize motors, power, sensors, E-stop, bumpers, and chassis iteration.
- AI HAT+ 2 remains useful later for local LLM/VLM experiments and offline fallback.

## D004: Safety And Reflexes Are Not LLM-Driven

Status: accepted

Safety-critical behavior must be deterministic and independent of LLM output.

Examples:

- E-stop cuts motor power.
- Bumper hit stops motors immediately.
- Watchdog timeout disables movement.
- Low battery forces stop or return-home behavior.
- `stop`, `wait`, and `mute` must have a fast local path.

Rationale:

- LLMs can choose high-level intentions, but they must never be trusted with raw motor authority.
- Physical safety needs boring, testable behavior.

## D005: Codex Is The Primary Agentic Identity

Status: accepted

The robot may use multiple models and services internally, but Codex/ChatGPT is the primary conversational and agentic identity.

Rationale:

- The body is intended to feel like Codex is physically present.
- Wake word, STT, TTS, object detection, and local classifiers are subsystems, not alternate personalities.
- This separation keeps the user experience coherent while allowing practical model choices.

## D006: Use Parametric CAD Source

Status: accepted

The printable body should be designed from parametric source files.

Defaults:

- OpenSCAD for first-pass blocky printable parts.
- `build123d` or CadQuery for Python CAD, richer assemblies, fillets, chamfers, STEP exports, and complex shells.

Rationale:

- Parametric CAD makes dimensions, mounts, clearances, and fit fixes easy to update.
- Source CAD is reviewable and reproducible.
- Generated STLs and STEP files should be treated as exports.

## D007: Build Voice And Bench Brain Before Autonomous Motion

Status: accepted

The first implementation slice should be a stationary bench brain before a roaming chassis.

Rationale:

- Camera, mic, speaker, wake word, TTS/STT, dashboard, and command routing can be tested safely on the desk.
- Voice and status behavior define the companion experience.
- Movement should wait until safety hardware and manual control are working.

## D008: Start MVP Storage With microSD

Status: accepted

For MVP storage, start with a reliable microSD card. Do not choose an official Raspberry Pi M.2/NVMe HAT as the default storage path if we want to preserve a clean future AI HAT+ 2 upgrade.

Rationale:

- Raspberry Pi documents both AI HAT+ / AI HAT+ 2 and M.2 HAT+ as using the Raspberry Pi 5 PCIe connector.
- The official AI HAT+ 2 and official M.2/NVMe HAT are therefore competing for the same Pi 5 PCIe interface.
- Third-party PCIe switch/splitter boards may exist, but they add mechanical, power, driver, thermal, and stability risk and should not be an MVP assumption.
- A microSD card keeps the PCIe connector available for a future AI HAT+ 2 and avoids extra moving-body cable strain in the first build.
- USB SSD or compact USB flash storage remains an easy later upgrade for logs, captures, maps, models, or boot storage if microSD becomes limiting.

## D009: Target The Bambu Lab P1S

Status: accepted

The production print-layout target is a Bambu Lab P1S with the standard 0.4 mm
nozzle and Textured PEI Plate. Printable pieces must fit the 256 mm square bed
with an 8 mm edge reserve, and Bambu Studio plates should remain separated by
material profile and color.

Rationale:

- It is the user's selected printer target.
- One reproducible target keeps split seams, orientations, brims, supports, and material recipes from drifting between slicers.
- The 248 mm safe span leaves room for bed-edge variation while still fitting the current modular shell strategy.

## D010: Use MDDS10 As The Motor-Controller Mechanical Baseline

Status: accepted for CAD; purchase remains gated by bench testing

The Cytron SmartDriveDuo-10 MDDS10 is the current mechanical baseline for the
dual brushed-motor controller. CAD follows Cytron's official STEP footprint and
four-hole pattern, with front terminal service, cooling clearance, and a
separate deterministic Pico 2 safety shelf.

Rationale:

- One dual-channel board matches the two-motor differential-drive baseline.
- Cytron publishes a usable official STEP model, allowing the mount to be drawing-backed instead of generic.
- Keeping the controller removable and mechanically separate from the safety MCU preserves serviceability and the fail-stopped control boundary.
- Final purchase still depends on selected motor voltage, stall current, thermal behavior, and bench verification of the fused cutoff path.

## D011: Use The Pololu 99:1 25D Rear Drivetrain Baseline

Status: accepted for CAD; purchase and loaded-motion release remain gated

The rear drive targets two Pololu #4867 99:1 25D MP 12 V encoder gearmotors,
two #1569 metal brackets, and two #1997 4 mm-shaft M3 aluminum hubs. Printed
PETG wheel cores and TPU tires retain the concept's 86 mm wheel envelope, while
the metal brackets and hubs carry motor reaction and shaft torque.

Rationale:

- Pololu publishes dimension drawings and STEP geometry for the motor family, bracket, and hub, allowing the pod, tray, wheel core, cable path, and service cover to be validated as one drawing-backed stack.
- The 68.45 mm motor body clears the current battery envelope while preserving the shared Z=66 axle and concept-matched inboard wheel stance.
- At 79 rpm no-load with an 86 mm wheel, the theoretical speed is about 0.356 m/s, closely matching the 0.35 m/s supervised indoor cap without depending on a high-current HP motor.
- The published 0.10 A no-load and 1.8 A / 11 kg-cm extrapolated stall values materially reduce the prototype pack demand while preserving the #4847 mechanical envelope.
- Purchased-part inspection, <=0.45 A steady per motor on target surfaces, current and thermal measurements, encoder direction, wheel retention, deterministic motor cutoff, obstruction tests, and loaded skid-turn tests remain mandatory; the selection does not authorize autonomous driving.

## D012: Use D85MG Servos And A Bearing-Supported Pan Axis

Status: accepted for CAD; purchase and repeated-motion release remain gated

The head targets two Hitec D85MG 24T digital metal-gear servos with R-ML24
aluminum horns. A Koyo/JTEKT 6807-2RS bearing carries the rotating neck and head
weight independently of the pan-servo spline. The passive tilt side uses an
MF84ZZ flanged bearing and McMaster 92981A143 shoulder screw.

Rationale:

- Hitec publishes both a dimensional STEP model and electrical/mechanical data, allowing the servo case, output offset, flange holes, spline, horn stations, current, and torque assumptions to be explicit.
- The 29 x 13 x 30 mm body fits the compact concept-matched head without enlarging its visible 140 x 72 mm face envelope.
- The 6807 outer carrier and rotating inner-ring journal keep axial/radial head loads off the pan-servo spline while preserving the 60 mm visible collar.
- The conservative CAD estimate is about 0.598 kg-cm static tilt torque including a 25 g electronics allowance, below the published 0.9 kg-cm peak-efficiency torque at 6 V; measured mass, acceleration, cable drag, current, heat, backlash, and holding behavior still require physical validation.
- The dedicated 6807 seat/journal coupon must select printer-specific fits before the full neck stack is printed.

## D013: Use IDEC XW1E And Omron D2HW Safety Switches

Status: accepted for CAD; purchase and physical safety release remain gated

The physical E-stop targets the IDEC XW1E-BV402M-R with two direct-opening NC
contacts. Six bumper zones target Omron D2HW-C202MR sealed SPST-NC pin-plunger
switches. The E-stop contacts control the low-voltage cutoff/enable path rather
than carrying motor current directly.

Rationale:

- The IDEC device provides a documented 40 mm operator, two NC channels, direct opening, a 0.8-6 mm panel range, and a compact 48.7 mm rear depth.
- Clamping only a removable 4 mm keyed panel avoids an impossible thick printed stack while preserving a reinforced, serviceable roof interface.
- The D2HW-C202MR provides a sealed molded-lead NC package, M3 mounting ears on 13 mm spacing, and drawing-defined free, operating, and total-travel positions.
- A 0.4 mm nominal bumper gap, 2 mm actuation stroke, and paired 2.4 mm rigid stops provide modeled electrical margin without allowing the plunger to reach total travel.
- Purchased-part inspection, representative coupons, dual-channel E-stop verification, six-zone broken-wire tests, and independent motor cutoff remain mandatory before powered motion.

## D014: Use Separate Pololu Rails And An SW60 Motor Contactor Baseline

Status: superseded for sourcing by D024; legacy CAD remains until replacement fit is validated

The Pi 5 rail targets a Pololu D24V90F5 5 V regulator, and the head servos use
a separate Pololu D36V50F6 6 V regulator. The motor branch's mechanical cutoff
baseline is an Albright SW60 normally-open contactor on a custom metal carrier.
The removable battery interface is refined by D022 around a measured prototype
candidate; no household-release battery pack is selected yet.

Rationale:

- Both regulators have manufacturer drawings and drill patterns, so seven metal-standoff paths, terminal/wire access, and deck clearances can be validated instead of reserving anonymous boxes.
- Separate 5 V and 6 V rails prevent head-servo transients from sharing the Pi supply directly; measured startup, thermal, transient, and EMI behavior still govern release.
- The SW60 is a normally-open DC contactor intended for inductive loads and small traction motors, with documented M6 main studs, coil terminals, dimensions, and dropout behavior.
- A custom metal carrier keeps the printed deck from being the sole contactor retention or cable-torque path.
- D022 replaces the earlier anonymous maximum envelope with a lower-current coordinated motor, battery, charger, and rear-inlet prototype baseline while retaining physical and electrical release gates.
- Exact SW60 coil ordering code, suppression, dual-channel E-stop wiring, reset latch, fusing, conductor sizing, charging, battery certification, and full-charge motor-voltage limiting require electrical-engineering review and physical testing.

## D015: Use Connectorized Adafruit 5975 Expression LEDs

Status: accepted for CAD; buy-one fit and optical release remain gated

The two head eyes and two body status lights each target one Adafruit 5975
NeoPixel breakout with keyed JST-SH input/output. The CAD follows Adafruit's
official STEP rather than a generic rectangular keepout and retains each board
with two M2 fasteners, 3 mm-OD spacers, and the existing removable carrier.

Rationale:

- The 12.192 x 11.43 mm PCB fits all four existing carrier envelopes without enlarging the concept-facing diffusers.
- Two documented M2 holes and keyed plug-in harnesses are easier to assemble and replace than the smaller solder-pad-only Mini Button board.
- Rotating the head boards 90 degrees keeps both plug paths clear of the carrier screws and restores the validated full pan/tilt envelope after reducing the carrier plate to 3 mm.
- One RGB pixel per diffuser limits the four-board worst-case design allowance to about 240 mA at 5 V before software brightness limiting.
- The expression branch is not safety-critical and must not be treated as a motion-status interlock. A failed LED or data line cannot authorize motion.
- Buy one board first. Delivered dimensions, M2 stack, JST insertion/removal, flexible cable bends, diffuser hotspotting and color, camera reflections, software-off behavior, and fused 5 V distribution remain physical release gates.

## D016: Split The Rear I/O Panel Into Three Service Cartridges

Status: accepted for CAD; D019 selects mute, D021 selects service, D022 selects charge-only inlet

The rear shell keeps its existing 126 x 58 mm four-M3 service frame, but the
center is divided into three independently removable cartridges assigned to
power/charge, service/data, and mute/status. Each flush 30 x 30 mm cartridge
uses a stepped 26 x 18 mm locating tongue and two M2.5 screws into frame-backed
inserts.

Rationale:

- Selecting or revising one connector no longer requires reprinting the full rear frame or reopening the shell.
- Exterior screw access and retained blanks let harness routing be proven before battery, charger, and service connectors are frozen.
- The six small insert bosses are explicitly removed from the internal service-bay keepout, so future cartridge designs cannot pretend that volume is unobstructed.
- D019 populates rear-right with the drawing-backed PVB3 physical mute, D021 populates center with the shallow protected UART service jack/carrier, and D022 populates rear-left with the keyed EN2 charge-only inlet. All three remain independently reprintable and purchased-part gated.

## D017: Use Two MAX98357A Boards Beneath The Speaker Plates

Status: accepted for CAD; current-board fit and stereo audio release remain gated

Each enclosed speaker receives one Adafruit #3006 MAX98357A mono I2S amplifier
mounted component-side-down beneath its removable speaker plate. The pair shares
BCLK, LRCLK, DIN, power, and ground; separate SD/MODE networks select left and
right channels.

Rationale:

- Analog Devices documents stereo operation using two MAX98357A devices, and each Adafruit board has only one bridge-tied speaker output.
- Putting one board beside each speaker keeps amplified PWM speaker leads short and frees the crowded power deck.
- Adafruit's official PCB source and STEP provide the 17.78 x 19.05 mm outline, two 2.5 mm holes on 12.7 mm spacing, and 1.57 mm substrate, allowing four real M2 standoff paths instead of anonymous strapped boxes.
- The official STEP dates from 2022 and omits the terminal block Adafruit began shipping pre-soldered in 2024. The model therefore keeps conservative terminal, screwdriver, wire-bend, and header/direct-wire envelopes without claiming those dimensions are final.
- Buy one current board first. Measure the supplied terminal and chosen harness, prove M2 fit and tool access, select left/right SD/MODE networks at the actual supply voltage, and verify current, heat, noise, grille behavior, and audio before purchasing or releasing the pair.

## D018: Retain Each Front Idler With A DIN 471 Ring And Pololu Hub

Status: superseded by D024; retained as the rejected machined-shaft history

Each removable front idler uses a 64.5 mm x 8 mm steel shaft with a Rotor Clip
DSH-8 / DIN 471 external ring at the inboard end and a Pololu #2693 aluminum
hub at the outboard wheel core. A steel washer, two 608 bearings, and two
metal spacer tubes define the axial stack.

Rationale:

- Rotor Clip publishes the 7.54-7.60 mm groove diameter, 0.90 mm groove width, 0.75-0.80 mm ring thickness, and 0.60 mm minimum edge margin for the DSH-8, replacing the previous generic collar envelope with machinable dimensions.
- The compact ring clears the Pi and motor-controller envelopes that a large inboard clamp collar did not.
- Pololu #2693 provides two set screws for the 8 mm shaft and six threaded M3 wheel paths on a 19.05 mm circle in a documented 25.4 x 14 mm body.
- The printed pod locates the bearing outer races and transfers reaction to the tray; metal hardware establishes spacing and prevents axial escape.
- Release still requires a qualified shaft supplier or inspected groove, deburred bearing journals, full ring seating, spacer squareness, both hub set screws, verified screw lengths, controlled axial play without bearing preload, wheel retention, and loaded skid-turn testing.

## D019: Use A Maintained Red-Ring PVB3 Physical Mute Switch

Status: accepted for CAD; purchased-switch and privacy-circuit release remain gated

The rear-right service cartridge targets the E-Switch PVB3F230SS311 maintained
SPDT anti-vandal switch. Fused microphone 5 V enters common; one maintained
throw powers microphone VBUS, while the other feeds the muted indication and a
protected state input. D021 independently populates the center service/data cartridge.

Rationale:

- A maintained physical state is visible and survives application, network, or Pi failure; the privacy path does not depend on a software toggle.
- The official drawing provides a 16.0 mm cutout with 14.6 mm flats, 18 mm bezel, 11.2 mm actuator, 12.8 mm LED ring, 26 mm rear body, and 1-7 mm clamp range, allowing a real cartridge and validator contract.
- The red ring gives an unambiguous local muted indication. The base red LED is documented at 1.8 V / 20 mA, so it requires a calculated resistor from the selected rail.
- The concept-positioned IDEC E-stop blocks the center cartridge's rear depth. Moving mute/status to rear-right provides at least 8.2 mm body clearance and 5.5 mm terminal-service clearance without changing the exterior frame.
- Charge remains an independently reprintable cartridge; D022 can populate it without disturbing mute or service.
- Release still requires purchased-part/nut fit, mounting torque, LED polarity and resistor checks, protected 3.3 V state sensing, removable-harness strain relief, USB backfeed testing, local capture-loss proof with software stopped, visible-state agreement, and repeated intentional restore tests.

## D020: Reject The Littelfuse 880024 From The Upper Power Deck

Status: rejected by CAD packaging audit; replacement selected in D023

The Littelfuse 880024 SD MINI four-way fuse block is not the v1 upper-deck
solution. Its official 85 x 47 mm plan envelope and 49.2 mm total stack were
modeled with terminal, cover, and mounting service space, then checked against
the complete current assembly.

Rationale:

- Every practical horizontal placement overlapped at least one protected volume: the IDEC E-stop body/terminal corridor, rear service bay and mute harness, left speaker/MAX98357A stack, or SW60 service envelope.
- Raising the block enough to preserve its lower 6.3 mm quick-connects kept terminals out of the battery bay but drove the housing and cover into roof-mounted hardware.
- Moving or shrinking those safety and service envelopes merely to accept a fuse block would make the model less truthful.
- The former 60 x 26 x 18 mm distribution reserve was only a provisional packaging target, not an endorsed component; D023 replaces it with a documented custom-board contract.
- The replacement must provide four separately sized accessory branches, protected live parts, removable fuse access, documented current/temperature ratings, strain-relieved terminals, and primary-source mechanical dimensions. The motor branch remains separately fused and independently cut by the deterministic E-stop chain.

## D021: Use A Shallow Protected TRRS UART Service Port

Status: superseded by D024; center rear cartridge is blank

The center rear cartridge now targets the Switchcraft 35RASMT5CHNTRX
four-conductor 3.5 mm jack on an 18 x 18 mm custom 3.3 V UART/service PCB. A
separate printed L-carrier bolts through the cartridge with two M2 screws and
holds the PCB with two more. Tip is robot TX, ring 1 robot RX, ring 2
service-detect, and sleeve ground.

Rationale:

- Switchcraft documents a 15.5 x 6.8 x 5.3 mm low-profile package, four gold-plated conductors, 5000-cycle life, and 85 C maximum temperature, allowing a real fit contract instead of another generic connector block.
- The shallow right-angle stack stays at least 8 mm in front of the E-stop body; larger USB-C feedthroughs evaluated for the same cartridge extend into the protected E-stop corridor.
- The removable carrier gives the small SMT jack a serviceable mechanical interface without asking the 1.25 mm cosmetic cartridge face to carry plug loads or PCB fasteners.
- The port exposes no raw battery, 5 V, motor-enable, or safety-bypass signal. It is not audio and must never be connected to RS-232 or an unverified headset/adapter.
- A labeled USB-powered adapter supplies its own power and uses protected 3.3 V UART levels. Series resistance, ESD protection, a defined service-detect bias, ground-first behavior, and connector pinout belong on the interface PCB.
- Service-detect may request deterministic motion inhibit but cannot authorize motion or replace E-stop/bumper isolation. Enter service with the motor branch physically isolated, and require intentional reset after disconnect.
- Release requires the purchased jack and plug, fabricated PCB, insertion/removal, shorts during mating, ESD, level, signal-integrity, adapter-labeling, repeated service-mode, and no-automatic-restart tests.

## D022: Coordinate The MP Motor, Flat LiFePO4 Pack, And Charge-Only Inlet

Status: accepted for prototype CAD; purchase, electrical review, and loaded release remain gated

The first rolling prototype targets two Pololu #4867 99:1 25D MP 12 V encoder
motors, one Bioenno BLF-1203AB 12 V/3 Ah LiFePO4 pack rotated flat, the matched
Bioenno BPC-1502DC 14.6 V/2 A charger, and a Switchcraft EN2P3M20 panel inlet
with EN2C3F20G2 female cord mate. Two EN2 contacts carry isolated charge +/-;
the third is protected `CHARGER_PRESENT`. The inlet is charge-only and exposes
no battery output.

Rationale:

- The #4867 preserves the validated #4847 mechanical stack while reducing the published electrical baseline to 79 rpm, 0.10 A no-load, and 1.8 A / 11 kg-cm extrapolated stall per motor. Its 86 mm-wheel no-load speed is about 0.356 m/s, aligned with the MVP cap.
- Bioenno documents the BLF-1203AB at 110 x 27 x 75 mm, 7 A continuous and 14 A for two seconds, with internal PCM/BMS protection, separate Powerpole discharge and 5.5 x 2.1 mm charge leads, MSDS, and UN38.3 transport evidence. Rotating it produces a 110 x 75 x 27 mm fit inside the existing body.
- The matched charger avoids inventing a LiFePO4 charge profile. The keyed, sealed, locking EN2 pair avoids exposing a generic barrel connector on the robot and provides a third contact for deterministic charger-presence inhibit.
- Switchcraft marks EN2 as unsuitable for current interruption. Mate or unmate only with charger AC removed; insertion must de-energize motor enable/SW60 and removal must require explicit reset.
- Buy one pack, charger, connector pair, and motor first. Release requires delivered geometry and evidence review, polarity/insulation/strain relief, <=0.45 A steady per motor on target surfaces, <=5.6 A sustained pack current, 45-minute mixed use with 20% reserve, full/low-charge floor tests, BMS/regen/thermal behavior, obstruction response, and deterministic no-restart charger inhibit.
- D023 selects a mechanically packaged custom four-branch distribution board; exact source/branch fuse values, PCB copper, SW60 coil variant and suppression, conductor sizing, and full-charge motor-voltage behavior remain open for electrical review.

## D023: Use A Covered Four-Branch Nano2 Distribution PCB

Status: superseded by D024; retained as the rejected custom-PCB history

The upper power deck uses a custom 40 x 21 x 1.6 mm accessory-distribution PCB
with four Littelfuse 01550900M OMNI-BLOK holders for replaceable Nano2 fuses.
A Molex 43045-1000 right-angle ten-circuit Micro-Fit header mates with a
43025-1000 latched receptacle. Two contacts are source positive/return; the
other eight are four separately fused positive/return branch pairs. The board
mounts on four 4 mm lower plus four 3 mm upper M2 metal standoffs beneath a
removable printed touch cover. A separate deck strap captures the first cable
bend.

Rationale:

- No complete catalog four-way module fits the protected body. Littelfuse 880024 is 85 x 47 x 49.2 mm serviced, and BPDMA104HXF1 is 86 x 34 x 77 mm; both collide or exceed the current deck/body envelope.
- Each 01550900M holder is only 9.73 x 5.03 x 3.81 mm, rated 10 A from -55 to 125 C, and accepts replaceable 451/453 fast-acting or 452/454 time-delay Nano2 fuses.
- The 43045-1000 is shrouded, polarized, latched through its mate, UL94 V-0, and drawing-backed at 18.65 mm across ten circuits. The ten-circuit harness supports a conservative 7 A/contact design limit with the selected wire/contact system.
- The complete board is capped more conservatively at 6 A total and 5 A on any branch. Those are design ceilings, not permission to choose 5 A fuses everywhere.
- Four lower standoffs retain the PCB; four upper stacking standoffs retain it independently before the cover screws are installed. The printed cover provides touch protection only and does not carry connector loads or establish conductor ampacity.
- A one-piece production-derived PETG gauge reproduces the PCB, four holder/fuse stacks, header, and four M2 paths so deck/standoff/cover fit can be rejected cheaply before ordering a PCB. It is mechanically exact but intentionally nonfunctional.
- Exact fuse values follow measured startup, steady, transient, fault, conductor, and time-current data. A battery-near feeder fuse remains mandatory because branch fuses do not protect the upstream cable.
- Release requires a reviewed 2 oz-copper layout, correct Molex contacts and tooling, crimp inspection/pull tests, durable labels, power-off-only fuse replacement, far-end selective short tests, all-branch thermal soak, vibration/tug testing, no cross-branch backfeed, and proof that the board cannot bypass the motor source fuse, SW60/E-stop chain, or charger-present inhibit.

## D024: Require Quantity-One US Retail Hardware

Status: accepted and implemented in the current body source; physical release remains gated

Every production hardware item must be purchasable in quantity one through a
normal US online checkout. Printed parts and wiring harnesses assembled from
retail components remain in scope, but RFQ-only parts, overseas-only sources,
factory minimums, custom-machined metal, custom sheet metal, and
custom-fabricated PCBs are rejected unless the user explicitly approves an
exception.

Rationale:

- A reproducible home build cannot depend on distributor quotes, export ordering, machine-shop work, or one-off PCB fabrication.
- Safety- and power-critical parts should preferably have two independent US sources, a manufacturer part number, a primary datasheet, and visible quantity-one stock before CAD is frozen.
- The Albright SW60/custom-carrier path and the intermediate Cole Hersee/Littelfuse 24117-01-BP candidate are rejected. The implemented cutoff is the Panasonic CB1A-R-M-12V sealed SPST-NO automotive relay: integral bracket with one 5.4 mm mounting hole, 40 A contacts at 14 V, 12 V/134 mA coil, built-in resistor, and retail availability. Release still requires delivered-part fit, correct terminal/conductor sizing, driver and suppression review, dropout, thermal, fault, and deterministic cutoff tests.
- The custom four-branch distribution PCB is rejected. The implemented replacement is the complete Blue Sea Systems 5045 covered four-circuit ATO/ATC fuse block, modeled at 92.5 x 43.8 x 32.5 mm with two mounting holes on 65.1 mm centers. Preserve the conservative 6 A total / 5 A any-branch ceilings, battery-near feeder fuse, branch selection from measured loads, touch protection, strain relief, labels, selective clearing, and thermal release gates.
- The custom grooved front-idler shafts, DSH-8 rings, and cut-to-length spacer tubes are rejected. Each implemented idler uses a WDS 615-M6-8-65 shoulder bolt, M6 washer, prevailing-torque locknut, and stock goBILDA spacers/shim. Purchased fit, thread engagement, axial play, retention, alignment, and loaded skid-turn tests remain mandatory.
- The custom rear UART PCB and jack are omitted. The center rear cartridge is blank; internal service requires shutdown or physical motor-branch isolation.
- Carry handles and custom clamp plates are omitted. Lift only the unpowered robot with two hands under the tray until a complete retail lifting interface is separately selected and qualified.
- D024 supersedes the production instructions in D018, D021, and D023 without deleting their historical rationale. Any generated manifest, image, Bambu project, or assembly-guide language that still names those interfaces is stale until regenerated from the retail-only source.

## D025: Printed-Only Structural Hardware

Status: accepted 2026-07-16; per-subsystem physical release gates apply

No purchased metal structure remains in the body: no brackets, standoffs,
spacers, shoulder bolts, bearings, hubs, washers, or locknuts. Structure is
printed PETG/TPU plus heat-set inserts and screws (see D026). Electronics,
motors, servos, switches, the battery, and hardware that ships attached to a
purchased component (E-stop nut, relay integral bracket, servo horns and horn
screws, connector nuts) remain purchased. Details and per-subsystem test
gates: [`printed-only-simplification-plan.md`](printed-only-simplification-plan.md).

Rationale:

- Replacements: tray-integrated motor saddles with bolted clamp caps plus the
  motor's own tapped M3 face holes (supersedes #1569 brackets as retention);
  wheel cores with integrated calibrated 4 mm D-bores plus one radial clamp
  screw (supersedes #1997 hubs); printed stub axles with replaceable printed
  bushings for the passive front wheels (supersedes the WDS shoulder-bolt /
  608 / goBILDA stack); greased printed pan journal with a bayonet collar and
  a printed tilt shoulder bushing (supersedes 6807-2RS, MF84ZZ, and the
  92981A143 shoulder screw); printed towers and pocket-peg-clamp PCB cradles
  (supersede all metal standoffs/spacers); printed saddle/pocket captures for
  the Blue Sea 5045 and Panasonic relay; printed PETG clamp bar with printed
  TPU pads for battery retention (supersedes textile straps).
- Torque and shear always pass through printed geometry (D-bores, keys,
  tongues, pockets); screws only clamp. No plastic thread or friction fit
  retains an axle — retention screws thread into metal inserts.
- Release gates before powered motion: D-bore coupon holds 2x the 11 kg-cm
  extrapolated stall torque without creep or slip; clamp-cap retention
  shake/pull test; loaded skid-turn axle wear test; battery clamp inverted
  shake and tilt-drop test; pan journal wear/current-rise cycle test.
- Fallback geometry is preserved, with precise strength (amended 2026-07-16
  across two reviews): the wheel core keeps the #1997 four-hole pattern and
  hub recess (true drop-in); the motor saddles keep the #1569 bracket's
  FULL installation envelope — 49 x 22 base, three M3 tray stations, 3 mm
  spacer stack, and tool access — as a registered fit volume, not just the
  holes (true drop-in); the battery bay keeps strap channels (true
  drop-in). The idler bushing cavity matches the 608 envelope, but a 608
  there rides the printed axle — it does not restore the WDS shoulder-bolt
  stack. The head pan journal has no drop-in fallback; reverting to the
  6807 requires reprinting the neck carrier/journal parts from a parametric
  switch kept in the source.
- D024's quantity-one US retail sourcing rule still governs everything that
  is purchased; this decision narrows what is purchased.
- Supersedes the metal-retention language in D011 (bracket/hub as primary
  retention), D012 (bearing-supported pan axis), and D024's shoulder-bolt
  idler stack. Any manifest, image, or guide naming those interfaces is stale
  until regenerated.

## D026: Single Fastener SKU

Status: accepted 2026-07-16; scope wording amended same day after review

The only separately purchased body-fastener SKUs are M3 x 5.7 mm x 4.6 mm OD
heat-set inserts and M3 x 8 mm socket head cap screws — one 100-pack of
each, one 2.5 mm hex key. Hardware bundled with purchased components (servo
horn screws, switch/connector nuts, the relay's bracket hardware) is exempt,
keeps its own model parameters, and requires no separate purchase. The
validator rule is "no separately-purchased fastener other than the two
SKUs," not "zero non-M3 references."

Rationale:

- The insert OD matches the existing `insert_hole_m3 = 4.6` parameter, so M3
  insert coupon calibration carries over.
- A validator-enforced clamp-stack rule (every screw path presents
  3.0-3.4 mm of clamped material via counterbores) makes the single 8 mm
  length work everywhere; an engagement-limit rule locally thickens flanges
  where screws enter parts with limited thread depth (Pololu #4867 face
  holes, verified against the drawing).
- PCBs with sub-M3 mounting holes (Pi 5, Pico 2, regulators, amps, ToF,
  NeoPixel, camera) are captured by printed pockets, locating pegs, and
  clamp bars instead of screwed through their holes; the MDDS10's 3 mm holes
  may take direct M3 screws.
- Printed PETG washers are used wherever a screw head would bear on TPU.
- Hardware bundled with purchased components is exempt and requires no
  separate purchase.
- Supersedes the M2/M2.5/M3/M4/M6 mixed-fastener baseline and the
  M2.5/M3/M4 insert kit in the BOM.

## D027: One-Piece 238 x 220 Body Footprint

Status: accepted as direction 2026-07-16; appearance deltas approved by
Brian the same day; the packing gate is OPEN. Three same-day review rounds
invalidated the first three box layouts; the current box screen (layout
v5, on verified model datums) closes with a 2 mm margin policy including
wall margins, but the gate requires the v2 BREP packing model plus a
passing inventory-driven production validator before any detailing builds
on the footprint.

The body shrinks from 300 x 220 to 238 x 220 and grows to 133 mm body
height (computed on verified datums, see below) so the shell, tray, and
lid each print as one piece on the P1S (240 mm usable with the 8 mm edge
reserve). The 57-part split contract, nine backing plates, 18 pilots, and
lap-lid joinery are deleted rather than simplified. The TPU bumper becomes
two C-halves joined at the side switch plates with printed dovetail laps.
Fairings merge into the shell as sculpted surface; the three rear
cartridges collapse to one rear panel; the vent inlay becomes a snap-in.

Rationale:

- Review round 1 (2026-07-16): the first study hardcoded reduced envelopes
  and omitted the E-stop's 66 mm panel/backing, the 28 mm battery-lead
  corridor, the AI-HAT reserve, Pi connector service, and keepout-keepout
  collisions, and its rotated MDDS10 kept an impossible front-facing
  terminal corridor. Its FEASIBLE result was withdrawn.
- Review round 2 (same day): layout v3 was also rejected, correctly — the
  mute switch needs 42 mm (26 body + 16 terminals), the fuse block's 22 mm
  wire service was absent, the MDDS10's 10 mm airflow contract was
  violated by 5.8 mm, the AI-HAT reserve is 96 x 74 x 22 (not 85 x 60 x
  18), incidental 0.1-1 mm clearances were rejected, and the battery riser
  was unmodeled. A new wheel-envelope check also pulled the axles in to
  ±74 (148 mm wheelbase).
- Review round 3 (same day): layout v4's datums were wrong, verified
  against the model: the tray top is Z=49 (`body_bottom`), the MDDS10
  thermal ceiling is 86.275 (`motor_controller_plate_top_z()` chain; the
  old formula also double-counted the PCB), the pan-servo drop bottom is
  131.6 (`pan_servo_fit` bounding box), and the deck plate is 102..106.
  Round 3 also added the D24V90F5's two terminal corridors, the D36V50F6's
  west-facing wire corridor, the full-height fuse wire corridor, the
  relay's full 52 x 22 bracket + body/terminal volume, and three policy
  fixes (overlap never waivable, exact-name allowlist, wall margins).
- Layout v5 (`cad/python/packing_study_printed_only.py`) closes with zero
  violations and no margin under 2 mm: body 238 x 220 x 133, where +12 mm
  is computed (thermal ceiling 86.275 + 4 shelf + 28 Pi + 22 HAT + 3
  margin = 143.275 required drop bottom vs the v1-derived 131.6) after
  offset-shelf alternatives failed at box level; MDDS10 terminals north;
  Pi shelf at the thermal ceiling with the full HAT reserve above and Pico
  on a NW wing; fuse block owning the deck's south half with a full-height
  wire corridor; E-stop at (55, 52) dropping entirely above the 102..106
  deck plate; EN2/mute swapped (charge north, mute south at full depth);
  battery riser through a deck notch; relay on the floor at X -46..6 with
  its complete envelope; regulators under the deck with all corridors;
  mic (60, -25); vent south strip; speakers on the FORWARD side walls with
  a 6 mm arch web. Rough CG X~7. The stacked 28+22 Pi/HAT band is
  deliberately conservative; BREP with the real HAT drawing may recover
  ~10 mm of height.
- Brian approved the appearance direction (off-center E-stop, offset mic,
  smaller vent, forward side-firing speakers, taller body, swapped rear
  connectors) on 2026-07-16; the height was subsequently revised 144 ->
  133 by the round-3 datum fix, within the approved direction.
- Review round 4 (same day) reproduced v5, verified the datums, and
  green-lit Phase 2 with four carry-in requirements (Pico USB/SWD
  corridors — fixed at box level in v5.1 by relocating the Pico to the
  floor NE quadrant; battery padding/clamp modeled; relay as three exact
  volumes; AI-HAT height recovery only as a BREP-discovered bonus). The
  gate itself stays open until the v2 model passes the inventory-driven
  validator.
- Fallback remains Option B (300 x 220 with integrated-flange half-splits)
  if BREP detailing breaks the box-model margins.

## D028: Part-Count Budget And Support-Free Printing

Status: accepted 2026-07-16 as v2 design requirements; enforcement lands
with the Phase-2 inventory-driven validator

The v2 printed inventory has a hard budget of 40 parts for the complete
robot (body + head + TPU tires, excluding calibration coupons and
explicitly optional cosmetics), and a zero-support target: every part
declares a print orientation, passes an overhang audit (no downward face
beyond 50 degrees from vertical outside allowlisted convex-rollover
regions) and a bridge-span audit in that orientation, and the
support-exception list starts empty — any entry requires a named reason
and sign-off. Details and the merge list:
[`printed-only-simplification-plan.md`](printed-only-simplification-plan.md).

Rationale:

- Brian's directive: badly wants fewer parts and easier printing with
  fewer supports; these become requirements the validator enforces, not
  aspirations a layout drifts away from.
- v1 baseline: 101 printed parts on 26 plates, with the shell quadrants
  and head shells requiring build-plate supports per the print manifest's
  own guidance. The v2 one-piece footprint already deletes the split
  system; D028 pushes integration further (switch pockets into the tray,
  harness rails into the deck, ToF pods into fascia/shell, pod shrouds
  into the shell, one controller-tower part, optional vent inlay and trim
  rings) toward ~36-42 parts.
- Every separately printed part must justify its existence: service
  access, material/color change, orientation conflict, calibration
  interface, or wear-part replaceability.
- Support-free design rules: up-opening troughs for motor saddles;
  upright shell with the convex rollover as an allowlisted dome-like
  region and chamfered/arched opening tops; cosmetic-face-down flat
  parts; 45-degree gussets under interior shelves; teardrops or
  vertical-axis redesigns for holes over 8 mm; open-section TPU; bridges
  capped at 30 mm; insert bosses biased vertical.
- Integration risk accepted deliberately: molding the bumper-switch
  pockets into the tray commits the coupon-calibrated 0.4/2.0/2.4 mm
  interface to the tray print; the recovery path if a printed tray still
  misses is a shim plate, not a tray reprint policy.

## D029: The Builder's Book Is A Retail-Grade Manual With No Grown-Up Callouts

Status: accepted 2026-07-16 (Brian's direction)

The v2 assembly guide is written and designed as a professionally
produced kit manual, and it must stay easy enough for a child to follow
WITHOUT ever labeling steps as needing a grown-up. The previous
"GROWN-UP STEP" banners, red step numbers, cover badge, and grown-up
tool/chapter framing are removed and must not be reintroduced. Safety
content stays; it is presented as plain instructions and checklists
(soldering-iron temperatures, meter checks, fail-stopped rules), not as
age gating.

Rationale:

- Brian's directive: the project should be polished until it could sell
  as a super easy-to-assemble kit; the guide should read like a
  professionally designed product, and the grown-up callouts are
  unnecessary.
- Child-followable stays a hard requirement: picture-first steps, one
  screw size, GATHER strips, per-step CHECK tests, and playful copy are
  the mechanism, in place of age labels.
- The book's design system (Avenir Next type, chapter thumb tabs with
  SHOP/PRINT/BUILD/WIRE/PLAY accents, step progress bars, computed cover
  TOC, annotated meet-the-robot spread, piece-inventory chart, hairline
  tables, back cover) is the retail-grade baseline; future edits should
  extend it rather than regress to the earlier utilitarian layout.

## D030: The Resident Agent Has Full Authority Over The Robot Computer

Status: accepted 2026-07-17 (Brian's direction)

The resident agent (Claude or Codex, per D031) gets full control of the
Raspberry Pi: live SSH access, code and scripts written on the fly, package
and service installs, direct velocity and head setpoints through the
`robotd` body daemon, and management of its own behaviors, schedules, and
memory. The fixed high-level intent vocabulary is retired as the control
boundary; the old intents survive only as the starter behavior library the
agent inherits and rewrites. Every `robotd` command and agent shell session
is captured in an append-only blackbox. See
`docs/agentic-control-plan.md`.

Rationale:

- Brian's directive: give Claude or Codex full control — live SSH, code on
  the fly, software installs, whatever the robot needs to get around, talk,
  and answer questions.
- An agentic model's value is writing code against reality. Nine canned
  intents cap the robot at its author's imagination and waste the model.
- Full software authority is safe to grant because the deterministic floor
  moved into hardware and firmware the Pi cannot alter (D032).
- The blackbox and recorded sessions keep trust inspectable after the fact
  instead of pretending to enforce it up front.

## D031: The Agent Seat Is Pluggable: Claude Or Codex

Status: accepted 2026-07-17 (Brian's direction)

Revises D005. The robot has one agent seat, and either Claude (via Claude
Code or the Claude Agent SDK) or Codex (via the Codex CLI) occupies it. One
resident narrator at a time; wake word, STT, TTS, perception, and other
subsystems remain tools, not alternate personalities. D005's coherence goal
stands — only its exclusivity to Codex is revised.

Rationale:

- Brian consistently frames the operator as "Claude or Codex"; the
  architecture should make the seat a choice, not a rebuild.
- Everything below the seat (voice services, `robotd`, firmware) is
  identity-agnostic, so pluggability costs one abstraction, not a redesign.
- One-narrator-at-a-time preserves the coherent-companion experience D005
  was protecting.

## D032: The Safety Floor Is Physical And Firmware Only, And The Pi Cannot Reach It

Status: accepted 2026-07-17 (Brian's direction)

Refines D004, which stands. The deterministic floor is exactly: E-stop,
normally-closed bumper loops with latched stops, watchdog, firmware
velocity/acceleration clamps, charger-present motion inhibit, low-battery
cutoff, and the hardware microphone mute. It is enforced by the safety MCU
firmware and physical controls. The Pi-to-MCU link carries only the framed
command/heartbeat protocol with no flash, bootloader, or config-write path;
the Pico's USB/SWD are service corridors never cabled to the Pi in
operation, so reflashing requires opening the robot. Firmware accepts a
rate-limited budget of remote bumper latch clears; past it, and always for
E-stop, recovery requires a physical reset input.

Software guardrails the firmware cannot sense — no-go zones, quiet hours,
supervision expectations, upload rules — are reclassified as policy the
agent is instructed to honor and the blackbox audits, not enforcement.

Rationale:

- Under D030 the agent has root on the Pi, so any Pi-side gate is a
  convention. Drawing the line where it can actually hold is more honest
  and therefore safer than layered software theater.
- The Pico 2 safety shelf, relay coil path, NC loops, and service-corridor
  wiring already position the hardware for exactly this boundary.
- Policy violations become visible and auditable; physics violations stay
  impossible from software. The worst honest failure is a capped-speed
  bump that latches stopped.
