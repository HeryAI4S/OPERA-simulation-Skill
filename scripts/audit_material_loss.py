#!/usr/bin/env python3
"""Audit numeric native Post material-loss exports without opening or changing OPERA databases."""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path


def number(value):
    return float(value.replace('D', 'E').replace('d', 'e'))


def close(a, b):
    return math.isclose(a, b, rel_tol=1e-8, abs_tol=1e-12)


def integrate(times, powers):
    energy = 0.0
    for t0, t1, p0, p1 in zip(times, times[1:], powers, powers[1:]):
        energy += (t1 - t0) * (p0 + p1) / 2
    if not math.isfinite(energy):
        raise ValueError('Nonfinite integrated energy.')
    return energy


def audit(text, labels, *, volume_unit, solver_points=None,
          full_magnet_factor=None, symmetry_evidence=None):
    if (len(labels) < 2 or labels[0] != 'ALL_VOLUMES'
            or len(set(labels)) != len(labels) or any(not x.strip() for x in labels)):
        raise ValueError('Labels must be distinct: ALL_VOLUMES first, then an exhaustive disjoint partition.')
    if volume_unit not in ('mm3', 'm3'):
        raise ValueError('Declare native volume unit: mm3 or m3.')
    if full_magnet_factor is not None:
        if (not math.isfinite(full_magnet_factor) or full_magnet_factor < 1
                or not symmetry_evidence or not symmetry_evidence.strip()):
            raise ValueError('Reconstruction needs a finite factor >= 1 and explicit domain/symmetry evidence.')
    elif symmetry_evidence is not None:
        raise ValueError('Symmetry evidence requires an explicit reconstruction factor.')

    times, blocks = [], []
    for line_index, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = [number(value) for value in line.split()]
        except ValueError as exc:
            raise ValueError(f'Line {line_index}: expected numeric native export, including numeric time.') from exc
        if len(row) != 5 or not all(math.isfinite(value) for value in row):
            raise ValueError(f'Line {line_index}: require five finite numbers.')
        time, label_id, power, volume, status = row
        if not label_id.is_integer() or not 0 <= label_id < len(labels):
            raise ValueError(f'Line {line_index}: unknown/noninteger label index.')
        if status != 0 or power < 0 or volume <= 0:
            raise ValueError(f'Line {line_index}: failed activation, negative power or nonpositive volume.')
        if not times or time != times[-1]:
            if times and time <= times[-1]:
                raise ValueError('Time blocks must be strictly increasing; repeated runs are unsupported.')
            times.append(time)
            blocks.append({})
        index = int(label_id)
        if index in blocks[-1]:
            raise ValueError(f'Line {line_index}: duplicate label in time block.')
        blocks[-1][index] = (power, volume)
    if len(times) < 2 or any(set(block) != set(range(len(labels))) for block in blocks):
        raise ValueError('Require at least two complete time blocks with every label exactly once.')

    powers = {label: [block[i][0] for block in blocks] for i, label in enumerate(labels)}
    volumes = {label: blocks[0][i][1] for i, label in enumerate(labels)}
    for block in blocks:
        if not close(block[0][0], sum(block[i][0] for i in range(1, len(labels)))):
            raise ValueError('Material power sum does not match ALL_VOLUMES.')
        if not close(block[0][1], sum(block[i][1] for i in range(1, len(labels)))):
            raise ValueError('Material volume sum does not match ALL_VOLUMES; check partition coverage.')
        if any(not close(block[i][1], volumes[label]) for i, label in enumerate(labels)):
            raise ValueError('Label volume changed between states; this helper requires a fixed geometry/selection.')

    energies = {label: integrate(times, values) for label, values in powers.items()}
    duration = times[-1] - times[0]
    result = dict(status='NATIVE_EXPORT_AUDITED', scope='native_export_domain',
                  times_s=times, interval_s=[times[0], times[-1]], labels=labels,
                  native_power_W=powers, label_volumes=volumes, volume_unit=volume_unit,
                  mesh_energy_J=energies,
                  mesh_interval_mean_power_W={label: value / duration for label, value in energies.items()},
                  mesh_sampled_peak_power_W={label: max(values) for label, values in powers.items()},
                  material_power_and_volume_closure=True, solver_comparison=None,
                  full_magnet_estimate=None,
                  comparison_tolerance=dict(relative=1e-8, absolute=1e-12,
                                            precision_contract='Export at least 12 significant digits; low-precision rounding can fail closure.'),
                  method='Trapezoidal quadrature over exported saved states; no inferred initial state.',
                  limits='Audits supplied exports, not a database reload or mesh/time-step convergence. '
                         'Closure establishes accounting within the common domain, not whole-magnet coverage. '
                         'Mechanisms outside the exported J dot E field are not included.')

    if solver_points is not None:
        if (len(solver_points) < 2
                or any(not math.isfinite(t) or not math.isfinite(p) or p < 0 for t, p in solver_points)
                or any(b[0] <= a[0] for a, b in zip(solver_points, solver_points[1:]))):
            raise ValueError('Solver history must be finite, nonnegative and strictly increasing.')
        if not close(times[0], solver_points[0][0]) or not close(times[-1], solver_points[-1][0]):
            raise ValueError('Native and solver histories must cover the same interval.')
        differences = []
        for time, power in zip(times, powers['ALL_VOLUMES']):
            matches = [p for t, p in solver_points if close(t, time)]
            if len(matches) != 1 or not close(matches[0], power):
                raise ValueError('Missing/ambiguous saved time or native/solver power mismatch.')
            differences.append(abs(matches[0] - power))
        solver_times, solver_powers = zip(*solver_points)
        result['solver_comparison'] = dict(
            max_abs_power_difference_W=max(differences),
            all_step_energy_J=integrate(solver_times, solver_powers),
            native_saved_energy_J=energies['ALL_VOLUMES'],
            interpretation='Matching saved-state power does not imply equal quadrature on denser solver records.')

    if full_magnet_factor is not None:
        full = dict(factor=full_magnet_factor, evidence=symmetry_evidence,
                    energy_J={label: value * full_magnet_factor for label, value in energies.items()},
                    interval_mean_power_W={label: value * full_magnet_factor
                                           for label, value in result['mesh_interval_mean_power_W'].items()},
                    sampled_peak_power_W={label: value * full_magnet_factor
                                          for label, value in result['mesh_sampled_peak_power_W'].items()},
                    scope='Conditional full-magnet estimate; caller must verify equivalent copies and no prior expansion.')
        for field in ('energy_J', 'interval_mean_power_W', 'sampled_peak_power_W'):
            if not all(math.isfinite(value) for value in full[field].values()):
                raise ValueError('Reconstruction overflow.')
        result['full_magnet_estimate'] = full
    return result


