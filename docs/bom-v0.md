# BOM v0: Codex House Companion MVP

Date: 2026-07-06

This is the first-pass bill of materials for the non-AI-HAT MVP: a small indoor differential-drive companion body using the already-owned Raspberry Pi 5 8GB and a 3D printer. Prices are rough current USD ranges before tax and shipping. Check stock before ordering; robot parts have a majestic ability to go out of stock right after we become emotionally attached.

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
| Pan/tilt micro servos or small pan/tilt kit | 1 set | Buy after bench | $20-$60 | Start with simple hobby servos; upgrade if noisy or jittery. |
| 5V servo regulator or isolated servo rail | 1 | Buy after bench | $10-$30 | Keep servo noise away from Pi/audio power. |
| Printed camera head shell and brackets | 1 set | Consumable | See filament | Source CAD only. Generated STLs belong under ignored exports, not as source assumptions. |

## Audio

| Item | Qty | Status | Est. subtotal | Notes |
| --- | ---: | --- | ---: | --- |
| USB far-field mic array | 1 | Buy now | $50-$90 | USB keeps audio independent from Pi HAT stacking. Seeed listed ReSpeaker USB Mic Array at $69.99: https://www.seeedstudio.com/ReSpeaker-USB-Mic-Array-p-4247.html |
| I2S mono amp | 1 | Buy now | $6-$12 | Adafruit MAX98357A was listed at $5.95: https://www.adafruit.com/product/3006 |
| Enclosed 3W 4 ohm speaker or small speaker set | 1 | Buy now | $5-$20 | Adafruit's stereo enclosed 3W set was $7.50: https://www.adafruit.com/product/1669 |
| Speaker grille, gasket, acoustic foam | 1 set | Consumable | $5-$20 | Print the grille, tune the rattle. The robot deserves dignity in tiny audio. |

## Expression And Status

| Item | Qty | Status | Est. subtotal | Notes |
| --- | ---: | --- | ---: | --- |
| Addressable RGB LED ring/strip | 1-2 | Buy now | $10-$30 | Eyes/status: listening, muted, moving, error, low battery. |
| Physical mute switch | 1 | Buy now | $5-$20 | Should have a visible state and be readable by software. |
| Small buttons or service switch cluster | 1 set | Buy now | $5-$20 | Pairing, safe-enable, shutdown, mode/reset as needed. |

## Safety And Sensing

| Item | Qty | Status | Est. subtotal | Notes |
| --- | ---: | --- | ---: | --- |
| Raspberry Pi Pico 2 or Pico 2 W | 1 | Buy now | $5-$10 | Safety MCU for watchdog, bumper inputs, motor enable, and heartbeat. Raspberry Pi lists Pico 2 from $5: https://www.raspberrypi.com/products/raspberry-pi-pico-2/ |
| Latching mushroom E-stop | 1 | Buy now | $10-$25 | Must cut motor power path, not just ask Linux politely. |
| Motor power cutoff relay, contactor, or MOSFET switch | 1 | Buy now | $15-$50 | Rated for the motor battery voltage/current. Choose after battery and motor driver are final. |
| Inline fuse holders, fuses, XT60 or equivalent connectors | 1 set | Buy now | $20-$60 | Put the smoke back where it belongs: not in the robot. |
| Bumper microswitches or tactile bumper switches | 6-10 | Buy now | $10-$30 | Front and side bumper segments. |
| VL53L1X ToF distance sensors | 4-6 | Buy now | $60-$100 | Front, front-left, front-right, and side coverage. Adafruit lists VL53L1X boards at $14.95 each: https://www.adafruit.com/product/3967 |
| Qwiic/STEMMA QT cables and I2C mux if needed | 1 set | Buy now | $10-$35 | Multiple same-address sensors may need a mux or switched enable lines. |
| Optional cliff/drop sensors | 2-4 | Optional later | $10-$40 | Add if there are stairs, thresholds, or ledges in the operating area. |

## Mobility

