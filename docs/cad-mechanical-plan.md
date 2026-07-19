# CAD Mechanical Plan

## Current v2 material and print policy

The v2 authority is `robot_body_v2_inventory.py` -> `robot_body_v2.py` ->
`validate_robot_body_v2.py --gate` -> the print/Bambu manifests. D034 separates
material family, mechanical role, and theme color for every registered part.
The fascia, rear panel, head faceplate, two diffuser bars, and optional lid
skin are direct PLA roles. The shell and head are PLA candidates with
independent automatic white-PETG fallback until exact-filament evidence passes.
All sustained structure, motion/wear, battery retention, safety-MCU retention,
and the E-stop lid remain PETG in white, black, or red; the three flexible part
families remain charcoal TPU 95A.

The optional 1.2 mm teal PLA lid skin uses four integral tabs in blind pockets
and duplicates the vent/microphone openings. It carries no E-stop, neck,
microphone, corner-screw, or shell load; the complete 4 mm white PETG lid works
without it. Inventory is 40 installed functional pieces + four spare washers +
one optional skin, 45 printed pieces total. The support-exception list is empty.

Eighteen material/mechanical qualification proofs now cover the legacy interfaces plus PLA
insert, shell-wall/opening, head-pivot, snap, optical, and PETG/PLA lid-boundary
evidence. The generated manifest requires manufacturer, product line, subtype,
color, nozzle, layer height, walls, insert temperature where applicable,
measurements, pass/fail, tester, and date. A blank record means the gate is open.

## Current v2 printed-only head mechanism (D035)

The v2 pan load path is now production geometry, not a prose placeholder. A
three-lug PETG collar bayonets into a blind underside race in the complete
structural lid. Its 40.3 mm printed bore supports the neck's 39.6 mm journal at
0.35 mm radial clearance; a 48 mm neck shoulder rides the collar's flat thrust
face. The collar integrates a downward D85MG cradle, while a removable 3.2 mm
black-PETG plate captures the servo flange with two standard M3 x 8 joints. The
R-ML24 horn drives the neck from below at its 13/16 mm M2 stations, leaving the
+X crescent and 20 mm center bore open for the camera ribbon. Commanded pan is
+/-60 degrees; printed collar/neck tabs engage beyond that range.

The black-PETG yoke attaches to four inserts in the neck flange with standard
M3 x 8 joints. Its active side carries the drawing-backed sideways D85MG frame
and R-ML24 horn; the head shell's integrated drive boss is reachable through
two exterior M2 service paths. The passive side uses a replaceable 3.2 mm PETG
shoulder bushing clamped by one M3 x 8 into a blind yoke insert, so the shell
rotates on the bushing instead of being pinched by the screw. Commanded tilt is
+/-20 degrees, with printed hard stops beginning beyond the command range. The
head shell's internal relief is generated from the actual yoke swept through
the hard-stop range rather than from a hand-maintained box.

`validate_robot_body_v2.py --gate` now checks both servo-case clearances, the
pan journal clearance, the 20 mm cable corridor, sampled collision-free command
ranges, and engagement of all four physical stops. CAD completion is not a
powered-motion release: exact-part fit, the bayonet/journal/bushing proofs,
PETG-safe grease selection, head mass, regulated current, cable drag, axial
play, backlash, temperature, and loaded wear cycling remain physical gates.

## Historical v1 implementation — not v2 build authority

The following section preserves the v1 source contract for historical rebuilds
only. Its metal brackets, hubs, bearings, shoulder bolts, standoffs, multiple
fastener families, and split body are not v2 purchases or assembly steps. The
v2 authority is the pipeline at the top of this document.

The historical source model is [`cad/python/robot_body.py`](../cad/python/robot_body.py), using build123d. It is organized as serviceable modules rather than one fused decorative mesh:

