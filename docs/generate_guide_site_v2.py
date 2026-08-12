"""Generate the interactive builder's site: the v2 guide as an offline-first web app.

The site and the PDF book are two renderers over ONE content source: this
module imports `generate_assembly_guide_v2` and reuses its live-manifest loads
and authored content (steps, notes, shop tables, proof copy, wiring maps,
annotation arrows) verbatim, so the two outputs cannot drift from each other
or from the CAD model. D029/D039 still govern every word shown to a builder.

What the site adds over the book:
  - persistent build progress in localStorage (shop, plates, pieces, proofs,
    steps, gather strips) with an exportable/importable build log JSON;
  - step-per-screen build mode with keyboard/swipe navigation, animated
    insertion arrows, and a screen wake-lock toggle for the workbench;
  - live release-gate styling for blocked shopping rows, a user-entered
    price column with running totals (the repo publishes no prices);
  - per-plate filament mass + print-time PLANNING estimates computed from the
    exported print STLs (confirm in the slicer; they are not release data);
  - digital proof record forms matching the proofs manifest process_record
    schema, exportable as JSON;
  - a Check & play page that (like everything here) works with the internet
    down and links the localhost robotd dashboard when one is running.

The site never authorizes powered motion and repeats the book's holds.

Run the v2 chain and both render passes first, then:
    .venv-cad/bin/python docs/generate_guide_site_v2.py
Outputs:
    output/site/index.html   (self-contained app; images under output/site/img/)
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import generate_assembly_guide_v2 as book  # noqa: E402  (shared content source)
from builder_release_catalog_v2 import SHOP_BENCH_GEAR  # noqa: E402
from guide_estimates_v2 import plate_estimates  # noqa: E402  (shared numbers)

ROOT = book.ROOT
SITE_OUT = ROOT / "output" / "site"
SITE_IMG = SITE_OUT / "img"


def esc(s):
    return book.esc(s)


# ---------------------------------------------------------------------------
# Asset copying
# ---------------------------------------------------------------------------
def copy_assets() -> None:
    SITE_IMG.mkdir(parents=True, exist_ok=True)
    for src in sorted(book.GUIDE_IMG.glob("*.png")):
        shutil.copy2(src, SITE_IMG / src.name)
    for hero in ("codex_robot_body_v2_assembled.png", "codex_robot_body_v2_rear.png"):
        src = book.IMG / hero
        if src.exists():
            shutil.copy2(src, SITE_IMG / hero)


def simg(name: str) -> str:
    return f"img/{name}"


def check_site_images(html_text: str) -> None:
    import re

    missing = []
    for m in re.finditer(r'src="img/([^"]+)"', html_text):
        if not (SITE_IMG / m.group(1)).exists():
            missing.append(m.group(1))
    if missing:
        raise SystemExit(f"site references missing images: {sorted(set(missing))[:8]}")


# ---------------------------------------------------------------------------
# View builders (HTML strings; interactivity handled by the JS at the bottom)
# ---------------------------------------------------------------------------
def home_view() -> str:
    chips = "".join(
        f'<span class="statchip">{c}</span>' for c in (
            "AGES 10+ WITH AN ADULT",
            f"{book.N_FUNCTIONAL} FUNCTIONAL + {book.N_SPARES} SPARE + {book.N_OPTIONAL} OPTIONAL",
            f"{book.N_PLATES} PLATES", "ONE SCREW SIZE"))
    cards = ""
    routes = ["shop", "print", "build", "wire", "play"]
    for i, (label, color, name, desc) in enumerate(book.CHAPTERS):
        cards += (
            f'<a class="chapcard" href="#{routes[i]}" style="--chap:{color}">'
            f'<span class="chapnum">{i + 1}</span>'
            f'<span class="chapname">{name}</span>'
            f'<span class="chapdesc">{esc(desc.replace("&amp;", "&"))}</span>'
            f'<span class="chapprog" data-chapter-progress="{routes[i]}"></span></a>')
    dots_front = "".join(
        f'<div class="callout" style="left:{x}%; top:{y}%;">{k}</div>'
        for k, (x, y, _) in enumerate(book.MEET_FRONT, start=1))
    legend_front = "".join(
        f'<div class="legendrow"><b class="n">{k}</b><span>{esc(t)}</span></div>'
        for k, (_, _, t) in enumerate(book.MEET_FRONT, start=1))
    dots_rear = "".join(
        f'<div class="callout" style="left:{x}%; top:{y}%;">{k}</div>'
        for k, (x, y, _) in enumerate(book.MEET_REAR, start=1))
    legend_rear = "".join(
        f'<div class="legendrow"><b class="n">{k}</b><span>{esc(t)}</span></div>'
        for k, (_, _, t) in enumerate(book.MEET_REAR, start=1))
    return f"""
<section class="view" id="view-home">
  <div class="hero">
    <div class="hero-copy">
      <p class="eyebrow gold">A prototype print-and-build preview</p>
      <p class="badge-red">DO NOT USE FOR POWERED MOTION</p>
      <h1>CODEX<br>ROVER BEAN</h1>
      <p class="subtitle">The Robot Body Builder&rsquo;s Site</p>
      <p class="intro">Review the geometry, print proofs, and dry-build the released chassis
      steps. Bench software/firmware and evidence runners ship; production wiring, powered
      outputs, head physical qualification, and signed commissioning remain open.</p>
      <div class="chips">{chips}</div>
      <div class="progressband">
        <div class="ring"><svg viewBox="0 0 44 44"><circle class="ring-bg" cx="22" cy="22" r="19"/>
        <circle class="ring-fg" cx="22" cy="22" r="19" data-progress-ring/></svg>
        <b data-progress-pct>0%</b></div>
        <div><b>Your build</b><span data-progress-summary>Nothing checked yet — start in Shop.</span>
        <div class="logbtns"><button class="mini" data-export-log>Save build log</button>
        <label class="mini">Load log<input type="file" accept="application/json" data-import-log hidden></label></div></div>
      </div>
    </div>
    <img class="hero-img" src="{simg('codex_robot_body_v2_assembled.png')}" alt="Rover Bean, assembled render">
  </div>
  <div class="chapgrid">{cards}</div>
  <h2>This is Rover Bean</h2>
  <div class="meet">
    <figure><div class="callwrap"><img src="{simg('codex_robot_body_v2_assembled.png')}" alt="Front view">{dots_front}</div>
      <figcaption>From the front</figcaption><div class="legend">{legend_front}</div></figure>
    <figure><div class="callwrap"><img src="{simg('codex_robot_body_v2_rear.png')}" alt="Back view">{dots_rear}</div>
      <figcaption>From the back</figcaption><div class="legend">{legend_rear}</div></figure>
  </div>
  <p class="release">Permanent build source: <a href="{esc(book.RELEASE_URL)}">{esc(book.RELEASE_ID)}</a>
  &mdash; 3MF downloads &middot; exact BOM &middot; software &middot; open gates.
  <img class="qr" src="{simg(book.RELEASE_QR.name)}" alt="QR code to the builder release"></p>
