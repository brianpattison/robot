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
limited direction-aware escape, persistent-open wiring faults, charger inhibit,
low-battery latch behavior, head clamps, CRC, and fragmented frames.
