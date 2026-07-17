"""Generate the v2 assembly guide: LEGO-style, picture-first, ages 10+.

Every step page is a big render (from cad/blender/render_assembly_steps_v2.py)
with a parts strip of thumbnails and at most one short sentence — a child
should be able to build the body from the pictures alone. Grown-up steps
(heat-set inserts, wiring, the E-stop) carry a red badge. Fastener counts
come from the live inventory so the guide cannot drift from the model.

Run the v2 chain and both render passes first, then:
    .venv-cad/bin/python docs/generate_assembly_guide_v2.py
Output: output/pdf/codex_robot_body_v2_assembly_guide.pdf
Verify pages with pypdfium2 (poppler is not installed here).
"""

from __future__ import annotations

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
IMG = ROOT / "docs" / "images"
GUIDE_IMG = IMG / "guide_v2"
OUT = ROOT / "output" / "pdf" / "codex_robot_body_v2_assembly_guide.pdf"

CREAM = (0.97, 0.94, 0.88)
TEAL = (0.04, 0.51, 0.57)
DARK = (0.13, 0.13, 0.14)
RED = (0.80, 0.10, 0.08)
CHIP = (0.90, 0.86, 0.78)

SCREW_COUNT = {j.name: len(j.positions) for j in inv.JOINTS}

# (image, title, sentence, [(thumb, count), ...], screws, grown_up)
STEPS = [
    ("step_01_tray", "Start with the floor", "Put the big tray flat on your table. This is the bottom of your robot.",
     [("tray_v2", 1)], 0, False),
    ("step_02_inserts", "Grown-up: melt in the brass inserts", "A grown-up uses a soldering iron to press a brass insert into every gold spot, flat and straight.",
     [("px_insert", 24)], 0, True),
    ("step_03_motors", "Drop in the motors", "Lay each motor in its cradle, put the little cap on top, and screw it down.",
     [("px_motor_L", 2), ("motor_cap_v2", 2)], SCREW_COUNT["motor_caps"], False),
    ("step_04_wheels_bench", "Make the wheels", "Stretch a rubber tire onto each of the four wheels.",
     [("rear_wheel_v2", 2), ("front_wheel_v2", 2), ("tire_v2", 4)], 0, False),
    ("step_05_front_pods", "Bolt on the front legs", "Screw both front pods to the tray. Their round pegs are the front axles.",
     [("front_pod_left_v2", 2)], SCREW_COUNT["front_pods"], False),
    ("step_06_wheels_on", "Put the wheels on", "Back wheels push onto the motor shafts, one clamp screw each. Front wheels spin on the pegs: washer first, then screw.",
     [("rear_wheel_v2", 2), ("front_wheel_v2", 2), ("printed_washer_v2", 2)],
     SCREW_COUNT["rear_wheel_clamps"] + SCREW_COUNT["front_axle_retainers"], False),
    ("step_07_tower", "Build the brain tower", "Screw the tower down, then set the purple motor board on its posts.",
     [("controller_tower_v2", 1), ("px_mdds10", 1)], SCREW_COUNT["controller_tower_base"], False),
    ("step_08_pi", "Add the computer", "The green Raspberry Pi sits on the tower's top shelf.",
     [("px_pi", 1)], 0, False),
    ("step_09_battery", "Strap in the battery", "Soft pad down first, battery on top, then the clamp bar holds it tight.",
     [("battery_pad_frame_v2", 1), ("px_battery", 1), ("battery_clamp_v2", 1)], SCREW_COUNT["battery_clamp"], False),
    ("step_10_pico", "Add the safety helper", "This tiny green board is the robot's reflexes. Clamp it gently.",
     [("px_pico", 1), ("pico_clamp_v2", 1)], SCREW_COUNT["pico_clamp"], False),
    ("step_11_relay", "Grown-up: the power relay", "A grown-up mounts the relay. Every wire in this robot is grown-up work.",
     [("px_relay", 1)], 0, True),
    ("step_12_deck", "Put on the power deck", "The deck is a shelf: fuse box on top, the two small green boards hang underneath.",
     [("deck_v2", 1), ("px_fuse", 1), ("px_reg1", 2)], SCREW_COUNT["deck_towers"], False),
    ("step_13_speakers", "Speakers and wall-sensing eyes", "Speakers rest on their shelves, little blue distance boards behind their windows. Clamp bars hold them.",
     [("px_speaker_L", 2), ("px_tof_L", 2), ("speaker_clamp_v2", 2), ("tof_clamp_v2", 2)],
     SCREW_COUNT["speaker_clamps"] + SCREW_COUNT["tof_clamps"], False),
    ("step_14_shell", "Lower the body shell", "Like a turtle shell! Four screws go up into it from underneath.",
     [("shell_v2", 1)], SCREW_COUNT["shell_tray"], False),
    ("step_15_bumpers", "Clip on the bumpers", "The soft black bumpers wrap the bottom, front and back.",
     [("bumper_front_v2", 2)], 0, False),
    ("step_16_panels", "Snap in the face and back panels", "The dark panels click into the front and the back.",
     [("fascia_v2", 1), ("rear_panel_v2", 1)], 0, False),
    ("step_17_lid", "Grown-up: the lid and the BIG RED BUTTON", "A grown-up wires the red emergency stop into the lid, adds the microphone, and screws the lid down.",
     [("lid_v2", 1), ("px_estop_cap", 1), ("px_mic", 1), ("mic_cradle_v2", 1)],
     SCREW_COUNT["lid_shell"] + SCREW_COUNT["mic_cradle"], True),
    ("step_18_neck", "Grow the neck", "The neck slides through the lid and the collar twists on underneath to lock it.",
     [("neck_v2", 1), ("bayonet_collar_v2", 1), ("px_servo", 1)], 0, False),
    ("step_19_head", "Build the head", "The head shell goes over the yoke; the camera peeks out the front; the little plate closes the bottom.",
     [("head_shell_v2", 1), ("yoke_v2", 1), ("head_pan_plate_v2", 1), ("px_camera", 1), ("tilt_bushing_v2", 1)],
     1, False),
    ("step_20_face", "Give it a face", "The face panel presses into place, with the glowing eye bar behind it. Say hi!",
     [("head_faceplate_v2", 1), ("eye_diffuser_bar_v2", 1), ("status_diffuser_bar_v2", 1)], 0, False),
]

