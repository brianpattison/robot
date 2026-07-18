# Executable commissioning package

The 27-step plan in [`plan-v2.json`](plan-v2.json) turns the release gates into
records instead of vibes. It starts unpowered, moves through logic fixtures and
wheels-up tests, and reaches floor/runtime tests only at the end.

```bash
python3 commissioning/commission.py list
python3 commissioning/commission.py run-automated C007
python3 commissioning/commission.py record C001 --result pass --operator Brian \
  --measure robot_serial=RB-001 --measure guide_sha256=... \
  --measure firmware_commit=... --measure battery_serial=... \
  --measure harness_revision=v2-prototype-H0
python3 commissioning/commission.py verify
python3 commissioning/commission.py report --output output/commissioning/report.md
```

`verify` is intentionally red in the repository: no physical evidence is
bundled. A step cannot pass the final gate unless it is recorded `pass` and
every named measurement is present. Fixed invariants also carry executable
acceptance predicates: for example, a record marked `pass` still fails if it
says a protocol clear succeeded, a service cable remained connected, a clamp
exceeded its limit, or a required fault/recovery event was not observed. The
runner pins evidence to the SHA-256 of the exact plan so editing the procedure
invalidates old records rather than quietly making them fit.

Never copy a pass from another robot, filament, battery, harness, firmware
build, or floor. A cute robot with borrowed paperwork is still just a cute
robot with forged paperwork.
