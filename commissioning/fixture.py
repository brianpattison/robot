#!/usr/bin/env python3
'''Validate RB-FIXTURE-V1 and generate its guide, labels, and CAD data.'''

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / 'commissioning' / 'fixture-v1.json'
GUIDE_PATH = ROOT / 'docs' / 'commissioning-fixture-v1.md'
LABEL_PATH = ROOT / 'commissioning' / 'generated' / 'fixture-v1-labels.svg'
SCAD_DATA_PATH = ROOT / 'cad' / 'openscad' / 'generated' / 'commissioning_fixture_v1_data.scad'

EXPECTED_COMPONENT_IDS = {
    'PICO', 'DEBUG_PROBE', 'BREADBOARD',
    *(f'BUMP_{index}' for index in range(1, 7)),
    'ESTOP_SENSE_SIM', 'RESET_BUTTON', 'CHARGER_SIM', 'ESTOP', 'DRIVER',
    'RELAY', 'LAMP', 'BENCH_12V', 'WAGO', 'WIRE', 'UART_CABLE', 'PLATE',
    'FIXTURE_FASTENERS',
}

EXPECTED_COMPONENT_PARTS = {
    'PICO': ('SC1632', 1),
    'DEBUG_PROBE': ('SC0889', 1),
    'BREADBOARD': ('BusBoard BB830 or Adafruit 239', 1),
    **{f'BUMP_{index}': ('D2HW-C202MR', 1) for index in range(1, 7)},
    'ESTOP_SENSE_SIM': ('fixture-only switch or jumper', 1),
    'RESET_BUTTON': ('fixture-only switch or jumper', 1),
    'CHARGER_SIM': ('fixture-only switch or jumper', 1),
    'ESTOP': ('XW1E-BV402M-R', 1),
    'DRIVER': ('5648', 1),
    'RELAY': ('CB1A-R-M-12V', 1),
    'LAMP': ('DX06WG012B', 1),
    'BENCH_12V': ('user bench supply', 1),
    'WAGO': ('221-412/K007-0000', 10),
    'WIRE': ('Adafruit 1311', 1),
    'UART_CABLE': ('Adafruit 3893', 1),
    'PLATE': ('cad/openscad/commissioning_fixture_v1.scad', 1),
    'FIXTURE_FASTENERS': ('M3 x 12 SHCS plus M3 nyloc nuts', 12),
}

EXPECTED_NETS = {
    'GND_COMMON': (
        'ground',
        {
            'PICO.GND', 'DEBUG_PROBE.GND', 'DRIVER.GND', 'BENCH_12V.NEG',
            *(f'BUMP_{index}.COM' for index in range(1, 7)),
            'ESTOP_SENSE_SIM.COM', 'RESET_BUTTON.COM', 'CHARGER_SIM.COM',
            'LAMP.NEG',
        },
    ),
    'UART_TX': ('PICO_LOGIC', {'PICO.GP0', 'DEBUG_PROBE.RX'}),
    'UART_RX': ('PICO_LOGIC', {'PICO.GP1', 'DEBUG_PROBE.TX'}),
    **{
        f'BUMP_{index}_NC': (
            'PICO_LOGIC', {f'PICO.GP{index + 1}', f'BUMP_{index}.NC'}
        )
        for index in range(1, 7)
    },
    'ESTOP_SENSE_SIM': ('PICO_LOGIC', {'PICO.GP8', 'ESTOP_SENSE_SIM.SW'}),
    'RESET_SIM': ('PICO_LOGIC', {'PICO.GP9', 'RESET_BUTTON.SW'}),
    'CHARGER_SIM': ('PICO_LOGIC', {'PICO.GP10', 'CHARGER_SIM.SW'}),
    'RELAY_LOGIC': ('PICO_LOGIC', {'PICO.GP11', 'DRIVER.IN'}),
    '12V_POS': ('BENCH_12V', {'BENCH_12V.POS', 'ESTOP.NC1_IN', 'RELAY.COM'}),
    'ESTOP_SERIES': ('BENCH_12V', {'ESTOP.NC1_OUT', 'ESTOP.NC2_IN'}),
    'DRIVER_VPLUS': (
        'BENCH_12V', {'ESTOP.NC2_OUT', 'DRIVER.VPLUS', 'RELAY.COIL_HIGH'}
    ),
    'DRIVER_OUT': ('BENCH_12V_SWITCHED', {'DRIVER.OUT', 'RELAY.COIL_LOW'}),
    'RELAY_NO_LAMP': ('BENCH_12V_SWITCHED', {'RELAY.NO', 'LAMP.POS'}),
}

