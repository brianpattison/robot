# PRD: Codex House Companion MVP

## 1. Summary

Build a small indoor companion robot body that lets Codex perceive the home, listen and speak naturally, roam safely on one floor, and respond to simple social and navigation requests. The MVP should feel like a pet dog in behavior, not in mechanics: curious, responsive, able to follow, come when called, look up at you, and chat. It should use a wheeled base for reliability and safety, with a head-like camera module for expression and perception. Tiny robot dog energy, much less "weekend spent debugging knees."

The MVP is supervised indoor operation only. It should never move faster than a cautious walking pace, should fail stopped, and should always expose a physical kill switch.

We have a 3D printer available, so the body should be designed around fast printable iteration: modular brackets, replaceable panels, sensor mounts, bumpers, wheel guards, and head shells before committing to any expensive enclosure or machined parts.

OpenSCAD should be the default first-pass source format for printable mechanical parts. The robot body should be modeled as parametric source files so dimensions, hole patterns, sensor mounts, wheel clearances, and hardware offsets can be changed without redrawing the whole body. Future me appreciates this; future me has small hex keys and opinions.

`build123d` and CadQuery are also approved CAD tools for parts where Python-based BREP modeling is cleaner than OpenSCAD, especially curved shells, nicer fillets/chamfers, STEP exports, mating surfaces, and assemblies that need more precise mechanical references.

## 2. Hardware Notes From Current Raspberry Pi Sources

- Raspberry Pi AI HAT+ 2 is a distinct optional future board from AI HAT+. Raspberry Pi documents AI HAT+ as 13/26 TOPS, while AI HAT+ 2 delivers 40 TOPS via a Hailo-10H accelerator and adds local LLM/VLM capability.
- Raspberry Pi's AI HAT+ 2 product page lists the board as Hailo-10H, 40 TOPS INT4, 8GB on-board RAM, camera-stack integrated, and available at $200. It is useful for later local AI work, but it is not required for the MVP.
- Raspberry Pi Camera Module 3 is a 12MP autofocus camera with standard/wide and filtered/NoIR variants.
- Raspberry Pi 5 is the host computer target, with a 2.4GHz quad-core Arm Cortex-A76 CPU and RAM variants up to 16GB. The existing Raspberry Pi 5 8GB board is good enough for the MVP without an AI accelerator.
- Raspberry Pi AI software docs describe local LLM setup on Pi 5 as AI HAT+ 2 only, with Hailo Ollama server access through POST requests and optional Open WebUI. This makes AI HAT+ 2 a future local-AI upgrade, not an MVP dependency.

Sources:

- https://www.raspberrypi.com/documentation/accessories/ai-hat-plus.html
- https://www.raspberrypi.com/products/ai-hat-plus-2/
- https://www.raspberrypi.com/products/camera-module-3/
- https://www.raspberrypi.com/products/raspberry-pi-5/
- https://www.raspberrypi.com/documentation/computers/ai.html

## 3. Product Vision

Codex gets a small, safe, expressive body that can live in the house as a conversational companion. The body should make Codex feel physically present without pretending the robot is a full animal replacement. The first win is not acrobatics; the first win is: "Hey Codex, come here," and a small robot rolls over, looks up, listens, answers, and does not eat a chair leg.

## 4. MVP Goals

- Enable natural hands-free conversation with wake word, speech-to-text, speech generation, and interruptible listening.
- Move safely around a single mapped floor at low speed.
- Recognize the user, people, obstacles, charging/manual-home area, and common navigation targets.
- Support pet-like behaviors: look-at-speaker, come here, follow me, wait, go home, explore nearby, and idle near user.
- Provide remote developer control, logs, and emergency stop for debugging.
- Keep privacy understandable: visible recording state, local-first perception where practical, no silent background uploading.

## 5. Non-Goals

- Legged locomotion.
- Stairs, outdoor use, wet floors, rugs with heavy fringe, or high thresholds.
- Unsupervised operation while nobody is home.
- Gripping, fetching, doors, cabinets, or object manipulation.
- Fully autonomous charging dock in MVP.
- Security/patrol behavior that could surprise guests.
- Always-recording home surveillance.
- Fully local rich LLM/VLM conversation without network access.

