# Documentation Index

## Build Rover Bean v2

Read these in order:

1. [v2 Builder Release Index](builder-release-v2.md) - the current artifact
   map, prototype selection list, and explicit purchase/release blockers.
2. [The Builder's Book](../output/pdf/codex_robot_body_v2_assembly_guide.pdf) -
   picture-first proof and dry-assembly preview; never powered-motion authority.
3. [Bambu Studio projects](../cad/bambu/README.md) - the 13-plate body and
   five-plate proof projects.
4. [v2 component/release coverage](cad-component-coverage.md) - what CAD proves
   and what still requires delivered-part or physical evidence.
5. [v2 proof protocol](cad-proofs.md) - all 18 logical qualification tests.
6. [Harness traveler](../harness/README.md) - 28 nominal routes with the
   production gate intentionally red.
7. [Commissioning package](../commissioning/README.md) and
   [first-article evidence](first-article-evidence.md) - the 27-step physical
   release path and signed evidence bundles.

The current release is geometry, dry assembly, bench software, and
hardware-free contract evidence only. Blank physical evidence means open.

## Runtime and safety

- [Body protocol v1](body-protocol-v1.md) - fixed Pi/Pico UART commands and
  D036's zero-motion rule for any open NC bumper loop.
- [MVP architecture](mvp-architecture.md) - runtime components and deterministic
  boundaries.
- [Agentic control plan](agentic-control-plan.md) - full Pi authority above the
  physical/firmware safety floor.
- [Hardware-free CI gates](ci-safety-gates.md) - exactly what green automation
  proves and what it cannot prove.
- [Commissioning fixture](commissioning-fixture-v1.md) - current-limited,
  motorless safety observation fixture.
- [Pi appliance provisioning](pi-appliance-provisioning.md) - reproducible Pi 5
  install and its live attestation gaps.

## Product and decisions

- [MVP PRD](mvp-prd.md)
- [Decision log](decision-log.md)
- [CAD mechanical plan](cad-mechanical-plan.md)
- [Retail sourcing policy](retail-sourcing-policy.md)
- [Printed-only simplification decision](printed-only-simplification-plan.md)

## Historical v1 material

`bom-v0.md`, `cad-v1-body.md`, `generate_assembly_guide.py`, and the v1
PDF/3MF are preserved for history. They contain metal brackets, hubs, bearings,
shoulder bolts, multiple fastener systems, and other assumptions that D025-D028
removed. Never mix a v1 purchase or assembly instruction into a v2 build.
