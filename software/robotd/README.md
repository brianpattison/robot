# robotd bench baseline

`robotd` is the observable, localhost-only body interface described in
[`docs/agentic-control-plan.md`](../../docs/agentic-control-plan.md). It is not
a permission gate. The Pico firmware remains the physical safety envelope.

Run without hardware:

```bash
python3 -m venv /tmp/rover-bean-robotd
/tmp/rover-bean-robotd/bin/pip install -e software/robotd
/tmp/rover-bean-robotd/bin/robotd --simulate \
  --socket /tmp/robotd.sock --blackbox /tmp/robotd-blackbox.jsonl
/tmp/rover-bean-robotd/bin/robotctl --socket /tmp/robotd.sock status
```

`drive` sends one setpoint. `robotd` does not refresh it on behalf of a silent
client; the Pico's independent 250 ms lease zeros motion. The daemon does send
the 20 Hz host heartbeat while its event loop is healthy. Every state-affecting
command (`drive`, `head`, `stop`, `clear_bumper`) and every firmware status
change is appended to the Pi-local blackbox and, when configured, a second
off-host/mounted path. The blackbox is a state-change journal, not a ticker:
read-only `status` queries are answered without a write, and the firmware
uptime counter alone does not count as a status change, so an idle bench stays
quiet instead of grinding the SD card at 10 Hz.

The local log is authoritative. The mirror parent must be a real mount point;
`robotd` will not silently write into the bare directory beneath a missing
mount. A disconnect emits one local `audit_mirror_gap` record, and the first
successful write after remount emits `audit_mirror_recovered` locally and
remotely. Any unexpected heartbeat or serial-loop task failure stops the daemon
so the firmware watchdog expires instead of leaving a cheerful zombie service.

## Head trim

Servo horns land on the nearest spline tooth, so a freshly assembled head can
sit a few degrees off center with no servo tester in sight (D041).
`--head-trim-pan-cdeg` and `--head-trim-tilt-cdeg` add a fixed offset
(centidegrees, clamped to ±800 — about one 15° tooth on the D85MG's 24T
spline) to every HEAD command before it is framed. The trim is a convenience,
not a wider envelope: the firmware clamps apply to the trimmed value exactly
as they would to an untrimmed one. Every head command's blackbox record keeps
both the raw request and the trimmed values actually sent, and `status`
reports the active trim as `head_trim`.

## robot-hello

`robot-hello` is the bench wake-up milestone: the robot says hello with no
battery and no drive motion. Against an already-running robotd it centers the
head, pans slowly left and right, tilts up briefly, and narrates what it is
doing in plain language. It moves only the head and only through robotd, so
every command crosses the same firmware envelope as any other client and
lands in the blackbox with source `hello`. It never starts robotd, and it
exits nonzero with a plain explanation if robotd is unreachable or the
firmware link is down. It works against the simulator today; on a real robot
it requires the same started-by-you robotd and crosses no safety gate.

```bash
/tmp/rover-bean-robotd/bin/robot-hello --socket /tmp/robotd.sock
```

Pass `--sound path/to/greeting.wav` to also play a WAV through `afplay`
(macOS) or `aplay` (Linux) if one exists. No audio ships with the repo; the
default is silent.

## Installing on the Pi

Install on Raspberry Pi OS with `sudo software/install.sh`. The service file
expects the off-host audit mirror at `/mnt/robot-audit`; do not call the audit
path complete until the commissioning check proves unplug/reconnect behavior
and readback from another machine.
