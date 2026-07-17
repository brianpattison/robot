# BOM v0: Codex House Companion MVP

Date: 2026-07-06

This is the first-pass bill of materials for the non-AI-HAT MVP: a small indoor differential-drive companion body using the already-owned Raspberry Pi 5 8GB and a 3D printer. Prices are rough current USD ranges before tax and shipping. Check stock before ordering; robot parts have a majestic ability to go out of stock right after we become emotionally attached.

## Retail Sourcing Rule

Production hardware must be purchasable in quantity one through a normal US
online checkout. Mainstream specialist retailers such as DigiKey, Mouser,
Pololu, Adafruit, SparkFun, McMaster-Carr, and established US marine/automotive
stores count. RFQ-only components, overseas-only sources, factory minimums,
custom-machined metal, custom sheet metal, and custom-fabricated PCBs do not.
Printed parts and wiring harnesses assembled from retail components are expected.
See [`retail-sourcing-policy.md`](retail-sourcing-policy.md) for the live audit.

## Cost Summary

| Scope | Incremental estimate | Notes |
| --- | ---: | --- |
| Already owned baseline | $0 | Raspberry Pi 5 8GB and 3D printer are treated as owned. |
| Bench brain and voice/vision | $165-$355 | Camera, mic, speaker, Pi cooling/storage/power if missing. |
| Safety and short-range sensing | $115-$260 | Safety MCU, E-stop path, bumpers, ToF sensors, wiring. |
| Mobility and mobile power | $335-$760 | Motors, wheels, motor driver, battery, charger, regulators, distribution. |
| Printable body supplies and hardware | $100-$260 | Filament, inserts, screws, standoffs, casters, bumper material. |
| MVP subtotal, no 2D LiDAR | $715-$1,635 | A practical target budget is about $1,200-$1,400. |
| Optional 2D LiDAR upgrade | +$100-$150 | Reserve mechanical and power space, but do not buy first. |
| Optional AI HAT+ 2 upgrade | +$200 | Deferred; not required for MVP responsiveness. |

## Status Legend

- Owned: already available, no incremental spend assumed.
- Buy now: needed for the first useful MVP path.
- Buy after bench: needed for rolling chassis, but can wait until voice/vision and safety bench tests are underway.
- Optional later: reserve space/interfaces, but defer purchase.
- Consumable: buy as needed and expect iteration.

## Core Compute

| Item | Qty | Status | Est. subtotal | Notes |
| --- | ---: | --- | ---: | --- |
| Raspberry Pi 5 8GB | 1 | Owned | $0 | Main computer. Replacement pricing is volatile, but this is not an MVP purchase. |
| Raspberry Pi 27W USB-C power supply | 1 | Buy now if missing | $14-$20 | Useful for bench work even if mobile power comes later. Adafruit listed the official 5.1V/5A supply at $14.04: https://www.adafruit.com/product/5814 |
| Raspberry Pi 5 active cooler | 1 | Buy now if missing | $5-$15 | Sustained audio, camera, and ROS services need boring thermal stability. Boring is beautiful. |
| Reliable microSD card | 1 | Buy now if missing | $15-$40 | MVP storage baseline. Use a reputable high-endurance or application-class card. Leaves the Pi 5 PCIe connector free. |
| Short camera cable and service cables | 1 set | Buy now | $10-$25 | Pi 5 camera connector/cable details matter for the head layout. |

## Vision And Head

