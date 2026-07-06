# Documentation Index

Read these in order when getting oriented:

1. [MVP PRD](mvp-prd.md)
   Product goals, non-goals, hardware baseline, safety requirements, milestones, and acceptance criteria.

2. [Decision Log](decision-log.md)
   Settled choices that should guide future design work.

3. [MVP Architecture](mvp-architecture.md)
   Runtime components, safety/control boundaries, voice flow, perception flow, dashboard, and deployment layout.

4. [BOM v0](bom-v0.md)
   First-pass parts list, rough cost ranges, already-owned parts, buy-now batch, and deferrals.

5. [CAD Mechanical Plan](cad-mechanical-plan.md)
   Printable modules, CAD parameter strategy, rough dimensions, fit-check tests, and export workflow.

6. [CAD v0 Body Concept](cad-v0-body.md)
   First OpenSCAD body concept, colored preview renders, assembly strategy, and known fit-check limitations.

Current MVP baseline:

- Existing Raspberry Pi 5 8GB.
- No AI HAT+ 2 required for MVP.
- Wheeled differential-drive body.
- Camera head, mic array, speaker, LEDs, E-stop, bumpers, ToF sensors, and local dashboard.
- OpenSCAD first for simple CAD; `build123d` and CadQuery when Python CAD is better.
