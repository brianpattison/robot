# MVP Architecture: Codex House Companion

## Overview

The MVP is a small wheeled indoor companion body for the resident agent — Claude or Codex. It runs on the existing Raspberry Pi 5 8GB, with no AI HAT+ 2 required for the first build. The robot listens, talks, looks around through a camera head, moves cautiously around approved indoor areas, and exposes a local dashboard for debugging and control.

The agent seat is pluggable: Claude or Codex is the primary conversational and agentic identity (D031), with full authority over the robot computer (D030; see [`agentic-control-plan.md`](agentic-control-plan.md)). The robot may still use other subsystems and models for wake word detection, speech-to-text, text-to-speech, person detection, navigation, and safety monitoring. Those subsystems are tools and reflexes; they are not alternate personalities. The tiny body gets one narrator, many nerves.

## Principles

- **Fail stopped:** boot, faults, watchdog timeouts, and low-confidence autonomy all end in stopped or manual-help states.
- **Safety is deterministic:** E-stop, bumpers, watchdog, motor enable, speed limits, and obstacle stops are not LLM-driven.
- **The agent owns the computer, firmware owns physics:** the resident agent (Claude or Codex) has full Linux authority — shell, installs, code on the fly, direct velocity setpoints — while the safety MCU firmware clamps speed and latches stops no matter what the Pi says (D030, D032).
- **Cloud can enrich, but not unblock safety:** network loss may reduce conversation quality, but local stop/mute/status/manual-control paths keep working.
- **Visible state:** LEDs/audio cues make listening, speaking, moving, muted, stopped, and error states obvious.
- **Modular body and software:** the MVP should be easy to print, inspect, service, and replace in small pieces.

## Runtime Components

### Physical Control Layer

- Safety microcontroller: the Raspberry Pi Pico 2 baseline owns the watchdog, motion-setpoint leases, latched stops, and the motor-enable path (D032); the Cytron MDDS10 remains the motor driver, not the safety owner.
- Motor enable relay or equivalent motor-power gate.
- Encoder motor control for differential drive.
- Bumper switches and optional cliff/drop sensors.
- Physical E-stop that cuts motor power independently of the Pi.
- Watchdog input from the Pi; timeout disables motion.

This layer owns immediate motor shutdown and hard limits. It should continue to make safe decisions even if Linux, ROS, the dashboard, or the agent is confused.

### Raspberry Pi Robot Runtime

- Sensor drivers for camera, mic array, proximity sensors, battery monitor, motor controller, and LEDs.
- `robotd` body daemon: exclusive serial link to the safety MCU, motion/head/speak/senses/LED API, mode and state tracking (`booting`, `stopped`, `idle`, `listening`, `speaking`, `manual_drive`, `fault`, `muted`, active behavior), event stream, command blackbox, and the firmware heartbeat, emitted only while its health checks pass.
- Agent-authored behaviors under `/home/agent/behaviors/`: the starter library (`come_here`, `follow_user`, `go_home`, ...) plus whatever the agent writes next, running as ordinary processes against `robotd`.
- Local command router for urgent commands such as `stop`, `wait`, `mute`, `unmute`, and `status`.
- Health monitor for battery, CPU temperature, service state, network, camera, mic, speaker, sensors, and motor faults.

### Local Service Interface

The center rear cartridge is intentionally blank. D024 removed the custom UART
PCB and external jack rather than adding an unnecessary powered interface.
Development diagnostics use the Pi/Pico's internal service connectors with the
robot shut down or the motor branch physically isolated. No service procedure
may bypass the E-stop, bumpers, watchdog, charger inhibit, or explicit motion
enable. A future external service interface requires its own retail-only
decision and safety review.

### Perception Layer

- Camera capture and optional preview stream.
- Person detection/tracking for follow and approach behaviors.
- Speaker direction estimate when the mic array supports it.
- Proximity fusion from ToF sensors, bumpers, and optional future LiDAR/depth sensor.
- Confidence scoring for person tracking, localization, and obstacle awareness.

Perception produces structured facts such as `person_seen`, `selected_user_track`, `path_blocked`, `speaker_angle`, and `low_confidence`. It should not directly command motors.

### Voice And Conversation Layer

- Wake word listener.
- Streaming or chunked speech-to-text.
- Local urgent-intent recognizer for safety-sensitive phrases.
- Resident agent seat (Claude or Codex) for conversation and everything the agent decides to do about it.
- Text-to-speech output with barge-in support.
- Conversation state, preferences, and memory hooks.
- Maintained E-Switch PVB3F230SS311 physical mute in the rear-right service cartridge. Its SPDT common receives fused microphone 5 V; LISTEN powers microphone VBUS, while MUTE removes VBUS and drives the red ring plus a protected local state input. This hardware state must work and remain visible without the conversation process or network.

