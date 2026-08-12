# Pico 2 safety firmware bench baseline

This directory contains two layers:

- A portable safety state machine and framed-protocol parser, built and tested
  on the host with ordinary CMake or a C11 compiler.
- A Pico SDK integration target that defaults to `RB_HARDWARE_RELEASE=0`.
  That fail-stopped build exercises UART/status logic but never enables the
  motor relay or motor PWM outputs.

Host tests:

```bash
cmake -S firmware/pico2-safety -B /tmp/rover-bean-safety-build
cmake --build /tmp/rover-bean-safety-build
ctest --test-dir /tmp/rover-bean-safety-build --output-on-failure
```

The repo-wide runner automatically falls back to the host C compiler when
CMake is unavailable:

```bash
python3 commissioning/run_host_tests.py
```

Pico build after installing the official Pico SDK:

```bash
cmake -S firmware/pico2-safety/pico -B /tmp/rover-bean-pico-build
cmake --build /tmp/rover-bean-pico-build
```

The generated UF2 is a **bench communications build**. Do not change
`RB_HARDWARE_RELEASE` to 1 until the reviewed board pinout, battery divider,
conditioned inputs, motor-driver mode, relay-driver circuit, harness readback,
and commissioning fixture are all present. The Pi cannot perform this flash in
the assembled robot: USB/SWD remain service-only.

The core already tests fixed velocity/acceleration clamps, independent
heartbeat and motion leases, physical reset latches, six NC bumper zones,
zero motion while any bumper loop is open, broken-wire clear rejection, charger
inhibit, low-battery latch behavior, head clamps, CRC, and fragmented frames.

## Stop-latency telemetry

The safety core self-reports stop-event timing: on every new onset of a
stopping cause (E-stop, bumper/wiring, watchdog, motion lease, charger, low
battery) it records the cause flags, the millisecond tick that first observed
the input, and the tick that folded it into the motor-enable decision. The
Pico target drains that single latest-wins slot into an EVENT (`0x82`) frame;
overwritten events are counted in `dropped_events`, not queued. Boot-time
latches are seeded as already active so power-up never fakes an event.

This is read-only telemetry. It adds no configuration path and no new
Pi-to-Pico command, and it changes no output logic -- the bench build's motor
enable stays hard-off either way. The number measures the firmware loop only,
so commissioning still cross-checks it once against an independent external
probe before trusting it (see `docs/body-protocol-v1.md`).
