"""Generate the v2 assembly guide: print-first HTML -> PDF, ages 10+.

"Ages 10+" here (and the cover chip it produces) is D039's plain-language
bar — every instruction stays simple enough for a ten-year-old building
with an adult — not a consumer age grading or safety claim. Keep the copy
at that reading level; a real retail age label is a separate future
compliance decision.

Authors the complete builder's book as fixed-size HTML pages (11 x 8.5 in
landscape) designed like a professionally produced kit manual, then prints
it to PDF with headless Chrome. Content is generated from the live
artifacts — the printed-part registry, joint/fastener registries, the
Bambu plate manifest, and the proof manifest — plus the authored step
and wiring copy below, so the book cannot drift from the model.

Pages: cover with a real table of contents, the annotated "meet the
robot" spread, the how-to-read anatomy page, shopping (filament /
fasteners / electronics / tools), printing with Bambu Studio (plates +
proofs + a LEGO-style piece inventory), twenty assembly steps with
progress bars and checks, the electronics orientation page, the wiring
chapter with SVG power and signal maps, the first-checks page, and a
back cover. The design system: Avenir Next type, chapter thumb tabs,
hairline tables, and the cream/teal/lime robot palette.

Run the v2 chain and both render passes first, then:
    .venv-cad/bin/python docs/generate_assembly_guide_v2.py
Outputs:
    output/guide/codex_robot_body_v2_guide.html
    output/pdf/codex_robot_body_v2_assembly_guide.pdf
Verify pages with pypdfium2 (poppler is not installed here).
"""

from __future__ import annotations

import html
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "cad" / "python"))

import robot_body_v2_inventory as inv  # noqa: E402
from builder_release_catalog_v2 import (  # noqa: E402
    FASTENER_COUNT,
    FILAMENT_GROUPS,
    SHOP_ELECTRONICS,
    SHOP_FASTENERS,
    SHOP_FILAMENT,
)
from builder_release_v2 import RELEASE_ID, RELEASE_URL  # noqa: E402

IMG = ROOT / "docs" / "images"
GUIDE_IMG = IMG / "guide_v2"
RELEASE_QR = GUIDE_IMG / "builder_release_v2_qr.png"
STEP_ANNOTATIONS = json.loads((GUIDE_IMG / "step_annotations.json").read_text())
PLATES = json.loads((ROOT / "cad" / "bambu" / "codex_robot_body_v2_p1s_plates.json").read_text())
PROOF_PLATES = json.loads(
    (ROOT / "cad" / "bambu" / "codex_robot_body_v2_proofs_p1s_plates.json").read_text())
N_PLATES = len(PLATES["plates"])
N_PIECES = sum(pl["part_count"] for pl in PLATES["plates"])
INVENTORY_COUNTS = PLATES.get("inventory_counts", {})
N_FUNCTIONAL = INVENTORY_COUNTS.get("functional_installed", 40)
N_SPARES = INVENTORY_COUNTS.get("spares", 4)
N_OPTIONAL = INVENTORY_COUNTS.get("optional_cosmetics", max(0, N_PIECES - N_FUNCTIONAL - N_SPARES))
PROOFS = json.loads((ROOT / "cad" / "exports" / "v2" / "proofs" /
                      "codex_robot_body_v2_proofs_manifest.json").read_text())
PROOF_NOTES = {
    "proof_insert_m3": "Melt one insert into each of the three holes. The one that sits flush without squeezing out goo is your printer’s perfect fit.",
    "proof_joint_flange": "Screw the small plate onto the block with one screw. It should pull down tight with no wobble and no cracking.",
    "proof_joint_boss": "The partner block for the plate test above.",
    "proof_dbore_torque": "Push this onto a motor shaft and twist HARD — twice as hard as driving ever will. If it never slips, wheels are safe.",
    "proof_axle_stub": "Spin the ring on the peg a few hundred times with some pressure. It should stay smooth, not sloppy.",
    "proof_bushing_ring": "The spinning ring for the peg test above.",
    "proof_snap_pair": "Click the two pieces together and apart ten times. The little hook must survive and still hold on.",
    "proof_bayonet_pair": "Twist the ring onto the stub a quarter turn — it should lock with a nice click and not pull straight off.",
    "proof_switch_pocket": "Seat one bumper switch in the pocket: it must click when pressed and spring back, never jammed.",
    "proof_tire_fit": "Stretch the mini tire onto the mini wheel. Snug and even = your big tires will fit too.",
    "proof_pcb_clamp": "Rest the little green safety board on the pegs and screw the bar over it. Held gently, nothing bending.",
    "proof_pla_insert_shell": "Use your exact body PLA and record the insert temperature. No white stress marks, cracks, sink, tilt, or pull-through.",
    "proof_pla_shell_wall": "Check the wall, rounded edge, opening, and panel seat after a bump test, warm soak, and full cool-down.",
    "proof_pla_head_pivot": "Fit the insert and bushing, load it like the finished head, then check for cracks and growing wobble.",
    "proof_pla_snap_pair": "Print this in every candidate visible PLA. Click it ten times; it must still latch fully with no whitening or crack.",
    "proof_pla_optical": "Print once per translucent PLA family/color. Compare the three thicknesses for brightness, hot spots, heat, and camera flare.",
    "proof_lid_boundary_petg": "Print with the white PETG lid profile and mate it to the teal PLA tab. The blind socket must not crack.",
    "proof_lid_boundary_pla": "Snap into the white PETG proof ten times, warm it, and check that it still holds without rattling.",
}
PROOF_TITLES = {
    "proof_insert_m3": "Insert fit",
    "proof_joint_flange": "Screw joint",
    "proof_joint_boss": "Screw joint partner",
    "proof_dbore_torque": "Wheel grip",
    "proof_axle_stub": "Axle spin",
    "proof_bushing_ring": "Axle spin ring",
    "proof_snap_pair": "Snap click",
    "proof_bayonet_pair": "Bayonet twist",
    "proof_switch_pocket": "Switch pocket",
    "proof_tire_fit": "Tire stretch",
    "proof_pcb_clamp": "Board clamp",
    "proof_pla_insert_shell": "PLA insert boss",
    "proof_pla_shell_wall": "PLA shell wall",
    "proof_pla_head_pivot": "PLA head pivot",
    "proof_pla_snap_pair": "PLA snap",
    "proof_pla_optical": "PLA light test",
    "proof_lid_boundary_petg": "PETG lid socket",
    "proof_lid_boundary_pla": "PLA skin tab",
}
HTML_OUT = ROOT / "output" / "guide" / "codex_robot_body_v2_guide.html"
PDF_OUT = ROOT / "output" / "pdf" / "codex_robot_body_v2_assembly_guide.pdf"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

SCREWS = {j.name: len(j.positions) for j in inv.JOINTS}

# Red banner above a step's numbered moves, for holds the builder must see
# before starting (kept out of the <ol> so arrow numbers stay aligned).
STEP_NOTES = {
    "step_18_neck": "DELIVERED-ARM PROOF FIRST — the arm from your servo's bag must pass the horn-capture proof (chapter 2) before it goes in; the capture slot's sizes are provisional until real arms are measured.",
    "step_19_head": "DELIVERED-ARM PROOF FIRST — same hold as step 18; prove the bag arm in the capture proof before building the head.",
}

# Per-camera FRONT hint: rear-camera steps see the front on the far side.
FRONT_LABEL = {
    "step_03_motors": "&#8598; FRONT (far side)",
    "step_06_wheels_on": "&#8598; FRONT (far side)",
    "step_15_panels": "&#8601; FRONT",
    "step_04_wheels_bench": None,   # bench shot, no robot orientation
}


# Per-step corrections to the exported arrow set. "drop" prunes arrows (by the
# exported part name) whose projected landing sits on hidden geometry, under a
# detail panel, or duplicates a part that is already seated in the scene —
# verified page by page in the 2026-07-19 audit. "chips" adds small labeled
# tags at normalized (x%, y%) for scenes that need identification, not motion.
STEP_ARROW_TWEAKS = {
    # Single part lying flat + FRONT chip already on the page; both arrows
    # (tray, front-edge anchor) landed on empty table or the front notch.
    "step_01_tray": {"drop": {"tray_v2", "front_edge"}},
    # The robot-left pair's destinations hide behind the front skirt, so their
    # arrows dove off the tray onto the floor. The robot-right pair lands in
    # its cradle and the text says "each cradle".
    "step_03_motors": {"drop": {"motor_cap_v2", "px_motor_L"}},
    # Bench scene: the near pair are the BACK wheels (grid -Y toward camera).
    "step_04_wheels_bench": {"chips": [
        (27, 68, "BACK"), (57, 74, "BACK"), (29, 40, "FRONT"), (57, 36, "FRONT")]},
    # The robot-left pod is already seated; its arrow pointed at bare tray.
    "step_05_front_pods": {"drop": {"front_pod_left_v2"}},
    # The board's landing projects to the tray's front edge — implausible for
    # a part that rests on TOP of the popped tower. The tower arrow carries
    # the step.
    "step_07_tower": {"drop": {"px_mdds10"}},
    # Pad, battery, and clamp arrows are near-collinear (they land in one
    # vertical stack); three arrowheads buried each other. The pad-frame
    # arrow defines the bay; the battery and clamp visibly hover above it.
    "step_09_battery": {"drop": {"battery_clamp_v2", "px_battery"}},
    # Clamp + Pico arrows collapsed into one shaft; the Pico arrow remains.
    "step_10_pico": {"drop": {"pico_clamp_v2"}},
    # The floor pocket is fully occluded at this camera; the arrow landed on
    # the front wheel's face. The move text locates the pocket instead.
    "step_11_relay": {"drop": {"px_relay"}},
    # The deck's landing dot fell in the shadow gap between tray and wheel.
    "step_12_deck": {"drop": {"deck_v2"}},
    # The shell's tail and landing both projected onto the front wheel face.
    "step_13_shell": {"drop": {"shell_v2"}},
    # The two bumper arrows crossed mid-shell with landings on the white
    # wall; the halves visibly wrap from front and back on their own.
    "step_14_bumpers": {"drop": {"bumper_front_v2", "bumper_rear_v2"}},
    # The rear panel's arrow projects under the Detail B inset; the face
    # panel's was a degenerate stub onto the aperture. Both panels float
    # directly in front of their openings.
    "step_15_panels": {"drop": {"fascia_v2", "rear_panel_v2"}},
    # Both clamp-bar arrows chained visually and the clamps are the inset
    # panel's subject; the interior view carries the placement.
    "step_16_speakers": {"drop": {"speaker_clamp_v2", "tof_clamp_v2"}},
    # front_wheel_v2's arrow is buried under Detail A; rear_wheel_v2_m's tip
    # lands in the background gap between wheels. One exemplar arrow per
    # wheel type remains.
    "step_06_wheels_on": {"drop": {"front_wheel_v2", "rear_wheel_v2_m"}},
    # All three destinations stack in the same lid opening — the arrows piled
    # into one tangle. The "lid hidden" inset is the pointer for this step.
    "step_18_neck": {"drop": {"bayonet_collar_v2", "head_pan_plate_v2", "neck_v2"}},
    # The bushing arrow projects under the inset cards; the camera arrow tips
    # into the servo cluster. Both parts have dedicated detail panels.
    "step_19_head": {"drop": {"tilt_bushing_v2", "px_camera"}},
    # The eye bar's stub pointed at blank faceplate; the status bar renders
    # already seated, so its arrow reached into empty background.
    "step_20_face": {"drop": {"eye_diffuser_bar_v2", "status_diffuser_bar_v2"}},
}


def annotation_svg(step_key):
    """Magenta assembly arrows projected from the actual Blender scene.

    Glyphless on purpose: the unbroken line pairs a floating part with its
    landing ring, so nothing here can be mistaken for the numbered moves or
    the lettered detail panels."""
    tweaks = STEP_ARROW_TWEAKS.get(step_key, {})
    dropped = tweaks.get("drop", set())
    arrows = [a for a in STEP_ANNOTATIONS.get(step_key, [])
              if a.get("part") not in dropped]
    chips = tweaks.get("chips", [])
    if not arrows and not chips:
        return ""
    marker = f"arrow_{step_key}"
    bits = [
        '<svg class="step-annotations" viewBox="0 0 1100 850" '
        'preserveAspectRatio="none" aria-hidden="true">',
        f'<defs><marker id="{marker}" markerWidth="9" markerHeight="9" refX="7" refY="3.5" '
        'orient="auto" markerUnits="strokeWidth"><path d="M0,0 L0,7 L8,3.5 z" fill="#D41468"/>'
        '</marker></defs>',
    ]
    for arrow in arrows:
        tx, ty = arrow["tail"][0] * 11, arrow["tail"][1] * 8.5
        dx, dy = arrow["tip"][0] * 11, arrow["tip"][1] * 8.5
        vx, vy = dx - tx, dy - ty
        length = max((vx * vx + vy * vy) ** 0.5, 1.0)
        # Keep the line clear of the tail dot and the landing ring.
        sx, sy = tx + vx * 9 / length, ty + vy * 9 / length
        ex, ey = dx - vx * 16 / length, dy - vy * 16 / length
        bits.append(
            f'<line x1="{sx:.1f}" y1="{sy:.1f}" x2="{ex:.1f}" y2="{ey:.1f}" '
            f'stroke="#D41468" stroke-width="5" stroke-linecap="round" marker-end="url(#{marker})"/>'
            f'<circle cx="{tx:.1f}" cy="{ty:.1f}" r="7" fill="#D41468" stroke="#FFF9EE" stroke-width="2.5"/>'
            f'<circle cx="{dx:.1f}" cy="{dy:.1f}" r="11" fill="none" '
            f'stroke="#D41468" stroke-width="4"/>'
            f'<circle cx="{dx:.1f}" cy="{dy:.1f}" r="14.5" fill="none" '
            f'stroke="#FFF9EE" stroke-width="2.5"/>'
        )
    for cx, cy, label in chips:
        x, y = cx * 11, cy * 8.5
        w = 24 + 13 * len(label)
        bits.append(
            f'<rect x="{x - w / 2:.1f}" y="{y - 16:.1f}" width="{w}" height="32" rx="9" '
            'fill="#22231F" fill-opacity=".88"/>'
            f'<text x="{x:.1f}" y="{y + 6:.1f}" text-anchor="middle" fill="#FFF9EE" '
            f'font-size="17" font-weight="800" letter-spacing="1.5">{label}</text>'
        )
    bits.append("</svg>")
    return "".join(bits)


# Camera family per step render: "front" cameras face the robot (so the
# robot's RIGHT projects to the image's LEFT — like looking at a friend),
# "rear" cameras stand behind it (image left = robot left), and the pico
# camera is a side view whose horizontal axis is front-back, where an L/R
# badge would simply lie. Must match CAMS in render_assembly_steps_v2.py.
STEP_VIEW = {
    "step_03_motors": "rear",
    "step_06_wheels_on": "rear",
    "step_10_pico": "side",
}


def robot_axis_badge(step_key):
    view = STEP_VIEW.get(step_key, "front")
    if view == "side":
        return ""
    if view == "rear":
        return ('<div class="axisbadge"><span>L</span><b>&larr;</b><i>FRONT</i>'
                '<b>&rarr;</b><span>R</span></div>')
    return ('<div class="axisbadge"><span>R</span><b>&larr;</b><i>FRONT &middot; IT FACES YOU</i>'
            '<b>&rarr;</b><span>L</span></div>')


