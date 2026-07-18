from copy import deepcopy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fixture import (  # noqa: E402
    FixtureValidationError,
    load_manifest,
    render_guide,
    validate_manifest,
)


class FixtureClosedWorldTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = load_manifest()

    def mutated(self) -> dict:
        return deepcopy(self.manifest)

    def test_reviewed_manifest_passes(self) -> None:
        validate_manifest(self.mutated())

    def test_renamed_or_forbidden_component_is_rejected(self) -> None:
        manifest = self.mutated()
        manifest['components'][3]['part'] = 'fixture motor'
        with self.assertRaisesRegex(FixtureValidationError, 'changed part or quantity'):
            validate_manifest(manifest)

    def test_firmware_pin_drift_is_rejected(self) -> None:
        source = (Path(__file__).resolve().parents[2] / 'firmware' / 'pico2-safety' /
                  'src' / 'pico_main.c').read_text(encoding='utf-8')
        source = source.replace('#define RB_RELAY_ENABLE_PIN 11',
                                '#define RB_RELAY_ENABLE_PIN 12')
        with self.assertRaisesRegex(FixtureValidationError, 'firmware pin drift'):
            validate_manifest(self.mutated(), source)

    def test_fail_stopped_output_drift_is_rejected(self) -> None:
        source = (Path(__file__).resolve().parents[2] / 'firmware' / 'pico2-safety' /
                  'src' / 'pico_main.c').read_text(encoding='utf-8')
        source = source.replace('bool enable = false;', 'bool enable = true;')
        with self.assertRaisesRegex(FixtureValidationError, 'fail-stopped relay output'):
            validate_manifest(self.mutated(), source)

    def test_witness_lamp_bypass_is_rejected(self) -> None:
        manifest = self.mutated()
        net = next(net for net in manifest['nets'] if net['id'] == 'RELAY_NO_LAMP')
        net['members'][0] = 'BENCH_12V.POS'
        with self.assertRaisesRegex(FixtureValidationError, 'topology changed'):
            validate_manifest(manifest)

    def test_misplaced_coil_flyback_topology_is_rejected(self) -> None:
        manifest = self.mutated()
        net = next(net for net in manifest['nets'] if net['id'] == 'DRIVER_OUT')
        net['members'][1] = 'RELAY.COIL_HIGH'
        with self.assertRaisesRegex(FixtureValidationError, 'DRIVER_OUT topology changed'):
            validate_manifest(manifest)

    def test_second_ground_net_is_rejected(self) -> None:
        manifest = self.mutated()
        manifest['nets'].append({
            'id': 'EXTRA_GROUND',
            'domain': 'ground',
            'members': ['PICO.GND', 'BENCH_12V.NEG'],
        })
        with self.assertRaisesRegex(FixtureValidationError, 'closed-world net names'):
            validate_manifest(manifest)

    def test_high_voltage_gpio_connection_is_rejected(self) -> None:
        manifest = self.mutated()
        net = next(net for net in manifest['nets'] if net['id'] == '12V_POS')
        net['members'].append('PICO.GP11')
        with self.assertRaisesRegex(FixtureValidationError, '12V_POS topology changed'):
            validate_manifest(manifest)

    def test_missing_nc_switch_is_rejected(self) -> None:
        manifest = self.mutated()
        manifest['components'] = [
            component for component in manifest['components']
            if component['id'] != 'BUMP_6'
        ]
        with self.assertRaisesRegex(FixtureValidationError, 'closed-world components'):
            validate_manifest(manifest)

    def test_guide_keeps_negative_control_boundary(self) -> None:
        guide = render_guide(self.mutated())
        self.assertIn('negative-control', guide)
        self.assertIn('0.20 A', guide)
        self.assertIn('must remain dark', guide)
        self.assertIn('no physical pass is bundled', guide)


if __name__ == '__main__':
    unittest.main()
