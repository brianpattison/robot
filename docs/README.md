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

6. [CAD v1 Body Preview](cad-v1-body.md)
   Generated assembled, head-detail, exploded, electronics-fit, Pico 2 safety-shelf, Cytron MDDS10 controller-stack, dual MAX98357A speaker-plate, upper power-deck, BLF-1203AB battery-cradle, split-tray carry, under-deck harness, drawing-backed EN2 charge/UART service/physical-mute cartridges, tray-fixed bumper-switch, printer-split joinery, and canonical print-orientation previews for the current build123d body source.

7. [CAD Component Coverage](cad-component-coverage.md)
   BOM-to-CAD matrix showing modeled interfaces, reserved service bays, and measured-hardware gates that still block release printing.

8. [CAD Calibration Coupons](cad-coupons.md)
   Seventeen parametric insert, clearance, bearing-seat, wall, production lid-lap, exact split-pilot, clipped tray/PETG/TPU bumper-interface, flush-fairing recess, and distribution-board fit coupons with a measured-use protocol.

9. [Bambu Studio P1S Project](../cad/bambu/README.md)
   Reproducible 103-part, 26-plate P1S 0.4 mm layout split into 14 material-profile/color groups, with an exact plate manifest and visual overview.

10. [Illustrated Assembly Guide](../output/pdf/codex_robot_body_v1_assembly_guide.pdf)
    Twenty-page visual build sequence covering calibration, P1S plates, split joinery, load paths, mobility, deterministic safety interfaces, electronics, the covered four-branch Nano2 distribution board, power, expression, head mechanisms, the three rear charge/service/mute cartridges, closure, and commissioning gates. Regenerate it with `docs/generate_assembly_guide.py` after current renders and manifests.

Current MVP baseline:

- Existing Raspberry Pi 5 8GB.
- No AI HAT+ 2 required for MVP.
- Wheeled differential-drive body.
- Camera head, mic array, speaker, LEDs, E-stop, bumpers, ToF sensors, and local dashboard.
- OpenSCAD first for simple CAD; `build123d` and CadQuery for richer geometry; Blender only for concept iteration and rendering the generated STL inventory.
- Bambu Lab P1S with the standard 0.4 mm nozzle and Textured PEI Plate as the settled print-layout target.
