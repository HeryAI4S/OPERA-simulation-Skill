import tempfile
import unittest
from pathlib import Path

from scripts.comi_preflight import analyse_file


class ComiPreflightTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def check(self, text):
        path = self.root / "test.comi"
        path.write_text(text, encoding="utf-8")
        return analyse_file(path)

    def test_file_parameter_does_not_consume_following_parameters(self):
        issues = self.check("PLOT FILE=TEMP COMPONENT=BY PRINT=NO GRAPH=NO\n")
        self.assertFalse(any(i.code == "unquoted-path" for i in issues))

    def test_real_unquoted_path_with_spaces_still_warns(self):
        issues = self.check("TABLE OUTFILE=some folder/table.dat F1=X\n")
        self.assertTrue(any(i.code == "unquoted-path" for i in issues))

    def test_quoted_path_with_spaces(self):
        issues = self.check("TABLE OUTFILE='some folder/table.dat' F1=X\n")
        self.assertFalse(any(i.code == "unquoted-path" for i in issues))

    def test_relative_include_with_both_separator_styles(self):
        (self.root / "sub").mkdir()
        (self.root / "sub" / "child.comi").write_text("/ child\n")
        for separator in ("/", "\\"):
            issues = self.check(f"$COMINPUT sub{separator}child.comi\n")
            self.assertFalse(any(i.code == "missing-cominput" for i in issues))

    def test_nested_loop_variables_and_blocks(self):
        issues = self.check("$DO #IR 1 7\n$FOR #K 0 1\n$IF #K GT 0\n$CONSTANT #X #IR+#K\n$END IF\n$END FOR\n$END DO\n")
        self.assertFalse(any(i.level == "error" or i.code == "unbound-variable" for i in issues))

    def test_truncated_or_mismatched_blocks_are_errors(self):
        for text in ("$IF 1\n", "$DO #K 1 5\n$END IF\n", "$END WHILE\n"):
            self.assertTrue(any(i.level == "error" for i in self.check(text)))


if __name__ == "__main__":
    unittest.main()