def technical_diagram(kind):
    """Small dimensioned sections for operations a perspective render hides."""
    common = ('<svg viewBox="0 0 520 310" style="width:100%;height:100%;display:block" '
              'aria-hidden="true"><rect width="520" height="310" fill="#F5EEE2"/>')
    end = "</svg>"
    if kind == "rear_well":
        return common + '''
          <rect x="70" y="42" width="300" height="226" rx="24" fill="#272724"/>
          <rect x="104" y="62" width="232" height="186" rx="18" fill="#4D4B46"/>
          <rect x="250" y="44" width="46" height="85" rx="18" fill="#E9DED0"/>
          <rect x="257" y="126" width="32" height="58" rx="7" fill="#C89B32"/>
          <rect x="264" y="176" width="18" height="76" rx="7" fill="#82817D"/>
          <rect x="252" y="238" width="42" height="18" rx="6" fill="#A9A8A3"/>
          <path d="M292 88 H368 M292 153 H368 M282 224 H368" stroke="#087A8C" stroke-width="3"/>
          <text x="376" y="92" font-size="13" font-weight="700" fill="#1F2828">7.2 mm tire port</text>
          <text x="376" y="157" font-size="13" font-weight="700" fill="#1F2828">deep insert seat</text>
          <text x="376" y="228" font-size="13" font-weight="700" fill="#1F2828">M3 tip on shaft flat</text>
          <text x="72" y="294" font-size="17" font-weight="700" fill="#087A8C">Nothing protrudes after assembly</text>
        ''' + end
    if kind == "rear_clamp":
        return common + '''
          <circle cx="170" cy="154" r="112" fill="#272724"/><circle cx="170" cy="154" r="78" fill="#4D4B46"/>
          <rect x="156" y="12" width="28" height="100" rx="12" fill="#E9DED0"/>
          <rect x="161" y="104" width="18" height="94" rx="7" fill="#8A8984"/>
          <path d="M170 198 V258 H310" stroke="#8A8984" stroke-width="26" fill="none"/>
          <path d="M170 237 H285" stroke="#F5EEE2" stroke-width="8"/>
          <text x="290" y="56" font-size="14" font-weight="700" fill="#1F2828">tool enters through tread</text>
          <path d="M278 62 H190" stroke="#087A8C" stroke-width="3"/>
          <text x="290" y="151" font-size="14" font-weight="700" fill="#1F2828">screw presses D-flat</text>
          <path d="M278 157 H190" stroke="#087A8C" stroke-width="3"/>
          <text x="290" y="246" font-size="14" font-weight="700" fill="#1F2828">motor shaft</text>
        ''' + end
    if kind == "front_washer":
        return common + '''
          <circle cx="208" cy="155" r="118" fill="#32312E"/>
          <circle cx="208" cy="155" r="57" fill="#4D4B46"/>
          <circle cx="208" cy="155" r="68" fill="none" stroke="#E9DED0" stroke-width="22"/>
          <circle cx="208" cy="155" r="79" fill="none" stroke="#22231F" stroke-width="2"/>
          <circle cx="208" cy="155" r="57" fill="none" stroke="#22231F" stroke-width="2"/>
          <circle cx="208" cy="155" r="13" fill="#8A8984"/>
          <path d="M129 42 H287 M129 34 V50 M287 34 V50" stroke="#087A8C" stroke-width="3"/>
          <text x="145" y="28" font-size="17" font-weight="700" fill="#087A8C">22 mm cap washer</text>
          <path d="M151 155 H265" stroke="#FFF9EE" stroke-width="3"/>
          <text x="312" y="121" font-size="14" font-weight="700" fill="#1F2828">washer overlaps</text>
          <text x="312" y="143" font-size="14" font-weight="700" fill="#1F2828">18.5 mm wheel bore</text>
          <path d="M302 137 H274" stroke="#087A8C" stroke-width="3"/>
          <text x="312" y="230" font-size="14" font-weight="700" fill="#1F2828">wheel remains free</text>
        ''' + end
    if kind == "bumper_section":
        return common + '''
          <rect x="42" y="44" width="260" height="168" rx="22" fill="#DED9CF"/>
          <rect x="172" y="170" width="94" height="46" rx="7" fill="#4B4A46"/>
          <rect x="122" y="184" width="54" height="18" rx="5" fill="#8B8983"/>
          <rect x="70" y="172" width="52" height="42" rx="8" fill="#F0C34A"/>
          <path d="M34 158 Q18 191 34 231 L89 255 H326 Q356 255 356 225 V204" fill="none" stroke="#242421" stroke-width="25"/>
          <path d="M96 203 H119" stroke="#D41468" stroke-width="4" marker-end="url(#tiny)"/>
          <defs><marker id="tiny" markerWidth="8" markerHeight="8" refX="7" refY="3.5" orient="auto"><path d="M0 0V7L8 3.5Z" fill="#D41468"/></marker></defs>
          <path d="M326 70 H305 M326 112 H305 M326 154 H305" stroke="#087A8C" stroke-width="3"/>
          <text x="330" y="74" font-size="14" font-weight="700" fill="#1F2828">0.4 mm rest gap</text>
          <text x="330" y="116" font-size="14" font-weight="700" fill="#1F2828">2.0 mm switch click</text>
          <text x="330" y="158" font-size="14" font-weight="700" fill="#1F2828">2.4 mm hard stop</text>
          <path d="M262 190 H326" stroke="#087A8C" stroke-width="3"/>
          <text x="330" y="194" font-size="14" font-weight="700" fill="#087A8C">button faces OUT</text>
          <path d="M148 194 Q136 240 210 288 H240" stroke="#087A8C" stroke-width="3" fill="none"/>
          <text x="246" y="292" font-size="14" font-weight="700" fill="#087A8C">lead exits IN</text>
        ''' + end
    if kind == "fascia_back":
        return common + '''
          <rect x="54" y="52" width="412" height="206" rx="18" fill="#292824"/>
          <rect x="95" y="94" width="78" height="82" rx="8" fill="#5F83D0"/>
          <rect x="347" y="94" width="78" height="82" rx="8" fill="#5F83D0"/>
          <circle cx="134" cy="135" r="12" fill="#141516" stroke="#DCE9F5" stroke-width="5"/>
          <circle cx="386" cy="135" r="12" fill="#141516" stroke="#DCE9F5" stroke-width="5"/>
          <rect x="188" y="194" width="54" height="30" rx="7" fill="#4C9B59"/>
          <rect x="278" y="194" width="54" height="30" rx="7" fill="#4C9B59"/>
          <path d="M134 85 V42 M386 85 V42 M215 229 V276 M305 229 V276" stroke="#087A8C" stroke-width="3"/>
          <text x="100" y="30" font-size="14" font-weight="700" fill="#1F2828">LEFT ToF</text>
          <text x="350" y="30" font-size="14" font-weight="700" fill="#1F2828">RIGHT ToF</text>
          <text x="182" y="52" font-size="13" font-weight="700" fill="#1F2828">lenses through low holes</text>
          <text x="115" y="300" font-size="14" font-weight="700" fill="#087A8C">status lights: arrows OUT, plugs IN</text>
        ''' + end
    if kind == "audio_section":
        return common + '''
          <rect x="42" y="46" width="430" height="220" rx="20" fill="#DED9CF"/>
          <rect x="78" y="78" width="210" height="88" rx="10" fill="#4B4944"/>
          <rect x="78" y="78" width="26" height="88" fill="#171817"/>
          <path d="M91 76 V52 M288 122 H360" stroke="#087A8C" stroke-width="3"/>
          <text x="8" y="40" font-size="14" font-weight="700" fill="#1F2828">grille OUT</text>
          <text x="364" y="118" font-size="14" font-weight="700" fill="#1F2828">magnet IN</text>
          <rect x="150" y="188" width="96" height="42" rx="7" fill="#397948"/>
          <rect x="250" y="191" width="58" height="36" rx="6" fill="#5F83D0"/>
          <path d="M198 232 V286 M279 230 V286" stroke="#087A8C" stroke-width="3"/>
          <text x="88" y="298" font-size="13" font-weight="700" fill="#1F2828">amp pocket + service loop</text>
          <text x="330" y="298" font-size="13" font-weight="700" fill="#1F2828">ToF lens OUT</text>
        ''' + end
    if kind == "estop_section":
        return common + '''
          <rect x="45" y="118" width="284" height="28" rx="8" fill="#D7D4CC"/>
          <rect x="45" y="94" width="284" height="20" rx="5" fill="#56C4C2"/>
          <rect x="155" y="38" width="72" height="70" rx="12" fill="#D52B20"/>
          <rect x="174" y="106" width="34" height="148" rx="9" fill="#30312F"/>
          <rect x="142" y="147" width="98" height="17" rx="6" fill="#9A9994"/>
          <rect x="137" y="171" width="108" height="32" rx="8" fill="none" stroke="#F0C34A" stroke-width="8"/>
          <rect x="138" y="232" width="52" height="47" rx="5" fill="#20211F"/>
          <rect x="194" y="232" width="52" height="47" rx="5" fill="#20211F"/>
          <path d="M250 257 H274" stroke="#087A8C" stroke-width="3"/>
          <text x="280" y="80" font-size="13" font-weight="700" fill="#1F2828">teal skin: cosmetic only</text>
          <text x="280" y="128" font-size="13" font-weight="700" fill="#1F2828">4 mm PETG lid clamps switch</text>
          <text x="280" y="178" font-size="13" font-weight="700" fill="#1F2828">nut + printed reinforcement</text>
          <text x="280" y="230" font-size="13" font-weight="700" fill="#1F2828">2 NC blocks</text>
          <text x="280" y="260" font-size="13" font-weight="700" fill="#087A8C">terminal corridor</text>
        ''' + end
    if kind == "status_bar":
        return common + '''
          <rect x="38" y="48" width="444" height="214" rx="24" fill="#E4E0D6"/>
          <rect x="76" y="102" width="368" height="76" rx="12" fill="#292824"/>
          <rect x="137" y="126" width="72" height="28" rx="7" fill="#DDFD73"/>
          <rect x="311" y="126" width="72" height="28" rx="7" fill="#DDFD73"/>
          <rect x="145" y="192" width="56" height="32" rx="7" fill="#438851"/>
          <rect x="319" y="192" width="56" height="32" rx="7" fill="#438851"/>
          <path d="M173 190 V160 M347 190 V160" stroke="#D41468" stroke-width="5"/>
          <text x="80" y="82" font-size="14" font-weight="700" fill="#1F2828">clip diffuser first</text>
          <text x="258" y="82" font-size="13" font-weight="700" fill="#1F2828">glow boards seat from behind — LATER</text>
          <text x="86" y="286" font-size="14" font-weight="700" fill="#087A8C">when their harness releases: LED arrows OUT, JST plugs IN</text>
        ''' + end
    raise KeyError(kind)
# Inset panels overlaid on a step's big picture: render name + caption.
INSETS = {
    "step_13_shell": ("step_13b_shell_inserts", "All 14 insert spots"),
}
EXTRA_PANELS = {
    "step_10_pico": [("step_10b_pico_close", "USB toward BACK; SWD toward FRONT; clamp touches blank PCB edges only")],
    "step_12_deck": [
        ("step_12b_regulators", "Detail A - underside: distinct 5 V and 6 V regulators"),
        ("step_12c_fuse", "Detail B - topside: covered fuse block and LEFT wire edge"),
    ],
    "step_14_bumpers": [("step_14b_switch_underside", "Detail A - 6 switches: buttons OUT, leads IN")],
    "step_15_panels": [("step_15b_rear_panel", "Detail B - rear: charge LEFT, blank center, mute RIGHT")],
    "step_16_speakers": [("step_16b_audio_close", "Detail A - speaker: grille OUT, magnet IN; clamp + ToF")],
    "step_17_lid": [
        ("step_17b_lid_inserts", "Detail A - lid flipped: the 2 mic bosses"),
        ("step_17c_estop_stack", "Detail B - full E-stop body, nut, and 2 NC blocks"),
    ],
    "step_18_neck": [
        ("step_18b_neck_cutaway", "Lid hidden: collar, cradle, servo, plate, horn"),
    ],
    "step_19_head": [
        ("step_19b_tilt_stack", "Tilt servo, horn, hard stops, passive bushing"),
        ("step_19c_camera", "Camera board, lens, and ribbon entrance"),
    ],
}
VECTOR_PANELS = {
    "step_04_wheels_bench": [("Rear wheel cutaway: port, deep insert, screw, shaft", "rear_well")],
    "step_06_wheels_on": [
        ("Detail A - rear wheel clamp path", "rear_clamp"),
        ("Detail B - front cap washer overlap", "front_washer"),
    ],
    "step_14_bumpers": [("Detail B - side section: rest, click, hard stop", "bumper_section")],
    "step_15_panels": [("Detail A - back of fascia: sensors and status lights", "fascia_back")],
    "step_16_speakers": [("Detail B - one-side orientation and wire exit", "audio_section")],
    "step_17_lid": [("Detail C - E-stop lid load path and terminal corridor", "estop_section")],
    "step_20_face": [("Detail - body status bar: diffuser, boards, plug direction", "status_bar")],
}
N_SCREWS, N_INSERTS = inv.fastener_tally()
if (N_SCREWS, N_INSERTS) != (FASTENER_COUNT, FASTENER_COUNT):
    raise RuntimeError(
        "builder_release_catalog_v2.FASTENER_COUNT drifted from the CAD joint registry"
    )

# Friendly names for parts (printed and purchased) used in strips and the
# piece inventory. Keys are registry/thumbnail base names.
PART_NAMES = {
    "tray_v2": "floor tray", "deck_v2": "power deck",
    "controller_tower_v2": "brain tower", "battery_clamp_v2": "battery clamp",
    "speaker_clamp_v2": "speaker clamp", "yoke_v2": "head yoke",
    "mic_cradle_v2": "mic cradle", "head_pan_plate_v2": "pan-servo plate",
    "pico_clamp_v2": "safety-board clamp", "front_pod_left_v2": "front pod (L)",
    "front_pod_right_v2": "front pod (R)", "motor_cap_v2": "motor cap",
    "tof_clamp_v2": "sensor clamp", "tilt_bushing_v2": "tilt bushing",
    "printed_washer_v2": "washer", "front_wheel_v2": "front wheel",
    "rear_wheel_v2": "back wheel", "shell_v2": "body shell",
    "head_shell_v2": "head shell", "bayonet_collar_v2": "neck collar",
    "neck_v2": "neck", "lid_v2": "lid", "head_faceplate_v2": "head face",
    "lid_skin_v2": "optional lid skin",
    "rear_panel_v2": "back panel", "fascia_v2": "face panel",
    "status_diffuser_bar_v2": "status light bar",
    "eye_diffuser_bar_v2": "eye light bar",
    "bumper_front_v2": "front bumper", "bumper_rear_v2": "back bumper",
    "battery_pad_frame_v2": "battery pad", "tire_v2": "tire",
    "px_insert": "brass inserts", "px_screw": "M3 screws",
    "px_motor_L": "gearmotors", "px_mdds10": "motor board",
    "px_pi": "Raspberry Pi", "px_battery": "battery", "px_relay": "relay",
    "px_fuse": "fuse block", "px_reg1": "regulators",
    "px_switch": "feeler switches", "px_tof_L": "distance boards",
    "px_speaker_L": "speakers", "px_estop_cap": "red button",
    "px_mic": "mic array", "px_servo": "D85MG servo (arm in its bag)", "px_camera": "camera",
    "px_pico": "Pico 2",
}
STRIP_NAME_OVERRIDES = {
    ("step_05_front_pods", "front_pod_left_v2"): "front pods",
    ("step_14_bumpers", "bumper_front_v2"): "bumpers",
    ("step_03_motors", "motor_cap_v2"): "motor caps",
}

# Chapter system: (tab label, accent color, TOC line). Page numbers are
# computed at assembly time.
CHAPTERS = [
    ("SHOP", "#B8892E", "Shop", "every spool, screw, and circuit board"),
    ("PRINT", "#0B6E84", "Print", "prototype plates, test parts, and a piece check"),
    ("BUILD", "#075365", "Build", "twenty steps from flat tray to finished body"),
    ("WIRE", "#C4230F", "Wire", "reference maps only — the harness is not released yet"),
    ("PLAY", "#74A22D", "Check &amp; play", "wake the brain, meet your copilot"),
]

# ---------------------------------------------------------------------------
# Authored content
# ---------------------------------------------------------------------------
SHOP_TOOLS = [
    ("Bambu Lab P1S printer (0.4 mm nozzle, Textured PEI plate)", "Prints all 45 pieces. Every plate file in this book is laid out for this exact printer and Bambu Studio — other printers mean re-slicing on your own."),
    ("2.5 mm hex key", f"Turns all {N_SCREWS} M3 screws — every screw you buy for this robot."),
    ("Soldering iron + heat-set insert tip", "Melts the brass inserts into the plastic at about 220 °C. The insert tip keeps them straight — a bare conical tip loves to tilt them."),
    ("PTFE or silicone grease (small tube)", "A thin smear on the neck’s journal and thrust faces in step 18. One tube outlasts the robot."),
    ("Zip ties (2.5 mm)", "Tie the future harness at every printed tie point — the wiring chapter shows where."),
    ("Small flush cutters / scissors", "Trims zip ties and TPU strings."),
    ("Painter’s tape + marker", "Label wires as you go."),
    ("Multimeter", "Checks every circuit before the battery ever goes in."),
]

SHOP_VISUALS = [
    ("thumb_px_pi.png", "Raspberry Pi 5"),
    ("thumb_px_pico.png", "Pico 2"),
    ("thumb_px_mdds10.png", "MDDS10"),
    ("thumb_px_motor_L.png", "25D motor ×2"),
    ("thumb_px_battery.png", "Bioenno battery"),
    ("thumb_px_relay.png", "Panasonic relay"),
    ("thumb_px_fuse.png", "Blue Sea fuse block"),
    ("thumb_px_reg1.png", "5 V regulator"),
    ("thumb_px_reg2.png", "6 V regulator (skip for now)"),
    ("thumb_px_switch.png", "Bumper switch ×6"),
    ("thumb_px_servo.png", "D85MG servo ×2"),
    ("thumb_px_speaker_L.png", "Speaker + amp ×2"),
    ("thumb_px_tof_L.png", "ToF board ×4"),
    ("thumb_px_camera.png", "Camera 3 Wide"),
    ("thumb_px_mic.png", "ReSpeaker mic"),
    ("thumb_px_estop_cap.png", "IDEC E-stop"),
]