EXPECTED_FIRMWARE_PINS = {
    'uart_tx': 0,
    'uart_rx': 1,
    **{f'bumper_{index}': index + 1 for index in range(1, 7)},
    'estop_sense': 8,
    'reset': 9,
    'charger_sense': 10,
    'relay_enable': 11,
}


class FixtureValidationError(ValueError):
    '''The fixture stopped being the reviewed closed-world circuit.'''


def load_manifest(path: Path = MANIFEST_PATH) -> dict:
    return json.loads(path.read_text(encoding='utf-8'))


def parse_firmware_pins(source: str) -> dict[str, int]:
    macros = {
        'UART_TX': 'uart_tx',
        'UART_RX': 'uart_rx',
        'RESET': 'reset',
        'ESTOP_SENSE': 'estop_sense',
        'CHARGER_SENSE': 'charger_sense',
        'RELAY_ENABLE': 'relay_enable',
    }
    pins: dict[str, int] = {}
    for macro, name in macros.items():
        match = re.search(rf'^#define RB_{macro}_PIN\s+(\d+)\s*$', source, re.MULTILINE)
        if not match:
            raise FixtureValidationError(f'firmware pin macro RB_{macro}_PIN is missing')
        pins[name] = int(match.group(1))
    match = re.search(
        r'static const uint8_t bumper_pins\[6\]\s*=\s*\{([^}]+)\};', source
    )
    if not match:
        raise FixtureValidationError('firmware bumper_pins[6] declaration is missing')
    bumpers = [int(value.strip()) for value in match.group(1).split(',')]
    if len(bumpers) != 6:
        raise FixtureValidationError('firmware must define exactly six bumper pins')
    for index, pin in enumerate(bumpers, start=1):
        pins[f'bumper_{index}'] = pin
    return pins


def _indexed(items: list[dict], label: str) -> dict[str, dict]:
    indexed: dict[str, dict] = {}
    for item in items:
        item_id = item.get('id')
        if not item_id or item_id in indexed:
            raise FixtureValidationError(f'duplicate or missing {label} id: {item_id!r}')
        indexed[item_id] = item
    return indexed


