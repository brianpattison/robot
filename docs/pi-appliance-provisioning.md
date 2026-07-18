# Raspberry Pi 5 appliance provisioning

`software/install.sh` turns a fresh 64-bit Raspberry Pi OS Bookworm image into
the versioned `RB-PI-APPLIANCE-V1` bench appliance. It installs `robotd`,
key-only SSH, an outbound-only Cloudflare Tunnel, tlog session capture, an
availability backup, and a stable RP1 UART name for the Pico.

This is a provisioning baseline, not powered-motion authorization. Keep the
motor branch physically isolated. The Pi has broad agent authority by design;
the independent Pico firmware and physical controls remain the safety boundary.

## What the installer deliberately does not do

- It does not flash, configure, or connect the Pico USB/SWD service corridors.
- It does not edit `/boot/firmware/cmdline.txt` or replace the Pi 5 debug UART10
  console.
- It does not start or stop `robotd`. A first install leaves it disabled and
  stopped; a rerun preserves both pre-existing state bits.
- It does not create Cloudflare dashboard resources or put Access service
  tokens on the Pi.
- It does not call the read-write `/mnt/robot-audit` copy tamper-proof. A
  separately administered append-only collector and independent readback are a
  commissioning requirement.
- It does not reboot. The operator keeps the current session open until a fresh
  SSH login succeeds, then reboots and proves both UARTs physically.

## Before touching the Pi

1. Install current 64-bit Raspberry Pi OS Lite Bookworm on the Pi 5. Keep its
   Pi 5 debug serial console available on UART10 as the physical break-glass
   path. HDMI plus keyboard or SD-card recovery is the second escape hatch.
2. In Cloudflare Zero Trust, create the named Tunnel and route one hostname to
   `ssh://localhost:22`.
3. Create an Access application for that hostname. Add the intended SSO policy
   and, if unattended clients need it, a narrowly scoped Service Auth policy.
   Do this before passing `--access-ready`; the flag is an operator attestation,
   not dashboard automation wearing a fake moustache.
4. Install `cloudflared` on each remote SSH client. Access service-token ID and
   secret values live on those clients only. The Tunnel run token is a different
   credential and is the only Cloudflare secret installed on the Pi.

Prepare three root-readable input files outside the repository. Do not commit
them:

```bash
umask 077
ssh-keygen -t ed25519 -f rover-bean-agent -C rover-bean-agent
cp rover-bean-agent.pub /secure/path/agent.pub

# On a Debian-family trusted workstation: apt install whois
mkpasswd -m yescrypt > /secure/path/console-password.hash

# Copy the named Tunnel's run token as one opaque line.
editor /secure/path/rover-bean-tunnel.token
```

The public key must be one option-free Ed25519 line. The console file must be
one `$y$` yescrypt hash, never plaintext. The tunnel token must be one opaque
line of at least 50 characters. The installer validates all three and never
prints their contents; the console hash is applied to shadow and not copied.

## Install

From the repository checkout on the Pi:

```bash
sudo software/install.sh \
  --ssh-public-key-file /secure/path/agent.pub \
  --tunnel-token-file /secure/path/rover-bean-tunnel.token \
  --console-password-hash-file /secure/path/console-password.hash \
  --access-ready
```

The script refuses non-Pi-5, non-aarch64, and non-Bookworm hosts. It uses
Cloudflare's signed APT repository, requires `cloudflared` 2025.4.0 or newer,
validates sudoers with `visudo`, validates the complete effective sshd config,
and rolls back its sshd drop-in if parsing fails. Generated files come from the
closed-world `software/appliance/appliance-v1.json` contract.

The resident `agent` account receives full passwordless sudo. That is the D030
control direction, not a safety control. Password and interactive SSH auth are
off; SSH accepts the installed public key only. The console password remains
usable locally on UART10.

## Do not close the first session

From a second machine, configure ProxyCommand mode:

```sshconfig
Host rover-bean
    HostName rover.example.com
    User agent
    IdentityFile ~/.ssh/rover-bean-agent
    IdentitiesOnly yes
    ProxyCommand /usr/local/bin/cloudflared access ssh --hostname %h
```