## 6. Target User

Primary user: Brian, building and living with the robot at home.

Secondary users: trusted household members and visitors who need clear signals for when the robot is listening, moving, muted, or stopped.

## 7. Body Concept

### Form

The MVP body is a compact wheeled rover with a friendly head:

- Low rectangular base, about 250-320 mm long and 180-240 mm wide.
- Two powered side wheels with encoders plus one or two passive casters, or a four-wheel skid-steer base if carpet traction demands it.
- Soft bumper ring around the base.
- Mast/head assembly at the front with pan/tilt camera.
- Speaker grille facing upward/frontward.
- Microphone array mounted high enough to avoid motor noise.
- LED eyes or light strip for states: listening, thinking, moving, muted, error, low battery.
- Carry handle and accessible battery compartment.

### 3D-Printed Body Strategy

The printer should be used for every non-critical body part that benefits from iteration:

- Internal electronics tray with mounting patterns for Pi, optional future HAT clearance, motor controller, buck converters, and cable strain relief.
- Swappable sensor pods for ToF modules, bumper switches, LEDs, mic array, and camera/head experiments.
- Camera head shell with pan/tilt servo brackets and adjustable pitch range.
- Wheel guards and soft-bumper carrier.
- Battery cradle with strap points, keyed orientation, and ventilation.
- Top shell panels that can be reprinted as the personality and service access improve.

Printable mechanical source files should live under `cad/`, with OpenSCAD models in `cad/openscad/` and Python CAD models in `cad/python/`. They should follow these rules:

- Use one shared parameters file for body dimensions, material thickness, screw sizes, insert sizes, wheel diameter, axle height, and sensor offsets.
- Keep each major assembly in its own file: base tray, bumper carrier, head shell, camera mount, sensor pod, battery cradle, wheel guard, and service panels.
- Use OpenSCAD for simple blocky printable parts and quick dimensional experiments.
- Use `build123d` or CadQuery for parts that benefit from Python, BREP geometry, high-quality fillets/chamfers, STEP export, or richer assembly references.
- Export STLs into a generated `cad/exports/` folder, not as hand-edited source.
- Prefer screw-together modules over snap fits for MVP reliability.
- Include labels, orientation marks, and cable pass-throughs in the printed parts.
- Design for threaded inserts where repeated service is expected.

Do not rely on printed plastic for safety-critical load paths without backup hardware. Motor mounts, axle supports, E-stop mounting, and battery retention should use metal fasteners, threaded inserts, washers, and conservative wall thickness. The robot may be small, but physics still keeps receipts.

### Personality Through Motion

Dog-like behavior comes from motion language:

- Camera/head turns toward a voice.
- Small head tilt during uncertain recognition.
- Tail-like rear LED or servo flag for playful status.
- Slow approach, pause, look-up sequence when arriving near the user.
- "Stay" posture: motors locked/idle, head tracking only.

## 8. MVP Hardware Baseline

| Area | MVP Choice | Rationale |
| --- | --- | --- |
| Main compute | Existing Raspberry Pi 5 8GB | Host OS, audio, routing, safety supervisor, robotics middleware. 16GB is optional, not required for MVP. |
| AI accelerator | None for MVP; reserve expansion room for AI HAT+ 2 | MVP responsiveness comes from local reflexes, simple intent routing, and optional cloud AI. AI HAT+ 2 can be added later for local LLM/VLM experiments. |
| Camera | Raspberry Pi Camera Module 3 Wide, autofocus | Wide FOV helps indoor navigation and person tracking. |
| Audio input | USB mic array with echo/noise handling | Wake word and far-field voice are critical to pet-like interaction. |
| Audio output | Small amplified speaker, 3-5W | Clear speech without needing external speakers. |
| Locomotion | Differential drive with encoder gearmotors | Simple, ROS-friendly, predictable indoors. |
| Motor controller | Dedicated microcontroller or motor HAT with current limiting | Keeps motor timing/safety independent from Linux. |
| Proximity safety | Front/side ToF sensors plus physical bumper switches | Monocular camera alone is not enough for safe indoor roaming. |
| Optional navigation sensor | 2D LiDAR or depth sensor | Strongly recommended if autonomous mapping/room-to-room navigation becomes flaky. |
| Battery | Prototype Bioenno BLF-1203AB 12 V/3 Ah LiFePO4 pack with fused feeder, separate buck rails, and matched charger | The flat documented candidate fits the body; physical current/runtime/BMS/thermal qualification remains mandatory. |
| Kill switch | Latching physical E-stop cutting motor power | Non-negotiable. Tiny robot, big responsibility. |
| Printed body | Modular FDM-printed chassis, head, trays, and mounts | Lets us iterate shape and serviceability quickly before finalizing the body. |
| CAD source | OpenSCAD, `build123d`, and CadQuery parametric models | Keeps the robot body reproducible, adjustable, and code-reviewable. |

