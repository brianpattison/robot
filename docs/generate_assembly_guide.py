#!/usr/bin/env python3
"""Generate the illustrated Codex robot body assembly guide PDF."""

from __future__ import annotations

import json
from io import BytesIO
from datetime import date
from pathlib import Path

from PIL import Image
from reportlab.lib.colors import HexColor, white
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas


ROOT = Path(__file__).resolve().parents[1]
IMAGE_DIR = ROOT / "docs" / "images"
OUTPUT = ROOT / "output" / "pdf" / "codex_robot_body_v1_assembly_guide.pdf"
PRINT_MANIFEST = ROOT / "cad" / "exports" / "print_ready" / "codex_robot_body_v1_print_manifest.json"
PLATE_MANIFEST = ROOT / "cad" / "bambu" / "codex_robot_body_v1_p1s_plates.json"

PRINT_MANIFEST_REGEN = """  .venv-cad/bin/python cad/python/robot_body.py
  .venv-cad/bin/python cad/python/robot_body_split.py --bed 256 --margin 8
  .venv-cad/bin/python cad/python/validate_robot_body.py --bed 256 --margin 8
  .venv-cad/bin/python cad/python/robot_body_print.py --bed 256 --margin 8"""
PLATE_MANIFEST_REGEN = "  .venv-cad/bin/python cad/bambu/generate_bambu_project.py"

PAGE_W, PAGE_H = landscape(letter)
MARGIN = 30

CREAM = HexColor("#F5E9D5")
PAPER = HexColor("#FFFDF8")
TEAL = HexColor("#0E8792")
DARK_TEAL = HexColor("#003F49")
CHARCOAL = HexColor("#202428")
MID_GRAY = HexColor("#667078")
LIGHT_GRAY = HexColor("#E7E2D8")
LIME = HexColor("#CFFF45")
ORANGE = HexColor("#E8792B")
RED = HexColor("#C83F35")
BLUE = HexColor("#2465D8")


def load_json(path: Path, regeneration_commands: str) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise SystemExit(
            f"Missing required generated input: {path}\n"
            f"Regenerate it from the repository root with:\n{regeneration_commands}"
        ) from None
    except json.JSONDecodeError as exc:
        raise SystemExit(
            f"Invalid JSON in generated input {path} "
            f"(line {exc.lineno}, column {exc.colno}).\n"
            f"Regenerate it from the repository root with:\n{regeneration_commands}"
        ) from None


def wrap_lines(text: str, font: str, size: float, width: float) -> list[str]:
    words = text.split()
    lines: list[str] = []
    line = ""
    for word in words:
        candidate = word if not line else f"{line} {word}"
        if stringWidth(candidate, font, size) <= width:
            line = candidate
        else:
            if line:
                lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


def draw_wrapped(
    c: canvas.Canvas,
    text: str,
    x: float,
    y: float,
    width: float,
    font: str = "Helvetica",
    size: float = 10,
    leading: float = 13,
    color=CHARCOAL,
) -> float:
    c.setFont(font, size)
    c.setFillColor(color)
    for line in wrap_lines(text, font, size, width):
        c.drawString(x, y, line)
        y -= leading
    return y


def draw_image(c: canvas.Canvas, path: Path, x: float, y: float, w: float, h: float) -> tuple[float, float, float, float]:
    if not path.exists():
        c.setFillColor(LIGHT_GRAY)
        c.roundRect(x, y, w, h, 10, fill=1, stroke=0)
        c.setFillColor(RED)
        c.setFont("Helvetica-Bold", 12)
        c.drawCentredString(x + w / 2, y + h / 2, f"Missing image: {path.name}")
        return x, y, w, h
    with Image.open(path) as image:
        iw, ih = image.size
        # Blender's PNGs currently carry a fully opaque alpha channel. Passing
        # that unnecessary channel through ReportLab's automatic mask handling
        # can produce black bands in Poppler when an image is reused. Flatten
        # to RGB before embedding so every PDF renderer sees the same pixels.
        encoded = BytesIO()
        # Most renders are most reliable as alpha-free PNG XObjects. Poppler's
        # decoder mishandles the current exploded head image specifically, so
        # embed that one as a high-quality RGB JPEG. Direct page renders in the
        # verification pass guard this deliberately narrow workaround.
        rgb = image.convert("RGB")
        if path.name == "codex_robot_body_v1_head_mechanism.png":
            rgb.save(encoded, format="JPEG", quality=95, subsampling=0)
        else:
            rgb.save(encoded, format="PNG")
        encoded.seek(0)
        pdf_image = ImageReader(encoded)
    scale = min(w / iw, h / ih)
    dw, dh = iw * scale, ih * scale
    dx, dy = x + (w - dw) / 2, y + (h - dh) / 2
    c.setFillColor(white)
    c.roundRect(x, y, w, h, 10, fill=1, stroke=0)
    c.drawImage(pdf_image, dx, dy, dw, dh, preserveAspectRatio=True)
    c.setStrokeColor(HexColor("#D1C8B8"))
    c.setLineWidth(0.8)
    c.roundRect(x, y, w, h, 10, fill=0, stroke=1)
    return dx, dy, dw, dh


