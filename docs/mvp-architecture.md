# MVP Architecture: Codex House Companion

## Overview

The MVP is a small wheeled indoor companion body for Codex. It runs on the existing Raspberry Pi 5 8GB, with no AI HAT+ 2 required for the first build. The robot listens, talks, looks around through a camera head, moves cautiously around approved indoor areas, and exposes a local dashboard for debugging and control.

Codex/ChatGPT is the primary conversational and agentic identity. The robot may still use other subsystems and models for wake word detection, speech-to-text, text-to-speech, person detection, navigation, and safety monitoring. Those subsystems are tools and reflexes; they are not alternate personalities. The tiny body gets one narrator, many nerves.

## Principles

- **Fail stopped:** boot, faults, watchdog timeouts, and low-confidence autonomy all end in stopped or manual-help states.
- **Safety is deterministic:** E-stop, bumpers, watchdog, motor enable, speed limits, and obstacle stops are not LLM-driven.
- **LLM issues intents, not wheel commands:** Codex can request `come_here`, `follow_user`, `look_at_speaker`, `go_home`, or `stop`; lower layers validate and execute.
- **Cloud can enrich, but not unblock safety:** network loss may reduce conversation quality, but local stop/mute/status/manual-control paths keep working.
- **Visible state:** LEDs/audio cues make listening, speaking, moving, muted, stopped, and error states obvious.
- **Modular body and software:** the MVP should be easy to print, inspect, service, and replace in small pieces.

## Runtime Components

### Physical Control Layer

- Safety microcontroller or dedicated motor controller.
- Motor enable relay or equivalent motor-power gate.
- Encoder motor control for differential drive.
- Bumper switches and optional cliff/drop sensors.
- Physical E-stop that cuts motor power independently of the Pi.
- Watchdog input from the Pi; timeout disables motion.

This layer owns immediate motor shutdown and hard limits. It should continue to make safe decisions even if Linux, ROS, the dashboard, or Codex is confused.

### Raspberry Pi Robot Runtime

- Sensor drivers for camera, mic array, proximity sensors, battery monitor, motor controller, and LEDs.
- Motion gateway that converts validated velocity or navigation requests into low-level controller messages.
- Behavior state machine for `booting`, `stopped`, `idle`, `listening`, `speaking`, `manual_drive`, `come_here`, `follow`, `go_home`, `mapping`, `fault`, and `muted`.
- Local command router for urgent commands such as `stop`, `wait`, `mute`, `unmute`, and `status`.
- Health monitor for battery, CPU temperature, service state, network, camera, mic, speaker, sensors, and motor faults.

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
- Codex/ChatGPT bridge for richer conversation and high-level decisions.
- Text-to-speech output with barge-in support.
- Conversation state, preferences, and memory hooks.

Simple acknowledgements such as "stopping," "muted," "battery is low," or "I need help" should be available locally even when cloud conversation is unavailable.

### Navigation And Behavior Layer

- Manual drive mode with strict velocity caps.
- One-floor map or manually defined named points.
- Local planner for short cautious motion.
- Follow behavior that keeps a comfortable distance from the selected user.
- Come-here behavior that approaches, stops, and looks up rather than crowding.
- Go-home behavior that navigates to a manually defined home area or asks for help.

Navigation can reject commands from Codex if the map, sensors, battery, or confidence state makes movement unsafe.

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

Codex can request high-level actions:

- `stop`
- `look_at_speaker`
- `come_here`
- `follow_user`
- `wait`
- `go_home`
- `explore_nearby`
- `say`
- `set_led_state`

Codex cannot directly set unbounded wheel speeds, disable bumpers, disable E-stop behavior, bypass the watchdog, ignore low battery, or override no-go zones.

Movement requests pass through this chain:

```text
Codex intent
  -> behavior state machine
  -> navigation / motion validator
  -> velocity and acceleration limiter
  -> Pi motion gateway
  -> safety controller / motor controller
  -> motors
```

