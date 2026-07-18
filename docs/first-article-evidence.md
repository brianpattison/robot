# First-article evidence capture and independent verification

## What this system proves

A passing verification proves one narrow, useful statement:

> The expected signer attested to these exact evidence bytes for the expected
> robot, commissioning plan, and source revision, and the latest record for
> every required step satisfies the plan's mechanical predicates.

It does **not** prove that a measurement is physically true, that an operator
or capture computer was honest, or that powered motion is safe. Operators and
timestamps are self-asserted until the bundle is signed. Even after signing,
the signature provides accountability, not a tiny cryptographic safety vest.
The harness release gate, physical review, and powered-motion decision remain
separate.

The threat model covers accidental record loss, post-signature byte changes,
artifact substitution, signature transplant, bundle-path tricks, and an
untrusted copy of a signing key placed inside a bundle. It cannot prevent a
dishonest operator from staging a photograph or typing a fabricated reading
before signing.

No first-article bundle is committed to this repository. The default gate is
therefore deliberately red.

## Platform and privacy requirements

- Use Linux or macOS with Python 3.11/3.12, Git, and OpenSSH 8.8 or newer.
  Windows is not supported by evidence schema v2.
- Work from a clean checkout at an immutable `refs/tags/...` release tag. The
  tool records the origin URL and confirms that `HEAD` is reachable from the
  tag. This is provenance context, not proof that a local Git ref is authentic;
  the final signer attests to the selection.
- Keep the bundle on one local filesystem and allow only one capture host to
  edit it. Mutations use an advisory file lock, durable object writes, and an
  atomic evidence-file replacement.
- Treat the bundle as private operational data. It can contain robot/battery
  serials, operator names, photographs, shell output, and household details.
  It is created mode `0700` and gitignored. Store, transmit, retain, and destroy
  it under the same policy as other sensitive engineering records.
- Review files before import. Photos may contain EXIF/GPS/device metadata, and
  automated stdout/stderr may contain usernames, paths, nonces, or secrets.
  The runner never serializes the process environment and does not claim to
  strip metadata.

Each imported attachment must be a regular file no larger than 512 MiB. The
importer refuses symlinks, directories, devices, and FIFOs, opens with
no-follow semantics, re-checks the opened descriptor, and hashes/copies from
that same descriptor. If the file changes during the copy, the event is not
recorded.

## 1. Establish signer trust outside the bundle

Use a dedicated passphrase-protected Ed25519 key or a supported hardware-backed
OpenSSH signing key. Never put the private key, `allowed_signers`, or revocation
policy inside the evidence bundle.

One software-key example is:

```bash
ssh-keygen -t ed25519 -a 64 -f /secure/path/commissioning_ed25519
```

The independently administered `allowed_signers` file follows the format in
`man ssh-keygen`. Give the signer a stable principal and, where policy calls
for it, `valid-after` / `valid-before` constraints. Example shape only:

```text
brian@example.com namespaces="rover-bean-commissioning",valid-after="20260701Z",valid-before="20270701Z" ssh-ed25519 AAAA...
```

The verifier supplies both that file and the expected principal out of band.
The bundle's `signer_claim` is signed for audit readability but is never a
trust root. Maintain a separate OpenSSH KRL or revoked-key list when keys are
compromised.

The verifier checks key validity at the signed manifest time. That preserves
historical verification through planned key rotation, but it does not erase a
later compromise: the verifier must still apply the current revocation policy.
If a key is lost after sealing, existing bundles remain verifiable. If it is
lost before sealing, onboard a replacement key and seal with the new trusted
principal.

## 2. Create the bundle

From the clean release-tag checkout:

```bash
python3 commissioning/commission.py \
  --bundle output/commissioning/RB-001 \
  init --robot-serial RB-001 --operator Brian \
  --source-ref refs/tags/REPLACE_WITH_RELEASE_TAG
```

Replace the placeholder with the immutable release tag that contains evidence
schema v2. The historical `v2.0.0-prototype.1` tag predates this workflow and
must not be moved or reused.

`init` records the bundle/robot identity, exact commit, origin, resolved release
tag, plan blob hash, and hashes derived from committed bytes for:

- the builder's book;
- the body and coupon 3MF projects;
- the RB-FIXTURE-V1 manifest;
- the complete Pico safety, `robotd`, and Pi-appliance source trees.

The three source-tree hashes are SHA-256 over a sorted byte sequence of
`repo/path NUL blob-sha256 LF`, where each blob hash is SHA-256 of the Git blob
bytes. They identify exact source trees; they are not deployed-binary proof.
C008 separately requires the exact flashed UF2, and C026 requires both the
independent collector receipt and the Pi live-attestation export.

## 3. Capture observations

Inspect a step before performing it:

```bash
python3 commissioning/commission.py \
  --bundle output/commissioning/RB-001 show C005
```

Record measurements and the declared artifact roles. `*_uri` values and
`*_sha256` values linked to artifacts are generated by the importer; never type
them by hand.

```bash
python3 commissioning/commission.py \
  --bundle output/commissioning/RB-001 record C005 \
  --result pass --operator Brian \
  --measure pico_usb_to_pi=false \
  --measure pico_swd_to_pi=false \
  --measure debug_uart_device=/dev/ttyAMA10 \
  --measure pico_uart_device=/dev/rover-pico \
  --measure dual_uart_contention=false \
  --attach separation_photo=/absolute/path/separation.jpg
```

