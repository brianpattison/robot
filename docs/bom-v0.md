# BOM v0: Codex House Companion MVP — HISTORICAL V1 ONLY

> **Do not purchase or assemble v2 from this file.** This page is a compact
> record of retired v1 assumptions. The only current v2 selection list and
> purchase blockers are in [`builder-release-v2.md`](builder-release-v2.md).

Date of the original estimate: 2026-07-06

The original BOM mixed a useful early product sketch with metal drivetrain,
idler, fastener, and speculative electrical purchases that D025-D028 later
removed. Leaving live shopping verbs beside those rows was unsafe for a
builder who landed here from search, so the obsolete checkout table is no
longer reproduced in the active documentation tree. Git history preserves it
for forensic comparison.

## Retired v1 assumptions

| Historical assumption | Why it is not a v2 instruction |
| --- | --- |
| Pololu #1569 metal motor brackets | v2 uses printed saddles and caps. |
| Pololu #1997 aluminum wheel hubs | v2 wheels clamp directly to the motor D-shafts. |
| 608 bearings, WDS shoulder bolts, M6 hardware, and goBILDA spacers | v2 front pods use printed axle/bushing load paths. |
| Purchased standoffs, spacers, straps, and multiple screw sizes | v2 body hardware is one M3 insert SKU plus one M3 × 8 screw SKU; only documented component-integral hardware is exempt. |
| Inline fuse/connector shopping from guessed loads | v2 has separate battery-near motor and accessory feeder fuses, but every fuse value, exact holder, terminal, conductor, and connector remains unreleased. |
| A complete mobile Pi power path | the protected locking Pi input, backfeed protection, downstream fusing, boot/load margin, and thermal proof remain blocked. |
| A complete servo/head power path | the D36V50F6 availability and two-servo transient/thermal qualification remain blocked. |
| A generic service-switch cluster or software-reset assumption | v2 still needs a selected, protected Pico-local physical reset. |

## Current route

Use these artifacts, in order:

1. [`builder-release-v2.md`](builder-release-v2.md) for current selections,
   sourcing state, and explicit holds.
2. [`../output/pdf/codex_robot_body_v2_assembly_guide.pdf`](../output/pdf/codex_robot_body_v2_assembly_guide.pdf)
   for coupon-first dry assembly.
3. [`retail-sourcing-policy.md`](retail-sourcing-policy.md) for the live retail
   rule and substitution policy.
4. [`../harness/README.md`](../harness/README.md) and
   [`first-article-evidence.md`](first-article-evidence.md) for the intentionally
   red electrical and physical release gates.

The v2 body can be printed and dry-assembled only after the coupons pass. It
is not a complete retail kit and this historical filename grants no powered
motion authority. Tiny robot archaeology belongs in Git, not in a shopping
cart.
