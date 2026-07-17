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
| Remote access | Dashboard only | Live SSH for the agent over the tailnet, plus the dashboard |
| E-stop, bumpers, watchdog, speed caps | Deterministic, non-LLM | Unchanged — and explicitly unreachable from the Pi |
| No-go zones, quiet hours, supervision | Described as hard limits | Reclassified honestly as policy the agent is instructed to honor |
| Identity | Codex only (old D005) | Pluggable seat: Claude or Codex, one narrator at a time (D031) |
| Audit | Logs | Append-only command blackbox plus recorded agent shell sessions |

## The Hard Floor

These invariants are enforced below the Pi and survive anything the agent
does in software, including `rm -rf /`:

| Invariant | Enforced by | Agent-changeable? |
| --- | --- | --- |
| E-stop cuts motor power | IDEC XW1E direct-opening NC contacts in the Panasonic CB1A-R-M-12V relay coil path, hardware reset latch | No — physical |
| Bumper hit stops motion | Safety MCU firmware; six normally-closed Omron D2HW loops; any open loop is a latched stop | Latch clear only, rate-limited in firmware |
| Watchdog timeout stops motion | Safety MCU firmware; stale heartbeat de-energizes motor enable | No |
| Velocity and acceleration caps (0.35 m/s MVP) | Safety MCU firmware clamps every setpoint before the MDDS10 | No — new values require reflashing with physical access |
| Charger inserted inhibits motion | `CHARGER_PRESENT` into the deterministic enable path; removal never auto-restarts | No |
| Low-battery motor cutoff | Safety MCU firmware | No |
| Microphone hard mute | E-Switch PVB3F230SS311 physically removes mic VBUS; red ring is hardware | No |

The floor stays unreachable because of how the safety MCU (Raspberry Pi
Pico 2) is wired, not because of software courtesy:

- The Pi-to-Pico link is a framed UART protocol whose command set contains
  motion setpoints, latch-clear requests, heartbeat, and status queries —
  and no flash, bootloader, or config-write commands at all.
- The Pico's USB and SWD interfaces are service corridors only. They are
  never cabled to the Pi in normal operation, so the Pi cannot reboot the
  Pico into its bootloader. Reflashing the firmware means opening the robot
  and physically connecting to the service corridor (BOOTSEL in hand).
- Bumper and E-stop stops are latched. Firmware accepts a limited budget of
  remote bumper latch clears (proposed: three per rolling ten minutes);
  beyond that, only a physical reset input clears the latch. The E-stop
  latch always requires physical reset. The E-stop does not care who is
  holding the shell.

## Topology

```text
Claude / Codex
  resident session on the Pi (robot-agent-host.service)
  or remote session over tailnet SSH
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
- Remote access is live SSH over a WireGuard/Tailscale tailnet, key-only,
  with no public port. A cloud session (claude.ai or Codex cloud) can drive
  the same machine the resident seat uses.

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
only while its own health checks pass. If the agent stops or breaks
`robotd`, the heartbeat stops and the robot stops — motion requires a
healthy body daemon by construction. The agent is free to take the serial
port and speak the contract directly (full control means full control), but
it then owns the heartbeat, loses the dashboard's eyes, and the blackbox
records that it did so.

Every command through `robotd` lands in an append-only blackbox log with
timestamps and source, rotated and surfaced in the dashboard.

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

- **Blackbox:** append-only log of every `robotd` command, latch event,
  policy read, and firmware status change.
- **Session recording:** agent shell sessions recorded (auditd + tlog or
  equivalent) and browsable from the dashboard.
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
- Agent kills `robotd` deliberately: covered above — no heartbeat, no
  motion, logged.
- Compromised or misbehaving seat: revoke its SSH key and the seat's API
  credentials, reflash the Pi. The blast radius of the agent account is the
  Pi, by design.

## Security Posture

- SSH is tailnet-only, key-only, `agent` user; no public ports, no
  password auth. The dashboard stays LAN/tailnet-local.
- The agent's API credentials and any secrets it needs live in a store
  scoped to the `agent` user; the seat never needs Brian's accounts.
- Privacy floor stays physical: the mute switch removes mic VBUS in
  hardware and its red ring cannot be spoofed from software. Software
  recording indicators are best-effort under full control; treat the
  hardware ring as the trustworthy one, and consider hardwiring a
  camera-power light as future hardening.

## Milestone Deltas

- **M0 Bench Brain:** additionally install the agent seat. Exit demo: the
  agent, over live SSH and the resident session, installs a package, writes
  and runs a new script, speaks, listens, and journals — no motors exist
  yet.
- **M1 Rolling Chassis:** unchanged and still gates everything. The
  firmware envelope (clamps, watchdog kill test, all six NC bumper zones,
  latch budget, E-stop, charger inhibit) passes bench tests before the
  agent's first drive command. Agent is read-only telemetry until then.
- **M2 Senses And Speech:** the agent authors its first behaviors
  (`look_at_speaker`, `come_here`) in a prepared area, replacing "voice
  commands route to intents."
- **M3/M4:** unchanged in intent; behaviors are agent-authored code.

Additional acceptance checks: kill `robotd` under commanded motion and see
the robot stop within the watchdog window; fill the latch-clear budget and
confirm only physical reset recovers; verify the blackbox and session
recording captured an entire agent-driven session; press the E-stop while
the agent is driving.

## Open Questions

- Exact harness shape per seat (Claude Code headless vs Agent SDK service;
  Codex CLI equivalents), session cadence, and token budget for background
  turns.
- Final heartbeat rate and watchdog timeout (proposed 20 Hz / 250 ms) and
  the bumper latch-clear budget values.
- Journal/memory privacy scoping and what syncs off-robot, now that the
  agent manages its own memory.
- Whether the perception baseline (person tracking) ships preinstalled or
  is the agent's first install job.
- Whether the physical latch-reset input is the E-stop twist cycle or a
  dedicated service button on the safety shelf.