Simple acknowledgements such as "stopping," "muted," "battery is low," or "I need help" should be available locally even when cloud conversation is unavailable.

### Navigation And Behavior Layer

- Manual drive mode with strict velocity caps.
- One-floor map or manually defined named points.
- Local planner for short cautious motion.
- Follow behavior that keeps a comfortable distance from the selected user.
- Come-here behavior that approaches, stops, and looks up rather than crowding.
- Go-home behavior that navigates to a manually defined home area or asks for help.

Navigation code is agent-maintained under D030. It should still refuse to move on low confidence as a matter of good behavior, but the guarantee that an open bumper loop produces a latched zero-motion state comes from the firmware envelope, not from navigation.

### Local Dashboard

- Browser-based local UI on the Pi.
- Camera preview.
- Robot state, current mode, battery, temperatures, network, and service health.
- Sensor status for bumpers, proximity, E-stop, watchdog, and motor faults.
- Manual drive controls with speed caps.
- Logs and recent events.
- Emergency stop / software stop button.
- Settings for no-go zones, named locations, quiet hours, and debug capture.

The dashboard is a development and supervision tool, not a replacement for the physical E-stop.

## Safety And Control Boundary

The resident agent has full authority over everything that runs on the Pi (D030): it commands velocity and head setpoints directly through `robotd`, writes and hot-swaps its own behaviors, installs software, and works over live SSH. The old intent list (`stop`, `look_at_speaker`, `come_here`, `follow_user`, `wait`, `go_home`, `explore_nearby`, `say`, `set_led_state`) survives as the starter behavior library, not as a boundary.

The boundary that remains is the one the Pi cannot reach (D032). The agent cannot exceed the firmware velocity/acceleration clamps, clear an E-stop latch, bypass the watchdog, defeat the normally-closed bumper stops, restart motion past the charger inhibit, or un-mute the hardware microphone switch. Those live in safety MCU firmware and physical controls, and the Pi-to-MCU protocol has no flash or config-write path.

Motion commands pass through this chain:

```text
Agent command (robotd call, or code the agent wrote)
  -> robotd body daemon: blackbox logging, telemetry, heartbeat
  -> serial contract to the safety MCU
  -> firmware envelope: clamps, setpoint leases, watchdog, latched stops
  -> motor controller
  -> motors
```

No-go zones, quiet hours, and supervision rules are policy the agent is instructed to honor and the blackbox audits (see [`agentic-control-plan.md`](agentic-control-plan.md)). The firmware has the final say on physics. Very democratic until safety votes no.

## Data And Control Flow

```text
Sensors
  camera, mic, ToF, bumpers, encoders, battery, E-stop
    -> Pi services
      -> perception facts, health state, odometry, audio events
        -> behavior state machine
          -> dashboard updates
          -> agent context
          -> navigation requests
            -> motion gateway
              -> safety controller
                -> motors / LEDs / speaker cues
```

Recommended message pattern:

- Events are append-only facts: `bumper_pressed`, `wake_word_heard`, `person_track_lost`, `battery_low`.
- Commands are explicit requests: `set_mode`, `speak_text`, `navigate_to`, `set_head_angle`, `drive_velocity`.
- State is observable: `current_mode`, `safety_state`, `motion_enabled`, `active_goal`, `confidence`, `last_fault`.

## Voice And Conversation Flow

1. Wake word listener runs locally.
2. On wake, LEDs show listening state and audio is sent to STT.
3. Local urgent-intent recognizer checks for commands like `stop`, `wait`, or `mute` as early as possible.
4. Non-urgent transcript becomes a turn in the resident agent session, with relevant robot state attached.
5. The agent answers however it sees fit: speak, drive through `robotd`, look something up, or write and run new code.
6. The firmware envelope clamps whatever motion results; policy and confidence shape what the agent chooses to do.
7. TTS speaks the response.
8. Barge-in can interrupt TTS for `stop`, `wait`, wake word, or dashboard stop.

If STT, network, or the agent seat fails, the robot still handles local `stop`, `mute`, `status`, and dashboard/manual-control commands — plus any behaviors the agent already deployed, since those are local code and do not need the agent in the loop.

## Perception And Navigation Flow