Any layer may downgrade the request to `stop`, `wait`, or `ask_for_help`. The safety controller has the final say. Very democratic until safety votes no.

## Data And Control Flow

```text
Sensors
  camera, mic, ToF, bumpers, encoders, battery, E-stop
    -> Pi services
      -> perception facts, health state, odometry, audio events
        -> behavior state machine
          -> dashboard updates
          -> Codex context
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
4. Non-urgent transcript goes to the Codex/ChatGPT bridge with relevant robot state.
5. Codex returns speech plus optional structured intents.
6. Behavior layer validates intents against safety, battery, map, and confidence state.
7. TTS speaks the response.
8. Barge-in can interrupt TTS for `stop`, `wait`, wake word, or dashboard stop.

If STT, network, or Codex fails, the robot should still handle local `stop`, `mute`, `status`, and dashboard/manual-control commands.

## Perception And Navigation Flow

1. Camera and proximity sensors publish observations.
2. Person detector identifies candidate users and tracks confidence.
3. Speaker direction, if available, rotates the head/camera toward the voice before movement.
4. Navigation receives a goal such as "approach selected user" or "go to home."
5. Planner checks no-go zones, obstacle distance, bumper state, battery, and localization confidence.
6. Motion gateway sends capped velocity commands to the motor controller.
7. Safety controller stops on bumper, E-stop, watchdog timeout, overcurrent, or invalid command stream.
8. If confidence drops, the robot stops, looks/speaks, and asks for help.

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
    behavior state machine
    service restart policy

  robot-safety-bridge.service
    watchdog heartbeat
    motor-controller link
    E-stop / bumper state ingestion

  robot-perception.service
    camera capture
    person tracking
    proximity fusion

  robot-voice.service
    wake word
    STT
    urgent local intents
    TTS

  robot-agent.service
    Codex/ChatGPT bridge
    conversation state
    high-level intent output

  robot-dashboard.service
    local web UI
    websocket/event stream
    manual drive API
```

For early development, these can be Python processes with simple JSON/WebSocket or ROS 2 topics between them. If ROS 2 is adopted, keep the safety bridge independent enough that it can still fail stopped when ROS nodes crash.

Boot behavior:

1. Robot starts in `stopped`.
2. Safety bridge connects to controller and confirms E-stop, bumpers, battery, and watchdog.
3. Dashboard becomes available.
4. Manual movement requires explicit enable.
5. Autonomous movement requires explicit mode selection and all safety checks passing.

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
- Cloud-assisted Codex/ChatGPT conversation.
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

- **AI HAT+ 2:** add later for local LLM/VLM experiments, privacy-sensitive scene summaries, and offline fallback intelligence.
- **2D LiDAR or depth sensor:** add if navigation reliability with camera + ToF is not good enough.
- **Docking:** add after manual charging and go-home behavior are reliable.
- **LeRobot:** add as an optional learning/data layer after deterministic safety and teleop are stable.
- **Better autonomy:** expand from prepared area to one mapped floor only after repeated safe trials.
- **Improved body shell:** move from simple printed modules to more polished `build123d`/CadQuery shells after the service layout stabilizes.

## Open Questions

- Which motor controller and safety microcontroller should own the watchdog and motor enable line?
- Should MVP use ROS 2 immediately, or start with simpler Python services and leave a ROS 2 migration path?
- Which mic array gives the best wake word accuracy while the motors are running?
- Do we want 2D LiDAR in the first rolling chassis, or only reserve the mount and power budget?
- What is the first safe test area in the house, and what no-go zones should be hardcoded before mapping?
- What is the preferred TTS voice and speaker loudness target?
- How should Codex memory for the body be stored, synced, and privacy-scoped?
- What local-only commands should work even with no internet?
- What battery chemistry, charger, and fuse layout best balance runtime, safety, and serviceability?
