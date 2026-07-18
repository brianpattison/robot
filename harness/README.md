# v2 harness traveler

[`harness-v2.json`](harness-v2.json) is the machine-readable first-article cut
and label schedule. It supplies stable wire IDs, routes, nominal cut lengths,
service loops, wire classes/gauges/colors, and both-end termination intent.

Generate the builder traveler:

```bash
python3 harness/generate_harness_docs.py
```

The normal command validates the engineering schedule and writes CSV/label
files under `output/harness/`. The production gate is intentionally red:

```bash
python3 harness/generate_harness_docs.py --release
```

It cannot pass until the first dry harness records measured cut lengths,
continuity and pull tests, every exact housing/contact, released branch fuse
values, a selective-fault test, and a thermal soak. Nominal CAD-derived lengths
are construction starting points, not a claim about an unbuilt robot.