| Item | Qty | Status | Est. subtotal | Notes |
| --- | ---: | --- | ---: | --- |
| 12V encoder gearmotors, 25D or 37D class | 2 | Buy after bench | $80-$180 | Pick ratio after target weight is known. Pololu 25D gearmotors are well documented; cheaper encoder motors exist but may cost debugging time. |
| Differential-drive wheels | 2 | Buy after bench | $15-$50 | Aim for rubber tread, about 65-90 mm diameter. |
| Passive caster or ball transfer units | 1-2 | Buy after bench | $10-$35 | Use placement that keeps weight on drive wheels. |
| Motor mounts, hubs, couplers | 1 set | Buy after bench | $20-$80 | Some can be printed, but shafts/hubs should be real hardware. |
| Cytron MDDS10 dual motor driver | 1 | Buy after bench | $55-$70 | Good default for two brushed DC motors. RobotShop listed MDDS10 at $55: https://www.robotshop.com/products/cytron-smartdriveduo-smart-dual-channel-10a-motor-driver |
| Pololu Dual G2 24v14 or similar driver | 1 | Optional alternative | $80-$110 | Pololu listed Dual G2 24v14 at $79.95: https://www.pololu.com/product/2516 |

## Mobile Power

| Item | Qty | Status | Est. subtotal | Notes |
| --- | ---: | --- | ---: | --- |
| 12V class LiFePO4 or Li-ion pack, 5-10Ah | 1 | Buy after bench | $60-$160 | Prefer a protected pack with BMS. LiFePO4 is calmer for indoor use; Li-ion is compact. |
| Compatible charger | 1 | Buy after bench | $25-$70 | Must match chemistry and cell count. Label it clearly. |
| 5V high-current buck regulator for Pi | 1 | Buy after bench | $30-$45 | Pololu D24V90F5 5V/9A was listed at $36.82: https://www.pololu.com/product/2866 |
| Secondary 5V/6V regulator for servos/LEDs | 1 | Buy after bench | $10-$35 | Keeps motor/servo noise from browning out the Pi. |
| Power distribution board or terminal blocks | 1 set | Buy after bench | $15-$50 | Include strain relief and service labels. |
| Main power switch/key/link | 1 | Buy after bench | $10-$35 | Separate from E-stop; E-stop is for immediate motor cut. |
| Battery strap, cradle, insulation, cable guards | 1 set | Consumable | $10-$40 | Print the cradle, use real straps and padding. |

## Printable Body And Hardware

| Item | Qty | Status | Est. subtotal | Notes |
| --- | ---: | --- | ---: | --- |
| PETG filament | 1-2 kg | Consumable | $25-$60 | Main chassis, trays, mounts, service panels. |
| PLA filament | 1 kg | Consumable | $15-$30 | Fast fit-check prints before PETG. |
| TPU filament or foam/rubber bumper material | 1 | Consumable | $20-$50 | Soft bumper carrier and impact padding. |
| Heat-set threaded inserts, M2.5/M3/M4 | 1 kit | Buy now | $15-$40 | Needed for serviceable printed parts. |
| Metric screw/standoff/washer assortment | 1 kit | Buy now | $25-$80 | M2.5/M3/M4. Do not rely on self-tapping into plastic for service parts. |
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
| Pico 2 or Pico 2 W, headers, prototyping board | $10-$30 |
| E-stop, fuse holders, switches, wiring, connectors | $50-$140 |
| 4x ToF sensors plus cables | $60-$90 |
| LEDs and physical mute switch | $20-$50 |
| PETG/PLA, inserts, M3 screw/standoff kit | $65-$170 |
| First batch estimate | $350-$800 |

## Defer Until Bench Tests Pass

- Drive motors, wheels, hubs, and motor mounts.
- Motor driver.
- Mobile battery, charger, and mobile power distribution.
- Pan/tilt servos if the first camera head can be static for bench testing.
- 2D LiDAR.
- AI HAT+ 2.
- Charging dock hardware.

## Open Decisions Before Mobility Purchase

1. Target loaded weight after bench hardware and printed tray are real, not vibes.
2. Wheel diameter and axle height that clear common rugs/thresholds without making the robot tall.
3. Motor ratio: slower and torquier is friendlier indoors; 0.35 m/s max means we do not need tiny race-car energy.
4. Battery chemistry and pack format: LiFePO4 for safety and cycle life, Li-ion for compactness, RC LiPo only if we commit to careful charging/storage practices.
5. Whether the first rolling chassis needs 2D LiDAR from day one or only a reserved top mount.

## Notes

- Generated CAD/STL/STEP exports should stay out of source control unless there is a deliberate release artifact. The source of truth should be OpenSCAD, build123d, or CadQuery files.
- The physical E-stop should cut motor power independent of the Pi. The Pi can know about the stop, but it should not be responsible for obeying it.
- If AI HAT+ 2 remains a plausible future upgrade, avoid making official M.2/NVMe storage part of the baseline; start with reliable microSD so the Pi 5 PCIe connector remains available.
- Leave expansion volume and power budget for AI HAT+ 2, LiDAR, and a charging dock, but do not let optional future magic block the first safe moving body.
