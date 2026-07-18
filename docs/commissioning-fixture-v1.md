# RB-FIXTURE-V1 — unpowered commissioning fixture

Status: **design and hardware-free validation only; no physical pass is bundled.**

This one-plate fixture makes the first Pico safety observations repeatable without
a battery, motor, or MDDS10. It uses the six real NC bumper switches, real IDEC
E-stop, and real Panasonic relay, but the headered Pico is a dedicated fixture
part. Passing this guide never authorizes powered motion.

## Boundary

- F1–F3 are mechanical, continuity, and USB-logic work.
- F4 adds a **12.0 V, 0.20 A current-limited bench supply** only after GP11 is low.
- Current firmware deliberately keeps GP11 low. This negative-control witness
  requires the relay and lamp to stay off.
- Remove 12 V before every Pico reset, flash, unplug, or wiring change. Apply USB
  first and 12 V last. Driver reset behavior is not a safety control.

## Print one part

Export `cad/openscad/commissioning_fixture_v1.scad` as PETG. The plate is
232 × 210 × 79 mm overall. Print its component face on the P1S plate with the four
hollow feet upward; no supports. Flip after printing. The 75 mm feet leave 6.3 mm
beyond the registered 68.7 mm E-stop-plus-terminal envelope. CAD clearance is not
delivered-part fit evidence.

## Parts

Availability references were checked 2026-07-17. Reused parts return to the robot
only after inspection. M3 × 12 screws and nylocs are fixture-only and do not alter
the robot's single-M3 × 8 rule.