For a Service Auth policy, provide `TUNNEL_SERVICE_TOKEN_ID` and
`TUNNEL_SERVICE_TOKEN_SECRET` in the remote client's protected environment.
They never belong in `~agent`, systemd, the tunnel-token file, or this repo.

Open a fresh connection and attest the actual authenticated public key:

```bash
ssh rover-bean
python3 /opt/rover-bean/appliance/appliance.py attest-ssh
```

`ExposeAuthInfo=yes` supplies `SSH_USER_AUTH`; the attestation records the
authenticated key fingerprint and connection tuple, not the key or any secret.
Find that connection in the Cloudflare Access authentication logs, copy its
event identifier, and bind the server-side record to it:

```bash
python3 /opt/rover-bean/appliance/appliance.py attest-access \
  --hostname rover.example.com --edge-log-id EDGE_EVENT_ID
```

Only after both attestations succeed should the original session be closed.

## Reboot and prove the two UARTs

Reboot once. The managed boot block enables RP1 UART0 on GPIO14/15 with the
official `uart0-pi5` overlay. The udev rule pins its device-tree node
`/rp1/serial@30000` to `/dev/rover-pico` by resolving the tty's actual
`of_node` symlink; it does not trust a floating ttyAMA number. The Pi 5 debug
UART10 console remains separate.

1. On the physical debug UART10 console, log in as `agent`, type and receive a
   test line, then run:

   ```bash
   python3 /opt/rover-bean/appliance/appliance.py attest-console
   ```

2. With Pico USB and SWD still physically disconnected from the Pi, inspect the
   GPIO UART identity:

   ```bash
   readlink -f /dev/serial0
   readlink -f /dev/rover-pico
   readlink -f /sys/class/tty/ttyAMA0/device/of_node
   ```

   The results must be `/dev/ttyAMA10`, `/dev/ttyAMA0`, and a device-tree path
   ending in `/rp1/serial@30000`, respectively. No getty may be active on
   ttyAMA0. The later first-article record must also prove the UART10 console
   and GPIO UART can operate together without contention.

3. Run the live verifier:

   ```bash
   sudo python3 /opt/rover-bean/appliance/appliance.py verify --live --json
   ```

   It stays red until SSH, console, and external-collector attestations all
   exist. That red result is intentional evidence hygiene, not a sad robot.

`robotd.service` uses `/dev/rover-pico` and refuses to start if the character
device is absent. Enable and start it only in the appropriate commissioning
step, with the motor branch physically isolated.

## Session capture and audit boundary

The `agent` login shell invokes tlog for both interactive shells and SSH
`command`/`-c` sessions. Record detection is namespaced by the current kernel
boot ID and audit session, so reused session numbers after a reboot do not hide
a recorder gap. A nonzero command result is propagated without replay. If tlog
emits no record, the wrapper raises an `authpriv.alert` and appends a
`capture_failure` event for off-host monitoring. Interactive login fails open
to Bash; an SSH `-c` command preserves the recorder's status and is never
executed a second time.

`rover-audit-backup.service` tails session and audit-event files by inode and
byte offset. It records mount gaps, recovery, and source truncation. It writes
to `/mnt/robot-audit` only when that path is a real mount. This copy improves
availability but is writable by a root-capable Pi and therefore cannot prove
integrity.

Commissioning C026 must use a separately administered collector. From another
machine, read back a nonce and records, then prove that the Pi credential cannot
read, delete, rewrite, or alter prior objects. Record those denials and the
independent administrator's readback. Until then, `collector.json` must remain
absent and live verification must remain blocked.

## Hardware-free checks

Run after any provisioning change:

```bash
python3 software/appliance/appliance.py
python3 commissioning/run_host_tests.py
python3 software/appliance/appliance.py --check
bash -n software/install.sh
```

The first command regenerates only the tracked, non-secret templates. Host tests
exercise idempotent staging, modes, key/token/hash rejection, UART mapping,
tlog fallback, audit gap/recovery/truncation, and closed-world drift. They do not
claim that a real Pi, Tunnel, serial console, or external collector passed.
