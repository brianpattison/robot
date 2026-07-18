# Agentic Control Plan: The Agent Owns The Computer, Firmware Owns Physics

Status: accepted 2026-07-17 (Brian's direction; decisions D030-D032).

This plan replaces the fixed high-level intent vocabulary as the robot's
control surface. The resident agent — Claude or Codex — becomes the robot's
operator and developer, with full authority over the Raspberry Pi: live SSH,
code and scripts written on the fly, package and service installs, direct
motion setpoints, and management of its own behaviors, schedules, and memory.

The deterministic safety layer does not get weaker; it gets more honest. Every
guarantee we actually rely on moves into hardware and firmware that the Pi
cannot alter, and everything else is openly the agent's to run. Root on the Pi
is not root on physics.

## Why Change The Old Boundary

The previous plan allowed the LLM nine canned intents (`come_here`,
`follow_user`, `go_home`, ...) and nothing else. That boundary had two
problems:

1. It capped the robot at its author's imagination. An agentic model's whole
   value is writing code against reality — new behaviors, new perception
   glue, new fixes — and a fixed vocabulary throws that away.
2. It implied software enforcement that could not survive contact with a
   capable agent anyway. Any gate that lives as editable code on the Pi is a
   convention, not a guarantee. Pretending otherwise is worse than saying so.

So the new boundary is drawn where it can actually hold: the safety MCU
firmware and the physical controls. Above that line, the agent is trusted,
supervised, and fully in charge. Below it, nothing negotiates.

## What Changes, What Does Not

| Area | Before | Now |
| --- | --- | --- |
| Agent authority on the Pi | Conversation plus nine intents | Full: shell, sudo, installs, services, cron, self-modification |
| Motion commands | Canned intents only | Direct velocity/head setpoints via `robotd`, clamped in firmware |
| Behaviors | Fixed vocabulary in the runtime | Code the agent writes, tests, and hot-swaps (`~/agent/behaviors/`) |
| Remote access | Dashboard only | Live SSH for the agent through an outbound-only Cloudflare Tunnel, plus the dashboard |
| E-stop, bumpers, watchdog, speed caps | Deterministic, non-LLM | Unchanged — and explicitly unreachable from the Pi |
| No-go zones, quiet hours, supervision | Described as hard limits | Reclassified honestly as policy the agent is instructed to honor |
| Identity | Codex only (old D005) | Pluggable seat: Claude or Codex, one narrator at a time (D031) |
| Audit | Logs | Command blackbox plus recorded agent sessions, streamed to an off-host mirror |

## The Hard Floor

These invariants are enforced below the Pi and survive anything the agent
does in software, including `rm -rf /`:

| Invariant | Enforced by | Agent-changeable? |
| --- | --- | --- |
| E-stop cuts motor power | IDEC XW1E direct-opening NC contacts in the Panasonic CB1A-R-M-12V relay coil path, hardware reset latch | No — physical |
| Bumper hit stops motion | Safety MCU firmware; six normally-closed Omron D2HW loops; any open loop is a latched stop | Clears freely once the loop reads released; capped-speed escape from a pressed zone |
| Watchdog timeout stops motion | Safety MCU firmware; stale heartbeat de-energizes motor enable | No |
| Motion setpoints expire | Safety MCU firmware; every nonzero setpoint carries a short lease and zeros unless refreshed — a heartbeat alone never sustains motion | No |
| Velocity and acceleration caps (0.35 m/s MVP) | Safety MCU firmware clamps every setpoint before the MDDS10 | No — new values require reflashing with physical access |
| Charger inserted inhibits motion | `CHARGER_PRESENT` into the deterministic enable path; removal never auto-restarts | No |
| Low-battery motor cutoff | Safety MCU firmware | No |
| Microphone hard mute | E-Switch PVB3F230SS311 physically removes mic VBUS; red ring is hardware | No |

The floor stays unreachable because of how the safety MCU (Raspberry Pi
Pico 2) is wired, not because of software courtesy:

- The Pi-to-Pico link is a framed UART protocol whose command set contains
  motion setpoints, latch-clear requests, heartbeat, and status queries —
  and no flash, bootloader, or config-write commands at all.
- Nonzero motion setpoints expire in firmware (fixed 250 ms bench baseline)
  unless refreshed. The heartbeat proves the host is alive; only a fresh
  setpoint stream keeps wheels turning. A behavior that crashes mid-drive
  coasts to a leased stop even while the rest of the Pi stays healthy.
- The firmware cannot tell who is talking. Any process that holds the
  serial port and speaks the contract is "the Pi" to the MCU — the floor
  binds all clients equally and vouches for none of them.
- The Pico's USB and SWD interfaces are service corridors only. They are
  never cabled to the Pi in normal operation, so the Pi cannot reboot the
  Pico into its bootloader. Reflashing the firmware means opening the robot
  and physically connecting to the service corridor (BOOTSEL in hand).
- Bumper and E-stop stops are latched. The agent may clear a bumper latch
  as soon as the loop reads released again — no budget, no human in the
  loop — and firmware permits capped-speed escape motion away from a
  pressed zone so the robot can free itself. Bump, back off, clear,
  continue is normal exploration, not a fault. A loop that cannot read
  released (broken wire, unplugged connector) holds a fault until
  repaired: that is wiring protection, not agent restriction. The E-stop
  latch always requires physical reset — it is the humans' button, and it
  does not care who is holding the shell.

What the floor is for — and not for: it catches malfunctions (code that
died mid-drive), protects hardware (stalled motors, deep-discharged packs,
shorted branches), and preserves the humans' two physical controls (E-stop
and mute). It places no gate between what the agent decides and what it
may attempt. The agent can drive anywhere in the house, at any hour, for
any reason it finds sufficient; the floor only shapes how gently that
meets walls and furniture. The hardware "can't do anything actually
unsafe" precisely because these caps and cutoffs are part of the hardware
— they are what make unbounded software freedom a low-stakes grant.

