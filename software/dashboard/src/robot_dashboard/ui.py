"""Inline single-page dashboard UI. No network assets: it must render offline."""

DASHBOARD_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Rover Bean Dashboard</title>
<style>
:root {
  --bg: #101418; --panel: #1a2027; --edge: #2a323c; --text: #e8edf2;
  --dim: #93a1b0; --ok: #3ecf8e; --warn: #f5b83d; --bad: #f4643d;
  --accent: #4aa8ff; --stop: #d92b2b;
}
* { box-sizing: border-box; }
body {
  margin: 0; background: var(--bg); color: var(--text);
  font: 15px/1.45 -apple-system, "Segoe UI", system-ui, sans-serif;
}
header { padding: 14px 20px 6px; display: flex; align-items: baseline; gap: 14px; flex-wrap: wrap; }
header h1 { font-size: 20px; margin: 0; }
#display-state { font-weight: 600; }
.banner {
  margin: 0 20px 10px; padding: 8px 12px; border: 1px solid var(--edge);
  border-left: 4px solid var(--warn); border-radius: 6px; color: var(--dim); font-size: 13px;
}
main {
  display: grid; gap: 14px; padding: 0 20px 20px;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
}
section {
  background: var(--panel); border: 1px solid var(--edge); border-radius: 10px; padding: 14px 16px;
}
section h2 { margin: 0 0 10px; font-size: 13px; text-transform: uppercase; letter-spacing: .08em; color: var(--dim); }
dl.kv { display: grid; grid-template-columns: auto 1fr; gap: 3px 14px; margin: 0; }
dl.kv dt { color: var(--dim); }
dl.kv dd { margin: 0; font-variant-numeric: tabular-nums; }
.pills { display: flex; flex-wrap: wrap; gap: 6px; }
.pill {
  padding: 3px 10px; border-radius: 999px; border: 1px solid var(--edge);
  font-size: 13px; color: var(--dim); background: #151a20;
}
.pill.on-bad { background: #3a1712; border-color: var(--bad); color: #ffb3a1; }
.pill.on-warn { background: #38290e; border-color: var(--warn); color: #ffdf9e; }
.pill.on-ok { background: #10301f; border-color: var(--ok); color: #a5f0cd; }
.zones { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; }
.zone { border: 1px solid var(--edge); border-radius: 8px; padding: 8px; text-align: center; }
.zone .state { display: block; font-size: 12px; margin: 3px 0 6px; color: var(--dim); }
.zone.open { border-color: var(--bad); }
.zone.latched { border-color: var(--warn); }
.zone button { font-size: 12px; padding: 2px 8px; }
button {
  background: #232c36; color: var(--text); border: 1px solid var(--edge);
  border-radius: 8px; padding: 8px 12px; cursor: pointer; font: inherit;
}
button:hover { border-color: var(--accent); }
button:disabled { opacity: .45; cursor: default; }
#stop-btn {
  width: 100%; background: var(--stop); border-color: #ff6a5e; font-size: 19px;
  font-weight: 700; padding: 14px; letter-spacing: .05em;
}
.dpad { display: grid; grid-template-columns: repeat(3, 64px); gap: 6px; justify-content: center; margin: 10px 0; }
.dpad button { height: 52px; font-size: 20px; touch-action: none; user-select: none; -webkit-user-select: none; }
.dpad .blank { visibility: hidden; }
label.slider { display: block; margin: 8px 0 2px; color: var(--dim); font-size: 13px; }
input[type=range] { width: 100%; }
.placeholder {
  border: 1px dashed var(--edge); border-radius: 8px; padding: 18px; text-align: center; color: var(--dim);
}
#log {
  height: 260px; overflow-y: auto; background: #0c1014; border: 1px solid var(--edge);
  border-radius: 8px; padding: 8px 10px; font: 12px/1.5 ui-monospace, Menlo, monospace;
  white-space: pre-wrap; word-break: break-word;
}
#log .k { color: var(--accent); }
#link-state { font-size: 13px; color: var(--dim); }
#link-state.lost { color: var(--bad); }
footer { padding: 0 20px 18px; color: var(--dim); font-size: 12px; }
</style>
</head>
<body>
<header>
  <h1>Rover Bean</h1>
  <span id="display-state">connecting&hellip;</span>
  <span id="link-state">dashboard link: connecting</span>
</header>
<div class="banner">
  Supervision tool only. The Pico firmware and the physical E-stop own safety: this page cannot
  clear an E-stop latch, bypass the open-bumper zero-motion rule, or exceed the firmware velocity
  clamps. Drive setpoints expire in firmware 250&nbsp;ms after the last refresh.
</div>
<main>
  <section id="status-card">
    <h2>Status</h2>
    <dl class="kv">
      <dt>robotd</dt><dd id="s-robotd">&mdash;</dd>
      <dt>firmware link</dt><dd id="s-fw">&mdash;</dd>
      <dt>status age</dt><dd id="s-age">&mdash;</dd>
      <dt>firmware uptime</dt><dd id="s-uptime">&mdash;</dd>
      <dt>battery</dt><dd id="s-batt">&mdash;</dd>
      <dt>applied velocity</dt><dd id="s-vel">&mdash;</dd>
      <dt>head</dt><dd id="s-head">&mdash;</dd>
      <dt>motor enable</dt><dd id="s-motor">&mdash;</dd>
      <dt>last error</dt><dd id="s-err">&mdash;</dd>
    </dl>
  </section>

  <section>
    <h2>Safety Flags</h2>
    <div class="pills" id="flags"></div>
    <p style="color:var(--dim);font-size:12px;margin:10px 0 0">
      The bench-safe Pico target always reports motor enable off. An open loop and a pressed
      bumper are electrically identical (D036).
    </p>
  </section>

  <section>
    <h2>Bumper Loops</h2>
    <div class="zones" id="zones"></div>
    <div style="margin-top:10px"><button id="clear-latched">Clear released, latched zones</button></div>
  </section>

  <section>
    <h2>Drive</h2>
    <button id="stop-btn">STOP</button>
    <div class="dpad">
      <span class="blank"></span><button data-v="1,0">&#8593;</button><span class="blank"></span>
      <button data-v="0,1">&#10226;</button><button data-v="-1,0">&#8595;</button><button data-v="0,-1">&#10227;</button>
    </div>
    <label class="slider">linear speed <span id="lin-val"></span> mm/s (firmware cap 350)</label>
    <input type="range" id="lin" min="0" max="350" value="150">
    <label class="slider">angular speed <span id="ang-val"></span> mrad/s (firmware cap 1500)</label>
    <input type="range" id="ang" min="0" max="1500" value="600">
    <p style="color:var(--dim);font-size:12px">
      Hold a button (or WASD/arrow keys) to drive; release stops. The page refreshes the setpoint
      at 10&nbsp;Hz while held; if it stops refreshing, firmware zeroes motion on its own.
    </p>
  </section>

  <section>
    <h2>Head</h2>
    <label class="slider">pan <span id="pan-val"></span>&deg; (&plusmn;60)</label>
    <input type="range" id="pan" min="-60" max="60" value="0">
    <label class="slider">tilt <span id="tilt-val"></span>&deg; (&plusmn;20)</label>
    <input type="range" id="tilt" min="-20" max="20" value="0">
    <div style="margin-top:8px"><button id="head-center">Center head</button></div>
  </section>

  <section>
    <h2>Live View</h2>
    <div class="placeholder">
      No camera stream on the bench baseline.<br>
      The perception layer (camera capture, person tracking, proximity fusion) is not built yet.
    </div>
  </section>

  <section style="grid-column: 1 / -1">
    <h2>Blackbox Log</h2>
    <div id="log"></div>
  </section>

  <section>
    <h2>Settings</h2>
    <div class="placeholder">
      Named points, no-go zones, quiet hours, and debug capture are not implemented yet.
      When they land they are audited policy, not enforcement (see the agentic control plan).
    </div>
  </section>
</main>
<footer>
  robot-dashboard bench baseline &middot; localhost only by default &middot; every command is
  blackbox-logged with source <code>dashboard</code>
</footer>
<script>
"use strict";
const $ = (id) => document.getElementById(id);
const FLAG_LABELS = {
  estop_latched: ["E-stop latched", "bad"],
  charger_present: ["charger present", "warn"],
  low_battery: ["low battery", "warn"],
  heartbeat_stale: ["heartbeat stale", "warn"],
  motion_lease_stale: ["motion lease stale", "ok"],
  bumper_latched: ["bumper latched", "warn"],
  wiring_fault: ["bumper loop open", "bad"],
  motor_enable: ["motor enable ON", "warn"],
};

async function post(path, body) {
  try {
    const response = await fetch(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body || {}),
    });
    return await response.json();
  } catch (err) {
    return { ok: false, error: String(err) };
  }
}

