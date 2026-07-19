# v2 Qualification Proofs

Each qualification proof is a small printed piece that proves exactly one v2
design contract before any large body part prints. Generate the 18 logical
tests:

```bash
python cad/python/robot_body_v2_proofs.py
python cad/bambu/generate_bambu_proofs_v2.py
```

The tracked five-plate project contains 19 material-correct objects because
the tire-fit test needs separate PETG and TPU pieces. The generated manifest
under `cad/exports/v2/proofs/` records each test's material, dimensions,
orientation, print recipe, purpose, and blank evidence fields.

The set covers M3 insert fit, flange/boss clamp stacks, D-bore torque, printed
axle wear, snap and bayonet cycles, bumper-switch geometry, tire fit, Pico
clamp stress, exact-PLA insert/shell/head/snap behavior, optical diffusion, and
the PETG-lid/PLA-skin boundary. Print each object in the exact production
material, orientation, nozzle, layer, walls, and conditioning it represents.

Record raw measurements, photos, material product/lot, printer/profile, tester,
date, and failures in the first-article evidence bundle. A failed or blank
proof changes the CAD/material decision or keeps the fallback/gate open; it
never becomes “close enough” by prose. Rerun the full v2 chain after changing a
shared parameter.

Historical v1 coupons for split pilots, metal bearings, fairings, and the
legacy distribution gauge are not v2 release evidence and keep their original
name (D038 renamed only the v2 pieces).