## Topology

```text
Claude / Codex
  resident session on the Pi (robot-agent-host.service)
  or remote session over SSH through the Cloudflare Tunnel
    |-- shell: code, installs, services, cron, self-modification
    |-- robotd API: drive, head, speak, listen, LEDs, senses, events
          |
          v
robotd (body daemon)
  telemetry, event stream, command blackbox, heartbeat-on-health
          |
          v  UART serial contract (no flash path)
Safety MCU firmware (Pico 2)
  velocity/accel clamps, watchdog, latched bumper/E-stop/charger stops
          |
          v
Cytron MDDS10 -> motors
          ^
Physical E-stop relay path — above everything, independent of the Pi
```

## Executable Bench Baseline

The control boundary now has runnable artifacts rather than prose alone:

- [`body-protocol-v1.md`](body-protocol-v1.md) fixes the 115200-baud framed
  UART vocabulary, CRC, 20 Hz heartbeat, 250 ms watchdog, 250 ms independent
  motion lease, clamps, and status payload. It has no flash/config-write path.
- [`../software/robotd/`](../software/robotd/) implements the local Unix-socket
  API, exclusive UART ownership, one-shot setpoints, 20 Hz heartbeat, firmware
  status readback, and Pi-local plus optional off-host JSONL blackbox.
- [`../firmware/pico2-safety/`](../firmware/pico2-safety/) implements and tests
  the portable safety state machine. Its Pico target is deliberately
  fail-stopped: it can exercise UART/status on the bench but contains no
  production motor-output driver and can never enable the relay.
- [`../harness/`](../harness/) and [`../commissioning/`](../commissioning/)
  make the remaining electrical and physical evidence machine-checkable.

`python3 commissioning/run_host_tests.py` exercises the daemon socket,
protocol framing/resynchronization, motion expiry, harness engineering gate,
and portable C safety core. Passing it is necessary and hardware-free; it is
not a substitute for the fixture and first-article results.

## The Agent Seat

- The seat is pluggable (D031): Claude occupies it through Claude Code or
  the Claude Agent SDK running headless on the Pi; Codex occupies it through
  the Codex CLI. One resident narrator at a time — wake word, STT, TTS, and
  perception remain tools, not personalities.
- The agent runs as the `agent` user with sudo. Its workspace is
  `/home/agent/` with `behaviors/` (motion and interaction code it authors),
  `journal/` (its own memory and notes), and `tools/` (scripts it builds for
  itself).
- `robot-agent-host.service` keeps a resident headless session alive and
  feeds it conversation turns from the voice service, robot state from
  `robotd`, and its own journal. Between conversations the agent may run
  background turns on its own schedule (cron it manages itself).
- Remote access is live SSH through a Cloudflare Tunnel (D033):
  `cloudflared` on the Pi dials out over HTTPS, so nothing listens on the
  WAN, and clients connect with `cloudflared access ssh` gated by
  Cloudflare Access service tokens. Any cloud session (claude.ai or Codex
  cloud) that can run the small `cloudflared` binary with outbound 443 —
  which is all of them — can drive the same machine the resident seat
  uses.

## robotd: The Body Daemon