def validate_manifest(manifest: dict, firmware_source: str | None = None) -> None:
    if manifest.get('fixture_id') != 'RB-FIXTURE-V1':
        raise FixtureValidationError('fixture_id must remain RB-FIXTURE-V1')

    components = _indexed(manifest.get('components', []), 'component')
    actual_ids = set(components)
    if actual_ids != EXPECTED_COMPONENT_IDS:
        missing = sorted(EXPECTED_COMPONENT_IDS - actual_ids)
        extra = sorted(actual_ids - EXPECTED_COMPONENT_IDS)
        raise FixtureValidationError(
            f'closed-world components changed: missing={missing}, extra={extra}'
        )
    for component_id, (part, quantity) in EXPECTED_COMPONENT_PARTS.items():
        component = components[component_id]
        if component.get('part') != part or component.get('qty') != quantity:
            raise FixtureValidationError(
                f'closed-world component {component_id} changed part or quantity'
            )

    forbidden_text = ' '.join(manifest.get('forbidden', [])).lower()
    for required in ('battery', 'motor', 'mdds10', 'production pico'):
        if required not in forbidden_text:
            raise FixtureValidationError(f'forbidden list must retain {required!r}')

    nets = _indexed(manifest.get('nets', []), 'net')
    if set(nets) != set(EXPECTED_NETS):
        raise FixtureValidationError('closed-world net names changed')
    for net_id, (expected_domain, expected_members) in EXPECTED_NETS.items():
        net = nets[net_id]
        members = net.get('members', [])
        if len(members) != len(set(members)):
            raise FixtureValidationError(f'{net_id} repeats an endpoint')
        if net.get('domain') != expected_domain or set(members) != expected_members:
            raise FixtureValidationError(
                f'{net_id} topology changed: expected {expected_domain} '
                f'{sorted(expected_members)}, actual {net.get("domain")} {sorted(members)}'
            )
        for endpoint in members:
            component_id, separator, _ = endpoint.partition('.')
            if not separator or component_id not in components:
                raise FixtureValidationError(f'unknown endpoint {endpoint!r} in {net_id}')

    all_members = [member for net in nets.values() for member in net['members']]
    for gpio in range(12):
        endpoint = f'PICO.GP{gpio}'
        if all_members.count(endpoint) != 1:
            raise FixtureValidationError(f'{endpoint} must appear on exactly one net')
    for net in nets.values():
        if net['domain'].startswith('BENCH_12V'):
            gpio_members = [member for member in net['members'] if member.startswith('PICO.GP')]
            if gpio_members:
                raise FixtureValidationError(f'Pico GPIO entered a 12 V domain: {gpio_members}')
    ground_nets = [net_id for net_id, net in nets.items() if net['domain'] == 'ground']
    if ground_nets != ['GND_COMMON']:
        raise FixtureValidationError('fixture must have exactly one common-ground net')

    member_nets: dict[str, list[str]] = {}
    for net_id, net in nets.items():
        for member in net['members']:
            member_nets.setdefault(member, []).append(net_id)
    if member_nets.get('LAMP.POS') != ['RELAY_NO_LAMP']:
        raise FixtureValidationError('witness lamp positive bypasses relay NO')
    if member_nets.get('LAMP.NEG') != ['GND_COMMON']:
        raise FixtureValidationError('witness lamp negative bypasses common ground')
    if member_nets.get('PICO.GP11') != ['RELAY_LOGIC']:
        raise FixtureValidationError('GP11 must connect only to DRIVER.IN')

    manifest_pins = manifest.get('firmware_contract', {}).get('pins')
    if manifest_pins != EXPECTED_FIRMWARE_PINS:
        raise FixtureValidationError('fixture pin contract changed')
    if firmware_source is None:
        firmware_path = ROOT / manifest['firmware_contract']['source']
        firmware_source = firmware_path.read_text(encoding='utf-8')
    parsed_pins = parse_firmware_pins(firmware_source)
    if parsed_pins != EXPECTED_FIRMWARE_PINS:
        raise FixtureValidationError(
            f'firmware pin drift: expected={EXPECTED_FIRMWARE_PINS}, actual={parsed_pins}'
        )
    fail_stopped_fragments = (
        '#define RB_HARDWARE_RELEASE 0',
        'bool enable = false;',
        'if (RB_HARDWARE_RELEASE) {\n        enable = false;\n    }',
        'gpio_put(RB_RELAY_ENABLE_PIN, enable && rb_safety_motor_enable(&safety));',
    )
    if any(fragment not in firmware_source for fragment in fail_stopped_fragments):
        raise FixtureValidationError(
            'current Pico target is no longer the reviewed fail-stopped relay output'
        )

    printer = manifest.get('printer', {})
    bed_x, bed_y = printer.get('bed_mm', [0, 0])
    plate_x, plate_y, plate_z = printer.get('plate_mm', [0, 0, 0])
    reserve = printer.get('edge_reserve_mm', 0)
    if plate_x > bed_x - 2 * reserve or plate_y > bed_y - 2 * reserve:
        raise FixtureValidationError('fixture exceeds the P1S bed reserve')
    if [plate_x, plate_y, plate_z] != [232, 210, 4] or printer.get('supports') is not False:
        raise FixtureValidationError('plate must remain 232 x 210 x 4 mm and support-free')
    foot_depth = printer.get('feet_below_plate_mm', 0)
    estop_depth = manifest.get('layout', {}).get('estop', {}).get(
        'body_plus_terminal_depth', 0
    )
    if foot_depth < estop_depth + 5:
        raise FixtureValidationError('E-stop needs at least 5 mm foot clearance')
    if manifest.get('power_domains', [])[-1].get('current_limit_a') != 0.2:
        raise FixtureValidationError('12 V ceiling must remain 0.20 A')