PRINT_TIPS = [
    ("Download, then open the prototype project", f"Download <b>codex_robot_body_v2_p1s.3mf</b> from the Builder Release (scan the QR on the previous page, or github.com/brianpattison/robot) and open it in Bambu Studio. Its {N_PLATES} plates are laid out for geometry review on a P1S with a 0.4 mm nozzle and Textured PEI plate; physical release gates remain open."),
    ("Load the exact family + color", "Each plate names one material and one theme color. Never substitute PLA for a white/black/red PETG plate just to preserve the palette."),
    ("No supports", "Every part targets zero supports. If the slicer asks for supports, stop and re-check the source, plate, and declared orientation."),
    ("TPU is slow and squishy", "Print the tire and bumper plates slowly (the profile already does this). TPU that has lived outside its bag needs a night in a filament dryer first — damp TPU prints stringy foam."),
    ("Big flat parts stay put", "The tray, shell, lid, skin, and bumper plates use lots of bed. Clean the plate with dish soap first so they stick."),
]

# Step tuple: (render name, title, screws, strip items, moves, check).
STEPS = [
    ("step_01_tray", "Start with the floor", 0,
     [("tray_v2", 1)],
     ["Clear a big table. Put the tray down flat, wheel cutouts toward you.",
      "Find the two round motor cradles at the back and the tall round towers — that’s the back of the robot."],
     "The tray sits flat and doesn’t rock."),
    ("step_02_inserts", "Melt in the tray’s brass inserts", 0,
     [("px_insert", 20)],
     ["Heat the soldering iron to about 220 °C — insert temperature.",
      "Rest a brass insert in each gold-marked hole, then press it straight down with the hot iron tip until it sits flush. (The gold pegs in the pictures just point at the holes — the real insert always ends up flush inside, nothing sticking out.)",
      "20 go into the tray now — the picture marks every spot. The other 27 come later: 2 in the wheels, 2 in the front pods, 14 in the shell, 2 in the lid, 6 in the neck and collar, and 1 in the head. The book calls for each batch when it’s time."],
     "Every insert is flush and straight, none tilted."),
    ("step_03_motors", "Drop in the motors", SCREWS["motor_caps"],
     [("px_motor_L", 2), ("motor_cap_v2", 2)],
     ["Lay a motor in each cradle with the metal shaft poking OUT through the hole toward the wheel side.",
      "Point each motor’s wire end — the end without the shaft — inward, toward the middle of the robot. (The picture’s plain grey motors leave the wires off.)",
      "Set a printed cap over each motor and screw it down with 2 screws per cap — snug, not gorilla-tight."],
     "Motors don’t wiggle. Each shaft turns when you twist it firmly — the gearbox drags, and that’s normal."),
    ("step_04_wheels_bench", "Make the wheels", 0,
     [("rear_wheel_v2", 2), ("front_wheel_v2", 2), ("tire_v2", 4), ("px_insert", 2)],
     ["The picture’s tags say which two are the BACK wheels (small middle hole with a flat). Each BACK wheel has a little screw well — a small round hole in its rim, shown in the cutaway. Drop 1 insert down each well (2 total), then press it to the bottom with the tip of the iron. It seats deep inside the wheel, close to the axle — nothing pokes out.",
      "Stretch a stretchy printed tire over each of the four wheels, like putting a rubber band on a yo-yo.",
      "Every tire has one little round port in its tread. On the BACK wheels, spin the tire until the port sits right over the screw well — poke a hex key through the port; it should slide into the well (the front wheels don’t care).",
      "Work each tire around evenly until it sits flat in the groove all the way around."],
     "No tire bulges, and a hex key through each BACK tire’s port drops into the screw well."),
    ("step_05_front_pods", "Bolt on the front pods", SCREWS["front_pods"],
     [("front_pod_left_v2", 2), ("px_insert", 2)],
     ["Melt 1 insert into the end of each pod’s peg (2 total).",
      "The two front pods have round pegs sticking out — those pegs are the front axles.",
      "Screw each pod to the tray through its little foot tabs, 2 screws each, pegs pointing OUT."],
     "Both pegs point straight out to the sides."),
    ("step_06_wheels_on", "Put the wheels on",
     SCREWS["rear_wheel_clamps"] + SCREWS["front_axle_retainers"],
     [("rear_wheel_v2", 2), ("front_wheel_v2", 2), ("printed_washer_v2", 2)],
     ["BACK wheels: the hole has a flat side, and so does the motor shaft. Line the flats up, push the wheel on, then drop the clamp screw down through the tire’s port and tighten until it presses snug on the shaft’s flat.",
      "FRONT wheels: slide onto the pegs — they should spin freely. Put a printed cap washer over the end (it covers the wheel’s middle hole), then a screw into the peg to keep the wheel from sliding off.",
      "Don’t overtighten the front screws: the wheels must still spin.",
      "You printed extra washers — drop the leftovers in your spares box."],
     "Back wheels should NOT spin freely by hand (the motor holds them). Front wheels spin freely."),
    ("step_07_tower", "Build the brain tower", SCREWS["controller_tower_base"],
     [("controller_tower_v2", 1), ("px_mdds10", 1)],
     ["Set the tower over the front of the tray — its screw holes match the four inserts.",
      "Drive 4 screws down through the base tabs.",
      "Rest the purple motor board on the four little posts, its green terminal blocks facing the RIGHT side of the robot."],
     "The board sits level on all four posts, terminals facing right."),
    ("step_08_pi", "Add the computer", 0,
     [("px_pi", 1)],
     ["The Raspberry Pi lies flat on the tower’s top shelf frame.",
      "Its USB ports face the BACK of the robot so the cables can reach.",
      "Don’t screw anything — the shelf pocket holds it, and the head’s camera cable drops down to it in step 19."],
     "The Pi sits in its pocket, ports facing backward."),
    ("step_09_battery", "Dry-fit the battery, then remove it", SCREWS["battery_clamp"],
     [("battery_pad_frame_v2", 1), ("px_battery", 1), ("battery_clamp_v2", 1)],
     ["Lay the soft TPU pad frame onto the four little floor pads behind the tower — the arrow shows the bay; the pads hide behind the tower from this angle.",
      "Set the battery on it, wires pointing at the BACK of the robot.",
      "Bridge the clamp bar across the battery onto the two posts and screw it down with 2 screws — firm, so the battery cannot slide.",
      "This is a DRY FIT only. Remove the screws, clamp, battery, and soft pad; put the battery in a safe box away from the build until the meter-check page calls for it."],
     "The battery fits without wrapper pinch or lead strain, and is now outside the robot."),
    ("step_10_pico", "Add the safety helper", SCREWS["pico_clamp"],
     [("px_pico", 1), ("pico_clamp_v2", 1)],
     ["The tiny green Pico sits on its little posts to the right of the tower, USB service end facing the BACK of the robot.",
      "USB and SWD are service-only. Never cable either one to the Pi inside the robot.",
      "Lay the small clamp bar across it and screw it down with 2 screws, gently — it’s a small board."],
     "The Pico is held snug, its USB end points back, and no USB/SWD cable is installed."),
    ("step_11_relay", "Mount the power relay", 0,
     [("px_relay", 1)],
     ["The relay drops into its floor pocket on the left, behind the tower.",
      "Its metal bracket slots into the printed pocket; the terminals face UP so they’re easy to wire later.",
      "No wires yet — the wiring chapter at the back of this book is the reference map for the future harness release."],
     "The relay clicks into its pocket and doesn’t rattle."),
    ("step_12_deck", "Put on the power deck", SCREWS["deck_towers"],
     [("deck_v2", 1), ("px_fuse", 1), ("px_reg1", 2)],
     ["First hang the two small green regulator boards under the deck’s BACK half (they clip under; wires come later). If the 6 V regulator is still on its shopping hold, hang just the 5 V one — the empty pocket is fine for the dry build.",
      "Lower the deck onto the four towers — the notch at the back-right corner is where the battery’s wires will pass once it moves back in.",
      "Drive 4 screws down into the tower tops.",
      "Set the black fuse box into its raised outline on the deck’s LEFT half, wire tail hanging over the left edge."],
     "The deck is level and the fuse box sits inside its printed fence."),
    ("step_13_shell", "Lower the body shell", SCREWS["shell_tray"],
     [("shell_v2", 1), ("px_insert", 14)],
     ["Melt the shell’s 14 inserts first (4 corner lugs, 4 lid-ledge holes, 4 speaker posts, 2 sensor bosses).",
      "Two people make this easy: lower the big shell straight down over EVERYTHING.",
      "The wheel arches go around the wheels; the lip settles onto the tray edge.",
      "Flip-check the underside: drive 4 screws UP through the tray’s corner holes into the shell’s lugs."],
     "No gaps between shell and tray. The robot is now a box with wheels."),
    ("step_14_bumpers", "Feeler switches, then bumpers", 0,
     [("px_switch", 6), ("bumper_front_v2", 2)],
     ["Tip the robot gently onto its side. Click each of the six little feeler switches into its pocket under the tray edge — two front, two back, one each side. Their tiny buttons face OUT.",
      "Their wires tuck up inside for the wiring chapter.",
      "Stand the robot back up. The two soft bumper halves wrap around the bottom, one from the front, one from the back.",
      "They hug the body loosely on purpose — they squish in to press those feeler switches."],
     "Press any bumper edge gently: it moves a tiny bit, you hear a soft click, and it springs back."),
    ("step_15_panels", "Face and back panels (with the front eyes)", 0,
     [("fascia_v2", 1), ("px_tof_L", 2), ("rear_panel_v2", 1)],
     ["First press the two front distance boards into the pockets on the FACE panel’s back — their little lenses peer through the two low holes.",
      "Click the FACE panel into the front opening.",
      "The dark BACK panel clicks into the back opening. Its two round holes are for the charger plug and the mute switch — their own nuts hold them once the harness release closes; in this dry build the holes stay empty.",
      "The face panel’s two light slots stay see-through into the body until the lime bars clip in at step 20 — that’s normal."],
     "Both panels sit flush; two tiny lenses look out of the face."),
    ("step_16_speakers", "Speakers and distance eyes",
     SCREWS["speaker_clamps"] + SCREWS["tof_clamps"],
     [("px_speaker_L", 2), ("px_tof_L", 2), ("speaker_clamp_v2", 2), ("tof_clamp_v2", 2)],
     ["Reach in through the open top: rest a speaker on each side shelf, magnet side in, grille facing the wall.",
      "Lay a clamp bar across each speaker’s top and screw into the two posts (2 screws per side) — the inserts went in with the shell step.",
      "Slide a little blue distance board behind each side window, then its clamp bar and 1 screw."],
     "Speakers can’t rattle; the blue boards peek through their side windows."),
    ("step_17_lid", "The lid and the BIG RED BUTTON",
     SCREWS["mic_cradle"],
     [("lid_v2", 1), ("lid_skin_v2", 1), ("px_estop_cap", 1), ("px_mic", 1), ("mic_cradle_v2", 1), ("px_insert", 2)],
     ["Melt the lid’s 2 mic-boss inserts, then drop the red emergency-stop through the SMALLER of the lid’s two round holes (the big front one belongs to the neck) and spin its nut on underneath — the lid IS its mounting panel, and the printed ring under the lid makes it strong.",
      "Set the round microphone under the lid’s slotted area and screw its ring cradle to the two bosses (2 screws).",
      "OPTIONAL: after the E-stop is clamped, press the teal skin’s four integral tabs into the lid’s blind pockets. It stays above the lid and never goes under the E-stop nut, neck, microphone, or corner screws.",
      "Rest the lid in its ledge — DON’T screw it yet. The neck, the head, and all the wiring still need the inside. Its 4 corner screws are the very last thing in this book."],
     "The optional skin sits flat with every slot open; with the PETG lid supported and nut tight, a centered firm press latches the red button; twist to release."),
    ("step_18_neck", "Build the pan journal and neck", SCREWS["pan_servo_plate"],
     [("neck_v2", 1), ("bayonet_collar_v2", 1), ("head_pan_plate_v2", 1), ("px_servo", 1), ("px_insert", 6)],
     ["Melt 2 inserts into the collar’s pan-plate towers and 4 into the neck’s top flange. Keep heat away from the smooth journal and thrust faces.",
      "From above the loose lid, align the collar’s 3 lugs with the keyways, press through, and twist about 20° until all 3 detents sit in the blind underside race.",
      "Flip the supported lid. Set the pan D85MG into the cradle with its shaft UP; the black pan plate captures its flange from below with 2 M3 screws. The case must not be pinched.",
      "Take the single arm out of the servo’s own bag and land it on the spline tooth closest to the two tick marks lining up — the marks on the collar and neck show center, and the robot’s software trims away the last few degrees later. Fix it with the bag’s spline screw; never force the gears by hand.",
      "Smear a thin film of grease (tools list) on the journal and thrust faces, feed the camera ribbon through the open +X crescent, lower the neck journal into the collar so the arm slides into the neck’s capture slot, and clamp the slot cover over it with 2 M3 screws — the slot walls carry the turning force, not the screws."],
     "The neck sits flat on the greased thrust face; it turns by hand through ±60°, meets both hard stops beyond that range, has no lift, and never rubs the ribbon."),
    ("step_19_head", "Build the tilt head and camera", SCREWS["yoke_neck"] + SCREWS["head_tilt_pivot"],
     [("head_shell_v2", 1), ("yoke_v2", 1), ("px_camera", 1), ("px_servo", 1), ("tilt_bushing_v2", 1), ("px_insert", 1)],
     ["Melt 1 insert into the yoke’s passive-pivot boss from the OUTSIDE end. Seat the yoke on the neck and install its 4 M3 screws without trapping the center ribbon.",
      "Mount the second D85MG sideways in the active frame with the grommets, eyelets, screws, and nuts from its own bag. Land its bag arm on the spline tooth closest to the tick marks on the yoke and head boss — software trims the rest.",
      "Slide the head shell over the yoke so the arm settles into the shell’s capture slot — the slot walls carry the turning force. The servo supplies torque; the printed pivots carry the head.",
      "From the -Y outside face, slide the black shoulder bushing through the shell and install 1 M3 screw into the yoke insert. Tighten against the bushing’s 3.2 mm sleeve — never pinch the moving shell.",
      "Dry-seat the Camera Module 3 behind the face opening and feed its FPC down the hollow neck. Permanent camera-board retention and the exact harness remain prototype release gates."],
     "The bushing flange is flush; the shell has no axial pinch, hand-tilts freely through ±20°, and contacts both printed hard stops only beyond the commanded range."),
    ("step_20_face", "Give it a face", 0,
     [("head_faceplate_v2", 1), ("eye_diffuser_bar_v2", 1), ("status_diffuser_bar_v2", 1)],
     ["Clip the lime eye bar behind the HEAD face’s eye slots (glow boards ride behind it).",
      "Press the head face into its recess on the head shell: camera hole over the lens.",
      "The second lime bar clips behind the body face panel’s light slots — each glow board rides in the pocket behind its bar.",
      "Leave the 4 glow boards in their bag for now — they seat in those pockets when the NeoPixel harness release closes."],
     "Rover Bean is looking at you. Say hi."),
]

