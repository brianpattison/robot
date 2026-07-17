"""Generate the v2 printed-only assembly guide PDF from live manifests.

Reads the print manifest, the coupon manifest, and the inventory's joint
and fastener registries, so the guide cannot drift from the model. Run
the v2 chain first (model -> validator -> print -> coupons), then:

    .venv-cad/bin/python docs/generate_assembly_guide_v2.py

Output: output/pdf/codex_robot_body_v2_assembly_guide.pdf. Render pages
with pdftoppm and inspect before delivery, per repo convention.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "cad" / "python"))

import robot_body_v2_inventory as inv  # noqa: E402
from reportlab.lib.pagesizes import landscape, letter  # noqa: E402
from reportlab.lib.units import inch  # noqa: E402
from reportlab.pdfgen import canvas as pdfcanvas  # noqa: E402

PAGE = landscape(letter)
W, H = PAGE
IMAGES = ROOT / "docs" / "images"
PRINT_MANIFEST = ROOT / "cad" / "exports" / "v2" / "print_ready" / "codex_robot_body_v2_print_manifest.json"
COUPON_MANIFEST = ROOT / "cad" / "exports" / "v2" / "coupons" / "codex_robot_body_v2_coupons_manifest.json"
OUT = ROOT / "output" / "pdf" / "codex_robot_body_v2_assembly_guide.pdf"

CREAM, TEAL, DARK, RED = (0.97, 0.94, 0.88), (0.04, 0.43, 0.52), (0.13, 0.13, 0.14), (0.72, 0.08, 0.06)

ASSEMBLY_STEPS = [
    ("Print and pass the coupons", "All 11 coupons print support-free. Do not print any large part until the insert, joint, D-bore, axle, snap, switch-pocket, and tire coupons pass.", "coupons"),
    ("Heat-set the tray and shell inserts", "Drive the M3 inserts flush: tray (controller base, pods, battery posts, Pico bosses, saddle tops, deck towers) and shell (corner lugs, lid ledge, speaker columns, ToF bosses).", "shell_tray, deck_towers, motor_caps, battery_clamp, controller_tower_base, front_pods, speaker_clamps, tof_clamps, pico_clamp"),
    ("Mount the rear motors and wheels", "Drop each #4867 into its saddle trough, fit the clamp cap (2 screws each), route the encoder leads into the motor-lead corridor. Press each wheel's D-bore onto the shaft and fit the radial clamp screw.", "motor_caps, rear_wheel_clamps"),
    ("Fit the front pods and wheels", "Bolt each pod's base flange to the tray (2 screws), slide the front wheel onto the printed axle, retain with a printed washer + screw into the axle-end insert.", "front_pods, front_axle_retainers"),
    ("Install the controller tower", "Bolt the plinth through its four counterbored tabs, seat the MDDS10 on its standoffs (terminals NORTH into the side corridor), stack the Pi on the shelf frame with the AI-HAT reserve above.", "controller_tower_base"),
    ("Seat the battery and Pico", "TPU pad frame on the tray pads, pack on top (leads rearward through the corridor and riser), clamp bar onto the rail posts. Pico onto its bosses, clamp bar over it (USB east, SWD up).", "battery_clamp, pico_clamp"),
    ("Hang the regulators and fit the deck", "Regulators hang under the deck (D36 wire corridor WEST), fuse block into its pocket lip on the deck's south half, wire exit over the edge. Deck onto the four towers.", "deck_towers"),
    ("Fit speakers, ToF boards, and the shell", "Speakers onto the shell ledges with clamp bars; side ToF boards behind their windows with clamps. Lower the shell over the chassis and drive the four corner-lug screws up through the tray.", "speaker_clamps, tof_clamps, shell_tray"),
    ("Close the lid with the E-stop", "The lid IS the IDEC clamp panel: mount the E-stop through the lid bore against the integrated collar, purchased nut clamps the 4 mm lid. Mic cradle onto its lid bosses. Four lid screws into the ledge.", "lid_shell, mic_cradle"),
    ("Build the head", "Neck through the lid bore onto the pan interface, bayonet collar retains it. Yoke on the neck flange, tilt bushing + M3 pivot on the passive side, faceplate into its recess, pan plate closes the underside.", "head joints are Phase-4 detail"),
]

RELEASE_GATES = [
    "Every purchased part: delivered-revision fit check before its assembly step.",
    "D-bore coupon holds 2x extrapolated stall (22 kg-cm) warm and cold before powered motion.",
    "Axle/bushing wear test on target flooring before household release.",
    "Battery clamp inverted-shake and tilt tests; pack current and runtime tests per the BOM.",
    "E-stop dual-NC, deterministic motor-cut, and bumper six-zone tests before any powered motion.",
    "Delivered-part weighing replaces every screen-grade mass in the inventory.",
    "A fresh external design review round precedes the D027 gate declaration.",
]


def page_header(c, title, num, total):
    c.setFillColorRGB(*CREAM)
    c.rect(0, 0, W, H, stroke=0, fill=1)
    c.setFillColorRGB(*TEAL)
    c.rect(0, H - 0.62 * inch, W, 0.62 * inch, stroke=0, fill=1)
    c.setFillColorRGB(1, 1, 1)
    c.setFont("Helvetica-Bold", 17)
    c.drawString(0.5 * inch, H - 0.44 * inch, title)
    c.setFont("Helvetica", 10)
    c.drawRightString(W - 0.5 * inch, H - 0.42 * inch, f"Codex robot body v2 — page {num}/{total}")


def wrapped(c, text, x, y, width, size=9.5, leading=12.5, bold=False):
    c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
    words, line = text.split(), ""
    for word in words:
        trial = (line + " " + word).strip()
        if c.stringWidth(trial, "Helvetica-Bold" if bold else "Helvetica", size) > width:
            c.drawString(x, y, line)
            y -= leading
            line = word
        else:
            line = trial
    if line:
        c.drawString(x, y, line)
        y -= leading
    return y


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    pm = json.loads(PRINT_MANIFEST.read_text())
    cm = json.loads(COUPON_MANIFEST.read_text())
    total = 8
    c = pdfcanvas.Canvas(str(OUT), pagesize=PAGE)

    # 1 — cover
    page_header(c, "Codex Robot Body v2 — Printed-Only Assembly Guide", 1, total)
    img = IMAGES / "codex_robot_body_v2_assembled.png"
    if img.exists():
        c.drawImage(str(img), 0.6 * inch, 0.7 * inch, width=6.4 * inch, height=4.8 * inch,
                    preserveAspectRatio=True, anchor="sw")
    c.setFillColorRGB(*DARK)
    x = 7.4 * inch
    y = H - 1.2 * inch
    y = wrapped(c, "One-piece 238 x 220 x 133 body. No purchased metal structure.", x, y, 3.2 * inch, 12, 16, bold=True)
    screws, inserts = inv.fastener_tally()
    draft, after, budget = inv.budget_report()
    for line in (
        f"{draft} printed parts (budget {budget}).",
        f"{screws} screws + {inserts} inserts — one SKU each: {inv.FASTENER['screw']}; {inv.FASTENER['insert']}.",
        "One 2.5 mm hex key assembles the robot.",
        "Zero-support print inventory (D028).",
        "Decisions D025-D028; the D027 packing gate is OPEN pending the external review round.",
    ):
        y -= 6
        y = wrapped(c, line, x, y, 3.2 * inch, 10.5, 14)
    c.setFillColorRGB(*RED)
    wrapped(c, "This guide describes the v2 design intent. Nothing here authorizes powered motion; the release gates on the final page hold.", x, 1.3 * inch, 3.2 * inch, 10, 13, bold=True)
    c.showPage()

    # 2 — safety
    page_header(c, "Safety first: the robot must fail stopped", 2, total)
    c.setFillColorRGB(*DARK)
    y = H - 1.1 * inch
    for line in (
        "The physical E-stop cuts motor power independently of the Pi — its dual-NC contacts stay in the low-current relay-enable path.",
        "Bumper switches and the Pico watchdog stop motion without consulting any software above them.",
        "Printed structure carries torque and shear through geometry (D-bores, keys, troughs, pockets); screws only clamp (D025/D026).",
        "Lift the unpowered robot with two hands under the tray. Never lift by the shell, lid, head, bumper, or wiring.",
        "The E-stop clamps the removable 4 mm lid (inside the IDEC 0.8-6 mm range) against the integrated collar boss; its slap access sweep and the head's pan sweep are validated non-intersecting (finding #11).",
        "Charge only through the keyed EN2 inlet with charger AC removed; insertion must inhibit motion deterministically.",
    ):
        y = wrapped(c, "•  " + line, 0.6 * inch, y, W - 1.2 * inch, 11, 16)
        y -= 8
    c.showPage()

    # 3 — fastener system + joints
    page_header(c, "The single-SKU fastener system (D026)", 3, total)
    c.setFillColorRGB(*DARK)
    y = H - 1.0 * inch
    y = wrapped(c, f"Every joint: one {inv.FASTENER['screw']} through a 3.0-3.4 mm clamp stack into one {inv.FASTENER['insert']}. Counterbores keep the stack constant; thicker flanges are counterbored, thinner parts ARE the stack.", 0.6 * inch, y, W - 1.2 * inch, 10.5, 14)
    y -= 10
    c.setFont("Helvetica-Bold", 10)
    c.drawString(0.6 * inch, y, "Joint family")
    c.drawString(3.4 * inch, y, "Screws")
    c.drawString(4.4 * inch, y, "Interface points (x, y)")
    y -= 4
    c.line(0.6 * inch, y, W - 0.6 * inch, y)
    y -= 13
    c.setFont("Helvetica", 9.5)
    for j in inv.JOINTS:
        pts = ", ".join(f"({p[0]:.0f},{p[1]:.0f})" for p in j.positions)
        c.drawString(0.6 * inch, y, j.name)
        c.drawString(3.4 * inch, y, str(len(j.positions)))
        c.drawString(4.4 * inch, y, pts[:110])
        y -= 13.5
    c.showPage()

    # 4 — coupons
    page_header(c, "Coupons print first — calibration gates every large part", 4, total)
    c.setFillColorRGB(*DARK)
    y = H - 1.0 * inch
    for name, entry in cm.items():
        y = wrapped(c, f"{name}  [{entry['material']}]  —  {entry['note']}", 0.6 * inch, y, W - 1.2 * inch, 9.5, 12.5)
        y -= 4
    c.showPage()

    # 5/6 — print inventory
    parts = sorted(pm["parts"].items())
    half = (len(parts) + 1) // 2
    for pg, chunk in enumerate((parts[:half], parts[half:]), start=5):
        page_header(c, f"Print inventory ({pg - 4}/2) — all parts support-free", pg, total)
        c.setFillColorRGB(*DARK)
        y = H - 1.0 * inch
        c.setFont("Helvetica-Bold", 10)
        for label, xx in (("Design", 0.6), ("Qty", 3.6), ("Material", 4.2), ("Print span (mm)", 5.3), ("Orientation", 7.0)):
            c.drawString(xx * inch, y, label)
        y -= 4
        c.line(0.6 * inch, y, W - 0.6 * inch, y)
        y -= 14
        c.setFont("Helvetica", 9.5)
        for name, e in chunk:
            span = " x ".join(str(v) for v in e["print_span_mm"])
            c.drawString(0.6 * inch, y, name.replace("_v2", ""))
            c.drawString(3.6 * inch, y, str(e["qty"]))
            c.drawString(4.2 * inch, y, e["material"])
            c.drawString(5.3 * inch, y, span)
            c.drawString(7.0 * inch, y, e["orientation"][:42])
            y -= 14
        c.showPage()

    # 7 — assembly order
    page_header(c, "Assembly order (one hex key)", 7, total)
    c.setFillColorRGB(*DARK)
    y = H - 0.95 * inch
    for i, (title, body, joints) in enumerate(ASSEMBLY_STEPS, start=1):
        y = wrapped(c, f"{i}. {title} — {body}", 0.6 * inch, y, W - 1.2 * inch, 9.5, 12)
        c.setFillColorRGB(*TEAL)
        y = wrapped(c, f"    joints: {joints}", 0.6 * inch, y, W - 1.2 * inch, 8.5, 11)
        c.setFillColorRGB(*DARK)
        y -= 3
    c.showPage()

    # 8 — chassis render + release gates
    page_header(c, "Service view and release gates", 8, total)
    img = IMAGES / "codex_robot_body_v2_chassis.png"
    if img.exists():
        c.drawImage(str(img), 0.5 * inch, 0.6 * inch, width=5.4 * inch, height=4.05 * inch,
                    preserveAspectRatio=True, anchor="sw")
    c.setFillColorRGB(*RED)
    x, y = 6.2 * inch, H - 1.05 * inch
    y = wrapped(c, "Nothing in this guide is a powered-motion release.", x, y, 4.3 * inch, 11.5, 15, bold=True)
    c.setFillColorRGB(*DARK)
    y -= 4
    for gate in RELEASE_GATES:
        y = wrapped(c, "•  " + gate, x, y, 4.3 * inch, 9.5, 12.5)
        y -= 4
    c.save()
    print(f"wrote {OUT} ({total} pages)")


if __name__ == "__main__":
    main()