A small always-on Python daemon, localhost-only, that makes the body
pleasant to use and everything observable. It is a convenience and telemetry
chokepoint, not a permission system — the firmware does not care who talks
to it.

- **Motion:** `drive(v, w)` velocity setpoints, `stop()`, head pan/tilt.
- **Voice:** `speak(text)` with barge-in, listening state, wake events.
- **Senses:** camera frames, ToF distances, bumper/E-stop/charger state,
  odometry, battery, temperatures.
- **Lights:** LED expressions, subject to the hardware mute ring's priority.
- **Policy:** read endpoint for the current policy file (no-go zones, quiet
  hours, roaming rules) so behaviors can honor it.
- **Events:** WebSocket stream of everything above, shared by the dashboard
  and the agent.

`robotd` holds the serial port exclusively and emits the firmware heartbeat
only while its own health checks pass. It relays motion setpoints without
refreshing them on behalf of a silent client, so a crashed behavior stops
at the firmware lease even while the daemon stays healthy, and stopping
`robotd` stops the robot in the ordinary case.

That is a property of the default stack, not a guarantee against the agent
itself: the firmware cannot distinguish `robotd`'s heartbeat from anyone
else's, so an agent that takes the serial port and speaks the contract
directly (full control means full control) can sustain motion on its own.
Doing so is allowed, ends the dashboard's visibility, makes the agent the
safety client of record, and is exactly the kind of move the off-host
audit mirror exists to make visible. Anything `robotd` cannot vouch for,
the firmware envelope still clamps.

Every command through `robotd` lands in the blackbox log with timestamps
and source, streamed live off-host as described under Observability. A
Pi-local file alone is not the audit trail — the mirror is.

## Conversation Loop

1. Wake word runs locally and lights the listening state.
2. Speech goes to STT.
3. The local urgent-phrase recognizer still catches `stop`, `wait`, `mute`,
   and `status` first and acts through `robotd` directly — under two
   seconds, no agent in the loop, works with the network down.
4. Everything else becomes a turn in the resident agent session, with
   current robot state attached.
5. The agent answers however it sees fit: speak, drive, look something up,
   write a script, install a package, or all five.
6. TTS speaks; barge-in interrupts for `stop`, `wait`, or the wake word.

If the network is down, the agent seat is down (both Claude and Codex are
cloud models for now), but the robot degrades exactly as before: urgent
local commands, scripted replies, manual dashboard drive — plus any
behaviors the agent already wrote, because those are local code and keep
running without it. The AI HAT+ 2 remains the future path to a local seat.

## Behaviors As Code, Not Vocabulary

The old intent list survives as the starter library the agent inherits,
implemented as ordinary programs against `robotd`: `stop`,
`look_at_speaker`, `come_here`, `follow_user`, `wait`, `go_home`,
`explore_nearby`, `say`, `set_led_state`.

From there the agent iterates: tighten `follow_user`'s distance control,
write `patrol_to_the_kitchen_and_report`, add a perception model it
installed that afternoon. Fast control loops run as normal processes the
agent deploys and hot-swaps; the agent does not need to be in the loop at
20 Hz, it needs to write the loop. Norm: new motion behaviors get a bench
or blocked-wheels dry run before they drive the floor, and the firmware
envelope makes the worst honest mistake a capped-speed bump.

## Policy, Not Physics

No-go zones, quiet hours, camera-upload rules, and supervision expectations
are policy: a config file Brian edits in the dashboard, served read-only
through `robotd`, and injected into the agent's system prompt. The agent is
instructed to honor policy and the blackbox shows whether it did.

This is a reclassification, not a new hole. The firmware cannot know where
the bathroom is; any zone enforcement necessarily lived on the Pi, and
anything on the Pi is now the agent's. The honest guarantee is: policy
violations are visible in the blackbox, and physics violations are
impossible from software. A robot that wanders somewhere it shouldn't does
so at a capped walking pace, bumps, stops, and gets audited.

## Observability

- **Blackbox:** a log of every `robotd` command, latch event, policy read,
  and firmware status change — streamed live to the dashboard client and
  to an off-robot subscriber (a laptop, a NAS, anything not the Pi). The
  Pi-local copy is convenience only: a sudo-capable agent can edit
  anything stored on the Pi, so the trustworthy record is the off-host
  mirror, and a gap or silence in that stream is itself a red flag.
- **Session recording:** agent shell sessions recorded (auditd + tlog or
  equivalent) and browsable from the dashboard, shipped to the same
  off-host mirror under the same rule.
- **Dashboard agent panel:** live view of the resident session, recent
  actions, current behaviors, and a software stop button — supervision
  conveniences. The physical E-stop remains the only stop that is not a
  courtesy.