PRINTED_BOX = [
    ("tray_v2", "floor tray", 1), ("shell_v2", "body shell", 1), ("lid_v2", "teal lid", 1),
    ("bumper_front_v2", "bumpers", 2), ("fascia_v2", "face panel", 1), ("rear_panel_v2", "back panel", 1),
    ("deck_v2", "power deck", 1), ("controller_tower_v2", "brain tower", 1),
    ("rear_wheel_v2", "back wheels", 2), ("front_wheel_v2", "front wheels", 2), ("tire_v2", "tires", 4),
    ("front_pod_left_v2", "front pods", 2), ("motor_cap_v2", "motor caps", 2),
    ("battery_clamp_v2", "battery bar", 1), ("battery_pad_frame_v2", "battery pad", 1),
    ("pico_clamp_v2", "little clamp", 1), ("speaker_clamp_v2", "speaker bars", 2),
    ("tof_clamp_v2", "sensor bars", 2), ("mic_cradle_v2", "mic ring", 1),
    ("head_shell_v2", "head", 1), ("head_faceplate_v2", "face", 1), ("neck_v2", "neck", 1),
    ("bayonet_collar_v2", "neck lock", 1), ("yoke_v2", "head yoke", 1),
    ("head_pan_plate_v2", "head base", 1), ("tilt_bushing_v2", "tilt bushing", 1),
    ("eye_diffuser_bar_v2", "eye glow bar", 1), ("status_diffuser_bar_v2", "light bar", 1),
    ("printed_washer_v2", "washers", 6),
]
ELECTRONICS_BOX = [
    ("px_pi", "Raspberry Pi 5"), ("px_mdds10", "motor board"), ("px_pico", "safety board"),
    ("px_motor_L", "motors x2"), ("px_battery", "battery"), ("px_fuse", "fuse box"),
    ("px_relay", "relay"), ("px_reg1", "power boards x2"), ("px_estop_cap", "BIG RED BUTTON"),
    ("px_mic", "microphone"), ("px_speaker_L", "speakers x2"), ("px_tof_L", "distance eyes x4"),
    ("px_servo", "neck motors x2"), ("px_camera", "camera"),
]


def bg(c, color=CREAM):
    c.setFillColorRGB(*color)
    c.rect(0, 0, W, H, stroke=0, fill=1)


def badge(c, x, y, w, text, fill=TEAL, size=12):
    c.setFillColorRGB(*fill)
    c.roundRect(x, y, w, 0.34 * inch, 0.17 * inch, stroke=0, fill=1)
    c.setFillColorRGB(1, 1, 1)
    c.setFont("Helvetica-Bold", size)
    c.drawCentredString(x + w / 2, y + 0.1 * inch, text)