WIRE_RULES = [
    "This chapter is the REFERENCE MAP for a harness that is not released yet — no step in this book cuts a wire. Read it to understand the design; build it only when the wire/terminal/fuse releases close.",
    "Wiring is the careful part. Read this whole chapter once, start to finish, before cutting a single wire.",
    "The battery stays OUT of the robot until every wire is checked against these maps.",
    "Use wire colors: RED = battery 12 V, YELLOW = switched motor 12 V, BLUE = 5 V, GREEN = 6 V, BLACK = ground, WHITE = signals.",
    "Crimp or solder every joint; no bare twists. Label both ends of every wire with tape.",
    "Fuse values are UNSET — NOT RELEASED. Do not install any from a prose guess; measured loads, conductor ampacity, inrush, time-current, selective-clearing, and thermal tests must close first.",
    "The robot must FAIL STOPPED: if any of this feels wrong, it stays off.",
]
POWER_MAP = [
    ("Battery +12 V", "covered split → accessory feeder fuse", "Blue Sea fuse block IN"),
    ("Fuse branch 1", "D24V90F5 regulator", "protected 5 V harness; Pi input BLOCKED"),
    ("Fuse branch 2", "D36V50F6 regulator", "6 V servos; regulator qualification BLOCKED"),
    ("Fuse branches 3 + 4", "covered spare positions", "no assigned loads or fuse values"),
    ("Battery +12 V", "separate motor fuse → relay contacts", "MDDS10 motor board power"),
    ("12 V coil feed (exact tap OPEN)", "BOTH E-stop NC contacts + driver (proof BLOCKED)", "relay coil"),
    ("Charger EN2", "assigned contacts TBD", "charge pair + protected charger-present; BLOCKED"),
]
SIGNAL_MAP = [
    ("Raspberry Pi / robotd", "Pico 2", "framed UART commands + heartbeat; no flash or config-write path"),
    ("Pico 2", "MDDS10", "clamped velocity outputs after leases, watchdog, and latch checks"),
    ("Motor encoders (6 wires each)", "Pico 2", "wheel speed feedback"),
    ("Bumper switches ×6", "Pico 2", "any open NC loop = latched stop in independent safety firmware"),
    ("ToF boards ×4", "Raspberry Pi", "I2C + four XSHUT branches; connectors and address proof open"),
    ("NeoPixels ×4", "Raspberry Pi", "data line; level shift, resistor, capacitance, and harness open"),
    ("Camera", "Raspberry Pi", "flat FPC ribbon down the hollow neck"),
    ("Servos ×2", "Pico 2", "future clamped PWM after RBSP HEAD; pins/outputs/harness open"),
    ("Mic array", "Raspberry Pi", "USB data; physical VBUS cut and no-backfeed circuit BLOCKED"),
    ("Pi I2S pins", "MAX98357A amps", "digital sound out; board mounts, channel straps, terminals, and strain relief not released"),
]

# "Meet Rover Bean" callouts: (x%, y%, legend). Percentages are positions
# on the uncropped 4:3 render.
MEET_FRONT = [
    (38.5, 13, "The head — camera in the middle, glowing eyes beside it. It nods and turns to look at you."),
    (55, 44, "The white PETG lid carries the red button and head. The teal PLA skin above it is optional decoration."),
    (27, 66, "Face panel — two distance eyes low, glowing status bars above."),
    (23, 83, "Soft bumper — a squishy ring that feels walls and tells the robot to stop."),
    (83, 72, "Four wheels with grippy printed tires. The back pair are the motor wheels."),
]
MEET_REAR = [
    (36, 38.5, "Cooling vents — warm air from the computer leaves here."),
    (51.5, 39, "The BIG RED BUTTON. Push = everything stops; twist to release."),
    (27, 57, "The charging plug and the mic mute switch bolt into these two holes."),
    (70, 77, "Motor wheels. Each one has its own motor and its own speed sensor — the sliver of red behind the wheel is its motor cap."),
]


# ---------------------------------------------------------------------------
# HTML
# ---------------------------------------------------------------------------
def esc(s):
    return html.escape(str(s), quote=False)


def img_uri(path: Path) -> str:
    relative = path.resolve().relative_to(ROOT)
    return "../../" + relative.as_posix()


def ensure_release_qr() -> None:
    try:
        import qrcode
        from qrcode.constants import ERROR_CORRECT_M
    except ImportError as exc:
        raise SystemExit(
            "qrcode is required for the versioned Builder Release link; "
            "install cad/python/requirements.txt") from exc
    RELEASE_QR.parent.mkdir(parents=True, exist_ok=True)
    qr = qrcode.QRCode(version=None, error_correction=ERROR_CORRECT_M, box_size=12, border=3)
    qr.add_data(RELEASE_URL)
    qr.make(fit=True)
    qr.make_image(fill_color="#075365", back_color="#FFFFFF").save(RELEASE_QR)


def friendly(base: str) -> str:
    return PART_NAMES.get(base, base.replace("_v2", "").replace("_", " "))


CSS = """
* { margin: 0; padding: 0; box-sizing: border-box; }
:root {
  --paper:#FBF7EC; --cream:#F3ECDA; --teal:#0B6E84; --teal-dk:#075365;
  --ink:#22231F; --ink2:#6E6553; --red:#C4230F; --gold:#B8892E;
  --lime:#B9E44A; --line:rgba(34,35,31,.16); --line-soft:rgba(34,35,31,.09);
}
@page { size: 11in 8.5in; margin: 0; }
body { font-family: "Avenir Next", "Helvetica Neue", Helvetica, sans-serif; color: var(--ink); }
section.page { width: 11in; height: 8.5in; page-break-after: always; position: relative;
  overflow: hidden; background: var(--paper); padding: .5in .6in; display: flex; flex-direction: column; }
h1 { font-size: 64px; font-weight: 800; color: var(--teal); letter-spacing: -1.5px; line-height: .93; }
h2 { font-size: 29px; font-weight: 600; color: var(--ink); letter-spacing: -.3px; margin-bottom: .16in; }
h3 { font-size: 15px; font-weight: 600; color: var(--teal-dk); margin: .14in 0 .05in; }
p, li { font-size: 12.5px; line-height: 1.5; }
.eyebrow { font-size: 10px; font-weight: 700; letter-spacing: .18em; color: var(--ink2);
  text-transform: uppercase; margin-bottom: .07in; display: flex; align-items: center; gap: .08in; }
.eyebrow i { width: .09in; height: .09in; border-radius: 2px; display: inline-block; }
.tab { position: absolute; right: 0; width: .3in; padding: .14in 0; border-radius: .09in 0 0 .09in;
  color: #fff; font-size: 8.5px; font-weight: 700; letter-spacing: .2em; writing-mode: vertical-rl;
  text-align: center; z-index: 5; }
table { border-collapse: collapse; width: 100%; font-size: 11.5px; }
th { text-align: left; font-size: 9px; letter-spacing: .12em; text-transform: uppercase;
  color: var(--teal-dk); border-bottom: 2px solid var(--teal); padding: .03in .07in .045in; }
td { padding: .052in .07in; border-bottom: 1px solid var(--line-soft); vertical-align: top; }
td b { font-weight: 600; }
.mono { font-family: Menlo, monospace; font-size: 8px; color: var(--ink2); }
.statchip { display: inline-block; border: 1.5px solid var(--ink); border-radius: .16in;
  padding: .045in .13in; font-size: 11px; font-weight: 700; letter-spacing: .03em; }
.stephead { display: flex; align-items: center; gap: .17in; }
.stepnum { width: .58in; height: .58in; border-radius: .13in; background: var(--teal); color: #fff;
  display: flex; align-items: center; justify-content: center; font-size: 29px; font-weight: 800; flex: none; }
.stephead h2 { margin: 0; font-size: 25px; }
.prog { margin-left: auto; text-align: right; }
.prog span { font-size: 8.5px; font-weight: 700; letter-spacing: .14em; color: var(--ink2); }
.prog .bar { display: flex; gap: 2.5px; margin-top: .045in; }
.prog .bar i { display: block; width: .1in; height: .075in; border-radius: 2px; background: #E7DFC8; }
.prog .bar i.on { background: var(--teal); }
.strip { background: var(--cream); border: 1px solid var(--line-soft); border-radius: .12in;
  display: flex; align-items: center; flex-wrap: wrap; gap: .1in; padding: .09in .14in;
  margin: .13in 0; min-height: 1.08in; }
.gather { writing-mode: vertical-rl; transform: rotate(180deg); font-size: 8px; font-weight: 700;
  letter-spacing: .22em; color: var(--ink2); margin-right: .04in; }
.strip .cell { background: #fff; border: 1px solid var(--line-soft); border-radius: .1in;
  padding: .045in .09in; display: flex; align-items: center; gap: .07in; }
.strip .cell img { width: .78in; height: .78in; object-fit: contain; }
.strip .cell b { font-size: 15px; font-weight: 700; display: block; line-height: 1.1; }
.strip .cell small { font-size: 8px; display: block; color: var(--ink2); font-weight: 600; }
.strip.dense { gap: .055in; }
.strip.dense .cell { padding: .03in .05in; gap: .04in; }
.strip.dense .cell img { width: .5in; height: .5in; }
.strip.dense .cell b { font-size: 11px; }
.strip.dense .cell small { font-size: 6.5px; }
.stepbody { display: flex; gap: .28in; flex: 1; min-height: 0; }
.stepbody .imgwrap { width: 6.15in; height: 4.85in; border-radius: .14in; overflow: hidden;
  position: relative; flex: none; border: 1px solid var(--line-soft); }
.stepbody .imgwrap img.main { width: 107%; height: 107%; object-fit: cover; object-position: 50% 55%; margin: -2.5% 0 0 -3.5%; }
.step-annotations { position: absolute; left: -3.5%; top: -2.5%; width: 107%; height: 107%;
  pointer-events: none; overflow: visible; }
.frontchip { position: absolute; left: .12in; bottom: .12in; background: rgba(34,35,31,.85); color: #fff;
  font-weight: 700; font-size: 10.5px; letter-spacing: .04em; padding: .04in .1in; border-radius: .1in; }
.axisbadge { position: absolute; left: .12in; top: .12in; display: flex; align-items: center; gap: .045in;
  background: rgba(255,249,238,.92); color: var(--ink); border: 1px solid rgba(34,35,31,.25);
  border-radius: .13in; padding: .045in .09in; font-size: 8px; font-weight: 800;
  letter-spacing: .06em; box-shadow: 0 1px 5px rgba(0,0,0,.12); }
.axisbadge b { color: var(--teal); font-size: 12px; line-height: 1; }
.axisbadge i { font-style: normal; color: var(--teal-dk); font-size: 7px; letter-spacing: .1em; }
.instr { flex: 1; display: flex; flex-direction: column; }
.instr ol { margin-left: .22in; }
.instr li { font-size: 13.5px; margin-bottom: .1in; line-height: 1.42; }
.instr.compact li { font-size: 12.2px; margin-bottom: .065in; line-height: 1.36; }
.instr.compact .check { font-size: 11.5px; }
.check { margin-top: auto; background: var(--lime); border-radius: .11in; padding: .1in .13in;
  font-weight: 600; font-size: 12.5px; display: flex; gap: .1in; align-items: flex-start; line-height: 1.35; }
.check .box { flex: none; width: .16in; height: .16in; background: #fff; border: 2px solid var(--ink);
  border-radius: 3px; margin-top: 1px; }
.check b { color: var(--teal-dk); letter-spacing: .08em; font-size: 10.5px; margin-right: .04in; }
.cols { display: flex; gap: .35in; }
.cols > div { flex: 1; }
.footer { position: absolute; bottom: .24in; left: .6in; right: .6in; display: flex;
  justify-content: space-between; font-size: 7.5px; font-weight: 600; letter-spacing: .14em;
  color: #A2967C; text-transform: uppercase; }
.rule { background: #FFF8F1; border: 1.5px solid #E8B8A9;
  border-radius: .07in; padding: .07in .13in; margin-bottom: .08in; font-size: 12.5px; }
.cmd { background: #22231F; color: #E8E4D8; border-radius: .1in; padding: .1in .13in;
  font-family: Menlo, monospace; font-size: 9.5px; line-height: 1.55; white-space: pre-wrap;
  word-break: break-all; }
.cmd b { color: #B9E44A; font-weight: 700; }
.hero { position: absolute; right: 0; top: 0; width: 6in; height: 8.5in; object-fit: cover; object-position: 62% 22%; }
.invgrid { display: grid; grid-template-columns: repeat(8, 1fr); gap: .08in; }
.invcell { background: #fff; border: 1px solid var(--line-soft); border-radius: .1in;
  padding: .05in .03in .045in; text-align: center; position: relative; }
.invcell img { width: .84in; height: .68in; object-fit: contain; }
.invcell .nm { font-size: 8px; font-weight: 600; line-height: 1.15; min-height: .19in; }
.invcell .ct { font-size: 11px; font-weight: 800; margin-top: .01in; }
.invcell .swatch { position: absolute; top: .05in; right: .05in; width: .1in; height: .1in;
  border-radius: 50%; border: 1px solid rgba(0,0,0,.25); }
table.roomy td { padding: .075in .07in; }
.callout { position: absolute; width: .26in; height: .26in; border-radius: 50%; background: var(--teal);
  color: #fff; font-size: 13px; font-weight: 800; display: flex; align-items: center;
  justify-content: center; border: 2.5px solid #fff; box-shadow: 0 1px 5px rgba(0,0,0,.3);
  transform: translate(-50%, -50%); }
.legend { margin-top: .09in; }
.legend div { display: flex; gap: .08in; font-size: 11px; line-height: 1.4; margin-bottom: .055in; }
.legend b.n { flex: none; width: .17in; height: .17in; border-radius: 50%; background: var(--teal);
  color: #fff; font-size: 9.5px; display: flex; align-items: center; justify-content: center; margin-top: 1px; }
.toc { margin-top: .3in; width: 3.9in; }
.toc .row { display: flex; align-items: baseline; gap: .09in; margin-bottom: .085in; }
.toc .n { font-size: 13px; font-weight: 800; width: .17in; }
.toc .t { font-size: 13.5px; font-weight: 600; }
.toc .d { font-size: 10px; color: var(--ink2); }
.toc .lead { flex: 1; border-bottom: 1.5px dotted #C4B896; transform: translateY(-3px); }
.toc .pg { font-size: 11px; font-weight: 700; color: var(--ink2); }
svg text { font-family: "Avenir Next", Helvetica, sans-serif; }
"""


def page(body, chapter=None, footer=True, num=None, total=None):
    tab = ""
    if chapter is not None:
        label, color, _, _ = CHAPTERS[chapter]
        top = 0.9 + chapter * 0.82
        tab = f'<div class="tab" style="background:{color}; top:{top}in;">{label}</div>'
    ft = ""
    if footer:
        ft = (f'<div class="footer"><span>Codex Rover Bean &middot; Builder’s Book</span>'
              f'<span>{"" if num is None else f"Page {num} of {total}"}</span></div>')
    return f'<section class="page">{tab}{body}{ft}</section>'


def eyebrow(chapter=None, text=None):
    if chapter is not None:
        label, color, name, _ = CHAPTERS[chapter]
        txt = f"Chapter {chapter + 1} &middot; {name}"
        dot = f'<i style="background:{color}"></i>'
    else:
        txt, dot = text, '<i style="background:var(--teal)"></i>'
    return f'<div class="eyebrow">{dot}{txt}</div>'


def progress(i, n=len(STEPS)):
    cells = "".join('<i class="on"></i>' if k <= i else "<i></i>" for k in range(1, n + 1))
    return f'<div class="prog"><span>STEP {i} OF {n}</span><div class="bar">{cells}</div></div>'


def strip_cells(step_key, items, screws):
    cells = ""
    for t, n in items:
        name = STRIP_NAME_OVERRIDES.get((step_key, t), friendly(t))
        if t == "px_insert" and n == 1:
            name = "brass insert"
        cells += (f'<div class="cell"><img src="{img_uri(GUIDE_IMG / ("thumb_" + t + ".png"))}">'
                  f'<div><b>&times;{n}</b><small>{esc(name)}</small></div></div>')
    if screws:
        cells += (f'<div class="cell"><img src="{img_uri(GUIDE_IMG / "thumb_px_screw.png")}">'
                  f'<div><b>&times;{screws}</b><small>M3 screw{"s" if screws != 1 else ""}</small></div></div>')
    return cells


