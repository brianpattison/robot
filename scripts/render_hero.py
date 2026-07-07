#!/usr/bin/env python3
"""Fast single-view hero render for concept-matching iteration.

Run:
    /Applications/Blender.app/Contents/MacOS/Blender --background --python scripts/render_hero.py

Renders only the front three-quarter hero shot so we can iterate quickly
against the finished concept art instead of rebuilding all 24 thumbnails.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "cad" / "blender"))

import concept_body_blender as cb  # noqa: E402

# Gitignored preview path so fast iteration does not touch committed docs.
OUT = ROOT / "cad" / "blender" / "hero_preview.png"


def main() -> None:
    cb.render_scene(OUT, "front_3q", progress=1.0, mode="assembled", refinement=1.0, width=1500, height=1000)
    print(f"wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
