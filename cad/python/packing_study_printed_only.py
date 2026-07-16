"""Box-level packing screen for the printed-only 238 x 220 body (D027).

STATUS: the D027 packing gate is OPEN. This screen is axis-aligned-box
feasibility evidence only; it cannot pass the gate. The gate requires the
v2 BREP packing model plus the inventory-driven production validator (see
docs/printed-only-simplification-plan.md, revised Phase 2).

As of Phase 2, the layout data lives in `robot_body_v2_inventory.py` —
the registered inventory shared with the forthcoming v2 BREP model and
validator. This file is only the box-level check engine.

Review history (all findings verified against the source before adoption):
- rev 1 reported a false FEASIBLE (hardcoded envelopes; omitted E-stop
  panel/backing, battery-lead corridor, AI-HAT reserve, Pi service, roof
  rollover, keepout-keepout checks; impossible MDDS10 orientation).
- rev 2 (layout v3) was rejected: mute depth is 26 + 16 = 42 mm, the fuse
  block's 22 mm wire service was absent, the MDDS10 10 mm airflow contract
  was violated by 5.8 mm, and the AI-HAT reserve is 96 x 74 x 22.
- rev 3 (layout v4) was rejected on datums and remaining envelopes: the
  tray top is Z=49 (body_bottom), the MDDS10 thermal ceiling is 86.275,
  the pan-servo bottom is 131.6, and the deck plate is 102..106; the
  regulator/fuse corridors and the relay's full envelope were missing;
  the margin policy could hide overlaps and ignored wall margins.
- rev 4 (layout v5) closed on verified datums at 238 x 220 x 133 and was
  reproduced independently in review round 4, which green-lit Phase 2.
- rev 5 (v5.1) registered the round-4 carry-ins: Pico relocated to the
  floor NE quadrant (its former USB corridor intersected the front bay)
  with explicit USB/SWD service volumes; battery on modeled 3 mm pads;
  relay as separate bracket/body/terminal volumes; AI-HAT height recovery
  remains a BREP-discovered bonus, never assumed.
- rev 6 (this file): data moved to the shared inventory module; checks
  unchanged.

Policy: overlap between distinct assemblies is never waivable; margins
under 2 mm fail unless the exact envelope-name pair is an allowlisted
support contact; items keep >= 2 mm to the interior walls; roof-panel
hardware stays inside the rollover-limited flat; wheels stay >= 2 mm
inside the shell length.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import robot_body_v2_inventory as inv  # noqa: E402

P = inv.P

boxes = inv.boxes()


def touch_ok(a, b):
    return frozenset((a[0].rstrip("~m"), b[0].rstrip("~m"))) in inv.ALLOWED_TOUCH


def gap(a, b):
    """Largest single-axis separation; negative means volumetric overlap."""
    return max(max(a[3] - b[4], b[3] - a[4]),
               max(a[5] - b[6], b[5] - a[6]),
               max(a[7] - b[8], b[7] - a[8]))


problems, warnings = [], []
for i, a in enumerate(boxes):
    if a[1] in ("item", "service"):
        wall_margin = min(a[3] + inv.IX, inv.IX - a[4], a[5] + inv.IY, inv.IY - a[6])
        if wall_margin < 0:
            problems.append(f"OUT OF INTERIOR: {a[0]}")
        elif wall_margin < inv.MIN_MARGIN:
            warnings.append(f"WALL MARGIN {wall_margin:.1f} mm: {a[0]}")
    for b in boxes[i + 1:]:
        if a[2].rstrip("~m") == b[2].rstrip("~m"):
            continue
        g = gap(a, b)
        if g < 0:
            problems.append(f"OVERLAP {-g:.1f} mm: {a[0]} <-> {b[0]}")
        elif g < inv.MIN_MARGIN and not touch_ok(a, b):
            warnings.append(f"MARGIN {g:.1f} mm: {a[0]} <-> {b[0]}")

for nm, x0, x1, y0, y1 in [
    ("estop_panel", inv.ESTOP[0] - inv.ESTOP_R, inv.ESTOP[0] + inv.ESTOP_R,
     inv.ESTOP[1] - inv.ESTOP_R, inv.ESTOP[1] + inv.ESTOP_R),
    ("mic", inv.MIC[0] - inv.MIC_R, inv.MIC[0] + inv.MIC_R,
     inv.MIC[1] - inv.MIC_R, inv.MIC[1] + inv.MIC_R),
    ("vent", 30, 90, -96, -65),
]:
    if x0 < -inv.ROOF_FLAT_X or x1 > inv.ROOF_FLAT_X or y0 < -inv.ROOF_FLAT_Y or y1 > inv.ROOF_FLAT_Y:
        problems.append(f"OFF ROOF FLAT: {nm}")

for nm, ax in [("front", inv.FRONT_AXLE_X), ("rear", inv.REAR_AXLE_X)]:
    if abs(ax) + P.wheel_radius > inv.BODY_L / 2 - inv.MIN_MARGIN:
        problems.append(f"WHEEL OUTSIDE BODY: {nm} axle X={ax}")

masses = [("battery", 340, 30), ("head+neck", 350, P.head_center_x), ("pi+hat", 140, -53),
          ("mdds10+plate", 160, -67), ("motors+wheels", 400, inv.REAR_AXLE_X),
          ("front wheels+pods", 150, inv.FRONT_AXLE_X), ("deck+fuse+regs", 300, 66),
          ("relay", 60, -20), ("printed body", 1000, 0), ("bumper+switches", 200, 0),
          ("speakers+mic", 120, -10), ("estop", 60, inv.ESTOP[0])]
cg_x = sum(m * x for _, m, x in masses) / sum(m for _, m, x in masses)

draft, after_merges, budget = inv.budget_report()
print(f"body {inv.BODY_L} x {inv.BODY_W} x {inv.BODY_H} (Z_TOP {inv.Z_TOP});"
      f" roof flat +/-{inv.ROOF_FLAT_X:.0f} x +/-{inv.ROOF_FLAT_Y:.0f}")
print(f"height derivation: thermal ceiling {inv.THERM_TOP:.3f} + shelf 4 + Pi {P.pi_clearance_height:.0f}"
      f" + HAT 22 + margin {inv.CLEAR_MARGIN:.0f} = {inv.HAT_TOP + inv.CLEAR_MARGIN:.3f} required drop bottom;"
      f" v1 drop {inv.DROP_V1} => dH +{inv.DH} => H {inv.BODY_H:.0f}")
print(f"axles {inv.FRONT_AXLE_X}/{inv.REAR_AXLE_X} (wheelbase {inv.REAR_AXLE_X - inv.FRONT_AXLE_X:.0f});"
      f" rough CG X={cg_x:.0f}")
print("critical margins: "
      f"HAT-to-drop {inv.DROP0 - inv.HAT_TOP:.1f}; estop-terms-to-deck {inv.ESTOP_TERM_Z0 - inv.DECK1:.1f}; "
      f"speaker-arch web {115 - 109:.0f}; rear-wheel-to-shell {inv.BODY_L / 2 - (inv.REAR_AXLE_X + P.wheel_radius):.0f}; "
      f"lead-corridor-to-wall {inv.IX - 113:.1f}")
print(f"printed-part registry (D028): draft {draft}, after owed merges {after_merges}, budget {budget}")
print()
if problems or warnings:
    for pr in problems:
        print("  ", pr)
    for w in warnings:
        print("  ", w)
    print(f"\nBOX-LEVEL RESULT: NOT CLOSED ({len(problems)} violations, {len(warnings)} thin margins).")
    sys.exit(1)
print("BOX-LEVEL RESULT: layout v5.1 closes with zero violations and no margin below 2 mm.")
print("D027 gate REMAINS OPEN: box screen only. The gate needs the v2 BREP")
print("packing model + the inventory-driven production validator (plan, Phase 2).")
