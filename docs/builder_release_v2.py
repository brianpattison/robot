#!/usr/bin/env python3
"""Generate the immutable-entry-point page for the v2 prototype release."""

from __future__ import annotations

import argparse
from pathlib import Path

from builder_release_catalog_v2 import (SHOP_BENCH_GEAR, SHOP_ELECTRONICS,
                                         SHOP_FASTENERS, SHOP_FILAMENT)

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "builder-release-v2.md"
RELEASE_ID = "v2.0.0-prototype.5"
RELEASE_URL = f"https://github.com/brianpattison/robot/releases/tag/{RELEASE_ID}"


def render() -> str:
    filament_rows = "\n".join(
        f"| {name} | {amount} | {role} |" for name, amount, role in SHOP_FILAMENT)
    fastener_rows = "\n".join(
        f"| {name} | {amount} | {role} |" for name, amount, role in SHOP_FASTENERS)
    electronics_rows = "\n".join(
        f"| {name} | {amount} | {role} |" for name, amount, role in SHOP_ELECTRONICS)
    bench_rows = "\n".join(
        f"| {name} | {amount} | {role} |" for name, amount, role in SHOP_BENCH_GEAR)
    return f"""# Rover Bean Builder Release — {RELEASE_ID}

Permanent source: [{RELEASE_URL}]({RELEASE_URL})

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
| Proof print project | `cad/bambu/codex_robot_body_v2_proofs_p1s.3mf` | 18 logical tests / 20 objects / 5 material-separated plates. |
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
{filament_rows}

## Fasteners

| Exact size | Buy | Role |
| --- | --- | --- |
{fastener_rows}

## Electronics and purchased hardware

This table is the prototype selection list, not blanket purchase authorization.
Any row whose fit, termination, load, or test evidence is open stays open.

| Part | Qty | Role / hold |
| --- | --- | --- |
{electronics_rows}

## Bench equipment

The commissioning plan's acceptance thresholds assume these instruments; they
are commissioning tools, not robot parts, and none of them ride in the body.

| Instrument | Qty | What it proves |
| --- | --- | --- |
{bench_rows}

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

- A protected mobile Pi 5 input, available/qualified servo regulator,
  production relay driver, and Pico-local physical reset (the R-ML24 sourcing
  blocker is retired — D048's printed arm-capture cradle drives the head with
  the arm from the servo's own bag, pending the delivered-arm proof).
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
"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    content = render()
    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_text(encoding="utf-8") != content:
            raise SystemExit(f"STALE_BUILDER_RELEASE: run {Path(__file__).relative_to(ROOT)}")
        print(f"BUILDER_RELEASE_PASS {RELEASE_ID}")
        return
    OUTPUT.write_text(content, encoding="utf-8")
    print(f"wrote {OUTPUT}")


if __name__ == "__main__":
    main()