- Hollow rounded body shell with an open lower service side, a 12 mm visible top-edge rollover paired to an 8.8 mm inner radius for a full 3.2 mm roof, a crisp lower tray/seam interface, four ribbed tray lugs, four supported lid bosses, and side-fairing insert bosses.
- Separate handle-free base tray with matching M3 clearance holes, controller rail patterns, a locating lip, four-point pads beneath every mobility pod, and a two-half split variant with a piloted underside insert plate. Lift the unpowered robot with two hands under the tray.
- Removable 117 x 92 mm battery cradle seated directly on the tray with four insert-backed screw tabs, four pack support pads, two 20 mm real-strap channels, and positive side/end locators around the Bioenno BLF-1203AB's rotated 110 x 75 x 27 mm envelope. A conservative rear upper lead corridor covers the separate Powerpole discharge and charge leads pending delivered-part measurement.
- Hollow continuous TPU lower bumper carrier with a 302 x 222 mm rigid-chassis cavity, wheel arches, two concealed low inboard bridges, and six local plate reliefs sized for the nominal compression stroke.
- Six rigid PETG bumper-switch plates seated against the tray underside, each using two inboard M3 screws into blind tray inserts; drawing-backed Omron D2HW-C202MR sealed SPST-NC bodies use separate 13 mm M3 mounting stations, side-lead corridors, and paired rigid stops while remaining independent of the moving TPU.
- Removable teal top lid, dark reveal, recessed 80 x 62 x 1.6 dark vent inlay with nine through-slots, four M2.5 retainers, and a curved E-stop-panel clearance; continuous 40 mm E-stop service opening; and a 12 mm stepped lap in the two-half printer variant. The inlay spans both halves as a removable secondary seam clamp.
- Removable 4 mm keyed IDEC E-stop mount panel and raised-collar underside backing ring joined by four cardinal M3 paths on a 28 mm radius; the purchased switch nut clamps only the panel and remains primary retention.
- Four partly inset wheel/tire modules with recessed teal hub rings, 24 shallow transverse traction grooves per TPU tire, 2 mm intact sidewall bands, shared shell/fairing/bumper arches, and one tire-tangent ground datum.
- Drawing-backed left/right rear-wheel drive modules for Pololu #4867 99:1 25D MP 12 V encoder gearmotors, #1569 metal brackets, and #1997 4 mm-shaft aluminum hubs. The #4867 preserves the prior motor geometry while reducing extrapolated stall current from 5.0 A to 1.8 A per motor. The printed pods are removable shrouds with inboard installation paths and 2 mm cable-notched service covers; three M3 bracket paths per side clamp through metal spacers into the tray, while four M3 screws couple each PETG wheel core to its hub.
- Removable non-driven front idler pods with two 608-class bearing seats and two flush screw-on outer-race rings around one WDS 615-M6-8-65 shoulder bolt per side. An M6 washer, prevailing-torque locknut, and stock goBILDA spacers/shim provide the retail metal retention stack while preserving the concept's front wheels and two-motor MVP.
- Flush 2 mm scalloped side wheel-fairing skins seated in 2.2 mm shell recesses with 0.3 mm perimeter clearance, a 0.2 mm clamp gap, and 1 mm continuous backing; circular wheel arches and a large center relief preserve the molded-side silhouette, a narrow upper bridge keeps one part per side, and the 220 mm variant produces four independently fastened arch caps that clear the lower shell seam.
- Bearing-supported rotating hourglass neck with a 34.8 mm 6807 inner-ring journal, 37.5 mm upper shoulder, four-screw lower retainer, hidden transition into the visible 24 -> 15.5 -> 20 mm profile, and four-screw insert-backed yoke flange; keyed stationary outer-ring carrier; removable pan-servo plate; drawing-backed Hitec D85MG pan and tilt servos with R-ML24 horns; width-derived fixed internal tilt yoke; removable three-screw drive adapter; removable three-screw passive cartridge around an MF84ZZ flanged bearing and 4 mm shoulder screw; compact 72 x 140 x 72 mm rounded camera capsule with concealed bezel roots, recessed screw-on black faceplate, interior-relieved rear cover, widened camera-ribbon/neck notch, narrow vertical eyes/eyebrows, and a faceplate-integrated stepped camera annulus.
- Front sensor fascia clamped to four shell-rooted spacers by the same black-on-black screws that retain its LED carriers, with two central ToF apertures and four rear bosses for the front ToF pods.
- A 70 mm microphone-array retaining ring aligned under through-lid acoustic slots and four downward roof bosses.
- Two enclosed-speaker mounting plates using a 64 x 24 mm hole rectangle plus two independent shell fasteners per plate. Each plate also carries one component-side-down Adafruit #3006 MAX98357A on two 6 mm M2 metal standoffs, with the exact official PCB/two-hole pattern, an inward signal-header path, and outward/downward provisional terminal service keepouts.
- Four removable VL53L1X sensor frames: two front pods fastened to the fascia and two side pods fastened to shell bosses behind open shell/fairing sightlines.
- Official-pattern Camera Module 3 Wide carrier with blind shell posts and an open-bottom ribbon exit.
- Head eye apertures with 9 x 14 mm framed diffusers, larger stepped internal board pockets, and two side-fastened removable carriers for rotated Adafruit 5975 NeoPixel JST breakouts. Each board uses two M2 through-fasteners and 3 mm-OD spacers; the 90-degree board orientation sends both keyed plug paths vertically clear of the carrier screws and yoke.
- Removable 145 x 116 upper service deck with drawing-backed D24V90F5 Pi power, D36V50F6 servo power, Panasonic CB1A-R-M-12V relay interface, and complete Blue Sea Systems 5045 covered four-circuit ATO/ATC fuse block. The audio amplifiers live beneath their speaker plates, and an I2C mux is not frozen unless bench wiring proves XSHUT/address assignment insufficient.
- Two removable under-deck U-channel harness rails with four paired reusable-strap stations each; the left bundle is reserved for signal/audio/sensors and the right for fused switched power/motors.
- Cytron MDDS10 controller plate lifted 5 mm above the tray on four M3 metal spacers, with the official 95.25 x 60.96 mm board-hole pattern, four 6 mm M3 board standoffs, front terminal fan-out, 10 mm cooling keepout, and a stacked Raspberry Pi Pico 2 safety shelf on a separate four-standoff pattern that clears the maximum battery envelope. The Pico uses its official four-hole pattern and four 6 mm M2 standoffs, with front USB and rear SWD service corridors.
- Tray-to-deck metal standoff paths that run continuously from the base tray to the removable power deck.
- Top cable strain-relief plate with six tie points and two dedicated roof-boss fasteners.
- Removable 126 x 58 rear service frame over the reserved connector/switch bay, with three flush 30 x 30 mm cartridges. Rear-left charge uses a drawing-backed Switchcraft EN2P3M20 sealed three-contact inlet with exact 10.92 mm front opening, rear nut/body counterbore, and EN2C3F20G2 mating envelope; two contacts are charge +/- and the third is CHARGER_PRESENT. The center cartridge is blank with no jack, PCB, or wiring. Rear-right mute/status uses a drawing-backed E-Switch PVB3F230SS311 maintained SPDT switch with red ring, 16.0 mm / 14.6 mm-flat cutout, and a validated E-stop-clear terminal corridor. Each cartridge retains its stepped 26 x 18 mm tongue and two M2.5 frame screws.
- Through-lid speaker grilles and high side intake/exhaust slots.
- Review-only Raspberry Pi, battery, motors, controller, power, safety MCU, audio, ToF, future AI HAT clearance, and cable-corridor volumes.
- Eighteen concealed 4 mm alignment pilots across the shell, tray, and bumper backing plates, with half-round mating recesses, 0.3 mm radial clearance, 0.4 mm axial clearance, and at least 1.2 mm of remaining exterior shell wall.

