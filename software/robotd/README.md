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
the 20 Hz host heartbeat while its event loop is healthy. Every command and
firmware status change is appended to the Pi-local blackbox and, when
configured, a second off-host/mounted path.

The local log is authoritative. The mirror parent must be a real mount point;
`robotd` will not silently write into the bare directory beneath a missing
mount. A disconnect emits one local `audit_mirror_gap` record, and the first
successful write after remount emits `audit_mirror_recovered` locally and
remotely. Any unexpected heartbeat or serial-loop task failure stops the daemon
so the firmware watchdog expires instead of leaving a cheerful zombie service.

Install on Raspberry Pi OS with `sudo software/install.sh`. The service file
expects the off-host audit mirror at `/mnt/robot-audit`; do not call the audit
path complete until the commissioning check proves unplug/reconnect behavior
and readback from another machine.
