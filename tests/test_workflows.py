import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / (name + '.py'))
    obj = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj


class LossTests(unittest.TestCase):
    def parse(self, text, **kwargs):
        return module('extract_solver_loss').parse_loss(text, **kwargs)

    def log(self):
        return ('File: demo.op3 simulation: 1\nTime-step: 0.5\n'
                '13 output times defined: example\nNumber of threads = 8\n'
                'Performing full step from 0 to 0.5\n'
                'Ohm Loss in meshed volume = 4 [W]\n'
                'Performing full step from 0.5 to 1\n'
                'Ohm Loss in meshed volume = 2 [W]\n'
                'Simulation 13 saved with solution at time 1\n'
                'Opera 2025 SP1 [Build 20] complete on example\n')

    def test_integrates_and_preserves_initial_assumption(self):
        r = self.parse(self.log(), initial_power=0)
        self.assertEqual(r['energy_J'], 2.5)
        self.assertEqual(r['threads'], 8)
        self.assertEqual(r['initial_power_source'], 'user_supplied')

    def test_initial_power_required(self):
        with self.assertRaises(ValueError):
            self.parse(self.log())

    def test_incomplete_rejected(self):
        with self.assertRaises(ValueError):
            self.parse(self.log().replace('complete on', 'started on'), initial_power=0)

    def test_repeated_run_rejected(self):
        with self.assertRaises(ValueError):
            self.parse(self.log() + self.log(), initial_power=0)

    def test_missing_step_rejected(self):
        with self.assertRaises(ValueError):
            self.parse(self.log().replace('from 0.5 to 1', 'from 0.7 to 1'), initial_power=0)

    def test_step_with_power_then_retry_from_previous_time_rejected(self):
        # A trial endpoint can print power before a rollback/retry. It is not an accepted history.
        text = self.log().replace(
            'Performing full step from 0.5 to 1',
            'Performing full step from 0 to 0.25\n'
            'Ohm Loss in meshed volume = 3 [W]\n'
            'Performing full step from 0.25 to 1')
        with self.assertRaises(ValueError):
            self.parse(text, initial_power=0)

    def test_missing_final_power_rejected(self):
        with self.assertRaises(ValueError):
            self.parse(self.log().replace('Ohm Loss in meshed volume = 2 [W]', ''), initial_power=0)

    def test_nonfinite_initial_rejected(self):
        with self.assertRaises(ValueError):
            self.parse(self.log(), initial_power=float('nan'))


class ProjectTests(unittest.TestCase):
    def test_new_project_is_unsolved_and_wont_overwrite(self):
        import json
        helper = module('init_project')
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / 'demo'
            helper.create_project(target, 'demo', 'ELEKTRATR')
            data = json.loads((target / 'project.json').read_text())
            self.assertEqual(data['status'], 'NOT_SOLVED')
            self.assertIsNone(data['units'])
            self.assertTrue((target / 'source').is_dir())
            with self.assertRaises(FileExistsError):
                helper.create_project(target, 'demo', 'ELEKTRATR')


if __name__ == '__main__':
    unittest.main()