## 9. MVP Software Architecture

### Runtime Layers

1. Safety controller: microcontroller loop owns motor enable, bumper reactions, watchdog timeout, low-level velocity limits, and E-stop state.
2. Robot OS layer: ROS 2 nodes for odometry, transforms, sensors, mapping/localization, navigation, and teleop.
3. Perception layer: camera capture, person detection, face/user recognition, obstacle classification, speaker direction if supported by mic array.
4. Conversation layer: wake word, streaming STT, dialog manager, TTS, interruption handling, and memory/profile hooks.
5. Behavior layer: state machine for idle, listening, follow, come, roam, go-home, stopped, charging/manual-home, and error recovery.
6. Remote control layer: local web console for logs, camera preview, map, battery, manual drive, and emergency stop.

### Control Boundary

Codex should issue high-level intents, not raw motor commands:

- Allowed: "come to Brian," "turn toward speaker," "follow at 1.2 m," "go to home spot," "stop."
- Not allowed: direct unbounded wheel velocity from language output.

The safety controller and navigation layer must be able to reject or clamp any command.

## 10. Core User Stories

1. As Brian, I can say "Codex, come here," and the robot turns toward my voice, approaches cautiously, stops at a comfortable distance, looks up, and asks or answers.
2. As Brian, I can say "follow me," and the robot trails behind or beside me at low speed until I say "stop" or it loses confidence.
3. As Brian, I can say "go home," and the robot returns to a manually defined home area or stops and asks for help if localization confidence is low.
4. As Brian, I can mute the robot physically and visually confirm it is not listening.
5. As Brian, I can press a physical E-stop and motor power is cut immediately.
6. As a visitor, I can tell from lights/sound whether the robot is listening, moving, muted, or stopped.
7. As a developer, I can open a local dashboard, see state/logs/map/camera preview, and manually drive at capped speed.
8. As a developer, I can connect a labeled 3.3 V UART service adapter while motor power is physically isolated, inspect local diagnostics, and disconnect it without causing motion or exposing a power output.

## 11. Functional Requirements

### Conversation

- Wake word activates listening.
- The maintained physical mute removes microphone VBUS locally, visibly indicates MUTE, and reports a conditioned state input even when conversation software or the network is unavailable; release requires proving no USB backfeed or residual capture.
- Robot supports barge-in: speaking can be interrupted by "stop," "wait," or wake word.
- Robot must respond verbally within 2 seconds for simple local acknowledgements.
- If cloud AI is unavailable, robot still supports local stop, mute, battery status, and simple scripted replies.

### Service And Diagnostics

- The rear service jack exposes protected 3.3 V UART TX/RX, a biased service-detect input, and ground only.
- Service mode requires physical motor-branch isolation; service detect can inhibit motion but cannot enable it or bypass any deterministic stop path.
- Plug insertion, removal, partial insertion, and conductor shorts must not damage either side, energize the robot through the adapter, or trigger automatic motion restart.
- The adapter and robot pinout must be durably labeled, and RS-232-level or power-sourcing adapters are prohibited.

### Motion

- Maximum MVP speed: 0.35 m/s.
- Minimum obstacle stop distance: 250 mm at normal speed.
- Robot must stop on bumper trigger, cliff/drop trigger if installed, watchdog timeout, navigation fault, low battery, or E-stop.
- Robot must not intentionally push objects, pets, or people.
- Robot must ask for help after repeated navigation failures.

