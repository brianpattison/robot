# robot-dashboard bench baseline

The localhost supervision dashboard from
[`docs/mvp-architecture.md`](../../docs/mvp-architecture.md): a stdlib-only
HTTP + Server-Sent-Events client of the local `robotd` Unix socket. It shows
robot state, decoded safety flags, per-zone NC bumper loops, a live blackbox
tail, and offers hold-to-drive manual controls, head pan/tilt, per-zone bumper
clears, and a software stop.

It is a supervision tool, not a safety device. It cannot clear an E-stop
latch, bypass the open-bumper zero-motion rule (D036), or exceed the firmware
clamps; it talks to `robotd` like any other client, every state-affecting
command it sends is blackbox-logged with source `dashboard`, and the firmware
envelope applies to all of it. The page says so on screen.

Run without hardware:

```bash
python3 -m venv /tmp/rover-bean-dash
/tmp/rover-bean-dash/bin/pip install -e software/robotd -e software/dashboard
/tmp/rover-bean-dash/bin/robotd --simulate \
  --socket /tmp/robotd.sock --blackbox /tmp/robotd-blackbox.jsonl &
/tmp/rover-bean-dash/bin/robot-dashboard \
  --socket /tmp/robotd.sock --blackbox /tmp/robotd-blackbox.jsonl
# open http://127.0.0.1:8072/
```

Design constraints:

- **Local-only by default.** It binds `127.0.0.1`; a non-loopback `--host`
  is refused unless `--expose-lan` is passed deliberately. Remote access is
  the Cloudflare Tunnel's job (D033), not an open port.
- **A web page cannot drive the robot.** On the loopback bind, requests with
  a non-local `Host` header are rejected (DNS rebinding), and POST requires
  `Content-Type: application/json`, which a cross-origin page cannot send
  without a CORS preflight this server never grants. This blocks other
  origins in the operator's browser, not the operator or the agent.
- **No dependencies, no network assets.** Pure Python standard library and one
  inline HTML page, so it renders with the internet down — the same failure
  mode the local stop path is designed for.
- **Single-setpoint honesty.** Holding a drive control refreshes the setpoint
  at 10 Hz from the browser; releasing it sends `stop`. If the page dies
  mid-hold, the Pico's independent 250 ms motion lease zeros motion without
  anyone's cooperation.
- **UI clamps mirror the firmware caps** (350 mm/s, 1500 mrad/s, pan
  +/-60 deg, tilt +/-20 deg) only so the page never claims to request more
  than firmware will apply. The firmware clamp remains the authority.
- **Truthful placeholders.** Camera preview, perception facts, the agent
  panel, and policy settings render as explicit "not built yet" cards until
  those layers exist.

`software/systemd/robot-dashboard.service` is the reference unit (localhost
bind, read-only blackbox access). The versioned Pi appliance contract does not
install or enable it yet; on first install even `robotd` itself ships stopped
and disabled.
