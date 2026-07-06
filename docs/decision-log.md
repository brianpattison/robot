# Decision Log

This file captures settled project decisions so future planning, CAD, and software work do not need to re-argue the basics every time. Future us has enough screws on the floor already.

## D001: Build A Wheeled MVP, Not A Legged Robot

Status: accepted

The MVP body will be a compact wheeled indoor companion, not a legged robot. Dog-like behavior should come from motion language, voice, attention, following, looking toward the user, and idle presence.

Rationale:

- Wheeled locomotion is safer, cheaper, and much easier to make reliable indoors.
- The first win is a responsive physical companion, not complex biomechanics.
- Legged locomotion would consume the budget and schedule before we prove the interaction loop.

## D002: Use The Existing Raspberry Pi 5 8GB For MVP

Status: accepted

The existing Raspberry Pi 5 8GB is the MVP compute baseline.

Rationale:

- It is already owned.
- MVP responsiveness depends more on deterministic local reflexes, clean power, audio, sensors, and safety than on larger RAM.
- 16GB can remain an optional future upgrade if local models or memory-heavy workloads demand it.

## D003: Defer AI HAT+ 2

Status: accepted

AI HAT+ 2 is not required for MVP. The mechanical and power design should reserve room for a future AI HAT+ 2, but the first body should not depend on it.

Rationale:

- MVP safety, movement, voice, dashboard, and basic perception can work without a local AI accelerator.
- ChatGPT/Codex can remain the primary personality through a networked service.
- The first hardware budget should prioritize motors, power, sensors, E-stop, bumpers, and chassis iteration.
- AI HAT+ 2 remains useful later for local LLM/VLM experiments and offline fallback.

## D004: Safety And Reflexes Are Not LLM-Driven

Status: accepted

Safety-critical behavior must be deterministic and independent of LLM output.

Examples:

- E-stop cuts motor power.
- Bumper hit stops motors immediately.
- Watchdog timeout disables movement.
- Low battery forces stop or return-home behavior.
- `stop`, `wait`, and `mute` must have a fast local path.

Rationale:

- LLMs can choose high-level intentions, but they must never be trusted with raw motor authority.
- Physical safety needs boring, testable behavior.

## D005: Codex Is The Primary Agentic Identity

Status: accepted

The robot may use multiple models and services internally, but Codex/ChatGPT is the primary conversational and agentic identity.

Rationale:

- The body is intended to feel like Codex is physically present.
- Wake word, STT, TTS, object detection, and local classifiers are subsystems, not alternate personalities.
- This separation keeps the user experience coherent while allowing practical model choices.

## D006: Use Parametric CAD Source

Status: accepted

The printable body should be designed from parametric source files.

Defaults:

- OpenSCAD for first-pass blocky printable parts.
- `build123d` or CadQuery for Python CAD, richer assemblies, fillets, chamfers, STEP exports, and complex shells.

Rationale:

- Parametric CAD makes dimensions, mounts, clearances, and fit fixes easy to update.
- Source CAD is reviewable and reproducible.
- Generated STLs and STEP files should be treated as exports.

## D007: Build Voice And Bench Brain Before Autonomous Motion

Status: accepted

The first implementation slice should be a stationary bench brain before a roaming chassis.

Rationale:

- Camera, mic, speaker, wake word, TTS/STT, dashboard, and command routing can be tested safely on the desk.
- Voice and status behavior define the companion experience.
- Movement should wait until safety hardware and manual control are working.

## D008: Start MVP Storage With microSD

Status: accepted

For MVP storage, start with a reliable microSD card. Do not choose an official Raspberry Pi M.2/NVMe HAT as the default storage path if we want to preserve a clean future AI HAT+ 2 upgrade.

Rationale:

- Raspberry Pi documents both AI HAT+ / AI HAT+ 2 and M.2 HAT+ as using the Raspberry Pi 5 PCIe connector.
- The official AI HAT+ 2 and official M.2/NVMe HAT are therefore competing for the same Pi 5 PCIe interface.
- Third-party PCIe switch/splitter boards may exist, but they add mechanical, power, driver, thermal, and stability risk and should not be an MVP assumption.
- A microSD card keeps the PCIe connector available for a future AI HAT+ 2 and avoids extra moving-body cable strain in the first build.
- USB SSD or compact USB flash storage remains an easy later upgrade for logs, captures, maps, models, or boot storage if microSD becomes limiting.
