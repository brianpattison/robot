# Rover Bean Builder Release — v2.0.0-prototype.5

Permanent source: [https://github.com/brianpattison/robot/releases/tag/v2.0.0-prototype.5](https://github.com/brianpattison/robot/releases/tag/v2.0.0-prototype.5)

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
| Proof print project | `cad/bambu/codex_robot_body_v2_proofs_p1s.3mf` | 18 logical tests / 19 objects / 5 material-separated plates. |
| UART contract | `docs/body-protocol-v1.md` | Fixed v1 bench protocol; no flash/config-write path. |
| Pi body daemon | `software/robotd/` | Executable local Unix-socket/UART baseline with blackbox logging. |
| Pi 5 appliance | `software/appliance/` + `software/install.sh` | Closed-world Bookworm provisioning baseline; real Pi, Tunnel, dual-UART, and append-only collector attestations remain open. |
| Pi provisioning guide | `docs/pi-appliance-provisioning.md` | The full appliance recipe the book's "Move the brain into the robot" page condenses. |
| Supervision dashboard | `software/dashboard/` | Localhost-only `robotd` client: status, decoded safety flags, bumper zones, hold-to-drive, blackbox tail. Not a safety device. |
| Pico safety firmware | `firmware/pico2-safety/` | Tested portable safety core plus a deliberately fail-stopped Pico integration. Production motor outputs are absent. |
| Harness traveler | `harness/harness-v2.json` | 28-route engineering schedule; exact terminals, measured lengths, fuses, and physical evidence remain red. |
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
| Candidate body-color PLA (optional) | one spool per color you audition | Proof try-out only: the shell/head color you hope to qualify. Those parts print white PETG until a candidate passes its recorded checks. |

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
| Raspberry Pi Camera Module 3 Wide + Pi 5 camera cable (22-pin, 300 mm) | 1 | The robot’s eye. The Pi 5 uses the small 22-pin camera connector — the 15-pin cable in the camera box fits older Pis, not this one. |
| Raspberry Pi Pico 2 (no headers, no WiFi) | 1 | The safety helper: reflexes and watchdog. |
| Cytron MDDS10 motor driver | 1 | The purple board that powers the wheels. |
| Pololu #4867 gearmotor (99:1, 25D, 12 V, encoder) | 2 | The wheel motors. |
| Hitec D85MG servo | 2 | The neck motors (look left/right, up/down). |
| Hitec R-ML24 aluminum horn (H24T) | 0 for now | DO NOT BUY YET — no normal US quantity-one source is confirmed, and an unmodeled substitute horn is forbidden. The head build pauses at the step 18 sourcing gate until this row clears. |
| Verified D85MG/R-ML24 component hardware pack | 0 for now | DO NOT BUY YET — not yet purchasable as a kit (spline-center screws, M2 horn-link screws, servo grommets, eyelets, nuts). Releases with the horn row above; confirm the delivered pack against the head proofs. |
| Bioenno BLF-1203AB 12 V 3 Ah LiFePO4 battery | 1 | The robot’s power pack. |
| Bioenno BPC-1502DC charger | 1 | The matching charger. Only ever use this one. |
| Switchcraft EN2P3M20 inlet + EN2C3F20G2 plug | 1 pair | The keyed charging plug on the back. |
| Pololu D24V90F5 regulator (5 V) | 1 | Safe to buy — the board itself is the settled pick and its deck pocket fits it. What stays BLOCKED is wiring it: the novice-safe locking Pi input, backfeed protection, downstream fusing, boot/load margin, and thermal proof are open; never feed the GPIO header from this preview. |
| Pololu D36V50F6 regulator (6 V) | 0 for now | DO NOT BUY YET — availability and two-servo transient/thermal evidence are open. The dry build tolerates its empty deck pocket (step 12 notes it). |
| Panasonic CB1A-R-M-12V relay | 1 | The motor power switch the red button controls. |
| Production relay driver | not released | BLOCKED: RB-FIXTURE-V1's Adafruit 5648 is negative-control evidence only; production default-off conditioning, fit, and EE review remain open. |
| Pico-local physical reset | not released | BLOCKED: exact momentary control, protected input, label, and CAD/service location are not selected. |
| Blue Sea Systems 5045 fuse block | 1 | Splits power safely into four fused branches. |
| ATO/ATC fuses | 0 for now | Every value is unset. Select and buy only after measured load, conductor, inrush, time-current, selective-clearing, and thermal evidence is reviewed. |
| IDEC XW1E-BV402M-R emergency stop | 1 | THE BIG RED BUTTON. |
| E-Switch PVB3F230SS311 mute switch | 1 | The microphone privacy switch (glows red when muted). |
| Omron D2HW-C202MR bumper switches | 6 | Feelers inside the bumpers. |
| VL53L1X time-of-flight boards (Adafruit 3967) | 4 | Distance eyes: two in front, one each side. |
| Adafruit 5975 NeoPixel breakouts + JST-SH cables | 4 | The glowing eyes and status lights. |
| ReSpeaker USB mic array | 1 | Selected envelope; exact revision plus a true VBUS-cut/no-backfeed mute interface remain BLOCKED. |
| Enclosed 3 W 4 ohm speakers + 2× Adafruit MAX98357A amps | 1 set | The robot’s voice. |
| Prototype wire, terminal, and connector kit | not released | The production terminal schedule, measured lengths, and crimp tooling are still open; do not improvise a powered harness from this preview. |

## Bench equipment

The commissioning plan's acceptance thresholds assume these instruments; they
are commissioning tools, not robot parts, and none of them ride in the body.

| Instrument | Qty | What it proves |
| --- | --- | --- |
| Current-limited DC bench supply (0–15 V, ≥3 A, settable current limit) | 1 | Regulator bring-up (C006), the fixture's 0.20 A negative-control stage, the low-battery sweep (C017), and the 6 V servo bench (C022). A settable limit is the requirement; programmable sweep is a convenience. |
| Multimeter with continuity beeper, mV resolution, and 0.01 A DC current | 1 | Every continuity check in the harness traveler, the ≤100 mV mute/backfeed readings (C018), and the per-motor / pack current ceilings (C024). |
| Contactless IR thermometer (or thermocouple meter) | 1 | Terminal, conductor, servo, motor, driver, and pack temperature evidence (C019, C022, C024, C025). |
| Raspberry Pi Debug Probe (SC0889) | 1 | Already in the fixture BOM: the Pi debug-console attestation cable, the Pico service corridor, and the one-time independent cross-check of the firmware's self-reported stop-latency telemetry. |

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

- A protected mobile Pi 5 input, normal US R-ML24 source, available/qualified
  servo regulator, production relay driver, and Pico-local physical reset.
- Exact delivered-part fit and the completed 18-proof record.
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
