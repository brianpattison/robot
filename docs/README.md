# Documentation Index

Read these in order when getting oriented:

1. [MVP PRD](mvp-prd.md)
   Product goals, non-goals, hardware baseline, safety requirements, milestones, and acceptance criteria.

2. [Decision Log](decision-log.md)
   Settled choices that should guide future design work.

3. [MVP Architecture](mvp-architecture.md)
   Runtime components, safety/control boundaries, voice flow, perception flow, dashboard, and deployment layout.

4. [Agentic Control Plan](agentic-control-plan.md)
   Full agent authority on the robot computer — live SSH, code on the fly, installs, direct motion setpoints — above the physical/firmware safety floor (D030-D032).

5. [BOM v0](bom-v0.md)
   First-pass parts list, rough cost ranges, already-owned parts, buy-now batch, and deferrals.

6. [Retail Sourcing Policy And Audit](retail-sourcing-policy.md)
   Quantity-one US checkout rule, known sourcing violations, and replacement directions.

7. [CAD Mechanical Plan](cad-mechanical-plan.md)
   Printable modules, CAD parameter strategy, rough dimensions, fit-check tests, and export workflow.

8. [CAD v1 Body Preview](cad-v1-body.md)
   Generated assembled, head-detail, exploded, electronics-fit, Pico 2 safety-shelf, Cytron MDDS10 controller-stack, dual MAX98357A speaker-plate, retail-only upper power-deck, BLF-1203AB battery cradle, under-deck harness, EN2 charge/blank-center/physical-mute cartridges, tray-fixed bumper switch, retail front-idler stack, printer-split joinery, and canonical print-orientation previews for the current build123d body source.

9. [CAD Component Coverage](cad-component-coverage.md)
   BOM-to-CAD matrix showing modeled interfaces, reserved service bays, and measured-hardware gates that still block release printing.

10. [CAD Calibration Coupons](cad-coupons.md)
   Seventeen parametric insert, clearance, bearing-seat, wall, production lid-lap, exact split-pilot, clipped tray/PETG/TPU bumper-interface, flush-fairing recess, and Blue Sea 5045 fit coupons with a measured-use protocol.

11. [Bambu Studio P1S Project](../cad/bambu/README.md)
   Reproducible 101-part, 26-plate P1S 0.4 mm layout split into 14 material-profile/color groups, with an exact plate manifest and visual overview.

12. [The Builder's Book — v2 Assembly Guide](../output/pdf/codex_robot_body_v2_assembly_guide.pdf)
    The generated **prototype assembly preview — not for powered motion** for the printed-only v2 body: computed
    cover TOC, annotated meet-the-robot spread, shopping and printing chapters, piece
    inventory, twenty picture-first steps with progress bars and CHECK tests, wiring
    maps, and release-gap callouts. Child-followable by design, with no "grown-up"
    callouts (D029), but not yet a standalone retail build manual: the D035 head
    mechanism is CAD-complete while exact-part fit, loaded wear/current tests,
    harness details, software/firmware, fuse release, and commissioning remain open.
    Regenerate with `docs/generate_assembly_guide_v2.py`.
    The 2026-07-17 review audit behind the current render/text conventions
    (insertion arrows, insert markers, insets, mirrored-direction fixes, the tire
    port, and the goalpost eye bar) is in
    [guide-v2-improvement-notes.md](guide-v2-improvement-notes.md).

    Its current print inventory follows D034: 40 functional pieces, four spare
    washers, and one optional PLA lid skin on 13 plates. Direct visible panels
    and diffusers are PLA; fixed PETG stays white/black/red; the PLA shell and
    head candidates automatically remain white PETG until physical evidence is
    recorded for the exact filament family.

13. [v1 Illustrated Assembly Guide (historical)](../output/pdf/codex_robot_body_v1_assembly_guide.pdf)
    Twenty-page visual build sequence synchronized with the D024 retail-only CAD, current renders, 101-part print manifest, and 26-plate P1S project.

> **D024 retail-only baseline:** CAD, validation, split and print manifests,
> coupons, renders, P1S project, and assembly PDF are synchronized around the
> Panasonic relay, Blue Sea 5045, WDS shoulder-bolt idlers, blank center rear
> cartridge, and handle-free tray. Legacy decisions remain historical records.

Current MVP baseline:

- Existing Raspberry Pi 5 8GB.
- No AI HAT+ 2 required for MVP.
- Wheeled differential-drive body.
- Camera head, mic array, speaker, LEDs, E-stop, bumpers, ToF sensors, and local dashboard.
- OpenSCAD first for simple CAD; `build123d` and CadQuery for richer geometry; Blender only for concept iteration and rendering the generated STL inventory.
- Bambu Lab P1S with the standard 0.4 mm nozzle and Textured PEI Plate as the settled print-layout target.
