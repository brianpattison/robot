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

The Blender model is a visual and packaging artifact, not a manufacturing model. Use it to settle silhouette, color placement, service layering, and component envelope fit before translating final surfaces back into print-ready CAD or STEP geometry.

The assembled and exploded renders are generated from the same procedural body-part inventory. Exploded mode applies offsets to those shared parts; it should not add fake one-off parts. The model intentionally avoids visible internal electronics and instead shows empty service pockets, bosses, rails, and alignment features.