1. Camera and proximity sensors publish observations.
2. Person detector identifies candidate users and tracks confidence.
3. Speaker direction, if available, rotates the head/camera toward the voice before movement.
4. Navigation receives a goal such as "approach selected user" or "go to home."
5. Planner checks no-go zones, obstacle distance, bumper state, battery, and localization confidence.
6. Motion gateway sends capped velocity commands to the motor controller.
7. Safety controller stops on bumper, E-stop, watchdog timeout, overcurrent, or invalid command stream.
8. If confidence drops, the robot stops, looks/speaks, and asks for help.

The six bumper inputs should use normally-closed circuits. Any open circuit,
including a pressed switch, disconnected plug, or broken wire, is a latched
stop/fault until the safety controller observes a valid released loop and
receives an explicit clear — from the agent, the dashboard, or a physical
input. Firmware permits no motion while a loop is open because a pressed
SPST-NC switch and a broken or unplugged conductor are electrically
indistinguishable. Do not infer bumper safety from Linux process health or the
LLM.

The motor branch's mechanical cutoff baseline is a Panasonic CB1A-R-M-12V
sealed SPST-NO automotive relay with an integral bracket, one 5.4 mm mounting
hole, 40 A contact rating at 14 V, 12 V/134 mA coil, and built-in resistor. The
Pi and safety controller remain on individually fused upstream branches so they
can report a stop; only the motor-driver positive branch passes through the
relay. Both IDEC direct-opening NC channels must be in the
low-current, fail-deenergized coil-enable path, with a hardware reset latch so
releasing the mushroom cannot restart motion. Exact coil variant, suppression,
terminal/conductor sizing, driver behavior, dropout time, fusing, contact-fault detection, and full-charge
LiFePO4 motor-voltage limiting require electrical-engineering review and bench
tests. The E-stop never carries motor current directly.

The rolling-prototype mobile-power baseline coordinates the lower-current
Pololu #4867 motors with one Bioenno BLF-1203AB 12 V/3 Ah LiFePO4 pack and its
matched BPC-1502DC 14.6 V/2 A charger. The rear Switchcraft EN2 inlet is
charge-only: two contacts go only to the pack's isolated charge lead and the
third reports protected `CHARGER_PRESENT`. It exposes no battery output and is
not a disconnect. Charger insertion must de-energize motor enable/the Panasonic relay through
the deterministic safety path; removal must not restart motion without an
explicit reset. Because EN2 is not rated for current interruption, remove
charger AC before mating or unmating. The candidate remains blocked on
delivered-part evidence/fit, Blue Sea 5045 mounting and fuse release,
polarity/strain relief, <=5.6 A sustained pack current, 45-minute runtime with
20% reserve, BMS/regen/thermal behavior, and full/low-charge loaded floor tests.

Accessory distribution uses a complete Blue Sea Systems 5045 covered four-
circuit ATO/ATC fuse block, modeled at 92.5 x 43.8 x 32.5 mm with two mounting
holes on 65.1 mm centers. It is limited provisionally to 6 A total and 5 A on
any branch despite its higher catalog ratings.
Exact fuse values remain unset until measured startup/transient/fault loads and
time-current curves are reviewed. A battery-near accessory feeder fuse is still
required; the fuse block must have covered live parts, terminal protection,
strain relief, labels, power-off-only service, selective-fault and thermal
tests, and no path around the independently fused and relay-cut motor branch.

D024 supersedes the custom Nano2/Micro-Fit board described by D023. The legacy
distribution coupon is historical mechanical evidence and is not a release
gate for the Blue Sea block.

MVP navigation should start with one-room or prepared-area behavior before full floor roaming. The body should reserve space and power for future 2D LiDAR, but camera + ToF + bumpers are enough for the first bench and supervised rolling tests.

## Dashboard

The dashboard should be available on the local network and usable from a laptop or phone. MVP panels:

- **Status:** mode, safety state, battery, temperature, uptime, network.
- **Live View:** camera preview and latest perception facts.
- **Drive:** capped manual controls, head pan/tilt, stop button.
- **Sensors:** bumpers, ToF distances, E-stop, watchdog, encoders, motor faults.
- **Logs:** recent events, service errors, voice command summaries, navigation failures.
- **Settings:** named points, no-go zones, speed cap, quiet hours, debug capture.

Access should be local-only for MVP unless remote access is explicitly designed later.

## Deployment And Runtime Process Layout

Target layout on the Raspberry Pi:

```text
systemd
  robot-supervisor.service
    health monitor
    service restart policy

  robotd.service
    serial contract to the safety MCU
    watchdog heartbeat, emitted only while health checks pass
    motion / head / speak / senses / LED API
    event stream and command blackbox

  robot-perception.service
    camera capture
    person tracking
    proximity fusion
    agent-managed; the agent may replace or extend it

  robot-voice.service
    wake word
    STT
    urgent local intents
    TTS

  robot-agent-host.service
    resident agent seat: Claude Code / Agent SDK or Codex CLI, headless
    conversation turns in, actions out
    agent journal and background schedule

  robot-dashboard.service
    local web UI
    websocket/event stream
    manual drive API
    agent panel: live session view, session recordings, software stop

  cloudflared.service
    outbound-only Cloudflare Tunnel (D033)
    SSH ingress via Access service tokens; no inbound ports anywhere
```