def render_guide(manifest: dict) -> str:
    component_rows = []
    for component in manifest['components']:
        part = component['part']
        if component.get('source'):
            part = f'[{part}]({component["source"]})'
        kind = 'reuse' if component.get('reused') else 'fixture'
        note = f'; {component["note"]}' if component.get('note') else ''
        component_rows.append(
            f'| `{component["id"]}` | {component["type"]} | {part} | '
            f'{component["qty"]} | {kind}{note} |'
        )
    net_rows = [
        f'| `{net["id"]}` | `{net["domain"]}` | '
        + ' -> '.join(f'`{member}`' for member in net['members']) + ' |'
        for net in manifest['nets']
    ]
    pin_rows = [
        f'| `{name}` | GP{pin} |'
        for name, pin in manifest['firmware_contract']['pins'].items()
    ]
    return GUIDE_TEMPLATE.format(
        component_rows='\n'.join(component_rows),
        net_rows='\n'.join(net_rows),
        pin_rows='\n'.join(pin_rows),
    )


GUIDE_TEMPLATE = '''# RB-FIXTURE-V1 — unpowered commissioning fixture

Status: **design and hardware-free validation only; no physical pass is bundled.**

This one-plate fixture makes the first Pico safety observations repeatable without
a battery, motor, or MDDS10. It uses the six real NC bumper switches, real IDEC
E-stop, and real Panasonic relay, but the headered Pico is a dedicated fixture
part. Passing this guide never authorizes powered motion.

## Boundary

- F1–F3 are mechanical, continuity, and USB-logic work.
- F4 adds a **12.0 V, 0.20 A current-limited bench supply** only after GP11 is low.
- Current firmware deliberately keeps GP11 low. This negative-control witness
  requires the relay and lamp to stay off.
- Remove 12 V before every Pico reset, flash, unplug, or wiring change. Apply USB
  first and 12 V last. Driver reset behavior is not a safety control.

## Print one part

Export `cad/openscad/commissioning_fixture_v1.scad` as PETG. The plate is
232 × 210 × 79 mm overall. Print its component face on the P1S plate with the four
hollow feet upward; no supports. Flip after printing. The 75 mm feet leave 6.3 mm
beyond the registered 68.7 mm E-stop-plus-terminal envelope. CAD clearance is not
delivered-part fit evidence.

## Parts

Availability references were checked 2026-07-17. Reused parts return to the robot
only after inspection. M3 × 12 screws and nylocs are fixture-only and do not alter
the robot's single-M3 × 8 rule.

| ID | Item | Exact part / source | Qty | Use |
| --- | --- | --- | ---: | --- |
{component_rows}

## Assemble with no power

1. Flip the print and confirm all four feet sit without rocking.
2. Apply `commissioning/generated/fixture-v1-labels.svg` at 100% scale.
3. Stick down the breadboard. Mount the six Omrons with M3 × 12 screws and nylocs.
4. Tie the driver and relay through their slots. Fit E-stop and lamp with their nuts.
5. Put the dedicated SC1632 Pico on the breadboard. Use only the Debug Probe UART
   U cable: GP0 TX to probe RX, GP1 RX to probe TX, and ground to ground. No SWD.
6. Build separate GP8 E-stop-sense, GP9 reset, and GP10 charger-simulation controls.
   They are logic simulations, not physical safety paths.

## Wire these nets exactly

The Adafruit 5648 is a **non-isolated low-side driver**. Output `+` is V+, output
`-` is switched ground, and all grounds are common.

| Net | Domain | Endpoints |
| --- | --- | --- |
{net_rows}

```text
12V_POS -> IDEC NC1 -> IDEC NC2 -> DRIVER.VPLUS / RELAY.COIL_HIGH
PICO.GP11 -> DRIVER.IN
DRIVER.OUT -> RELAY.COIL_LOW
12V_POS -> RELAY.COM -> RELAY.NO -> LAMP -> GND_COMMON
```

The driver carries the flyback diode across V+/OUT. **Reverse polarity can
forward-bias it.** Meter polarity before 12 V and keep the 0.20 A limit set. Do
not discover polarity with sparks, however festive.

## Firmware pins

`python3 commissioning/fixture.py --check` parses the authoritative Pico target.

| Signal | Pico pin |
| --- | ---: |
{pin_rows}

## F1 — mechanical, no power

- [ ] Plate is flat; feet are uncracked; labels are legible.
- [ ] Tallest underside part has at least 5 mm table clearance.
- [ ] Switches operate without moving their mounts.
- [ ] Pico is the fixture SC1632, not production Pico.
- [ ] Battery, motors, and MDDS10 are absent.

## F2 — continuity, no power

- [ ] Each bumper is closed at rest and opens when pressed.
- [ ] IDEC NC1 opens when pressed; release/twist, then repeat for NC2.
- [ ] The series coil path opens when either NC channel opens.
- [ ] No Pico GPIO has continuity to a 12 V net.
- [ ] 12V_POS is not shorted to ground; loose supply leads meter with correct polarity.

The series E-stop path proves each contact individually only while unpowered. It
cannot create two independent powered channel results. Record that limitation.

## F3 — USB logic and UART

1. Leave 12 V disconnected. Connect Pico USB and Debug Probe USB separately.
2. Observe 115200-baud status and measure GP11 low.
3. Open one bumper at a time; record exact zone identity. Hold one open to observe
   broken-wire behavior.
4. Exercise GP8, GP9, and GP10 separately. GP10 closed to ground means charger
   absent; open means charger present through the firmware pull-up.
5. Send fixed-contract status/heartbeat/drive frames. Capture clamps and latches,
   but do not record relay or motor behavior.
6. Confirm GP11 stayed low. Disconnect USB before changing wires.

## F4 — 12 V negative control

1. Re-run F2. Set the disconnected supply to 12.0 V and **0.20 A maximum**. Turn it
   off and meter its polarity again.
2. Start USB logic, wait for stable status, and measure GP11 low.
3. With Pico stable, connect 12V_POS and ground while the supply is off, then turn
   it on. Never reset or flash the Pico while 12 V is present.
4. Only the driver's small idle/indicator current is expected. The 134 mA relay
   coil must not energize and the roughly 20 mA lamp must remain dark.
5. If the relay clicks, lamp lights, current limit trips, or current approaches the
   coil load, turn 12 V off immediately and record failure.
6. Press the physical E-stop only to confirm the already-off feed is removed. This
   is not a powered de-energization timing result.
7. Turn off and disconnect 12 V before stopping USB logic.

## This fixture cannot pass

- Coil actuation, a positive lamp result, or powered E-stop timing with the current
  fail-stopped target.
- Production conditioned inputs, relay driver, contact wetting, fuses, harness,
  motor outputs, encoders, battery, or thermal behavior.
- Independent powered proof of the two series E-stop channels.
- Any physical commissioning result without exact first-article measurements.

`commissioning/fixture-v1.json` is authoritative. Generated prose, labels, and
SCAD data are conveniences; `--check` makes drift loud.
'''