## Failure And Recovery

- Agent wedges Linux or fills the disk: heartbeat stops, robot stops. Pull
  the microSD, reflash the golden image, and the safety MCU never noticed.
  Keep a tested golden image from M0 onward.
- Runaway behavior loop: firmware clamps speed, bumpers latch on contact,
  the latch-clear budget runs out, robot stays stopped.
- Agent kills `robotd` deliberately: no heartbeat, no motion — unless the
  agent takes over the serial contract itself, which is allowed, visible
  in the off-host mirror as a `robotd` outage, and makes the agent the
  safety client of record. The firmware envelope binds it all the same.
- Compromised or misbehaving seat: revoke its Cloudflare Access service
  token at the edge, its SSH key, and the seat's API credentials, then
  reflash the Pi. The blast radius of the agent account is the Pi, by
  design.

## Security Posture

- Remote ingress is a Cloudflare Tunnel (`cloudflared` as a systemd
  service, D033): the Pi dials out over HTTPS and exposes no inbound port
  anywhere — the home firewall stays closed. SSH rides the tunnel
  end-to-end via `ProxyCommand cloudflared access ssh`, never the
  browser-rendered terminal, so Cloudflare transports the stream but
  cannot read it. Cloudflare Access gates the hostname: service tokens
  for agent clients, SSO for humans, both revocable per-client at the
  edge without touching the Pi, and every connection logged there — a
  second audit trail that conveniently lives off-host.
- sshd stays key-only, no password auth, `agent` user, bound to
  loopback/LAN only. A WireGuard/Tailscale mesh remains a fine complement
  for Brian's own devices; the standard agent path is the tunnel.
- The dashboard and off-host mirror stay LAN-local by default; publishing
  either is allowed only behind the same Cloudflare Access gate.
- The agent's API credentials and any secrets it needs live in a store
  scoped to the `agent` user; the seat never needs Brian's accounts.
- Privacy floor stays physical: the mute switch removes mic VBUS in
  hardware and its red ring cannot be spoofed from software. For this to
  be true with a USB mic array, the switch must be interposed in the USB
  VBUS conductor between the Pi's port and the mic — an opened conductor
  cannot be re-powered from software — and the existing backfeed release
  gate applies in full: prove no data-line backfeed or residual capture
  with VBUS removed before trusting the mute (mandatory at M0, per the
  PRD and D019). Software recording indicators are best-effort under full
  control; treat the hardware ring as the trustworthy one, and consider
  hardwiring a camera-power light as future hardening.

## Milestone Deltas

- **M0 Bench Brain:** additionally install the agent seat. Exit demo: the
  agent, over live SSH and the resident session, installs a package, writes
  and runs a new script, speaks, listens, and journals — no motors exist
  yet.
- **M1 Rolling Chassis:** unchanged and still gates everything. The
  firmware envelope (clamps, watchdog kill test, all six NC bumper zones,
  latch clear and escape motion, setpoint-lease expiry, E-stop, charger
  inhibit) passes
  bench tests before the agent's first drive command. The agent is
  read-only telemetry until then, enforced physically during
  commissioning — motor branch isolated or wheels off the floor — not by
  trusting software to abstain.
- **M2 Senses And Speech:** the agent authors its first behaviors
  (`look_at_speaker`, `come_here`) in a prepared area, replacing "voice
  commands route to intents."
- **M3/M4:** unchanged in intent; behaviors are agent-authored code.

Additional acceptance checks: kill `robotd` under commanded motion and see
the robot stop within the watchdog window; kill a driving behavior while
`robotd` stays healthy and see motion stop at the setpoint lease; bump,
back away, clear, and continue with no human in the loop; confirm a
simulated broken bumper wire holds a fault no protocol command clears;
verify the off-host mirror captured an entire agent-driven session, blackbox and
shell recording both; prove no mic capture with the hardware mute engaged
and software running; press the E-stop while the agent is driving.

## Open Questions

- Exact harness shape per seat (Claude Code headless vs Agent SDK service;
  Codex CLI equivalents), session cadence, and token budget for background
  turns.
- Physical validation of the fixed 20 Hz / 250 ms / 250 ms heartbeat,
  watchdog, and motion-setpoint lease baseline under worst-case Pi load and
  real relay/motor timing.
- Journal/memory privacy scoping and what syncs off-robot, now that the
  agent manages its own memory.
- Whether the perception baseline (person tracking) ships preinstalled or
  is the agent's first install job.
- Whether the E-stop's latched reset input is the twist-release cycle
  plus a confirm, or a dedicated service button on the safety shelf.