def build_body_pages():
    """Everything except the cover; returns a list of page dicts."""
    pages = []

    def add(html_body, chapter=None, footer=True, mark=None):
        pages.append({"html": html_body, "chapter": chapter, "footer": footer, "mark": mark})

    # --- Meet the robot -----------------------------------------------------
    def figure(img_name, callouts, caption):
        dots = "".join(f'<div class="callout" style="left:{x}%; top:{y}%;">{k}</div>'
                       for k, (x, y, _) in enumerate(callouts, start=1))
        legend = "".join(f'<div><b class="n">{k}</b><span>{esc(t)}</span></div>'
                         for k, (_, _, t) in enumerate(callouts, start=1))
        return (f'<div style="flex:1;"><div style="position:relative; border-radius:.14in; overflow:hidden;'
                f' border:1px solid var(--line-soft); aspect-ratio:4/3;">'
                f'<img src="{img_uri(IMG / img_name)}" style="width:100%; height:100%; object-fit:cover;">{dots}</div>'
                f'<p style="font-size:9px; font-weight:700; letter-spacing:.12em; color:var(--ink2);'
                f' text-transform:uppercase; margin-top:.05in;">{caption}</p>'
                f'<div class="legend">{legend}</div></div>')

    stats = "".join(
        f'<div style="flex:1; text-align:center;"><div style="font-size:26px; font-weight:800; color:var(--teal);">{v}</div>'
        f'<div style="font-size:9px; font-weight:700; letter-spacing:.12em; color:var(--ink2); text-transform:uppercase;">{k}</div></div>'
        for v, k in [(N_PIECES, "printed incl. spare + optional"), (N_SCREWS, "screws, one size"),
                     (N_PLATES, "printer plates"), ("0", "supports needed")])
    add(f"""
      {eyebrow(text="Meet your robot")}
      <h2>This is Rover Bean</h2>
      <div style="display:flex; gap:.3in;">
        {figure('codex_robot_body_v2_assembled.png', MEET_FRONT, 'From the front')}
        {figure('codex_robot_body_v2_rear.png', MEET_REAR, 'From the back')}
      </div>
      <div style="display:flex; gap:.2in; border-top:1px solid var(--line); padding-top:.14in; margin-top:.22in;">{stats}</div>""",
        mark="meet")

    # --- How the book works -------------------------------------------------
    mini_bar = "".join('<i class="on"></i>' if k <= 7 else "<i></i>" for k in range(1, 21))
    anatomy = f"""
      <div style="background:#fff; border:1px solid var(--line); border-radius:.14in; padding:.16in; width:4.9in;">
        <div class="stephead"><div class="stepnum" style="width:.42in;height:.42in;font-size:20px;">7</div>
          <h2 style="font-size:17px;">Every step looks like this</h2>
          <div class="prog"><span>STEP 7 OF 20</span><div class="bar">{mini_bar}</div></div></div>
        <div class="strip" style="min-height:.72in; margin:.09in 0;"><span class="gather">GATHER</span>
          <div class="cell"><img src="{img_uri(GUIDE_IMG / 'thumb_controller_tower_v2.png')}" style="width:.5in;height:.5in;">
            <div><b style="font-size:12px;">&times;1</b><small>brain tower</small></div></div>
          <div class="cell"><img src="{img_uri(GUIDE_IMG / 'thumb_px_screw.png')}" style="width:.5in;height:.5in;">
            <div><b style="font-size:12px;">&times;4</b><small>M3 screws</small></div></div></div>
        <div style="display:flex; gap:.12in;">
          <div style="width:2.5in; height:1.5in; border-radius:.1in; background:#E8DFC9; position:relative;">
            <div class="frontchip" style="font-size:8px; padding:.03in .07in;">&#8601; FRONT</div>
            <div style="position:absolute; top:38%; left:0; right:0; text-align:center; font-size:9px; font-weight:700; color:var(--ink2); letter-spacing:.1em;">THE BIG PICTURE</div></div>
          <div style="flex:1; display:flex; flex-direction:column;">
            <ol style="margin-left:.16in;"><li style="font-size:9px; margin-bottom:.04in;">Numbered moves&hellip;</li>
              <li style="font-size:9px;">&hellip;if you want words too.</li></ol>
            <div class="check" style="font-size:9px; padding:.06in .08in; gap:.06in;"><span class="box" style="width:.12in;height:.12in;"></span>
              <div><b style="font-size:8px;">CHECK</b> A 10-second test.</div></div></div>
        </div>
      </div>"""
    add(f"""
      {eyebrow(text="How this book works")}
      <h2>Four things to know before you build</h2>
      <div style="display:flex; gap:.32in; flex:1;">
        <div>{anatomy}
          <p style="font-size:11px; color:var(--ink2); margin-top:.1in; width:4.9in;">The tan GATHER strip lists every
          part and screw the step needs — lay them out like a cooking show. The picture shows the robot so far,
          with the new parts floating just off their spot; a magenta arrow slides a floating part into its landing ring.
          The FRONT tag points at the robot’s face.</p>
        </div>
        <div style="flex:1;">
          <h3 style="margin-top:0;">1. The pictures do the talking</h3>
          <p>Match the big picture, then read the numbered lines if you want words too. Do the little green
          CHECK before moving on — if it fails, fix it now, because later steps cover things up.</p>
          <h3>2. One screw. One key.</h3>
          <p>Every screw in this robot is the same M3 × 8 screw, and one 2.5 mm hex key turns them all —
          the only other fastener anywhere is the tiny spline screw that comes in each servo’s own bag.
          “Snug” means: stop when it stops, then an eighth of a turn. Plastic hates gorillas.</p>
          <h3>3. Front and back</h3>
          <p>The FRONT is where the face panel and head look. The BACK has the charging plug, the mute switch,
          and the motor wheels. Left and right are always the robot’s left and right, not yours — and most pictures
          FACE the robot, so its R sits on your left, like shaking hands. The corner badge on those pictures
          spells out the flip.</p>
          <h3>4. Go in order</h3>
          <p>The steps nest like LEGO bags: wheels before shell, shell before lid. The soldering iron and the
          multimeter each come out for their own steps — the book tells you exactly when.</p>
        </div>
      </div>
      <div style="display:flex; align-items:center; gap:.14in; border-top:1px solid var(--line);
           padding-top:.16in; margin-top:.1in;">
        <div style="font-size:9px; font-weight:700; letter-spacing:.14em; color:var(--ink2); width:.9in;">THE ROAD TO A ROBOT</div>
        {"".join(
            f'<div style="flex:1; display:flex; align-items:center; gap:.1in;">'
            f'<div style="flex:1; text-align:center;"><div style="background:{c}; color:#fff; border-radius:.09in;'
            f' padding:.045in 0; font-size:10.5px; font-weight:800; letter-spacing:.1em;">{i + 1} &middot; {lbl}</div>'
            f'<div style="font-size:8.5px; color:var(--ink2); margin-top:.03in; font-weight:600;">{hint}</div></div>'
            + ('<div style="font-size:14px; color:#B4A785;">&#8594;</div>' if i < 4 else "")
            + "</div>"
            for i, ((lbl, c, _, _), hint) in enumerate(zip(CHAPTERS,
                ["buy the box", f"{N_PLATES} plates", f"{len(STEPS)} steps", "reference maps", "brain on, motors off"])))}
      </div>""",
        mark="how")

    # --- Chapter 1: shop -----------------------------------------------------
    fil = "".join(f"<tr><td><b>{esc(a)}</b></td><td>{esc(b)}</td><td>{esc(c)}</td></tr>" for a, b, c in SHOP_FILAMENT)
    fas = "".join(f"<tr><td><b>{esc(a)}</b></td><td>{esc(b)}</td><td>{esc(c)}</td></tr>" for a, b, c in SHOP_FASTENERS)
    tools = "".join(f"<tr><td><b>{esc(a)}</b></td><td>{esc(b)}</td></tr>" for a, b in SHOP_TOOLS)
    add(f"""
      {eyebrow(0)}
      <h2>Go shopping: plastic, screws, tools</h2>
      <div class="cols"><div>
        <h3 style="margin-top:0;">Filament (for the printer)</h3>
        <table><tr><th>Filament</th><th>How much</th><th>What it becomes</th></tr>{fil}</table>
        <h3 style="margin-top:.2in;">The only two fastener packs</h3>
        <table><tr><th>Fastener</th><th>Buy</th><th>Why</th></tr>{fas}</table>
        <div style="margin-top:.22in; background:var(--cream); border-radius:.12in; padding:.11in .14in;">
          <p style="font-size:11.5px;"><b>Get a spares box.</b> A cheap compartment box keeps screws, inserts,
          washers, and every printed spare sorted through the whole build. Future-you says thanks.</p>
        </div>
      </div><div>
        <h3 style="margin-top:0;">Tools</h3>
        <table><tr><th>Tool</th><th>Job</th></tr>{tools}</table>
        <div style="margin-top:.22in; background:#fff; border:1px solid var(--line-soft); border-radius:.12in;
             padding:.12in; display:flex; gap:.22in; align-items:center;">
          <img src="{img_uri(GUIDE_IMG / 'thumb_px_screw.png')}" style="width:1.15in;">
          <img src="{img_uri(GUIDE_IMG / 'thumb_px_insert.png')}" style="width:1.15in;">
          <p style="font-size:11.5px;">This screw and this brass insert are the only fasteners you’ll buy on their own
          for the whole robot — everything else a step needs ships in a component’s own box. When a step says “2 screws,”
          it always means these.</p>
        </div>
      </div></div>""",
        chapter=0, mark="ch0")

    # Shopping: electronics (split across two pages so nothing clips; the
    # first page carries taller hold rows, so it takes one fewer).
    half = (len(SHOP_ELECTRONICS) + 1) // 2 - 1
    for part_i, chunk in enumerate((SHOP_ELECTRONICS[:half], SHOP_ELECTRONICS[half:]), start=1):
        elec = "".join(f"<tr><td><b>{esc(a)}</b></td><td style='text-align:center'>{esc(b)}</td><td>{esc(c)}</td></tr>"
                       for a, b, c in chunk)
        intro = ("Every production component must ultimately be a normal buy-one-online part in the US. Rows marked DO NOT BUY YET or not released are decisions to close, not shopping instructions — skip them and the book tells you where their build steps pause. The nominal "
                 "28-route harness traveler ships with this version; exact terminals, measured lengths, crimp tooling, and fuse values remain open."
                 if part_i == 1 else "The rest of the electronics box:")
        add(f"""
          {eyebrow(0)}
          <h2>Go shopping: the electronics box ({part_i} of 2)</h2>
          <p style="margin-bottom:.12in;">{intro}</p>
          <table class="roomy" style="font-size:12px;"><tr><th>Part</th><th>Qty</th><th>What it does</th></tr>{elec}</table>""",
            chapter=0)

    visual_cells = "".join(
        f'<div style="height:1.02in; border:1px solid var(--line-soft); border-radius:.1in; background:#fff; '
        f'padding:.05in; display:flex; align-items:center; gap:.07in;">'
        f'<img src="{img_uri(GUIDE_IMG / image)}" style="width:.72in; height:.72in; object-fit:contain;">'
        f'<div style="font-size:10.5px; font-weight:750; line-height:1.15;">{esc(label)}</div></div>'
        for image, label in SHOP_VISUALS)
    add(f"""
      {eyebrow(0)}
      <h2>Match the electronics before they enter the robot</h2>
      <p style="margin-bottom:.12in;">Use these silhouettes to sort the big purchased parts. They show identity and connector direction,
      not exact scale; small buys (memory card, charger, plugs, glow boards) go by their bag labels, and the delivered-part
      fit record still decides whether a component passes.</p>
      <div style="display:grid; grid-template-columns:repeat(4,1fr); gap:.08in;">{visual_cells}</div>
      <div style="margin-top:auto; display:flex; align-items:center; gap:.14in; border-top:1px solid var(--line); padding-top:.1in;">
        <img src="{img_uri(RELEASE_QR)}" style="width:.72in; height:.72in; image-rendering:pixelated;">
        <p style="font-size:10.5px;"><b>One source, one version:</b> scan for the permanent Builder Release
        <span class="mono">{RELEASE_ID}</span>. Download both 3MF print projects and this PDF there — plus the exact BOM, software paths, bench commands, and every open physical gate.</p>
      </div>""", chapter=0)

    # --- Chapter 2: print ----------------------------------------------------
    tips = "".join(
        f'<div style="display:flex; gap:.12in; margin-bottom:.13in;">'
        f'<div style="flex:none; width:.28in; height:.28in; border-radius:50%; background:var(--teal); color:#fff;'
        f' font-size:14px; font-weight:800; display:flex; align-items:center; justify-content:center;">{k}</div>'
        f'<div><h3 style="margin:0 0 .02in;">{esc(t)}</h3><p style="font-size:11.5px;">{d}</p></div></div>'
        for k, (t, d) in enumerate(PRINT_TIPS, start=1))
    order_data = [("#fff", "TEST PARTS", f"{len(PROOFS)} proofs first")]
    for group in FILAMENT_GROUPS.values():
        plate, count = group["plate"], group["count"]
        theme = inv.DEFAULT_THEME[plate["color_profile"]]
        label = (f"{theme['name']} PLA" if theme["name"].startswith("Translucent") and "PLA" in plate["material"]
                 else f"{theme['name']} {plate['material']}")
        order_data.append((plate["color_hex"], label,
                           f"{count} plate{'s' if count != 1 else ''}"))
    order_chips = "".join(
        f'<div style="text-align:center; background:#fff; border:1px solid var(--line); border-radius:.09in; padding:.05in .04in;">'
        f'<div style="font-size:9px; font-weight:800; letter-spacing:.04em;">'
        f'<span style="display:inline-block; width:.11in; height:.11in; border-radius:50%; background:{c};'
        f' border:1px solid rgba(0,0,0,.2); vertical-align:-1.5px; margin-right:.045in;"></span>{esc(t)}</div>'
        f'<div style="font-size:8px; color:var(--ink2); margin-top:.02in; font-weight:600;">{esc(d)}</div></div>'
        for c, t, d in order_data)
    add(f"""
      {eyebrow(1)}
      <div style="display:inline-block; margin-bottom:.1in; background:var(--red); color:#fff; padding:.07in .12in; font-size:11px; font-weight:800; letter-spacing:.08em;">PROTOTYPE PLATES — PHYSICAL RELEASE GATES OPEN</div>
      <h2>Print it with Bambu Studio</h2>
      <div class="cols">
        <div>{tips}</div>
        <div>
          <img src="{img_uri(IMG / 'codex_robot_body_v2_p1s_plates.png')}"
               style="width:100%; border-radius:.12in; border:1px solid var(--line-soft);">
          <p style="font-size:10px; margin-top:.06in; color:var(--ink2);">All {N_PLATES} prototype plates, exactly as they open in Bambu Studio. The layout is print review, not a powered-motion release.</p>
        </div>
      </div>
      <div style="border-top:1px solid var(--line); padding-top:.12in; margin-top:auto;">
        <div style="font-size:9px; font-weight:700; letter-spacing:.14em; color:var(--ink2); margin-bottom:.06in;">PRINTING ORDER</div>
        <div style="display:grid; grid-template-columns:repeat(4,1fr); gap:.06in;">{order_chips}</div>
      </div>""",
        chapter=1, mark="ch1")

    # Plate table: aggregate instances and use the same friendly part names
    # as the piece chart and step strips, so a kid can match them.
    from guide_estimates_v2 import plate_estimates, totals
    estimates = plate_estimates(PLATES)
    est_g, est_h = totals(estimates)
    rows = ""
    for p in PLATES["plates"]:
        plate_counts: dict[str, int] = {}
        for pp in p["parts"]:
            base = re.sub(r"_i\d+$", "", pp["name"])
            plate_counts[base] = plate_counts.get(base, 0) + 1
        items = []
        for base, n in plate_counts.items():
            txt = esc(friendly(base)) if n == 1 else f"{esc(friendly(base))} ×{n}"
            if base == "printed_washer_v2":
                txt += " <i>(the robot uses 2 — the rest are spares)</i>"
            items.append(txt)
        parts_txt = ", ".join(items)
        rows += (
            f"<tr><td style='text-align:center'><b>{p['plate_number']}</b></td>"
            f"<td><span style='display:inline-block;width:.13in;height:.13in;border-radius:50%;"
            f"background:{p['color_hex']};border:1px solid rgba(0,0,0,.25); vertical-align:-2px;'></span> "
            f"{esc(p['name'].replace(' - ', ' · '))}</td>"
            f"<td style='text-align:center'>{p['part_count']}</td>"
            f"<td>{parts_txt}</td>"
            f"<td style='text-align:center; white-space:nowrap;'>≈{estimates[p['plate_number']]['grams']} g<br>"
            f"≈{estimates[p['plate_number']]['hours']:g} h</td></tr>")
    add(f"""
      {eyebrow(1)}
      <h2>The {N_PLATES} prototype plates, in printing order</h2>
      <table class="roomy" style="font-size:10.5px;"><tr><th style="width:.35in;">#</th><th style="width:2.3in;">Plate (load this filament)</th><th style="width:.5in;">Parts</th><th>What’s on it</th><th style="width:.7in;">Plan for*</th></tr>{rows}</table>
      <p style="margin-top:.12in; font-size:11px;"><b>The whole job plans at ≈{est_g:,} g of filament and ≈{est_h:g} printer-hours.</b>
      *Planning estimates computed from the exported geometry — your slicer’s numbers win.
      <b>Tip:</b> the plates are grouped by exact material and color — print each group back to back, then label its box before
      changing filament. Every plate carries a small corner <b>check tab</b>: test its insert bore and screw hole
      before starting the next plate, and fix the printer first if either is off.</p>""",
        chapter=1)

    bin_labels = "".join(
        f'<div style="height:.92in; border:1.5px dashed #8D897E; border-radius:.08in; padding:.07in .09in; '
        f'display:grid; grid-template-columns:.32in 1fr; column-gap:.08in; align-items:center; background:#fff;">'
        f'<div style="width:.28in; height:.28in; border-radius:50%; background:{p["color_hex"]}; '
        f'border:1px solid rgba(0,0,0,.25);"></div>'
        f'<div><div style="font-size:8px; font-weight:800; letter-spacing:.12em; color:var(--ink2);">PLATE {p["plate_number"]}</div>'
        f'<div style="font-size:10.5px; font-weight:800; line-height:1.1;">{esc(p["name"])}</div>'
        f'<div style="font-size:8.5px; margin-top:.02in;">{p["part_count"]} printed piece{"s" if p["part_count"] != 1 else ""}</div></div></div>'
        for p in PLATES["plates"])
    add(f"""
      {eyebrow(1)}
      <h2>Cut-apart labels for the parts boxes</h2>
      <p style="margin-bottom:.12in;">Cut on the dotted lines and tape each label to its box as a plate finishes.
      Keep failed/reprinted pieces outside the counted box so the Chapter 3 gather strips stay honest.</p>
      <div style="display:grid; grid-template-columns:repeat(4,1fr); gap:.09in;">{bin_labels}</div>
      <div class="check" style="margin-top:auto;"><span class="box"></span><div><b>CHECK</b>
      All {N_PLATES} boxes are labeled, and their piece totals match the plate manifest before assembly starts.</div></div>""",
        chapter=1)

    # Proofs are a real tracked P1S project, not an STL treasure hunt.
    add(f"""
      {eyebrow(1)}
      <div style="display:inline-block; margin-bottom:.1in; background:var(--lime); color:var(--ink); padding:.07in .12in; font-size:11px; font-weight:850; letter-spacing:.08em;">FIRST PRINT: QUALIFICATION PROOFS</div>
      <h2>Open one file. Print the evidence first.</h2>
      <div class="cols">
        <div>
          <img src="{img_uri(IMG / 'codex_robot_body_v2_proofs_p1s_plates.png')}"
               style="width:100%; border-radius:.12in; border:1px solid var(--line-soft);">
          <p style="font-size:10px; margin-top:.06in; color:var(--ink2);">
            {len(PROOFS)} logical tests, {sum(p['part_count'] for p in PROOF_PLATES['plates'])} printable objects,
            {len(PROOF_PLATES['plates'])} material-separated P1S plates. The tire ring and core are separate objects.
          </p>
        </div>
        <div>
          <h3 style="margin-top:0;">codex_robot_body_v2_proofs_p1s.3mf</h3>
          <ol style="font-size:12px; margin-left:.24in;">
            <li>Open the tracked proof 3MF in Bambu Studio.</li>
            <li>Load the exact filament product and color you intend to use.</li>
            <li>Print one material plate at a time; do not substitute a pass from another spool family.</li>
            <li>Run the matching fit, load, wear, heat, or optical check on the next two pages.</li>
            <li>Record the machine, filament, settings, measured result, tester, and date. Blank means OPEN.</li>
          </ol>
          <div style="margin-top:.14in; background:var(--cream); border-radius:.1in; padding:.09in .12in;">
            <p style="font-size:10.5px;"><b>About the “Body Primary PLA” plate:</b> that one is the try-out plate — print it in the
            body-color PLA you <i>hope</i> to use for the shell and head. Until a candidate passes every check, those parts print in
            white PETG (this book’s plates already do), so the try-out spool is a color audition, not a shopping-list item.</p>
          </div>
          <div class="check" style="margin-top:.14in;"><span class="box"></span><div><b>CHECK</b>
            Every proof object is present, each plate contains one material/color, and no support is enabled.</div></div>
        </div>
      </div>""", chapter=1)

    # Proofs: keep the original mechanical checks and the new material
    # qualification evidence on separate pages so the recording fields remain
    # readable instead of becoming microscopic ant paperwork.
    standard_proofs = [(k, v) for k, v in PROOFS.items()
                        if "_pla_" not in k and "lid_boundary" not in k]
    material_proofs = [(k, v) for k, v in PROOFS.items()
                        if "_pla_" in k or "lid_boundary" in k]
    for proof_page, proof_items in enumerate((standard_proofs, material_proofs), start=1):
        crows = "".join(f"<tr><td><b>{esc(PROOF_TITLES.get(k, k))}</b><br>"
                        f"<span class='mono'>{esc(' + '.join(o['stl'] for o in v['objects']))}</span></td>"
                        f"<td>{esc(v['material'])}</td><td>{esc(PROOF_NOTES.get(k, v['note']))}</td></tr>"
                        for k, v in proof_items)
        intro = ("These checks prove the shared screw, wheel, switch, board, and motion interfaces."
                 if proof_page == 1 else
                 "These checks are specific to the exact PLA/PETG product lines you load. A pass never transfers to another brand, subtype, or effect filament.")
        record = "" if proof_page == 1 else """
          <div style="margin-top:.12in; border:2px solid var(--red); border-radius:.1in; padding:.08in .12in; font-size:10px;">
            <b>RECORD BEFORE PASS:</b> manufacturer · product line · subtype · color · nozzle · layer height · wall count ·
            insert-tool temperature (when used) · measurements · pass/fail · tester · date. Blank evidence means the gate is open.
          </div>"""
        add(f"""
          {eyebrow(1)}
          <h2>Print the little test parts first ({proof_page} of 2)</h2>
          <p style="margin-bottom:.1in;">Print them from <b>codex_robot_body_v2_proofs_p1s.3mf</b>. {intro}</p>
          <table class="roomy" style="font-size:10.5px;"><tr><th>Test part</th><th>Filament</th><th>What it proves</th></tr>{crows}</table>
          {record}""", chapter=1)

    proof_record_rows = "".join(
        f'<tr><td><b>{esc(PROOF_TITLES.get(key, key))}</b></td><td>{esc(value["material"])}</td>'
        '<td>&nbsp;</td><td>&nbsp;</td><td>&#9633; P&nbsp; &#9633; F</td><td>&nbsp;</td><td>&nbsp;</td></tr>'
        for key, value in PROOFS.items())
    add(f"""
      {eyebrow(1)}
      <h2>Proof qualification record — blank means OPEN</h2>
      <div style="display:grid; grid-template-columns:1.3fr 1fr 1fr; gap:.1in; margin-bottom:.1in; font-size:10px;">
        <div><b>Printer / serial:</b> ____________________</div>
        <div><b>Nozzle:</b> ______</div><div><b>Date started:</b> __________</div>
      </div>
      <table style="font-size:8.2px; table-layout:fixed;">
        <tr><th style="width:1.45in;">Test</th><th style="width:1.1in;">Required family</th>
        <th style="width:1.55in;">Exact product + color</th><th style="width:1.7in;">Settings + measurements</th>
        <th style="width:.72in;">Result</th><th style="width:.72in;">Tester</th><th style="width:.72in;">Date</th></tr>
        {proof_record_rows}
      </table>
      <p style="font-size:9px; margin-top:.08in;"><b>Attach detail sheets</b> for loads, cycles, temperatures, photos, and failure notes.
      Every row must identify the exact machine, spool product/color, settings, measured result, tester, and date; another spool family’s pass does not transfer.</p>""",
        chapter=1)

    # Piece inventory
    counts: dict[str, int] = {}
    colors: dict[str, str] = {}
    for pl in PLATES["plates"]:
        for pp in pl["parts"]:
            base = re.sub(r"_i\d+$", "", pp["name"])
            counts[base] = counts.get(base, 0) + 1
            colors[base] = pl["color_hex"]
    cells = ""
    for base, n in counts.items():
        note = " <span style='font-weight:600; font-size:8px; color:var(--ink2);'>(4 spares)</span>" \
            if base == "printed_washer_v2" else ""
        cells += (f'<div class="invcell"><span class="swatch" style="background:{colors[base]}"></span>'
                  f'<img src="{img_uri(GUIDE_IMG / ("thumb_" + base + ".png"))}">'
                  f'<div class="nm">{esc(friendly(base))}</div><div class="ct">&times;{n}{note}</div></div>')
    add(f"""
      {eyebrow(1)}
      <h2>When the printer stops: count your pieces</h2>
      <p style="margin-bottom:.12in;">All {N_PIECES} printed pieces: {N_FUNCTIONAL} installed functional parts,
      {N_SPARES} spare washers, and {N_OPTIONAL} optional cosmetic skin. Line yours up before Chapter 3; the dot shows each piece’s current effective color.</p>
      <div class="invgrid">{cells}</div>""",
        chapter=1)

    # --- Chapter 3: build ----------------------------------------------------
    add(f"""
      <img class="hero" src="{img_uri(IMG / 'codex_robot_body_v2_chassis.png')}">
      <div style="width:4.3in; padding-top:1.05in;">
        {eyebrow(2)}
        <h1 style="font-size:52px;">Build it</h1>
        <p style="font-size:14px; margin-top:.2in; width:3.9in;">Twenty steps. Lay out the parts from each step’s
        GATHER strip before you start, match the big picture, then run the green CHECK.</p>
        <p style="font-size:13px; margin-top:.15in; width:3.9in;">The little <b>FRONT</b> tag on the robot pictures points
        at the robot’s face, so left and right never get confusing. (The wheel-bench step has no robot in it — no tag.)
        Magenta arrows slide floating parts into their landing rings.</p>
        <p style="font-size:13px; margin-top:.15in; width:3.9in;">One rule: <b>go in order.</b> The steps nest —
        skipping ahead means taking things apart later.</p>
        <div style="display:flex; gap:.3in; margin-top:.32in; width:4in; border-top:1px solid var(--line); padding-top:.18in;">
          {"".join(
              '<div style="flex:1;">' + "".join(
                  f'<div style="display:flex; gap:.07in; margin-bottom:.052in; align-items:baseline;">'
                  f'<span style="font-size:9.5px; font-weight:800; color:var(--teal); width:.16in; text-align:right;">{n}</span>'
                  f'<span style="font-size:9.5px; font-weight:500;">{esc(t)}</span></div>'
                  for n, (_, t, *_) in col) + "</div>"
              for col in (list(enumerate(STEPS, start=1))[:10], list(enumerate(STEPS, start=1))[10:]))}
        </div>
      </div>""",
        chapter=2, footer=False, mark="ch2")

    # Steps
    for i, (img_name, title, screws, items, subs, check) in enumerate(STEPS, start=1):
        label = FRONT_LABEL.get(img_name, "&#8601; FRONT")
        front_chip = f'<div class="frontchip">{label}</div>' if label else ""
        direction_text = " ".join((title, *subs, check)).upper()
        axis = (robot_axis_badge(img_name)
                if label is not None and re.search(r"\b(LEFT|RIGHT)\b", direction_text)
                else "")
        arrows = annotation_svg(img_name)
        inset = ""
        if img_name in INSETS:
            inset_img, inset_caption = INSETS[img_name]
            inset = (
                f'<div style="position:absolute; top:.1in; right:.1in; width:2.05in; background:#fff;'
                f' border:1px solid var(--line); border-radius:.1in; overflow:hidden;'
                f' box-shadow:0 1px 6px rgba(0,0,0,.2);">'
                f'<img src="{img_uri(GUIDE_IMG / (inset_img + ".png"))}" style="width:100%; display:block;">'
                f'<div style="font-size:8.5px; font-weight:700; letter-spacing:.06em; padding:.035in .06in;'
                f' color:var(--teal-dk); text-transform:uppercase;">{inset_caption}</div></div>')
        panel_specs = [
            ("image", panel_img, panel_caption)
            for panel_img, panel_caption in EXTRA_PANELS.get(img_name, [])
        ] + [
            ("vector", kind, panel_caption)
            for panel_caption, kind in VECTOR_PANELS.get(img_name, [])
        ]
        if panel_specs:
            panel_count = len(panel_specs)
            panel_h = {1: 2.55, 2: 2.15}.get(panel_count, 1.44)
            chunks = []
            for panel_i, (panel_kind, panel_source, panel_caption) in enumerate(panel_specs):
                top = 0.10 + panel_i * (panel_h + 0.12)
                media_h = panel_h - .38
                if panel_kind == "image":
                    media = (
                        f'<img src="{img_uri(GUIDE_IMG / (panel_source + ".png"))}" '
                        f'style="width:100%; height:{media_h:.2f}in; object-fit:cover; display:block;">')
                else:
                    media = (
                        f'<div style="width:100%; height:{media_h:.2f}in; display:block;">'
                        f'{technical_diagram(panel_source)}</div>')
                chunks.append(
                    f'<div style="position:absolute; top:{top:.2f}in; right:.1in; width:2.25in; background:#fff;'
                    f' border:1px solid var(--line); border-radius:.1in; overflow:hidden;'
                    f' box-shadow:0 1px 6px rgba(0,0,0,.2);">'
                    f'{media}'
                    f'<div style="font-size:8px; font-weight:700; line-height:1.15; padding:.045in .06in;'
                    f' color:var(--teal-dk); text-transform:uppercase;">{panel_caption}</div></div>')
            inset = "".join(chunks)
        cells = strip_cells(img_name, items, screws)
        strip_cls = "strip dense" if len(items) + (1 if screws else 0) >= 6 else "strip"
        lis = "".join(f"<li>{esc(s)}</li>" for s in subs)
        note = ""
        instr_cls = "instr"
        if img_name in STEP_NOTES:
            instr_cls = "instr compact"
            note = (f'<div style="border:2px solid var(--red); color:var(--red); border-radius:.08in;'
                    f' padding:.04in .08in; margin-bottom:.07in; font-size:9.5px; font-weight:700;'
                    f' line-height:1.3;">{esc(STEP_NOTES[img_name])}</div>')
        add(f"""
          <div class="stephead"><div class="stepnum">{i}</div><h2>{esc(title)}</h2>{progress(i)}</div>
          <div class="{strip_cls}"><span class="gather">GATHER</span>{cells}</div>
            <div class="stepbody">
            <div class="imgwrap"><img class="main" src="{img_uri(GUIDE_IMG / (img_name + '.png'))}">
              {arrows}{front_chip}{axis}{inset}</div>
            <div class="{instr_cls}">{note}<ol>{lis}</ol>
              <div class="check"><span class="box"></span><div><b>CHECK</b>{esc(check)}</div></div></div>
          </div>""",
            chapter=2)

    # --- Chapter 4: wire -----------------------------------------------------
    add(f"""
      {eyebrow(3)}
      <h2>Where every electronic part lives</h2>
      <div class="cols">
        <div><img src="{img_uri(IMG / 'codex_robot_body_v2_populated_cutaway.png')}"
             style="width:100%; border-radius:.12in; border:1px solid var(--line-soft);"></div>
        <div>
          <table style="font-size:10.5px;">
            <tr><th>Part</th><th>Home</th><th>Faces</th></tr>
            <tr><td><b>MDDS10 motor board</b></td><td>tower posts, front-center</td><td>terminals RIGHT</td></tr>
            <tr><td><b>Raspberry Pi 5</b></td><td>tower top shelf</td><td>USB ports BACK</td></tr>
            <tr><td><b>Pico 2</b></td><td>floor, right of tower</td><td>USB/SWD service ends accessible; never cabled to Pi</td></tr>
            <tr><td><b>Battery</b></td><td>middle-back floor</td><td>wires BACK</td></tr>
            <tr><td><b>Relay</b></td><td>floor pocket, left</td><td>terminals UP</td></tr>
            <tr><td><b>Fuse block</b></td><td>deck, left half</td><td>wire exit LEFT edge</td></tr>
            <tr><td><b>Regulators (5 V + 6 V)</b></td><td>hang UNDER deck, back half</td><td>6 V wire exit FRONT</td></tr>
            <tr><td><b>Big red button</b></td><td>through the lid</td><td>UP; test with a centered firm press</td></tr>
            <tr><td><b>Mic array</b></td><td>under the lid slots</td><td>UP</td></tr>
            <tr><td><b>Speakers</b></td><td>side shelves</td><td>grilles OUT</td></tr>
            <tr><td><b>ToF distance boards</b></td><td>2 behind face, 2 side windows</td><td>lenses OUT</td></tr>
            <tr><td><b>Bumper feeler switches ×6</b></td><td>pockets under the tray edge</td><td>buttons OUT</td></tr>
            <tr><td><b>Charger inlet + mute</b></td><td>back panel holes</td><td>BACK</td></tr>
            <tr><td><b>Camera</b></td><td>head, pocket behind the face opening</td><td>lens FRONT</td></tr>
            <tr><td><b>Pan + tilt servos</b></td><td>pan inside the neck, tilt in the head’s side</td><td>pan shaft UP, tilt shaft SIDEWAYS</td></tr>
            <tr><td><b>Glow boards ×4</b></td><td>pockets behind the eye + status bars</td><td>lights OUT</td></tr>
          </table>
          <p style="font-size:10px; margin-top:.08in; color:var(--ink2);">The cutaway hides the shell, lid, and head, so parts
          that mount on them — the white neck collar ring, the side speakers — hover at their true installed heights.</p>
          <p style="font-size:10px; margin-top:.05in; color:var(--red);"><b>PROTOTYPE HOLD:</b> This populated cutaway
          proves placement only. MAX98357A mounts, NeoPixel installation, and the exact harness schedule are not released yet.</p>
        </div>
      </div>""",
        chapter=3, mark="ch3")

    # Wiring rules + power map
    rules = "".join(f'<div class="rule">{esc(r)}</div>' for r in WIRE_RULES)
    prow = "".join(f"<tr><td>{esc(a)}</td><td>{esc(b)}</td><td>{esc(c)}</td></tr>" for a, b, c in POWER_MAP)
    add(f"""
      {eyebrow(3)}
      <h2>The wiring rules</h2>
      {rules}
      <h3 style="margin-top:.15in;">The power map (every 12 V wire)</h3>
      <table class="roomy" style="font-size:11.5px;"><tr><th>From</th><th>Through</th><th>To</th></tr>{prow}</table>""",
        chapter=3)

    # SVG power diagram
    add(f"""
      {eyebrow(3)}
      <h2>Power, as a picture</h2>
      <svg viewBox="0 0 1000 560" style="width:100%; height:6.5in;">
        <defs><marker id="a" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
          <path d="M0,0 L6,3 L0,6 z" fill="#6E6553"/></marker></defs>
        <rect x="20" y="230" width="150" height="90" rx="12" fill="#075365"/>
        <text x="95" y="270" fill="#fff" font-size="20" font-weight="bold" text-anchor="middle">BATTERY</text>
        <text x="95" y="295" fill="#9fd4e2" font-size="14" text-anchor="middle">12 V LiFePO4</text>
        <rect x="240" y="150" width="120" height="60" rx="10" fill="#B8892E"/>
        <text x="300" y="177" font-size="14" font-weight="bold" text-anchor="middle" fill="#fff">ACCESSORY</text>
        <text x="300" y="195" font-size="14" font-weight="bold" text-anchor="middle" fill="#fff">FEEDER FUSE</text>
        <rect x="430" y="130" width="170" height="100" rx="10" fill="#22231F"/>
        <text x="515" y="170" fill="#fff" font-size="16" font-weight="bold" text-anchor="middle">FUSE BLOCK</text>
        <text x="515" y="192" fill="#bbb" font-size="12" text-anchor="middle">4 branches; values unset</text>
        <g>
          <rect x="688" y="40" width="214" height="52" rx="10" fill="#fff" stroke="#d8cfb6"/>
          <rect x="688" y="40" width="8" height="52" rx="4" fill="#2b6cb0"/>
          <text x="800" y="62" fill="#22231F" font-size="13" font-weight="bold" text-anchor="middle">BRANCH 1 → 5 V REG</text>
          <text x="800" y="79" fill="#C4230F" font-size="11" text-anchor="middle">PROTECTED PI INPUT BLOCKED</text>
          <rect x="688" y="110" width="214" height="52" rx="10" fill="#fff" stroke="#d8cfb6"/>
          <rect x="688" y="110" width="8" height="52" rx="4" fill="#2f855a"/>
          <text x="800" y="132" fill="#22231F" font-size="13" font-weight="bold" text-anchor="middle">BRANCH 2 → 6 V REG</text>
          <text x="800" y="149" fill="#C4230F" font-size="11" text-anchor="middle">SERVO QUALIFICATION BLOCKED</text>
          <rect x="688" y="180" width="214" height="52" rx="10" fill="#fff" stroke="#d8cfb6"/>
          <rect x="688" y="180" width="8" height="52" rx="4" fill="#8C887E"/>
          <text x="800" y="202" fill="#22231F" font-size="13" font-weight="bold" text-anchor="middle">BRANCH 3 → COVERED SPARE</text>
          <text x="800" y="219" fill="#6E6553" font-size="11" text-anchor="middle">NO LOAD OR FUSE VALUE</text>
          <rect x="688" y="250" width="214" height="52" rx="10" fill="#fff" stroke="#d8cfb6"/>
          <rect x="688" y="250" width="8" height="52" rx="4" fill="#8C887E"/>
          <text x="800" y="272" fill="#22231F" font-size="13" font-weight="bold" text-anchor="middle">BRANCH 4 → COVERED SPARE</text>
          <text x="800" y="289" fill="#6E6553" font-size="11" text-anchor="middle">NO LOAD OR FUSE VALUE</text>
        </g>
        <rect x="240" y="360" width="120" height="60" rx="10" fill="#B8892E"/>
        <text x="300" y="396" font-size="15" font-weight="bold" text-anchor="middle" fill="#fff">MOTOR FUSE</text>
        <rect x="430" y="350" width="150" height="80" rx="10" fill="#22231F"/>
        <text x="505" y="382" fill="#fff" font-size="16" font-weight="bold" text-anchor="middle">RELAY</text>
        <text x="505" y="404" fill="#f0a89d" font-size="11" text-anchor="middle">both E-stop NC + driver</text>
        <text x="505" y="418" fill="#f0a89d" font-size="11" text-anchor="middle">DRIVER PROOF BLOCKED</text>
        <rect x="660" y="350" width="150" height="80" rx="10" fill="#5e2b7a"/>
        <text x="735" y="384" fill="#fff" font-size="15" font-weight="bold" text-anchor="middle">MDDS10</text>
        <text x="735" y="406" fill="#dcf" font-size="12" text-anchor="middle">motor board</text>
        <rect x="860" y="340" width="110" height="44" rx="10" fill="#fff" stroke="#d8cfb6"/>
        <text x="915" y="367" fill="#22231F" font-size="13" font-weight="bold" text-anchor="middle">MOTOR L</text>
        <rect x="860" y="396" width="110" height="44" rx="10" fill="#fff" stroke="#d8cfb6"/>
        <text x="915" y="423" fill="#22231F" font-size="13" font-weight="bold" text-anchor="middle">MOTOR R</text>
        <rect x="20" y="440" width="220" height="70" rx="12" fill="#0B6E84"/>
        <text x="130" y="470" fill="#fff" font-size="14" font-weight="bold" text-anchor="middle">CHARGER PLUG (EN2)</text>
        <text x="130" y="492" fill="#c9ecf5" font-size="11" text-anchor="middle">contact assignments TBD</text>
        <path d="M170,260 C210,260 210,180 240,180" stroke="#C4230F" stroke-width="5" fill="none" marker-end="url(#a)"/>
        <path d="M360,180 L430,180" stroke="#C4230F" stroke-width="5" fill="none" marker-end="url(#a)"/>
        <path d="M600,155 C650,155 650,66 688,66" stroke="#C4230F" stroke-width="4" fill="none" marker-end="url(#a)"/>
        <path d="M600,175 C650,175 650,136 688,136" stroke="#C4230F" stroke-width="4" fill="none" marker-end="url(#a)"/>
        <path d="M600,195 C650,195 650,206 688,206" stroke="#8C887E" stroke-width="4" stroke-dasharray="8 6" fill="none" marker-end="url(#a)"/>
        <path d="M600,215 C650,215 650,276 688,276" stroke="#8C887E" stroke-width="4" stroke-dasharray="8 6" fill="none" marker-end="url(#a)"/>
        <path d="M170,300 C210,300 210,390 240,390" stroke="#C4230F" stroke-width="5" fill="none" marker-end="url(#a)"/>
        <path d="M360,390 L430,390" stroke="#C4230F" stroke-width="5" fill="none" marker-end="url(#a)"/>
        <path d="M580,390 L660,390" stroke="#DFA400" stroke-width="5" fill="none" marker-end="url(#a)"/>
        <path d="M810,368 L860,362" stroke="#DFA400" stroke-width="4" fill="none" marker-end="url(#a)"/>
        <path d="M810,412 L860,418" stroke="#DFA400" stroke-width="4" fill="none" marker-end="url(#a)"/>
        <path d="M130,440 C130,380 95,360 95,320" stroke="#075365" stroke-width="4" fill="none" marker-end="url(#a)"/>
        <text x="300" y="135" font-size="12" fill="#6E6553" text-anchor="middle" font-weight="bold">RED = always-hot 12 V</text>
        <text x="468" y="342" font-size="12" fill="#6E6553" font-weight="bold">YELLOW = motor 12 V, dead unless the relay says so</text>
      </svg>""",
        chapter=3)

    # Signal map
    srow = "".join(f"<tr><td>{esc(a)}</td><td>{esc(b)}</td><td>{esc(c)}</td></tr>" for a, b, c in SIGNAL_MAP)
    add(f"""
      {eyebrow(3)}
      <h2>The signal map (thin wires)</h2>
      <div style="padding:.1in .14in; margin-bottom:.12in; border:2px solid var(--red); color:var(--red); font-size:11px; font-weight:700;">
        PICO USB/SWD ARE SERVICE-ONLY. DO NOT CONNECT THEM TO THE PI INSIDE THE ROBOT.
      </div>
      <table style="font-size:11px;"><tr><th>From</th><th>To</th><th>What travels</th></tr>{srow}</table>
      <div class="cols" style="margin-top:.15in;">
        <div>
          <h3 style="margin-top:0;">Cable neatness</h3>
          <p style="font-size:11.5px;">Quiet wires (signals, audio, sensors) ride the LEFT channel under the deck.
          Power wires ride the RIGHT channel. The camera ribbon goes up the little tunnel beside the neck servo,
          through the hollow neck, into the head. Zip-tie at every printed tie point; no wire may touch a wheel or the fan.</p>
        </div>
        <div>
          <h3 style="margin-top:0;">The meter checklist (preview — runs only after the harness release)</h3>
          <p style="font-size:11.5px;">Nothing below happens today; it goes live with the released harness. First, no shorts: beep-test + to − at the fuse block (no fuses in yet). Then:</p>
          <ol style="font-size:11.5px; margin-left:.25in;">
          <li>Red button held down = relay coil circuit reads OPEN.</li>
          <li>Regulator outputs read 5.0–5.2 V and 6.0 V on the bench before their loads connect.</li>
          <li>Do not choose or install fuses until the measured-load, conductor, inrush, selective-clearing, and thermal evidence is released.</li>
          <li>Charger plug in = motors will not run.</li>
          <li>The eventual first powered test (its own future release) starts with the lid closed with its 4 corner screws; reopen only while shut down with the motor branch physically isolated.</li></ol>
        </div>
      </div>""",
        chapter=3)

    # --- Chapter 5: check & play ---------------------------------------------
    add(f"""
      <img class="hero" src="{img_uri(IMG / 'codex_robot_body_v2_assembled.png')}">
      <div style="width:4.4in; padding-top:.6in;">
        {eyebrow(4)}
        <div style="display:inline-block; background:var(--red); color:white; padding:.06in .12in; font-size:11px; font-weight:800; letter-spacing:.08em;">PROTOTYPE PREVIEW — NO POWERED MOTION</div>
        <h2 style="font-size:36px; letter-spacing:-.8px; margin-top:.12in;">The body preview is assembled</h2>
        <p style="font-size:13px; margin-top:.08in; width:3.9in;">This version really ships the robot’s software: the Pi installer, the
        <span class="mono">robotd</span> body daemon with its supervision dashboard, the fixed Pi-to-Pico message rules, a tested safety
        core that always fails stopped, the wiring plan, and the step-by-step commissioning checklist. What it does <b>not</b> ship:
        production motor outputs, exact wire lengths and fuse values, or signed physical test results. Do not energize the motor branch from this book.</p>
        <h3 style="margin-top:.2in;">Commissioning gate</h3>
        <p style="font-size:11.5px; width:3.9in;">A released checklist must cover both E-stop NC channels and physical reset;
        all six NC bumper zones plus a broken wire; watchdog and setpoint-lease expiry; velocity/acceleration clamps;
        charger inhibit; low-battery cutoff; hardware mic mute with no backfeed; regulator polarity and voltage;
        branch-by-branch power-up; stop latency; motor direction; and a wheels-off-ground run before any floor test.</p>
        <p style="font-size:11.5px; margin-top:.1in; width:3.9in;">Until those physical results and production integrations exist,
        the body’s number one rule is wonderfully easy: <b>admire, measure, and keep the battery out.</b></p>
        <p style="font-size:11.5px; margin-top:.1in; width:3.9in;">The brain is a different story. Nothing on the next three pages
        needs the battery, the motors, or a single open gate — <b>you can wake Rover Bean’s mind up tonight.</b></p>
      </div>""",
        chapter=4, footer=False, mark="ch4")

    # Bench brain: the shipped robotd simulator + dashboard, runnable today.
    add(f"""
      {eyebrow(4)}
      <h2>Wake the brain up tonight (no robot needed)</h2>
      <div style="display:flex; gap:.26in; flex:1;">
        <div style="width:4.15in; flex:none;">
          <p style="font-size:12px;">The robot’s mind ships in this release as two programs: <span class="mono" style="font-size:11px;">robotd</span>,
          the body daemon, and a supervision dashboard. They run on any Mac or Linux computer with Python 3.11 or newer —
          today, before a single part is printed — because <span class="mono" style="font-size:11px;">robotd</span> carries a
          deterministic pretend body (the simulator) for exactly this.</p>
          <p style="font-size:12px; margin-top:.08in;">Open a terminal in the downloaded release folder and type:</p>
          <div class="cmd" style="margin-top:.06in;">python3 -m venv /tmp/rover-bean
/tmp/rover-bean/bin/pip install -e software/robotd \\
    -e software/dashboard
/tmp/rover-bean/bin/robotd --simulate --socket /tmp/robotd.sock \\
    --blackbox /tmp/robotd-blackbox.jsonl &amp;
/tmp/rover-bean/bin/robot-dashboard --socket /tmp/robotd.sock \\
    --blackbox /tmp/robotd-blackbox.jsonl</div>
          <p style="font-size:12px; margin-top:.08in;">Then point a browser at <b>http://127.0.0.1:8072/</b> — the page in this
          picture, live on your desk. It only ever listens to your own computer. When you want the pretend body to perform,
          run <span class="mono" style="font-size:11px;">/tmp/rover-bean/bin/robot-hello --socket /tmp/robotd.sock</span> —
          Rover Bean looks left, looks right, and settles back to center, narrating as it goes. On the real robot this same
          script is the mid-build wake-up: head and lights only, battery still out, no gate crossed.</p>
          <div style="margin-top:.1in; background:var(--cream); border-radius:.1in; padding:.09in .12in;">
            <p style="font-size:10.5px;"><b>It’s a window, not a remote override.</b> The dashboard talks to
            <span class="mono" style="font-size:9.5px;">robotd</span> like every other client. On the real robot the Pico firmware
            still owns safety: it cannot clear an E-stop latch, cannot bypass the open-bumper zero-motion rule, and cannot exceed
            the firmware speed clamps. Release a drive button (or lose the page) and the firmware’s 250&nbsp;ms lease zeros motion by itself.</p>
          </div>
          <div class="check" style="margin-top:.1in;"><span class="box"></span>
            <div><b>CHECK</b> The STATUS card reads <i>robotd reachable · firmware link up</i>, and dragging the head slider changes
            its numbers while the blackbox log grows.</div></div>
        </div>
        <div style="flex:1; display:flex; flex-direction:column;">
          <img src="{img_uri(GUIDE_IMG / 'dashboard_bench.png')}"
               style="width:100%; border-radius:.12in; border:1px solid var(--line-soft);">
          <div class="legend" style="margin-top:.08in;">
            <div><b class="n">1</b><span><b>STATUS</b> — the simulated body reporting in: battery, speed, and the head aimed at
            pan 25.0°, tilt &minus;8.0° from the little session below.</span></div>
            <div><b class="n">2</b><span><b>SAFETY FLAGS + BUMPER LOOPS</b> — quiet chips mean nothing is latched. Six NC zones;
            any open loop means zero motion (D036), and this page can show that but never overrule it.</span></div>
            <div><b class="n">3</b><span><b>DRIVE + HEAD</b> — hold-to-drive buttons and sliders, capped at the firmware limits
            the page prints next to each control.</span></div>
            <div><b class="n">4</b><span><b>BLACKBOX LOG</b> — the flight recorder. Every command from every client lands here
            with its source name. This capture shows a <span class="mono" style="font-size:9.5px;">source="agent"</span> session:
            a head aim, one drive setpoint, a stop.</span></div>
          </div>
        </div>
      </div>""",
        chapter=4)

    # Real brain: the Pi 5 appliance install.
    add(f"""
      {eyebrow(4)}
      <h2>Move the brain into the robot</h2>
      <p style="margin-bottom:.1in; font-size:12px;">The robot’s real computer is the Raspberry Pi 5 from your electronics box. The release
      turns a fresh Pi into the <b>versioned bench appliance</b> — same <span class="mono" style="font-size:11px;">robotd</span>, plus key-only SSH
      through an outbound-only Cloudflare Tunnel (the robot opens no door into your house), recorded shell sessions, and a stable name for the
      safety Pico’s wire. This is the longest recipe in the book; the full card is <b>docs/pi-appliance-provisioning.md</b> in the release. The short version:</p>
      <div class="cols">
        <div>
          <ol style="margin-left:.22in; font-size:11.5px; line-height:1.5;">
            <li style="margin-bottom:.07in;"><b>Flash the microSD</b> with 64-bit Raspberry Pi OS <b>Lite</b> (Bookworm) using Raspberry Pi Imager,
              and boot the Pi once.</li>
            <li style="margin-bottom:.07in;"><b>Make the robot’s only door.</b> In Cloudflare Zero Trust (the free tier is fine): create a named
              Tunnel whose one route points your chosen hostname at <span class="mono" style="font-size:10px;">ssh://localhost:22</span>, protect that
              hostname with an Access application, and install <span class="mono" style="font-size:10px;">cloudflared</span> on the computer you will
              connect from.</li>
            <li style="margin-bottom:.07in;"><b>Prepare three secret files</b> outside the release folder, and never share or commit them:
              an option-free Ed25519 public key, a yescrypt console-password hash, and the Tunnel’s run token (one line each).</li>
            <li style="margin-bottom:.07in;"><b>Run the installer on the Pi</b> from the release folder:</li>
          </ol>
          <div class="cmd">sudo software/install.sh \\
  --ssh-public-key-file  /secure/path/agent.pub \\
  --tunnel-token-file    /secure/path/tunnel.token \\
  --console-password-hash-file /secure/path/console.hash \\
  --access-ready</div>
          <ol start="5" style="margin-left:.22in; font-size:11.5px; line-height:1.5; margin-top:.08in;">
            <li style="margin-bottom:.07in;"><b>Keep that first session open.</b> From your second computer, SSH in through the tunnel, run the
              two attestation commands from the recipe card, and only then close the original session.</li>
            <li><b>Reboot once and prove the two serial ports</b> exactly as the card shows: the debug console still answers, and the Pico’s future
              wire is pinned to <span class="mono" style="font-size:10px;">/dev/rover-pico</span> — with the Pico’s USB and SWD still unplugged. They are
              service corridors, never robot wiring.</li>
          </ol>
        </div>
        <div>
          <h3 style="margin-top:0;">What the installer refuses to do (on purpose)</h3>
          <div class="rule">It does not start <span class="mono" style="font-size:10px;">robotd</span>. On a first install the body daemon is parked —
          stopped and disabled — until the commissioning plan says otherwise.</div>
          <div class="rule">It does not touch the Pico, the motor branch, or any power wiring. Software cannot close a physical gate.</div>
          <div class="rule">It does not reboot for you, and it never prints your secrets.</div>
          <h3 style="margin-top:.16in;">When the verifier stays red</h3>
          <p style="font-size:11.5px;">The live check (<span class="mono" style="font-size:10px;">appliance.py verify --live</span>) stays red until
          the SSH, console, and independent audit-collector attestations all exist. Red here is the system telling the truth about missing evidence —
          not a sad robot. The 27-step commissioning plan in the release closes it.</p>
          <div class="check" style="margin-top:.14in;"><span class="box"></span>
            <div><b>CHECK</b> A fresh SSH login works through the tunnel, both serial-port readbacks match the card, and
            <span class="mono" style="font-size:9.5px;">systemctl status robotd</span> reports it parked (inactive, disabled) — exactly as shipped.</div></div>
        </div>
      </div>""",
        chapter=4)

    # The resident agent: the copilot's seat, its floor, and its journal.
    add(f"""
      {eyebrow(4)}
      <h2>The copilot takes the seat</h2>
      <div class="cols">
        <div>
          <p style="font-size:12px;">Rover Bean’s resident narrator is a frontier AI copilot — <b>Claude or Codex, one at a time</b> —
          living on the robot’s own computer. Through the tunnel you built on the last page, it gets the whole seat by design:
          it can log in from anywhere, read its own sensors, write and run new code for itself, install what it needs, and send
          drive and head setpoints to <span class="mono" style="font-size:11px;">robotd</span> like any other client. Root on the Pi
          is the copilot’s to hold.</p>
          <h3 style="margin-top:.14in;">The floor it can never cross</h3>
          <p style="font-size:11.5px;">Root on the Pi is <b>not</b> root on physics. Every hard guarantee lives in the safety Pico’s
          firmware and in real circuits the Pi cannot reach — there is no way to reflash or reconfigure the Pico over the robot’s
          one UART wire, and its USB/SWD service plugs are never cabled in operation:</p>
          <div class="rule">Speed and acceleration clamps trim every setpoint, whoever sends it.</div>
          <div class="rule">A drive setpoint dies in 250&nbsp;ms unless refreshed — a crashed or distracted driver coasts to a stop.</div>
          <div class="rule">Any open bumper loop means zero motion, latched until cleared. Same for the E-stop, the charger plug,
          low battery, and a lost heartbeat.</div>
          <div class="rule">The BIG RED BUTTON and the microphone mute switch are physical. No software — copilot included — can
          press or unpress them.</div>
          <p style="font-size:11.5px; margin-top:.08in;">House rules like quiet hours and no-go rooms are <i>policy</i> the copilot
          is instructed to honor and the journal audits; the hardware floor above is what makes even a misbehaving brain safe to stop.</p>
        </div>
        <div>
          <h3 style="margin-top:0;">Everything on the record</h3>
          <p style="font-size:11.5px;">Every <span class="mono" style="font-size:10px;">robotd</span> command carries a source name into
          the blackbox journal, and every shell session on the Pi is recorded and mirrored off the robot (the commissioning plan is what
          proves the off-robot copy can’t be quietly edited). You met the journal on the dashboard page — its
          <span class="mono" style="font-size:9.5px;">source="agent"</span> lines are a copilot session exactly as it will appear on the real robot.</p>
          <h3 style="margin-top:.16in;">Try the copilot’s hands yourself</h3>
          <p style="font-size:11.5px;">With the bench simulator from two pages ago still running:</p>
          <div class="cmd">/tmp/rover-bean/bin/robotctl --socket /tmp/robotd.sock \\
    --source agent head 2500 -800
/tmp/rover-bean/bin/robotctl --socket /tmp/robotd.sock \\
    --source agent drive 120 0
/tmp/rover-bean/bin/robotctl --socket /tmp/robotd.sock \\
    --source agent stop</div>
          <p style="font-size:11px; margin-top:.06in;">Head angles are hundredths of a degree (2500 = pan 25.00°); drive takes forward
          speed (mm/s), then turn rate (0 = straight). Watch the dashboard while you type — and notice the drive setpoint zeroing itself
          a quarter-second after you stop refreshing it.</p>
          <h3 style="margin-top:.16in;">Then, when the gates close</h3>
          <p style="font-size:11.5px;">Today the copilot’s robot is the simulator plus a parked body daemon — that is this release,
          honestly. As your printed proofs, purchased parts, harness, and the 27-step commissioning record close the gates on the
          previous pages, the very same seat starts the real wheels. You built its body; it will help you finish its own bring-up.</p>
          <div class="check" style="margin-top:.12in;"><span class="box"></span>
            <div><b>CHECK</b> All three commands answer <span class="mono" style="font-size:9.5px;">"accepted": true</span>, appear in
            the blackbox with <span class="mono" style="font-size:9.5px;">source="agent"</span>, and the STATUS card’s head numbers match
            the aim you sent.</div></div>
        </div>
      </div>""",
        chapter=4)

    # --- Back cover ----------------------------------------------------------
    features = "".join(
        f'<div style="display:flex; gap:.14in; margin-bottom:.17in; align-items:flex-start;">'
        f'<div style="flex:none; width:.34in; height:.34in; border-radius:.09in; background:rgba(255,255,255,.12);'
        f' display:flex; align-items:center; justify-content:center;">{icon}</div>'
        f'<div><div style="font-size:12.5px; font-weight:700; letter-spacing:.06em; color:#fff;">{t}</div>'
        f'<div style="font-size:11px; color:#B7D6DE; line-height:1.4;">{d}</div></div></div>'
        for icon, t, d in [
            ('<svg width="18" height="18" viewBox="0 0 18 18"><circle cx="9" cy="9" r="6.5" fill="none" stroke="#B9E44A" stroke-width="1.8"/><path d="M9 5.2 12.3 7.1 12.3 10.9 9 12.8 5.7 10.9 5.7 7.1 Z" fill="none" stroke="#B9E44A" stroke-width="1.4"/></svg>',
             "ONE SCREW, ONE KEY",
             f"Every one of the {N_SCREWS} screws you buy is the same M3 × 8, and one 2.5 mm hex key turns them all. M3 is the only fastener thread in the robot."),
            ('<svg width="18" height="18" viewBox="0 0 18 18"><path d="M2.5 13.5 H15.5 M2.5 10 H15.5 M2.5 6.5 H15.5" stroke="#B9E44A" stroke-width="1.8" stroke-linecap="round"/><path d="M9 4.5 V1.5 M7.2 3 L9 1.2 L10.8 3" stroke="#B9E44A" stroke-width="1.5" fill="none" stroke-linecap="round"/></svg>',
             "ZERO SUPPORTS",
             f"{N_FUNCTIONAL} functional + {N_SPARES} spare + {N_OPTIONAL} optional pieces target {N_PLATES} prototype plates. Physical gates remain open."),
            ('<svg width="18" height="18" viewBox="0 0 18 18"><path d="M5.6 2.2 H12.4 L15.8 5.6 V12.4 L12.4 15.8 H5.6 L2.2 12.4 V5.6 Z" fill="none" stroke="#B9E44A" stroke-width="1.8" stroke-linejoin="round"/></svg>',
             "FAILS STOPPED",
             "The E-stop is physically independent. The tested bench safety core defines bumper, lease, and watchdog stops; physical commissioning remains open."),
        ])
    add(f"""
      <div style="position:absolute; inset:0; background:var(--teal-dk); padding:.65in .75in; display:flex; flex-direction:column;">
        <div style="font-size:11px; font-weight:700; letter-spacing:.24em; color:#7FB6C4;">CODEX ROVER BEAN</div>
        <div style="position:absolute; left:.75in; top:.92in; background:#C4230F; color:#fff; padding:.07in .12in; font-size:10px; font-weight:800; letter-spacing:.08em;">PROTOTYPE PREVIEW — NO POWERED MOTION</div>
        <div style="display:flex; gap:.55in; flex:1; align-items:center;">
          <div style="width:4.1in;">
            <div style="font-size:33px; font-weight:800; color:#fff; line-height:1.12; letter-spacing:-.5px; margin-bottom:.32in;">
              Print proofs.<br>Dry-build the chassis.<br>Measure everything.</div>
            {features}
          </div>
          <div style="flex:1;">
            <div style="border-radius:.16in; overflow:hidden; border:1px solid rgba(255,255,255,.18);">
              <img src="{img_uri(IMG / 'codex_robot_body_v2_populated_cutaway.png')}" style="width:100%; display:block;"></div>
            <p style="font-size:10px; color:#7FB6C4; margin-top:.08in; text-align:center; letter-spacing:.08em;">
              INSIDE: RASPBERRY PI 5 BRAIN &middot; SAFETY CO-PILOT &middot; FAIL-STOPPED POWER</p>
            <div style="display:flex; align-items:center; gap:.12in; margin-top:.14in; padding:.1in; border:1px solid rgba(255,255,255,.2); border-radius:.1in;">
              <img src="{img_uri(RELEASE_QR)}" style="width:.72in; height:.72in; background:#fff; image-rendering:pixelated;">
              <div><div style="font-size:10px; font-weight:800; color:#fff; letter-spacing:.08em;">PERMANENT BUILD SOURCE</div>
              <div style="font-size:9px; color:#B7D6DE; margin-top:.03in;">{RELEASE_ID}<br>3MF downloads · exact BOM · software · open gates</div></div>
            </div>
          </div>
        </div>
        <div style="display:flex; justify-content:space-between; font-size:9.5px; font-weight:600;
             letter-spacing:.14em; color:#7FB6C4;">
          <span>BODY V2 &middot; PRINTED-ONLY STRUCTURE</span>
          <span>github.com/brianpattison/robot</span>
        </div>
      </div>""",
        footer=False, mark="back")

    return pages