def render_labels(manifest: dict) -> str:
    del manifest
    labels = [
        'RB-FIXTURE-V1', 'NO BATTERY / NO MOTORS / NO MDDS10',
        'USB FIRST · 12 V LAST · 0.20 A MAX', 'REMOVE 12 V BEFORE RESET',
        'PICO GP0 TX', 'PICO GP1 RX', 'COMMON GROUND',
        *(f'B{index} · GP{index + 1}' for index in range(1, 7)),
        'GP8 · E-STOP SIM', 'GP9 · RESET', 'GP10 · CHARGER SIM',
        'GP11 · DRIVER IN', '12V+', 'NC1', 'NC2', 'DRIVER V+', 'DRIVER OUT',
        'COIL +', 'COIL -', 'RELAY COM', 'RELAY NO', 'GREEN WITNESS',
        'NEGATIVE CONTROL ONLY',
    ]
    rows = []
    for index, label in enumerate(labels):
        y = 38 + index * 40
        rows.append(
            f'<rect x="18" y="{y}" width="780" height="34" rx="4" '
            'fill="white" stroke="#171717"/>'
        )
        rows.append(
            f'<text x="30" y="{y + 23}" font-family="Arial, sans-serif" '
            f'font-size="16" font-weight="700">{html.escape(label)}</text>'
        )
    height = 50 + len(labels) * 40
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<svg xmlns="http://www.w3.org/2000/svg" width="8.5in" '
        f'height="{height / 96:.3f}in" viewBox="0 0 816 {height}">\n'
        '<rect width="100%" height="100%" fill="white"/>\n'
        '<text x="18" y="24" font-family="Arial, sans-serif" font-size="14" '
        'fill="#444">Print at 100%; cut on rectangles; labels are not evidence.</text>\n'
        + '\n'.join(rows) + '\n</svg>\n'
    )