For C001, enter only the physical identity fields; the repository fields are
derived from the source commit:

```bash
python3 commissioning/commission.py \
  --bundle output/commissioning/RB-001 record C001 \
  --result pass --operator Brian \
  --measure battery_serial=BAT-001 \
  --measure harness_revision=v2-H1-RB001 \
  --attach first_article_identity_photo=/absolute/path/labels.jpg
```

For a safe command declared in the plan, capture full bounded stdout/stderr as
the required object:

```bash
python3 commissioning/commission.py \
  --bundle output/commissioning/RB-001 run-automated C007 \
  --operator Brian
```

Record actual failures as failures. Never delete them:

```bash
python3 commissioning/commission.py \
  --bundle output/commissioning/RB-001 record C018 \
  --result fail --operator Brian \
  --note "Backfeed exceeded limit; inspect USB power gate"
```

After repair, record a new event for C018. The latest event controls closure,
while the earlier failure remains in the signed history. `list` reports the
number of superseded events.

Generate a readable status report at any time:

```bash
python3 commissioning/commission.py \
  --bundle output/commissioning/RB-001 report \
  --output output/commissioning/RB-001-report.md
```

The report separates record completeness, bundle-byte integrity, and signer
trust. It lists every missing step, measurement, artifact role, integrity
problem, or trust failure.

## 4. Recover an interrupted unsealed capture

Every evidence mutation locks the bundle, writes imported object bytes and
`fsync`s them before recording a reference, then replaces canonical
`evidence.json` atomically and `fsync`s the containing directory. This protects
against normal crashes within the guarantees of the local filesystem; it is
not a claim about broken storage hardware.

After an interrupted import or seal, inspect the bundle, preserve a backup,
then remove only verified unreferenced objects, known temporary files, or an
invalid partial seal:

```bash
python3 commissioning/commission.py \
  --bundle output/commissioning/RB-001 cleanup
```

`cleanup` refuses to remove a cryptographically valid seal. Referenced objects
are never deleted. If `evidence.json` itself is unavailable, recover the bundle
from backup; do not reconstruct history by hand.

## 5. Seal only a complete bundle

Sealing requires every latest step event to be `pass`, every required scalar
and artifact to exist, every acceptance rule to hold, all committed provenance
to recompute, the complete event chain to validate, and every object to match
its lowercase SHA-256 name and recorded size.

```bash
python3 commissioning/commission.py \
  --bundle output/commissioning/RB-001 seal \
  --signing-key /secure/path/commissioning_ed25519 \
  --signer brian@example.com
```

The canonical signed manifest binds schema and bundle IDs, robot serial, source
commit/tag, plan hash, evidence-file hash, event count, chain head, supersession
link, signature namespace/time, signer claim, and the exact object set. A
manifest without a valid signature is BLOCKED. After sealing, capture commands
refuse mutation.

Canonical event and manifest JSON uses UTF-8, lexicographically sorted object
keys, JSON separators `,` and `:`, unescaped Unicode, finite JSON scalar
measurements, and no trailing newline. The plan declares every measurement as
`string`, `boolean`, `integer`, or `number`; `show` displays that type. Boolean
input must be exactly `true` or `false`, and numeric input must use canonical
JSON spelling, so Python cannot quietly treat integer `0` as boolean `false`.
Event sequence begins at 1; the genesis previous hash is 64 ASCII zeroes. Each
event hash covers every canonical event field except `event_sha256`, including
its sequence and previous hash.

## 6. Verify independently

Send the whole bundle, but send the trusted policy and expected identity by a
separate channel. On the independent verifier's clean source clone:

```bash
python3 commissioning/commission.py \
  --bundle /received/RB-001 \
  --source-repo /clean/robot-clone \
  verify \
  --allowed-signers /secure/policy/allowed_signers \
  --revocation-file /secure/policy/revoked.krl \
  --signer brian@example.com \
  --robot-serial RB-001
```

Verification rejects changed or missing objects, extra/unlisted files,
symlinks, hard-linked objects, malformed names, a changed source tag, plan or
source drift, event-chain edits, a signature from another bundle, a bundled
trust root, a signer mismatch, a robot mismatch, an invalid key-validity time,
and current revocations. The namespace is fixed to
`rover-bean-commissioning` for signing and verification.

Archive the exact sealed directory without normalizing or rewriting its files.
Re-run the same command after transfer and whenever retention storage is
audited.

## 7. Correct a sealed bundle

Never edit a sealed record. First independently verify the old bundle, then
start a new one with an auditable supersession link:

```bash
python3 commissioning/commission.py \
  --bundle output/commissioning/RB-001-correction-1 \
  --source-repo /clean/robot-clone \
  init --robot-serial RB-001 --operator Brian \
  --source-ref refs/tags/REPLACE_WITH_RELEASE_TAG \
  --supersedes-bundle /archive/RB-001 \
  --supersedes-allowed-signers /secure/policy/allowed_signers \
  --supersedes-signer brian@example.com
```

The new evidence records the prior bundle ID and manifest SHA-256 only after
the prior bundle independently verifies. Re-record all required steps, seal the
new bundle, and retain both. A correction is a new attestation, not an eraser.

## Migration from schema v1

Schema-v1 evidence was mutable, did not capture artifact bytes, and had no
external signature. It cannot be upgraded without overstating provenance.
`commission.py` therefore rejects it with migration guidance. Create a v2
bundle and repeat each observation against the exact first article; keep the v1
file only as clearly labeled historical context.