let lastStatus = null;

function renderStatus(s) {
  lastStatus = s;
  $("display-state").textContent = s.display_state || "unknown";
  $("s-robotd").textContent = s.robotd_reachable ? "reachable" : (s.error || "unreachable");
  $("s-fw").textContent = s.robotd_reachable ? (s.connected ? "up" : "down") : "—";
  $("s-age").textContent = s.status_age_ms != null ? s.status_age_ms + " ms" : "—";
  $("s-err").textContent = s.last_error || "none";
  const fw = s.firmware || {};
  const haveFw = Object.keys(fw).length > 0;
  $("s-uptime").textContent = haveFw ? (fw.uptime_ms / 1000).toFixed(1) + " s" : "—";
  $("s-batt").textContent = haveFw ? (fw.battery_mv / 1000).toFixed(2) + " V" : "—";
  $("s-vel").textContent = haveFw
    ? fw.linear_mm_s + " mm/s, " + fw.angular_mrad_s + " mrad/s" : "—";
  $("s-head").textContent = haveFw
    ? "pan " + (fw.pan_cdeg / 100).toFixed(1) + "°, tilt " + (fw.tilt_cdeg / 100).toFixed(1) + "°"
    : "—";
  const flags = s.safety_flags || {};
  $("s-motor").textContent = haveFw ? (flags.motor_enable ? "ON" : "off (bench-safe)") : "—";
  const pills = Object.entries(FLAG_LABELS).map(([key, [label, severity]]) => {
    const active = !!flags[key];
    return '<span class="pill' + (active ? " on-" + severity : "") + '">' + label + "</span>";
  });
  $("flags").innerHTML = pills.join("");
  const zones = (s.bumpers || []).map((z) => {
    const cls = !z.loop_closed ? "open" : (z.latched ? "latched" : "");
    const state = !z.loop_closed ? "loop OPEN" : (z.latched ? "closed, latched" : "closed");
    const btn = z.latched && z.loop_closed
      ? '<button data-zone="' + z.zone + '">clear</button>' : "";
    return '<div class="zone ' + cls + '"><strong>zone ' + z.zone + "</strong>" +
      '<span class="state">' + state + "</span>" + btn + "</div>";
  });
  $("zones").innerHTML = zones.join("");
}