## v1 envelope

All dimensions are millimetres. The current modeled body envelope is approximately:

| Item | Envelope |
| --- | ---: |
| Main body | 300 L x 220 W x 121 H |
| Bumper | 318 L x 238 W x 28 H; 302 x 222 rigid-chassis cavity |
| Wheel diameter | 86 |
| Wheel center height | 66 |
| Tire ground plane | Z=23 |
| Wheel side inset | 4 into the 220 mm body envelope |
| Minimum bumper ground clearance | 6 |
| Camera head | approximately 84 overall D including bezel/rear cover x 140 W x 72 H; structural shell depth 72 |
| Overall top height | about 278 |

The silhouette intentionally follows the supplied concept: cream appliance-like
body, inset darker teal lid, charcoal lower bumper, small inboard wheels, red
rear E-stop, and a compact friendly camera head.

## Fit-check assumptions

The board footprints now use the published Raspberry Pi reference dimensions,
while the surrounding clearance volumes remain conservative placeholders:

- Raspberry Pi 5 board reference: 85 x 56, with four mounting holes inset 3.5 mm from the board edges. See the [official Raspberry Pi 5 mechanical drawing](https://datasheets.raspberrypi.com/rpi5/raspberry-pi-5-mechanical-drawing.pdf).
- Raspberry Pi 5 fit clearance: 96 x 68 x 28, including cooling, connectors, and cable bend room.
- Camera Module 3 Wide reference: 25 x 23.862 PCB, four 2.2 mm holes on 21 x 12.5 mm spacing, a conservative 12.4 mm total depth, lens face 1 mm behind the faceplate front, and a conservative circular keepout using the 102-degree horizontal FOV. The faceplate-integrated annulus clears 13 mm at its front and the shell/faceplate bores clear 11.5 mm. See [Raspberry Pi drawing RP-008155-DS-1](https://pip-assets.raspberrypi.com/categories/1207-design-files/documents/RP-008155-DS-1-camera-module-3-wide-mechanical-drawing.pdf).
- ReSpeaker USB Mic Array reference: 70 mm diameter. See the [Seeed product brief](https://files.seeedstudio.com/wiki/ReSpeaker_Mic_Array_V2/res/ReSpeaker%20MicArray%20v2.0%20Product%20Brief.pdf).
- Enclosed speaker reference: 70 x 30 x 17, with a 64 x 24 mounting rectangle and 3.1 mm holes. See the [Adafruit speaker product](https://www.adafruit.com/product/1669).
- Stereo amplifier reference: two Adafruit #3006 MAX98357A mono I2S boards, each using the official 17.78 x 19.05 x 1.57 mm PCB datum, two 2.5 mm holes at X=2.54/15.24 and Y=16.51 mm, and four total 6 mm M2 standoffs beneath the speaker plates. Shared BCLK/LRCLK/DIN feeds both boards while SD/MODE selects left and right. The [official CAD folder](https://github.com/adafruit/Adafruit_CAD_Parts/tree/main/3006%20MAX98357) predates the current pre-soldered terminal block, so terminal, screwdriver, speaker-wire, and chosen header/direct-wire envelopes require one-board measurement.
- VL53L1X breakout reference: 25.5 x 17.5 x 4.6. See the [Adafruit sensor product](https://www.adafruit.com/product/3967).
- Battery prototype reference: Bioenno BLF-1203AB rotated flat to 110 x 75 x 27 in a 117 x 92 cradle with four support pads, two 20 mm straps, positive side/end locators, power-deck-standoff scallops, and a rear lead corridor. It remains a prototype candidate, not an unattended-use release.
- Cytron MDDS10 motor controller: official 101.092 x 66.802 mm STEP footprint, 1.57 mm PCB, 1.93 mm underside pin protrusion, 12.275 mm component height above the PCB datum, four 3 mm holes on 95.25 x 60.96 mm spacing, a 24 x 44 x 16 mm front terminal service corridor, and 10 mm reserved cooling volume below the safety shelf. See the [official Cytron MDDS10 page and CAD resource](https://th.cytron.io/p-10amp-7v-35v-smartdrive-dc-motor-driver-2-channels).
- Raspberry Pi Pico 2 safety MCU: official 51 x 21 x 1 board, 52.3 x 21 x 3.8 bare-board/USB STEP envelope, four 2.1 mm holes on 48.26 x 17.78 spacing, and a conservative 62 x 33 x 14 wired-header/cable keepout. See the [official Pico 2 datasheet](https://datasheets.raspberrypi.com/pico/pico-2-datasheet.pdf).
- Future AI HAT+ 2 clearance: 96 x 74 x 22 above the Pi region.
- E-stop reference: IDEC XW1E-BV402M-R, 40 mm operator, 2NC direct-opening contacts, 22.5 mm keyed panel opening, 37 mm rear body, 48.7 mm body depth, 20 mm terminal service reserve, 4 mm removable clamp panel, 40 mm pass-throughs in surrounding printed layers, 66 mm backing/panel flange, four cardinal M3 paths on a 28 mm radius, and a 60 mm yellow legend. See the [official IDEC product page](https://www.idec.com/en-us/switches-indicator-lights/switches-pushbuttons/emergency-stop-switches/xw-22mm-estop/xw1e-bv402m-r).
- Physical mute reference: E-Switch PVB3F230SS311 maintained SPDT On-On switch, red base-voltage LED ring, 16.0 mm panel opening with 14.6 mm flats, 18 mm bezel, 11.2 mm actuator, 26 mm rear body, and 1-7 mm panel range. It mounts in the rear-right 1.25 mm cartridge face because the center lane is occupied by the E-stop body. See the [official PVB3 drawing](https://www.e-switch.com/wp-content/uploads/2024/01/PVB3.pdf).
- Center-cartridge reference: blank 30 x 30 mm cap with the standard 26 x 18 mm tongue and two M2.5 frame screws. It contains no connector, PCB, wiring, or service-detect function. Internal service requires shutdown or physical motor-branch isolation.
- Bumper-switch reference: six Omron D2HW-C202MR sealed SPST-NC pin-plunger switches with an 18.5 x 6.5 x 5.3 mm mounting envelope, 13 mm M3 hole spacing, 7.2 mm maximum free position, 6.4 +/-0.2 mm operating position, and 5.1 mm maximum total-travel position. The 22 x 40 x 4 PETG plates reserve recessed switch screws, a side-lead corridor, a 0.4 mm rest gap, 2 mm nominal TPU displacement, and paired rigid stops at 2.4 mm. See the [official Omron D2HW datasheet](https://omronfs.omron.com/en_US/ecb/products/pdf/en-d2hw.pdf).
- Pan/tilt hardware reference: two Hitec D85MG 24T servos with 29 x 13 x 30 mm cases, 39.8 mm flanges, 30.8 mm mounting-hole spacing, and 7.8723 mm output offset; two Hitec R-ML24 aluminum horns with M2 x 0.4 stations at 13 and 16 mm; one MF84ZZ 4 x 8 x 3 mm flanged bearing with a 9.2 x 0.6 mm flange; and one McMaster 92981A143 4 x 12 mm shoulder screw with M3 x 4 mm thread. See the [official D85MG page](https://www.hiteccs.com/actuators/product-details/D85MG), [Hitec horn chart](https://shop.multiplex-rc.de/userdata/files/HITEC%20SERVO%20ACTUATOR%20HORN%20%26%20SPLINE%20TECHNICAL%20DATA%20SHEET_v3_0_1_26C.pdf), and [MF84ZZ data](https://www.smbbearings.com/firebrick/ckeditor/plugins/upload/Uploads/Documents/bearingpdfs/MF84ZZ-flanged-miniature-bearing-4x8x3mm.pdf).
- Neck interface: 53 mm body/lid opening; 60 mm visible stationary collar over a keyed 52.4 mm fixed outer-ring carrier; Koyo/JTEKT 6807-2RS bearing at 35 x 47 x 7 mm; rotating 34.8 mm journal, 37.5 mm upper inner-ring shoulder, and four-M2.5 lower retainer; hollow visible hourglass with a 20 mm clear waist; flat 13 x 1.5 mm cable passage beside the pan horn; and a 21.5 mm-radius top flange carrying four blind M2.5 insert pockets on an 18 mm radius. See [Koyo's 6807-2RS data](https://koyo.jtekt.co.jp/en/products/detail/?pno=6807+2RS).
- Rear gearmotor reference: Pololu #4867, 98.78:1, 79 rpm/0.10 A no-load and 1.8 A/11 kg-cm extrapolated stall at 12 V, 25 mm gearbox diameter, 68.45 mm face-to-encoder length, 4 x 12.5 mm D shaft, 7 x 2.5 mm boss, and two M3 face holes on 17 mm spacing. The matching #1569 bracket uses a 1.5 mm-thick 49 x 22 mm base; the #1997 hub is 19 x 5 mm with four M3 wheel holes on a 6.35 mm radius. See the [official motor page](https://www.pololu.com/product/4867), [motor drawing](https://www.pololu.com/file/0J1634/25d-metal-gearmotor-dimension-diagram.pdf), [bracket drawing](https://www.pololu.com/file/download/1569-bracket-dimensions.pdf?file_id=0J725), and [hub drawing](https://www.pololu.com/file/0J663/1997-4mm-m3-hub-dimensions.pdf).
- Front idler reference: two 608-class bearings per side at 8 mm bore x 22 mm OD x 7 mm width; one WDS 615-M6-8-65 shoulder bolt with 65 mm-long 8 mm shoulder and M6 threaded end; one M6 washer; one prevailing-torque M6 locknut; and stock goBILDA spacers/shim. Confirm purchased bearing and shoulder tolerances, spacer squareness, full thread engagement, retained prevailing torque, controlled axial play without preload, wheel alignment, and loaded skid-turn retention.
- Mobility stance reference: the 43 mm-radius tires are centered at Z=66 and Y=+/-118, placing their inner faces 4 mm inside the shell envelope and their tangent plane at Z=23. Each tire has 24 offset 5.5 mm-wide x 2 mm-deep transverse grooves across the center 20 mm, leaving both 2 mm sidewall bands and the 86 mm rolling envelope intact. The bumper begins at Z=29 for 6 mm static clearance. All four pod shells remain seated at Z=53 despite the lower axle, and the wheel-well, tread, tray-pad, pod, and bumper-relief contracts are validated from the same parameters.
- Bumper chassis reference: the TPU inner cavity follows the 300 x 220 mm cream shell with 1 mm nominal radial clearance per side and clears the 292 x 212 mm tray by 5 mm per side. The low bridges span inward beneath the tray, not through it. Any bumper/body or bumper/tray solid overlap is a validation failure.
- Side ToF reference: board/window center X=-20 between the wheel arches, with two shell-boss fasteners at X=-40 and open paths through the shell and removable fairing.
- Power deck reference: 145 x 116 plate on four metal standoffs; exact D24V90F5 and D36V50F6 M2 patterns/service corridors; Panasonic CB1A-R-M-12V 26 x 22 x 25 mm relay body, integral 52 x 22 x 0.8 mm bracket, one 5.4 mm mount, 6.3 mm terminals, and terminal-service volume; plus the complete Blue Sea 5045 92.5 x 43.8 x 32.5 mm covered block, two 4.5 mm deck paths on 65.1 mm centers, fuse-service reach, wire exit, and strain slots.
- Lifting reference: no integrated handle or custom load-bearing metal. Power down and lift with two hands under the tray.
- Harness reference: two 108 x 14 mm open-bottom rails under the power deck, each with a 7.6 x 5 mm conservative bundle corridor and four paired 10 x 3.5 mm strap slots. The rails sit tangent to, but do not consume, the battery and motor-cover envelopes; connector exits and actual bundle diameters remain unselected.

Before printing the chassis, confirm the delivered MDDS10, Pololu drivetrain,
both Pololu regulators, IDEC E-stop, Omron bumper switches, Panasonic relay,
Blue Sea fuse block, and WDS/goBILDA idler stack; physically qualify the selected
battery/charger/inlet and the camera, speaker, and microphone hardware.
The E-stop, battery retention, motor retention, and axle loads must use real
hardware and metal fasteners; printed plastic is only the supporting enclosure.
There is no carry interface: lift the unpowered robot with two hands under the tray.

## Assembly interfaces

1. Install M3 heat-set inserts into the four ribbed shell lugs at X +/-124 and Y +/-84.
2. Place the shell over the base tray; the shallow perimeter lip locates it before screws are installed.
3. Drive four M3 screws upward through the tray clearance holes into the shell inserts.
4. Confirm the tray contains no handle slots, webbing, or custom clamp plates. Keep clear two-hand access beneath the unpowered tray without using the shell or bumper as a lifting point.
5. Install four M3 inserts from below into the removable E-stop mount panel, pass the IDEC XW1E-BV402M-R through its keyed opening and durable 60 mm yellow legend, and tighten the purchased nut against only that 4 mm panel. Seat the panel into the lid recess, align the 40 mm body through the lid/shell/backing passage, and screw the raised-collar backing upward into the panel inserts. Perform this before the upper power deck limits screwdriver access.
6. Seat the BLF-1203AB cradle on the tray, install its four M3 screws, add nonconductive padding, route both 20 mm straps, and verify all four support pads plus side/end locators meet the rotated 110 x 75 x 27 mm pack without rocking or wrapper pinch. Route the separate Powerpole discharge and charge leads through the rear upper corridor without bending at the wrapper exit.
7. Install four 5 mm M3 metal spacers in the shared tray inserts, bolt on the locally notched controller plate, add four 6 mm M3 board standoffs, and mount the MDDS10 with its six high-current terminals facing robot-front. Confirm at least 3 mm clearance below the longest underside pin and preserve the front terminal fan-out.
8. Install four metal standoffs above the controller plate, bolt on the safety-MCU shelf, and verify the safety wiring remains independently serviceable.
9. Mount the D24V90F5 and D36V50F6 on their seven 6 mm M2 metal standoffs. Bolt the Panasonic CB1A-R-M-12V integral bracket through its single 5.4 mm deck path with retail metal hardware, leaving its 6.3 mm terminals and service envelope clear; the printed deck must not carry terminal loads. Bolt the complete covered Blue Sea 5045 through its two deck paths on 65.1 mm centers, protect the terminal side, and strain-relieve its wire exit. Route signal/audio/sensor wiring through the left harness rail and fused switched-power/motor wiring through the right, secure both rails and bundles to the deck through all four paired reusable-strap stations, then install the complete serviced deck on its four metal standoffs. Do not fit final ATO/ATC values until measured loads, conductor ampacity, time-current curves, and electrical review select them.
10. Bolt each #1569 bracket through three 3 mm metal spacers into the tray, fasten the #4867 motor to the bracket with its two M3 face screws, and route the six encoder leads into the assigned harness rail. Install the #1997 hub on the 4 mm D shaft with verified set-screw engagement, attach the PETG core with four M3 screws, seat the TPU tire and trim ring, then reinstall the inboard pod cover and pod fasteners.
11. Fit two 608 bearings into each removable idler pod and install both flush printed outer-race rings with four M2.5 screws per pod. Assemble the WDS 615-M6-8-65 shoulder bolt, stock goBILDA spacers/shim, bearings, M6 washer, and prevailing-torque locknut in the documented orientation. Verify the 65 mm shoulder supports both bearing inner races, the thread is fully engaged, the locknut retains prevailing torque, axial play is controlled without preload, and the wheel rotates freely with no plastic thread or friction fit carrying retention.
12. Install six Omron D2HW-C202MR switches on their rigid PETG plates, route each molded side lead through its tray corridor with strain relief, and fasten every plate upward into two blind tray inserts. With the TPU removed, verify NC continuity and service access. Fit the bumper without clamping it to those plates, then prove the 0.4 mm nominal rest gap, no preload, positive actuation by 2 mm, paired rigid-stop protection near 2.4 mm, rebound, and electrical opening from all six zones before connecting motor power.
13. Buy and measure one current Adafruit #3006 board. Install it component-side-down beneath one speaker plate using two 6 mm M2 metal standoffs, keep the seven-pin header/direct-wire side inward and speaker terminal outward, and prove screwdriver plus wire-bend access. After that fit passes, build the matching left/right pair, configure SD/MODE for separate channels, screw the microphone cradle into its 40 x 80 mm four-boss pattern, attach both populated speaker plates, mount the purchased speakers, and verify every grille path remains open.
14. Seat the dark vent inlay in its 1.4 mm lid recess and install its four M2.5 screws into the underside bosses; verify all nine 36 x 3 mm microphone slots remain open through the inlay, both lid halves, and shell.
15. Bolt one Adafruit 5975 board to each front LED carrier with two M2 screws, 3 mm-OD spacers, washers, and locknuts; connect and strain-relieve both JST-SH harnesses. Bolt the two front ToF pods to the fascia, seat the keyed fascia, clamp it through the shell spacers while installing the populated LED carriers with four shared black-on-black M2.5 screws, then fasten the two side pods before fitting the fairings.
16. After selecting the cooled 6807 coupon stations, press the bearing outer ring squarely into the keyed fixed carrier, pass the neck journal through the inner ring, seat the 37.5 mm upper shoulder, and install the four-M2.5 lower retainer without axial preload. Install the D85MG pan servo through its removable underside plate, connect the R-ML24 horn to the retainer at its 13/16 mm M2 stations, and verify the flat ribbon corridor remains free at both pan limits.
17. Seat the fixed tilt-yoke base on the hourglass neck's top flange and install four M2.5 screws into its blind insert pockets without pinching the central cable bundle. Install the second D85MG, fasten the active drive adapter to the right head bosses with three M2.5 screws, and connect its R-ML24 horn through the 13/16 mm M2 stations. Fasten the passive cartridge to the left bosses with three M2.5 screws, seat the MF84ZZ through the shell/cartridge, and install the 92981A143 shoulder screw into the yoke without axially clamping the moving head. Bolt the Camera Module 3 Wide to its carrier, route the ribbon through the 30 x 14 mm lower notch, then fit the faceplate and rear cover. Verify image quality and clear motion at center and every pan/tilt limit.
18. Screw the cable strain-relief plate into its two roof bosses. Install the EN2P3M20 in the rear-left charge cartridge with the purchased nut at 5-6 in-lb; wire two contacts only to the isolated Bioenno charge lead and the third to protected CHARGER_PRESENT logic that requests deterministic motion inhibit. Use the female EN2C3F20G2 on the charger adapter so energized contacts remain recessed, and mate/unmate only with charger AC removed. Install the PVB3F230SS311 in the rear-right mute cartridge and prove the maintained privacy path. Leave the center cartridge blank. Install six M2.5 frame inserts, fit all three cartridges with two screws each, and attach the frame with four outer M3 screws. Charger insertion must de-energize the Panasonic relay/motor enable and removal must require explicit reset.
19. After wiring the E-stop in the independent motor-power path, verify its nut cannot rotate, apply controlled push/twist loads, and prove it cuts motor power without the Pi.

For the 220 mm-bed split configuration:

1. Print and cycle-test the exact three-piece split-pilot coupon. The pilot must seat by hand without forcing, rocking, or splitting the 3.2 mm shell wall; adjust the shared clearance parameters before any large split part if it fails.
2. Heat-set the 44 provisional M3 inserts only after validating the insert coupon and soldering-iron temperature.
3. Join the shell's front/rear seams by seating the two end plates' four pilots in the shared half-round recesses, then install and tighten the eight screws evenly.
4. Seat the two side plates' four pilots and install the eight lower shell-seam screws; the scalloped fairing reliefs remain clear of this structural joint.
5. Seat the four fairing halves in their flush shell recesses and install their eight dedicated upper screws; each wheel-arch cap is independently removable. Reject binding, perimeter whitening, visible bowing, or an exterior edge proud of Y +/-110.
6. Seat the underside plate's two pilots across the base-tray seam, then install and tighten its eight screws evenly.
7. Verify the joined tray remains handle-free and that no obsolete carry slots, clamp plates, or M4 carry paths are present.
8. Seat the four bumper plates' eight pilots in the four quadrants, then install the eight screws before adding the six switch plates.
9. Capture the two 1 mm reveal/gasket halves, engage the lid's 12 mm stepped lap, and install the four lid screws into the supported roof bosses.

The 44-count covers split joinery only. It does not include electronics,
motor, E-stop, head-panel, or shell-to-tray fasteners. Screw lengths
remain provisional until the insert and wall-thickness coupons are measured.

The current collision audit places the Pi at front-left, the drawing-backed MDDS10 at
front-right centered at (-65, 33.5), the drawing-backed Pico 2 safety MCU
directly above the controller on its own shelf, and
the battery centered between the mobility-pod keepouts. The AI HAT clearance
is stacked above the Pi rather than occupying a second floor-plan region. The
power deck occupies a separate layer above the battery, with the E-stop column
and rear service bay kept clear.

## Generate and review

```bash
.venv-cad/bin/python cad/python/robot_body.py
.venv-cad/bin/python cad/python/robot_body_split.py --bed 256 --margin 8
.venv-cad/bin/python cad/python/validate_robot_body.py --bed 256 --margin 8
.venv-cad/bin/python cad/python/robot_body_print.py --bed 256 --margin 8
.venv-cad/bin/python cad/python/robot_body_coupons.py --bed 256 --margin 8
/Applications/Blender.app/Contents/MacOS/Blender -b --python cad/blender/render_robot_body.py
/Applications/Blender.app/Contents/MacOS/Blender -b --python cad/blender/render_print_ready.py
/Applications/Blender.app/Contents/MacOS/Blender -b --python cad/blender/render_coupons.py
/Applications/Blender.app/Contents/MacOS/Blender -b --python cad/blender/render_alignment_pilot.py
.venv-cad/bin/python cad/bambu/generate_bambu_project.py
```

The main body command currently exports 83 printable parts plus three
review-only hardware stand-ins and 177 fit envelopes; the validator audits all
86 main solids. The split command generates 57 printer-aware
variants and a manifest, including two halves for the thin reveal/gasket. With
the P1S 256 mm bed and 8 mm margin, the largest XY span is the 212 mm-wide
base-tray half.

The canonical print command replaces the seven oversized main parts with their
split equivalents and exports 101 uniquely named STLs under
`cad/exports/print_ready/`. It applies deliberate orthogonal rotations, centers
and grounds every part, checks that rotation preserved volume, requires at
least 50 mm^2 of sampled first-layer contact, and assigns prototype PETG, TPU,
or translucent-PETG profiles plus support guidance. The print manifest marks
hardware-dependent parts as prototype-only and includes the current fastener,
insert, standoff, and locknut interface counts; orientation validation is not
a release waiver. Use the actual printer's measured usable area before slicing,
especially if clips, brims, or bed-edge exclusion zones reduce the nominal
dimensions.

The settled production-layout target is a Bambu Lab P1S with the standard
0.4 mm nozzle and Textured PEI Plate. The canonical 101-part inventory is packed
onto 26 named plates across 14 material-profile/color groups, with each plate
containing only one group, in
`cad/bambu/codex_robot_body_v1_p1s.3mf`. The split geometry remains compatible
with the earlier 220 mm-bed contract; the P1S project uses an 8 mm edge reserve
and adds brim-aware spacing before Bambu Studio round-trip validation.

The coupon command exports seventeen small parts covering M3/M2.5 insert holes,
M3/M2.5 screw clearance, three 608 bearing seats, three 6807 outer-seat and
three 6807 rotating-journal stations on one block, three wall thicknesses, and
the actual production lid-lap pair, an exact three-piece shell pilot/recess
interface, an exact clipped tray/PETG-plate/TPU bumper-switch interface, an
exact two-piece flush-fairing recess interface, plus a legacy D023 gauge for the
rejected custom distribution PCB. The legacy gauge
validates 32 openings, six bearing shoulders, exact lid-lap reconstruction,
pilot fusion and recess clearance, bumper reconstruction/seating/rest-gap/
nominal-stroke behavior, fairing free insertion/backing-floor contact,
legacy distribution-gauge reconstruction,
grounding, contact area, and bed fit.
Use the measurement and selection protocol in [v2 Qualification Proofs](cad-proofs.md)
before changing shared parameters.

The validator checks that every main, fit, and split artifact is one valid
solid; that the molded shell retains at least a 10 mm visible top rollover and
full nominal roof material at three quiet probe locations; that each fairing
lands flush at the body-width datum, retains a printable clamp gap, and leaves
at least 0.8 mm of continuous shell backing; that large
electronics envelopes do not collide with each other or the motor-pod
keepouts; that all four tires meet one ground plane, the bumper keeps
at least 6 mm clearance, every other hard part stays above the ground datum,
the pod shells stay seated on the tray pads, and wheels clear the body, tray,
matching pods, fairings, and bumper; that the TPU carrier occupies zero shell
or tray volume and retains its nominal body clearance; that all six rigid switch plates seat
against the tray without touching the TPU, all 12 screw paths reach blind tray
inserts, all 12 D2HW mounting paths remain open, switch bodies and side leads
clear their tray pockets at rest, 2 mm local TPU displacement reaches the
worst-case operating position, and paired 2.4 mm stops prevent total travel; that
bumper-switch keepouts clear motors and wheels; that body-mounted fit volumes
remain inside the cavity; that both D85MG servos, both R-ML24 horns, the 6807
pan bearing stack, MF84ZZ passive bearing, shoulder screw,
shoulder-bolt, and cable envelopes clear their printed mounts; that six adapter
screw paths, two horn holes, and the passive pivot path remain open; that the
complete moving printed head clears the yoke and neck through its configured
+/-20-degree tilt and sampled +/-60-degree pan poses; and that every
oversized main part has a complete split inventory whose pieces stay within the
requested bed envelope. It also proves the lid lap/gasket reconstruct their
unsplit sources exactly, backing plates do not overlap their mating pieces, all
18 pilots are fused and clear their matching recess halves, at least 1.2 mm of
shell wall remains behind each body recess, and shared lid/fairing/seam screw
paths remain open. The head checks additionally
require at least 1 mm faceplate clearance inside the bezel, a visible recess,
and open paths through all four front and four rear panel screws.
The D024 validator contract additionally enforces the BOM coverage contract, official camera-carrier
hole paths, rear motor cavities, installation sweeps, service covers, and tray
screws, front bearing/shaft clearances,
all four mobility-pod seating and screw paths, battery/controller tray seating,
controller and safety-shelf standoff alignment, audio roof-boss fasteners,
front-fascia and ToF fasteners, cable-relief roof fasteners, continuous
tray-to-power-deck standoffs, open side-sensor sightlines,
rear-panel access, speaker outlets, side airflow, power-deck standoffs,
separated ToF sightlines, four LED light paths/carriers, absence of carry
hardware, the WDS shoulder-bolt idler stacks, blank center cartridge, Panasonic
relay, Blue Sea 5045, and the complete
E-stop keyed panel/body/barrel/terminal stack, four backing screws, both harness rails against the
battery, mobility pods, body, deck and future AI-HAT clearance, all sixteen
shared strap openings, the 102-degree camera FOV envelope, and all 177 fit-volume collisions.

Review images:

- [Assembled preview](images/codex_robot_body_v1_assembled.png)
- [Inset head bezel detail](images/codex_robot_body_v1_head_detail.png)
- [Retained head-tilt mechanism](images/codex_robot_body_v1_head_mechanism.png)
- [Exploded preview](images/codex_robot_body_v1_exploded.png)
- [Electronics fit preview](images/codex_robot_body_v1_electronics_fit.png)
- [Legacy split-tray carry interface, superseded by D024](images/codex_robot_body_v1_carry_interface.png)
- [Under-deck harness routing](images/codex_robot_body_v1_harness_routing.png)
- [Tray-fixed bumper-switch interface](images/codex_robot_body_v1_bumper_interface.png)
- [Printer-split joinery preview](images/codex_robot_body_v1_split_joinery.png)
- [Representative print-ready orientations](images/codex_robot_body_v1_print_ready.png)
- [Calibration coupon plate](images/codex_robot_body_v1_coupons.png)
- [Split-pilot coupon detail](images/codex_robot_body_v1_alignment_pilot.png)

The next physical validation step is the applicable coupon suite in
the intended PETG and slicer profile. After recording the selected dimensions,
print one shell backing plate, one bumper backing plate, the base seam, pan
plate, 6807 carrier/journal/retainer stack, tilt yoke, both tilt adapters, and motor service cover. Do not commit to a
full-size body until the interface coupons and representative service parts
pass. Do not print or use the legacy custom-distribution gauge as a release
gate. Verify the handle-free tray has safe two-hand access beneath it and label
the robot for unpowered two-hand lifting only.
Print the E-stop mount panel and backing ring first; then fit a purchased IDEC
XW1E-BV402M-R and verify the keyed opening, 4 mm clamp stack, nut engagement,
yellow legend, body passage, terminal access, wire bend, and controlled
push/twist loading before powering motors.
Print one harness rail before the full deck, load it with representative cable
and connector bundles, and confirm the reusable straps retain the wiring
without pinching insulation or forcing power and signal bundles together.
Print the faceplate before the complete head shell, install the real Camera
Module 3 Wide, and inspect full-resolution corner illumination, focus,
reflections, and ribbon behavior at the configured pan/tilt limits.
Fit the selected D85MG/R-ML24 hardware, MF84ZZ, and shoulder screw to the two
tilt adapters before printing the complete head. Select the 6807 seat and
journal from the cooled coupon, then assemble its carrier, neck, and retainer
without bearing preload. Confirm free rotation without sidewall rub, adapter
rocking, insert pullout, axial clamping, or cable pinch; measure current and
temperature, then cycle the loaded head through at least 500 supervised pan and
tilt reversals.
Print one switch plate plus the representative tray-pocket/TPU section and fit
a purchased D2HW-C202MR. Verify its mounting, molded lead, 0.4 mm gap, 2 mm
actuation point, paired 2.4 mm stops, force, hysteresis, and release point before
printing the complete bumper. The assembled
robot must stop motor power from every front, rear, and side zone, including a
broken/open switch circuit, before any autonomous movement.
