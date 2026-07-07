#!/usr/bin/env python3
"""Compose Blender concept renders into review images."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "images"
REFERENCE = OUT / "codex_body_finished_concept.png"
FRONT = OUT / "codex_body_blender_front_3q.png"
COMPARISON = OUT / "codex_body_blender_concept_comparison.png"
CONTACT = OUT / "codex_body_blender_iteration_contact_sheet.png"
REFINEMENT_CONTACT = OUT / "codex_body_blender_refinement_contact_sheet.png"


ITERATION_LABELS = [
    "01 blockout",
    "02 wider teal deck",
    "03 softer shell",
    "04 bumper wrap",
    "05 wheel fenders",
    "06 lower stance",
    "07 capsule head",
    "08 friendlier face",
    "09 real E-stop",
    "10 service details",
    "11 package fit",
    "12 matched pass",
]


REFINEMENT_LABELS = [
    "13 darker inset deck",
    "14 lower cream shell",
    "15 shaped hood inset",
    "16 recessed fascia",
    "17 bumper halo",
    "18 lower E-stop",
    "19 softer head bezel",
    "20 smaller eyes",
    "21 curved brows",
    "22 slimmer neck",
    "23 fender wrap",
    "24 refined match",
]


def font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in (
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ):
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def resize_to_height(image: Image.Image, height: int) -> Image.Image:
    return image.resize((int(image.width * height / image.height), height), Image.Resampling.LANCZOS)


def make_comparison() -> None:
    ref = resize_to_height(Image.open(REFERENCE).convert("RGB"), 760)
    cad = resize_to_height(Image.open(FRONT).convert("RGB"), 760)
    pad = 28
    title_h = 62
    canvas = Image.new("RGB", (ref.width + cad.width + pad * 3, 760 + title_h + pad), "#F6EFE5")
    canvas.paste(ref, (pad, title_h))
    canvas.paste(cad, (ref.width + pad * 2, title_h))
    draw = ImageDraw.Draw(canvas)
    label_font = font(20)
    draw.text((pad, 20), "Concept art reference", fill="#22242A", font=label_font)
    draw.text((ref.width + pad * 2, 20), "Latest Blender CAD concept render", fill="#22242A", font=label_font)
    canvas.save(COMPARISON)


def make_contact_sheet(
    output: Path,
    start_index: int,
    labels: list[str],
    title: str,
) -> None:
    thumbs: list[Image.Image] = []
    for offset, label in enumerate(labels):
        index = start_index + offset
        path = OUT / f"codex_body_blender_iter_{index:02d}.png"
        image = Image.open(path).convert("RGB")
        image.thumbnail((390, 270), Image.Resampling.LANCZOS)
        thumb = Image.new("RGB", (400, 315), "#F6EFE5")
        thumb.paste(image, ((400 - image.width) // 2, 36))
        draw = ImageDraw.Draw(thumb)
        draw.text((14, 10), label, fill="#22242A", font=font(18))
        thumbs.append(thumb)

    cols = 4
    rows = 3
    pad = 18
    title_h = 68
    canvas = Image.new("RGB", (cols * 400 + (cols + 1) * pad, rows * 315 + (rows + 1) * pad + title_h), "#EFE7DB")
    draw = ImageDraw.Draw(canvas)
    draw.text((pad, 22), title, fill="#22242A", font=font(24))
    for index, thumb in enumerate(thumbs):
        col = index % cols
        row = index // cols
        x = pad + col * (400 + pad)
        y = title_h + pad + row * (315 + pad)
        canvas.paste(thumb, (x, y))
    canvas.save(output)


def main() -> None:
    make_contact_sheet(
        CONTACT,
        1,
        ITERATION_LABELS,
        "Blender concept iteration loop: first 12 literal passes toward the body art",
    )
    make_contact_sheet(
        REFINEMENT_CONTACT,
        13,
        REFINEMENT_LABELS,
        "Blender concept refinement loop: second 12 literal passes toward the body art",
    )
    make_comparison()
    print("composed:")
    print(f"  {CONTACT.relative_to(ROOT)}")
    print(f"  {REFINEMENT_CONTACT.relative_to(ROOT)}")
    print(f"  {COMPARISON.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
