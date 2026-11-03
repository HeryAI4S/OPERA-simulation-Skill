from __future__ import annotations

import py_compile
import re
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = {
    "SKILL.md",
    "LICENSE",
    "NOTICE.md",
    "README.md",
    "agents/openai.yaml",
    "scripts/comi_preflight.py",
    "scripts/run_cases.py",
    "scripts/field_quality.py",
    "assets/field-quality/post.comi.in",
    "references/scan-magnet-dct-workflow.md",
    "references/documentation-map.md",
    "references/transient-losses.md",
}

FORBIDDEN_SUFFIXES = {
    ".op2",
    ".op3",
    ".opc",
    ".track",
    ".pyc",
    ".pdf",
    ".cond",
    ".bh",
    ".res",
}

TEXT_SUFFIXES = {".md", ".py", ".yaml", ".yml", ".json", ".toml", ".in", ".comi"}


def markdown_slug(title: str) -> str:
    title = title.strip().lower()
    title = re.sub(r"[^\w\s-]", "", title, flags=re.UNICODE)
    return re.sub(r"\s+", "-", title)


class PublicationTests(unittest.TestCase):
    def test_required_publication_files_exist(self) -> None:
        missing = sorted(path for path in REQUIRED_FILES if not (ROOT / path).is_file())
        self.assertEqual([], missing, f"missing publication files: {missing}")

    def test_skill_frontmatter_is_discoverable(self) -> None:
        skill_path = ROOT / "SKILL.md"
        self.assertTrue(skill_path.is_file(), "SKILL.md is missing")
        skill = skill_path.read_text(encoding="utf-8")
        match = re.match(r"^---\n(.*?)\n---\n", skill, flags=re.DOTALL)
        self.assertIsNotNone(match, "SKILL.md must start with YAML frontmatter")
        frontmatter = match.group(1)
        self.assertRegex(frontmatter, r"(?m)^name:\s*opera-simulation\s*$")
        description = re.search(r"(?m)^description:\s*(.+)$", frontmatter)
        self.assertIsNotNone(description)
        self.assertTrue(description.group(1).startswith("Use when"))

    def test_repository_excludes_private_and_vendor_artifacts(self) -> None:
        bad_paths: list[str] = []
        tracked = subprocess.run(
            ["git", "ls-files"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.splitlines()
        for relative in tracked:
            path = ROOT / relative
            if "__pycache__" in path.parts or path.suffix.lower() in FORBIDDEN_SUFFIXES:
                bad_paths.append(relative)
        self.assertEqual([], sorted(bad_paths), f"forbidden artifacts: {bad_paths}")

    def test_public_text_has_no_machine_private_absolute_paths(self) -> None:
        findings: list[str] = []
        for path in ROOT.rglob("*"):
            if ".git" in path.parts or not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
                continue
            text = path.read_text(encoding="utf-8")
            for line_number, line in enumerate(text.splitlines(), start=1):
                if re.search(r"(?i)\b[A-Z]:\\", line):
                    findings.append(f"{path.relative_to(ROOT)}:{line_number}: Windows absolute path")
        self.assertEqual([], findings, "\n".join(findings))

    def test_markdown_links_and_local_anchors_resolve(self) -> None:
        failures: list[str] = []
        for path in ROOT.rglob("*.md"):
            if ".git" in path.parts:
                continue
            text = path.read_text(encoding="utf-8")
            headings = {
                markdown_slug(match.group(1))
                for match in re.finditer(r"(?m)^#{1,6}\s+(.+?)\s*$", text)
            }
            for match in re.finditer(r"\[[^\]]+\]\(([^)]+)\)", text):
                target = match.group(1).strip()
                if target.startswith(("http://", "https://", "mailto:")):
                    continue
                file_part, separator, anchor = target.partition("#")
                target_path = path if not file_part else (path.parent / file_part).resolve()
                if not target_path.exists():
                    failures.append(f"{path.relative_to(ROOT)} -> missing {target}")
                    continue
                if separator and target_path == path.resolve() and anchor not in headings:
                    failures.append(f"{path.relative_to(ROOT)} -> missing anchor #{anchor}")
        self.assertEqual([], failures, "\n".join(failures))

    def test_python_scripts_compile_without_writing_bytecode(self) -> None:
        scripts = sorted((ROOT / "scripts").glob("*.py"))
        self.assertGreaterEqual(len(scripts), 2)
        with tempfile.TemporaryDirectory() as temporary_directory:
            for index, script in enumerate(scripts):
                cfile = Path(temporary_directory) / f"script-{index}.pyc"
                py_compile.compile(str(script), cfile=str(cfile), doraise=True)

    def test_readme_documents_installation_and_rights_boundary(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8").lower()
        for phrase in ("installation", "prerequisites", "license", "third-party", "opera manuals"):
            self.assertIn(phrase, readme)


if __name__ == "__main__":
    unittest.main(verbosity=2)
