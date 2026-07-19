# Hardware-free CI gates

The `Bench safety` workflow runs the same hardware-free entry point used on a
developer machine:

```bash
python3 commissioning/run_host_tests.py
python3 docs/builder_release_v2.py --check
```

A green run proves only that:

- the `robotd` protocol, simulator, socket, and blackbox tests pass, and the
  blackbox stays a quiet state-change journal under status polling;
- the supervision dashboard serves its UI, decodes safety flags/bumper masks
  in firmware bit order, clamps and forwards commands through `robotd`,
  refuses non-loopback binds by default, and streams status/blackbox events;
- commissioning evidence rejects incomplete/contradictory records, unsafe
  artifacts, changed source provenance, damaged event chains, transplanted
  signatures, bundled trust roots, and signer/robot mismatches;
- RB-FIXTURE-V1 matches its generated guide/labels/CAD data, its circuit matches
  the Pico pin contract, and closed-world mutation tests reject unsafe drift;
- the checked-in harness passes its engineering checks while its separate
  physical release gate still rejects blank conductor/first-article evidence;
- synthetic commissioning bundles can be signed and independently verified,
  while the repository's missing real bundle and separate harness release gate
  both remain red;
- the portable C11 protocol and safety core compile and pass their host tests;
- the Pi appliance manifest/templates are closed-world and fresh, staging is
  idempotent, secret formats and modes are enforced, tlog failure behavior and
  audit backup gaps/recovery/truncation are host-tested, and the installer parses;
- the tracked builder-release page matches its lightweight source catalog.
- beginner-facing contracts keep the v1 BOM historical, include the Pico head
  route, enforce open-bumper-zero semantics, pin CAD dependencies, and keep the
  tracked HTML portable and free of retired wiring/fuse claims.

The runner creates an isolated Python environment, uses only the Python
standard library and repository sources, and needs no secrets, robot hardware,
or package download. It uses CMake/CTest when available and otherwise a strict
C11 compiler fallback.

The separate `CAD release` workflow regenerates the v2 BREP geometry on macOS,
runs the production CAD gate, and cross-checks body/coupon plate counts and
generator identities. Green CI still does **not** provision a Pi, contact Cloudflare, prove either physical
UART, validate an append-only collector, build or flash Pico firmware, validate
a physical circuit, release the harness, replace any of the 27 commissioning
steps, or authorize powered motion. It also does not prove the fixture was printed, wired, or tested.
The shipped Pico integration remains fail-stopped and has no production motor
outputs. A green robot emoji would be adorable, but it would still not be a fuse
value.