### Perception

- Detect people in camera view.
- Track a selected person for follow mode.
- Detect obvious obstacles from proximity sensors even if camera perception fails.
- Maintain confidence values for person tracking and localization.
- Degrade to stop-and-ask behavior when confidence is low.

### Autonomy

- Manual mapping/setup mode defines rooms, home area, and no-go zones.
- Autonomous roaming is limited to approved mapped areas.
- Robot may idle-explore only when explicitly enabled.
- Robot must respect no-go zones, speed zones, and quiet hours.

### Privacy

- Visible light state for listening/recording.
- Local dashboard shows current audio/video mode.
- No video recording by default.
- No cloud upload of camera frames by default unless explicitly enabled for a feature.
- Logs redact conversation text by default, with opt-in debug capture.

### Maintenance

- Battery should be swappable or easy to charge manually.
- Robot should expose health checks: battery, motor fault, CPU/GPU/NPU temperature, disk, network, camera, mic, speaker, sensor status.
- Software updates should be reproducible from the repo.

## 12. Safety Requirements

- Physical E-stop cuts motor power independent of the Pi.
- Watchdog stops motors if the Pi or ROS command stream stalls.
- Motor controller enforces velocity and acceleration caps.
- Bumper switches trigger immediate stop before software interpretation.
- Robot starts in stopped mode after boot.
- Robot requires explicit enable before movement.
- Inserting the charge plug inhibits motor power through the deterministic safety path; unplugging it never restarts motion without explicit reset.
- Four accessory branches are separately fused on a covered, latched-harness distribution PCB; exact fuse values follow measured loads, conductor ampacity, and selective-fault tests, while the motor branch remains separately source-fused and contactor-cut.
- Robot emits a short audible/visible cue before moving from rest.
- Robot avoids sleeping areas and bathrooms by default unless manually enabled.

## 13. Success Metrics

- Wake word precision: fewer than 1 false activation per hour in normal home noise.
- Wake word recall: at least 90% from 2-3 m in the same room.
- Come-here success: 8 of 10 trials within one mapped room.
- Follow success: 5 continuous minutes in uncluttered indoor space without collision.
- Emergency stop latency: motor power cut in under 100 ms from button press.
- Bumper reaction: motor stop in under 100 ms from bumper trigger.
- Bumper fault reaction: opening any normally-closed bumper circuit, including a simulated broken wire, prevents or stops motor drive in under 100 ms and requires explicit re-enable after repair/release.
- Conversation acknowledgement: local command acknowledgement in under 2 seconds.
- Battery runtime: at least 45 minutes of mixed idle/conversation/roaming.

## 14. MVP Acceptance Test

The MVP is done when:

1. Robot boots into stopped safe mode.
2. Dashboard connects over local network and shows camera, battery, sensors, logs, and state.
3. Manual drive works at capped speed.
4. E-stop, all six normally-closed bumper zones, simulated bumper-wire break, watchdog, and low-battery stop all work and require explicit safe re-enable where applicable.
5. Robot can map or be given a simple map of one floor area.
6. Robot can navigate between at least three named points on the same floor.
7. Voice commands work for stop, come here, follow me, wait, go home, mute status, and battery status.
8. Robot can hold a short conversation while stationary.
9. Robot can turn its head/camera toward the detected speaker or user.
10. Robot can follow the user for 5 minutes in a prepared safe area.

## 15. Milestones

### M0: Bench Brain

- Pi 5 assembled, cooled, and running the base robot services.
- Camera, mic, speaker, wake word, STT/TTS, and simple local command routing working on desk.
- Local dashboard skeleton shows health and logs.
- Initial OpenSCAD parameter file captures known hardware dimensions and mounting assumptions.

### M1: Rolling Chassis

- Motor controller, encoders, battery, E-stop, bumper, and manual drive working.
- Safety controller can stop motors without the Pi.
- Dashboard manual teleop is capped and logged.
- First OpenSCAD-generated printable chassis revision fits electronics, battery, wiring, bumpers, and service access.