| Item | Qty | Status | Est. subtotal | Notes |
| --- | ---: | --- | ---: | --- |
| Raspberry Pi Camera Module 3 Wide | 1 | Buy now | $35-$45 | Wide FOV helps indoor interaction. Raspberry Pi lists Camera Module 3 from $25 and describes the Wide variant as 120 degree FOV: https://www.raspberrypi.com/products/camera-module-3/ |
| Hitec D85MG 24T digital metal-gear servo | 2 | Selected; buy after static-head bench | $100-$160 | Drawing-backed pan/tilt baseline: 29 x 13 x 30 mm, 4.3 kg-cm stall torque and 1.4 A stall current at 6 V. Use the programmed motion limits and never treat stall torque as an operating target: https://www.hiteccs.com/actuators/product-details/D85MG |
| Hitec R-ML24 24T aluminum horn | 2 | Selected; buy with servos | $20-$45 | Uses the modeled M2 x 0.4 stations at 13 and 16 mm. Confirm the delivered spline and center-screw hardware against the servo before assembly. |
| Koyo/JTEKT 6807-2RS bearing | 1 | Selected; buy before neck print | $15-$35 | 35 x 47 x 7 mm pan support bearing; print the combined seat/journal coupon and press only the race being fitted: https://koyo.jtekt.co.jp/en/products/detail/?pno=6807+2RS |
| MF84ZZ flanged bearing | 1 | Selected; buy with servos | $5-$15 | 4 x 8 x 3 mm with 9.2 x 0.6 mm flange for the passive tilt cartridge. |
| McMaster 92981A143 shoulder screw | 1 | Selected; buy with servos | $10-$25 | 4 x 12 mm shoulder with M3 x 4 mm thread; fixes into the yoke without clamping the moving head. |
| Pololu D36V50F6 6 V regulator | 1 | Selected for CAD; buy after bench | $35-$45 | Drawing-backed 25.4 mm square board on three M2 standoffs for the separate head-servo rail. Both D85MGs can demand 2.8 A combined at published stall; verify actual 12 V-input current capability, transient margin, local capacitance, heat, and wiring. [Official product](https://www.pololu.com/product/4092). |
| Printed camera head shell and brackets | 1 set | Consumable | See filament | Source CAD only. Generated STLs belong under ignored exports, not as source assumptions. |

## Audio

| Item | Qty | Status | Est. subtotal | Notes |
| --- | ---: | --- | ---: | --- |
| USB far-field mic array | 1 | Buy now | $50-$90 | USB keeps audio independent from Pi HAT stacking. Seeed listed ReSpeaker USB Mic Array at $69.99: https://www.seeedstudio.com/ReSpeaker-USB-Mic-Array-p-4247.html |
| Adafruit #3006 MAX98357A I2S mono amp | 2 | Buy one for current-revision fit test | $12-$24 | One board per left/right speaker. Both share BCLK/LRCLK/DIN; configure SD/MODE for separate channels. The exact PCB/two-hole pattern is modeled under each speaker plate, but Adafruit's official 2022 STEP predates the terminal block now shipped pre-soldered. Measure one current board before buying/releasing both: https://www.adafruit.com/product/3006 |
| Enclosed 3W 4 ohm speaker or small speaker set | 1 | Buy now | $5-$20 | Adafruit's stereo enclosed 3W set was $7.50: https://www.adafruit.com/product/1669 |
| Speaker grille, gasket, acoustic foam | 1 set | Consumable | $5-$20 | Print the grille, tune the rattle. The robot deserves dignity in tiny audio. |

## Expression And Status

| Item | Qty | Status | Est. subtotal | Notes |
| --- | ---: | --- | ---: | --- |
| Adafruit 5975 NeoPixel JST breakout | 4 | Buy one for fit test | $6-$20 incl. cables | One RGB pixel per eye/status diffuser; M2 mounting and keyed JST-SH input/output. Four-board worst-case allowance is 240 mA at 5 V before software brightness limiting. |
| E-Switch PVB3F230SS311 physical mute switch | 1 | Selected; buy for rear-cartridge fit | $12-$25 | Maintained SPDT with red LED ring, 16 mm two-flat panel cutout, and 1-7 mm panel range. The right rear cartridge is modeled. Route fused microphone 5 V either to mic VBUS or to the muted indication/protected state-input branch; verify LED resistor, polarity, no USB backfeed, and true capture loss: https://www.e-switch.com/wp-content/uploads/2024/01/PVB3.pdf |
| Center rear cartridge | 1 blank printed cartridge | Implemented; no electrical hardware | Filament | D024 rejects the former Switchcraft jack/custom UART PCB. Keep the center cartridge blank. Use internal service access only after shutdown or physical motor-branch isolation. |
| Optional E-Switch PVPB3WS3 socket harness | 1 | Optional for serviceability | $8-$20 | Matching SPDT/LED socket with 140 mm 22 AWG leads. Measure its rear depth and prove latch/removal clearance before replacing the modeled solder-lug service corridor. |
| Small buttons or service switch cluster | 1 set | Buy now | $5-$20 | Pairing, safe-enable, shutdown, mode/reset as needed. |

## Safety And Sensing

| Item | Qty | Status | Est. subtotal | Notes |
| --- | ---: | --- | ---: | --- |
| Raspberry Pi Pico 2, non-W without headers | 1 | Buy now | $5-$10 | Drawing-backed safety-MCU baseline for watchdog, bumper inputs, motor enable, and heartbeat. Use wired USB/UART/GPIO links rather than giving the independent safety path an unnecessary radio. Raspberry Pi lists Pico 2 from $5: https://www.raspberrypi.com/products/raspberry-pi-pico-2/ |
| IDEC XW1E-BV402M-R E-stop | 1 | Buy now | $60-$85 | Selected drawing-backed 40 mm red mushroom with 2NC direct-opening contacts. Use its contacts in low-voltage cutoff/enable channels rather than carrying motor current; add a durable 60 mm yellow legend. [Official IDEC product](https://www.idec.com/en-us/switches-indicator-lights/switches-pushbuttons/emergency-stop-switches/xw-22mm-estop/xw1e-bv402m-r). |
| Panasonic CB1A-R-M-12V motor-cut relay | 1 | Implemented mechanical baseline; buy one for fit/electrical test | $15-$35 | Sealed SPST-NO automotive relay with integral bracket and one 5.4 mm mounting hole; rated 40 A at 14 V with a 12 V/134 mA coil and built-in resistor. Verify exact delivered identity, 6.3 mm terminals, conductor/terminal sizing, strain relief, driver, suppression interpretation, dropout, temperature, contact fault behavior, and fail-stopped E-stop operation before powered motion. |
| Inline fuse holders, fuses, XT60 or equivalent connectors | 1 set | Buy now | $20-$60 | Put the smoke back where it belongs: not in the robot. |
| Omron D2HW-C202MR bumper switches | 6 | Buy two first | $35-$75 | Selected sealed SPST-NC pin-plunger switch with molded right-side leads and M3 mounting. Qualify two in the exact 0.4/2.0/2.4 mm coupon interface before buying all six. [Official Omron datasheet](https://omronfs.omron.com/en_US/ecb/products/pdf/en-d2hw.pdf). |
| VL53L1X ToF distance sensors | 4-6 | Buy now | $60-$100 | Front, front-left, front-right, and side coverage. Adafruit lists VL53L1X boards at $14.95 each: https://www.adafruit.com/product/3967 |
| Qwiic/STEMMA QT cables and I2C mux if needed | 1 set | Buy now | $10-$35 | Multiple same-address sensors may need a mux or switched enable lines. |
| Optional cliff/drop sensors | 2-4 | Optional later | $10-$40 | Add if there are stairs, thresholds, or ledges in the operating area. |

## Mobility

| Item | Qty | Status | Est. subtotal | Notes |
| --- | ---: | --- | ---: | --- |
| Pololu #4867 99:1 Metal Gearmotor 25Dx69L MP 12V with 48 CPR encoder | 2 | Selected; buy for bench | $80-$180 | Drawing-backed rear-drive baseline: 98.78:1, 79 rpm/0.10 A no-load and 1.8 A/11 kg-cm extrapolated stall at 12 V, 4 mm D shaft, and 200 mm six-wire leads. The package matches the prior #4847 CAD while materially reducing battery demand. Target <=0.45 A steady per motor on intended surfaces and verify loaded torque/current/temperature: https://www.pololu.com/product/4867 |
| Pololu #1569 metal bracket for 25D gearmotor | 2 | Selected; buy with motors | $10-$25 | Primary motor retention; three M3 tray paths per bracket use 3 mm metal spacers. Drawing: https://www.pololu.com/file/download/1569-bracket-dimensions.pdf?file_id=0J725 |
| Pololu #1997 universal aluminum hub for 4 mm shaft, M3 holes | 2 | Selected; buy with motors | $15-$30 | Couples each 4 mm D shaft to the four-screw printed PETG wheel core. Confirm set-screw engagement and use thread-locking practice appropriate to the hardware: https://www.pololu.com/product/1997 |
| Printed 86 mm rear wheel stack | 2 | Prototype after coupons | Filament | Annular TPU tire, PETG structural core/flange, and teal trim ring; loaded retention and floor tests required. |
| 608 bearings | 4 | Buy after bearing coupon | $10-$30 | Two per removable front-idler pod; 8 x 22 x 7 mm. Cool and measure the coupon before selecting the seat station. |
| WDS 615-M6-8-65 shoulder bolt | 2 | Implemented front-idler axle; buy for fit test | $20-$50 | Quantity-one retail 8 mm x 65 mm shoulder with M6 threaded end. The purchased metal shoulder carries both 608 bearings; no machined groove or plastic thread provides retention. |
| M6 washer and prevailing-torque locknut | 2 sets | Buy with shoulder bolts | $5-$15 | Positive outboard metal retention. Verify full thread engagement, prevailing torque after repeated service, and no bearing preload. |
| Stock goBILDA spacers and shim | 2 axle sets | Implemented stack; buy for fit test | $10-$30 | Use unmodified catalog spacers/shim to establish the axial stack. Confirm actual lengths, squareness, wheel alignment, free rotation, and controlled axial play. |
| Cytron MDDS10 dual motor driver | 1 | Buy after bench | $55-$70 | Drawing-backed CAD baseline for two brushed DC motors: official 101.092 x 66.802 mm STEP footprint and four-hole mount are modeled with terminal, cooling, and service clearance. Cytron specifies 7-35 V, 10 A continuous per channel, and no reverse-polarity protection: https://th.cytron.io/p-10amp-7v-35v-smartdrive-dc-motor-driver-2-channels |
| Pololu Dual G2 24v14 or similar driver | 1 | Optional alternative | $80-$110 | Pololu listed Dual G2 24v14 at $79.95: https://www.pololu.com/product/2516 |

## Mobile Power

| Item | Qty | Status | Est. subtotal | Notes |
| --- | ---: | --- | ---: | --- |
| Bioenno BLF-1203AB 12 V/3 Ah LiFePO4 pack | 1 | Prototype baseline; buy one for fit/current test | $50-$80 | Official 110 x 27 x 75 mm pack is modeled rotated to 110 x 75 x 27 mm. Bioenno documents 7 A continuous, 14 A for two seconds, internal PCM/BMS protection, Powerpole discharge, separate DC charge lead, MSDS, and UN38.3 transport evidence. Require delivered lead fit, product-safety evidence beyond UN38.3, <=5.6 A sustained measured current, BMS/regen/thermal tests, and 45-minute runtime with 20% reserve: https://www.bioennopower.com/products/12v-3ah-lifepo4-battery-pvc |
| Bioenno BPC-1502DC charger | 1 | Prototype baseline; buy with battery | $25-$50 | Manufacturer-matched 14.6 V/2 A LiFePO4 charger. Adapt its center-positive 5.5 x 2.1 mm output to the dedicated keyed EN2 cord connector; do not expose a generic barrel jack on the robot: https://www.bioennopower.com/products/lithium-12v-2a-amp-lifepo4-battery-charger |
| Switchcraft EN2P3M20 + EN2C3F20G2 charge connector pair | 1 pair | Prototype baseline; buy for rear-cartridge fit | $20-$45 | Sealed, keyed, bayonet-locking, UL/CSA-listed three-contact pair rated 6.5 A. Two contacts are charge +/-; the third is CHARGER_PRESENT. Charge-only, never a battery output. Switchcraft marks it not for current interruption, so mate/unmate only with charger AC removed. [Panel connector](https://www.switchcraft.com/en2-panel-connector-3-position-20-male-pins-20-contact-size/en2p3m20/), [cord connector](https://www.switchcraft.com/en2-cord-connector-3-position-20-female-sockets-20-contact-size-0-140-0-180-3-6-4-6mm-grommet-ribbed-coupling-ring/en2c3f20g2/). |
| Pololu D24V90F5 5 V regulator for Pi | 1 | Selected for CAD; buy after bench | $30-$45 | Drawing-backed 40.6 x 20.3 mm board on four M2 standoffs with both terminal corridors modeled. Verify Pi 5 startup/USB load, voltage drop, thermals, fusing, and power-good behavior. [Official product](https://www.pololu.com/product/2866). |
| Pololu D36V50F6 6 V regulator for servos | 1 | See selected head rail above | $35-$45 | Keep it electrically separate from the Pi rail and validate measured dual-D85MG transients. |
| Blue Sea Systems 5045 covered four-circuit ATO/ATC fuse block | 1 | Implemented accessory-distribution baseline; buy one for fit/electrical test | $35-$60 | Complete retail assembly with cover and labels, modeled at 92.5 x 43.8 x 32.5 mm with two mounting holes on 65.1 mm centers. Preserve the conservative 6 A total / 5 A any-branch ceilings, battery-near feeder fuse, measured-load fuse selection, terminal protection, strain relief, labels, selective-fault tests, thermal testing, and separation from the independently relay-cut motor branch. |
| Main power switch/key/link | 1 | Buy after bench | $10-$35 | Separate from E-stop; E-stop is for immediate motor cut. |
| Battery strap, cradle, insulation, cable guards | 1 set | Consumable | $10-$40 | Print the cradle, use real straps and padding. |

## Printable Body And Hardware

| Item | Qty | Status | Est. subtotal | Notes |
| --- | ---: | --- | ---: | --- |
| White PETG filament | 1 kg | v2 prototype baseline (D034) | $20-$35 | Tray, structural lid, deck/tower/clamps, neck/collar, plus automatic shell/head fallback while their exact PLA gates remain open. Confirm the slicer estimate before buying. |
| Black PETG filament | 0.5 kg | v2 prototype baseline (D034) | $15-$30 | Wheels, pods, washers, pan plate, yoke, and tilt bushing: every motion/wear part. |
| Red PETG filament | Small spool | v2 prototype baseline (D034) | $15-$30 | Battery, Pico, and motor retainers. Red is a service convention, not a safety label substitute. |
| Visible PLA / PLA+ | Existing collection or small spools | Prototype; exact-family coupons required | $0-$30 | Dark fascia/rear/head panels and optional teal lid skin. Standard or credible PLA+ may enter the shell/head qualification path; effect PLAs stay cosmetic-only by default. |
| Translucent PLA | Smallest available spool | Prototype optical gate open | $15-$30 | Eye and status diffusers after brightness, hot-spot, camera-flare, clip, and LED-temperature checks. |
| Charcoal TPU 95A | 0.5 kg | v2 prototype baseline | $20-$50 | Tires, front/rear bumper halves, and battery pad frame. |
| M3 x 5.7 x 4.6 OD heat-set inserts, 100-pack | 1 | Buy now (v2 baseline, D026) | $12-$20 | The ONLY insert SKU in the v2 printed-only body (41 used + spares). Supersedes the old M2.5/M3/M4 kit. |
| M3 x 8 socket head cap screws (ISO 4762), 100-pack | 1 | Buy now (v2 baseline, D026) | $8-$15 | The ONLY separately purchased screw SKU (41 used + spares); one 2.5 mm hex key drives the robot. Supersedes the old multi-size assortment and all metal standoffs/spacers. |
| Cable glands, zip ties, ferrules, heat-shrink | 1 set | Buy now | $15-$50 | Cable management is robot hygiene. |
| Rubber feet/pads and anti-vibration tape | 1 set | Buy now | $5-$25 | Useful for audio and electronics isolation. |

## Optional Later

| Item | Est. subtotal | Why defer |
| --- | ---: | --- |
| Raspberry Pi AI HAT+ 2 | $200 | Useful for local LLM/VLM experiments, but MVP uses cloud/high-level Codex plus local deterministic reflexes. |
| USB 3 SSD or compact USB 3 flash drive | $25-$120 | Easy later upgrade for logs, captures, maps, models, `/data`, or boot storage if microSD becomes limiting. Mount in a printed cradle with cable strain relief. |
| Official M.2/NVMe HAT storage | $25-$100+ | Defer if AI HAT+ 2 remains a likely future upgrade; both official paths compete for the Pi 5 PCIe connector. Use microSD or USB SSD first. |
| Raspberry Pi SSD Kit | $70-$120+ | Official, tidy NVMe route, but it uses the M.2 HAT+/PCIe path and therefore conflicts with a clean future AI HAT+ 2 plan. |
| 2D LiDAR, e.g. Slamtec RPLIDAR A1 | $100-$150 | Strong upgrade for mapping/navigation. Adafruit listed RPLIDAR A1 at $99.95: https://www.adafruit.com/product/4010 |
| Depth camera or OAK-style vision module | $150-$300 | Useful if monocular tracking is weak, but not first purchase. |
| Charging dock hardware | $50-$200 | Manual charging is acceptable for MVP. Reserve base geometry for future contacts. |
| Better motor controller with encoder PID onboard | $100-$200 | Consider if Pi/Pico encoder handling becomes fussy. |
| Second camera or rear camera | $25-$80 | Add only after main interaction loop works. |
| Better battery telemetry coulomb counter | $20-$80 | Nice for runtime estimates; voltage-only is enough for first safety cutoff. |

## Recommended First Purchase Batch

Buy the bench-brain and safety-prototype parts first. This gets the robot hearing, seeing, speaking, and proving its stop paths before we buy heavy motion hardware.

| Batch item | Est. subtotal |
| --- | ---: |
| Camera Module 3 Wide plus cable | $45-$70 |
| USB mic array | $50-$90 |
| I2S amp, speaker, audio wiring | $15-$45 |
| Pi active cooler, bench power, storage if missing | $35-$115 |
| Non-wireless Pico 2 without headers, four 6 mm M2 standoffs, and wired harness/prototyping board | $10-$30 |
| E-stop, fuse holders, switches, wiring, connectors | $50-$140 |
| 4x ToF sensors plus cables | $60-$90 |
| LEDs and physical mute switch | $20-$50 |
| PETG/PLA, inserts, M3 screw/standoff kit | $65-$170 |
| First batch estimate | $350-$800 |

## Defer Full Mobility Purchase Until Bench Tests Pass

- Buy only one BLF-1203AB/charger/EN2 set and one #4867 motor first; do not order the full mobility set until fit/current tests pass.
- Remaining drive motor, wheels, hubs, and motor mounts.
- Motor driver.
- Final mobile power distribution and released wiring kit.
- Pan/tilt servos if the first camera head can be static for bench testing.
- 2D LiDAR.
- AI HAT+ 2.
- Charging dock hardware.

## Open Decisions Before Mobility Purchase

1. Target loaded weight after bench hardware and printed tray are real, not vibes.
2. Wheel diameter and axle height that clear common rugs/thresholds without making the robot tall.
3. Whether the #4867 pair meets rug/threshold and carpet skid-turn requirements at <=0.45 A steady per motor with measured loaded mass.
4. Whether the BLF-1203AB completes the 45-minute mixed-use test with 20% measured energy reserve and <=5.6 A sustained pack current; otherwise revisit the larger BLF-1206A and body-height trade.
5. Whether the first rolling chassis needs 2D LiDAR from day one or only a reserved top mount.

## Notes

- Generated CAD/STL/STEP exports should stay out of source control unless there is a deliberate release artifact. The source of truth should be OpenSCAD, build123d, or CadQuery files.
- The physical E-stop should cut motor power independent of the Pi. The Pi can know about the stop, but it should not be responsible for obeying it.
- If AI HAT+ 2 remains a plausible future upgrade, avoid making official M.2/NVMe storage part of the baseline; start with reliable microSD so the Pi 5 PCIe connector remains available.
- Leave expansion volume and power budget for AI HAT+ 2, LiDAR, and a charging dock, but do not let optional future magic block the first safe moving body.