def read_solver_csv(text):
    reader = csv.DictReader(text.splitlines())
    fields = reader.fieldnames or []
    power_fields = [key for key in ('mesh_ohmic_power_W', 'solver_mesh_ohmic_power_W') if key in fields]
    if 'time_s' not in fields or len(power_fields) != 1:
        raise ValueError('Solver CSV requires time_s and one supported mesh power column; never a scaled full-magnet total.')
    return [(number(row['time_s']), number(row[power_fields[0]])) for row in reader]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('native', type=Path, help='Five columns: time_s label_index power_W volume activation_status.')
    parser.add_argument('--labels', nargs='+', required=True, help='Index order: ALL_VOLUMES followed by a disjoint exhaustive partition.')
    parser.add_argument('--volume-unit', choices=['mm3', 'm3'], required=True)
    parser.add_argument('--solver-csv', type=Path, help='Optional unscaled history from extract_solver_loss.py.')
    parser.add_argument('--full-magnet-factor', type=float, help='Explicit additional factor only; omitted by default.')
    parser.add_argument('--symmetry-evidence', help='Geometric coverage, equivalent copies and prior activation expansion.')
    parser.add_argument('--out', type=Path, required=True, help='New output directory; existing paths are refused.')
    args = parser.parse_args()
    raw = args.native.read_bytes()
    solver_raw = args.solver_csv.read_bytes() if args.solver_csv else None
    result = audit(raw.decode('utf-8-sig'), args.labels, volume_unit=args.volume_unit,
                   solver_points=read_solver_csv(solver_raw.decode('utf-8-sig')) if solver_raw is not None else None,
                   full_magnet_factor=args.full_magnet_factor, symmetry_evidence=args.symmetry_evidence)
    inputs = [(args.native, raw)]
    if args.solver_csv:
        inputs.append((args.solver_csv, solver_raw))
    result['sources'] = []
    for path, data in inputs:
        if path.read_bytes() != data:
            raise ValueError('Input changed during audit.')
        result['sources'].append(dict(path=str(path.resolve()), sha256=hashlib.sha256(data).hexdigest()))
    args.out.mkdir(parents=True, exist_ok=False)
    with (args.out / 'material_power.csv').open('w', newline='', encoding='utf-8') as stream:
        writer = csv.writer(stream)
        writer.writerow(['time_s', 'region', 'native_power_W', 'conditional_full_magnet_power_W'])
        for i, time in enumerate(result['times_s']):
            for label in args.labels:
                power = result['native_power_W'][label][i]
                writer.writerow([time, label, power, power * args.full_magnet_factor
                                 if args.full_magnet_factor is not None else ''])
    (args.out / 'summary.json').write_text(json.dumps(result, indent=2, allow_nan=False), encoding='utf-8')
    print(json.dumps({key: value for key, value in result.items() if key != 'native_power_W'}, indent=2))


if __name__ == '__main__':
    main()
