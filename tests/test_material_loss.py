import importlib.util
import hashlib
import json
import math
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def helper():
    path = ROOT / 'scripts' / 'audit_material_loss.py'
    spec = importlib.util.spec_from_file_location('audit_material_loss', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class MaterialLossTests(unittest.TestCase):
    labels = ['ALL_VOLUMES', 'STEEL', 'SHIELD', 'AIR']

    def native(self):
        # time, label index, power W, volume mm3, activation status.
        return ('0 0 0 10 0\n0 1 0 2 0\n0 2 0 3 0\n0 3 0 5 0\n'
                '0.5 0 6 10 0\n0.5 1 2 2 0\n0.5 2 4 3 0\n0.5 3 0 5 0\n'
                '1 0 2 10 0\n1 1 1 2 0\n1 2 1 3 0\n1 3 0 5 0\n')

    def audit(self, text=None, **kwargs):
        self.assertTrue((ROOT / 'scripts' / 'audit_material_loss.py').is_file(),
                        'Native material audit helper has not been implemented')
        return helper().audit(text if text is not None else self.native(),
                              self.labels, volume_unit='mm3', **kwargs)

    def test_integrates_materials_without_assuming_whole_magnet(self):
        result = self.audit()
        self.assertEqual(result['mesh_energy_J']['ALL_VOLUMES'], 3.5)
        self.assertEqual(result['mesh_energy_J']['STEEL'], 1.25)
        self.assertEqual(result['mesh_energy_J']['SHIELD'], 2.25)
        self.assertIsNone(result['full_magnet_estimate'])
        self.assertEqual(result['scope'], 'native_export_domain')

    def test_reconstruction_scales_energy_once_and_preserves_times(self):
        result = self.audit(full_magnet_factor=8, symmetry_evidence='Verified octant; no activated copies')
        self.assertEqual(result['full_magnet_estimate']['energy_J']['ALL_VOLUMES'], 28)
        self.assertEqual(result['times_s'], [0, 0.5, 1])
        self.assertEqual(result['mesh_energy_J']['ALL_VOLUMES'], 3.5)

    def test_scaling_requires_evidence_and_finite_positive_factor(self):
        for factor, evidence in [(8, None), (8, ' '), (0, 'x'), (-1, 'x'),
                                 (math.inf, 'x'), (math.nan, 'x'), (0.5, 'x')]:
            with self.subTest(factor=factor), self.assertRaises(ValueError):
                self.audit(full_magnet_factor=factor, symmetry_evidence=evidence)

    def test_rejects_partial_or_duplicate_material_block(self):
        for text in [self.native().replace('0.5 2 4 3 0\n', ''),
                     self.native().replace('0.5 2 4 3 0', '0.5 1 4 3 0')]:
            with self.subTest(text=text), self.assertRaises(ValueError):
                self.audit(text)

    def test_rejects_nonzero_activation_and_nonintegral_label_id(self):
        for text in [self.native().replace('0.5 1 2 2 0', '0.5 1 2 2 1'),
                     self.native().replace('0.5 1 2 2 0', '0.5 1.5 2 2 0')]:
            with self.subTest(text=text), self.assertRaises(ValueError):
                self.audit(text)

    def test_rejects_power_or_volume_closure_failure_and_volume_drift(self):
        for text in [self.native().replace('0.5 2 4 3 0', '0.5 2 5 3 0'),
                     self.native().replace('0.5 2 4 3 0', '0.5 2 4 4 0'),
                     self.native().replace(' 3 0', ' 4 0')]:
            with self.subTest(text=text), self.assertRaises(ValueError):
                self.audit(text)

    def test_rejects_nonfinite_negative_and_malformed_records(self):
        for old, new in [('0.5 2 4 3 0', '0.5 2 nan 3 0'),
                         ('0.5 2 4 3 0', '0.5 2 -4 3 0'),
                         ('0.5 2 4 3 0', '0.5 2 4 -3 0'),
                         ('0.5 2 4 3 0', '0.5 2 4 3'),
                         ('0.5 2 4 3 0', 'TTIME 2 4 3 0')]:
            with self.subTest(new=new), self.assertRaises(ValueError):
                self.audit(self.native().replace(old, new))

    def test_rejects_repeated_or_nonmonotonic_times(self):
        with self.assertRaises(ValueError):
            self.audit(self.native().replace('0.5 ', '1.5 '))
        with self.assertRaises(ValueError):
            self.audit(self.native() + self.native())

    def test_d_exponents_and_unordered_labels_within_each_time(self):
        text = self.native().replace('0.5 2 4 3 0', '5D-1 2 4D0 3D0 0')
        lines = text.splitlines()
        lines[4:8] = reversed(lines[4:8])
        result = self.audit('\n'.join(lines))
        self.assertEqual(result['mesh_energy_J']['ALL_VOLUMES'], 3.5)

    def test_compares_saved_states_without_hiding_denser_solver_quadrature(self):
        solver = [(0, 0), (0.25, 5), (0.5, 6), (0.75, 4), (1, 2)]
        result = self.audit(solver_points=solver)
        self.assertEqual(result['solver_comparison']['max_abs_power_difference_W'], 0)
        self.assertEqual(result['solver_comparison']['all_step_energy_J'], 4)
        self.assertEqual(result['solver_comparison']['native_saved_energy_J'], 3.5)

    def test_rejects_solver_mismatch_missing_times_or_interval(self):
        for points in [[(0, 0), (0.5, 7), (1, 2)],
                       [(0, 0), (0.6, 6), (1, 2)],
                       [(0.5, 6), (1, 2)],
                       [(0, 0), (1, 2), (0.5, 6)],
                       [(0, 0), (0.5, math.nan), (1, 2)]]:
            with self.subTest(points=points), self.assertRaises(ValueError):
                self.audit(solver_points=points)

    def test_rejects_invalid_label_contract(self):
        self.assertTrue((ROOT / 'scripts' / 'audit_material_loss.py').is_file())
        for labels in [['TOTAL', 'STEEL'], ['ALL_VOLUMES', 'STEEL', 'STEEL'],
                       ['ALL_VOLUMES']]:
            with self.subTest(labels=labels), self.assertRaises(ValueError):
                helper().audit(self.native(), labels, volume_unit='mm3')

    def test_cli_outputs_provenance_and_refuses_existing_directory(self):
        self.assertTrue((ROOT / 'scripts' / 'audit_material_loss.py').is_file())
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            native = directory / 'native.txt'
            solver = directory / 'solver.csv'
            native.write_text(self.native(), encoding='utf-8')
            solver.write_text('time_s,mesh_ohmic_power_W\n0,0\n0.5,6\n1,2\n', encoding='utf-8')
            original = native.read_bytes()
            target = directory / 'audit'
            command = [sys.executable, str(ROOT / 'scripts' / 'audit_material_loss.py'),
                       str(native), '--labels', *self.labels, '--volume-unit', 'mm3',
                       '--solver-csv', str(solver), '--out', str(target)]
            first = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(first.returncode, 0, first.stderr)
            summary = json.loads((target / 'summary.json').read_text(encoding='utf-8'))
            self.assertEqual(summary['sources'][0]['sha256'], hashlib.sha256(original).hexdigest())
            self.assertEqual(summary['mesh_energy_J']['ALL_VOLUMES'], 3.5)
            self.assertIsNone(summary['full_magnet_estimate'])
            self.assertEqual(native.read_bytes(), original)
            before = (target / 'summary.json').read_bytes()
            second = subprocess.run(command, capture_output=True, text=True)
            self.assertNotEqual(second.returncode, 0)
            self.assertEqual((target / 'summary.json').read_bytes(), before)

    def test_solver_csv_requires_unscaled_power_column(self):
        self.assertTrue((ROOT / 'scripts' / 'audit_material_loss.py').is_file())
        with self.assertRaises(ValueError):
            helper().read_solver_csv('time_s,full_magnet_power_W\n0,0\n1,2\n')
        points = helper().read_solver_csv('time_s,solver_mesh_ohmic_power_W\n0,0\n1D0,2D0\n')
        self.assertEqual(points, [(0, 0), (1, 2)])

    def test_low_precision_export_is_rejected_under_recorded_precision_contract(self):
        # These independently rounded six-digit fields cannot satisfy the documented tolerance.
        text = self.native().replace('0.5 0 6 10 0', '0.5 0 3.58024 10 0')
        text = text.replace('0.5 1 2 2 0', '0.5 1 1.23456 2 0')
        text = text.replace('0.5 2 4 3 0', '0.5 2 2.34567 3 0')
        with self.assertRaises(ValueError):
            self.audit(text)
        self.assertEqual(self.audit()['comparison_tolerance']['relative'], 1e-8)


if __name__ == '__main__':
    unittest.main()