def build_cover(chapter_pages):
    toc_rows = ""
    for idx, (label, color, name, desc) in enumerate(CHAPTERS):
        toc_rows += (f'<div class="row"><span class="n" style="color:{color}">{idx + 1}</span>'
                     f'<span class="t">{name}</span><span class="d">{desc}</span>'
                     f'<span class="lead"></span><span class="pg">{chapter_pages[idx]}</span></div>')
    # The ages chip is D039's plain-language bar (a ten-year-old with an
    # adult can follow the book), not an age grading or safety claim —
    # keep it, and keep it worded simply.
    chips = "".join(f'<span class="statchip">{c}</span>' for c in
                    ("AGES 10+ WITH AN ADULT", f"{N_FUNCTIONAL} FUNCTIONAL + {N_SPARES} SPARE + {N_OPTIONAL} OPTIONAL",
                     f"{N_PLATES} PLATES", "ONE SCREW SIZE"))
    return f"""
      <img class="hero" src="{img_uri(IMG / 'codex_robot_body_v2_assembled.png')}">
      <div style="width:4.4in; padding-top:.55in;">
        <div class="eyebrow" style="color:var(--gold);"><i style="background:var(--gold)"></i>A prototype print-and-build preview</div>
        <div style="display:inline-block; margin:.08in 0 .04in; background:var(--red); color:#fff; padding:.07in .12in; font-size:11px; font-weight:800; letter-spacing:.08em;">DO NOT USE FOR POWERED MOTION</div>
        <h1 style="font-size:55px;">CODEX<br>ROVER BEAN</h1>
        <p style="font-size:19px; font-weight:600; margin-top:.16in;">The Robot Body Builder’s Book</p>
        <p style="font-size:13px; margin-top:.08in; color:var(--ink2);">Review the geometry, print proofs, and dry-build the released chassis steps.<br>
        Bench software/firmware and evidence runners ship; production wiring, powered outputs, head physical qualification, and signed commissioning remain open.</p>
        <div style="display:flex; gap:.09in; margin-top:.22in; flex-wrap:wrap;">{chips}</div>
        <div class="toc">{toc_rows}</div>
        <p style="font-size:9.5px; font-weight:600; letter-spacing:.14em; color:#A2967C; margin-top:.28in;">
          BODY V2 &middot; ZERO SUPPORTS &middot; {N_SCREWS} SCREWS, ONE SIZE</p>
      </div>"""


