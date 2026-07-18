#!/usr/bin/env python3
"""Check beginner-facing release artifacts without CAD or network dependencies."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"BEGINNER_CONTRACT_FAIL: {message}")


def main() -> None:
    harness = json.loads((ROOT / "harness/harness-v2.json").read_text())
    routes = {route["id"]: route for route in harness["conductors"]}
    require(len(routes) == 28, f"expected 28 harness routes, found {len(routes)}")
    require("HEAD-01" in routes, "Pico-to-servo head-control route is missing")
    require("Pico" in routes["HEAD-01"]["from"], "head control does not originate at Pico")

    current_safety = "\n".join(
        (ROOT / path).read_text()
        for path in (
            "AGENTS.md",
            "docs/body-protocol-v1.md",
            "docs/mvp-architecture.md",
            "docs/agentic-control-plan.md",
            "firmware/pico2-safety/include/safety_core.h",
            "firmware/pico2-safety/src/safety_core.c",
        )
    ).lower()
    for forbidden in ("capped-speed escape", "rb_escape_", "escape window"):
        require(forbidden not in current_safety, f"retired bumper policy remains: {forbidden}")

    readme = (ROOT / "README.md").read_text()
    require("Current v2 purchase authority" in readme, "README lacks current purchase authority")
    require("Buy the bench-brain" not in readme, "README still sends builders to the v1 BOM")
    legacy_bom = (ROOT / "docs/bom-v0.md").read_text()[:500]
    require("HISTORICAL V1" in legacy_bom and "Do not purchase" in legacy_bom,
            "v1 BOM lacks an effective historical warning")
    legacy_bom_all = (ROOT / "docs/bom-v0.md").read_text().lower()
    for forbidden in (
        "buy now",
        "buy with",
        "buy after",
        "buy for",
        "recommended first purchase batch",
    ):
        require(forbidden not in legacy_bom_all,
                f"historical v1 BOM still contains a shopping imperative: {forbidden}")

    guide_html = (ROOT / "output/guide/codex_robot_body_v2_guide.html").read_text()
    for forbidden in (
        "file://",
        "/Users/",
        "PROTOTYPE STARTING VALUES",
        "Fuse branch 3</td><td>mute",
        "I2C daisy chain",
        "Servos ×2</td><td>Raspberry Pi",
        "5 V REG → RASPBERRY PI",
        "MUTE SWITCH → MIC",
        "GLOW LIGHTS (5 V)",
        "pins 1+2 → battery charge lead",
    ):
        require(forbidden not in guide_html, f"unsafe/non-portable guide text remains: {forbidden}")
    for required in (
        "PROTECTED PI INPUT BLOCKED",
        "BRANCH 3 → COVERED SPARE",
        "contact assignments TBD",
    ):
        require(required in guide_html, f"blocked wiring state is not visible in guide: {required}")

    requirements = [
        line for line in (ROOT / "cad/python/requirements.txt").read_text().splitlines()
        if line and not line.startswith("#")
    ]
    require(all("==" in line for line in requirements), "CAD/guide dependency is not exactly pinned")
    print("BEGINNER_CONTRACT_PASS routes=28 guide=portable bumper=open-means-zero")


if __name__ == "__main__":
    main()
