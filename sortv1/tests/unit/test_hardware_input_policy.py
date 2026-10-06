import csv
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / 'sortv1/hardware/source'

def rows(name):
    with (SOURCE/name).open(encoding='utf-8', newline='') as handle:
        return list(csv.DictReader(handle))

class HardwareInputPolicyTests(unittest.TestCase):
    def test_nine_dry_contacts_have_external_bias_in_both_canonical_tables(self):
        contacts = {12,13,14,15,16,17,18,19,27}
        signals = {r['gpio']:r for r in rows('signals_master.csv')}
        pins = {int(r['gpio']):json.loads(r['source_json']) for r in rows('pinout_master.csv')}
        wires = [json.loads(r['source_json']) for r in rows('connections_master.csv')]
        for pin in contacts:
            with self.subTest(pin=pin):
                self.assertIn('external 10k', signals[str(pin)]['notes'])
                self.assertIn('external 10k', pins[pin]['pull'])
                self.assertIn('TBC_CALIBRATE', signals[str(pin)]['polarity'])
                self.assertTrue(any(w['to_pin'] == f'GPIO{pin}' and w['from_component']==f'MVP-87-R{pin}' for w in wires))
                self.assertTrue(any(w['signal']==f'DRY_CONTACT_GPIO{pin}_RETURN' and w['voltage']=='0V_LOGIC' for w in wires))

    def test_electronic_sensors_do_not_inherit_contact_pulls(self):
        signals = {r['gpio']:r for r in rows('signals_master.csv')}
        for pin in (10,20,21,22,26,28):
            self.assertIn('no generic pull-up', signals[str(pin)]['notes'])
        self.assertIn('NEVER 12V', signals['28']['notes'])

    def test_bom_accounts_for_bias_and_separate_enable_button(self):
        bom = {r['id']:r for r in rows('bom_master.csv')}
        self.assertEqual(bom['MVP-87']['quantity'], '12')
        self.assertEqual(bom['MVP-83']['quantity'], '1')
        self.assertIn('10kOhm 1% 0.25W', bom['MVP-83']['part_number'])
        self.assertEqual(bom['MVP-88']['quantity'], '1')
        self.assertEqual(bom['BOM-26']['quantity'], '1')
        self.assertEqual(bom['MVP-88']['actual_quote_mxn'], '')
        signals = {r['signal']:r for r in rows('signals_master.csv')}
        self.assertEqual(signals['ACTUATOR_ENABLE']['gpio'], 'N/A')
        self.assertEqual(signals['PHYSICAL_RESET']['gpio'], '15')

    def test_latch_enable_branch_is_downstream_of_guards_and_not_gpio(self):
        wires = {r['wire_id']:json.loads(r['source_json']) for r in rows('connections_master.csv')}
        self.assertEqual(wires['W114']['from_component'], 'SENS-25')
        self.assertEqual(wires['W114']['to_component'], 'MVP-88')
        self.assertEqual(wires['W147']['from_component'], 'MVP-88')
        self.assertEqual(wires['W147']['to_component'], 'SAFE-34')
        self.assertEqual(wires['W148']['from_component'], 'SENS-25')
        self.assertNotIn('GPIO', wires['W147']['to_pin'])
