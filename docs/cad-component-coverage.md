# v2 Component and Release Coverage

**Current v2 matrix.** Historical v1 coverage is preserved by Git history and
must not be used as a purchase list.

| Area | CAD or source proof | Still required physically |
| --- | --- | --- |
| Body envelope | 238 x 220 x 133 body; inventory validator passes | Printer calibration, large-part warp, delivered-part fit |
| Printed inventory | 40 functional + 4 spare + 1 optional; all solids registered | Print and inspect all production plates |
| Fasteners | 47 modeled M3 x 8 joints and 47 M3 inserts | Exact lot proofs, insert temperature, torque/service cycles |
| Motors/wheels | Printed saddles/caps, D-bores, tread service ports, axle caps | #4867 revision, torque, retention, wear, current, heat, skid turns |
| Bumpers | Two TPU halves, six switch pockets, rest/stroke/stops modeled | Switch proof, six-zone actuation/rebound, broken-wire stop timing |
| Battery | BLF-1203AB envelope, pad, cradle, clamp, lead corridor | Pack evidence, insulation, retention, current/runtime/BMS/regen/thermal |
| Controller/Pi | MDDS10 and Pi envelopes, airflow and port service | Exact revisions/connectors/thermals; protected mobile Pi input is blocked |
| Power deck | Blue Sea 5045, relay, D24/D36 envelopes and service | Production relay driver/reset/mute fit, terminals, fuses, EE review |
| Rear I/O | EN2 and mute cutouts/envelopes | Pin/polarity/strain, USB mute/backfeed circuit, charger inhibit |
| Head | D85MG/R-ML24 envelopes, journal/bushing, travel and stop sampling | US horn source, fit, grease, load/current/wear/backlash/heat/cable drag |
| Camera/audio/ToF/light | Camera, speaker, mic, side ToF and pixel pockets | Camera retention, amp/pixel/XSHUT mounts, connectors, exact harness |
| Safety logic | Fixed protocol plus Python/C host tests | Qualified production outputs, pin/conditioning review, HIL, binary hash, real stop timing |
| Pi appliance | Closed-world generated image and host attestations | Real Pi, Tunnel, dual UART, collector mutation denial/readback |
| Harness | 28 nominal route records and fail-closed release checker | Every exact terminal, length, pull/continuity result, fuse, thermal/fault result |
| Builder artifacts | Body/proof 3MFs and 45-page guide generate from source | Physical print/fit review and wiring rewrite after blocked parts are selected |

Passing `validate_robot_body_v2.py --gate` proves registered geometry and
kinematics. It does not prove a fuse, crimp, polymer, battery, switch, relay,
motor, servo, or human assembly. Current release holds live in
[`builder-release-v2.md`](builder-release-v2.md) and the executable
[`commissioning/plan-v2.json`](../commissioning/plan-v2.json).