def check_images(pages_html):
    missing = []
    for pg in pages_html:
        for source in re.findall(r'src="([^"]+)"', pg):
            if source.startswith(("data:", "http://", "https://")):
                continue
            if not (HTML_OUT.parent / source).resolve().exists():
                missing.append(source)
    if missing:
        raise SystemExit("MISSING GUIDE IMAGES:\n" + "\n".join(missing))


def main():
    HTML_OUT.parent.mkdir(parents=True, exist_ok=True)
    PDF_OUT.parent.mkdir(parents=True, exist_ok=True)
    ensure_release_qr()
    body_pages = build_body_pages()
    total = len(body_pages) + 1
    # Chapter start page numbers (cover is page 1; body pages start at 2).
    chapter_pages = []
    for idx in range(len(CHAPTERS)):
        first = next(i for i, p in enumerate(body_pages) if p["mark"] == f"ch{idx}")
        chapter_pages.append(first + 2)
    cover = {"html": build_cover(chapter_pages), "chapter": None, "footer": False, "mark": "cover"}
    pages = [cover] + body_pages
    check_images([p["html"] for p in pages])
    body = "".join(
        page(p["html"], chapter=p["chapter"], footer=p["footer"], num=i, total=total)
        for i, p in enumerate(pages, start=1))
    html_doc = ("<!doctype html><html><head><meta charset='utf-8'>"
                "<title>Codex Rover Bean — Builder’s Book</title>"
                f"<style>{CSS}</style></head><body>{body}</body></html>")
    html_doc = "\n".join(line.rstrip() for line in html_doc.splitlines()) + "\n"
    HTML_OUT.write_text(html_doc, encoding="utf-8")
    # Chrome will not reliably replace an existing --print-to-pdf target. A
    # mere existence check therefore accepts a stale book while claiming the
    # new page count. Remove only this exact generated artifact, then prove the
    # replacement has the authored number of fixed pages.
    PDF_OUT.unlink(missing_ok=True)
    result = subprocess.run(
        [CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
         "--no-margins", f"--print-to-pdf={PDF_OUT}", HTML_OUT.resolve().as_uri()],
        capture_output=True, text=True, timeout=300)
    if result.returncode != 0 or not PDF_OUT.exists():
        raise SystemExit(f"Chrome PDF failed:\n{result.stderr[-2000:]}")
    import pypdfium2 as pdfium
    emitted_pages = len(pdfium.PdfDocument(PDF_OUT))
    if emitted_pages != total:
        raise SystemExit(
            f"Chrome PDF page mismatch: authored {total}, emitted {emitted_pages}. ")
    print(f"wrote {HTML_OUT}")
    print(f"wrote {PDF_OUT} ({emitted_pages} pages, verified)")


if __name__ == "__main__":
    main()