</section>"""


def shop_view() -> str:
    fil_rows = ""
    for i, (label, amount, becomes) in enumerate(book.SHOP_FILAMENT):
        fil_rows += (f'<label class="checkrow" data-check="shop" data-key="fil{i}">'
                     f'<input type="checkbox"><b>{esc(label)}</b>'
                     f'<span>{esc(amount)} &mdash; {esc(becomes)}</span></label>')
    fast_rows = ""
    for i, (label, amount, why) in enumerate(book.SHOP_FASTENERS):
        fast_rows += (f'<label class="checkrow" data-check="shop" data-key="fast{i}">'
                      f'<input type="checkbox"><b>{esc(label)}</b>'
                      f'<span>{esc(amount)} &mdash; {esc(why)}</span></label>')
    tool_rows = ""
    for i, (label, why) in enumerate(book.SHOP_TOOLS):
        tool_rows += (f'<label class="checkrow" data-check="shop" data-key="tool{i}">'
                      f'<input type="checkbox"><b>{esc(label)}</b><span>{esc(why)}</span></label>')
    bench_rows = ""
    for i, (label, qty, why) in enumerate(SHOP_BENCH_GEAR):
        bench_rows += (f'<label class="checkrow" data-check="shop" data-key="bench{i}">'
                       f'<input type="checkbox"><b>{esc(label)} <i class="qty">&times;{esc(qty)}</i></b>'
                       f'<span>{esc(why)}</span></label>')

    elec_rows = ""
    for i, (name, qty, what) in enumerate(book.SHOP_ELECTRONICS):
        # A row is a gate only when the quantity itself says so or the copy
        # leads with the hold; rows that are safe to buy but carry a wiring
        # caveat (D24V90F5, ReSpeaker) stay checkable with their caveat shown.
        blocked = qty in ("0 for now", "not released") or what.startswith("DO NOT BUY YET")
        cls = "checkrow blocked" if blocked else "checkrow"
        price = ("" if blocked else
                 f'<span class="price">$<input type="number" min="0" step="0.01" '
                 f'placeholder="0.00" data-price="{i}" inputmode="decimal"></span>')
        box = "" if blocked else '<input type="checkbox">'
        gate = '<span class="gatechip">GATE OPEN — DO NOT BUY YET</span>' if blocked else ""
        elec_rows += (f'<label class="{cls}" data-check="shop" data-key="elec{i}">{box}'
                      f'<b>{esc(name)} <i class="qty">&times;{esc(qty)}</i>{gate}</b>'
                      f'<span>{esc(what)}</span>{price}</label>')

    visuals = "".join(
        f'<figure class="matchcell"><img src="{simg(t)}" alt="{esc(lbl)}" loading="lazy">'
        f'<figcaption>{esc(lbl)}</figcaption></figure>'
        for t, lbl in book.SHOP_VISUALS if (SITE_IMG / t).exists() or (book.GUIDE_IMG / t).exists())

    return f"""
<section class="view" id="view-shop">
  <p class="eyebrow gold">Chapter 1 &middot; Shop</p>
  <h1>Go shopping: plastic, screws, tools</h1>
  <p class="lead">Check things off as they arrive — this page remembers. Rows marked
  <b>GATE OPEN</b> are decisions still to close, not shopping instructions: skip them, and the
  build pauses exactly where the steps say. The repo publishes no prices, so the price column
  is yours: type what you actually paid and the site totals it.</p>
  <div class="shoptotal">Your spend so far: <b data-shop-total>$0.00</b>
  <span data-shop-count></span></div>
  <h2>Filament</h2><div class="checklist">{fil_rows}</div>
  <h2>The only two fastener packs</h2><div class="checklist">{fast_rows}</div>
  <h2>Tools</h2><div class="checklist">{tool_rows}</div>
  <h2>Bench equipment (for the check-out chapters)</h2>
  <p class="lead">Commissioning tools, not robot parts — the measured-evidence steps assume
  these instruments.</p>
  <div class="checklist">{bench_rows}</div>
  <h2>The electronics box</h2><div class="checklist">{elec_rows}</div>
  <h2>Match the electronics</h2>
  <p class="lead">When a box arrives, match it to its picture.</p>
  <div class="matchgrid">{visuals}</div>
</section>"""


def print_view(estimates: dict[int, dict]) -> str:
    tips = "".join(
        f'<div class="tipcard"><b>{esc(t)}</b><span>{d}</span></div>'
        for t, d in book.PRINT_TIPS)
    total_g = sum(e["grams"] for e in estimates.values())
    total_h = sum(e["hours"] for e in estimates.values())
    plate_cards = ""
    for plate in book.PLATES["plates"]:
        n = plate["plate_number"]
        est = estimates.get(n, {"grams": 0, "hours": 0})
        parts = ", ".join(book.friendly(p["name"].rsplit("_i", 1)[0] if "_i" in p["name"]
                                        else p["name"]) for p in plate["parts"])
        tab = plate.get("qc_tab")
        tabline = (f'<span class="tabline">+ check tab {esc(tab["name"])}</span>' if tab else "")
        plate_cards += f"""
    <label class="platecard" data-check="plates" data-key="p{n}">
      <input type="checkbox">
      <span class="platehead"><i class="swatch" style="background:{esc(plate.get('color_hex', '#ccc'))}"></i>
      <b>Plate {n}</b><span class="platemat">{esc(plate['material'])}</span></span>
      <span class="platename">{esc(plate['name'])}</span>
      <span class="plateparts">{esc(parts)}{tabline}</span>
      <span class="plateest">&approx;{est['grams']} g &middot; &approx;{est['hours']:g} h
      <i>planning estimate — confirm in the slicer</i></span>
    </label>"""

    pieces = ""
    seen = []
    for plate in book.PLATES["plates"]:
        for p in plate["parts"]:
            base = p["name"].rsplit("_i", 1)[0] if "_i" in p["name"] else p["name"]
            seen.append(base)
    from collections import Counter

    counts = Counter(seen)
    for base, cnt in sorted(counts.items(), key=lambda kv: book.friendly(kv[0])):
        thumb = f"thumb_{base}.png"
        img = (f'<img src="{simg(thumb)}" alt="" loading="lazy">'
               if (SITE_IMG / thumb).exists() or (book.GUIDE_IMG / thumb).exists() else
               '<span class="noimg"></span>')
        pieces += (f'<label class="piececell" data-check="pieces" data-key="{esc(base)}">'
                   f'<input type="checkbox">{img}<b>{esc(book.friendly(base))}</b>'
                   f'<span>&times;{cnt}</span></label>')

    proof_cards = ""
    for key in book.PROOFS:
        title = book.PROOF_TITLES.get(key, key)
        note = book.PROOF_NOTES.get(key, "")
        material = book.PROOFS[key].get("material", "")
        proof_cards += f"""
    <details class="proofcard" data-proof="{esc(key)}">
      <summary><b>{esc(title)}</b><span class="proofmat">{esc(material)}</span>
      <span class="proofstate" data-proof-state></span></summary>
      <p>{esc(note)}</p>
      <div class="prooffields">
        <label>Filament (maker, line, color)<input type="text" data-field="material_line"></label>
        <label>Insert tool temp (&deg;C)<input type="number" data-field="insert_tool_temperature_c"></label>
        <label>What you measured / saw<textarea rows="2" data-field="measured_results"></textarea></label>
        <label>Result<select data-field="pass_fail"><option value="">open</option>
          <option value="pass">pass</option><option value="fail">fail</option></select></label>
        <label>Tested by<input type="text" data-field="tested_by"></label>
        <label>Date<input type="date" data-field="test_date"></label>
      </div>
    </details>"""

    return f"""
