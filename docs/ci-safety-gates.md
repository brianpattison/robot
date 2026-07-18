# Hardware-free CI gates

The `Bench safety` workflow runs the same hardware-free entry point used on a
developer machine:

```bash
python3 commissioning/run_host_tests.py
python3 docs/builder_release_v2.py --check
```

A green run proves only that:

- the `robotd` protocol, simulator, socket, and blackbox tests pass;
- commissioning evidence rejects incomplete or contradictory records;
- RB-FIXTURE-V1 matches its generated guide/labels/CAD data, its circuit matches
  the Pico pin contract, and closed-world mutation tests reject unsafe drift;
- the checked-in harness passes its engineering checks while its physical
  release gate still rejects blank first-article evidence;
- the portable C11 protocol and safety core compile and pass their host tests;
- the tracked builder-release page matches its lightweight source catalog.

The runner creates an isolated Python environment, uses only the Python
standard library and repository sources, and needs no secrets, robot hardware,
or package download. It uses CMake/CTest when available and otherwise a strict
C11 compiler fallback.

Green CI does **not** build or flash Pico firmware, validate a physical circuit,
release the harness, replace any of the 27 commissioning steps, or authorize
powered motion. It also does not prove the fixture was printed, wired, or tested.
The shipped Pico integration remains fail-stopped and has no production motor
outputs. A green robot emoji would be adorable, but it would still not be a fuse
value.