For early development, these can be Python processes with simple JSON/WebSocket or ROS 2 topics between them. If ROS 2 is adopted, keep `robotd` independent enough that it can still fail stopped when ROS nodes crash. The agent may reorganize anything above `robotd`; `robotd` and the firmware contract are the parts to keep boring.

The tracked bench implementation currently covers the boring core:

- `software/robotd/` provides the local Unix-socket/UART daemon, client,
  simulator, blackbox, and systemd unit. `software/appliance/` plus
  `software/install.sh` provision a versioned Pi 5 Bookworm appliance with
  key-only Access-gated SSH, preserved debug UART10, RP1 GPIO UART0 pinned as
  `/dev/rover-pico`, local tlog capture, and an explicitly untrusted RW backup.
- `docs/body-protocol-v1.md` is the fixed framed-UART contract.
- `firmware/pico2-safety/` supplies a host-tested C11 safety core and a
  fail-stopped Pico SDK integration with no production motor output.
- `harness/` supplies the nominal 28-route first-article traveler and a
  deliberately red physical release gate.
- `commissioning/` supplies the 27-step evidence plan and runner. No physical
  pass is bundled.

Run `python3 commissioning/run_host_tests.py` for the hardware-free baseline.
The wider perception, voice, dashboard, and agent-host, production motor/encoder
output, real Pi/Tunnel/UART attestations, append-only external collector proof,
and physical commissioning layers remain to be built and tested.

Boot behavior:

1. Robot starts in `stopped`.
2. Safety bridge connects to controller and confirms E-stop, bumpers, battery, and watchdog.
3. Dashboard becomes available.
4. Manual movement requires explicit enable.
5. Autonomous movement requires explicit mode selection and all safety checks passing.

Boot validation must reject motion if any normally-closed bumper loop is open,
shorted into an implausible state, stale, or untested after controller reset.

## MVP Boundary

### Required For MVP

- Raspberry Pi 5 8GB runtime.
- Camera, mic array, speaker, LEDs.
- Differential drive with encoders.
- Physical E-stop independent of the Pi.
- Bumper switches.
- Watchdog-driven motor disable.
- Local dashboard.
- Local urgent commands for `stop`, `wait`, `mute/status`.
- A resident agent seat (Claude or Codex) with full shell authority, live SSH through the Cloudflare Tunnel, and the `robotd` body API.
- Append-only command blackbox and recorded agent sessions.
- Cautious one-room or prepared-area movement.
- Manual drive and supervised follow/come/go-home demos.

### Explicitly Not Required For MVP

- AI HAT+ 2.
- Fully local rich LLM/VLM conversation.
- Fully autonomous charging dock.
- Unsupervised whole-house roaming.
- Outdoor use.
- Stairs.
- Object manipulation.
- Legged locomotion.
- Silent always-on recording.

## Future Upgrade Boundaries

- **AI HAT+ 2:** add later for local LLM/VLM experiments, privacy-sensitive scene summaries, offline fallback intelligence, and eventually a local agent seat.
- **2D LiDAR or depth sensor:** add if navigation reliability with camera + ToF is not good enough.
- **Docking:** add after manual charging and go-home behavior are reliable.
- **LeRobot:** add as an optional learning/data layer after deterministic safety and teleop are stable.
- **Better autonomy:** expand from prepared area to one mapped floor only after repeated safe trials.
- **Improved body shell:** move from simple printed modules to more polished `build123d`/CadQuery shells after the service layout stabilizes.

## Open Questions

- Should MVP use ROS 2 immediately, or start with simpler Python services and leave a ROS 2 migration path?
- Which mic array gives the best wake word accuracy while the motors are running?
- Do we want 2D LiDAR in the first rolling chassis, or only reserve the mount and power budget?
- What is the first safe test area in the house, and what no-go zones should be hardcoded before mapping?
- What is the preferred TTS voice and speaker loudness target?
- How should the agent's journal/memory be stored, synced, and privacy-scoped, now that the agent manages it itself?
- What local-only commands should work even with no internet?
- Which exact feeder and ATO/ATC branch fuse values, terminal parts, and wire gauges pass the measured-load, selective-short, crimp-pull, and Blue Sea 5045 thermal review?