def render_scad_data(manifest: dict) -> str:
    printer = manifest['printer']
    layout = manifest['layout']
    plate_x, plate_y, plate_z = printer['plate_mm']
    bumper_centers = ', '.join(f'[{x}, {y}]' for x, y in layout['bumper_centers'])
    return f'''// Generated by commissioning/fixture.py; do not hand-edit.
fixture_id = "{manifest['fixture_id']}";
plate_width = {plate_x};
plate_depth = {plate_y};
plate_thickness = {plate_z};
foot_height = {printer['feet_below_plate_mm']};
breadboard_center = {layout['breadboard']['center']};
breadboard_size = {layout['breadboard']['size']};
estop_center = {layout['estop']['center']};
estop_hole_diameter = {layout['estop']['panel_hole_diameter']};
lamp_center = {layout['lamp']['center']};
lamp_hole_diameter = {layout['lamp']['panel_hole_diameter']};
bumper_centers = [{bumper_centers}];
bumper_hole_spacing = {layout['bumper_hole_spacing']};
driver_tie_center = {layout['driver_tie_center']};
relay_tie_center = {layout['relay_tie_center']};
'''


def generated_content(manifest: dict) -> dict[Path, str]:
    return {
        GUIDE_PATH: render_guide(manifest),
        LABEL_PATH: render_labels(manifest),
        SCAD_DATA_PATH: render_scad_data(manifest),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    manifest = load_manifest()
    validate_manifest(manifest)
    outputs = generated_content(manifest)
    if args.check:
        stale = [
            str(path.relative_to(ROOT))
            for path, content in outputs.items()
            if not path.exists() or path.read_text(encoding='utf-8') != content
        ]
        if stale:
            raise SystemExit(f'STALE_FIXTURE_ARTIFACTS: {", ".join(stale)}')
        print('RB_FIXTURE_V1_PASS')
        return
    for path, content in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding='utf-8')
        print(f'wrote {path.relative_to(ROOT)}')


if __name__ == '__main__':
    main()
