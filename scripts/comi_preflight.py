#!/usr/bin/env python3
"""Static, conservative preflight checks for OPERA COMI files.

This checker intentionally does not claim to parse COMI fully. It finds common
automation hazards without an OPERA installation: unresolved local includes,
unsafe output operations, obvious model/mesh ordering errors and unbound user
variables. Treat warnings as review prompts, not solver diagnostics.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


VARIABLE_RE = re.compile(r"(?<!#)(#[A-Za-z][A-Za-z0-9_#$\[\]]*)")
DEFINE_RE = re.compile(
    r"^\s*(?:\$(?:CONSTANT|PARAMETER|MODELDIMENSION|EQUATION)\s+|)(#[A-Za-z][A-Za-z0-9_#$\[\]]*)\s*(?::=|=|\s)",
    re.IGNORECASE,
)
COMINPUT_RE = re.compile(
    r"\$COMINPUT\s+(?:'([^']+)'|\"([^\"]+)\"|([^\s|,]+))", re.IGNORECASE
)
FILE_VALUE_RE = re.compile(
    r"\b(?:FILE|FILENAME|OUTFILE|INFILE)\s*=\s*"
    r"(%QUOTE(?:<[^>]*>|\([^)]*\))|'[^']*'|\"[^\"]*\"|.*?)"
    r"(?=\s+[+-]?[A-Za-z]\w*\s*=|[,|]|$)", re.IGNORECASE
)


@dataclass(frozen=True)
class Issue:
    level: str
    code: str
    file: str
    line: int
    message: str


def _normalise_variable(name: str) -> str:
    return name.upper()


def _source_lines(path: Path) -> Iterable[tuple[int, str]]:
    """Read tolerant text; COMI files in the template library may be legacy encoded."""
    data = path.read_bytes()
    for encoding in ("utf-8-sig", "gb18030", "cp1252", "latin-1"):
        try:
            text = data.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    else:  # pragma: no cover - latin-1 above always succeeds
        text = data.decode("latin-1", errors="replace")
    yield from enumerate(text.splitlines(), start=1)


def _is_comment(line: str) -> bool:
    return line.lstrip().startswith("/")


def _local_include(parent: Path, raw_name: str) -> Path:
    candidate = Path(raw_name.replace("\\", "/"))
    if not candidate.suffix:
        candidate = candidate.with_suffix(".comi")
    return candidate if candidate.is_absolute() else parent / candidate


def _is_safe_state_or_case_output_overwrite(line: str) -> bool:
    """Recognise deterministic state changes and output confined to a COMI case results folder."""
    upper = line.upper().replace("/", "\\")
    if re.match(r"^BUFFER\s+OPTION\s*=\s*OVERWRITE\b", upper):
        return True
    return "&COMIPATH&" in upper and "\\RESULTS\\" in upper


def analyse_file(path: Path, allowed_variables: set[str] | None = None) -> list[Issue]:
    """Analyse one file without following includes; suitable for predictable CI output."""
    allowed_variables = allowed_variables or set()
    issues: list[Issue] = []
    defined: set[str] = set(allowed_variables)
    used: dict[str, int] = {}
    model_created = False
    surface_meshed = False
    blocks: list[tuple[str, int]] = []

    for number, raw_line in _source_lines(path):
        line = raw_line.strip()
        if not line or _is_comment(line):
            continue

        definition = DEFINE_RE.match(line)
        if definition:
            defined.add(_normalise_variable(definition.group(1)))
        loop = re.match(r"^\$(?:DO|FOR)\s+(#[A-Za-z][A-Za-z0-9_]*)\b", line, re.IGNORECASE)
        if loop:
            defined.add(_normalise_variable(loop.group(1)))
        opening = re.match(r"^\$(IF|DO|FOR|WHILE)\b", line, re.IGNORECASE)
        closing = re.match(r"^\$END\s+(IF|DO|FOR|WHILE)\b", line, re.IGNORECASE)
        if opening:
            blocks.append((opening.group(1).upper(), number))
        elif closing:
            kind = closing.group(1).upper()
            if not blocks or blocks[-1][0] != kind:
                issues.append(Issue("error", "block-mismatch", str(path), number,
                                    f"Unmatched $END {kind}"))
            else:
                blocks.pop()

        for variable in VARIABLE_RE.findall(line):
            key = _normalise_variable(variable)
            used.setdefault(key, number)

        include = COMINPUT_RE.search(line)
        if include:
            include_name = next(value for value in include.groups() if value is not None)
            include_path = _local_include(path.parent, include_name)
            if not include_path.exists():
                issues.append(
                    Issue(
                        "error",
                        "missing-cominput",
                        str(path),
                        number,
                        f"$COMINPUT target does not exist: {include_path}",
                    )
                )

        upper = line.upper()
        if re.search(r"\bOVERWRITE\b", upper) and not _is_safe_state_or_case_output_overwrite(line):
            issues.append(
                Issue(
                    "warning",
                    "overwrite",
                    str(path),
                    number,
                    "Destructive overwrite detected; verify case-local output path.",
                )
            )
        if upper.startswith("$OS"):
            issues.append(
                Issue(
                    "warning",
                    "os-command",
                    str(path),
                    number,
                    "$OS executes a shell command; restrict it to a verified case folder.",
                )
            )
        if upper.startswith("$EXEC"):
            issues.append(
                Issue(
                    "info",
                    "external-exec",
                    str(path),
                    number,
                    "External program invocation found; inspect EXECEXITCODE handling.",
                )
            )
        if "$PYTHON" in upper:
            issues.append(
                Issue(
                    "info",
                    "python-hook",
                    str(path),
                    number,
                    "Embedded Python found; verify installed OPERA API and case-local path.",
                )
            )

        for value in FILE_VALUE_RE.findall(line):
            candidate = value.strip()
            if " " in candidate and not candidate.startswith(("'", '"', "&", "%QUOTE")):
                issues.append(
                    Issue(
                        "warning",
                        "unquoted-path",
                        str(path),
                        number,
                        f"Path-like parameter contains spaces without an obvious quote: {candidate}",
                    )
                )
            if re.match(r"^[A-Za-z]:[\\/]", candidate.lstrip("'\"")):
                issues.append(
                    Issue(
                        "warning",
                        "absolute-path",
                        str(path),
                        number,
                        "Absolute path found; replace with a case-local/configured path before reuse.",
                    )
                )

        if re.match(r"^MODEL\s+(?:OPTION\s*=\s*)?CREATE\b", upper):
            model_created = True
        elif re.match(r"^MESH\b", upper):
            if not model_created:
                issues.append(
                    Issue(
                        "warning",
                        "mesh-before-model",
                        str(path),
                        number,
                        "MESH appears before local MODEL CREATE or MODEL OPTION=CREATE; confirm setup is in an included file.",
                    )
                )
            surface_meshed = True
        elif re.match(r"^FILL\b", upper):
            if not surface_meshed:
                issues.append(
                    Issue(
                        "warning",
                        "fill-before-mesh",
                        str(path),
                        number,
                        "FILL appears before local MESH; confirm setup is in an included file.",
                    )
                )

    for kind, first_line in blocks:
        issues.append(Issue("error", "unclosed-block", str(path), first_line,
                            f"Missing $END {kind}"))
    for variable, first_line in sorted(used.items()):
        if variable not in defined:
            issues.append(
                Issue(
                    "info",
                    "unbound-variable",
                    str(path),
                    first_line,
                    f"{variable} is used but not defined locally; it may be a case/input/include variable.",
                )
            )
    return issues


def collect_comi_paths(inputs: Iterable[str]) -> list[Path]:
    paths: list[Path] = []
    for raw in inputs:
        path = Path(raw).expanduser().resolve()
        if path.is_dir():
            paths.extend(sorted(path.rglob("*.comi")))
        elif path.suffix.lower() == ".comi":
            paths.append(path)
        else:
            raise ValueError(f"Expected a COMI file or directory: {path}")
    return sorted(set(paths))


def main() -> int:
    parser = argparse.ArgumentParser(description="Static safety checks for OPERA COMI files.")
    parser.add_argument("paths", nargs="+", help="COMI files or directories to inspect")
    parser.add_argument("--allow-variable", action="append", default=[], help="Expected external #variable")
    parser.add_argument("--json", dest="json_path", help="Write structured report to this path")
    parser.add_argument("--fail-on-warning", action="store_true", help="Return nonzero for warnings")
    args = parser.parse_args()

    allowed = {_normalise_variable(name if name.startswith("#") else f"#{name}") for name in args.allow_variable}
    try:
        paths = collect_comi_paths(args.paths)
    except ValueError as error:
        parser.error(str(error))
    if not paths:
        parser.error("No .comi files found.")

    issues = [issue for path in paths for issue in analyse_file(path, allowed)]
    counts = {level: sum(issue.level == level for issue in issues) for level in ("error", "warning", "info")}
    report = {
        "checked_files": [str(path) for path in paths],
        "summary": counts,
        "issues": [asdict(issue) for issue in issues],
    }
    for issue in issues:
        print(f"{issue.level.upper():7} {issue.file}:{issue.line} [{issue.code}] {issue.message}")
    print(f"Checked {len(paths)} file(s): {counts['error']} error(s), {counts['warning']} warning(s), {counts['info']} info item(s).")

    if args.json_path:
        destination = Path(args.json_path).expanduser().resolve()
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if counts["error"] or (args.fail_on_warning and counts["warning"]):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