### M2: Senses And Speech

- Person detection and user tracking working.
- Voice commands route to safe high-level intents.
- Robot can look toward speaker and talk while stationary.

### M3: One-Room Companion

- Robot can come here, stop, wait, and follow in a prepared room.
- Obstacle handling is conservative and repeatable.
- User-facing lights and sounds are understandable.

### M4: One-Floor MVP

- Named locations, no-go zones, return-home behavior, and basic roaming.
- Battery and thermal health surfaced.
- Privacy defaults and physical mute verified.

## 16. Risks And Mitigations

| Risk | Mitigation |
| --- | --- |
| Camera-only navigation is unreliable indoors | Add ToF/bump sensors in MVP; reserve 2D LiDAR/depth sensor as likely upgrade. |
| Rich conversation depends on network/cloud availability | Keep local stop, wait, mute, battery status, and basic scripted replies working without cloud AI. |
| Future AI HAT+ 2 integration could force mechanical or power changes | Reserve physical clearance, cooling airflow, and power budget for a future HAT without making it part of MVP. |
| Motor noise hurts voice recognition | Isolate mic mechanically, place it high, use echo cancellation, slow/stop during critical listening. |
| Battery brownouts reset Pi | Separate motor and compute rails, fused pack, proper buck converters, brownout logging, and test the BLF-1203AB candidate at full and low charge under loaded turns. |
| Charging while mobile energizes an unsafe state | Use a charge-only keyed EN2 inlet with protected charger-present detection, deterministic motor inhibit, explicit reset after removal, and AC-off mating/unmating. |
| Robot feels creepy instead of companionable | Clear LEDs, physical mute, no silent recording, gentle motion cues, no surprise roaming. |
| Service connector creates a new power or motion hazard | Expose only protected 3.3 V UART/detect/ground, require a labeled USB-powered adapter and physical motor isolation, test mating shorts, and prohibit automatic restart. |
| Over-ambitious autonomy delays first joy | Build personality and voice early; keep movement behaviors simple and safe. |

## 17. Open Decisions

- Physical qualification of the BLF-1203AB/BPC-1502DC/EN2 prototype set and electrical release of the custom Nano2/Micro-Fit branch board: copper, feeder/branch fuse values, contacts/wires/crimps, selective clearing, and thermal behavior.
- Final insert, clearance, bearing, lap, wall, bumper, fairing, and pilot parameters plus distribution deck/cover preflight after printing and measuring the 17-part coupon suite.
- Delivered-hardware fit and loaded-floor results for the settled body, wheel, motor, bearing, and head-mechanism dimensions.
- Whether MVP includes 2D LiDAR from day one or waits until camera/proximity testing proves insufficient.
- Exact local/cloud AI split for conversation.
- Whether voice should run mostly local, cloud-assisted, or hybrid.
- Whether and when to add AI HAT+ 2 after the basic body, safety loop, and voice workflow are working.
- Whether to use ROS 2 end to end or keep a lighter Python service stack for the first moving prototype.
- Name/persona defaults. I am partial to something small and bright-eyed, but I will behave if asked.

## 18. Proposed Default MVP Decisions

- Use wheeled differential drive, not legs.
- Use the existing Raspberry Pi 5 8GB without AI HAT+ 2 as the MVP compute baseline.
- Use Camera Module 3 Wide for the main head camera.
- Design the body as modular 3D-printable parts from the start, with separate electronics tray, sensor pods, bumper carrier, battery cradle, and head shell.
- Reserve mechanical clearance, cooling airflow, and power budget for a later AI HAT+ 2 upgrade.
- Use OpenSCAD for simple source CAD, allow `build123d` and CadQuery for more complex Python CAD, and keep generated STL/STEP exports out of the authoritative design source.
- Include physical E-stop, bumper switches, and ToF proximity sensors before any autonomous movement.
- Build ROS-compatible interfaces even if early prototypes start as Python services.
- Make local dashboard and manual teleop part of MVP, not an afterthought.
- Treat autonomous roaming as opt-in and bounded by mapped no-go zones.
