import copy
import json
import math
import tempfile
import unittest
from pathlib import Path

from scripts import field_quality as fq


def config():
    return dict(half_range_mm=950., check_range_mm=850., inner_radius_mm=25.,
                outer_radius_mm=35., axial_step_mm=5., target_tm=.2,
                uniformity_limit_percent=1., target_error_limit_percent=1.,
                boundary_limit_percent=.1, rings=7, angles=8, simulation=1,
                x_component="BY", y_component="BX")


def records(c):
    rows, summaries = [], []
    for axis, center, amplitude in ((1, -.2, .004), (2, .2, .008)):
        rows.append([70, axis, 0, 0, 0, 0, 0, 0, c["half_range_mm"], center, c["axial_step_mm"], c["simulation"]])
        for ring in range(1, c["rings"] + 1):
            radius = c["outer_radius_mm"] * ring / c["rings"]
            for k in range(c["angles"]):
                angle = 360 * k / c["angles"]
                x, y = radius * math.cos(math.radians(angle)), radius * math.sin(math.radians(angle))
                value = center * (1 + amplitude * (x / c["outer_radius_mm"]) ** 2)
                rows.append([70, axis, 1 + (ring - 1) * c["angles"] + k, ring, x, y, radius, angle,
                             c["half_range_mm"], value, c["axial_step_mm"], c["simulation"]])
        summaries.append([90, axis, center, 0, 100 * amplitude * (c["inner_radius_mm"] / c["outer_radius_mm"]) ** 2,
                          100 * amplitude, c["outer_radius_mm"], 0, c["half_range_mm"], c["axial_step_mm"],
                          c["rings"], c["angles"]])
        summaries.append([91, axis, center / 1.0002, center, .02, .05, .4, -.0002, .0002,
                          c["check_range_mm"], c["half_range_mm"], c["axial_step_mm"]])
    return rows, summaries


def write_rows(path, rows):
    path.write_text("\n".join(" ".join(f"{v:.16E}".replace("E", "D") for v in row) for row in rows) + "\n", encoding="utf-8")


class FieldQualityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.c = config()

    def package(self):
        database = self.root / "source.op3"
        database.write_text("Synthetic unit-test marker; not an OPERA database.")
        manifest = fq.prepare(database, self.root / "post output", self.c)
        rows, summaries = records(self.c)
        write_rows(manifest.parent / "field_raw.dat", rows)
        write_rows(manifest.parent / "field_summary.dat", summaries)
        return manifest

    def test_analytic_two_axis_signed_integrals(self):
        report = fq.evaluate(self.package())
        self.assertAlmostEqual(report["axes"]["1"]["outer_uniformity_percent"], .4)
        self.assertAlmostEqual(report["axes"]["2"]["outer_uniformity_percent"], .8)
        self.assertAlmostEqual(report["axes"]["1"]["inner_uniformity_percent"], .4 * 25**2 / 35**2)
        self.assertTrue(report["numeric_field_pass"])
        self.assertTrue(report["center_range_check_pass"])
        self.assertFalse(report["solver_provenance_verified"])
        self.assertFalse(report["sampling_convergence_verified"])
        self.assertFalse(report["mesh_convergence_verified"])

    def test_off_center_failure_is_not_center_target_failure(self):
        rows, _ = records(self.c)
        rows[-1][9] = .204
        report, _ = fq.reduce_grid(rows, self.c)
        self.assertAlmostEqual(report["2"]["outer_uniformity_percent"], 2)
        self.assertEqual(report["2"]["target_error_percent"], 0)

    def test_prepare_missing_database_is_explicit_and_never_creates_it(self):
        database = self.root / "future.op3"
        manifest = fq.prepare(database, self.root / "prepared", self.c)
        data = json.loads(manifest.read_text())
        self.assertIsNone(data["database_sha256"])
        self.assertEqual(data["status"], "prepared_not_executed")
        self.assertFalse(database.exists())
        self.assertNotIn("@@", (manifest.parent / data["post_comi"]).read_text())

    def test_rejects_existing_output_and_unsafe_path(self):
        self.package()
        with self.assertRaises(FileExistsError):
            fq.prepare(self.root / "source.op3", self.root / "post output", self.c)
        for name in ("quote'file.op3", "amp&file.op3", "macro%file.op3"):
            with self.assertRaises(ValueError):
                fq.prepare(self.root / name, self.root / "unused", self.c)
        self.assertFalse((self.root / "unused").exists())

    def test_rejects_invalid_parameters_before_creating_output(self):
        for key, value in (("target_tm", 0), ("half_range_mm", math.nan), ("check_range_mm", 950),
                           ("inner_radius_mm", 24), ("axial_step_mm", 3), ("angles", 0)):
            candidate = dict(self.c, **{key: value})
            with self.subTest(key=key), self.assertRaises(ValueError):
                fq.prepare(self.root / "source.op3", self.root / "invalid", candidate)
        self.assertFalse((self.root / "invalid").exists())

    def test_rejects_incomplete_duplicate_and_wrong_geometry(self):
        rows, _ = records(self.c)
        candidates = [rows[:-1], rows + [rows[0]]]
        for column, value in ((3, 99), (4, 999), (8, 850), (11, 2)):
            altered = copy.deepcopy(rows)
            altered[-1][column] = value
            candidates.append(altered)
        for candidate in candidates:
            with self.assertRaises(ValueError):
                fq.reduce_grid(candidate, self.c)

    def test_rejects_nonfinite_and_wrong_width_files(self):
        for value in (" ".join(["nan"] * 12), " ".join(["0"] * 11), "bad input"):
            file = self.root / "bad.dat"
            file.write_text(value)
            with self.assertRaises(ValueError):
                fq.numeric_rows(file)

    def test_rejects_zero_integral_references(self):
        rows, _ = records(self.c)
        rows[0][9] = 0
        with self.assertRaisesRegex(ValueError, "reference is too small"):
            fq.reduce_grid(rows, self.c)
        manifest = self.package()
        _, summary = records(self.c)
        summary[1][2] = 0
        write_rows(manifest.parent / "field_summary.dat", summary)
        with self.assertRaisesRegex(ValueError, "reference is too small"):
            fq.evaluate(manifest)

    def test_numeric_pass_and_range_diagnostic_have_separate_flags(self):
        self.c["uniformity_limit_percent"] = .5
        manifest = self.package()
        _, summary = records(self.c)
        summary[1][5] = .25
        summary[1][7:9] = [-.001, .001]
        write_rows(manifest.parent / "field_summary.dat", summary)
        report = fq.evaluate(manifest)
        self.assertTrue(report["axes"]["1"]["numeric_field_pass"])
        self.assertFalse(report["axes"]["2"]["numeric_field_pass"])
        self.assertFalse(report["axes"]["1"]["center_range_check_pass"])
        self.assertTrue(report["axes"]["2"]["center_range_check_pass"])
        self.assertFalse(report["numeric_field_pass"])
        self.assertFalse(report["center_range_check_pass"])

    def test_rejects_missing_or_forged_summary(self):
        manifest = self.package()
        _, summary = records(self.c)
        candidates = [summary[:-1], summary + [summary[0]]]
        for column, value in ((3, 2), (4, 5), (6, 99), (8, 850)):
            altered = copy.deepcopy(summary)
            altered[0][column] = value
            candidates.append(altered)
        altered = copy.deepcopy(summary)
        altered[1][5] = .001  # endpoint claim disagrees with saved endpoint fields
        candidates.append(altered)
        for candidate in candidates:
            write_rows(manifest.parent / "field_summary.dat", candidate)
            with self.assertRaises(ValueError):
                fq.evaluate(manifest)

    def test_rejects_changed_comi_and_database(self):
        manifest = self.package()
        post = manifest.parent / "post_integrated_field.comi"
        original = post.read_bytes()
        post.write_bytes(original + b"\n/ changed\n")
        with self.assertRaisesRegex(ValueError, "COMI changed"):
            fq.evaluate(manifest)
        post.write_bytes(original)
        (self.root / "source.op3").write_text("changed database")
        with self.assertRaisesRegex(ValueError, "database changed"):
            fq.evaluate(manifest)


if __name__ == "__main__":
    unittest.main()
