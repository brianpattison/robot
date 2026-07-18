# Executable commissioning and evidence bundles

The 27-step [`plan-v2.json`](plan-v2.json) is the physical release procedure.
[`commission.py`](commission.py) captures each first article in a private,
content-addressed bundle and can seal a complete bundle with an OpenSSH
signature. It does not include or invent a physical pass.

Start with the full [first-article evidence guide](../docs/first-article-evidence.md).
The short command map is:

```bash
python3 commissioning/fixture.py --check
python3 commissioning/commission.py list
python3 commissioning/commission.py show C001
python3 commissioning/commission.py --bundle output/commissioning/RB-001 init \
  --robot-serial RB-001 --operator Brian \
  --source-ref refs/tags/REPLACE_WITH_RELEASE_TAG
python3 commissioning/commission.py --bundle output/commissioning/RB-001 record C001 \
  --result pass --operator Brian \
  --measure battery_serial=... --measure harness_revision=... \
  --attach first_article_identity_photo=/absolute/path/labels.jpg
python3 commissioning/commission.py --bundle output/commissioning/RB-001 report
```

`show` prints a step's exact measurements, evidence roles, and predicates.
`record` imports each file into `objects/sha256/`; paths are never kept as
evidence. A later event supersedes an earlier event for the same step, so normal
FAIL -> repair -> PASS work remains visible.

Final sealing and independent verification require an out-of-repository trust
policy:

```bash
python3 commissioning/commission.py --bundle output/commissioning/RB-001 seal \
  --signing-key /secure/path/commissioning_ed25519 \
  --signer brian@example.com
python3 commissioning/commission.py --bundle /received/RB-001 \
  --source-repo /clean/robot-clone verify \
  --allowed-signers /secure/policy/allowed_signers \
  --signer brian@example.com --robot-serial RB-001
```

The final command means only that the expected signer attested to the exact
bundle bytes for the expected robot and committed source. It does not prove a
measurement was honestly taken, and it never replaces the harness or powered
release gates. A cute robot with borrowed paperwork remains a cute robot with
forged paperwork—now with a much easier audit trail.
