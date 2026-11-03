#!/usr/bin/env python3
"""Prepare OPERA integral-field Post and independently audit its numeric outputs.

No command in this helper launches OPERA. A numeric field pass is not solver,
symmetry, sampling or finite-element mesh acceptance.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path


SCHEMA = "opera-integrated-field-v1"
TEMPLATE = Path(__file__).resolve().parents[1] / "assets" / "field-quality" / "post.comi.in"


def digest(path):
    hasher = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def validate(config):
    for name in ("half_range_mm", "check_range_mm", "inner_radius_mm", "outer_radius_mm",
                 "axial_step_mm", "target_tm", "uniformity_limit_percent",
                 "target_error_limit_percent", "boundary_limit_percent"):
        if not math.isfinite(config[name]) or config[name] <= 0:
            raise ValueError(f"{name} must be positive and finite")
    for name, minimum in (("rings", 1), ("angles", 8), ("simulation", 1)):
        if not isinstance(config[name], int) or config[name] < minimum:
            raise ValueError(f"{name} must be an integer >= {minimum}")
    if config["check_range_mm"] >= config["half_range_mm"]:
        raise ValueError("check range must be smaller than integration half-range")
    if config["inner_radius_mm"] >= config["outer_radius_mm"]:
        raise ValueError("inner radius must be smaller than outer radius")
    inner_ring = config["rings"] * config["inner_radius_mm"] / config["outer_radius_mm"]
    if not math.isclose(inner_ring, round(inner_ring), abs_tol=1e-9, rel_tol=0):
        raise ValueError("inner radius must lie on a radial sampling ring")
    for name in ("half_range_mm", "check_range_mm"):
        count = 2 * config[name] / config["axial_step_mm"]
        if count < 2 or not math.isclose(count, round(count), abs_tol=1e-8, rel_tol=0):
            raise ValueError("both axial spans must be integer multiples of axial_step_mm")
    for name in ("x_component", "y_component"):
        if config[name] not in ("BX", "BY", "BZ"):
            raise ValueError("field components must be BX, BY or BZ")


def safe_path(path):
    text = str(Path(path).expanduser().resolve())
    if any(char in text for char in "'\"\r\n<>&%|"):
        raise ValueError("path contains unsupported COMI quoting/expansion characters")
    return text


def prepare(database, output, config):
    validate(config)
    database = Path(safe_path(database))
    if database.suffix.lower() != ".op3":
        raise ValueError("database must name an .op3 file")
    output = Path(safe_path(output))
    rendered = TEMPLATE.read_text(encoding="utf-8")
    values = {key.upper(): str(value) for key, value in config.items()}
    values.update(DATABASE_FILE=str(database), RAW_FILE=str(output / "field_raw.dat"),
                  SUMMARY_FILE=str(output / "field_summary.dat"))
    for key, value in values.items():
        rendered = rendered.replace("@@" + key + "@@", value)
    if "@@" in rendered:
        raise ValueError("unresolved COMI template token")
    manifest = dict(schema=SCHEMA, status="prepared_not_executed", config=config,
                    database=str(database), database_sha256=digest(database) if database.is_file() else None,
                    raw_file="field_raw.dat", summary_file="field_summary.dat",
                    post_comi="post_integrated_field.comi", solver_provenance_verified=False)
    output.mkdir(parents=True, exist_ok=False)
    post = output / manifest["post_comi"]
    post.write_text(rendered, encoding="utf-8")
    manifest["post_comi_sha256"] = digest(post)
    (output / "field_quality.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return output / "field_quality.json"


def numeric_rows(path):
    rows = []
    for number, line in enumerate(Path(path).read_text(encoding="utf-8-sig").splitlines(), 1):
        if not line.strip() or line.lstrip().startswith("/"):
            continue
        try:
            row = [float(token.replace("D", "E").replace("d", "e")) for token in line.split()]
        except ValueError as error:
            raise ValueError(f"{Path(path).name}:{number}: invalid numeric row") from error
        if len(row) != 12 or not all(math.isfinite(value) for value in row):
            raise ValueError(f"{Path(path).name}:{number}: expected 12 finite values")
        rows.append(row)
    return rows


def close(actual, expected, label):
    if not math.isclose(actual, expected, rel_tol=1e-9, abs_tol=1e-10):
        raise ValueError(f"{label} mismatch: {actual} != {expected}")


def reduce_grid(rows, config):
    """Audit records 70 and return max deviation from signed centre integrals."""
    validate(config)
    count = 1 + config["rings"] * config["angles"]
    samples = {1: {}, 2: {}}
    for row in rows:
        kind, axis, index, ring, x, y, radius, theta, half_range, value, step, simulation = row
        if kind != 70 or axis not in samples or index != int(index) or not 0 <= index < count:
            raise ValueError("unexpected record type, axis or sample index")
        index = int(index)
        if index in samples[axis]:
            raise ValueError("duplicate sample")
        if index == 0:
            expected_ring, expected_theta, expected_r = 0, 0, 0
        else:
            expected_ring = 1 + (index - 1) // config["angles"]
            expected_theta = 360 * ((index - 1) % config["angles"]) / config["angles"]
            expected_r = config["outer_radius_mm"] * expected_ring / config["rings"]
        for actual, expected, label in (
            (ring, expected_ring, "ring"), (radius, expected_r, "radius"),
            (theta, expected_theta, "theta"),
            (x, expected_r * math.cos(math.radians(expected_theta)), "x"),
            (y, expected_r * math.sin(math.radians(expected_theta)), "y"),
            (half_range, config["half_range_mm"], "range"),
            (step, config["axial_step_mm"], "axial step"),
            (simulation, config["simulation"], "simulation")):
            close(actual, expected, label)
        samples[axis][index] = row
    result = {}
    for axis, points in samples.items():
        if len(points) != count:
            raise ValueError(f"axis {axis}: incomplete grid: {len(points)}/{count}")
        center = points[0][9]
        if abs(center) < 1e-10:
            raise ValueError("integrated reference is too small")
        errors = [(100 * abs(points[i][9] - center) / abs(center), points[i]) for i in range(count)]
        worst, point = max(errors, key=lambda item: item[0])
        inner = max(error for error, row in errors if row[6] <= config["inner_radius_mm"] + 1e-10)
        result[str(axis)] = dict(component=config["x_component" if axis == 1 else "y_component"],
                                center_tm=center, target_error_percent=100 * abs(abs(center) / config["target_tm"] - 1),
                                inner_uniformity_percent=inner, outer_uniformity_percent=worst,
                                worst_xy_mm=point[4:6], sample_count=count)
    return result, samples


def evaluate(manifest_path):
    manifest_path = Path(manifest_path).resolve()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema") != SCHEMA:
        raise ValueError("unsupported field-quality manifest schema")
    config = manifest["config"]
    folder = manifest_path.parent
    post = folder / manifest["post_comi"]
    if digest(post) != manifest["post_comi_sha256"]:
        raise ValueError("Post COMI changed after preparation; regenerate a separate package")
    database = Path(manifest["database"])
    source_hash = digest(database) if database.is_file() else None
    if manifest["database_sha256"] and source_hash != manifest["database_sha256"]:
        raise ValueError("source database changed or disappeared after preparation")
    raw = folder / manifest["raw_file"]
    summary = folder / manifest["summary_file"]
    axes, samples = reduce_grid(numeric_rows(raw), config)
    summary_rows = {}
    for row in numeric_rows(summary):
        key = (row[0], row[1])
        if key not in ((90, 1), (90, 2), (91, 1), (91, 2)) or key in summary_rows:
            raise ValueError("unexpected or duplicate summary record")
        summary_rows[key] = row
    if len(summary_rows) != 4:
        raise ValueError("missing completed summary or range-check records")
    for axis in (1, 2):
        item = axes[str(axis)]
        row, boundary = summary_rows[(90, axis)], summary_rows[(91, axis)]
        expected = [item["center_tm"], item["target_error_percent"], item["inner_uniformity_percent"],
                    item["outer_uniformity_percent"]]
        for actual, value in zip(row[2:6], expected):
            close(actual, value, "COMI summary")
        # Tied extrema may legitimately identify another point on the same grid.
        matching = [p for p in samples[axis].values()
                    if math.dist(p[4:6], row[6:8]) < 1e-8]
        if not matching:
            raise ValueError("summary worst point is outside the declared grid")
        worst = 100 * abs(matching[0][9] - item["center_tm"]) / abs(item["center_tm"])
        close(worst, item["outer_uniformity_percent"], "worst point error")
        for actual, value in zip(row[8:], [config["half_range_mm"], config["axial_step_mm"], config["rings"], config["angles"]]):
            close(actual, value, "summary sampling metadata")
        if abs(boundary[2]) < 1e-10 or abs(boundary[6]) < 1e-15:
            raise ValueError("range-check reference is too small")
        close(boundary[3], item["center_tm"], "range-check centre")
        change = 100 * abs(boundary[3] - boundary[2]) / abs(boundary[2])
        close(boundary[4], change, "range-check increment")
        close(boundary[9], config["check_range_mm"], "shorter half-range")
        close(boundary[10], config["half_range_mm"], "range-check half-range")
        close(boundary[11], config["axial_step_mm"], "range-check step")
        endpoint = 100 * max(abs(boundary[7]), abs(boundary[8])) / abs(boundary[6])
        close(boundary[5], endpoint, "endpoint percentage")
        item["range_increment_percent"] = change
        item["endpoint_percent"] = endpoint
        item["center_range_check_pass"] = max(change, boundary[5]) <= config["boundary_limit_percent"]
        item["numeric_field_pass"] = (item["outer_uniformity_percent"] < config["uniformity_limit_percent"]
                                      and item["target_error_percent"] < config["target_error_limit_percent"])
    return dict(schema=SCHEMA, status="numeric_outputs_audited", axes=axes,
                numeric_field_pass=all(a["numeric_field_pass"] for a in axes.values()),
                center_range_check_pass=all(a["center_range_check_pass"] for a in axes.values()),
                source_hashes=dict(manifest=digest(manifest_path), post=digest(post), raw=digest(raw),
                                   summary=digest(summary), database=source_hash),
                solver_provenance_verified=False, sampling_convergence_verified=False,
                mesh_convergence_verified=False,
                limitations=["Finite sampled disk, fixed transverse straight rays.",
                             "Centre-only range check is not a bound on the unintegrated tail.",
                             "Hashes associate supplied files; they do not prove a completed solver/Post run."])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prep = commands.add_parser("prepare", help="render a new Post package; never launch OPERA")
    prep.add_argument("--database", type=Path, required=True)
    prep.add_argument("--out", type=Path, required=True)
    for flag in ("half-range-mm", "check-range-mm", "inner-radius-mm", "outer-radius-mm", "target-tm"):
        prep.add_argument("--" + flag, type=float, required=True)
    for flag, default in (("axial-step-mm", 5), ("uniformity-limit-percent", 1),
                          ("target-error-limit-percent", 1), ("boundary-limit-percent", 0.1)):
        prep.add_argument("--" + flag, type=float, default=default)
    for flag, default in (("rings", 14), ("angles", 64), ("simulation", 1)):
        prep.add_argument("--" + flag, type=int, default=default)
    prep.add_argument("--x-component", choices=("BX", "BY", "BZ"), default="BY")
    prep.add_argument("--y-component", choices=("BX", "BY", "BZ"), default="BX")
    audit = commands.add_parser("evaluate", help="independently recompute and audit existing numeric outputs")
    audit.add_argument("manifest", type=Path)
    audit.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == "prepare":
            config = {k: v for k, v in vars(args).items() if k not in ("command", "database", "out")}
            print(prepare(args.database, args.out, config))
        else:
            result = evaluate(args.manifest)
            # Refuse overwrite, including accidental overwrite of any input.
            with args.out.open("x", encoding="utf-8") as stream:
                json.dump(result, stream, indent=2, allow_nan=False)
                stream.write("\n")
            print(args.out.resolve())
    except (ValueError, OSError, KeyError) as error:
        parser.exit(2, f"error: {error}\n")


if __name__ == "__main__":
    main()