<section class="view" id="view-print">
  <p class="eyebrow teal">Chapter 2 &middot; Print</p>
  <h1>Print it with Bambu Studio</h1>
  <div class="tipgrid">{tips}</div>
  <h2>The {book.N_PLATES} prototype plates</h2>
  <p class="lead">Whole job, all plates: &approx;{total_g:,} g of filament and &approx;{total_h:g}
  printer-hours — <b>planning estimates</b> computed from the exported geometry, not release
  data; your slicer's numbers win. Check each plate off as it comes off the bed, and check its
  corner tab first: if the tab's insert bore or screw hole is off, fix the printer before the
  next plate, not after.</p>
  <div class="plategrid">{plate_cards}</div>
  <h2>Every piece, checked in</h2>
  <p class="lead">Cut plates apart, then tap each piece as you match it. {book.N_PIECES} pieces total.</p>
  <div class="piecegrid">{pieces}</div>
  <h2>The 18 qualification proofs</h2>
  <p class="lead">Print the little test pieces first and record what happened — the forms below
  match the proof record in the release, and <b>Save build log</b> on the home page exports them
  as JSON. A failed or blank proof keeps its gate open; it never becomes &ldquo;close
  enough.&rdquo;</p>
  <div class="proofgrid">{proof_cards}</div>
</section>"""


def build_view() -> str:
    index_cards = ""
    for i, (img_name, title, screws, items, subs, check) in enumerate(book.STEPS, 1):
        index_cards += (f'<a class="stepcard" href="#build/{i}" data-step-card="{i}">'
                        f'<span class="stepnum">{i}</span><b>{esc(title)}</b>'
                        f'<i class="stepdone" aria-hidden="true">&check;</i></a>')

    step_views = ""
    for i, (img_name, title, screws, items, subs, check) in enumerate(book.STEPS, 1):
        strip = ""
        for base, qty in items:
            name = book.STRIP_NAME_OVERRIDES.get((img_name, base), book.friendly(base))
            thumb = f"thumb_{base}.png"
            timg = (f'<img src="{simg(thumb)}" alt="" loading="lazy">'
                    if (book.GUIDE_IMG / thumb).exists() else '<span class="noimg"></span>')
            strip += (f'<label class="gathercell" data-check="gathers" data-key="{i}:{esc(base)}">'
                      f'<input type="checkbox">{timg}<b>&times;{qty}</b>'
                      f'<span>{esc(name)}</span></label>')
        if screws:
            strip += (f'<label class="gathercell" data-check="gathers" data-key="{i}:screws">'
                      f'<input type="checkbox"><img src="{simg("thumb_px_screw.png")}" alt="" loading="lazy">'
                      f'<b>&times;{screws}</b><span>M3 screws</span></label>')
        moves = "".join(f"<li>{m}</li>" for m in subs)
        note = book.STEP_NOTES.get(img_name)
        banner = f'<p class="stepbanner">{esc(note)}</p>' if note else ""
        front = book.FRONT_LABEL.get(img_name, "&check; FRONT")
        chip = f'<span class="frontchip">{front}</span>' if front else ""
        badge = book.robot_axis_badge(img_name)
        overlay = book.annotation_svg(img_name)

        panels = ""
        inset = book.INSETS.get(img_name)
        if inset:
            panels += (f'<figure class="panel"><img src="{simg(inset[0] + ".png")}" loading="lazy" '
                       f'alt="{esc(inset[1])}"><figcaption>{esc(inset[1])}</figcaption></figure>')
        for img2, cap in book.EXTRA_PANELS.get(img_name, []):
            panels += (f'<figure class="panel"><img src="{simg(img2 + ".png")}" loading="lazy" '
                       f'alt="{esc(cap)}"><figcaption>{esc(cap)}</figcaption></figure>')
        for cap, kind in book.VECTOR_PANELS.get(img_name, []):
            panels += (f'<figure class="panel vector">{book.technical_diagram(kind)}'
                       f'<figcaption>{esc(cap)}</figcaption></figure>')
        panel_block = f'<div class="panels">{panels}</div>' if panels else ""

        step_views += f"""
  <article class="stepview" id="step-{i}" hidden>
    <header class="stephead"><span class="stepnum">{i}</span><h1>{esc(title)}</h1>
      <span class="stepcount">step {i} of {len(book.STEPS)}</span></header>
    <div class="stepdots">{"".join(f'<i data-dot="{k}"></i>' for k in range(1, len(book.STEPS) + 1))}</div>
    {banner}
    <div class="gather">{strip}</div>
    <div class="stepmedia"><div class="imgwrap">
      <img src="{simg(img_name + '.png')}" alt="Step {i}: {esc(title)}" loading="lazy" decoding="async">{overlay}{chip}{badge}
    </div>{panel_block}</div>
    <ol class="moves">{moves}</ol>
    <label class="checkbar" data-check="steps" data-key="{i}">
      <input type="checkbox"><b>CHECK</b><span>{esc(check)}</span></label>
    <nav class="stepnav">
      <a class="navbtn" href="#build/{i - 1 if i > 1 else 0}">{'&larr; Step ' + str(i - 1) if i > 1 else '&larr; All steps'}</a>
      <a class="navbtn primary" href="#build/{i + 1 if i < len(book.STEPS) else 0}">{'Step ' + str(i + 1) + ' &rarr;' if i < len(book.STEPS) else 'Done — all steps &rarr;'}</a>
    </nav>
  </article>"""

    return f"""
<section class="view" id="view-build">
  <div id="build-index">
    <p class="eyebrow deep">Chapter 3 &middot; Build</p>
    <h1>Build it</h1>
    <p class="lead">Twenty steps. Lay out the parts from each step&rsquo;s GATHER strip, match
    the big picture, then run the green CHECK. One rule: <b>go in order</b> — the steps nest,
    and skipping ahead means taking things apart later. Arrow keys or swipes move between
    steps; your place is saved.</p>
    <div class="stepgrid">{index_cards}</div>
  </div>
  {step_views}
</section>"""


def wire_view() -> str:
    rules = "".join(f'<div class="rulecard">{esc(r)}</div>' for r in book.WIRE_RULES)
    power = "".join(
        f'<tr><td>{esc(a)}</td><td>{esc(b)}</td><td>{esc(c)}</td></tr>'
        for a, b, c in book.POWER_MAP)
    signal = "".join(
        f'<tr><td>{esc(a)}</td><td>{esc(b)}</td><td>{esc(c)}</td></tr>'
        for a, b, c in book.SIGNAL_MAP)
    return f"""