| ID | Item | Exact part / source | Qty | Use |
| --- | --- | --- | ---: | --- |
| `PICO` | Raspberry Pi Pico 2 with headers | [SC1632](https://pip.raspberrypi.com/categories/1005-raspberry-pi-pico-2) | 1 | fixture; dedicated fixture board; never the production robot Pico |
| `DEBUG_PROBE` | Raspberry Pi Debug Probe | [SC0889](https://www.raspberrypi.com/documentation/microcontrollers/debug-probe.html) | 1 | fixture; use only the three-wire UART U cable; no SWD connection during observations |
| `BREADBOARD` | 830-point solderless breadboard | [BusBoard BB830 or Adafruit 239](https://www.adafruit.com/product/239) | 1 | fixture; attach with the supplied adhesive backing |
| `BUMP_1` | Omron SPST-NC bumper switch | [D2HW-C202MR](https://omronfs.omron.com/en_US/ecb/products/pdf/en-d2hw.pdf) | 1 | reuse |
| `BUMP_2` | Omron SPST-NC bumper switch | [D2HW-C202MR](https://omronfs.omron.com/en_US/ecb/products/pdf/en-d2hw.pdf) | 1 | reuse |
| `BUMP_3` | Omron SPST-NC bumper switch | [D2HW-C202MR](https://omronfs.omron.com/en_US/ecb/products/pdf/en-d2hw.pdf) | 1 | reuse |
| `BUMP_4` | Omron SPST-NC bumper switch | [D2HW-C202MR](https://omronfs.omron.com/en_US/ecb/products/pdf/en-d2hw.pdf) | 1 | reuse |
| `BUMP_5` | Omron SPST-NC bumper switch | [D2HW-C202MR](https://omronfs.omron.com/en_US/ecb/products/pdf/en-d2hw.pdf) | 1 | reuse |
| `BUMP_6` | Omron SPST-NC bumper switch | [D2HW-C202MR](https://omronfs.omron.com/en_US/ecb/products/pdf/en-d2hw.pdf) | 1 | reuse |
| `ESTOP_SENSE_SIM` | breadboard SPST logic control | fixture-only switch or jumper | 1 | fixture; separate logic simulation; not an E-stop contact |
| `RESET_BUTTON` | breadboard momentary SPST logic control | fixture-only switch or jumper | 1 | fixture |
| `CHARGER_SIM` | breadboard SPST logic control | fixture-only switch or jumper | 1 | fixture; closed is charger absent; open is charger present because GP10 uses the firmware pull-up |
| `ESTOP` | IDEC dual-NC emergency stop | [XW1E-BV402M-R](https://us.idec.com/idec-us/en/USD/medias/IDEC-XA-XW-EMO-Datasheet.pdf) | 1 | reuse; both NC channels are physically in series; test each channel power-off before 12 V |
| `DRIVER` | Adafruit MOSFET Driver | [5648](https://learn.adafruit.com/adafruit-mosfet-driver/pinouts) | 1 | fixture; non-isolated low-side switch; integral flyback diode; output + is V+ and output - is switched ground |
| `RELAY` | Panasonic sealed SPST-NO relay | CB1A-R-M-12V | 1 | reuse; 12 V, 134 mA coil; fixture uses the real robot relay |
| `LAMP` | Bulgin green 12 V LED indicator | [DX06WG012B](https://www.bulgin.com/pdf/pdf.php?sku=DX06WG012B) | 1 | fixture; witness load on relay NO only |
| `BENCH_12V` | current-limited bench supply | user bench supply | 1 | fixture; set 12.0 V and 0.20 A before connecting; no battery |
| `WAGO` | two-conductor lever connector | [221-412/K007-0000](https://www.wago.com/us/wire-splicing-connectors/compact-splicing-connector/p/221-412) | 10 | fixture |
| `WIRE` | 22 AWG solid-core breadboard wire set | [Adafruit 1311](https://www.adafruit.com/product/1311) | 1 | fixture; fixture-only low-current wiring; do not infer a production harness release |
| `UART_CABLE` | three-pin JST-SH socket cable | [Adafruit 3893](https://www.adafruit.com/product/3893) | 1 | fixture; optional spare/adapter; Debug Probe U cable remains the UART baseline |
| `PLATE` | printed fixture plate | cad/openscad/commissioning_fixture_v1.scad | 1 | fixture; PETG; 232 x 210 x 79 mm overall; no supports |
| `FIXTURE_FASTENERS` | fixture-only fasteners | M3 x 12 SHCS plus M3 nyloc nuts | 12 | fixture; temporary fixture hardware, deliberately distinct from the robot's M3 x 8 single-SKU system |

## Assemble with no power

1. Flip the print and confirm all four feet sit without rocking.
2. Apply `commissioning/generated/fixture-v1-labels.svg` at 100% scale.
3. Stick down the breadboard. Mount the six Omrons with M3 × 12 screws and nylocs.
4. Tie the driver and relay through their slots. Fit E-stop and lamp with their nuts.
5. Put the dedicated SC1632 Pico on the breadboard. Use only the Debug Probe UART
   U cable: GP0 TX to probe RX, GP1 RX to probe TX, and ground to ground. No SWD.
6. Build separate GP8 E-stop-sense, GP9 reset, and GP10 charger-simulation controls.
   They are logic simulations, not physical safety paths.

## Wire these nets exactly

The Adafruit 5648 is a **non-isolated low-side driver**. Output `+` is V+, output
`-` is switched ground, and all grounds are common.

| Net | Domain | Endpoints |
| --- | --- | --- |
| `GND_COMMON` | `ground` | `PICO.GND` -> `DEBUG_PROBE.GND` -> `DRIVER.GND` -> `BENCH_12V.NEG` -> `BUMP_1.COM` -> `BUMP_2.COM` -> `BUMP_3.COM` -> `BUMP_4.COM` -> `BUMP_5.COM` -> `BUMP_6.COM` -> `ESTOP_SENSE_SIM.COM` -> `RESET_BUTTON.COM` -> `CHARGER_SIM.COM` -> `LAMP.NEG` |
| `UART_TX` | `PICO_LOGIC` | `PICO.GP0` -> `DEBUG_PROBE.RX` |
| `UART_RX` | `PICO_LOGIC` | `PICO.GP1` -> `DEBUG_PROBE.TX` |
| `BUMP_1_NC` | `PICO_LOGIC` | `PICO.GP2` -> `BUMP_1.NC` |
| `BUMP_2_NC` | `PICO_LOGIC` | `PICO.GP3` -> `BUMP_2.NC` |
| `BUMP_3_NC` | `PICO_LOGIC` | `PICO.GP4` -> `BUMP_3.NC` |
| `BUMP_4_NC` | `PICO_LOGIC` | `PICO.GP5` -> `BUMP_4.NC` |
| `BUMP_5_NC` | `PICO_LOGIC` | `PICO.GP6` -> `BUMP_5.NC` |
| `BUMP_6_NC` | `PICO_LOGIC` | `PICO.GP7` -> `BUMP_6.NC` |
| `ESTOP_SENSE_SIM` | `PICO_LOGIC` | `PICO.GP8` -> `ESTOP_SENSE_SIM.SW` |
| `RESET_SIM` | `PICO_LOGIC` | `PICO.GP9` -> `RESET_BUTTON.SW` |
| `CHARGER_SIM` | `PICO_LOGIC` | `PICO.GP10` -> `CHARGER_SIM.SW` |
| `RELAY_LOGIC` | `PICO_LOGIC` | `PICO.GP11` -> `DRIVER.IN` |
| `12V_POS` | `BENCH_12V` | `BENCH_12V.POS` -> `ESTOP.NC1_IN` -> `RELAY.COM` |
| `ESTOP_SERIES` | `BENCH_12V` | `ESTOP.NC1_OUT` -> `ESTOP.NC2_IN` |
| `DRIVER_VPLUS` | `BENCH_12V` | `ESTOP.NC2_OUT` -> `DRIVER.VPLUS` -> `RELAY.COIL_HIGH` |
| `DRIVER_OUT` | `BENCH_12V_SWITCHED` | `DRIVER.OUT` -> `RELAY.COIL_LOW` |
| `RELAY_NO_LAMP` | `BENCH_12V_SWITCHED` | `RELAY.NO` -> `LAMP.POS` |

```text
12V_POS -> IDEC NC1 -> IDEC NC2 -> DRIVER.VPLUS / RELAY.COIL_HIGH
PICO.GP11 -> DRIVER.IN
DRIVER.OUT -> RELAY.COIL_LOW
12V_POS -> RELAY.COM -> RELAY.NO -> LAMP -> GND_COMMON
```

The driver carries the flyback diode across V+/OUT. **Reverse polarity can
forward-bias it.** Meter polarity before 12 V and keep the 0.20 A limit set. Do
not discover polarity with sparks, however festive.

## Firmware pins

`python3 commissioning/fixture.py --check` parses the authoritative Pico target.

| Signal | Pico pin |
| --- | ---: |
| `uart_tx` | GP0 |
| `uart_rx` | GP1 |
| `bumper_1` | GP2 |
| `bumper_2` | GP3 |
| `bumper_3` | GP4 |
| `bumper_4` | GP5 |
| `bumper_5` | GP6 |
| `bumper_6` | GP7 |
| `estop_sense` | GP8 |
| `reset` | GP9 |
| `charger_sense` | GP10 |
| `relay_enable` | GP11 |

## F1 — mechanical, no power

- [ ] Plate is flat; feet are uncracked; labels are legible.
- [ ] Tallest underside part has at least 5 mm table clearance.
- [ ] Switches operate without moving their mounts.
- [ ] Pico is the fixture SC1632, not production Pico.
- [ ] Battery, motors, and MDDS10 are absent.

## F2 — continuity, no power

- [ ] Each bumper is closed at rest and opens when pressed.
- [ ] IDEC NC1 opens when pressed; release/twist, then repeat for NC2.
- [ ] The series coil path opens when either NC channel opens.
- [ ] No Pico GPIO has continuity to a 12 V net.
- [ ] 12V_POS is not shorted to ground; loose supply leads meter with correct polarity.

The series E-stop path proves each contact individually only while unpowered. It
cannot create two independent powered channel results. Record that limitation.

## F3 — USB logic and UART

1. Leave 12 V disconnected. Connect Pico USB and Debug Probe USB separately.
2. Observe 115200-baud status and measure GP11 low.
3. Open one bumper at a time; record exact zone identity. Hold one open to observe
   broken-wire behavior.
4. Exercise GP8, GP9, and GP10 separately. GP10 closed to ground means charger
   absent; open means charger present through the firmware pull-up.
5. Send fixed-contract status/heartbeat/drive frames. Capture clamps and latches,
   but do not record relay or motor behavior.
6. Confirm GP11 stayed low. Disconnect USB before changing wires.

## F4 — 12 V negative control

1. Re-run F2. Set the disconnected supply to 12.0 V and **0.20 A maximum**. Turn it
   off and meter its polarity again.
2. Start USB logic, wait for stable status, and measure GP11 low.
3. With Pico stable, connect 12V_POS and ground while the supply is off, then turn
   it on. Never reset or flash the Pico while 12 V is present.
4. Only the driver's small idle/indicator current is expected. The 134 mA relay
   coil must not energize and the roughly 20 mA lamp must remain dark.
5. If the relay clicks, lamp lights, current limit trips, or current approaches the
   coil load, turn 12 V off immediately and record failure.
6. Press the physical E-stop only to confirm the already-off feed is removed. This
   is not a powered de-energization timing result.
7. Turn off and disconnect 12 V before stopping USB logic.

## This fixture cannot pass

- Coil actuation, a positive lamp result, or powered E-stop timing with the current
  fail-stopped target.
- Production conditioned inputs, relay driver, contact wetting, fuses, harness,
  motor outputs, encoders, battery, or thermal behavior.
- Independent powered proof of the two series E-stop channels.
- Any physical commissioning result without exact first-article measurements.

`commissioning/fixture-v1.json` is authoritative. Generated prose, labels, and
SCAD data are conveniences; `--check` makes drift loud.