// ---- event stream ----
const log = $("log");
function appendLog(records) {
  const nearBottom = log.scrollHeight - log.scrollTop - log.clientHeight < 40;
  for (const r of records) {
    const line = document.createElement("div");
    const detail = Object.entries(r)
      .filter(([k]) => !["ts", "monotonic_ns", "kind"].includes(k))
      .map(([k, v]) => k + "=" + JSON.stringify(v)).join(" ");
    const kind = document.createElement("span");
    kind.className = "k";
    kind.textContent = r.kind || "?";
    line.append((r.ts || "") + " ", kind, " " + detail);
    log.append(line);
  }
  while (log.childElementCount > 400) log.firstElementChild.remove();
  if (nearBottom) log.scrollTop = log.scrollHeight;
}

function connectEvents() {
  const source = new EventSource("/api/events");
  source.addEventListener("status", (e) => renderStatus(JSON.parse(e.data)));
  source.addEventListener("blackbox", (e) => appendLog(JSON.parse(e.data)));
  source.onopen = () => {
    $("link-state").textContent = "dashboard link: live";
    $("link-state").classList.remove("lost");
  };
  source.onerror = () => {
    $("link-state").textContent = "dashboard link: lost, retrying";
    $("link-state").classList.add("lost");
    $("display-state").textContent = "dashboard link lost";
  };
}
connectEvents();

