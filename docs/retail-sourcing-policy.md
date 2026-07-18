# Retail Sourcing Policy and v2 Audit

Date: 2026-07-18

Every purchased production item must have a stable manufacturer part number,
primary documentation, and normal quantity-one checkout from a mainstream US
retailer or distributor. Safety/power parts should have two US sources when
practical. RFQ-only, overseas-only, factory-minimum, custom-machined, custom
sheet-metal, and custom-PCB items are rejected unless Brian approves an
exception. Printed parts and assembled harnesses made from retail components
remain allowed.

Availability is volatile. Refresh immediately before ordering; a link is not
stock, and a shopping-cart screenshot is not a datasheet.

## Current v2 audit

| Item | Design identity | Retail state on 2026-07-18 | Release consequence |
| --- | --- | --- | --- |
| Pi 5, Camera 3 Wide, Pico 2 | Raspberry Pi | normal US channels | exact owned/delivered revisions still recorded |
| Motors | Pololu #4867 | product page offered a backorder path | buy one only after stock refresh; mobility purchase blocked |
| Pi regulator | Pololu D24V90F5 | normal specialist-retail trail | not a complete novice-safe Pi input; mobile compute power blocked |
| Servo regulator | Pololu D36V50F6 #4092 | rationed/out of stock during audit | blocked; no substitution without electrical/CAD review |
| Servos | Hitec D85MG | manufacturer and US hobby trail present | exact fit/current tests open |
| Horns | Hitec R-ML24 H24T | easy direct trail found only in Europe | violates US rule; source or redesign required |
| Battery/charger | Bioenno BLF-1203AB/BPC-1502DC | manufacturer quantity-one checkout | complete physical battery gate open |
| E-stop | IDEC XW1E-BV402M-R | stable manufacturer/distributor identity | fit and independent cutoff tests open |
| Motor relay | Panasonic CB1A-R-M-12V | manufacturer identity and US distributor trail | production driver/terminal/dropout/thermal/fault tests open |
| Fuse block | Blue Sea 5045 | normal marine retail trail | every fuse value remains unset |
| Charge connector | Switchcraft EN2P3M20/EN2C3F20G2 | active manufacturer/distributors | pin/polarity/strain tests open |
| Bumper switches | Omron D2HW-C202MR | mainstream distributor family | exact suffix/lead and coupon tests open |
| Mobile Pi input | protected Pi 5 battery input | no accepted part/interface | **hard sourcing/design blocker** |
| Physical reset | Pico-local momentary control | no accepted part/location | **hard design blocker** |
| Mic mute/backfeed gate | protected USB data/power interface | no accepted exact circuit/parts | **hard electrical blocker** |

The current purchase authority is
[`builder-release-v2.md`](builder-release-v2.md). Older audits that discuss
metal motor brackets, wheel hubs, bearings, shoulder bolts, standoffs, spacers,
straps, or split-body hardware are v1 history after D025-D026.

## Substitution rule

A substitute is a design change, not a checkout convenience. Re-run sourcing,
datasheet, envelope/service, electrical, thermal, firmware, CAD, print, guide,
and physical gates affected by the change. Never silently substitute a motor,
servo horn, regulator, battery, relay, switch contact form, or connector.

## Purchase batches

1. Buy only filament, the two body-fastener packs, bench supplies, and one
   sample of each fit-critical component needed for coupons/dry fit.
2. Close delivered-fit and bench electrical gates before paired motors,
   servos, horns, regulators, or harness inventory.
3. Buy final wire, terminals, and fuses only from the measured, reviewed
   harness plan. There is intentionally no “close enough” robot-wiring aisle.
