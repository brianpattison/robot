# Body protocol v1

This is the deliberately small Pi-to-Pico contract for Rover Bean. It carries
live body setpoints and safety status over a 3.3 V UART. It contains **no**
flash, bootloader, firmware-update, pin-mode, threshold, or configuration-write
command. Changing the safety envelope requires opening the robot and flashing
the Pico through its service-only USB/SWD corridor.

Status: executable bench baseline. The protocol implementation and host tests
ship in this repository; pinout, noise, disconnect, latency, and fault-injection
results remain commissioning evidence, not assumptions.

## Link

- 3.3 V UART, 115200 baud, 8 data bits, no parity, 1 stop bit.
- Pi TX -> Pico RX, Pi RX <- Pico TX, and one signal ground.
- Pico USB and SWD are never connected to the Pi in normal operation.
- `robotd` normally owns the serial device, but the firmware safety envelope
  applies equally to any process that speaks this contract.

## Frame

All multi-byte integers are little-endian.

| Bytes | Field |
| --- | --- |
| `A5 5A` | start marker |
| `01` | protocol version |
| 1 byte | message type |
| 2 bytes | sequence number |
| 2 bytes | payload length, 0..64 |
| 0..64 bytes | payload |
| 2 bytes | CRC-16/CCITT-FALSE over version through payload |

The receiver discards bytes until the start marker, rejects a wrong version,
oversize payload, or bad CRC, and never lets a malformed frame refresh a timer.

## Pi -> Pico commands

| Type | Name | Payload | Effect |
| --- | --- | --- | --- |
| `0x01` | HEARTBEAT | none | Refreshes the fixed 250 ms host watchdog only. It never sustains motion. |
| `0x02` | DRIVE | `i16 linear_mm_s`, `i16 angular_mrad_s` | Sets a new motion target and refreshes the independent fixed 250 ms motion lease. Firmware clamps velocity and acceleration. |
| `0x03` | STOP | none | Immediately zeros the target and applied motion. |
| `0x04` | CLEAR_BUMPER | `u8 zone_mask` | Clears only requested bumper latches whose normally-closed loops currently read released. It cannot clear E-stop, charger, low-battery, watchdog, or a currently open-loop wiring indication. |
| `0x05` | STATUS_REQUEST | none | Requests a STATUS frame. Does not refresh heartbeat or motion. |
| `0x06` | HEAD | `i16 pan_cdeg`, `i16 tilt_cdeg` | Sets head targets, clamped to +/-60.00 and +/-20.00 degrees. |

Unknown commands are rejected and reported. There is intentionally no generic
register read/write escape hatch. Boring is beautiful when the wheels have
opinions.

## Pico -> Pi messages

| Type | Name | Payload |
| --- | --- | --- |
| `0x80` | ACK | `u8 command_type`, `u8 result` |
| `0x81` | STATUS | `u32 uptime_ms`, `u16 flags`, `u8 released_mask`, `u8 latched_mask`, `u16 battery_mv`, `i16 linear_mm_s`, `i16 angular_mrad_s`, `i16 pan_cdeg`, `i16 tilt_cdeg` |
| `0x82` | EVENT | `u8 event_type`, then event-specific fields; see "EVENT: stop-latency telemetry" below |

Safety flags are: E-stop latched, charger present, low battery, heartbeat stale,
motion lease stale, bumper latched, wiring fault, and motor-enable output. The
bench-safe Pico target always reports motor enable false; a future reviewed
production integration may report it true only when the deterministic
conditions permit and the actual output is enabled. The physical E-stop NC
contacts still cut the relay coil independently.

Under D036, opening any NC bumper circuit sets both the bumper-latched flag and
the wiring-fault flag because a press and a broken conductor are electrically
indistinguishable. Continuity returning clears the wiring-fault flag; the
bumper flag remains latched until a valid `CLEAR_BUMPER` request. The flags are
therefore complementary state, not mutually exclusive fault categories.

## EVENT `0x82`: stop-latency telemetry

EVENT is telemetry and nothing more. The Pi may ignore every EVENT frame
without losing any safety property: the frame carries no authority, changes no
firmware state, and has no acknowledgement or configuration path attached to
it. The safety envelope is identical whether the frames are read, logged, or
discarded.

The only defined event type is `0x01`, stop latency. The firmware self-reports
how long its own loop took to turn a stopping input into a motor-enable drop.
Payload after the frame header, little-endian like everything else:

| Field | Meaning |
| --- | --- |
| `u8 event_type` | `0x01` = stop latency. Other values are reserved. |
| `u16 cause_flags` | The safety flags whose onset produced this event, using the STATUS flag bit definitions. |
| `u32 observed_ms` | Firmware uptime at the update that first observed the stopping input. |
| `u32 enacted_ms` | Firmware uptime at the tick that folded the cause into the motor-enable decision. |
| `u16 dropped_events` | Events overwritten since the last emitted EVENT. Storage is a single latest-wins slot, not a queue. |

Onset semantics: the firmware records one event for every *new* onset of a
stopping cause -- E-stop, charger, low battery, watchdog, motion lease,
bumper, wiring -- regardless of whether motor enable was already off for
another reason, because commissioning triggers causes one at a time while the
robot is parked wheels-off. A cause must first be observed inactive for at
least one update before its next onset is reported, so the deliberate
boot-time latches (E-stop, charger, stale watchdog and lease, open bumper
loops) never produce a spurious event.

`enacted_ms - observed_ms` measures the firmware loop only. It deliberately
excludes everything the firmware cannot see: switch bounce, input
conditioning, UART transit, and relay drop-out. Commissioning therefore still
requires a one-time independent probe cross-check of sensor-edge-to-sample
latency -- external instrument from the physical edge to the relay coil --
before any self-reported number is trusted as stop-timing evidence. After
that cross-check, the C013/C015/C016/C023 stop-timing steps become
read-the-number exercises.

## Fixed safety constants in the bench baseline

- Heartbeat/watchdog: 250 ms.
- Nonzero motion lease: 250 ms.
- Linear velocity cap: 350 mm/s.
- Angular velocity cap: 1500 mrad/s.
- Linear acceleration cap: 500 mm/s^2.
- Angular acceleration cap: 2000 mrad/s^2.
- Bumper rule: any open NC loop immediately holds applied motion at zero in
  every direction. A pressed switch, unplugged connector, and broken wire are
  electrically indistinguishable, so the protocol never authorizes escape
  motion while a loop is open. A latch can clear only after continuity returns.
- Head command range: pan +/-60 degrees; tilt +/-20 degrees.

The low-battery threshold and GPIO assignment are compile-time board constants,
not protocol configuration. Their production values remain blocked on the
delivered BLF-1203AB voltage-sag/runtime tests and the released wiring review.