def image(c, path, x, y, w, h):
    if path.exists():
        c.drawImage(str(path), x, y, width=w, height=h, preserveAspectRatio=True,
                    anchor="c", mask="auto")


def parts_strip(c, items, screws, y):
    c.setFillColorRGB(*CHIP)
    c.roundRect(0.4 * inch, y, W - 0.8 * inch, 1.28 * inch, 0.12 * inch, stroke=0, fill=1)
    x = 0.55 * inch
    for thumb, count in items:
        image(c, GUIDE_IMG / f"thumb_{thumb}.png", x, y + 0.24 * inch, 0.92 * inch, 0.92 * inch)
        c.setFillColorRGB(*DARK)
        c.setFont("Helvetica-Bold", 13)
        c.drawString(x + 0.94 * inch, y + 0.56 * inch, f"x{count}")
        x += 1.42 * inch
    if screws:
        image(c, GUIDE_IMG / "thumb_px_screw.png", x, y + 0.24 * inch, 0.8 * inch, 0.8 * inch)
        c.setFillColorRGB(*DARK)
        c.setFont("Helvetica-Bold", 13)
        c.drawString(x + 0.84 * inch, y + 0.62 * inch, f"x{screws}")
        c.setFont("Helvetica", 9)
        c.drawString(x + 0.84 * inch, y + 0.44 * inch, "M3 screws")


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    c = pdfcanvas.Canvas(str(OUT), pagesize=PAGE)
    total = 4 + len(STEPS) + 1

    # Cover.
    bg(c)
    image(c, IMG / "codex_robot_body_v2_assembled.png", W * 0.42, 0.35 * inch, W * 0.55, H - 0.9 * inch)
    c.setFillColorRGB(*TEAL)
    c.setFont("Helvetica-Bold", 44)
    c.drawString(0.6 * inch, H - 1.5 * inch, "CODEX")
    c.drawString(0.6 * inch, H - 2.15 * inch, "ROVER BEAN")
    c.setFillColorRGB(*DARK)
    c.setFont("Helvetica-Bold", 19)
    c.drawString(0.62 * inch, H - 2.75 * inch, "Robot Body Builder's Guide")
    c.setFont("Helvetica", 13)
    c.drawString(0.62 * inch, H - 3.15 * inch, "You build it with pictures. One tool. No glue.")
    x = 0.62 * inch
    for label, wd in (("AGES 10+", 1.1), ("39 PRINTED PARTS", 1.9), ("1 HEX KEY", 1.25), ("GROWN-UP HELPS", 1.8)):
        badge(c, x, H - 3.85 * inch, wd * inch, label,
              fill=RED if label == "GROWN-UP HELPS" else TEAL)
        x += (wd + 0.16) * inch
    c.setFillColorRGB(*DARK)
    c.setFont("Helvetica", 10)
    c.drawString(0.62 * inch, 0.5 * inch,
                 "v2 printed-only body - the grown-up pages and the release gates at the back are part of the kit.")
    c.showPage()

    # What you printed.
    bg(c)
    c.setFillColorRGB(*TEAL)
    c.setFont("Helvetica-Bold", 26)
    c.drawString(0.6 * inch, H - 0.75 * inch, "What you printed")
    cols, cw, ch = 8, 1.28 * inch, 1.5 * inch
    for i, (thumb, label, qty) in enumerate(PRINTED_BOX):
        gx = 0.5 * inch + (i % cols) * cw
        gy = H - 1.35 * inch - (i // cols + 1) * ch
        image(c, GUIDE_IMG / f"thumb_{thumb}.png", gx, gy + 0.36 * inch, 1.1 * inch, 1.05 * inch)
        c.setFillColorRGB(*DARK)
        c.setFont("Helvetica-Bold", 9.5)
        c.drawCentredString(gx + 0.58 * inch, gy + 0.22 * inch, f"{label}  x{qty}")
    c.showPage()

    # Electronics box.
    bg(c)
    c.setFillColorRGB(*TEAL)
    c.setFont("Helvetica-Bold", 26)
    c.drawString(0.6 * inch, H - 0.75 * inch, "The electronics box")
    badge(c, W - 3.55 * inch, H - 0.82 * inch, 2.95 * inch, "A GROWN-UP HANDLES ALL WIRES", fill=RED, size=10)
    cols, cw, ch = 7, 1.45 * inch, 1.85 * inch
    for i, (thumb, label) in enumerate(ELECTRONICS_BOX):
        gx = 0.55 * inch + (i % cols) * cw
        gy = H - 1.4 * inch - (i // cols + 1) * ch
        image(c, GUIDE_IMG / f"thumb_{thumb}.png", gx, gy + 0.4 * inch, 1.25 * inch, 1.25 * inch)
        c.setFillColorRGB(*DARK)
        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(gx + 0.66 * inch, gy + 0.22 * inch, label)
    c.showPage()

    # Tools & hardware.
    bg(c)
    c.setFillColorRGB(*TEAL)
    c.setFont("Helvetica-Bold", 26)
    c.drawString(0.6 * inch, H - 0.75 * inch, "Tools and hardware")
    screws, inserts = inv.fastener_tally()
    rows = (
        ("thumb_px_screw.png", f"M3 x 8 screws  x{screws}", "Every screw in the robot is this exact screw."),
        ("thumb_px_insert.png", f"Brass inserts  x{inserts}", "A grown-up melts these in with a soldering iron."),
    )
    for i, (thumb, label, note) in enumerate(rows):
        gy = H - 2.5 * inch - i * 1.9 * inch
        image(c, GUIDE_IMG / thumb, 0.8 * inch, gy, 1.5 * inch, 1.5 * inch)
        c.setFillColorRGB(*DARK)
        c.setFont("Helvetica-Bold", 17)
        c.drawString(2.6 * inch, gy + 0.9 * inch, label)
        c.setFont("Helvetica", 13)
        c.drawString(2.6 * inch, gy + 0.55 * inch, note)
    c.setFillColorRGB(*TEAL)
    c.roundRect(0.8 * inch, H - 6.7 * inch, 1.5 * inch, 0.55 * inch, 0.12 * inch, stroke=0, fill=1)
    c.setFillColorRGB(1, 1, 1)
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(1.55 * inch, H - 6.52 * inch, "2.5 mm")
    c.setFillColorRGB(*DARK)
    c.setFont("Helvetica-Bold", 17)
    c.drawString(2.6 * inch, H - 6.35 * inch, "One 2.5 mm hex key")
    c.setFont("Helvetica", 13)
    c.drawString(2.6 * inch, H - 6.68 * inch, "It fits every screw. That's the whole toolbox.")
    c.showPage()

    # Steps.
    for i, (img_name, title, sentence, items, screws, grown_up) in enumerate(STEPS, start=1):
        bg(c)
        c.setFillColorRGB(*(RED if grown_up else TEAL))
        c.circle(0.95 * inch, H - 0.85 * inch, 0.42 * inch, stroke=0, fill=1)
        c.setFillColorRGB(1, 1, 1)
        c.setFont("Helvetica-Bold", 30)
        c.drawCentredString(0.95 * inch, H - 0.99 * inch, str(i))
        c.setFillColorRGB(*DARK)
        c.setFont("Helvetica-Bold", 23)
        c.drawString(1.6 * inch, H - 0.97 * inch, title)
        if grown_up:
            badge(c, W - 2.7 * inch, H - 1.02 * inch, 2.15 * inch, "GROWN-UP STEP", fill=RED)
        parts_strip(c, items, screws, H - 2.65 * inch)
        image(c, GUIDE_IMG / f"{img_name}.png", 0.9 * inch, 0.72 * inch, W - 1.8 * inch, H - 3.55 * inch)
        c.setFillColorRGB(*DARK)
        c.setFont("Helvetica", 13.5)
        c.drawCentredString(W / 2, 0.42 * inch, sentence)
        c.showPage()

    # Finish page.
    bg(c)
    image(c, IMG / "codex_robot_body_v2_assembled.png", 0.6 * inch, 0.9 * inch, W * 0.5, H - 1.8 * inch)
    c.setFillColorRGB(*TEAL)
    c.setFont("Helvetica-Bold", 34)
    c.drawString(W * 0.55, H - 1.4 * inch, "You built a robot!")
    c.setFillColorRGB(*DARK)
    c.setFont("Helvetica", 13)
    for j, line in enumerate((
        "High five. Rover Bean's body is done.",
        "",
        "For the grown-ups, before ANY power or motion:",
        "- print and pass the 11 calibration coupons first,",
        "- check every purchased part's fit on delivery,",
        "- wire and test the E-stop, bumpers, and watchdog,",
        "- and follow every release gate in the plan docs.",
        "",
        "The robot must always fail stopped.",
    )):
        c.drawString(W * 0.55, H - (1.9 + j * 0.32) * inch, line)
    c.save()
    print(f"wrote {OUT} ({total} pages)")


if __name__ == "__main__":
    main()