def footer(c: canvas.Canvas, page_no: int, section: str) -> None:
    c.setStrokeColor(HexColor("#D8D0C2"))
    c.line(MARGIN, 24, PAGE_W - MARGIN, 24)
    c.setFont("Helvetica", 7.5)
    c.setFillColor(MID_GRAY)
    c.drawString(MARGIN, 12, f"Codex Robot Body v1 | {section}")
    c.drawRightString(PAGE_W - MARGIN, 12, f"Page {page_no} | Generated {date.today().isoformat()}")


def page_header(c: canvas.Canvas, number: str, title: str, subtitle: str, page_no: int) -> None:
    c.setFillColor(PAPER)
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    c.setFillColor(DARK_TEAL)
    c.roundRect(MARGIN, PAGE_H - 66, 52, 36, 8, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 15)
    c.drawCentredString(MARGIN + 26, PAGE_H - 54, number)
    c.setFillColor(CHARCOAL)
    c.setFont("Helvetica-Bold", 23)
    c.drawString(MARGIN + 66, PAGE_H - 47, title)
    c.setFillColor(MID_GRAY)
    c.setFont("Helvetica", 9.5)
    c.drawString(MARGIN + 66, PAGE_H - 62, subtitle)
    footer(c, page_no, title)


def label(c: canvas.Canvas, text: str, x: float, y: float, color=TEAL) -> None:
    c.setFillColor(color)
    c.roundRect(x, y - 3, stringWidth(text, "Helvetica-Bold", 8) + 14, 17, 8, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(x + 7, y + 2, text)


def draw_steps(
    c: canvas.Canvas,
    x: float,
    y: float,
    width: float,
    steps: list[str],
    start: int = 1,
    size: float = 9.3,
) -> float:
    for index, step in enumerate(steps, start=start):
        c.setFillColor(TEAL)
        c.circle(x + 10, y - 4, 10, fill=1, stroke=0)
        c.setFillColor(white)
        c.setFont("Helvetica-Bold", 9)
        c.drawCentredString(x + 10, y - 7, str(index))
        lines = wrap_lines(step, "Helvetica", size, width - 30)
        c.setFillColor(CHARCOAL)
        c.setFont("Helvetica", size)
        line_y = y
        for line in lines:
            c.drawString(x + 28, line_y, line)
            line_y -= 12
        y = line_y - 9
    return y


def parts_box(c: canvas.Canvas, x: float, y: float, w: float, text: str) -> float:
    lines = wrap_lines(text, "Helvetica", 8.2, w - 20)
    h = 31 + len(lines) * 10
    c.setFillColor(CREAM)
    c.roundRect(x, y - h, w, h, 8, fill=1, stroke=0)
    c.setFillColor(DARK_TEAL)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(x + 10, y - 15, "PARTS / HARDWARE")
    c.setFillColor(CHARCOAL)
    c.setFont("Helvetica", 8.2)
    text_y = y - 28
    for line in lines:
        c.drawString(x + 10, text_y, line)
        text_y -= 10
    return y - h - 10


def gate_banner(c: canvas.Canvas, text: str, color=ORANGE) -> None:
    c.setFillColor(color)
    c.roundRect(MARGIN, 38, PAGE_W - 2 * MARGIN, 36, 8, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(MARGIN + 12, 60, "DO NOT PROCEED UNTIL")
    draw_wrapped(c, text, MARGIN + 12, 49, PAGE_W - 2 * MARGIN - 24, "Helvetica", 8.3, 10, white)


def instruction_page(
    c: canvas.Canvas,
    page_no: int,
    number: str,
    title: str,
    subtitle: str,
    images: list[str],
    parts: str,
    steps: list[str],
    gate: str,
    gate_color=ORANGE,
) -> None:
    page_header(c, number, title, subtitle, page_no)
    image_x, image_y, image_w, image_h = 30, 84, 474, 442
    if len(images) == 1:
        draw_image(c, IMAGE_DIR / images[0], image_x, image_y, image_w, image_h)
    elif len(images) == 2:
        gap = 10
        each_h = (image_h - gap) / 2
        draw_image(c, IMAGE_DIR / images[0], image_x, image_y + each_h + gap, image_w, each_h)
        draw_image(c, IMAGE_DIR / images[1], image_x, image_y, image_w, each_h)
    else:
        gap = 8
        top_h = 268
        draw_image(c, IMAGE_DIR / images[0], image_x, image_y + image_h - top_h, image_w, top_h)
        bottom_w = (image_w - gap) / 2
        draw_image(c, IMAGE_DIR / images[1], image_x, image_y, bottom_w, image_h - top_h - gap)
        draw_image(c, IMAGE_DIR / images[2], image_x + bottom_w + gap, image_y, bottom_w, image_h - top_h - gap)
    text_x, text_w = 520, 242
    y = parts_box(c, text_x, 520, text_w, parts)
    draw_steps(c, text_x, y, text_w, steps)
    gate_banner(c, gate, gate_color)
    c.showPage()


def set_fill_alpha_if_supported(c: canvas.Canvas, alpha: float) -> None:
    """Set fill opacity when the installed ReportLab canvas supports it."""
    setter = getattr(c, "setFillAlpha", None)
    if setter is not None:
        setter(alpha)


def cover_page(c: canvas.Canvas, page_no: int, plate_manifest: dict) -> None:
    c.setFillColor(CHARCOAL)
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    image_path = IMAGE_DIR / "codex_robot_body_v1_assembled.png"
    if image_path.exists():
        with Image.open(image_path) as image:
            iw, ih = image.size
            encoded = BytesIO()
            image.convert("RGB").save(encoded, format="PNG")
            encoded.seek(0)
            pdf_image = ImageReader(encoded)
        scale = max(PAGE_W / iw, PAGE_H / ih)
        dw, dh = iw * scale, ih * scale
        c.drawImage(pdf_image, (PAGE_W - dw) / 2, (PAGE_H - dh) / 2, dw, dh)
    else:
        draw_image(c, image_path, 0, 0, PAGE_W, PAGE_H)
    c.saveState()
    set_fill_alpha_if_supported(c, 0.86)
    c.setFillColor(DARK_TEAL)
    c.roundRect(36, 54, 430, 170, 16, fill=1, stroke=0)
    c.restoreState()
    c.setFillColor(LIME)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(58, 195, "BAMBU LAB P1S / 0.4 MM NOZZLE")
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 31)
    c.drawString(58, 155, "Codex Robot Body v1")
    c.setFont("Helvetica-Bold", 23)
    c.drawString(58, 124, "Illustrated Assembly Guide")
    c.setFont("Helvetica", 10)
    plate_count = len(plate_manifest["plates"])
    part_count = sum(len(plate["parts"]) for plate in plate_manifest["plates"])
    c.drawString(58, 93, f"{part_count} printed parts | {plate_count} plates | PETG + TPU | Prototype hardware gates apply")
    c.setFont("Helvetica", 8)
    c.drawString(58, 72, "Assemble unpowered. Motion and battery release require the tests in this guide.")
    footer(c, page_no, "Cover")
    c.showPage()


def overview_page(c: canvas.Canvas, page_no: int) -> None:
    page_header(c, "00", "How to use this guide", "Build by stage; stop at every orange or red gate.", page_no)
    draw_image(c, IMAGE_DIR / "codex_robot_body_v1_exploded.png", 30, 86, 430, 438)
    x, y, w = 485, 510, 277
    label(c, "BUILD ORDER", x, y)
    y -= 30
    stages = [
        ("A", "Calibrate", "Print coupons and verify measured fits."),
        ("B", "Structure", "Join split parts and install metal load paths."),
        ("C", "Mobility", "Build wheels, pods, motors, and bumper."),
        ("D", "Electronics", "Mount boards, power deck, sensors, and harnesses."),
        ("E", "Head", "Build bearing-supported pan/tilt, camera, and expression."),
        ("F", "Commission", "Prove stop behavior before any powered motion."),
    ]
    for code, title, body in stages:
        c.setFillColor(DARK_TEAL)
        c.circle(x + 14, y - 3, 13, fill=1, stroke=0)
        c.setFillColor(white)
        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(x + 14, y - 7, code)
        c.setFillColor(CHARCOAL)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(x + 37, y + 2, title)
        y = draw_wrapped(c, body, x + 37, y - 11, w - 42, size=8.5, leading=10)
        y -= 12
    gate_banner(c, "Read the complete stage before tightening hardware. Screw lengths remain provisional until coupons and delivered components are measured.", RED)
    c.showPage()


def hardware_page(c: canvas.Canvas, page_no: int, print_manifest: dict) -> None:
    page_header(c, "02", "Fastener and material legend", "Keep hardware bagged by interface, not merely by thread size.", page_no)
    colors = [("M2", LIME, "NeoPixels, Pico 2, camera, servo horns"), ("M2.5", TEAL, "Head panels, LED carriers, ToF, bearing retainers"), ("M3", ORANGE, "Structure, motors, decks, shell, safety plates"), ("M4", RED, "Metal carry clamps only")]
    x, y = 42, 500
    for thread, color, use in colors:
        c.setFillColor(color)
        c.roundRect(x, y - 42, 150, 42, 8, fill=1, stroke=0)
        c.setFillColor(CHARCOAL if thread == "M2" else white)
        c.setFont("Helvetica-Bold", 18)
        c.drawString(x + 12, y - 26, thread)
        c.setFillColor(CHARCOAL)
        draw_wrapped(c, use, x + 166, y - 12, 245, size=9, leading=11)
        y -= 70
    c.setFillColor(CREAM)
    c.roundRect(474, 300, 286, 220, 12, fill=1, stroke=0)
    c.setFillColor(DARK_TEAL)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(492, 492, "WORKBENCH KIT")
    kit = [
        "Temperature-controlled insert tool and coupon-selected settings",
        "M2/M2.5/M3 drivers, M4 wrench, external circlip pliers, torque-conscious hand tools",
        "Calipers, deburring tools, threadlocker only where hardware permits",
        "Multimeter, fused bench supply, current clamp, nonconductive mat",
        "Washers, locknuts, rated webbing, metal spacers, cable strain relief",
        "Eye protection and a padded low-height lift-test area",
    ]
    yy = 464
    for item in kit:
        c.setStrokeColor(TEAL)
        c.rect(492, yy - 4, 9, 9, fill=0, stroke=1)
        yy = draw_wrapped(c, item, 510, yy, 232, size=8.6, leading=10) - 10
    c.setFillColor(HexColor("#E8F5F2"))
    c.roundRect(42, 88, 718, 176, 12, fill=1, stroke=0)
    c.setFillColor(DARK_TEAL)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(60, 238, "THREAD RULES")
    rules = [
        "Install inserts only after the matching coupon passes. Heat-set square; never chase a tilted insert with more heat.",
        "Use washers and locknuts on metal load paths. Printed threads are not acceptable for axles, motors, carrying, battery retention, or the E-stop.",
        "Start every screw by hand. Tighten split plates and panel screws in alternating passes so thin printed skins do not bow.",
        "Record final screw lengths after the first physical build and update the manifest before ordering a production hardware kit.",
    ]
    yy = 218
    for i, rule in enumerate(rules, start=1):
        c.setFillColor(TEAL)
        c.circle(64, yy - 3, 9, fill=1, stroke=0)
        c.setFillColor(white)
        c.setFont("Helvetica-Bold", 8)
        c.drawCentredString(64, yy - 6, str(i))
        yy = draw_wrapped(c, rule, 82, yy, 658, size=8.5, leading=10) - 7
    footer(c, page_no, "Fastener legend")
    c.showPage()


def plate_map_page(c: canvas.Canvas, page_no: int, plate_manifest: dict) -> None:
    page_header(c, "18", "P1S plate-to-stage map", "Keep each material/color group separate; the 3MF is editable, not pre-sliced G-code.", page_no)
    draw_image(c, IMAGE_DIR / "codex_robot_body_v1_p1s_plates.png", 30, 88, 470, 430)
    groups = [
        ("01-06", "Structural PETG", "Decks, tray, pods, head mechanism, seam plates"),
        ("07-11", "Cream PETG", "Head shell, body quadrants, fairings, neck"),
        ("12-20", "Shell/detail PETG", "Lid, fascia, panels, carriers, diffusers"),
        ("21-22", "Dark teal TPU", "Two-part lid reveal / gasket"),
        ("23-26", "Charcoal TPU", "Bumper quadrants and four tires"),
    ]
    x, y = 520, 500
    plate_count = len(plate_manifest["plates"])
    part_count = sum(len(plate["parts"]) for plate in plate_manifest["plates"])
    label(c, f"{plate_count} PLATES / {part_count} PARTS", x, y)
    y -= 34
    for plate_range, material, use in groups:
        c.setFillColor(CREAM)
        c.roundRect(x, y - 54, 242, 54, 8, fill=1, stroke=0)
        c.setFillColor(DARK_TEAL)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(x + 10, y - 17, f"PLATES {plate_range}")
        c.setFillColor(CHARCOAL)
        c.setFont("Helvetica-Bold", 8.5)
        c.drawString(x + 10, y - 31, material)
        draw_wrapped(c, use, x + 94, y - 18, 136, size=7.8, leading=9)
        y -= 64
    gate_banner(c, "Open the current 3MF in Bambu Studio, confirm P1S / 0.4 mm / Textured PEI, inspect every support and brim preview, and print the coupon suite before any full shell plate.")
    c.showPage()


def build_pdf() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    print_manifest = load_json(PRINT_MANIFEST, PRINT_MANIFEST_REGEN)
    plate_manifest = load_json(PLATE_MANIFEST, PLATE_MANIFEST_REGEN)
    c = canvas.Canvas(str(OUTPUT), pagesize=(PAGE_W, PAGE_H), pageCompression=1)
    c.setTitle("Codex Robot Body v1 - Illustrated Assembly Guide")
    c.setAuthor("Codex robot project")
    c.setSubject("P1S printing, mechanical assembly, wiring access, and safety gates")

    page = 1
    cover_page(c, page, plate_manifest); page += 1
    overview_page(c, page); page += 1
    instruction_page(c, page, "01", "Print and calibrate", "Coupon results set the large-part parameters.", ["codex_robot_body_v1_coupons.png", "codex_robot_body_v1_alignment_pilot.png"], "17 coupon parts; PETG and TPU production profiles; calipers; insert tool; sample M3/M2.5 hardware; 608 and 6807 bearings; production distribution cover and M2 stacking standoffs.", ["Print coupons in their production material and profile. Let every part cool before measuring.", "Select insert, clearance, bearing-seat, journal, wall, lap, pilot, bumper, and fairing stations from the notched datum.", "On the production deck, mount the orange distribution fit gauge with the specified lower/upper M2 standoffs. Fit the actual cover and verify screw start, foot seating, header opening, and zero bow.", "Update shared CAD parameters and rerun the complete export/validator pipeline before printing large plates or ordering the distribution PCB."], "Every selected station fits by hand as intended; the distribution gauge and cover seat cleanly; measurements are recorded; and the regenerated validator is green. The gauge is mechanical only, never an electrical test."); page += 1
    hardware_page(c, page, print_manifest); page += 1
    instruction_page(c, page, "03", "Join the split structure", "Pilots locate; screws clamp. Do not force the seams.", ["codex_robot_body_v1_split_joinery.png"], "4 shell quadrants; 4 shell plates; 2 tray halves; underside plate; 4 bumper quadrants; 4 bumper plates; 18 pilots; 44 M3 inserts and screws.", ["Dry-fit every pilot/recess pair. Deburr only high spots; do not enlarge one side by force.", "Join front/rear shell seams first, then both side plates. Tighten the eight screws per direction in alternating passes.", "Join tray halves with the underside plate. Join bumper quadrants while preserving the compliant perimeter and wheel reliefs.", "Engage the 12 mm lid lap and capture both TPU reveal halves before final lid screws."], "All seams close without whitening, rocking, proud exterior edges, blocked wheel arches, or trapped TPU."); page += 1
    instruction_page(c, page, "04", "Build the tray load paths", "Metal carries the load; plastic locates and protects.", ["codex_robot_body_v1_carry_interface.png", "codex_robot_body_v1_battery_interface.png"], "Split tray and underside plate; two 25 mm webbing loops; two deburred 92 x 28 x 2 mm metal plates; eight M4 bolts, 16 washers, eight locknuts; 117 x 92 mm BLF-1203AB cradle; four M3 screws; two 20 mm straps; nonconductive padding.", ["Feed each webbing loop through both rounded slots. Confirm no cut edge contacts the webbing.", "Clamp each loop under its metal plate with four M4 through-bolts. Both plates must bridge the tray seam.", "Install the cradle and padding. Seat the BLF-1203AB flat at 110 x 75 x 27 mm; all four pads and side/end locators must meet without rocking or wrapper pinch.", "Route both 20 mm straps and the separate Powerpole discharge/DC charge leads through the rear corridor. Do not bend either lead at the wrapper exit."], "The empty tray survives a gentle low lift. Loaded retention remains prototype-only until delivered lead fit, <=5.6 A sustained pack current, 45-minute runtime with 20% reserve, thermal/BMS behavior, and the padded low-lift test pass."); page += 1
    instruction_page(c, page, "05", "Install rear drive", "Use the metal bracket and hub as the structural drivetrain.", ["codex_robot_body_v1_drivetrain.png"], "2 Pololu #4867 MP motors; 2 #1569 brackets; 2 #1997 hubs; six 3 mm M3 spacers; motor face screws; eight wheel screws; PETG cores; TPU tires; pod covers.", ["Bolt each metal bracket through three spacers into the tray. Keep the encoder lead corridor open.", "Fasten the motor to the bracket; verify the D-shaft and hub set-screw engagement before installing the wheel core.", "Bolt each core to its hub, seat the TPU tire and trim ring, then install the removable pod cover.", "Turn each wheel by hand and verify encoder direction before applying power."], "Purchased revisions, screw lengths, wheel retention, <=0.45 A steady per motor on target surfaces, temperature, encoder direction, obstruction response, and deterministic cutoff pass on the bench."); page += 1
    instruction_page(c, page, "06", "Install front idlers", "Follow the exploded stack from inboard circlip to outboard trim ring.", ["codex_robot_body_v1_front_idler.png"], "2 pods; 4 x 608 bearings; 4 printed bearing rings; 2 x 64.5 mm grooved 8 mm steel shafts; 2 DSH-8 circlips; 2 steel washers; 4 metal spacer tubes; 2 Pololu #2693 hubs; 12 M3 wheel screws; eight M2.5 retainer screws.", ["Confirm each shaft groove is 7.54-7.60 mm diameter x 0.90 mm wide with at least 0.60 mm edge margin. Deburr it; never grind a groove into an assembled pod.", "Seat two cooled, coupon-approved 608 bearings in each pod. Install both flush printed outer-race rings with four M2.5 screws per pod.", "From inboard to outboard, slide on the DSH-8 circlip, 8 x 15 x 2 washer, inner bearing, 12 x 8 x 14 spacer, outer bearing, 10 x 8 x 19 spacer, and #2693 hub.", "Tighten both hub set screws, fasten the PETG core with six M3 screws, then seat the TPU tire and teal trim ring. Bolt the pod to its four-point tray pad and spin by hand."], "The circlip is fully seated, both hub set screws engage the shaft, axial play is controlled without bearing preload, and no plastic thread or friction fit retains the axle. Loaded skid-turn testing remains pending."); page += 1
    instruction_page(c, page, "07", "Assemble the safety bumper", "The TPU moves; six rigid PETG plates and NC switches stay fixed.", ["codex_robot_body_v1_bumper_interface.png"], "6 Omron D2HW-C202MR switches; 6 PETG plates; 12 tray screws/inserts; 12 switch screws; TPU bumper; continuity meter.", ["Bolt each NC switch to its PETG plate and strain-relieve the molded side lead.", "Fasten every plate upward into two blind tray inserts. The TPU must not be clamped by these screws.", "With motor power disconnected, verify 0.4 mm rest gap, no preload, opening by 2.0 mm, rigid-stop contact near 2.4 mm, and rebound in all six zones.", "Prove a broken wire reads as stop before connecting the motor branch."], "All six zones and broken-wire cases cut the deterministic motion-enable path. This is a red safety gate.", RED); page += 1
    instruction_page(c, page, "08", "Mount controller and safety MCU", "Keep Linux control and deterministic stop hardware mechanically serviceable.", ["codex_robot_body_v1_motor_controller.png", "codex_robot_body_v1_safety_mcu.png"], "Controller plate; four 5 mm M3 metal spacers; Cytron MDDS10; four 6 mm M3 board standoffs; Pico 2 shelf; four shelf standoffs; four 6 mm M2 Pico standoffs.", ["Install the lower plate on four metal spacers above the carry doubler.", "Mount the MDDS10 with terminals facing robot-front; preserve underside-pin, terminal, and cooling clearances.", "Install the separate safety shelf and Pico 2. Keep micro-USB, SWD, headers, watchdog, and NC-input wiring accessible."], "Polarity, terminal bend, cooling, watchdog, NC inputs, and motor-cut output are bench-tested with the motor branch fused and wheels lifted."); page += 1
    instruction_page(c, page, "09", "Build power deck and E-stop", "The E-stop de-energizes motor power independently of the Pi.", ["codex_robot_body_v1_power_deck.png", "codex_robot_body_v1_harness_routing.png", "codex_robot_body_v1_top_detail.png"], "145 x 116 mm deck; both Pololu regulators and seven M2 standoffs; SW60/metal carrier; distribution fit gauge; custom 40 x 21 mm PCB; 4 x 01550900M holders; Nano2 fuses TBD; 43045-1000/43025-1000 Micro-Fit pair; eight stacked M2 standoffs; printed cover; strain strap; IDEC XW1E.", ["Mount both regulators on metal standoffs. Keep the 5 V Pi and 6 V servo rails separate.", "Attach the SW60 to its metal carrier, then through-bolt the carrier to the deck. Printed plastic must not carry stud-lug torque.", "Before ordering the PCB, mount the orange fit gauge on four 4 mm lower plus four 3 mm upper M2 standoffs. Fit the production cover; reject blocked screws, header contact, wall rub, or bow.", "Replace the gauge with the reviewed PCB. Connect the latched harness, strap its first bend, add the cover, and route signal/audio/sensors left while fused switched power/motors stay right. Keep the feeder fuse and contactor-cut motor branch outside this board.", "Install the keyed E-stop panel, legend, purchased nut, and reinforced backing before deck access closes."], "Before power: the fit gauge and cover pass mechanically, and electrical review approves PCB copper, source/branch fuse values, contacts/wires/crimps, labels, selective short clearing, thermal behavior, SW60 coil/suppression, polarity, reset, and dual-NC cutoff.", RED); page += 1
    instruction_page(c, page, "10", "Install audio and top services", "Keep amplified speaker leads short and every acoustic path open.", ["codex_robot_body_v1_audio_interface.png", "codex_robot_body_v1_top_detail.png"], "Mic cradle; two speaker plates; 2 Adafruit #3006 MAX98357A boards; four 6 mm M2 standoffs and screws; purchased mic/speakers; cable strain plate; vent inlay; lid and reveal.", ["Buy and measure one current #3006 board. Verify its supplied terminal, chosen header/direct-wire stack, screwdriver travel, and speaker-wire bend against the provisional fit corridors.", "Mount one amp component-side-down beneath each speaker plate: signal edge inward, terminal edge outward. Share BCLK/LRCLK/DIN and configure SD/MODE for left and right.", "Attach the mic cradle and populated speaker plates to their independent roof bosses; verify every grille slot and service tool path remains open.", "Seat the vent inlay, tighten its four split-bridging screws, and install the cable strain plate with every tie point accessible."], "One-board fit passes before buying the second; then both channels pass polarity, shutdown, current, heat, noise, grille-rattle, channel-assignment, and lid-off service tests."); page += 1
    instruction_page(c, page, "11", "Populate fascia and expression", "Install boards on carriers before the carriers enter the shell.", ["codex_robot_body_v1_led_interface.png", "codex_robot_body_v1_electronics_fit.png"], "4 Adafruit 5975 NeoPixel breakouts; eight M2 screws, spacers, washers, locknuts; four JST-SH harnesses; front and side ToF pods; fascia; four M2.5 carrier screws.", ["Bolt each NeoPixel board to its carrier through two 3 mm-OD spacers. Head boards rotate 90 degrees; front boards remain upright.", "Connect JST-SH plugs and prove latch/finger/first-bend clearance before installing the module.", "Mount both front ToF pods to the fascia, then install the populated status carriers with the shared fascia screws.", "Install side ToF pods and keep all four light and sensor paths open."], "One purchased board passes M2 fit, cable insertion/removal, fused 5 V current, brightness cap, diffuser hotspot/color, camera reflection, and software-off tests before buying all four."); page += 1
    instruction_page(c, page, "12", "Build pan bearing and neck", "The 6807 carries head weight; the servo supplies rotation only.", ["codex_robot_body_v1_head_mechanism.png"], "6807-2RS bearing; keyed fixed carrier; rotating neck journal and shoulder; four-screw lower retainer; D85MG pan servo; R-ML24 horn; flat ribbon harness.", ["Select the cooled 6807 seat and journal coupon stations. Press only the outer ring into the fixed carrier.", "Pass the journal through the inner ring, seat the upper shoulder, and tighten the four-screw retainer without preload.", "Install the pan servo and horn connection. Route the flat cable through the hollow neck with slack for both pan limits.", "Rotate by hand before powering; the bearing, not the servo spline, must carry axial/radial load."], "Bearing fits are smooth, retainer has no axial preload, cable drag is measured, and the regulated servo rail survives repeated motion."); page += 1
    instruction_page(c, page, "13", "Build tilt head and camera", "Assemble the active and passive pivots before closing the head.", ["codex_robot_body_v1_head_detail.png"], "Fixed yoke; D85MG tilt servo; R-ML24 horn; active adapter; MF84ZZ bearing; 92981A143 shoulder screw; Camera Module 3 Wide and carrier; faceplate; rear cover; eye modules. Refer to the preceding exploded mechanism page for the pivot stack.", ["Bolt the yoke to the neck flange without pinching the cable bundle.", "Install the tilt servo and active adapter on the right; install the passive bearing cartridge and shoulder screw on the left without axial clamp.", "Mount the camera and route its ribbon through the lower notch. Install both populated eye carriers from the rear.", "Fit faceplate and rear cover, then hand-sweep the complete head through every pan/tilt limit."], "Measured head mass/torque, cable drag, backlash, heat, camera corners/focus/reflections, and all sampled motion poses pass."); page += 1
    instruction_page(c, page, "14", "Fit rear charge, service, and mute", "Three removable cartridges; none may expose or authorize motor power.", ["codex_robot_body_v1_rear_service.png"], "Rear frame; EN2P3M20 charge cartridge and EN2C3F20G2 cord mate; BPC-1502DC charger adapter; center 35RASMT5CHNTRX UART cartridge/PCB/L-carrier; PVB3F230SS311 mute cartridge; six M2.5 frame inserts/screws; removable harnesses.", ["Install the EN2P3M20 at rear-left with its purchased nut. Two contacts go only to isolated charge +/-; the third is protected CHARGER_PRESENT. Expose no battery output.", "Fit the protected UART jack/PCB/carrier at center. Use TX, RX, SERVICE_DETECT, and ground only; expose no power, audio, motor-enable, safety bypass, or RS-232 levels.", "Fit the PVB3 at rear-right. Route fused mic 5 V to LISTEN; route MUTE to its red ring/resistor and protected state input. Prove capture loss with software stopped.", "Install all six frame inserts and cartridges. Test polarity, insertion shorts, charger/service motion inhibit, explicit reset, no automatic restart, privacy state, strain relief, and external removal. Mate/unmate EN2 only with charger AC removed."], "Purchased parts fit; charger insertion de-energizes motor enable/SW60 and unplugging never restarts motion; UART protection and MUTE capture loss pass; all cartridges remain externally removable.", RED); page += 1
    instruction_page(c, page, "15", "Close shell and install bumper", "Close only after every hidden connector has a service plan.", ["codex_robot_body_v1_exploded.png", "codex_robot_body_v1_assembled.png"], "Populated shell; base tray; four shell screws/inserts; lid and reveal; fairing halves; modular rear frame; complete TPU bumper; head/neck stack.", ["Lower the shell over the tray locating lip while watching harnesses, carry loops, battery straps, and wheel/pod clearance.", "Drive four M3 shell screws upward through the tray. Tighten evenly; do not pull a warped shell into alignment with torque.", "Install fairing halves in their flush recesses, then lid/reveal, rear frame and cartridges, vent, E-stop operator, and head stack.", "Fit the TPU bumper last and verify it floats around the rigid body with its designed clearance."], "No harness is pinched, all service cartridges remain removable, wheels spin, bumper rebounds, and the E-stop operates freely."); page += 1
    instruction_page(c, page, "16", "First power and stop tests", "Commission on blocks with wheels clear of the floor.", ["codex_robot_body_v1_electronics_fit.png"], "Fused bench supply; current measurement; continuity meter; physical E-stop; six bumper zones; watchdog fixture; BLF-1203AB and BPC-1502DC; fire-safe battery area; wheel blocks.", ["Power logic first with motor power isolated. Verify polarity, idle current, regulators, Pico heartbeat, local stop/mute/status, audio, camera, sensors, and LEDs.", "With charger AC removed, insert EN2: CHARGER_PRESENT must de-energize motor enable/SW60. Remove it and prove motion still needs explicit reset.", "Energize the motor branch with wheels lifted. Verify direction and encoder sign at the lowest bounded command.", "Trigger E-stop, every bumper, broken wire, watchdog timeout, Pi crash, Pico reset, obstruction, and low voltage. Every case must fail stopped.", "Then measure full/low-charge turns on target floors: <=0.45 A steady per motor, <=5.6 A sustained pack current, temperatures acceptable, and no BMS trip or unsafe restart."], "No software, network service, Pi state, charger state, or Codex command can bypass the physical stop chain or cause automatic restart.", RED); page += 1
    instruction_page(c, page, "17", "Final inspection and records", "A successful prototype produces measurements, not just a cute robot.", ["codex_robot_body_v1_assembled.png"], "Torque/inspection log; coupon measurements; delivered-part dimensions; wiring diagram; fuse list; battery/charger records; current/runtime/temperature logs; test results; updated CAD parameters and guide revision.", ["Record final screw lengths, insert settings, bearing stations, mass, center of gravity, per-motor/pack current, runtime, temperatures, cable slack, and failures.", "Photograph every hidden wiring layer before closure and label both ends of every serviceable harness.", "Perform the low-height loaded carry test, full/low-charge skid turns on rugs/carpet/hard floor, 45-minute mixed use with 20% reserve, repeated head motion, and thermal soak under supervision.", "Update the CAD, manifests, BOM, and this guide before calling the next print a revision-controlled build."], "All unresolved gates remain visibly open in the records. Prototype success is not permission for unattended household operation."); page += 1
    plate_map_page(c, page, plate_manifest)

    c.save()
    print(f"ASSEMBLY_GUIDE_WRITTEN pages={page} output={OUTPUT}")


if __name__ == "__main__":
    build_pdf()