// ---- drive ----
const held = { lin: 0, ang: 0 };
let driveTimer = null;

function currentVector() {
  return {
    linear_mm_s: held.lin * Number($("lin").value),
    angular_mrad_s: held.ang * Number($("ang").value),
  };
}
function startDrive() {
  if (driveTimer) return;
  post("/api/drive", currentVector());
  driveTimer = setInterval(() => {
    if (!held.lin && !held.ang) return stopDrive();
    post("/api/drive", currentVector());
  }, 100);
}
function stopDrive() {
  if (driveTimer) { clearInterval(driveTimer); driveTimer = null; }
  held.lin = 0; held.ang = 0;
  post("/api/stop", {});
}
document.querySelectorAll(".dpad button").forEach((btn) => {
  const [lin, ang] = btn.dataset.v.split(",").map(Number);
  const press = (e) => { e.preventDefault(); held.lin = lin; held.ang = ang; startDrive(); };
  const release = () => { if (held.lin === lin && held.ang === ang) stopDrive(); };
  btn.addEventListener("pointerdown", press);
  btn.addEventListener("pointerup", release);
  btn.addEventListener("pointerleave", release);
  btn.addEventListener("pointercancel", release);
});
const KEYS = { w: [1, 0], ArrowUp: [1, 0], s: [-1, 0], ArrowDown: [-1, 0],
               a: [0, 1], ArrowLeft: [0, 1], d: [0, -1], ArrowRight: [0, -1] };
document.addEventListener("keydown", (e) => {
  if (e.target.tagName === "INPUT") return;
  if (e.key === " " || e.key === "Escape") { e.preventDefault(); stopDrive(); return; }
  const vec = KEYS[e.key];
  if (vec && !e.repeat) { held.lin = vec[0]; held.ang = vec[1]; startDrive(); }
});
document.addEventListener("keyup", (e) => {
  const vec = KEYS[e.key];
  if (vec && held.lin === vec[0] && held.ang === vec[1]) stopDrive();
});
document.addEventListener("visibilitychange", () => { if (document.hidden) stopDrive(); });
$("stop-btn").addEventListener("click", stopDrive);

// ---- head ----
let headTimer = null;
function sendHead() {
  if (headTimer) return;
  headTimer = setTimeout(() => {
    headTimer = null;
    post("/api/head", {
      pan_cdeg: Number($("pan").value) * 100,
      tilt_cdeg: Number($("tilt").value) * 100,
    });
  }, 150);
}
for (const id of ["pan", "tilt"]) $(id).addEventListener("input", () => { syncSliders(); sendHead(); });
$("head-center").addEventListener("click", () => {
  $("pan").value = 0; $("tilt").value = 0; syncSliders(); sendHead();
});

// ---- bumper clears ----
$("zones").addEventListener("click", (e) => {
  const zone = e.target.dataset && e.target.dataset.zone;
  if (zone != null && zone !== "") post("/api/clear_bumper", { zone_mask: 1 << Number(zone) });
});
$("clear-latched").addEventListener("click", () => {
  if (!lastStatus || !lastStatus.bumpers) return;
  let mask = 0;
  for (const z of lastStatus.bumpers) if (z.latched && z.loop_closed) mask |= 1 << z.zone;
  if (mask) post("/api/clear_bumper", { zone_mask: mask });
});

// ---- sliders ----
function syncSliders() {
  $("lin-val").textContent = $("lin").value;
  $("ang-val").textContent = $("ang").value;
  $("pan-val").textContent = $("pan").value;
  $("tilt-val").textContent = $("tilt").value;
}
for (const id of ["lin", "ang"]) $(id).addEventListener("input", syncSliders);
syncSliders();
</script>
</body>
</html>
"""
