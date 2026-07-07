# Blender Concept Body Pass

This folder holds Blender source for visual industrial-design iteration on the Codex Rover Bean body.

`concept_body_blender.py` procedurally builds the current concept shell and renders:

- Twenty-four iteration thumbnails across the initial and refinement tuning loops.
- Front three-quarter, side, top, exploded, service, and safety-review views.
- A final side-by-side concept comparison after running the compose script.

Run from the repo root:

```bash
/Applications/Blender.app/Contents/MacOS/Blender --background --python cad/blender/concept_body_blender.py
.venv-cad/bin/python scripts/compose_blender_concept_previews.py
```

For fast single-shot iteration against the concept art (renders only the hero
front three-quarter view to a gitignored `cad/blender/hero_preview.png`, ~2s):

```bash
/Applications/Blender.app/Contents/MacOS/Blender --background --python scripts/render_hero.py
```

The Blender model is a visual and packaging artifact, not a manufacturing model. Use it to settle silhouette, color placement, service layering, and component envelope fit before translating final surfaces back into print-ready CAD or STEP geometry.

The assembled render is tuned to match the finished concept art. The assembled, exploded, and service renders are generated from the same procedural body-part inventory; exploded/service modes apply offsets to those shared parts rather than adding fake one-off parts.

The exploded and service views also build **representative internal components** sized to `docs/bom-v0.md` and the `docs/cad-mechanical-plan.md` parameter contract — Raspberry Pi 5, Pico 2 safety MCU, dual motor driver, 5V/servo regulators, power distribution, 12V LiFePO4 battery, encoder gearmotors, rear caster, VL53L1X ToF sensors, USB mic array, and speaker — so the body demonstrably houses the MVP build. These sit inside the closed shell and are hidden in the assembled (concept-match) view. The teal deck is modeled as a real service hatch: a top opening is cut in the shell beneath it, so lifting the deck (service view) exposes the electronics bay.