<section class="view" id="view-wire">
  <p class="eyebrow red">Chapter 4 &middot; Wire</p>
  <h1>The wiring rules</h1>
  <p class="stepbanner">This chapter is the REFERENCE MAP for a harness that is not released
  yet — nothing here cuts a wire. Read it to understand the design; build it only when the
  wire/terminal/fuse releases close.</p>
  <div class="rules">{rules}</div>
  <h2>The power map (every 12 V wire)</h2>
  <div class="tablewrap"><table><thead><tr><th>From</th><th>Through</th><th>To</th></tr></thead>
  <tbody>{power}</tbody></table></div>
  <h2>The signal map (thin wires)</h2>
  <p class="stepbanner">PICO USB/SWD ARE SERVICE-ONLY. DO NOT CONNECT THEM TO THE PI INSIDE THE ROBOT.</p>
  <div class="tablewrap"><table><thead><tr><th>From</th><th>To</th><th>What travels</th></tr></thead>
  <tbody>{signal}</tbody></table></div>
</section>"""


def play_view() -> str:
    return f"""
<section class="view" id="view-play">
  <p class="eyebrow lime">Chapter 5 &middot; Check &amp; play</p>
  <h1>Wake the brain up tonight</h1>
  <p class="stepbanner">PROTOTYPE PREVIEW — NO POWERED MOTION. Until the physical gates close,
  the body&rsquo;s number one rule is wonderfully easy: admire, measure, and keep the battery
  out.</p>
  <p class="lead">The robot&rsquo;s mind ships in this release as two programs: <code>robotd</code>,
  the body daemon, and a supervision dashboard. They run on any Mac or Linux computer with
  Python 3.11 or newer — today, before a single part is printed — because <code>robotd</code>
  carries a deterministic pretend body (the simulator) for exactly this.</p>
  <div class="playcard">
    <h2>1 &middot; Run the simulator</h2>
    <pre><code>python3 -m venv /tmp/rover-bean
/tmp/rover-bean/bin/pip install -e software/robotd \\
    -e software/dashboard
/tmp/rover-bean/bin/robotd --simulate --socket /tmp/robotd.sock \\
    --blackbox /tmp/robotd-blackbox.jsonl &amp;
/tmp/rover-bean/bin/robot-dashboard --socket /tmp/robotd.sock \\
    --blackbox /tmp/robotd-blackbox.jsonl</code><button class="mini" data-copy>Copy</button></pre>
    <p>Then open <a href="http://127.0.0.1:8072/" target="_blank" rel="noopener">http://127.0.0.1:8072/</a>
    — it only ever listens to your own computer.</p>
    <p class="dashping" data-dashping hidden>&#9679; A dashboard is answering on
    <a href="http://127.0.0.1:8072/" target="_blank" rel="noopener">127.0.0.1:8072</a> right now —
    your robot&rsquo;s heartbeat is one click away.</p>
  </div>
  <div class="playcard">
    <h2>2 &middot; Say hello</h2>
    <pre><code>/tmp/rover-bean/bin/robot-hello --socket /tmp/robotd.sock</code><button class="mini" data-copy>Copy</button></pre>
    <p>Rover Bean looks left, looks right, and settles back to center — narrated in plain words
    as it goes, journaled in the blackbox as <code>source="hello"</code>. On the real robot this
    same script is the mid-build wake-up milestone: head and lights only, battery still out,
    no safety gate crossed.</p>
  </div>
  <div class="playcard">
    <h2>3 &middot; Move the brain into the robot</h2>
    <p>The full recipe is <code>docs/pi-appliance-provisioning.md</code> in the release. The
    installer refuses to start <code>robotd</code> (parked until commissioning says otherwise),
    never touches the Pico or power wiring, and never prints your secrets.</p>
    <img src="{simg('dashboard_bench.png')}" alt="The supervision dashboard on the bench" loading="lazy">
  </div>
  <div class="playcard">
    <h2>The copilot takes the seat</h2>
    <p>Rover Bean&rsquo;s resident narrator is a frontier AI copilot — Claude or Codex, one at
    a time — living on the robot&rsquo;s own computer. It gets the whole seat by design; the
    floor it can never cross lives in the safety Pico&rsquo;s firmware and in real circuits:
    speed clamps, the 250 ms setpoint lease, latched stops on any open bumper loop, and the BIG
    RED BUTTON no software — copilot included — can press or unpress.</p>
  </div>
  <p class="release">Permanent build source: <a href="{esc(book.RELEASE_URL)}">{esc(book.RELEASE_ID)}</a></p>
</section>"""


# ---------------------------------------------------------------------------
# CSS + JS (plain strings — no f-string interpolation, keep braces natural)
# ---------------------------------------------------------------------------
CSS = """
* { margin:0; padding:0; box-sizing:border-box; }
:root {
  --paper:#FBF7EC; --cream:#F3ECDA; --teal:#0B6E84; --teal-dk:#075365;
  --ink:#22231F; --ink2:#6B6656; --red:#C4230F; --gold:#B8892E; --lime:#74A22D;
  --line:#D9CFB8; --line-soft:#E7DFCC; --magenta:#D41468;
}
body { background:var(--paper); color:var(--ink); font-size:16px; line-height:1.55;
  font-family:"Avenir Next", Avenir, Futura, "Trebuchet MS", sans-serif; }
img { max-width:100%; display:block; }
a { color:var(--teal-dk); }
h1 { font-size:clamp(1.6rem,4.5vw,2.4rem); font-weight:800; color:var(--teal-dk);
  letter-spacing:-.01em; line-height:1.1; margin:.35rem 0 .8rem; text-wrap:balance; }
