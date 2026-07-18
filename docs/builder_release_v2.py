#!/usr/bin/env python3
"""Generate the immutable-entry-point page for the v2 prototype release."""

from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "builder-release-v2.md"
RELEASE_ID = "v2.0.0-prototype.1"
RELEASE_URL = f"https://github.com/brianpattison/robot/tree/{RELEASE_ID}"


def render() -> str:
    import generate_assembly_guide_v2 as guide

    filament_rows = "\n".join(
        f"| {name} | {amount} | {role} |" for name, amount, role in guide.SHOP_FILAMENT)
    fastener_rows = "\n".join(
        f"| {name} | {amount} | {role} |" for name, amount, role in guide.SHOP_FASTENERS)
    electronics_rows = "\n".join(
        f"| {name} | {amount} | {role} |" for name, amount, role in guide.SHOP_ELECTRONICS)
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
| Coupon print project | `cad/bambu/codex_robot_body_v2_coupons_p1s.3mf` | 18 logical tests / 19 objects / 5 material-separated plates. |
| UART contract | `docs/body-protocol-v1.md` | Fixed v1 bench protocol; no flash/config-write path. |
| Pi body daemon | `software/robotd/` | Executable local Unix-socket/UART baseline with blackbox logging. |
| Pi installer | `software/install.sh` | Bench install; keep the motor branch physically isolated. |
| Pico safety firmware | `firmware/pico2-safety/` | Tested portable safety core plus a deliberately fail-stopped Pico integration. Production motor outputs are absent. |
| Harness traveler | `harness/harness-v2.json` | 27-conductor engineering schedule; exact terminals, measured lengths, fuses, and physical evidence remain red. |
| Commissioning plan | `commissioning/plan-v2.json` | Executable 27-step evidence gate; no physical pass is bundled. |

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

## Bench commands

```bash
python3 commissioning/run_host_tests.py
python3 harness/generate_harness_docs.py
python3 harness/generate_harness_docs.py --release
python3 commissioning/commission.py list
python3 commissioning/commission.py verify
```

The first two commands must pass without robot hardware. The two release gates
are intentionally red until the exact first article supplies every required
measurement and test record.

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
  45-minute runtime/reserve, off-host audit readback, and closure inspection.
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
