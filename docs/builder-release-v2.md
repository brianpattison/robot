# Rover Bean Builder Release — v2.0.0-prototype.1

Permanent source: [https://github.com/brianpattison/robot/tree/v2.0.0-prototype.1](https://github.com/brianpattison/robot/tree/v2.0.0-prototype.1)

## Verdict

This is a **prototype geometry, dry-assembly, and bench-software release**. It is
not authorization for powered motion and it is not a complete retail kit. The
tracked body/head geometry and hardware-free tests pass; every delivered-part,
electrical, loaded-motion, and commissioning result remains specific to the
physical first article.

## One-version artifact map

| Artifact | Path | Release meaning |
| --- | --- | --- |
| Builder's Book | `output/pdf/codex_robot_body_v2_assembly_guide.pdf` | Picture-first dry assembly plus explicit release holds. |
| Body print project | `cad/bambu/codex_robot_body_v2_p1s.3mf` | 45 prototype pieces on 13 material-separated plates. |
| Coupon print project | `cad/bambu/codex_robot_body_v2_coupons_p1s.3mf` | 18 logical tests / 19 objects / 5 material-separated plates. |
| UART contract | `docs/body-protocol-v1.md` | Fixed v1 bench protocol; no flash/config-write path. |
| Pi body daemon | `software/robotd/` | Executable local Unix-socket/UART baseline with blackbox logging. |
| Pi 5 appliance | `software/appliance/` + `software/install.sh` | Closed-world Bookworm provisioning baseline; real Pi, Tunnel, dual-UART, and append-only collector attestations remain open. |
| Pico safety firmware | `firmware/pico2-safety/` | Tested portable safety core plus a deliberately fail-stopped Pico integration. Production motor outputs are absent. |
| Harness traveler | `harness/harness-v2.json` | 27-conductor engineering schedule; exact terminals, measured lengths, fuses, and physical evidence remain red. |
| Commissioning evidence | `commissioning/plan-v2.json` + `docs/first-article-evidence.md` | Executable 27-step gate plus content-addressed, externally signed per-robot bundles; no physical pass is bundled. |
| Unpowered commissioning fixture | `commissioning/fixture-v1.json` + `docs/commissioning-fixture-v1.md` | Closed-world circuit, one support-free PETG plate, and USB-logic/0.20 A negative-control guide; no physical pass is bundled. |

## Filament

| Product slot | Buy | Role |
| --- | --- | --- |
| White PETG | one 1 kg spool; confirm the slicer estimate | white general and enclosure-fallback structure (5 plates). |
| Black PETG | a small spool or known-good leftovers | black motion and wear structure (1 plate). |
| Red PETG | a small spool or known-good leftovers | red battery, safety-board, and motor retainers (1 plate). |
| Charcoal PLA | a small spool or known-good leftovers | direct visible cosmetic parts; physical fit/temperature gates open (1 plate). |
| Teal PLA | a small spool or known-good leftovers | direct visible cosmetic parts; physical fit/temperature gates open (1 plate). |
| Translucent lime PLA | a small spool or known-good leftovers | light diffusers; optical/thermal gates open (1 plate). |
| Charcoal TPU 95A | one 500 g spool | tires, bumper halves, battery pads (3 plates). |

## Fasteners

| Exact size | Buy | Role |
| --- | --- | --- |
| M3 × 8 mm socket head screws | one 100-pack | The ONLY screw in the robot (47 used + spares). |
| M3 × 5.7 mm brass heat-set inserts (4.6 mm OD) | one 100-pack | The only insert (47 used + spares). |

## Electronics and purchased hardware

This table is the prototype selection list, not blanket purchase authorization.
Any row whose fit, termination, load, or test evidence is open stays open.

| Part | Qty | Role / hold |
| --- | --- | --- |
| Raspberry Pi 5 (8 GB) | 1 | The robot’s computer. |
| 32 GB+ A2 microSD card | 1 | The computer’s memory card — the robot’s programs live here. |
| Raspberry Pi Camera Module 3 Wide + long FPC cable | 1 | The robot’s eye. |
| Raspberry Pi Pico 2 (no headers, no WiFi) | 1 | The safety helper: reflexes and watchdog. |
| Cytron MDDS10 motor driver | 1 | The purple board that powers the wheels. |
| Pololu #4867 gearmotor (99:1, 25D, 12 V, encoder) | 2 | The wheel motors. |
| Hitec D85MG servo | 2 | The neck motors (look left/right, up/down). |
| Hitec R-ML24 aluminum horn (H24T) | 2 | One per servo; 22 mm single arm with M2 × 0.4 stations at 13 and 16 mm. |
| Verified D85MG/R-ML24 component hardware pack | 1 set | 2 spline-center screws, 4 M2 horn-link screws, and both servos’ mounting grommets, eyelets, screws, and nuts. Confirm the delivered pack against the head coupons before use. |
| Bioenno BLF-1203AB 12 V 3 Ah LiFePO4 battery | 1 | The robot’s power pack. |
| Bioenno BPC-1502DC charger | 1 | The matching charger. Only ever use this one. |
| Switchcraft EN2P3M20 inlet + EN2C3F20G2 plug | 1 pair | The keyed charging plug on the back. |
| Pololu D24V90F5 regulator (5 V) | 1 | Makes clean 5 V for the Pi. |
| Pololu D36V50F6 regulator (6 V) | 1 | Makes 6 V for the neck servos. |
| Panasonic CB1A-R-M-12V relay | 1 | The motor power switch the red button controls. |
| Blue Sea Systems 5045 fuse block | 1 | Splits power safely into four fused branches. |
| ATO fuse assortment (values not released) | 1 kit | Prototype starting values require measured load, conductor, inrush, selective-clearing, and thermal tests before use. |
| IDEC XW1E-BV402M-R emergency stop | 1 | THE BIG RED BUTTON. |
| E-Switch PVB3F230SS311 mute switch | 1 | The microphone privacy switch (glows red when muted). |
| Omron D2HW-C202MR bumper switches | 6 | Feelers inside the bumpers. |
| VL53L1X time-of-flight boards (Adafruit 3967) | 4 | Distance eyes: two in front, one each side. |
| Adafruit 5975 NeoPixel breakouts + JST-SH cables | 4 | The glowing eyes and status lights. |
| ReSpeaker USB mic array | 1 | The robot’s ears. |
| Enclosed 3 W 4 ohm speakers + 2× Adafruit MAX98357A amps | 1 set | The robot’s voice. |
| Prototype wire, terminal, and connector kit | not released | The production terminal schedule, measured lengths, and crimp tooling are still open; do not improvise a powered harness from this preview. |

## Bench commands

```bash
python3 commissioning/run_host_tests.py
python3 software/appliance/appliance.py --check
python3 commissioning/fixture.py --check
python3 harness/generate_harness_docs.py
python3 harness/generate_harness_docs.py --release
python3 commissioning/commission.py list
python3 commissioning/commission.py show C001
```

The first three commands must pass without robot hardware. The two release
gates are intentionally red until the exact first article supplies every
required measurement and test record. Final evidence verification also requires
the sealed bundle, expected robot serial, and an independently administered
OpenSSH `allowed_signers` / revocation policy.

## Powered-motion release remains blocked on

- Exact delivered-part fit and the completed 18-coupon record.
- Exact connector housings/contacts, measured harness lengths, continuity and
  pull tests, released fuse values, selective-fault tests, and thermal soak.
- Reviewed conditioned-input, relay-driver, battery-sense, motor-output, and
  encoder integration; the shipped Pico target can never enable the motors.
- E-stop, all six NC bumper zones, broken-wire behavior, watchdog, independent
  setpoint lease, charger inhibit, low-battery cutoff, and hardware mic-mute
  fixture results.
- Head wear/current/cable-drag, wheel retention, target-floor current,
  45-minute runtime/reserve, real Pi/Tunnel/dual-UART proof, append-only off-host
  audit readback and denied-mutation proof, and closure inspection.
- Real first-article wiring and hidden-layer photographs.

If a field is blank, the answer is not “probably.” The answer is “open.” Tiny
robot, enormous respect for empty checkboxes.