h2 { font-size:1.25rem; font-weight:800; color:var(--teal-dk); margin:2rem 0 .6rem; }
.lead { max-width:62ch; color:var(--ink); margin-bottom:1rem; }
code, pre { font-family:ui-monospace,"SF Mono",Menlo,monospace; font-size:.86em; }
.topbar { position:sticky; top:0; z-index:40; display:flex; align-items:center; gap:.7rem;
  background:var(--teal-dk); color:#FFF9EE; padding:.55rem .9rem; flex-wrap:wrap; }
.topbar .wordmark { font-weight:800; letter-spacing:.06em; text-decoration:none; color:#FFF9EE; }
.topbar nav { display:flex; gap:.15rem; flex-wrap:wrap; }
.topbar nav a { color:#CFE7ED; text-decoration:none; font-size:.78rem; font-weight:700;
  letter-spacing:.08em; padding:.3rem .55rem; border-radius:999px; }
.topbar nav a.active { background:#FFF9EE; color:var(--teal-dk); }
.topbar .bar { flex:1 1 90px; height:6px; border-radius:3px; background:#0e5568; min-width:60px; }
.topbar .bar i { display:block; height:100%; width:0%; border-radius:3px; background:#9FD468;
  transition:width .3s; }
.wakebtn { background:none; border:1.5px solid #CFE7ED; color:#CFE7ED; border-radius:999px;
  font-size:.72rem; font-weight:700; letter-spacing:.08em; padding:.28rem .6rem; cursor:pointer; }
.wakebtn.on { background:#9FD468; border-color:#9FD468; color:#1E3A08; }
main { max-width:70rem; margin:0 auto; padding:1.2rem 1rem 4rem; }
.view { display:block; }
.eyebrow { font-size:.72rem; font-weight:800; letter-spacing:.16em; text-transform:uppercase; }
.eyebrow::before { content:""; display:inline-block; width:.55em; height:.55em; margin-right:.5em;
  background:currentColor; }
.eyebrow.gold { color:var(--gold); } .eyebrow.teal { color:var(--teal); }
.eyebrow.deep { color:var(--teal-dk); } .eyebrow.red { color:var(--red); }
.eyebrow.lime { color:var(--lime); }
.badge-red { display:inline-block; background:var(--red); color:#fff; font-weight:800;
  font-size:.74rem; letter-spacing:.1em; padding:.35em .7em; margin:.5rem 0; }
.hero { display:flex; gap:1.4rem; align-items:center; flex-wrap:wrap; margin-bottom:1.2rem; }
.hero-copy { flex:1 1 20rem; }
.hero-img { flex:1 1 16rem; max-width:26rem; border-radius:.6rem; border:1px solid var(--line-soft); }
.subtitle { font-weight:700; font-size:1.05rem; margin:.2rem 0 .4rem; }
.intro { color:var(--ink2); max-width:52ch; font-size:.92rem; }
.chips { display:flex; flex-wrap:wrap; gap:.4rem; margin:.8rem 0; }
.statchip { border:1.5px solid var(--ink); border-radius:999px; padding:.22em .7em;
  font-size:.68rem; font-weight:800; letter-spacing:.07em; white-space:nowrap; }
.progressband { display:flex; gap:.9rem; align-items:center; background:var(--cream);
  border:1px solid var(--line-soft); border-radius:.7rem; padding:.7rem .9rem; max-width:30rem; }
.progressband b { display:block; }
.progressband span { font-size:.85rem; color:var(--ink2); }
.ring { position:relative; width:64px; height:64px; flex:none; }
.ring svg { width:64px; height:64px; transform:rotate(-90deg); }
.ring-bg { fill:none; stroke:var(--line-soft); stroke-width:5; }
.ring-fg { fill:none; stroke:var(--lime); stroke-width:5; stroke-linecap:round;
  stroke-dasharray:119.4; stroke-dashoffset:119.4; transition:stroke-dashoffset .4s; }
.ring b { position:absolute; inset:0; display:flex; align-items:center; justify-content:center;
  font-size:.8rem; }
.logbtns { display:flex; gap:.4rem; margin-top:.3rem; }
.mini { font:inherit; font-size:.72rem; font-weight:700; letter-spacing:.05em; cursor:pointer;
  background:#fff; border:1px solid var(--line); border-radius:999px; padding:.2rem .6rem; }
.chapgrid { display:grid; grid-template-columns:repeat(auto-fit,minmax(11rem,1fr)); gap:.6rem;
  margin:1.4rem 0 2rem; }
.chapcard { display:flex; flex-direction:column; gap:.15rem; text-decoration:none; color:var(--ink);
  background:#fff; border:1px solid var(--line-soft); border-top:4px solid var(--chap);
  border-radius:.6rem; padding:.7rem .8rem; }
.chapnum { font-weight:800; color:var(--chap); font-size:.8rem; }
.chapname { font-weight:800; font-size:1.05rem; }
.chapdesc { font-size:.78rem; color:var(--ink2); }
.chapprog { font-size:.72rem; font-weight:700; color:var(--lime); min-height:1em; }
.meet { display:flex; gap:1rem; flex-wrap:wrap; }
.meet figure { flex:1 1 18rem; }
.callwrap { position:relative; border-radius:.6rem; overflow:hidden; border:1px solid var(--line-soft); }
.callout { position:absolute; width:1.5rem; height:1.5rem; border-radius:50%; background:var(--teal);
  color:#fff; font-size:.8rem; font-weight:800; display:flex; align-items:center; justify-content:center;
  transform:translate(-50%,-50%); border:2px solid #FFF9EE; }
.meet figcaption { font-size:.7rem; font-weight:800; letter-spacing:.12em; text-transform:uppercase;
  color:var(--ink2); margin:.35rem 0; }
.legendrow { display:flex; gap:.5rem; font-size:.85rem; margin-bottom:.25rem; }
.legendrow .n { flex:none; width:1.25rem; height:1.25rem; border-radius:50%; background:var(--teal);
  color:#fff; font-size:.72rem; display:flex; align-items:center; justify-content:center; }
.release { margin:2rem 0 0; font-size:.85rem; color:var(--ink2); display:flex; gap:.7rem;
  align-items:center; flex-wrap:wrap; }
.release .qr { width:64px; image-rendering:pixelated; }
.checklist { display:flex; flex-direction:column; gap:.35rem; }
.checkrow { display:grid; grid-template-columns:auto 1fr auto; gap:.15rem .6rem; align-items:start;
  background:#fff; border:1px solid var(--line-soft); border-radius:.5rem; padding:.55rem .7rem;
  cursor:pointer; }
.checkrow input { grid-row:span 2; margin-top:.25rem; width:1.05rem; height:1.05rem; accent-color:var(--lime); }
.checkrow b { font-size:.92rem; }
.checkrow span { grid-column:2; font-size:.8rem; color:var(--ink2); }
.checkrow.done b { color:var(--ink2); text-decoration:line-through; }
.checkrow.blocked { grid-template-columns:1fr; background:var(--cream); cursor:default; }
.checkrow.blocked b, .checkrow.blocked span { grid-column:1; color:var(--ink2); }
.qty { font-style:normal; color:var(--teal); font-weight:800; font-size:.8rem; }
.gatechip { display:inline-block; background:var(--red); color:#fff; font-size:.62rem;
  font-weight:800; letter-spacing:.08em; border-radius:999px; padding:.15em .6em; margin-left:.4em; }
.price { grid-column:3; grid-row:1 / span 2; align-self:center; font-weight:700; }
.price input { width:5.2rem; font:inherit; padding:.2rem .3rem; border:1px solid var(--line);
  border-radius:.35rem; background:var(--paper); }
.shoptotal { position:sticky; top:3.2rem; z-index:10; background:var(--cream); border:1px solid var(--line);
  border-radius:.6rem; padding:.5rem .8rem; margin:.6rem 0 1rem; font-size:.9rem; }
.shoptotal b { color:var(--teal-dk); font-size:1.05rem; }
.shoptotal span { color:var(--ink2); margin-left:.5rem; font-size:.8rem; }
.matchgrid { display:grid; grid-template-columns:repeat(auto-fill,minmax(7.5rem,1fr)); gap:.5rem; }
.matchcell { background:#fff; border:1px solid var(--line-soft); border-radius:.5rem; padding:.4rem; }
.matchcell figcaption { font-size:.72rem; font-weight:700; text-align:center; margin-top:.2rem; }
.tipgrid { display:grid; grid-template-columns:repeat(auto-fit,minmax(14rem,1fr)); gap:.6rem; }
.tipcard { background:#fff; border:1px solid var(--line-soft); border-radius:.6rem; padding:.7rem .8rem; }
.tipcard b { display:block; margin-bottom:.2rem; }
.tipcard span { font-size:.83rem; color:var(--ink2); }
.plategrid { display:grid; grid-template-columns:repeat(auto-fill,minmax(15rem,1fr)); gap:.6rem; }
.platecard { display:flex; flex-direction:column; gap:.3rem; background:#fff; cursor:pointer;
  border:1px solid var(--line-soft); border-radius:.6rem; padding:.65rem .75rem; position:relative; }
.platecard input { position:absolute; top:.7rem; right:.7rem; width:1.1rem; height:1.1rem;
  accent-color:var(--lime); }
.platecard.done { outline:2px solid var(--lime); }
.platehead { display:flex; gap:.45rem; align-items:center; font-size:.95rem; }
.swatch { width:.95rem; height:.95rem; border-radius:50%; border:1px solid var(--line); flex:none; }
.platemat { font-size:.72rem; color:var(--ink2); font-weight:700; }
.platename { font-size:.78rem; color:var(--ink2); }
.plateparts { font-size:.78rem; }
.tabline { display:block; color:var(--gold); font-weight:700; font-size:.74rem; }
.plateest { font-size:.78rem; font-weight:700; color:var(--teal-dk); }
.plateest i { display:block; font-style:normal; font-weight:400; font-size:.68rem; color:var(--ink2); }
.piecegrid { display:grid; grid-template-columns:repeat(auto-fill,minmax(6.8rem,1fr)); gap:.45rem; }
.piececell { background:#fff; border:1px solid var(--line-soft); border-radius:.5rem; padding:.4rem;
  text-align:center; cursor:pointer; position:relative; font-size:.72rem; }
.piececell input { position:absolute; top:.35rem; left:.35rem; accent-color:var(--lime); }
.piececell b { display:block; font-size:.72rem; }
.piececell.done { outline:2px solid var(--lime); }
.noimg { display:block; aspect-ratio:1; background:var(--cream); border-radius:.3rem; }
.proofgrid { display:grid; grid-template-columns:repeat(auto-fit,minmax(19rem,1fr)); gap:.6rem; }
.proofcard { background:#fff; border:1px solid var(--line-soft); border-radius:.6rem; padding:.3rem .75rem .55rem; }
.proofcard summary { display:flex; gap:.5rem; align-items:center; cursor:pointer; padding:.35rem 0;
  list-style:none; }
.proofcard p { font-size:.84rem; color:var(--ink2); margin:.3rem 0 .5rem; }
.proofmat { font-size:.7rem; color:var(--ink2); }
.proofstate { margin-left:auto; font-size:.68rem; font-weight:800; letter-spacing:.06em; }
.proofstate.pass { color:var(--lime); } .proofstate.fail { color:var(--red); }
.prooffields { display:grid; grid-template-columns:1fr 1fr; gap:.45rem; }
.prooffields label { display:flex; flex-direction:column; font-size:.7rem; font-weight:700;
  color:var(--ink2); gap:.15rem; }
.prooffields input, .prooffields select, .prooffields textarea { font:inherit; font-size:.85rem;
  padding:.3rem .4rem; border:1px solid var(--line); border-radius:.35rem; background:var(--paper); }
.prooffields label:nth-child(3) { grid-column:1 / -1; }
.stepgrid { display:grid; grid-template-columns:repeat(auto-fill,minmax(12rem,1fr)); gap:.5rem; }
.stepcard { display:flex; gap:.6rem; align-items:center; background:#fff; text-decoration:none;
  color:var(--ink); border:1px solid var(--line-soft); border-radius:.6rem; padding:.6rem .7rem; }
.stepcard .stepdone { margin-left:auto; color:var(--line); font-style:normal; font-weight:800; }
.stepcard.done .stepdone { color:var(--lime); }
.stepnum { flex:none; width:2rem; height:2rem; background:var(--teal); color:#FFF9EE; font-weight:800;
  display:flex; align-items:center; justify-content:center; border-radius:.4rem; }
.stepview .stephead { display:flex; gap:.7rem; align-items:center; margin:.4rem 0; }
.stepview h1 { margin:0; font-size:clamp(1.3rem,4vw,1.9rem); }
.stepcount { margin-left:auto; font-size:.72rem; font-weight:800; letter-spacing:.1em;
  color:var(--ink2); white-space:nowrap; }
.stepdots { display:flex; gap:.22rem; margin:.2rem 0 .8rem; }
.stepdots i { flex:1; height:.35rem; border-radius:.2rem; background:var(--line-soft); max-width:1.6rem; }
.stepdots i.on { background:var(--teal); }
.stepdots i.now { background:var(--lime); }
.stepbanner { background:var(--red); color:#fff; font-weight:700; font-size:.85rem;
  border-radius:.5rem; padding:.5rem .8rem; margin:.6rem 0; }
.gather { display:flex; gap:.45rem; overflow-x:auto; background:var(--cream); border:1px solid var(--line-soft);
  border-radius:.6rem; padding:.55rem; margin-bottom:.8rem; }
.gathercell { flex:none; width:6.4rem; background:#fff; border:1px solid var(--line-soft);
  border-radius:.5rem; padding:.35rem; text-align:center; font-size:.7rem; cursor:pointer; position:relative; }
.gathercell input { position:absolute; top:.3rem; left:.3rem; accent-color:var(--lime); }
.gathercell b { display:block; }
.gathercell.done { outline:2px solid var(--lime); }
.stepmedia { display:flex; gap:.8rem; flex-wrap:wrap; align-items:flex-start; }
.imgwrap { position:relative; flex:2 1 24rem; border-radius:.6rem; overflow:hidden;
  border:1px solid var(--line-soft); background:#fff; }
.imgwrap > img { width:100%; }
.step-annotations { position:absolute; inset:0; width:100%; height:100%; pointer-events:none; }
/* Breathe the whole overlay layer: opacity on the <svg> element composites on
   its own layer, unlike per-line dash animation, which stalled page paint. */
@media (prefers-reduced-motion: no-preference) {
  .step-annotations { will-change:opacity; animation:arrowpulse 1.8s ease-in-out infinite; }
  @keyframes arrowpulse { 0%, 100% { opacity:1; } 50% { opacity:.5; } }
}
.frontchip { position:absolute; left:.6rem; bottom:.6rem; background:#22231F; color:#FFF9EE;
  font-size:.7rem; font-weight:800; letter-spacing:.08em; border-radius:999px; padding:.25em .7em; }
.axisbadge { position:absolute; right:.6rem; bottom:.6rem; background:#FFF9EEE6; border:1px solid var(--line);
  border-radius:999px; padding:.2em .6em; font-size:.66rem; font-weight:800; letter-spacing:.06em;
  display:flex; gap:.3em; align-items:center; }
.axisbadge i { font-style:normal; color:var(--ink2); }
.panels { flex:1 1 14rem; display:flex; flex-direction:column; gap:.6rem; min-width:14rem; }
.panel { background:#fff; border:1px solid var(--line-soft); border-radius:.6rem; overflow:hidden; }
.panel figcaption { font-size:.72rem; font-weight:700; color:var(--ink2); padding:.35rem .55rem; }
.panel.vector svg { width:100%; height:auto; }
.moves { margin:1rem 0 0 1.2rem; max-width:62ch; }
.moves li { margin-bottom:.5rem; }
.checkbar { display:flex; gap:.6rem; align-items:center; background:#CDE29B; border-radius:.6rem;
  padding:.6rem .8rem; margin:1rem 0; cursor:pointer; font-size:.9rem; }
.checkbar input { width:1.2rem; height:1.2rem; accent-color:var(--teal-dk); }
.checkbar b { color:var(--teal-dk); letter-spacing:.06em; }
.stepnav { display:flex; justify-content:space-between; gap:.6rem; margin:1.2rem 0; }
.navbtn { text-decoration:none; font-weight:800; font-size:.9rem; color:var(--teal-dk);
  border:1.5px solid var(--teal-dk); border-radius:999px; padding:.5rem 1rem; }
.navbtn.primary { background:var(--teal-dk); color:#FFF9EE; }
.rules { display:flex; flex-direction:column; gap:.4rem; margin-bottom:1rem; }
.rulecard { background:#fff; border:1px solid var(--line-soft); border-left:4px solid var(--red);
  border-radius:.5rem; padding:.5rem .8rem; font-size:.9rem; }
.tablewrap { overflow-x:auto; background:#fff; border:1px solid var(--line-soft); border-radius:.6rem; }
table { border-collapse:collapse; width:100%; font-size:.85rem; }
th { text-align:left; font-size:.68rem; letter-spacing:.12em; text-transform:uppercase;
  color:var(--gold); padding:.55rem .7rem .35rem; border-bottom:2px solid var(--line-soft); }
td { padding:.45rem .7rem; border-bottom:1px solid var(--line-soft); vertical-align:top; }
tbody tr:last-child td { border-bottom:none; }
.playcard { background:#fff; border:1px solid var(--line-soft); border-radius:.7rem;
  padding:.9rem 1rem; margin:.8rem 0; max-width:46rem; }
.playcard h2 { margin-top:0; }
.playcard pre { position:relative; background:#22231F; color:#E7DFCC; border-radius:.5rem;
  padding:.7rem .9rem; overflow-x:auto; margin:.5rem 0; }
.playcard pre .mini { position:absolute; top:.45rem; right:.45rem; }
.dashping { color:var(--lime); font-weight:700; }
footer { text-align:center; font-size:.75rem; color:var(--ink2); padding:2rem 1rem; }
@media (max-width: 640px) {
  .prooffields { grid-template-columns:1fr; }
  .stepnav .navbtn { flex:1; text-align:center; }
}
"""

JS = r"""
(function () {
  "use strict";
  var KEY = "rover-bean-build-v1";
  var state;
  try { state = JSON.parse(localStorage.getItem(KEY) || "{}"); } catch (e) { state = {}; }
  state.checks = state.checks || {};   // "<group>:<key>" -> true
  state.prices = state.prices || {};   // idx -> number
  state.proofs = state.proofs || {};   // proof key -> {field: value}
  function save() { try { localStorage.setItem(KEY, JSON.stringify(state)); } catch (e) {} }

  // ---- checklists -------------------------------------------------------
  var checkables = document.querySelectorAll("[data-check]");
  checkables.forEach(function (row) {
    var box = row.querySelector("input[type=checkbox]");
    if (!box) return;
    var id = row.getAttribute("data-check") + ":" + row.getAttribute("data-key");
    if (state.checks[id]) { box.checked = true; row.classList.add("done"); }
    box.addEventListener("change", function () {
      if (box.checked) state.checks[id] = true; else delete state.checks[id];
      row.classList.toggle("done", box.checked);
      save(); refresh();
    });
  });

  // ---- prices ------------------------------------------------------------
  var priceInputs = document.querySelectorAll("[data-price]");
  priceInputs.forEach(function (inp) {
    var k = inp.getAttribute("data-price");
    if (state.prices[k]) inp.value = state.prices[k];
    inp.addEventListener("input", function () {
      var v = parseFloat(inp.value);
      if (isFinite(v) && v > 0) state.prices[k] = v; else delete state.prices[k];
      save(); refresh();
    });
    inp.addEventListener("click", function (e) { e.preventDefault(); });
  });

  // ---- proof forms --------------------------------------------------------
  document.querySelectorAll("[data-proof]").forEach(function (card) {
    var key = card.getAttribute("data-proof");
    var rec = state.proofs[key] || {};
    card.querySelectorAll("[data-field]").forEach(function (f) {
      var name = f.getAttribute("data-field");
      if (rec[name] !== undefined) f.value = rec[name];
      f.addEventListener("input", function () {
        rec = state.proofs[key] = state.proofs[key] || {};
        if (f.value === "") delete rec[name]; else rec[name] = f.value;
        save(); refresh();
      });
    });
  });

  // ---- progress ------------------------------------------------------------
  function count(prefix) {
    var n = 0;
    Object.keys(state.checks).forEach(function (k) { if (k.indexOf(prefix) === 0) n++; });
    return n;
  }
  function refresh() {
    // shop total
    var total = 0;
    Object.keys(state.prices).forEach(function (k) { total += state.prices[k]; });
    var tEl = document.querySelector("[data-shop-total]");
    if (tEl) tEl.textContent = "$" + total.toFixed(2);
    var cEl = document.querySelector("[data-shop-count]");
    if (cEl) {
      var bought = count("shop:elec");
      cEl.textContent = bought ? bought + " electronics rows checked in" : "";
    }
    // proof states
    document.querySelectorAll("[data-proof]").forEach(function (card) {
      var rec = state.proofs[card.getAttribute("data-proof")] || {};
      var el = card.querySelector("[data-proof-state]");
      el.textContent = rec.pass_fail ? rec.pass_fail.toUpperCase() : "OPEN";
      el.className = "proofstate " + (rec.pass_fail || "");
    });
    // step cards + dots
    document.querySelectorAll("[data-step-card]").forEach(function (card) {
      card.classList.toggle("done", !!state.checks["steps:" + card.getAttribute("data-step-card")]);
    });
    // chapter + overall progress
    var totals = {
      shop: [document.querySelectorAll('[data-check="shop"] input').length, count("shop:")],
      print: [document.querySelectorAll('[data-check="plates"] input, [data-check="pieces"] input').length,
              count("plates:") + count("pieces:")],
      build: [STEP_TOTAL, count("steps:")],
      wire: [0, 0], play: [0, 0]
    };
    Object.keys(totals).forEach(function (ch) {
      var el = document.querySelector('[data-chapter-progress="' + ch + '"]');
      if (!el) return;
      var t = totals[ch];
      el.textContent = t[0] ? t[1] + " / " + t[0] + " done" : "";
    });
    var done = totals.shop[1] + totals.print[1] + totals.build[1];
    var all = totals.shop[0] + totals.print[0] + totals.build[0];
    var pct = all ? Math.round(100 * done / all) : 0;
    var ring = document.querySelector("[data-progress-ring]");
    if (ring) ring.style.strokeDashoffset = (119.4 * (1 - pct / 100)).toFixed(1);
    var pEl = document.querySelector("[data-progress-pct]");
    if (pEl) pEl.textContent = pct + "%";
    var sEl = document.querySelector("[data-progress-summary]");
    if (sEl) sEl.textContent = pct === 0 ? "Nothing checked yet — start in Shop."
      : pct < 100 ? done + " of " + all + " checks done. Keep going."
      : "Every tracked check is done. Admire, measure, keep the battery out.";
    var bar = document.querySelector(".topbar .bar i");
    if (bar) bar.style.width = pct + "%";
  }

  // ---- build log export / import -------------------------------------------
  var exp = document.querySelector("[data-export-log]");
  if (exp) exp.addEventListener("click", function () {
    var blob = new Blob([JSON.stringify({
      format: "rover-bean-build-log-v1", saved: new Date().toISOString(),
      release: RELEASE_ID, state: state
    }, null, 2)], { type: "application/json" });
    var a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "rover-bean-build-log.json";
    a.click(); URL.revokeObjectURL(a.href);
  });
  var imp = document.querySelector("[data-import-log]");
  if (imp) imp.addEventListener("change", function () {
    var file = imp.files && imp.files[0];
    if (!file) return;
    file.text().then(function (text) {
      var data = JSON.parse(text);
      if (!data || data.format !== "rover-bean-build-log-v1") throw new Error("wrong file");
      state = data.state || {};
      state.checks = state.checks || {}; state.prices = state.prices || {}; state.proofs = state.proofs || {};
      save(); location.reload();
    }).catch(function () { alert("That file isn't a Rover Bean build log."); });
  });

  // ---- router ----------------------------------------------------------------
  var views = ["home", "shop", "print", "build", "wire", "play"];
  function route() {
    var hash = location.hash.replace(/^#/, "") || "home";
    var parts = hash.split("/");
    var view = views.indexOf(parts[0]) >= 0 ? parts[0] : "home";
    views.forEach(function (v) {
      var el = document.getElementById("view-" + v);
      if (el) el.style.display = v === view ? "" : "none";
    });
    document.querySelectorAll(".topbar nav a").forEach(function (a) {
      a.classList.toggle("active", a.getAttribute("href") === "#" + view);
    });
    var idx = document.getElementById("build-index");
    var stepNo = view === "build" ? parseInt(parts[1] || "0", 10) : 0;
    if (idx) idx.style.display = view === "build" && !stepNo ? "" : "none";
    for (var i = 1; i <= STEP_TOTAL; i++) {
      var sv = document.getElementById("step-" + i);
      if (sv) sv.hidden = !(view === "build" && stepNo === i);
    }
    if (stepNo) {
      state.lastStep = stepNo; save();
      var art = document.getElementById("step-" + stepNo);
      if (art) art.querySelectorAll(".stepdots i").forEach(function (dot, k) {
        dot.className = (k + 1) < stepNo ? "on" : (k + 1) === stepNo ? "now" : "";
      });
    }
    window.scrollTo(0, 0);
    refresh();
  }
  window.addEventListener("hashchange", route);

  // keyboard + swipe between steps
  function stepDelta(d) {
    var m = location.hash.match(/^#build\/(\d+)$/);
    if (!m) return;
    var n = parseInt(m[1], 10) + d;
    if (n >= 1 && n <= STEP_TOTAL) location.hash = "#build/" + n;
    else if (n === 0) location.hash = "#build";
  }
  window.addEventListener("keydown", function (e) {
    if (e.target.matches("input, textarea, select")) return;
    if (e.key === "ArrowRight") stepDelta(1);
    if (e.key === "ArrowLeft") stepDelta(-1);
  });
  var touchX = null;
  window.addEventListener("touchstart", function (e) { touchX = e.touches[0].clientX; }, { passive: true });
  window.addEventListener("touchend", function (e) {
    if (touchX === null) return;
    var dx = e.changedTouches[0].clientX - touchX;
    if (Math.abs(dx) > 70) stepDelta(dx < 0 ? 1 : -1);
    touchX = null;
  }, { passive: true });

  // ---- wake lock ---------------------------------------------------------------
  var wakeBtn = document.querySelector("[data-wake]");
  var lock = null;
  if (wakeBtn && "wakeLock" in navigator) {
    wakeBtn.addEventListener("click", function () {
      if (lock) { lock.release(); lock = null; wakeBtn.classList.remove("on");
        wakeBtn.textContent = "KEEP SCREEN ON"; return; }
      navigator.wakeLock.request("screen").then(function (l) {
        lock = l; wakeBtn.classList.add("on"); wakeBtn.textContent = "SCREEN STAYS ON";
        l.addEventListener("release", function () { lock = null;
          wakeBtn.classList.remove("on"); wakeBtn.textContent = "KEEP SCREEN ON"; });
      }).catch(function () {});
    });
  } else if (wakeBtn) { wakeBtn.hidden = true; }

  // ---- copy buttons ---------------------------------------------------------------
  document.querySelectorAll("[data-copy]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var code = btn.parentElement.querySelector("code");
      navigator.clipboard && navigator.clipboard.writeText(code.textContent).then(function () {
        btn.textContent = "Copied"; setTimeout(function () { btn.textContent = "Copy"; }, 1200);
      });
    });
  });

  // ---- robotd dashboard ping (reachability only; opaque no-cors probe) ------------
  var ping = document.querySelector("[data-dashping]");
  if (ping && location.protocol.indexOf("http") === 0) {
    fetch("http://127.0.0.1:8072/", { mode: "no-cors" }).then(function () {
      ping.hidden = false;
    }).catch(function () {});
  }

  route();
})();
"""


# ---------------------------------------------------------------------------
# Assembly
# ---------------------------------------------------------------------------
def build_site() -> Path:
    copy_assets()
    estimates = plate_estimates(book.PLATES)
    nav = "".join(
        f'<a href="#{r}">{label}</a>'
        for r, label in [("home", "HOME"), ("shop", "SHOP"), ("print", "PRINT"),
                         ("build", "BUILD"), ("wire", "WIRE"), ("play", "PLAY")])
    body = (home_view() + shop_view() + print_view(estimates) + build_view()
            + wire_view() + play_view())
    js = (JS.replace("STEP_TOTAL", str(len(book.STEPS)))
            .replace("RELEASE_ID", json.dumps(book.RELEASE_ID)))
    html_text = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light">
<title>Codex Rover Bean &mdash; The Builder&rsquo;s Site ({esc(book.RELEASE_ID)})</title>
<style>{CSS}</style>
</head>
<body>
<header class="topbar">
  <a class="wordmark" href="#home">ROVER BEAN</a>
  <nav>{nav}</nav>
  <div class="bar"><i></i></div>
  <button class="wakebtn" data-wake>KEEP SCREEN ON</button>
</header>
<main>
{body}
</main>
<footer>Codex Rover Bean &middot; Builder&rsquo;s Site &middot; {esc(book.RELEASE_ID)} &middot;
prototype preview — no powered motion &middot; progress lives only in this browser
(save a build log from the home page).</footer>
<script>{js}</script>
</body>
</html>"""
    SITE_OUT.mkdir(parents=True, exist_ok=True)
    out = SITE_OUT / "index.html"
    out.write_text(html_text)
    check_site_images(html_text)
    return out


def main() -> None:
    book.ensure_release_qr()
    out = build_site()
    n_img = len(list(SITE_IMG.glob("*")))
    size_mb = sum(f.stat().st_size for f in SITE_OUT.rglob("*") if f.is_file()) / 1e6
    print(f"GUIDE_SITE_VALID steps={len(book.STEPS)} plates={book.N_PLATES} "
          f"images={n_img} size_mb={size_mb:.1f} output={out}")


if __name__ == "__main__":
    main()
